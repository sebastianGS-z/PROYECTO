# %% [markdown]
# # Laboratorio E1 · Series de tiempo y pronóstico (Análisis Estadístico, unidad 3)
#
# Cuaderno reproducible en formato *percent* (se abre como notebook en VS Code o Jupyter con jupytext).
# Ejecutar completo: ``python -m laboratorio.e1_series``. Lee solo la capa Oro versionada y escribe:
#
# * ``laboratorio/resultados/e1/resultados.json`` (todas las cifras),
# * figuras en ``docs/E1/laboratorio/`` y el informe ``docs/E1/laboratorio_series.md``.
#
# Serie principal: precio frecuente mensual (MXN/kg) del limón c/semilla #5 de origen Colima en el
# Mercado de Abasto de Guadalajara. Serie secundaria: papaya Maradol (mismo origen y plaza).

# %%
from __future__ import annotations

import argparse
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, adfuller, ccf, kpss, pacf

from laboratorio.comun import BASE_DIR, RESULTADOS, fmt, guardar_figura, guardar_json, rel, tabla_md
from src.tdl_e4.observatorio import _mensual_colima

SERIES = {
    "limon_c5": {"variante_id": 421, "mercado": "140", "nombre": "Limón c/semilla #5 · Colima → Guadalajara", "producto": "el limón c/semilla #5"},
    "papaya_maradol": {"variante_id": 609, "mercado": "140", "nombre": "Papaya Maradol · Colima → Guadalajara", "producto": "la papaya Maradol"},
}
PRINCIPAL = "limon_c5"
PRUEBA = 6          # últimos meses reservados como prueba (datos que el modelo no vio)
HORIZONTE = 3       # meses a pronosticar para el cliente
ALFA = 0.05


# %% [markdown]
# ## 1. Datos: serie mensual desde Oro
# Se usa la misma agregación del observatorio (promedio ponderado por número de cotizaciones del mes).
# El mes en curso se excluye porque es un agregado parcial.

# %%
def cargar_series(oro_path: Path, corte: pd.Period | None = None) -> dict[str, pd.Series]:
    gold = pd.read_csv(oro_path)
    mensual = _mensual_colima(gold)
    corte = corte or (pd.Period(pd.Timestamp.today(), freq="M") - 1)
    series = {}
    for clave, cfg in SERIES.items():
        sub = mensual[(mensual["variante_id"].astype(float) == cfg["variante_id"]) & (mensual["mercado"].astype(str) == cfg["mercado"])]
        s = sub.set_index("mes")["precio_frecuente_kg"].sort_index()
        s = s[s.index <= corte]
        if s.empty:
            continue
        s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))
        series[clave] = s.astype("float64")
    return series


def clima_mensual(oro_path: Path) -> pd.Series:
    gold = pd.read_csv(oro_path, usecols=["fecha_mes", "tavg_c_mean"])
    gold["mes"] = pd.to_datetime(gold["fecha_mes"]).dt.to_period("M")
    return gold.dropna().groupby("mes")["tavg_c_mean"].first().sort_index()


# %% [markdown]
# ## 2. Caracterización y descomposición
# Criterio aditivo vs. multiplicativo: si la amplitud estacional crece con el nivel, conviene el
# multiplicativo. Se mide (a) la correlación entre el nivel anual y la desviación estándar anual y
# (b) qué descomposición deja residuos con menor coeficiente de variación relativo al nivel.

# %%
def caracterizar(s: pd.Series) -> dict[str, Any]:
    cambios = s.pct_change().dropna()
    salto = cambios.abs().idxmax()
    anual = s.groupby(s.index.year).agg(["mean", "std", "count"])
    anual = anual[anual["count"] >= 6]
    corr_nivel_var = float(np.corrcoef(anual["mean"], anual["std"])[0, 1]) if len(anual) >= 3 else None
    x = np.arange(len(s))
    pendiente, _, r, p, _ = stats.linregress(x, s.to_numpy())
    mes_mayor = s.groupby(s.index.month).mean()
    return {"n": int(s.notna().sum()), "desde": str(s.index.min()), "hasta": str(s.index.max()),
            "media": s.mean(), "mediana": s.median(), "min": s.min(), "max": s.max(), "cv": s.std() / s.mean(),
            "tendencia_lineal_mxn_kg_mes": pendiente, "tendencia_r2": r ** 2, "tendencia_p": p,
            "mayor_cambio_mensual": {"mes": str(salto), "cambio_pct": cambios.loc[salto] * 100},
            "mes_calendario_mas_caro": int(mes_mayor.idxmax()), "mes_calendario_mas_barato": int(mes_mayor.idxmin()),
            "corr_nivel_desviacion_anual": corr_nivel_var}


def descomponer(s: pd.Series, corr_nivel_var: float | None = None) -> dict[str, Any]:
    ts = s.copy()
    ts.index = ts.index.to_timestamp()
    add = seasonal_decompose(ts, model="additive", period=12, extrapolate_trend="period")
    mul = seasonal_decompose(ts, model="multiplicative", period=12, extrapolate_trend="period")
    cv_add = float(np.nanstd(add.resid) / np.nanmean(ts))
    cv_mul = float(np.nanstd((mul.resid - 1) * mul.trend) / np.nanmean(ts))
    fuerza_est = max(0.0, 1 - np.nanvar(add.resid) / np.nanvar(add.resid + add.seasonal))
    fuerza_tend = max(0.0, 1 - np.nanvar(add.resid) / np.nanvar(add.resid + add.trend))
    # Se exige una mejora de al menos 5 % en el residuo, o evidencia de que la dispersión crece con el nivel,
    # para preferir el multiplicativo; si no, se elige el aditivo por parsimonia.
    mejora = (cv_add - cv_mul) / cv_add if cv_add else 0.0
    elegido = "multiplicativo" if (mejora >= 0.05 or (mejora > 0 and (corr_nivel_var or 0) > 0.5)) else "aditivo"
    return {"modelo_elegido": elegido, "mejora_relativa_multiplicativo": mejora, "cv_residuo_aditivo": cv_add, "cv_residuo_multiplicativo": cv_mul,
            "fuerza_estacional": fuerza_est, "fuerza_tendencia": fuerza_tend,
            "indices_estacionales_aditivos": {int(k.month): float(v) for k, v in add.seasonal.iloc[:12].items()},
            "_add": add, "_mul": mul}


# %% [markdown]
# ## 3. Estacionariedad y autocorrelación
# Dickey-Fuller aumentada (H0: raíz unitaria) complementada con KPSS (H0: estacionaria).
# Se diferencia hasta que ADF rechace H0 al 5 %.

# %%
def estacionariedad(s: pd.Series) -> dict[str, Any]:
    pruebas = []
    serie, d = s.dropna(), 0
    while True:
        adf = adfuller(serie, autolag="AIC", result_object=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kp = kpss(serie, regression="c", nlags="auto")
        pruebas.append({"d": d, "adf_estadistico": adf[0], "adf_p": adf[1], "adf_rezagos": adf[2],
                        "adf_valores_criticos": adf[4], "kpss_estadistico": kp[0], "kpss_p": kp[1],
                        "estacionaria_adf": adf[1] < ALFA})
        if adf[1] < ALFA or d >= 2:
            break
        serie, d = serie.diff().dropna(), d + 1
    return {"d_recomendado": d, "pruebas": pruebas}


def autocorrelacion(s: pd.Series, d: int, rezagos: int = 12) -> dict[str, Any]:
    serie = s.dropna()
    for _ in range(d):
        serie = serie.diff().dropna()
    rezagos = min(rezagos, len(serie) // 2 - 1)
    banda = 1.96 / np.sqrt(len(serie))
    a, p = acf(serie, nlags=rezagos, fft=False), pacf(serie, nlags=rezagos, method="ywm")
    sig_acf = [k for k in range(1, rezagos + 1) if abs(a[k]) > banda]
    sig_pacf = [k for k in range(1, rezagos + 1) if abs(p[k]) > banda]
    # Lectura de Box-Jenkins: PACF que se corta sugiere AR(p); ACF que se corta sugiere MA(q).
    p_sug = max([k for k in sig_pacf if k <= 3], default=0)
    q_sug = max([k for k in sig_acf if k <= 3], default=0)
    return {"serie": f"diferencia de orden {d}" if d else "nivel", "n": len(serie), "banda_95": banda,
            "acf": a.tolist(), "pacf": p.tolist(), "rezagos_significativos_acf": sig_acf,
            "rezagos_significativos_pacf": sig_pacf, "p_sugerido": p_sug, "q_sugerido": q_sug,
            "_serie": serie}


def correlacion_cruzada(x: pd.Series, y: pd.Series, nombre_y: str, max_lag: int = 6) -> dict[str, Any]:
    """Correlación cruzada de las primeras diferencias (evita correlación espuria por tendencia)."""
    df = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    dx, dy = df["x"].diff().dropna(), df["y"].diff().dropna()
    n = len(dx)
    if n < 12:
        return {"variable": nombre_y, "n": n, "estado": "insuficiente"}
    banda = 1.96 / np.sqrt(n)
    valores = {}
    for k in range(-max_lag, max_lag + 1):
        # k > 0: la variable y adelanta a x en k meses
        valores[k] = float(dx.corr(dy.shift(k)))
    mejor = max(valores, key=lambda k: abs(valores[k]) if not np.isnan(valores[k]) else -1)
    return {"variable": nombre_y, "n": n, "banda_95": banda, "ccf": valores, "rezago_max": mejor,
            "corr_max": valores[mejor], "significativa": abs(valores[mejor]) > banda,
            "ccf_statsmodels_lag0": float(ccf(dx.to_numpy(), dy.to_numpy(), adjusted=False)[0])}


# %% [markdown]
# ## 4. Cuatro modelos y selección por error en datos no vistos
# Suavizamiento simple, Holt, Holt-Winters aditivo (modelos ETS con error aditivo, que además dan
# intervalos de predicción) y ARIMA/SARIMA con (p, d, q) elegido por AIC en la rejilla guiada por ACF/PACF.

# %%
@dataclass
class Ajuste:
    nombre: str
    pronostico: np.ndarray
    resultado: Any
    detalle: dict[str, Any]


def _ets(train: pd.Series, tipo: str):
    kw = {"error": "add", "initialization_method": "estimated"}
    if tipo == "holt":
        kw["trend"] = "add"
    if tipo == "holt_winters":
        kw.update(trend="add", seasonal="add", seasonal_periods=12)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ETSModel(train.reset_index(drop=True), **kw).fit(disp=False)


def seleccionar_arima(train: pd.Series, d: int) -> dict[str, Any]:
    filas = []
    y = train.reset_index(drop=True)
    for p in range(0, 4):
        for q in range(0, 4):
            for P in (0, 1):
                orden, est = (p, d, q), (P, 0, 0, 12) if P else (0, 0, 0, 0)
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        r = ARIMA(y, order=orden, seasonal_order=est, trend="c" if d == 0 else "n").fit()
                    if np.isfinite(r.aic):
                        filas.append({"orden": orden, "estacional": est, "aic": r.aic, "bic": r.bic})
                except Exception:  # combinaciones que no convergen se omiten y se registran por ausencia
                    continue
    tabla = pd.DataFrame(filas).sort_values("aic").reset_index(drop=True)
    return {"tabla": tabla, "mejor": tabla.iloc[0].to_dict()}


def ajustar_modelos(train: pd.Series, h: int, d: int) -> tuple[list[Ajuste], dict[str, Any]]:
    ajustes = []
    for nombre, tipo in (("Suavizamiento simple", "simple"), ("Holt", "holt"), ("Holt-Winters aditivo", "holt_winters")):
        try:
            r = _ets(train, tipo)
            ajustes.append(Ajuste(nombre, np.asarray(r.forecast(h)), r, {"aic": r.aic, "parametros": {k: float(v) for k, v in r.params.items()}}))
        except Exception as exc:  # noqa: BLE001 - se documenta el fallo del modelo
            ajustes.append(Ajuste(nombre, np.full(h, np.nan), None, {"error": f"{type(exc).__name__}: {exc}"}))
    sel = seleccionar_arima(train, d)
    orden, est = tuple(sel["mejor"]["orden"]), tuple(sel["mejor"]["estacional"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = ARIMA(train.reset_index(drop=True), order=orden, seasonal_order=est, trend="c" if d == 0 else "n").fit()
    nombre = f"{'SARIMA' if est[0] else 'ARIMA'}{orden}" + (f"x{est}" if est[0] else "")
    ajustes.append(Ajuste(nombre, np.asarray(r.forecast(h)), r, {"aic": r.aic, "orden": orden, "estacional": est}))
    return ajustes, sel


def metricas(real: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    e = pred - real
    return {"MAE": float(np.mean(np.abs(e))), "RMSE": float(np.sqrt(np.mean(e ** 2))),
            "MAPE_pct": float(np.mean(np.abs(e / real)) * 100)}


# %% [markdown]
# ## 5. Residuos del ganador, intervalo de predicción y frase para el cliente
# Puerta 3 (supuestos): si Ljung-Box rechaza independencia o la varianza no es estable, el intervalo
# paramétrico no se publica y se usa un intervalo empírico basado en los errores de la prueba.

# %%
def reajustar(nombre: str, s: pd.Series, detalle: dict[str, Any]):
    tipo = {"Suavizamiento simple": "simple", "Holt": "holt", "Holt-Winters aditivo": "holt_winters"}.get(nombre)
    if tipo:
        return _ets(s, tipo)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ARIMA(s.reset_index(drop=True), order=detalle["orden"], seasonal_order=detalle["estacional"],
                     trend="c" if detalle["orden"][1] == 0 else "n").fit()


def diagnostico_residuos(resultado, n_params: int = 0) -> dict[str, Any]:
    resid = pd.Series(np.asarray(resultado.resid)).dropna()
    resid = resid.iloc[1:] if len(resid) > 13 else resid  # el primer residuo depende de la inicialización
    lags = [k for k in (6, 12) if k < len(resid) // 2]
    lb = acorr_ljungbox(resid, lags=lags, model_df=min(n_params, min(lags) - 1) if lags else 0, return_df=True)
    mitad = len(resid) // 2
    lev = stats.levene(resid.iloc[:mitad], resid.iloc[mitad:])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        arch = het_arch(resid, nlags=min(4, len(resid) // 5))
    sh = stats.shapiro(resid)
    return {"n": len(resid), "ljung_box": {int(k): {"Q": float(r.lb_stat), "p": float(r.lb_pvalue)} for k, r in lb.iterrows()},
            "sin_autocorrelacion": bool((lb["lb_pvalue"] > ALFA).all()),
            "levene_mitades_p": float(lev.pvalue), "arch_lm_p": float(arch[1]),
            "varianza_estable": bool(lev.pvalue > ALFA and arch[1] > ALFA),
            "shapiro_p": float(sh.pvalue), "normal": bool(sh.pvalue > ALFA), "_resid": resid}


def intervalos(nombre: str, resultado, h: int, residuos_ok: bool, errores_prueba: np.ndarray) -> pd.DataFrame:
    if residuos_ok:
        if hasattr(resultado, "get_prediction") and isinstance(resultado.model, ETSModel):
            pr = resultado.get_prediction(start=resultado.nobs, end=resultado.nobs + h - 1)
            f80, f95 = pr.summary_frame(alpha=0.2), pr.summary_frame(alpha=0.05)
            return pd.DataFrame({"pronostico": f95["mean"].to_numpy(), "li80": f80["pi_lower"].to_numpy(), "ls80": f80["pi_upper"].to_numpy(),
                                 "li95": f95["pi_lower"].to_numpy(), "ls95": f95["pi_upper"].to_numpy(), "metodo": "paramétrico ETS"})
        fc = resultado.get_forecast(h)
        c80, c95 = fc.conf_int(alpha=0.2), fc.conf_int(alpha=0.05)
        return pd.DataFrame({"pronostico": np.asarray(fc.predicted_mean), "li80": c80.iloc[:, 0].to_numpy(), "ls80": c80.iloc[:, 1].to_numpy(),
                             "li95": c95.iloc[:, 0].to_numpy(), "ls95": c95.iloc[:, 1].to_numpy(), "metodo": "paramétrico ARIMA"})
    # Intervalo empírico: cuantiles del error absoluto observado en la prueba, ampliado con sqrt(h).
    punto = np.asarray(resultado.forecast(h))
    q80, q95 = np.quantile(np.abs(errores_prueba), 0.8), np.quantile(np.abs(errores_prueba), 0.95)
    k = np.sqrt(np.arange(1, h + 1))
    return pd.DataFrame({"pronostico": punto, "li80": punto - q80 * k, "ls80": punto + q80 * k,
                         "li95": np.maximum(0, punto - q95 * k), "ls95": punto + q95 * k, "metodo": "empírico (errores de prueba)"})


# %% [markdown]
# ## 6. Ejecución completa, figuras e informe

# %%
def analizar(s: pd.Series, nombre: str, producto: str = "el producto") -> dict[str, Any]:
    s = s.dropna()
    car = caracterizar(s)
    desc = descomponer(s, car["corr_nivel_desviacion_anual"])
    est = estacionariedad(s)
    auto = autocorrelacion(s, est["d_recomendado"])
    train, test = s.iloc[:-PRUEBA], s.iloc[-PRUEBA:]
    ajustes, sel = ajustar_modelos(train, PRUEBA, est["d_recomendado"])
    filas = []
    for a in ajustes:
        m = metricas(test.to_numpy(), a.pronostico) if np.isfinite(a.pronostico).all() else {"MAE": np.nan, "RMSE": np.nan, "MAPE_pct": np.nan}
        filas.append({"modelo": a.nombre, **m, "AIC_entrenamiento": a.detalle.get("aic")})
    comp = pd.DataFrame(filas).sort_values(["RMSE", "MAPE_pct"]).reset_index(drop=True)
    ganador = comp.iloc[0]["modelo"]
    aj = next(a for a in ajustes if a.nombre == ganador)
    errores_prueba = aj.pronostico - test.to_numpy()
    final = reajustar(ganador, s, aj.detalle)
    n_params = len(getattr(final, "params", []))
    diag = diagnostico_residuos(final, n_params=n_params if "ARIMA" in ganador else 0)
    ok = diag["sin_autocorrelacion"] and diag["varianza_estable"]
    futuro = intervalos(ganador, final, HORIZONTE, ok, errores_prueba)
    futuro.insert(0, "mes", [str(s.index[-1] + i) for i in range(1, HORIZONTE + 1)])
    return {"nombre": nombre, "producto": producto, "serie": s, "caracterizacion": car, "descomposicion": desc, "estacionariedad": est,
            "autocorrelacion": auto, "arima_aic": sel, "comparacion": comp, "ganador": ganador, "ajustes": ajustes,
            "train": train, "test": test, "residuos": diag, "supuestos_ok": ok, "pronostico": futuro}


def figuras(r: dict[str, Any], carpeta: Path, clave: str) -> dict[str, Path]:
    import matplotlib.pyplot as plt
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    out = {}
    s = r["serie"]
    x = s.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(x, s.values, marker="o", ms=3, label="Precio frecuente (MXN/kg)")
    ax.plot(x, s.rolling(6, center=True).mean().values, lw=2, alpha=.7, label="Media móvil 6 meses")
    ax.set_title(r["nombre"]); ax.set_ylabel("MXN/kg"); ax.grid(alpha=.3); ax.legend()
    out["serie"] = guardar_figura(fig, carpeta / f"{clave}_serie.png")

    d = r["descomposicion"]["_add" if r["descomposicion"]["modelo_elegido"] == "aditivo" else "_mul"]
    fig = d.plot(); fig.set_size_inches(9, 6); fig.suptitle(f"Descomposición {r['descomposicion']['modelo_elegido']}", y=1.0)
    out["descomposicion"] = guardar_figura(fig, carpeta / f"{clave}_descomposicion.png")

    serie_d = r["autocorrelacion"]["_serie"]
    lags = min(12, len(serie_d) // 2 - 1)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    plot_acf(serie_d, lags=lags, ax=axes[0]); plot_pacf(serie_d, lags=lags, ax=axes[1], method="ywm")
    axes[0].set_title(f"ACF ({r['autocorrelacion']['serie']})"); axes[1].set_title(f"PACF ({r['autocorrelacion']['serie']})")
    out["acf_pacf"] = guardar_figura(fig, carpeta / f"{clave}_acf_pacf.png")

    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(x, s.values, color="black", lw=1.5, label="Real")
    xt = r["test"].index.to_timestamp()
    for a in r["ajustes"]:
        if np.isfinite(a.pronostico).all():
            ax.plot(xt, a.pronostico, marker="o", ms=3, lw=1.2, label=a.nombre)
    ax.axvspan(xt[0], xt[-1], color="grey", alpha=.12, label="Prueba (no vista)")
    ax.set_title("Pronósticos sobre los 6 meses de prueba"); ax.set_ylabel("MXN/kg"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    out["comparacion"] = guardar_figura(fig, carpeta / f"{clave}_comparacion_modelos.png")

    f = r["pronostico"]
    xf = pd.PeriodIndex(f["mes"], freq="M").to_timestamp()
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(x[-18:], s.values[-18:], marker="o", ms=3, color="black", label="Observado")
    ax.plot(xf, f["pronostico"], marker="o", color="tab:blue", label=f"Pronóstico ({r['ganador']})")
    ax.fill_between(xf, f["li95"], f["ls95"], alpha=.15, color="tab:blue", label="Intervalo 95 %")
    ax.fill_between(xf, f["li80"], f["ls80"], alpha=.25, color="tab:blue", label="Intervalo 80 %")
    ax.set_ylabel("MXN/kg"); ax.grid(alpha=.3); ax.legend(fontsize=8); ax.set_title("Pronóstico con intervalo de predicción")
    out["pronostico"] = guardar_figura(fig, carpeta / f"{clave}_pronostico.png")

    resid = r["residuos"]["_resid"]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
    axes[0].plot(resid.values, marker="o", ms=3); axes[0].axhline(0, color="k", lw=.8); axes[0].set_title("Residuos")
    plot_acf(resid, lags=min(12, len(resid) // 2 - 1), ax=axes[1]); axes[1].set_title("ACF de residuos")
    stats.probplot(resid, plot=axes[2]); axes[2].set_title("Q-Q normal")
    out["residuos"] = guardar_figura(fig, carpeta / f"{clave}_residuos.png")
    return out


def frase_cliente(r: dict[str, Any]) -> str:
    f = r["pronostico"].iloc[0]
    return (f"Para {f['mes']} esperamos que {r['producto']} de Colima se cotice en Guadalajara "
            f"alrededor de {f['pronostico']:.1f} MXN/kg; con 80 % de probabilidad estará entre {f['li80']:.1f} y {f['ls80']:.1f} "
            f"y con 95 % entre {max(0, f['li95']):.1f} y {f['ls95']:.1f} MXN/kg. En los 6 meses de prueba el modelo se equivocó en "
            f"promedio {r['comparacion'].iloc[0]['MAE']:.1f} MXN/kg ({r['comparacion'].iloc[0]['MAPE_pct']:.0f} %), así que úselo como "
            "rango de referencia para planear, no como precio garantizado.")


def informe(resultados: dict[str, dict[str, Any]], figs: dict[str, dict[str, Path]], cruzadas: list[dict[str, Any]], destino: Path) -> str:
    carpeta = destino.parent
    r = resultados[PRINCIPAL]
    c, d, e, a = r["caracterizacion"], r["descomposicion"], r["estacionariedad"], r["autocorrelacion"]
    f = figs[PRINCIPAL]
    lineas = []
    lineas.append("# Laboratorio E1 · Series de tiempo y pronóstico\n")
    lineas.append("> Documento **generado** por `python -m laboratorio.e1_series` a partir de `data/oro/panel_mensual.csv`. "
             "No editar a mano: las cifras se regeneran. Resultados completos en `laboratorio/resultados/e1/resultados.json`.\n")
    lineas.append(f"**Serie principal:** {r['nombre']}, precio frecuente mensual en MXN/kg, {c['desde']} a {c['hasta']} "
             f"({c['n']} meses, sin imputación). Serie secundaria: {resultados['papaya_maradol']['nombre'] if 'papaya_maradol' in resultados else '—'}.\n")
    lineas.append("## 1. Caracterización\n")
    lineas.append(f"![Serie]({rel(f['serie'], carpeta)})\n")
    lineas.append(f"- Nivel: media {fmt(c['media'], 2)} MXN/kg, mediana {fmt(c['mediana'], 2)}, rango {fmt(c['min'], 2)}–{fmt(c['max'], 2)}; "
             f"coeficiente de variación {fmt(c['cv'] * 100, 1)} %.")
    lineas.append(f"- Tendencia lineal: {fmt(c['tendencia_lineal_mxn_kg_mes'], 3)} MXN/kg por mes (R² = {fmt(c['tendencia_r2'], 3)}, p = {fmt(c['tendencia_p'], 4)}).")
    lineas.append(f"- Estacionalidad: en promedio el mes calendario más caro es el {c['mes_calendario_mas_caro']} y el más barato el {c['mes_calendario_mas_barato']} "
             f"(fuerza estacional {fmt(d['fuerza_estacional'], 2)} en escala 0–1).")
    lineas.append(f"- Cambio estructural visible: el mayor cambio mensual fue en {c['mayor_cambio_mensual']['mes']} ({fmt(c['mayor_cambio_mensual']['cambio_pct'], 1)} %).")
    lineas.append("- Ciclos: con 36 meses no se pueden identificar ciclos de más de un año; solo se analiza tendencia y estacionalidad anual.\n")
    lineas.append("## 2. Descomposición\n")
    lineas.append(f"![Descomposición]({rel(f['descomposicion'], carpeta)})\n")
    lineas.append(f"Se eligió el modelo **{d['modelo_elegido']}**. Criterio: preferir el multiplicativo solo si reduce el residuo al menos 5 % "
             "o si la dispersión crece claramente con el nivel; si no, el aditivo por parsimonia. El coeficiente de variación del residuo "
             f"(MXN/kg relativo al nivel) es {fmt(d['cv_residuo_aditivo'], 4)} en el aditivo y {fmt(d['cv_residuo_multiplicativo'], 4)} en el multiplicativo "
             f"(mejora {fmt(d['mejora_relativa_multiplicativo'] * 100, 1)} %)"
             + (f"; además la correlación entre nivel anual y desviación anual es {fmt(c['corr_nivel_desviacion_anual'], 2)} "
                "(solo 3 años, evidencia débil)." if c["corr_nivel_desviacion_anual"] is not None else ".") + "\n")
    lineas.append("## 3. Estacionariedad (Dickey-Fuller aumentada y KPSS)\n")
    tab = pd.DataFrame([{"Serie": "nivel" if p["d"] == 0 else f"Δ^{p['d']}", "ADF": p["adf_estadistico"], "p ADF": p["adf_p"],
                         "KPSS": p["kpss_estadistico"], "p KPSS": p["kpss_p"],
                         "Conclusión ADF (5 %)": "estacionaria" if p["estacionaria_adf"] else "raíz unitaria"} for p in e["pruebas"]])
    lineas.append(tabla_md(tab, 4) + "\n")
    lineas.append(f"Orden de diferenciación usado: **d = {e['d_recomendado']}**. KPSS se reporta como contraste (H0 opuesta); "
             "su p-valor está acotado entre 0.01 y 0.10 por las tablas de statsmodels.\n")
    lineas.append("## 4. Autocorrelación (ACF, PACF) y correlación cruzada\n")
    lineas.append(f"![ACF y PACF]({rel(f['acf_pacf'], carpeta)})\n")
    lineas.append(f"Sobre la serie en {a['serie']} (n = {a['n']}, banda ±{fmt(a['banda_95'], 3)}): rezagos significativos en ACF {a['rezagos_significativos_acf'] or 'ninguno'} "
             f"y en PACF {a['rezagos_significativos_pacf'] or 'ninguno'}. Lectura Box-Jenkins: p ≈ {a['p_sugerido']}, q ≈ {a['q_sugerido']}; "
             "la rejilla de AIC explora p, q ∈ {0..3} y un término AR estacional alrededor de esa sugerencia.\n")
    for cc in cruzadas:
        if cc.get("estado") == "insuficiente":
            lineas.append(f"- Correlación cruzada con {cc['variable']}: solo {cc['n']} meses comunes; no se interpreta.")
        else:
            lineas.append(f"- Correlación cruzada (primeras diferencias) con **{cc['variable']}**: máximo |r| = {fmt(cc['corr_max'], 3)} en el rezago {cc['rezago_max']} "
                     f"(n = {cc['n']}, banda ±{fmt(cc['banda_95'], 3)}): {'significativa' if cc['significativa'] else 'no significativa'} al 5 %. "
                     "Rezago k > 0 significa que la otra variable adelanta al precio del limón en k meses.")
    lineas.append("")
    lineas.append("## 5. Cuatro modelos y selección con datos que no vio\n")
    sel = r["arima_aic"]["tabla"].head(5).copy()
    sel["orden"] = sel["orden"].astype(str); sel["estacional"] = sel["estacional"].astype(str)
    lineas.append("Rejilla ARIMA por AIC sobre el entrenamiento (5 mejores):\n")
    lineas.append(tabla_md(sel, 2) + "\n")
    lineas.append(f"Entrenamiento: {r['train'].index.min()}–{r['train'].index.max()} ({len(r['train'])} meses). "
             f"Prueba: {r['test'].index.min()}–{r['test'].index.max()} ({len(r['test'])} meses, pronóstico a 1–{PRUEBA} pasos sin reentrenar).\n")
    lineas.append(f"![Comparación]({rel(f['comparacion'], carpeta)})\n")
    lineas.append(tabla_md(r["comparacion"], 3) + "\n")
    lineas.append(f"**Ganador por menor RMSE (desempate MAPE): {r['ganador']}.** Se elige por error fuera de muestra, no por complejidad.\n")
    lineas.append("Nota: el tablero del observatorio usa además una validación *walk-forward* a un paso (6 meses de selección + 6 de holdout) "
             "en `data/oro/metricas_backtest_colima.csv`; ambos procedimientos son complementarios.\n")
    rd = r["residuos"]
    lineas.append("## 6. Residuos del modelo ganador (puerta de calidad 3)\n")
    lineas.append(f"![Residuos]({rel(f['residuos'], carpeta)})\n")
    lb = "; ".join(f"rezago {k}: Q = {fmt(v['Q'], 2)}, p = {fmt(v['p'], 3)}" for k, v in rd["ljung_box"].items())
    lineas.append(f"- Ljung-Box ({lb}): {'sin autocorrelación' if rd['sin_autocorrelacion'] else '**autocorrelación remanente**'}.")
    lineas.append(f"- Varianza: Levene entre mitades p = {fmt(rd['levene_mitades_p'], 3)}, ARCH-LM p = {fmt(rd['arch_lm_p'], 3)} → "
             f"{'estable' if rd['varianza_estable'] else '**no estable**'}.")
    lineas.append(f"- Normalidad (Shapiro-Wilk) p = {fmt(rd['shapiro_p'], 3)} → {'compatible con normal' if rd['normal'] else 'no normal'}.")
    lineas.append(f"- Decisión: {'se publica el intervalo paramétrico del modelo' if r['supuestos_ok'] else 'el supuesto no se cumple, así que se publica un **intervalo empírico** construido con los errores observados en la prueba (método que no depende de ese supuesto)'}.\n")
    lineas.append("## 7. Pronóstico publicado e interpretación para el cliente\n")
    lineas.append(f"![Pronóstico]({rel(f['pronostico'], carpeta)})\n")
    lineas.append(tabla_md(r["pronostico"], 2) + "\n")
    lineas.append(f"> {frase_cliente(r)}\n")
    lineas.append("El pronóstico y su intervalo también se publican en el tablero, en `tablero/laboratorio.html`.\n")
    if "papaya_maradol" in resultados:
        p = resultados["papaya_maradol"]
        lineas.append("## 8. Serie secundaria: papaya Maradol\n")
        lineas.append(f"d = {p['estacionariedad']['d_recomendado']}; descomposición {p['descomposicion']['modelo_elegido']}; ganador **{p['ganador']}**; "
                 f"residuos {'aprobados' if p['supuestos_ok'] else 'con supuestos no cumplidos (intervalo empírico)'}.\n")
        lineas.append(tabla_md(p["comparacion"], 3) + "\n")
        lineas.append(f"> {frase_cliente(p)}\n")
    lineas.append("## Limitaciones\n")
    lineas.append("- 36 meses permiten estimar estacionalidad anual con solo tres repeticiones por mes; los índices estacionales son inestables.")
    lineas.append("- La prueba usa 6 meses; un ranking de modelos con tan pocos puntos puede cambiar con la siguiente actualización.")
    lineas.append("- Los precios son cotizaciones mayoristas SNIIM en plaza, no precio pagado al productor.")
    return "\n".join(lineas) + "\n"


def ejecutar(oro_path: Path, salida: Path, docs: Path, corte: pd.Period | None = None) -> dict[str, Any]:
    series = cargar_series(oro_path, corte)
    if PRINCIPAL not in series:
        raise RuntimeError("No se encontró la serie principal en Oro")
    resultados = {k: analizar(s, SERIES[k]["nombre"], SERIES[k]["producto"]) for k, s in series.items() if s.dropna().size >= 30}
    figs = {k: figuras(r, docs / "laboratorio", k) for k, r in resultados.items()}
    principal = resultados[PRINCIPAL]["serie"]
    cruzadas = [correlacion_cruzada(principal, clima_mensual(oro_path), "temperatura media mensual (NOAA, Manzanillo)")]
    if "papaya_maradol" in series:
        cruzadas.append(correlacion_cruzada(principal, series["papaya_maradol"], "precio de papaya Maradol (misma plaza)"))
    md = informe(resultados, figs, cruzadas, docs / "laboratorio_series.md")
    (docs / "laboratorio_series.md").write_text(md, encoding="utf-8")
    salida_json = {}
    for k, r in resultados.items():
        salida_json[k] = {
            "nombre": r["nombre"], "caracterizacion": r["caracterizacion"],
            "descomposicion": {kk: v for kk, v in r["descomposicion"].items() if not kk.startswith("_")},
            "estacionariedad": r["estacionariedad"],
            "autocorrelacion": {kk: v for kk, v in r["autocorrelacion"].items() if not kk.startswith("_")},
            "arima_rejilla_aic": r["arima_aic"]["tabla"].assign(orden=lambda t: t["orden"].astype(str), estacional=lambda t: t["estacional"].astype(str)).to_dict("records"),
            "comparacion_prueba": r["comparacion"].to_dict("records"), "ganador": r["ganador"],
            "residuos": {kk: v for kk, v in r["residuos"].items() if not kk.startswith("_")}, "supuestos_ok": r["supuestos_ok"],
            "pronostico": r["pronostico"].to_dict("records"), "frase_cliente": frase_cliente(r),
            "serie": {str(i): v for i, v in r["serie"].items()},
        }
    salida_json["correlacion_cruzada"] = cruzadas
    guardar_json(salida_json, salida / "resultados.json")
    return salida_json


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Laboratorio E1: series de tiempo y pronóstico")
    ap.add_argument("--oro", type=Path, default=BASE_DIR / "data" / "oro" / "panel_mensual.csv")
    ap.add_argument("--salida", type=Path, default=RESULTADOS / "e1")
    ap.add_argument("--docs", type=Path, default=BASE_DIR / "docs" / "E1")
    ap.add_argument("--corte", help="último mes completo AAAA-MM (por defecto, el mes anterior al actual)")
    a = ap.parse_args(argv)
    r = ejecutar(a.oro, a.salida, a.docs, pd.Period(a.corte, freq="M") if a.corte else None)
    print(f"E1: ganador {r[PRINCIPAL]['ganador']} · supuestos_ok={r[PRINCIPAL]['supuestos_ok']} · {a.docs / 'laboratorio_series.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
