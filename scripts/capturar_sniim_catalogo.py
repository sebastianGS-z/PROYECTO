"""Captura las cotizaciones del catálogo SNIIM (ProductoId=Todos) por mercado.

El SNIIM devuelve la tabla publicada para una fecha, no una historia inventada.
Los originales HTML y sus metadatos se conservan en Bronce; --solo-procesar
regenera los CSV/JSON públicos sin volver a consultar la fuente.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

from almacenamiento.bronze_writer import BronzeWriter, sha256_file
from almacenamiento.manifest import Manifest, new_run_id
from config.settings import BASE_DIR, get_settings, setup_logging
from extractores.base import RobotsDisallowed, RobotsUnavailable
from extractores.sniim_extractor import SniimExtractor, decodificar_html, parse_resultados


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFD", str(value or ""))
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).lower().split())


FRUIT_PREFIXES = ("aguacate", "ciruela", "coco", "durazno", "fresa", "granada", "guanabana",
                  "guayaba", "higo", "kiwi", "lima", "limon", "mamey", "mandarina", "mango",
                  "manzana", "melon", "membrillo", "nanche", "naranja", "nectarina", "papaya",
                  "pera", "pina", "platano", "sandia", "tamarindo", "tejocote", "toronja",
                  "tuna", "uva", "zapote", "zarzamora")


def _number(value: str) -> float | None:
    raw = str(value or "").replace("$", "").replace(",", "").strip()
    try:
        result = float(raw)
        return result if result >= 0 else None
    except ValueError:
        return None


def _weight(presentation: str) -> tuple[float | None, str]:
    normalized = _norm(presentation)
    if normalized in {"kg", "kilogramo", "kilogramos"}:
        return 1.0, "kilogramo_reportado"
    match = re.search(r"\bde\s+(\d+(?:\.\d+)?)\s*kg\b", normalized)
    if match:
        value = float(match.group(1))
        if value > 0:
            return value, "peso_explicito_en_presentacion"
    return None, "sin_peso_explicito"


def capturar(fecha: date, mercados: list[str] | None = None) -> dict:
    settings = get_settings()
    run_id = new_run_id()
    setup_logging(run_id, settings)
    extractor = SniimExtractor(settings, precios_por="presentacion")
    catalog = extractor.cargar_catalogo()
    all_products = next((p for p in catalog.productos if p.valor == "-1"), None)
    if all_products is None:
        raise RuntimeError("El catálogo SNIIM ya no ofrece la opción Todos; no se hará captura incompleta.")
    market_options = [m for m in catalog.mercados if m.valor != "-1"]
    if mercados:
        wanted = set(mercados)
        market_options = [m for m in market_options if m.valor in wanted]
        unknown = wanted - {m.valor for m in market_options}
        if unknown:
            raise ValueError(f"Claves de mercado no presentes en el catálogo SNIIM: {sorted(unknown)}")
    writer = BronzeWriter(settings.bronze_dir)
    manifest = Manifest(run_id, "sniim_catalogo", "diaria", "local",
                       parametros={"producto": "Todos", "producto_id": "-1", "fecha": fecha.isoformat(),
                                   "mercados": [m.valor for m in market_options]})
    for market in market_options:
        try:
            capture = extractor.fetch_precios(all_products, market.etiqueta, fecha, fecha)
            saved = writer.write(capture, run_id)
            manifest.add_archivo(saved.ruta, saved.sha256, capture.url, saved.bytes,
                                 base=settings.data_dir.parent if settings.data_dir.parent in saved.ruta.parents else None)
            manifest.add_consulta({"mercado_id": market.valor, "mercado": market.etiqueta,
                                   "fecha": fecha.isoformat()}, capture.estado, capture.registros,
                                  saved.ruta.name, advertencias=capture.advertencias)
            print(f"SNIIM {market.valor} {market.etiqueta}: {capture.registros} filas ({capture.estado})", flush=True)
        except (RobotsDisallowed, RobotsUnavailable):
            raise
        except Exception as exc:
            manifest.add_consulta({"mercado_id": market.valor, "mercado": market.etiqueta,
                                   "fecha": fecha.isoformat()}, "fallida", error=f"{type(exc).__name__}: {exc}")
            print(f"SNIIM {market.valor} {market.etiqueta}: ERROR {type(exc).__name__}: {exc}", flush=True)
    manifest.finalizar()
    out = settings.bronze_dir / "sniim_catalogo" / "manifests"
    manifest.save(out)
    return {"run_id": run_id, "fecha": fecha.isoformat(), "capturas": len(market_options),
            "ok": sum(c.get("estado") in {"ok", "parcial"} for c in manifest.consultas),
            "fallidas": sum(c.get("estado") == "fallida" for c in manifest.consultas)}


def procesar() -> dict:
    root = BASE_DIR / "data/bronce/sniim"
    rows: list[dict] = []
    captures_by_market: dict[tuple[str, str], tuple[Path, dict, str]] = {}
    for path in sorted(root.rglob("*.html")):
        sidecar = path.with_name(path.name + ".meta.json")
        if not sidecar.is_file():
            continue
        meta = json.loads(sidecar.read_text(encoding="utf-8")).get("metadatos_captura", {})
        if meta.get("producto_id") != "-1" or meta.get("fecha_ref_inicio") != meta.get("fecha_ref_fin"):
            continue
        sha = sha256_file(path)
        if sha != meta.get("sha256"):
            raise ValueError(f"SHA256 de captura no coincide: {path}")
        key = (str(meta.get("fecha_ref_inicio", "")), str(meta.get("mercado_id", "")))
        previous = captures_by_market.get(key)
        if previous and str(previous[1].get("fecha_captura", "")) >= str(meta.get("fecha_captura", "")):
            continue
        captures_by_market[key] = (path, meta, sha)
    captures = []
    for path, meta, sha in captures_by_market.values():
        parsed = parse_resultados(decodificar_html(path.read_bytes()))
        captures.append({"archivo": path.relative_to(BASE_DIR).as_posix(), "sha256": sha,
                         "fecha": meta.get("fecha_ref_inicio"), "mercado_id": meta.get("mercado_id"),
                         "mercado": meta.get("mercado"), "estado": "ok" if parsed.registros else "sin_resultados",
                         "filas": len(parsed.registros), "pagina": list(parsed.pagina) if parsed.pagina else None})
        for index, raw in enumerate(parsed.registros, 1):
            product, quality = raw.get("Producto", "").strip(), raw.get("Calidad", "").strip()
            variant = f"{product} - {quality}".strip(" -")
            frequent = _number(raw.get("Precio Frec"))
            if frequent is None:
                continue
            presentation = raw.get("Presentación", "").strip()
            weight, rule = _weight(presentation)
            category = "fruta" if _norm(product).startswith(FRUIT_PREFIXES) else "otros_productos"
            rows.append({"fecha": meta.get("fecha_ref_inicio"), "mercado_id": str(meta.get("mercado_id", "")),
                         "mercado": meta.get("mercado", ""), "producto": product, "calidad": quality,
                         "categoria": category, "variante": variant, "origen": raw.get("Origen", "").strip(),
                         "presentacion": presentation, "unidad_precio": "MXN/kg" if weight else f"MXN/{presentation or 'presentación reportada'}",
                         "precio_min": _number(raw.get("Precio Mín")), "precio_max": _number(raw.get("Precio Max")),
                         "precio_frecuente_presentacion": frequent,
                         "peso_presentacion_kg": weight,
                         "precio_frecuente_mxn_kg": frequent / weight if weight else None,
                         "regla_conversion": rule, "source_file": path.relative_to(BASE_DIR).as_posix(),
                         "source_sha256": sha, "source_record_index": index})
    rows.sort(key=lambda r: (r["producto"], r["variante"], r["mercado"], r["origen"]))
    public = BASE_DIR / "data/publico"
    public.mkdir(parents=True, exist_ok=True)
    csv_path = public / "precios_sniim_actuales.csv"
    fields = list(rows[0]) if rows else ["fecha", "mercado_id", "mercado", "producto", "calidad", "categoria", "variante", "origen", "presentacion", "unidad_precio", "precio_min", "precio_max", "precio_frecuente_presentacion", "peso_presentacion_kg", "precio_frecuente_mxn_kg", "regla_conversion", "source_file", "source_sha256", "source_record_index"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    rows.sort(key=lambda r: (r["producto"], r["variante"], r["mercado"], r["origen"]))
    dates = sorted({r["fecha"] for r in rows if r["fecha"]})
    fruits = [r for r in rows if r["categoria"] == "fruta"]
    report = {"esquema": "oaic-sniim-catalogo/1", "generado_utc": datetime.now().astimezone().isoformat(),
              "fechas_observadas": dates, "filas": len(rows),
              "productos": sorted({r["producto"] for r in rows}),
              "frutas": sorted({r["producto"] for r in fruits}), "variantes_fruta": sorted({r["variante"] for r in fruits}),
              "filas_fruta": len(fruits), "mercados_con_fruta": sorted({r["mercado_id"] for r in fruits}),
              "mercados": sorted({r["mercado_id"] for r in rows}),
              "filas_mxn_kg": sum(r["precio_frecuente_mxn_kg"] is not None for r in rows),
              "capturas": captures,
              "advertencia": "Cotización diaria publicada por SNIIM para la fecha mostrada. No se imputan productos o mercados sin observación. El precio solo se convierte a MXN/kg si la presentación declara kg; los demás conservan su unidad.",
              "fuente": "SNIIM · Secretaría de Economía", "csv": "precios_sniim_actuales.csv"}
    (public / "precios_sniim_actuales.json").write_text(json.dumps({"reporte": report, "registros": rows}, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return {"filas": len(rows), "productos": len(report["productos"]), "filas_fruta": len(fruits),
            "frutas": len(report["frutas"]), "mercados": len(report["mercados"]),
            "filas_mxn_kg": report["filas_mxn_kg"], "fechas": dates, "json": str(public / "precios_sniim_actuales.json")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", help="Fecha SNIIM AAAA-MM-DD; por defecto ayer")
    parser.add_argument("--mercados", nargs="*", help="IDs del formulario SNIIM; por defecto todos")
    parser.add_argument("--solo-procesar", action="store_true")
    args = parser.parse_args(argv)
    if not args.solo_procesar:
        fecha = date.fromisoformat(args.fecha) if args.fecha else date.today() - timedelta(days=1)
        print(json.dumps(capturar(fecha, args.mercados), ensure_ascii=False, indent=2))
    print(json.dumps(procesar(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
