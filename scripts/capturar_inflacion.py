"""Índice de precios al consumidor de México (Banco Mundial, FP.CPI.TOTL, 2010 = 100) a Bronce.

    python main.py inflacion-captura

Sirve para expresar precios de años anteriores en pesos del último año disponible (precios reales).
API pública sin clave; extractor ético (robots.txt, User-Agent, pausa). Es un índice anual: deflactar
precios mensuales con él es una aproximación y así se declara.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

from almacenamiento.bronze_writer import BronzeWriter
from almacenamiento.manifest import new_run_id
from config.settings import get_settings, setup_logging
from extractores.base import BaseExtractor, RawCapture

URL = "https://api.worldbank.org/v2/country/MEX/indicator/FP.CPI.TOTL"


class InflacionExtractor(BaseExtractor):
    fuente = "banco_mundial"

    def inpc(self, desde: int, hasta: int) -> RawCapture:
        r = self.get(URL, params={"format": "json", "date": f"{desde}:{hasta}", "per_page": 100})
        payload = self.parse_json(r)
        if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
            raise ValueError("El Banco Mundial no devolvió la serie de inflación")
        return RawCapture(fuente=self.fuente, url=r.url, contenido=r.content, formato="json", http_status=r.status_code,
                          registros=len(payload[1]), estado="ok",
                          metadatos={"etiqueta": f"ipc-mexico-{desde}-{hasta}", "fecha_ref_inicio": f"{desde}-01-01", "fecha_ref_fin": f"{hasta}-12-31",
                                     "indicador": "FP.CPI.TOTL", "nota": "Índice de precios al consumidor, 2010 = 100 (Banco Mundial)."})


def indice(bronze: Path) -> dict[int, float]:
    """Último índice anual capturado: {año: valor}."""
    rutas = sorted((bronze / "banco_mundial").rglob("ipc-mexico*.json") if (bronze / "banco_mundial").is_dir() else [],
                   key=lambda p: p.name.rsplit("__", 1)[-1])
    rutas = [p for p in rutas if not p.name.endswith(".meta.json")]
    if not rutas:
        rutas = sorted(p for p in (bronze / "banco_mundial").rglob("*.json") if not p.name.endswith(".meta.json")) if (bronze / "banco_mundial").is_dir() else []
    if not rutas:
        return {}
    datos = json.loads(rutas[-1].read_text(encoding="utf-8"))
    return {int(x["date"]): float(x["value"]) for x in datos[1] if x.get("value") is not None}


def a_pesos_de(indice_anual: dict[int, float], anio_base: int | None = None) -> dict[int, float]:
    """Factor por año para expresar precios en pesos de ``anio_base`` (por defecto el último disponible)."""
    if not indice_anual:
        return {}
    base = anio_base or max(indice_anual)
    return {a: indice_anual[base] / v for a, v in indice_anual.items()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--desde", type=int, default=2010)
    ap.add_argument("--hasta", type=int, default=date.today().year)
    a = ap.parse_args(argv)
    settings = get_settings()
    run_id = new_run_id()
    setup_logging(run_id, settings)
    cap = InflacionExtractor(settings).inpc(a.desde, a.hasta)
    saved = BronzeWriter(settings.bronze_dir).write(cap, run_id)
    print(json.dumps({"archivo": str(saved.ruta), "anios": len(indice(settings.bronze_dir))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
