"""Pruebas del portal (inicio y administración) y de la captura SIAP con respuestas HTTP FIXTURE."""
from __future__ import annotations

import json

import pandas as pd
import pytest

from scripts import capturar_siap as cs
from src.inteligencia import portal
from tests.conftest import FakeResponse, FakeSession

CSV_SIAP = "Anio,Idestado,Nomestado,Idmunicipio,Nommunicipio,Nomunidad,Nomcultivo,Sembrada,Cosechada,Volumenproduccion,Valorproduccion\n2020,6,Colima,9,Tecomán,Tonelada,Limón,10,10,100,700000\n"


def test_captura_siap_guarda_y_omite_repetidos(settings):
    s = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "ANIO=2020": [FakeResponse(200, CSV_SIAP.encode("cp1252"))]})
    r = cs.capturar([2020], settings, extractor=cs.SiapExtractor(settings, session=s))
    assert r["estado"] == "exitosa"
    assert cs.ya_capturados(settings.bronze_dir) == {2020}
    otra = cs.capturar([2020], settings, extractor=cs.SiapExtractor(settings, session=s))
    assert otra["consultas"][0]["estado"] == "omitida"


def test_captura_siap_rechaza_respuesta_que_no_es_csv(settings):
    s = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "ANIO=2019": [FakeResponse(200, b"<html>mantenimiento</html>")]})
    r = cs.capturar([2019], settings, extractor=cs.SiapExtractor(settings, session=s))
    assert r["estado"] == "fallida" and "no es el CSV" in r["consultas"][0]["error"]


@pytest.fixture
def base(tmp_path):
    (tmp_path / "data/publico").mkdir(parents=True)
    (tmp_path / "data/plata").mkdir(parents=True)
    (tmp_path / "calidad/reportes").mkdir(parents=True)
    (tmp_path / "tablero").mkdir()
    bronce = tmp_path / "data/bronce/sniim/2026/11"
    bronce.mkdir(parents=True)
    (bronce / "sniim__x__2026-11-01_2026-11-01__20261127T000000Z-aaaaaa.html").write_text("<table></table>")
    pd.DataFrame([{"cultivo": "limon", "horizonte_meses": 1, "tipo_serie": "origen_colima", "nombre_mercado": "GDL", "fecha_pronostico": "2026-11",
                   "precio_frecuente_mxn_kg": 21.0, "li80_mxn_kg": 15.0, "ls80_mxn_kg": 27.0, "variante": "Limón #5", "modelo_elegido": "arima_aic",
                   "meses_entrenamiento": 36, "mape_backtest_pct": 15.0, "cobertura_80_holdout": 0.8, "fecha_ultimo_dato": "2026-10"}]).to_csv(tmp_path / "data/publico/pronosticos_colima.csv", index=False)
    pd.DataFrame([{"cultivo": "limon", "ultimo_mes": "2026-10", "ultimo_precio_mxn_kg": 23.0, "percentil_historico": 44, "meses_historia": 36}]).to_csv(
        tmp_path / "data/publico/senales_mercado.csv", index=False)
    (tmp_path / "data/publico/preguntas_productor.json").write_text(json.dumps({"respuestas": {"limon": [{"pregunta": "¿A cuánto ... el próximo mes?", "confianza": "media"}]}}))
    (tmp_path / "data/publico/inteligencia.json").write_text(json.dumps({"hallazgos": ["Hallazgo X"]}))
    (tmp_path / "calidad/reportes/fiabilidad.json").write_text(json.dumps({
        "generado_utc": "2026-11-27T00:00:00Z", "periodos": {"ventana_sello_14_dias": {"disponibilidad": 0.9, "dias": 14, "n_fallas": 1, "mttr_h": 24, "hasta": "2026-11-27"}},
        "frescura": {"alertas": ["noaa: sin datos"]}, "por_fuente": {"sniim": {"ejecuciones": 3, "tasa_exito_tecnico": 1.0, "tasa_con_datos_nuevos": 0.5,
                                                                              "ultimo_dia_con_datos_nuevos": "2026-11-26", "duracion_s_mediana": 90}},
        "puntualidad_schedule": {"retraso_h_mediana": 8}, "detalle_diario": [{"dia": "2026-11-26", "operativo": True, "estados": {}},
                                                                              {"dia": "2026-11-27", "operativo": False, "estados": {}}]}))
    (tmp_path / "calidad/reportes/iso25012.json").write_text(json.dumps({"medidas": {"completitud": {"valor": 1.0, "definicion": "x"}}}))
    (tmp_path / "data/plata/reporte_calidad.json").write_text(json.dumps({"registros_bronce_parseados": 100, "registros_plata_validos": 90, "registros_cuarentena": 2,
                                                                           "registros_rechazados_por_reglas": 2, "registros_duplicados_descartados": 8, "filas_oro": 10}))
    return tmp_path


def test_inicio_muestra_productos_y_confianza(base):
    pagina = portal.inicio(base)
    assert "Limón" in pagina and "21.00 MXN/kg" in pagina and "15.00 – 27.00" in pagina and "Confianza media" in pagina
    assert "Hallazgo X" in pagina and "90 %" in pagina and "sin serie elegible" in pagina  # papaya sin pronóstico


def test_admin_levanta_alertas_y_contabilidad(base):
    pagina = portal.admin(base)
    assert "noaa: sin datos" in pagina and "por debajo del objetivo" in pagina and "2 registros en cuarentena" in pagina
    assert "Versiones duplicadas descartadas" in pagina and 'class="dia bad"' in pagina
    inv = portal.inventario_bronce(base)
    assert inv.iloc[0]["fuente"] == "sniim" and inv.iloc[0]["archivos"] == 1
    assert portal.ejecutar(base) and (base / "tablero/admin.html").is_file()
