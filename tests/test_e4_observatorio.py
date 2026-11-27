from datetime import date

import pandas as pd

from src.tdl_e1.pipeline import _peso_presentacion_kg
from src.tdl_e4.observatorio import MARKET_NAMES, _market_id, generar_observatorio


def test_presentacion_only_converts_explicit_kg_weights():
    assert _peso_presentacion_kg("Kilogramo") == (1.0, "kilogramo_reportado_por_sniim")
    assert _peso_presentacion_kg("Caja de 15 kg.") == (15.0, "peso_explicito_en_presentacion_sniim")
    assert _peso_presentacion_kg("Arpilla de 19 kg.") == (19.0, "peso_explicito_en_presentacion_sniim")
    assert _peso_presentacion_kg("Ciento") == (None, "sin_peso_verificable")
    assert _market_id(140.0) == "140"
    assert MARKET_NAMES["140"] == "Guadalajara · Mercado de Abasto"
    assert MARKET_NAMES["100"] == "CDMX · Central de Abasto de Iztapalapa"


def test_observatorio_emits_walk_forward_forecast_and_dashboard(tmp_path):
    months = pd.date_range("2023-01-01", periods=36, freq="MS")
    gold = pd.DataFrame({
        "cultivo": "limon", "variante_id": "421", "variante": "Limón c/semilla #5",
        "origen": "Colima", "mercado": "140", "fecha_mes": months,
        "presentacion": "Caja de 15 kg.", "precio_frecuente_kg_mean": [20 + i * 0.1 for i in range(36)],
        "precio_frecuente_kg_count": 20, "linaje_precios_bronce": '[{"archivo":"bronce.html","sha256":"' + "a" * 64 + '","registro":1,"ingesta_utc":"2026-01-01T00:00:00Z"}]',
    })
    gold_path = tmp_path / "oro.csv"
    gold.to_csv(gold_path, index=False)
    report = generar_observatorio(
        gold_path=gold_path, output_dir=tmp_path / "oro", public_dir=tmp_path / "publico",
        dashboard_path=tmp_path / "tablero" / "index.html", horizon=3, as_of_date=date(2026, 1, 20),
    )
    forecast = pd.read_csv(tmp_path / "oro" / "pronosticos_colima.csv")
    assert report["series_pronosticadas"] == 1
    assert forecast["fecha_pronostico"].tolist() == ["2026-01", "2026-02", "2026-03"]
    assert forecast["precio_frecuente_mxn_kg"].notna().all()
    assert forecast["linaje_serie_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert report["comparaciones_pareadas"] == 0
    metrics = pd.read_csv(tmp_path / "oro" / "metricas_backtest_colima.csv")
    assert set(metrics["n_validaciones"]) == {6}
    assert set(metrics["segmento"]) == {"seleccion", "holdout"}
    assert metrics.groupby("segmento")["modelo_elegido"].sum().to_dict() == {"holdout": 1, "seleccion": 1}
    holdout = metrics[metrics["segmento"].eq("holdout") & metrics["modelo_elegido"]].iloc[0]
    assert forecast["mae_backtest_mxn_kg"].eq(holdout["mae_mxn_kg"]).all()
    validations = pd.read_csv(tmp_path / "oro" / "validaciones_pronostico_colima.csv")
    selection_months = set(validations[validations["segmento"].eq("seleccion")]["mes_validacion"])
    holdout_months = set(validations[validations["segmento"].eq("holdout")]["mes_validacion"])
    assert selection_months.isdisjoint(holdout_months)
    comparison = pd.read_csv(tmp_path / "oro" / "comparativa_mercados_colima.csv")
    assert comparison.iloc[0]["estado_comparacion"] == "sin_dos_mercados_con_origen_variante_y_mes_comunes"
    assert (tmp_path / "publico" / "panel_mensual_actual.csv").is_file()
    dashboard = (tmp_path / "tablero" / "index.html").read_text(encoding="utf-8")
    assert "Estimaciones mensuales" in dashboard
    assert "MXN / kg" in dashboard
    assert "Comportamiento de precios" in dashboard
    assert "data-range=\"24\"" in dashboard
    assert "Evaluación de modelos" in dashboard
    assert "Calidad y trazabilidad" in dashboard
    assert "function renderChart()" in dashboard
    assert 'id="fallback-data"' in dashboard
    assert "Estimaciones de precio" in dashboard
    assert "__FALLBACK__" not in dashboard
    assert "diferencia_mxn_kg\": NaN" not in dashboard
