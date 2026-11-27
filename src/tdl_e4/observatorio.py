"""Pronóstico y comparación acotados a series SNIIM de origen Colima.

Los modelos se evalúan con origen móvil antes de ajustarse al historial completo.
No se rellenan meses ausentes y no se emite pronóstico cuando la cobertura no
alcanza el mínimo declarado.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import shutil
import warnings
from datetime import date
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing, Holt, SimpleExpSmoothing

from config.settings import BASE_DIR

LOG = logging.getLogger("tdl.e4")
KEYS = ["cultivo", "variante_id", "variante", "origen"]
MIN_MONTHS = 36
SELECTION_STEPS = 6
HOLDOUT_STEPS = 6
MODEL_NAMES = ("suavizamiento_simple", "holt", "holt_winters_aditivo", "arima_111")
MARKET_NAMES = {
    "80": "Colima · Centros de distribución",
    "100": "CDMX · Central de Abasto de Iztapalapa",
    "140": "Guadalajara · Mercado de Abasto",
    "141": "Guadalajara · Mercado Felipe Ángeles",
    "160": "Morelia · Mercado de Abasto",
    "180": "Tepic · Mercado Adolfo López Mateos",
    "181": "Tepic · Nayarabastos",
}


def _market_id(value: Any) -> str:
    try:
        number = float(value)
        if math.isfinite(number) and number.is_integer():
            return str(int(number))
    except (TypeError, ValueError):
        pass
    return str(value)


def _fit_predict(model: str, values: np.ndarray, steps: int) -> np.ndarray:
    series = pd.Series(values, dtype="float64")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if model == "suavizamiento_simple":
            fitted = SimpleExpSmoothing(series, initialization_method="estimated").fit(optimized=True)
        elif model == "holt":
            fitted = Holt(series, initialization_method="estimated").fit(optimized=True)
        elif model == "holt_winters_aditivo":
            if len(series) < 24:
                raise ValueError("Holt-Winters requiere al menos dos ciclos mensuales completos")
            fitted = ExponentialSmoothing(
                series, trend="add", seasonal="add", seasonal_periods=12,
                initialization_method="estimated",
            ).fit(optimized=True, use_brute=False)
        elif model == "arima_111":
            fitted = ARIMA(series, order=(1, 1, 1), trend="t",
                           enforce_stationarity=False, enforce_invertibility=False).fit()
        else:
            raise ValueError(f"Modelo no soportado: {model}")
    forecast = np.asarray(fitted.forecast(steps=steps), dtype="float64")
    if len(forecast) != steps or not np.isfinite(forecast).all():
        raise ValueError("el modelo devolvió pronósticos no finitos")
    return forecast


def _score(actual: list[float], predicted: list[float]) -> dict[str, float]:
    error = np.asarray(predicted, dtype="float64") - np.asarray(actual, dtype="float64")
    denom = np.abs(np.asarray(actual, dtype="float64"))
    mape = float(np.mean(np.abs(error[denom > 0] / denom[denom > 0])) * 100) if (denom > 0).any() else math.nan
    return {"mae_mxn_kg": float(np.mean(np.abs(error))),
            "rmse_mxn_kg": float(np.sqrt(np.mean(np.square(error)))), "mape_pct": mape}


def _mensual_colima(gold: pd.DataFrame, origen_objetivo: str | None = "Colima") -> pd.DataFrame:
    required = {"cultivo", "variante_id", "variante", "origen", "mercado", "fecha_mes",
                "precio_frecuente_kg_mean", "precio_frecuente_kg_count", "presentacion",
                "linaje_precios_bronce"}
    missing = required - set(gold.columns)
    if missing:
        raise ValueError("Faltan columnas en Oro: " + ", ".join(sorted(missing)))
    df = gold.copy()
    df["fecha_mes"] = pd.to_datetime(df["fecha_mes"], errors="coerce")
    df["mercado"] = df["mercado"].map(_market_id).astype("string")
    df["origen"] = df["origen"].astype("string")
    df = df[df["origen"].notna()].copy()
    if origen_objetivo is not None:
        df = df[df["origen"].str.casefold().eq(origen_objetivo.casefold())].copy()
    df = df[df["precio_frecuente_kg_mean"].notna() & df["precio_frecuente_kg_count"].fillna(0).gt(0)]
    df["_valor_ponderado"] = df["precio_frecuente_kg_mean"] * df["precio_frecuente_kg_count"]
    group = [*KEYS, "mercado", "fecha_mes"]
    aggregations: dict[str, tuple[str, Any]] = {
        "_valor_ponderado": ("_valor_ponderado", "sum"),
        "n_observaciones": ("precio_frecuente_kg_count", "sum"),
        "presentaciones": ("presentacion", lambda s: " | ".join(sorted({str(x) for x in s.dropna()}))),
    }
    if "linaje_precios_bronce" in df:
        aggregations["linaje_mes_sha256"] = (
            "linaje_precios_bronce",
            lambda s: hashlib.sha256("\n".join(sorted(str(x) for x in s.dropna())).encode("utf-8")).hexdigest(),
        )
    monthly = df.groupby(group, dropna=False, as_index=False).agg(**aggregations)
    monthly["precio_frecuente_kg"] = monthly["_valor_ponderado"] / monthly["n_observaciones"]
    monthly["mes"] = monthly["fecha_mes"].dt.to_period("M")
    return monthly.drop(columns="_valor_ponderado")


def _backtest(series: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    values = series.to_numpy(dtype="float64")
    selection_start = len(values) - SELECTION_STEPS - HOLDOUT_STEPS
    holdout_start = len(values) - HOLDOUT_STEPS
    if selection_start < 24:
        return pd.DataFrame(), pd.DataFrame()
    rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for model in MODEL_NAMES:
        for segment, splits in (
            ("seleccion", range(selection_start, holdout_start)),
            ("holdout", range(holdout_start, len(values))),
        ):
            actuals: list[float] = []
            predicted: list[float] = []
            failures = []
            for split in splits:
                try:
                    pred = float(_fit_predict(model, values[:split], 1)[0])
                    actual = float(values[split])
                    actuals.append(actual)
                    predicted.append(pred)
                    predictions.append({"segmento": segment, "modelo": model,
                                        "mes_validacion": str(series.index[split]),
                                        "real_mxn_kg": actual, "pronostico_mxn_kg": pred,
                                        "error_mxn_kg": pred - actual})
                except Exception as exc:  # un modelo que no converge no bloquea los demás
                    failures.append(f"{series.index[split]}: {type(exc).__name__}: {exc}")
            if len(actuals) >= 4:
                rows.append({"segmento": segment, "modelo": model,
                             **_score(actuals, predicted), "n_validaciones": len(actuals),
                             "errores_ajuste": " | ".join(failures)})
    return pd.DataFrame(rows), pd.DataFrame(predictions)


def _comparar_mercados(monthly: pd.DataFrame) -> pd.DataFrame:
    columns = [*KEYS, "meses_comunes", "mercados_observados", "mercado_con_mayor_precio_medio",
               "diferencia_mxn_kg", "estado_comparacion"]
    rows = []
    for key, group in monthly.groupby(KEYS, dropna=False):
        by_market = group.pivot_table(index="mes", columns="mercado", values="precio_frecuente_kg", aggfunc="mean")
        markets = [str(x) for x in by_market.columns]
        common = by_market.dropna()
        base = dict(zip(KEYS, key if isinstance(key, tuple) else (key,), strict=True))
        if len(markets) < 2 or common.empty:
            rows.append(base | {"meses_comunes": int(len(common)),
                                "mercados_observados": " | ".join(MARKET_NAMES.get(x, x) for x in markets),
                                "mercado_con_mayor_precio_medio": "",
                                "diferencia_mxn_kg": np.nan,
                                "estado_comparacion": "sin_dos_mercados_con_origen_variante_y_mes_comunes"})
            continue
        means = common.mean(axis=0).sort_values(ascending=False)
        rows.append(base | {"meses_comunes": int(len(common)),
                            "mercados_observados": " | ".join(MARKET_NAMES.get(str(x), str(x)) for x in means.index),
                            "mercado_con_mayor_precio_medio": MARKET_NAMES.get(str(means.index[0]), str(means.index[0])),
                            "diferencia_mxn_kg": float(means.iloc[0] - means.iloc[-1]),
                            "estado_comparacion": "comparacion_descriptiva_meses_pareados"})
    return pd.DataFrame(rows, columns=columns)


def generar_observatorio(gold_path: Path | None = None, output_dir: Path | None = None,
                         public_dir: Path | None = None, dashboard_path: Path | None = None,
                         horizon: int = 3, as_of_date: date | None = None) -> dict[str, Any]:
    if not 1 <= horizon <= 12:
        raise ValueError("El horizonte debe estar entre 1 y 12 meses")
    gold_path = gold_path or BASE_DIR / "data/oro/panel_mensual.csv"
    output_dir = output_dir or BASE_DIR / "data/oro"
    public_dir = public_dir or BASE_DIR / "data/publico"
    dashboard_path = dashboard_path or BASE_DIR / "tablero/index.html"
    gold = pd.read_csv(gold_path)
    current_month = pd.Timestamp(as_of_date or pd.Timestamp.now(tz=ZoneInfo("America/Mexico_City")).date()).to_period("M")
    last_closed_month = current_month - 1
    monthly_all = _mensual_colima(gold)
    monthly = monthly_all[monthly_all["mes"].le(last_closed_month)].copy()
    forecast_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    history_rows: list[dict[str, Any]] = []
    eligibility: list[dict[str, Any]] = []
    series_keys = [*KEYS, "mercado"]
    for key, group in monthly.groupby(series_keys, dropna=False):
        group = group.sort_values("mes").drop_duplicates("mes", keep="last")
        periods = pd.period_range(group["mes"].min(), group["mes"].max(), freq="M")
        indexed = group.set_index("mes")["precio_frecuente_kg"].reindex(periods)
        meta = dict(zip(series_keys, key if isinstance(key, tuple) else (key,), strict=True))
        meta["nombre_mercado"] = MARKET_NAMES.get(str(meta["mercado"]), str(meta["mercado"]))
        # Retenemos observaciones reales aunque la cobertura todavía no alcance
        # el umbral de pronóstico. Esto permite mostrar nuevos cultivos con su
        # estado de cobertura explícito, sin completar meses faltantes.
        for period, price in indexed.dropna().items():
            history_rows.append(meta | {"fecha": str(period), "precio_frecuente_mxn_kg": float(price)})
        if len(indexed) < MIN_MONTHS or indexed.isna().any():
            eligibility.append(meta | {"meses": int(len(indexed)), "pronosticable": False,
                                       "motivo": "requiere_36_meses_contiguos_sin_imputacion"})
            continue
        score_table, predictions = _backtest(indexed)
        if score_table.empty:
            eligibility.append(meta | {"meses": int(len(indexed)), "pronosticable": False,
                                       "motivo": "ningun_modelo_obtuvo_validaciones_suficientes"})
            continue
        selection_scores = score_table[score_table["segmento"].eq("seleccion")].sort_values(
            ["mae_mxn_kg", "rmse_mxn_kg"], kind="stable")
        holdout_scores = score_table[score_table["segmento"].eq("holdout")]
        if selection_scores.empty:
            eligibility.append(meta | {"meses": int(len(indexed)), "pronosticable": False,
                                       "motivo": "sin_modelo_con_validacion_de_seleccion"})
            continue
        winner = str(selection_scores.iloc[0]["modelo"])
        winner_holdout = holdout_scores[holdout_scores["modelo"].eq(winner)]
        if winner_holdout.empty:
            eligibility.append(meta | {"meses": int(len(indexed)), "pronosticable": False,
                                       "motivo": "modelo_elegido_sin_resultado_holdout"})
            continue
        winner_holdout = winner_holdout.iloc[0]
        try:
            future = _fit_predict(winner, indexed.to_numpy(dtype="float64"), horizon)
        except Exception as exc:
            eligibility.append(meta | {"meses": int(len(indexed)), "pronosticable": False,
                                       "motivo": f"fallo_ajuste_final_{type(exc).__name__}"})
            continue
        metric_table = score_table.assign(**meta, modelo_elegido=score_table["modelo"].eq(winner))
        metric_rows.extend(metric_table.to_dict("records"))
        if not predictions.empty:
            predictions = predictions.assign(**meta)
            validation_rows.extend(predictions.to_dict("records"))
        last = periods[-1]
        selection_start = len(periods) - SELECTION_STEPS - HOLDOUT_STEPS
        holdout_start = len(periods) - HOLDOUT_STEPS
        selection_first_month = str(periods[selection_start])
        selection_last_month = str(periods[holdout_start - 1])
        holdout_first_month = str(periods[holdout_start])
        holdout_last_month = str(periods[-1])
        input_lineage = ""
        if "linaje_mes_sha256" in group:
            lineage_rows = group.sort_values("mes")[["mes", "linaje_mes_sha256"]].to_dict("records")
            input_lineage = hashlib.sha256(json.dumps(lineage_rows, ensure_ascii=False, default=str,
                                                       sort_keys=True).encode("utf-8")).hexdigest()
        for step, point in enumerate(future, start=1):
            forecast_rows.append(meta | {
                "modelo_elegido": winner, "meses_entrenamiento": int(len(indexed)),
                "fecha_pronostico": str(last + step), "horizonte_meses": step,
                "precio_frecuente_mxn_kg": max(0.0, float(point)),
                "mae_backtest_mxn_kg": float(winner_holdout["mae_mxn_kg"]),
                "rmse_backtest_mxn_kg": float(winner_holdout["rmse_mxn_kg"]),
                "mape_backtest_pct": float(winner_holdout["mape_pct"]),
                "n_validaciones": int(winner_holdout["n_validaciones"]),
                "n_validaciones_seleccion": int(selection_scores.iloc[0]["n_validaciones"]),
                "fecha_inicio_holdout": holdout_first_month,
                "fecha_fin_holdout": holdout_last_month,
                "fecha_primer_dato": str(periods[0]), "linaje_serie_sha256": input_lineage,
                "fecha_ultimo_dato": str(last),
                "nota": "estimacion puntual; sin garantia; validar antes de uso comercial",
            })
        eligibility.append(meta | {"meses": int(len(indexed)), "pronosticable": True,
                                   "modelo_elegido": winner,
                                   "n_validaciones_seleccion": int(selection_scores.iloc[0]["n_validaciones"]),
                                   "n_validaciones_holdout": int(winner_holdout["n_validaciones"]),
                                   "periodo_seleccion": [selection_first_month, selection_last_month],
                                   "periodo_holdout": [holdout_first_month, holdout_last_month],
                                   "fecha_primer_dato": str(periods[0]), "fecha_ultimo_dato": str(periods[-1]),
                                   "linaje_serie_sha256": input_lineage})

    forecasts = pd.DataFrame(forecast_rows)
    metrics = pd.DataFrame(metric_rows)
    backtest = pd.DataFrame(validation_rows)
    comparisons = _comparar_mercados(monthly)
    # La vista de cliente también puede explorar precios de otros orígenes y plazas.
    # El modelado predictivo se mantiene restringido al origen Colima.
    client_monthly = _mensual_colima(gold, origen_objetivo=None)
    client_monthly = client_monthly[client_monthly["mes"].le(last_closed_month)].copy()
    client_history_rows = []
    for row in client_monthly.to_dict("records"):
        client_history_rows.append({
            "cultivo": row["cultivo"], "variante_id": row["variante_id"],
            "variante": row["variante"], "origen": row["origen"],
            "mercado": row["mercado"],
            "nombre_mercado": MARKET_NAMES.get(str(row["mercado"]), str(row["mercado"])),
            "fecha": str(row["mes"]),
            "precio_frecuente_mxn_kg": float(row["precio_frecuente_kg"]),
        })
    client_comparisons = _comparar_mercados(client_monthly)
    # Presentaciones sin conversión verificable a kg (p. ej. coco por pieza)
    # se publican aparte, conservando unidad y precio originales.
    unit_prices = gold.copy()
    unit_price_columns = {"precio_frecuente_count", "precio_frecuente_kg_count",
                          "precio_frecuente_mean", "anio", "mes"}
    if unit_price_columns.issubset(unit_prices.columns):
        if "tipo_registro" in unit_prices:
            unit_prices = unit_prices[unit_prices["tipo_registro"].eq("precio")]
        frequent_count = pd.to_numeric(unit_prices["precio_frecuente_count"], errors="coerce").fillna(0)
        kg_count = pd.to_numeric(unit_prices["precio_frecuente_kg_count"], errors="coerce").fillna(0)
        unit_prices = unit_prices[
            frequent_count.gt(0) & kg_count.eq(0) & unit_prices["precio_frecuente_mean"].notna()
        ].copy()
    else:
        unit_prices = unit_prices.iloc[0:0].copy()
    unit_price_rows = []
    for row in unit_prices.to_dict("records"):
        month = pd.Period(year=int(row["anio"]), month=int(row["mes"]), freq="M")
        if month > last_closed_month:
            continue
        unit_price_rows.append({
            "cultivo": row.get("cultivo"), "variante_id": row.get("variante_id"),
            "variante": row.get("variante"), "origen": row.get("origen"),
            "mercado": row.get("mercado"),
            "nombre_mercado": MARKET_NAMES.get(str(row.get("mercado")), str(row.get("mercado"))),
            "fecha": str(month), "presentacion": row.get("presentacion"),
            "precio_mxn_presentacion": float(row["precio_frecuente_mean"]),
            "n_observaciones": int(row.get("precio_frecuente_count", 0) or 0),
        })
    climate_months: list[str] = []
    climate_stations: list[str] = []
    if "dias_clima_observados" in gold and "fecha_mes" in gold:
        climate_rows = gold[pd.to_numeric(gold["dias_clima_observados"], errors="coerce").fillna(0).gt(0)]
        climate_months = sorted(pd.to_datetime(climate_rows["fecha_mes"], errors="coerce").dropna()
                                .dt.to_period("M").astype(str).unique())
        if "estacion" in climate_rows:
            climate_stations = sorted(climate_rows["estacion"].dropna().astype(str).unique())
    # Explicitly report unsupported crops/origins instead of manufacturing a market winner.
    observed_crops = sorted({str(x) for x in gold.loc[gold.get("tipo_registro", "precio").eq("precio"), "cultivo"].dropna()}) if "tipo_registro" in gold else sorted(gold["cultivo"].dropna().astype(str).unique())
    colima_crops = set(monthly["cultivo"].dropna().astype(str))
    for crop in observed_crops:
        if crop not in colima_crops:
            eligibility.append({"cultivo": crop, "origen": "Colima", "pronosticable": False,
                                "motivo": "sin_cotizaciones_SNIIM_con_origen_Colima"})

    output_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    forecast_path = output_dir / "pronosticos_colima.csv"
    metric_path = output_dir / "metricas_backtest_colima.csv"
    validation_path = output_dir / "validaciones_pronostico_colima.csv"
    comparison_path = output_dir / "comparativa_mercados_colima.csv"
    eligibility_path = output_dir / "cobertura_analitica_colima.csv"
    forecasts.to_csv(forecast_path, index=False, encoding="utf-8")
    metrics.to_csv(metric_path, index=False, encoding="utf-8")
    backtest.to_csv(validation_path, index=False, encoding="utf-8")
    comparisons.to_csv(comparison_path, index=False, encoding="utf-8")
    pd.DataFrame(eligibility).to_csv(eligibility_path, index=False, encoding="utf-8")
    # A current public export is refreshed on every run; the E3 dataset remains a frozen snapshot.
    shutil.copyfile(gold_path, public_dir / "panel_mensual_actual.csv")
    shutil.copyfile(forecast_path, public_dir / "pronosticos_colima.csv")
    shutil.copyfile(comparison_path, public_dir / "comparativa_mercados_colima.csv")
    shutil.copyfile(metric_path, public_dir / "metricas_backtest_colima.csv")
    shutil.copyfile(validation_path, public_dir / "validaciones_pronostico_colima.csv")
    shutil.copyfile(eligibility_path, public_dir / "cobertura_analitica_colima.csv")
    client_comparisons.to_csv(public_dir / "comparativa_plazas_cliente.csv", index=False, encoding="utf-8")
    try:
        gold_reference = gold_path.resolve().relative_to(BASE_DIR.resolve()).as_posix()
    except ValueError:
        # Mantener el reporte portable y no publicar rutas locales del equipo.
        gold_reference = gold_path.name
    report = {
        "esquema": "oaic-e4-observatorio/1", "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "capa_oro": gold_reference, "origen_objetivo": "Colima", "horizonte_meses": horizon,
        "mes_actual_excluido_por_incompleto": str(current_month),
        "ultimo_mes_cerrado_usado": str(last_closed_month),
        "regla_normalizacion": "SNIIM declara Kilogramo o peso en kg en la presentación; se normaliza cada cotización antes de agregar. Presentaciones sin peso explícito quedan fuera del pronóstico por kg.",
        "metodo": "36 meses contiguos mínimos; selección por MAE en seis meses walk-forward y evaluación independiente en los seis meses cerrados siguientes; reentrenamiento del modelo elegido con toda la serie",
        "validacion": {"meses_seleccion": SELECTION_STEPS, "meses_holdout_independiente": HOLDOUT_STEPS,
                       "holdout": "Los últimos seis meses no participan en la selección del modelo; el MAE/RMSE/MAPE publicados para el modelo elegido se calculan sobre este bloque."},
        "linaje_pronostico": "Cada pronóstico incluye el periodo de Oro usado y el SHA-256 del conjunto ordenado de huellas de linaje mensual; se puede reconstruir desde la serie y periodos en panel_mensual.csv.",
        "modelos": list(MODEL_NAMES), "minimo_meses_contiguos": MIN_MONTHS,
        "series_pronosticadas": sum(1 for item in eligibility if item.get("pronosticable") is True),
        "filas_pronostico": len(forecasts), "comparaciones_pareadas": int((comparisons["estado_comparacion"] == "comparacion_descriptiva_meses_pareados").sum()) if not comparisons.empty else 0,
        "contexto_climatico": {"meses_con_observaciones": len(climate_months),
                               "ultimo_mes_con_observacion": climate_months[-1] if climate_months else None,
                               "estaciones": climate_stations,
                               "uso": "contexto descriptivo; no es predictor ni clima local de las plazas mayoristas"},
        "limitacion_comparacion": "Se compara solo cuando coinciden origen Colima, cultivo, variante y mes en al menos dos mercados; sin par no se declara un mejor mercado.",
        "series": eligibility,
        "advertencia": "Pronósticos académicos exploratorios, no consejo comercial ni garantía. Sin intervalo predictivo validado; factores de transporte, calidad, volumen y precio en parcela no están modelados.",
    }
    report_path = output_dir / "reporte_observatorio_e4.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    shutil.copyfile(report_path, public_dir / "reporte_observatorio_e4.json")
    # Payload pequeño y explícitamente público para la vista de cliente. No incluye
    # referencias de linaje por archivo ni datos de seguimiento comercial.
    client_payload = {
        "esquema": "oaic-vista-cliente/1",
        "generado_utc": report["generado_utc"],
        "ultimo_periodo_cerrado": report["ultimo_mes_cerrado_usado"],
        "horizonte_meses": report["horizonte_meses"],
        "origen_objetivo": report["origen_objetivo"],
        "metodo": report["metodo"],
        "advertencia": report["advertencia"],
        "series": eligibility,
        "historial": client_history_rows,
        "pronosticos": forecasts.to_dict("records"),
        "metricas": metrics.to_dict("records"),
        "comparaciones": client_comparisons.to_dict("records"),
        "precios_sin_conversion": unit_price_rows,
    }
    (public_dir / "resumen_cliente.json").write_text(
        json.dumps(_json_safe(client_payload), ensure_ascii=False, indent=2,
                   default=str, allow_nan=False).replace("<", "\\u003c") + "\n",
        encoding="utf-8",
    )
    quality_path = BASE_DIR / "data/plata/reporte_calidad.json"
    quality = json.loads(quality_path.read_text(encoding="utf-8")) if quality_path.is_file() else {}
    _write_dashboard(dashboard_path, forecasts.to_dict("records"), comparisons.to_dict("records"),
                     history_rows, report, metric_rows, quality)
    return report


def _render_charts(history: list[dict[str, Any]], forecasts: list[dict[str, Any]]) -> str:
    charts = []
    groups = {}
    for row in history:
        key = (row["cultivo"], row["variante_id"], row["mercado"])
        groups.setdefault(key, []).append(row)
    for key, observed in groups.items():
        future = [x for x in forecasts if (x["cultivo"], x["variante_id"], x["mercado"]) == key]
        observed = sorted(observed, key=lambda x: x["fecha"])
        future = sorted(future, key=lambda x: x["fecha_pronostico"])
        values = [float(x["precio_frecuente_mxn_kg"]) for x in observed + future]
        low, high = min(values), max(values)
        pad = max((high - low) * 0.12, max(abs(high), 1.0) * 0.03)
        low, high = max(0.0, low - pad), high + pad
        left, right, top, bottom, width, height = 78, 870, 28, 218, 920, 300
        count = max(1, len(values) - 1)
        def x(i, left=left, right=right, count=count):
            return left + i * (right - left) / count

        def y(v, low=low, high=high, top=top, bottom=bottom):
            return bottom - (v - low) * (bottom - top) / max(high - low, 1e-9)
        obs_path = " ".join(("M" if i == 0 else "L") + f"{x(i):.1f},{y(float(row['precio_frecuente_mxn_kg'])):.1f}"
                            for i, row in enumerate(observed))
        forecast_points = [(len(observed) - 1, float(observed[-1]["precio_frecuente_mxn_kg"]))]
        forecast_points.extend((len(observed) + i, float(row["precio_frecuente_mxn_kg"])) for i, row in enumerate(future))
        forecast_path = " ".join(("M" if i == 0 else "L") + f"{x(pos):.1f},{y(val):.1f}"
                                  for i, (pos, val) in enumerate(forecast_points))
        title = escape(f"{observed[0]['cultivo']} · {observed[0]['variante']} · {observed[0]['nombre_mercado']}")
        ticks = []
        for val in (low, (low + high) / 2, high):
            ticks.append(f'<line x1="{left}" y1="{y(val):.1f}" x2="{right}" y2="{y(val):.1f}" stroke="#d9e0e6"/><text x="{left-10}" y="{y(val)+4:.1f}" text-anchor="end">{val:.1f}</text>')
        charts.append(f'''<article class="chart"><h3>{title}</h3><svg viewBox="0 0 {width} {height}" role="img" aria-label="Precio frecuente mensual en MXN por kg; histórico y pronóstico para {title}">
<g font-family="system-ui,sans-serif" font-size="12" fill="#526171">{''.join(ticks)}
<text x="{(left+right)/2}" y="{height-6}" text-anchor="middle">Fecha (mes)</text>
<text transform="translate(17 {(top+bottom)/2}) rotate(-90)" text-anchor="middle">Precio frecuente (MXN/kg)</text>
<text x="{left}" y="{height-28}">{escape(observed[0]['fecha'])}</text>
<text x="{right}" y="{height-28}" text-anchor="end">{escape(future[-1]['fecha_pronostico'] if future else observed[-1]['fecha'])}</text></g>
<path d="{obs_path}" fill="none" stroke="#326b8b" stroke-width="2.5"/>
<path d="{forecast_path}" fill="none" stroke="#a46b17" stroke-width="2.5" stroke-dasharray="7 5"/>
<g fill="#326b8b">{''.join(f'<circle cx="{x(i):.1f}" cy="{y(float(r["precio_frecuente_mxn_kg"])):.1f}" r="2.4"/>' for i,r in enumerate(observed))}</g>
<g font-family="system-ui,sans-serif" font-size="12"><text x="{left}" y="16" fill="#326b8b">Observado · {len(observed)} meses</text><text x="{right}" y="16" text-anchor="end" fill="#a46b17">Pronóstico · {len(future)} meses</text></g>
</svg></article>''')
    return "".join(charts)


def _json_safe(value: Any) -> Any:
    """Convierte valores analíticos a JSON estricto y compatible con cualquier navegador."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _render_fallback(history: list[dict[str, Any]], forecasts: list[dict[str, Any]],
                     metrics: list[dict[str, Any]], report: dict[str, Any],
                     quality: dict[str, Any]) -> str:
    """Resumen útil y visible incluso si el navegador bloquea o falla JavaScript."""
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in history:
        groups.setdefault((str(row["cultivo"]), str(row["variante_id"]), str(row["mercado"])), []).append(row)
    first = next(iter(groups.values()), [])
    latest = sorted(first, key=lambda row: str(row["fecha"]))[-1] if first else {}
    norm = quality.get("normalizacion_precio_kg", {})
    converted = int(norm.get("cotizaciones_con_precio_frecuente_kg", 0) or 0)
    total = int(norm.get("cotizaciones_totales", 0) or 0)
    valid = int(quality.get("registros_plata_validos", 0) or 0)
    parsed = int(quality.get("registros_bronce_parseados", 0) or 0)
    count_series = sum(bool(row.get("pronosticable")) for row in report.get("series", []))
    forecast_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('variante', row.get('cultivo', ''))))}</td>"
        f"<td>{escape(str(row.get('nombre_mercado', '')))}</td>"
        f"<td>{escape(str(row.get('fecha_pronostico', '')))}</td>"
        f"<td>{escape(str(row.get('modelo_elegido', '')))}</td>"
        f"<td>{float(row.get('precio_frecuente_mxn_kg', 0)):.2f}</td>"
        f"<td>{float(row.get('mae_backtest_mxn_kg', 0)):.2f}</td></tr>"
        for row in forecasts
    ) or '<tr><td colspan="6">No hay proyecciones elegibles en este corte.</td></tr>'
    chart_markup = _render_charts(history, forecasts).replace('class="chart"', 'class="chart fallback-chart"')
    return f'''<section class="fallback-data" id="fallback-data" aria-label="Resumen de datos precargado">
<h2>Resumen de datos</h2><p>Esta vista ya contiene los resultados del último cálculo; no depende de una descarga dinámica para mostrar los datos.</p>
<div class="fallback-stats"><div class="fallback-stat"><span>Series pronosticables</span><strong>{count_series}</strong></div>
<div class="fallback-stat"><span>Precio observado · {escape(str(latest.get('fecha', '—')))}</span><strong>{float(latest.get('precio_frecuente_mxn_kg', 0)):.2f} MXN/kg</strong></div>
<div class="fallback-stat"><span>Registros válidos en Plata</span><strong>{valid:,} / {parsed:,}</strong></div>
<div class="fallback-stat"><span>Precios convertidos a MXN/kg</span><strong>{converted:,} / {total:,}</strong></div></div>
<h2>Estimaciones de precio</h2><div class="table-wrap"><table class="data-table"><thead><tr><th>Producto / variante</th><th>Mercado</th><th>Mes</th><th>Modelo</th><th>Precio (MXN/kg)</th><th>MAE (MXN/kg)</th></tr></thead><tbody>{forecast_rows}</tbody></table></div>
<h2 style="margin-top:18px">Historial y proyección</h2>{chart_markup}
</section>'''


def _write_dashboard(path: Path, forecasts: list[dict[str, Any]], comparisons: list[dict[str, Any]],
                     history: list[dict[str, Any]], report: dict[str, Any],
                     metrics: list[dict[str, Any]], quality: dict[str, Any]) -> None:
    payload = json.dumps(_json_safe({"pronosticos": forecasts, "comparaciones": comparisons,
                                    "historial": history, "metricas": metrics,
                                    "calidad": quality, "reporte": report}),
                         ensure_ascii=False, default=str, allow_nan=False).replace("<", "\\u003c")
    template = Path(__file__).resolve().parents[2] / "tablero" / "plantilla.html"
    fallback = _render_fallback(history, forecasts, metrics, report, quality)
    html = template.read_text(encoding="utf-8").replace("__PAYLOAD__", payload).replace("__FALLBACK__", fallback)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="main.py observatorio", description="Genera pronósticos auditables y tablero local")
    parser.add_argument("--horizonte", type=int, default=3, help="meses a pronosticar (1–12)")
    parser.add_argument("--oro", type=Path, default=BASE_DIR / "data/oro/panel_mensual.csv")
    parser.add_argument("--corte", type=date.fromisoformat, help="fecha de corte YYYY-MM-DD para reproducibilidad")
    args = parser.parse_args(argv)
    report = generar_observatorio(gold_path=args.oro, horizon=args.horizonte, as_of_date=args.corte)
    print(json.dumps({k: report[k] for k in ("series_pronosticadas", "filas_pronostico", "comparaciones_pareadas", "generado_utc")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
