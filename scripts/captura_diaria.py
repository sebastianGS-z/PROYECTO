"""Captura diaria: SNIIM (precios) + NOAA NCEI (clima) de una fecha (por defecto, ayer en Colima).

Códigos de salida: 0 exitosa/sin_resultados · 1 fallida · 2 parcial.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime, timedelta

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:  # ejecución directa
    import _bootstrap  # type: ignore # noqa: F401

from almacenamiento.manifest import new_run_id
from config.settings import COLIMA_TZ, get_settings, setup_logging
from pipeline import capturar_clima, capturar_sniim, exit_code


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fecha", help="AAAA-MM-DD; por defecto ayer (hora de Colima)")
    ap.add_argument("--solo", choices=["sniim", "clima"], help="limitar a una fuente")
    a = ap.parse_args(argv)
    settings, run_id = get_settings(), new_run_id()
    setup_logging(run_id, settings)
    log = logging.getLogger("tdl.diaria")
    fecha = date.fromisoformat(a.fecha) if a.fecha else datetime.now(COLIMA_TZ).date() - timedelta(days=1)
    log.info("Inicio captura diaria run=%s fecha=%s", run_id, fecha)
    mans = []
    if a.solo in (None, "sniim"):
        mans.append(capturar_sniim(run_id, "diaria", [(fecha, fecha)], settings))
    if a.solo in (None, "clima"):
        mans.append(capturar_clima(run_id, "diaria", fecha, fecha, settings, por_mes=False))
    code = exit_code(mans)
    log.info("Fin captura diaria run=%s estados=%s codigo_salida=%d", run_id, {m.fuente: m.estado for m in mans}, code)
    return code


if __name__ == "__main__":
    sys.exit(main())
