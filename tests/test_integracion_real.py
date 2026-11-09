"""Pruebas contra servicios REALES. Se omiten por defecto.

    RUN_INTEGRATION=1 python -m pytest -m integration -s
Requieren red. Respetan robots.txt y pausas como cualquier captura.
"""
import os
from datetime import date, timedelta

import pytest

from config.settings import cargar_localidades, get_settings
from extractores.sniim_extractor import SniimExtractor
from extractores.weather_extractor import WeatherExtractor

pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1", reason="defina RUN_INTEGRATION=1")]


def test_noaa_ncei_real_una_semana():
    cap = WeatherExtractor(get_settings()).fetch(cargar_localidades()["manzanillo"], date(2024, 1, 1), date(2024, 1, 7))
    print("NOAA NCEI:", cap.estado, cap.registros, cap.advertencias)
    assert cap.http_status == 200 and cap.estado in ("ok", "sin_resultados")


def test_sniim_real_formulario_y_una_consulta():
    e = SniimExtractor(get_settings())
    e.cargar_catalogo()
    assert e.variantes("Plátano") and e.variantes("Limón") and e.variantes("Papaya")
    variante = next(v for v in e.variantes("Papaya") if "Maradol" in v.etiqueta)
    fin = date.today() - timedelta(days=3)
    cap = e.fetch_precios(variante, "DF: Central de Abasto de Iztapalapa DF", fin - timedelta(days=10), fin)
    print("SNIIM real:", variante.etiqueta, cap.estado, cap.registros, cap.url)
    assert cap.estado in ("ok", "sin_resultados", "parcial")
