"""Integración de la tubería completa con fuentes simuladas (FIXTURES, no datos reales)."""
import json
from datetime import date

from almacenamiento.bronze_writer import META_SUFFIX
from calidad.objetivos import evaluar_objetivos
from pipeline import capturar_clima, capturar_sniim, exit_code, meses, ultimos_36_meses
from scripts.validar_bronce import validar
from extractores.sniim_extractor import SniimExtractor
from extractores.weather_extractor import WeatherExtractor
from tests.conftest import FakeResponse, FakeSession
from tests.test_sniim import FORM, RESULTADOS, SIN
from tests.test_weather import payload


def test_meses_y_ultimos_36():
    assert meses(date(2025, 1, 15), date(2025, 3, 10)) == [(date(2025, 1, 15), date(2025, 1, 31)),
                                                          (date(2025, 2, 1), date(2025, 2, 28)),
                                                          (date(2025, 3, 1), date(2025, 3, 10))]
    ini, fin = ultimos_36_meses(date(2026, 11, 8))
    assert (ini, fin) == (date(2023, 11, 1), date(2026, 10, 31)) and len(meses(ini, fin)) == 36


def sniim_ext(settings, resultados):
    s = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "ConsultaFrutasYHortalizas.aspx": [FakeResponse(200, FORM)],
                     "ResultadosConsulta": resultados})
    return SniimExtractor(settings, session=s)


def test_sniim_exitosa_genera_bronce_manifiesto_y_valida(settings):
    ext = sniim_ext(settings, [FakeResponse(200, RESULTADOS)])
    m = capturar_sniim("RUNA", "diaria", [(date(2026, 3, 1), date(2026, 3, 31))], settings,
                       productos=["platano"], mercados=["guadalajara"], extractor=ext)
    assert m.estado == "exitosa" and m.registros == 4 and len(m.archivos) == 3  # formulario + 2 variantes
    assert exit_code([m]) == 0
    n, errores = validar(settings.bronze_dir)
    assert n == 3 and errores == []
    assert (settings.bronze_dir / "sniim" / "manifests" / "manifest_RUNA.json").is_file()


def test_sniim_fallo_se_refleja_en_estado(settings):
    ext = sniim_ext(settings, [FakeResponse(200, RESULTADOS), FakeResponse(500, b"x")])
    m = capturar_sniim("RUNB", "diaria", [(date(2026, 3, 1), date(2026, 3, 31))], settings,
                       productos=["platano"], mercados=["guadalajara"], extractor=ext)
    assert m.estado == "parcial" and m.errores and exit_code([m]) == 2


def test_robots_bloqueado_aborta_como_fallida(settings):
    s = FakeSession({"robots.txt": [FakeResponse(200, "User-agent: *\nDisallow: /\n")]})
    m = capturar_sniim("RUNC", "diaria", [(date(2026, 3, 1), date(2026, 3, 1))], settings, extractor=SniimExtractor(settings, session=s))
    assert m.estado == "fallida" and exit_code([m]) == 1 and not list(settings.bronze_dir.rglob("*.html"))


def test_sin_resultados_no_es_fallo(settings):
    ext = sniim_ext(settings, [FakeResponse(200, SIN)])
    m = capturar_sniim("RUND", "diaria", [(date(2026, 3, 7), date(2026, 3, 7))], settings,
                       productos=["papaya"], mercados=["cdmx"], extractor=ext)
    assert m.estado == "sin_resultados" and exit_code([m]) == 0


def test_clima_un_tramo_por_mes(settings):
    s = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "ncei.noaa.gov": [FakeResponse(200, json.dumps(payload(31)))]})
    ext = WeatherExtractor(settings, session=s)
    m = capturar_clima("RUNE", "historica", date(2025, 1, 1), date(2025, 2, 28), settings, ["manzanillo"], extractor=ext)
    assert len(m.consultas) == 2 and m.fuente == "noaa_ncei" and len(m.archivos) == 2


def test_respuesta_no_entendida_se_guarda_para_diagnostico(settings):
    raro = "<html><body><p>Error ASP.NET</p></body></html>"
    ext = sniim_ext(settings, [FakeResponse(200, raro)])
    m = capturar_sniim("RUNH", "diaria", [(date(2026, 3, 1), date(2026, 3, 1))], settings,
                       productos=["papaya"], mercados=["cdmx"], extractor=ext)
    assert m.estado == "fallida"
    guardados = list(settings.diagnostic_dir.glob("RUNH__*"))
    assert guardados and guardados[0].read_bytes() == raro.encode("utf-8")


def test_objetivos_sin_datos_no_inventa(settings):
    assert evaluar_objetivos(settings.bronze_dir, date(2026, 11, 1), date(2026, 11, 7))["estado"] == "sin_datos"


def test_objetivos_con_manifiestos_reales_simulados(settings):
    man_dir = settings.bronze_dir / "sniim" / "manifests"
    man_dir.mkdir(parents=True)
    for dia, estado, errs in [("2026-11-01", "exitosa", []), ("2026-11-02", "fallida", ["HTTP 500"]), ("2026-11-04", "exitosa", [])]:
        (man_dir / f"manifest_{dia}.json").write_text(json.dumps(
            {"fuente": "sniim", "modo": "diaria", "inicio": f"{dia}T03:00:00Z", "estado": estado, "run_id": dia,
             "errores": errs, "consultas": []}), encoding="utf-8")
    r = evaluar_objetivos(settings.bronze_dir, date(2026, 11, 1), date(2026, 11, 4))
    assert r["OQ1"]["valor"] == 66.67 and r["OQ1"]["cumple"] is False
    assert r["OQ2"]["dias_sin_manifiesto"] == 1 and r["OQ2"]["cumple"] is False  # 03/11 sin manifiesto
    assert r["OQ3"]["valor"] == 75.0 and r["ejecuciones_no_exitosas_identificadas"][0]["dia"] == "2026-11-02"


def test_sinteticos_solo_en_directorio_aparte(tmp_path, monkeypatch):
    monkeypatch.setenv("TDL_DATA_DIR", str(tmp_path / "data"))
    from scripts.generar_sinteticos import main
    assert main(["--dias", "2"]) == 0
    arch = list((tmp_path / "data" / "sintetico").glob("SINTETICO_*.csv"))
    assert arch and "es_sintetico" in arch[0].read_text(encoding="utf-8").splitlines()[0]
    assert not (tmp_path / "data" / "bronce").exists()


def test_bitacora_registra_cada_ejecucion_incluso_fallida(settings):
    import csv
    s = FakeSession({"robots.txt": [FakeResponse(200, "User-agent: *\nDisallow: /\n")]})
    capturar_sniim("RUNF", "diaria", [(date(2026, 3, 1), date(2026, 3, 1))], settings, extractor=SniimExtractor(settings, session=s))
    SniimExtractor.reset_shared_state()  # la caché de robots es compartida por proceso
    ext = sniim_ext(settings, [FakeResponse(200, RESULTADOS)])
    capturar_sniim("RUNG", "diaria", [(date(2026, 3, 1), date(2026, 3, 1))], settings, productos=["papaya"], mercados=["cdmx"], extractor=ext)
    filas = list(csv.DictReader(open(settings.bitacora_path, encoding="utf-8")))
    assert [f["run_id"] for f in filas] == ["RUNF", "RUNG"]
    assert filas[0]["estado"] == "fallida" and "robots" in filas[0]["primer_error"].lower()
    assert filas[1]["estado"] == "exitosa" and filas[1]["fuente"] == "sniim"
