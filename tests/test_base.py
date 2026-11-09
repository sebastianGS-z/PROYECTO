import pytest
import requests

from extractores.base import (BaseExtractor, EmptyResponseError, HttpError, RequestFailed,
                              RobotsDisallowed, RobotsUnavailable)
from tests.conftest import ROBOTS_OK, FakeResponse, FakeSession

URL = "https://ejemplo.mx/datos"


def ext(settings, rutas):
    s = FakeSession({"robots.txt": [ROBOTS_OK], **rutas})
    return BaseExtractor(settings, session=s), s


def test_user_agent_configurado(settings):
    e, s = ext(settings, {"/datos": [FakeResponse(200, b"ok")]})
    assert s.headers["User-Agent"] == "TDL-Observatorio/1.0 (proyecto academico; contacto: equipo@correo.mx)"


def test_lee_robots_y_bloquea_ruta_prohibida(settings):
    e, s = ext(settings, {"/privado": [FakeResponse(200, b"x")]})
    assert e.can_fetch("https://ejemplo.mx/datos") is True
    with pytest.raises(RobotsDisallowed):
        e.get("https://ejemplo.mx/privado/x")
    assert not any("/privado" in u for _, u in s.llamadas if "robots" not in u)


def test_robots_inaccesible_no_hace_scraping(settings):
    s = FakeSession({"robots.txt": [FakeResponse(503, b"x")], "/datos": [FakeResponse(200, b"ok")]})
    e = BaseExtractor(settings, session=s)
    with pytest.raises(RobotsUnavailable):
        e.get(URL)
    assert not any(u.endswith("/datos") for _, u in s.llamadas)


def test_robots_403_se_trata_como_denegado(settings):
    s = FakeSession({"robots.txt": [FakeResponse(403, b"x")], "/datos": [FakeResponse(200, b"ok")]})
    with pytest.raises(RobotsDisallowed):
        BaseExtractor(settings, session=s).get(URL)


def test_robots_404_permite(settings):
    s = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "/datos": [FakeResponse(200, b"ok")]})
    assert BaseExtractor(settings, session=s).get(URL).status_code == 200


def test_pausa_minima_entre_peticiones(settings, reloj):
    e, _ = ext(settings, {"/datos": [FakeResponse(200, b"ok")]})
    e.get(URL); e.get(URL)
    assert any(p >= 1.5 - 1e-9 for p in reloj["pausas"])


def test_pausa_compartida_entre_instancias(settings, reloj):
    e1, _ = ext(settings, {"/datos": [FakeResponse(200, b"ok")]})
    e2, _ = ext(settings, {"/datos": [FakeResponse(200, b"ok")]})
    e1.get(URL)
    antes = len(reloj["pausas"])
    e2.get(URL)  # otra instancia, mismo dominio: debe esperar
    assert len(reloj["pausas"]) > antes and reloj["pausas"][-1] > 0


def test_respeta_crawl_delay(settings, reloj):
    s = FakeSession({"robots.txt": [FakeResponse(200, "User-agent: *\nCrawl-delay: 4\n")], "/datos": [FakeResponse(200, b"ok")]})
    e = BaseExtractor(settings, session=s)
    e.get(URL); e.get(URL)
    assert max(reloj["pausas"]) >= 3.9


def test_reintentos_con_backoff_exponencial(settings, reloj):
    e, s = ext(settings, {"/datos": [FakeResponse(503, b"x"), requests.ConnectionError("caído"), FakeResponse(200, b"ok")]})
    assert e.get(URL).content == b"ok"
    assert e.stats["reintentos"] == 2
    assert 1.0 in reloj["pausas"] and 2.0 in reloj["pausas"]


def test_agota_reintentos(settings):
    e, s = ext(settings, {"/datos": [FakeResponse(500, b"x")]})
    with pytest.raises(RequestFailed):
        e.get(URL)
    assert sum(1 for _, u in s.llamadas if u.endswith("/datos")) == settings.max_retries + 1


def test_error_http_no_recuperable_no_reintenta(settings):
    e, s = ext(settings, {"/datos": [FakeResponse(404, b"nada")]})
    with pytest.raises(HttpError) as exc:
        e.get(URL)
    assert exc.value.status == 404
    assert sum(1 for _, u in s.llamadas if u.endswith("/datos")) == 1


def test_timeout_se_reintenta(settings):
    e, _ = ext(settings, {"/datos": [requests.Timeout("lento"), FakeResponse(200, b"ok")]})
    assert e.get(URL).status_code == 200


def test_respuesta_vacia_se_rechaza(settings):
    e, _ = ext(settings, {"/datos": [FakeResponse(200, b"   ")]})
    with pytest.raises(EmptyResponseError):
        e.get(URL)
