"""Genera datos SINTÉTICOS exclusivamente para pruebas de la tubería.

Salida SIEMPRE en data/sintetico/ (nunca en data/bronce/), con columna y nombre que lo identifican
como sintético. Estos archivos NO son capturas reales y no deben usarse como evidencia de cobertura.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from datetime import date, timedelta

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

from config.settings import get_settings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dias", type=int, default=30)
    ap.add_argument("--semilla", type=int, default=42)
    a = ap.parse_args(argv)
    destino = get_settings().synthetic_dir
    destino.mkdir(parents=True, exist_ok=True)
    rnd, hoy = random.Random(a.semilla), date.today()
    ruta = destino / f"SINTETICO_precios_{hoy.isoformat()}.csv"
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["es_sintetico", "fecha", "producto", "precio_frecuente"])
        for i in range(a.dias):
            for prod in ("platano", "limon", "papaya"):
                w.writerow([True, (hoy - timedelta(days=i)).isoformat(), prod, round(rnd.uniform(8, 40), 2)])
    print(f"SINTÉTICO (solo pruebas): {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
