"""Captura histórica inicial (por defecto, los últimos 36 meses completos) + reporte de cobertura.

Nunca inventa datos: los meses sin registros reales quedan listados en el reporte de cobertura.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import date

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

from almacenamiento.manifest import Manifest, new_run_id
from config.settings import get_settings, setup_logging
from pipeline import capturar_clima, capturar_sniim, exit_code, meses, ultimos_36_meses


def reporte_cobertura(man: Manifest, periodos_esperados: int) -> dict:
    """Cobertura real por producto×mercado: meses con al menos un registro del SNIIM."""
    por_clave: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    fallidos: dict[tuple[str, str], set[str]] = defaultdict(set)
    for c in man.consultas:
        if "producto_clave" not in c or "mercado_clave" not in c or "inicio" not in c:
            continue
        k, mes = (c["producto_clave"], c["mercado_clave"]), c["inicio"][:7]
        por_clave[k][mes] = por_clave[k].get(mes, 0) + c["registros"]
        if c["estado"] == "fallida":
            fallidos[k].add(mes)
    filas = []
    for (prod, mer), meses_d in sorted(por_clave.items()):
        con = sorted(m for m, n in meses_d.items() if n > 0)
        filas.append({
            "producto": prod, "mercado": mer, "periodos_esperados": periodos_esperados,
            "periodos_con_datos": len(con), "periodos_sin_datos": sorted(m for m, n in meses_d.items() if n == 0 and m not in fallidos[(prod, mer)]),
            "periodos_fallidos": sorted(fallidos[(prod, mer)]), "cumple_36": len(con) >= 36,
            "primer_periodo": con[0] if con else None, "ultimo_periodo": con[-1] if con else None,
        })
    return {"run_id": man.run_id, "nota": "Un periodo cuenta solo si la fuente devolvió registros reales; archivos vacíos o fallidos no cuentan.",
            "cobertura": filas}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inicio"); ap.add_argument("--fin")
    ap.add_argument("--productos", nargs="*"); ap.add_argument("--mercados", nargs="*")
    ap.add_argument("--incluir-mercados-opcionales", action="store_true")
    ap.add_argument("--localidades", nargs="*")
    ap.add_argument("--solo", choices=["sniim", "clima"])
    ap.add_argument("--max-consultas", type=int, help="límite de consultas SNIIM (pruebas)")
    ap.add_argument("--dry-run", action="store_true", help="solo muestra el plan, sin red")
    a = ap.parse_args(argv)
    ini0, fin0 = ultimos_36_meses()
    inicio = date.fromisoformat(a.inicio) if a.inicio else ini0
    fin = date.fromisoformat(a.fin) if a.fin else fin0
    periodos = meses(inicio, fin)
    settings, run_id = get_settings(), new_run_id()
    setup_logging(run_id, settings)
    log = logging.getLogger("tdl.historica")
    log.info("Captura histórica run=%s %s → %s (%d periodos mensuales)", run_id, inicio, fin, len(periodos))
    if a.dry_run:
        print(f"Plan: {len(periodos)} periodos, {inicio} → {fin}. Sin solicitudes (dry-run).")
        return 0
    mans = []
    if a.solo in (None, "sniim"):
        m = capturar_sniim(run_id, "historica", periodos, settings, a.productos, a.mercados,
                           a.incluir_mercados_opcionales, max_consultas=a.max_consultas)
        mans.append(m)
        rep = reporte_cobertura(m, len(periodos))
        base = settings.bronze_dir / "sniim" / "manifests"
        ruta_json = base / f"cobertura_{run_id}.json"
        with open(ruta_json, "xb") as fh:
            fh.write(json.dumps(rep, ensure_ascii=False, indent=2).encode("utf-8"))
        with open(base / f"cobertura_{run_id}.csv", "x", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["producto", "mercado", "periodos_esperados", "periodos_con_datos", "cumple_36"])
            for f in rep["cobertura"]:
                w.writerow([f["producto"], f["mercado"], f["periodos_esperados"], f["periodos_con_datos"], f["cumple_36"]])
        for f in rep["cobertura"]:
            log.info("Cobertura %s/%s: %d/%d periodos con datos reales", f["producto"], f["mercado"], f["periodos_con_datos"], f["periodos_esperados"])
        log.info("Reporte de cobertura: %s", ruta_json)
    if a.solo in (None, "clima"):
        mans.append(capturar_clima(run_id, "historica", inicio, fin, settings, a.localidades))
    return exit_code(mans)


if __name__ == "__main__":
    sys.exit(main())
