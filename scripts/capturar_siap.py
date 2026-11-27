"""Captura los cierres anuales de la producción agrícola municipal del SIAP (SADER) a Bronce.

    python main.py siap-captura --anios 2016 2017 ... 2025

Cada año es un CSV nacional oficial (~5–6 MB) que se guarda sin modificar con sidecar y SHA-256. Usa el
extractor ético (robots.txt, User-Agent identificable, pausa ≥ 1.5 s). Si un año ya está en Bronce no se
vuelve a descargar. Después ``python main.py siap`` integra todos los años a Oro.
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

URL = "https://nube.agricultura.gob.mx/index.php?view=10AE434F-A2158368-A120BC5A-EDF4AFAA&ANIO={anio}"
COLUMNAS_MINIMAS = ("Anio", "Idestado", "Nomcultivo", "Volumenproduccion", "Valorproduccion")


class SiapExtractor(BaseExtractor):
    fuente = "siap"

    def fetch_anio(self, anio: int) -> RawCapture:
        response = self.get(URL.format(anio=anio))
        cabecera = response.content[:600].decode("cp1252", errors="replace")
        faltan = [c for c in COLUMNAS_MINIMAS if c not in cabecera]
        if faltan:
            raise ValueError(f"La respuesta del SIAP para {anio} no es el CSV esperado (faltan {faltan})")
        filas = response.content.count(b"\n")
        return RawCapture(fuente=self.fuente, url=response.url, contenido=response.content, formato="csv",
                          http_status=response.status_code, registros=max(0, filas - 1), estado="ok",
                          metadatos={"etiqueta": f"cierre-agricola-municipal-{anio}", "fecha_ref_inicio": f"{anio}-01-01",
                                     "fecha_ref_fin": f"{anio}-12-31", "anio_estadistico": anio, "estado": "nacional (se filtra Colima en Oro)",
                                     "unidad_geografica": "municipio",
                                     "nota": "Descarga oficial SIAP DGSIAP, bytes originales sin modificar; producción histórica no representa inventario disponible."})


def ya_capturados(bronze: Path) -> set[int]:
    anios = set()
    for meta in (bronze / "siap").rglob("*.meta.json"):
        md = json.loads(meta.read_text(encoding="utf-8")).get("metadatos_captura", {})
        if md.get("anio_estadistico"):
            anios.add(int(md["anio_estadistico"]))
    return anios


def capturar(anios: list[int], settings=None, extractor: SiapExtractor | None = None) -> dict:
    settings = settings or get_settings()
    run_id = new_run_id()
    ext = extractor or SiapExtractor(settings)
    writer = BronzeWriter(settings.bronze_dir)
    man = Manifest(run_id, "siap", "historica", "local", parametros={"anios": anios})
    existentes = ya_capturados(settings.bronze_dir)
    for anio in anios:
        clave = {"anio": anio}
        if anio in existentes:
            man.add_consulta(clave, "omitida", error="ya existe en Bronce")
            continue
        try:
            cap = ext.fetch_anio(anio)
            saved = writer.write(cap, run_id)
            man.add_archivo(saved.ruta, saved.sha256, cap.url, saved.bytes)
            man.add_consulta(clave, "ok", cap.registros, saved.ruta.name)
        except Exception as exc:  # noqa: BLE001 - se registra y se continúa con el siguiente año
            man.add_consulta(clave, "fallida", error=f"{type(exc).__name__}: {exc}")
    man.solicitudes = ext.stats["solicitudes"]
    man.finalizar().save(settings.bronze_dir / "siap" / "manifests")
    return {"run_id": run_id, "estado": man.estado, "consultas": man.consultas}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--anios", nargs="+", type=int, required=True)
    a = ap.parse_args(argv)
    settings = get_settings()
    setup_logging(new_run_id(), settings)
    r = capturar(a.anios, settings)
    print(json.dumps({"estado": r["estado"], "consultas": [{k: c.get(k) for k in ("parametros", "clave", "estado", "registros", "error") if k in c} for c in r["consultas"]]},
                     ensure_ascii=False, indent=2, default=str))
    return 0 if r["estado"] in {"exitosa", "sin_resultados"} else 2


if __name__ == "__main__":
    sys.exit(main())
