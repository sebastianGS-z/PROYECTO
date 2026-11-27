"""Comercio exterior para exportadores: UN Comtrade (varios años y frutas) y tipo de cambio USD/MXN.

    python main.py comtrade-captura --anios 2019 2020 2021 2022 2023 2024
    python main.py comtrade-captura --solo-tipo-cambio --anios 2019 ... 2024

Consultas por código HS y año (API pública de UN Comtrade, previsualización de hasta 500 filas):

* ``destinos_mexico``  — importaciones que cada país reporta **desde México** (flujo M, socio 484).
* ``importadores_mundo`` — importaciones totales de cada país desde **todo el mundo** (flujo M, socio 0):
  tamaño del mercado, para ver dónde compran mucho y México vende poco.
* ``exportadores`` — exportaciones de cada país al mundo (flujo X, socio 0): competidores.

Tipo de cambio: promedio anual USD→MXN del Banco Central Europeo vía Frankfurter (sin clave).

Usa el extractor ético (robots.txt, User-Agent identificable, pausa ≥ 1.5 s). Lo ya capturado no se repite;
si el API responde 429 (cuota), se detiene y la siguiente corrida continúa donde quedó.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

from almacenamiento.bronze_writer import BronzeWriter
from almacenamiento.manifest import Manifest, new_run_id
from config.settings import get_settings, setup_logging
from extractores.base import BaseExtractor, RawCapture
from scripts.capturar_comercio_internacional import FRUITS

BASE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
PAUSA_COMTRADE_S = 6.0
FX = "https://api.frankfurter.dev/v1/{a}-01-01..{a}-12-31"
CONSULTAS = {
    "destinos_mexico": {"flowCode": "M", "partnerCode": "484"},
    "importadores_mundo": {"flowCode": "M", "partnerCode": "0"},
    "exportadores": {"flowCode": "X", "partnerCode": "0"},
}


class ComtradeExtractor(BaseExtractor):
    fuente = "un_comtrade"

    def consulta(self, codigo: str, tipo: str, anio: int) -> RawCapture:
        params = {"period": str(anio), "cmdCode": codigo, "maxRecords": 500, **CONSULTAS[tipo]}
        r = self.get(BASE, params=params, headers={"Accept": "application/json"})
        payload = self.parse_json(r)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        n = int(payload.get("count", len(payload.get("data", []))))
        return RawCapture(fuente=self.fuente, url=r.url, contenido=r.content, formato="json", http_status=r.status_code,
                          registros=n, estado="ok" if n else "sin_resultados",
                          metadatos={"etiqueta": f"{tipo.replace('_', '-')}-{codigo}-{anio}", "fecha_ref_inicio": f"{anio}-01-01",
                                     "fecha_ref_fin": f"{anio}-12-31", "codigo_hs": codigo, "tipo_consulta": tipo, "periodo": anio,
                                     "limite_preview": 500, "truncamiento_posible": n >= 500,
                                     "nota": "Datos aduanales de comercio de mercancías; no equivalen a cotizaciones ni a oportunidad rentable."})


class TipoCambioExtractor(BaseExtractor):
    fuente = "tipo_cambio"

    def anual(self, anio: int) -> RawCapture:
        r = self.get(FX.format(a=anio), params={"base": "USD", "symbols": "MXN"})
        payload = self.parse_json(r)
        if not payload.get("rates"):
            raise ValueError(f"Frankfurter no devolvió tasas para {anio}")
        return RawCapture(fuente=self.fuente, url=r.url, contenido=r.content, formato="json", http_status=r.status_code,
                          registros=len(payload["rates"]), estado="ok",
                          metadatos={"etiqueta": f"usd-mxn-{anio}", "fecha_ref_inicio": f"{anio}-01-01", "fecha_ref_fin": f"{anio}-12-31",
                                     "periodo": anio, "nota": "Tipos de referencia diarios del Banco Central Europeo publicados por Frankfurter."})


def _existentes(bronze: Path, fuente: str) -> set[str]:
    out = set()
    for meta in (bronze / fuente).rglob("*.meta.json"):
        md = json.loads(meta.read_text(encoding="utf-8")).get("metadatos_captura", {})
        if md.get("estado_captura") in {"ok", "sin_resultados"}:
            out.add(str(md.get("etiqueta")))
    return out


def capturar(anios: list[int], codigos: list[str] | None = None, tipos: list[str] | None = None, solo_fx: bool = False,
             settings=None, extractor: ComtradeExtractor | None = None, fx: TipoCambioExtractor | None = None) -> dict:
    settings = settings or get_settings()
    run_id = new_run_id()
    writer = BronzeWriter(settings.bronze_dir)
    resultado = {"run_id": run_id, "comtrade": [], "tipo_cambio": []}
    fx = fx or TipoCambioExtractor(settings)
    hechos_fx = _existentes(settings.bronze_dir, "tipo_cambio")
    for anio in anios:
        if f"usd-mxn-{anio}" in hechos_fx:
            continue
        try:
            cap = fx.anual(anio)
            writer.write(cap, run_id)
            resultado["tipo_cambio"].append({"anio": anio, "estado": "ok", "dias": cap.registros})
        except Exception as exc:  # noqa: BLE001
            resultado["tipo_cambio"].append({"anio": anio, "estado": "fallida", "error": f"{type(exc).__name__}: {exc}"})
    if solo_fx:
        return resultado
    # La previsualización pública de Comtrade responde 429 con pausas de 1.5 s: se usa una pausa mayor.
    from dataclasses import replace
    ext = extractor or ComtradeExtractor(replace(settings, min_delay=max(settings.min_delay, PAUSA_COMTRADE_S)))
    man = Manifest(run_id, "un_comtrade", "historica", "local", parametros={"anios": anios})
    hechos = _existentes(settings.bronze_dir, "un_comtrade")
    for codigo in codigos or list(FRUITS):
        for tipo in tipos or list(CONSULTAS):
            for anio in anios:
                etiqueta = f"{tipo.replace('_', '-')}-{codigo}-{anio}"
                if etiqueta in hechos:
                    continue
                clave = {"codigo_hs": codigo, "tipo": tipo, "anio": anio}
                try:
                    cap = ext.consulta(codigo, tipo, anio)
                    saved = writer.write(cap, run_id)
                    man.add_archivo(saved.ruta, saved.sha256, cap.url, saved.bytes)
                    man.add_consulta(clave, cap.estado if cap.estado == "sin_resultados" else "ok", cap.registros, saved.ruta.name)
                except Exception as exc:  # noqa: BLE001
                    texto = f"{type(exc).__name__}: {exc}"
                    man.add_consulta(clave, "fallida", error=texto)
                    if "429" in texto:  # cuota del API público: no se insiste
                        man.add_consulta({"paso": "cuota"}, "fallida", error="límite 429 del API público; continuar en la siguiente corrida")
                        man.solicitudes = ext.stats["solicitudes"]
                        man.finalizar().save(settings.bronze_dir / "un_comtrade" / "manifests")
                        resultado["comtrade"] = man.consultas
                        resultado["detenido_por_cuota"] = True
                        return resultado
    man.solicitudes = ext.stats["solicitudes"]
    man.finalizar().save(settings.bronze_dir / "un_comtrade" / "manifests")
    resultado["comtrade"] = man.consultas
    return resultado


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anios", nargs="+", type=int, default=[2019, 2020, 2021, 2022, 2023, 2024])
    ap.add_argument("--codigos", nargs="*")
    ap.add_argument("--tipos", nargs="*", choices=list(CONSULTAS))
    ap.add_argument("--solo-tipo-cambio", action="store_true")
    a = ap.parse_args(argv)
    settings = get_settings()
    setup_logging(new_run_id(), settings)
    r = capturar(a.anios, a.codigos, a.tipos, a.solo_tipo_cambio, settings)
    ok = sum(1 for c in r["comtrade"] if c.get("estado") in {"ok", "sin_resultados"})
    print(json.dumps({"comtrade_ok": ok, "comtrade_fallidas": sum(1 for c in r["comtrade"] if c.get("estado") == "fallida"),
                      "detenido_por_cuota": r.get("detenido_por_cuota", False), "tipo_cambio": r["tipo_cambio"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
