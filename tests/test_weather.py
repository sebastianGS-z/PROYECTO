"""Pruebas del extractor NOAA NCEI con JSON FIXTURE (no es una captura real)."""
import json
from datetime import date

import pytest

from extractores.base import RobotsDisallowed, StructureChangedError
from extractores.weather_extractor import WeatherExtractor
from tests.conftest import FakeResponse, FakeSession

LOC = {"id": "manzanillo", "nombre": "Manzanillo", "estacion": "MXM00076654", "latitud": 19.14, "longitud": -104.56}
RUTA = "ncei.noaa.gov/access/services/data/v1"


def payload(dias=3):
    filas = [{"DATE": f"2025-01-{i + 1:02d}", "STATION": "MXM00076654", "TMAX": "31.0", "TMIN": "20.0", "PRCP": "0.0"} for i in range(dias)]
    filas[0]["TAVG"] = "25.1"  # TAVG solo existe un día: no se rellena en los demás
    return filas


def extractor(settings, body, robots=None):
    s = FakeSession({"robots.txt": [robots or FakeResponse(404, b"x")], RUTA: [FakeResponse(200, json.dumps(body))]})
    return WeatherExtractor(settings, session=s), s


def test_captura_arma_url_y_conserva_original(settings):
    e, s = extractor(settings, payload())
    cap = e.fetch(LOC, date(2025, 1, 1), date(2025, 1, 3))
    url = [u for _, u in s.llamadas if "startDate=" in u][0]
    for frag in ("dataset=daily-summaries", "stations=MXM00076654", "startDate=2025-01-01", "endDate=2025-01-03", "units=metric", "format=json"):
        assert frag in url
    assert cap.registros == 3 and cap.estado == "ok" and cap.fuente == "noaa_ncei"
    assert json.loads(cap.contenido)[1].get("TAVG") is None  # no se rellena
    assert any("TAVG" in a and "no se rellenan" in a for a in cap.advertencias)
    assert cap.metadatos["estacion"] == "MXM00076654"


def test_lista_vacia_es_sin_resultados(settings):
    e, _ = extractor(settings, [])
    cap = e.fetch(LOC, date(2025, 1, 1), date(2025, 1, 3))
    assert cap.estado == "sin_resultados" and cap.registros == 0


def test_estructura_invalida(settings):
    e, _ = extractor(settings, {"error": "x"})
    with pytest.raises(StructureChangedError):
        e.fetch(LOC, date(2025, 1, 1), date(2025, 1, 3))


def test_json_invalido(settings):
    s = FakeSession({"robots.txt": [FakeResponse(404, b"x")], RUTA: [FakeResponse(200, "<html>")]})
    with pytest.raises(StructureChangedError):
        WeatherExtractor(settings, session=s).fetch(LOC, date(2025, 1, 1), date(2025, 1, 3))


def test_robots_que_prohibe_la_ruta_detiene_la_captura(settings):
    robots = FakeResponse(200, "User-agent: *\nDisallow: /access/\n")
    e, s = extractor(settings, payload(), robots)
    with pytest.raises(RobotsDisallowed):
        e.fetch(LOC, date(2025, 1, 1), date(2025, 1, 3))
    assert not any("startDate=" in u for _, u in s.llamadas)
