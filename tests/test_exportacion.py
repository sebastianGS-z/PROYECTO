"""Pruebas de mercados extranjeros (UN Comtrade + tipo de cambio) con respuestas FIXTURE."""
from __future__ import annotations

import json

import pandas as pd

from scripts import capturar_comtrade as cc
from src.inteligencia import exportacion as ex
from tests.conftest import FakeResponse, FakeSession


def _payload(filas):
    return json.dumps({"count": len(filas), "data": filas})


def test_captura_comtrade_y_tipo_de_cambio(settings):
    fx = json.dumps({"rates": {"2024-01-02": {"MXN": 17.0}, "2024-01-03": {"MXN": 18.0}}})
    s_fx = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "frankfurter": [FakeResponse(200, fx)]})
    datos = _payload([{"refYear": 2024, "reporterCode": 842, "partnerCode": 484, "primaryValue": 1000.0, "netWgt": 500.0}])
    s_ct = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "comtradeapi": [FakeResponse(200, datos)]})
    r = cc.capturar([2024], codigos=["080550"], tipos=["destinos_mexico"], settings=settings,
                    extractor=cc.ComtradeExtractor(settings, session=s_ct), fx=cc.TipoCambioExtractor(settings, session=s_fx))
    assert r["tipo_cambio"][0]["estado"] == "ok" and r["comtrade"][0]["estado"] == "ok"
    assert ex.tipo_cambio(settings.bronze_dir) == {2024: 17.5}
    reg = ex.registros(settings.bronze_dir)
    assert len(reg) == 1 and reg.iloc[0]["reporter"] == 842
    # segunda corrida: no repite lo ya capturado
    r2 = cc.capturar([2024], codigos=["080550"], tipos=["destinos_mexico"], settings=settings,
                     extractor=cc.ComtradeExtractor(settings, session=s_ct), fx=cc.TipoCambioExtractor(settings, session=s_fx))
    assert r2["comtrade"] == [] and r2["tipo_cambio"] == []


def test_captura_se_detiene_con_429(settings):
    s_fx = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "frankfurter": [FakeResponse(200, json.dumps({"rates": {"d": {"MXN": 17}}}))]})
    s_ct = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "comtradeapi": [FakeResponse(429, b"too many")]})
    r = cc.capturar([2023, 2024], codigos=["080550"], tipos=["destinos_mexico"], settings=settings,
                    extractor=cc.ComtradeExtractor(settings, session=s_ct), fx=cc.TipoCambioExtractor(settings, session=s_fx))
    assert r.get("detenido_por_cuota") is True


def test_destinos_participacion_y_conversion():
    reg = pd.DataFrame([
        {"tipo": "destinos_mexico", "codigo_hs": "080550", "anio": 2024, "reporter": 842, "partner": 484, "valor_usd": 800.0, "kg": 400.0},
        {"tipo": "importadores_mundo", "codigo_hs": "080550", "anio": 2024, "reporter": 842, "partner": 0, "valor_usd": 1000.0, "kg": 500.0},
        {"tipo": "importadores_mundo", "codigo_hs": "080550", "anio": 2024, "reporter": 276, "partner": 0, "valor_usd": 900.0, "kg": 300.0},
        {"tipo": "importadores_mundo", "codigo_hs": "080550", "anio": 2024, "reporter": 0, "partner": 0, "valor_usd": 9e9, "kg": 1.0},
    ])
    d = ex.destinos(reg, {842: "USA", 276: "Germany"}, {2024: 18.0}).set_index("pais")
    assert "Área 0" not in d.index  # el agregado "mundo" se excluye
    assert d.loc["USA", "iso_numerico"] == 840 and d.loc["USA", "participacion_mexico_pct"] == 80.0
    assert d.loc["USA", "mxn_kg_desde_mexico"] == 36.0
    assert d.loc["Germany", "valor_usd"] == 0 and d.loc["Germany", "participacion_mexico_pct"] == 0


def test_resumen_detecta_oportunidad_y_prima(tmp_path):
    filas = [{"codigo_hs": "080440", "anio": 2024, "reporter": 842, "valor_usd": 5e9, "kg": 1e9, "mundo_usd": 6e9, "mundo_kg": 1.2e9}]
    for i, iso in enumerate(range(100, 110)):
        filas.append({"codigo_hs": "080440", "anio": 2024, "reporter": iso, "valor_usd": 0.0, "kg": 0.0, "mundo_usd": 1e8 * (i + 1), "mundo_kg": 1e7})
    base = pd.DataFrame(filas)
    base["pais"] = base["reporter"].map(lambda c: "USA" if c == 842 else f"P{c}")
    base["iso_numerico"] = base["reporter"].map(lambda c: ex.M49_A_ISO.get(c, c))
    base["usd_kg_desde_mexico"] = (base["valor_usd"] / base["kg"]).where(base["kg"] > 0)
    base["usd_kg_mundo"] = base["mundo_usd"] / base["mundo_kg"]
    base["tipo_cambio_usd_mxn"] = 18.0
    base["mxn_kg_desde_mexico"] = base["usd_kg_desde_mexico"] * 18
    base["participacion_mexico_pct"] = base["valor_usd"] / base["mundo_usd"] * 100
    (tmp_path / "data/oro").mkdir(parents=True)
    pd.DataFrame([{"cultivo": "aguacate_hass", "origen": "Michoacán", "fecha_mes": "2026-10-01", "precio_frecuente_kg_mean": 45.0,
                   "precio_frecuente_kg_count": 10}]).to_csv(tmp_path / "data/oro/panel_mensual.csv", index=False)
    r = ex.resumen(tmp_path, base)["aguacate"]
    assert r["disponible"] and r["destinos"][0]["pais"] == "USA" and r["valor_unitario_exportacion_mxn_kg"] == 90.0
    assert r["prima_exportacion_pct"] == 100.0 and r["base_precio_nacional"] == "todos los orígenes"
    assert r["oportunidades"] and r["oportunidades"][0]["pais"] == "P109"
    assert ex.resumen(tmp_path, base)["guanabana"]["disponible"] is False
