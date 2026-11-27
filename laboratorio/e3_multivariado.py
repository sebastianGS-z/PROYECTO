# %% [markdown]
# # Laboratorio E3 · Mapa multivariado: normalidad, PCA y MANOVA (Análisis Estadístico, unidad 5)
#
# Unidad de análisis: una serie de cotización en un mes (variante × plaza × origen × presentación × mes)
# tomada de la capa Oro, solo con presentaciones convertibles a MXN/kg. Grupos a comparar: los cinco
# productos con cobertura suficiente (plátano, limón, papaya, guayaba y tamarindo).
#
#     python -m laboratorio.e3_multivariado

# %%
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.multivariate.manova import MANOVA
from statsmodels.stats.anova import anova_lm

from laboratorio.comun import BASE_DIR, RESULTADOS, SEMILLA, fmt, guardar_figura, guardar_json, rel, tabla_md

GRUPOS = ["platano", "limon", "papaya", "guayaba", "tamarindo"]
VARIABLES = {
    "log_precio": "log del precio frecuente medio (MXN/kg)",
    "amplitud": "amplitud de cotización (máx − mín) / frecuente",
    "dispersion": "coeficiente de variación del precio frecuente dentro del mes",
    "log_cotizaciones": "log del número de cotizaciones del mes",
    "cambio_mensual": "cambio logarítmico del precio frente al mes anterior de la misma serie",
}
ALFA = 0.05
PERMUTACIONES = 999


# %% [markdown]
# ## 1. Matriz multivariada

# %%
def construir_matriz(oro: pd.DataFrame) -> pd.DataFrame:
    df = oro[oro["cultivo"].isin(GRUPOS) & oro["precio_frecuente_kg_mean"].gt(0)].copy()
    df["fecha_mes"] = pd.to_datetime(df["fecha_mes"])
    serie = ["variante_id", "mercado", "origen", "presentacion"]
    df = df.sort_values([*serie, "fecha_mes"])
    df["log_precio"] = np.log(df["precio_frecuente_kg_mean"])
    df["amplitud"] = (df["precio_max_kg_mean"] - df["precio_min_kg_mean"]) / df["precio_frecuente_kg_mean"]
    df["dispersion"] = (df["precio_frecuente_kg_std"] / df["precio_frecuente_kg_mean"]).where(df["precio_frecuente_kg_count"].ge(2))
    df["log_cotizaciones"] = np.log(df["n_observaciones_precio"])
    previo = df.groupby(serie)["fecha_mes"].shift(1)
    consecutivo = (df["fecha_mes"].dt.to_period("M") - previo.dt.to_period("M")).apply(lambda x: getattr(x, "n", np.nan)) == 1
    df["cambio_mensual"] = df.groupby(serie)["log_precio"].diff().where(consecutivo)
    cols = ["cultivo", "variante", "mercado", "origen", "presentacion", "fecha_mes", *VARIABLES]
    return df[cols].dropna().reset_index(drop=True)


def describir(X: pd.DataFrame) -> dict[str, Any]:
    return {"media": X.mean(), "covarianza": X.cov(), "correlacion": X.corr()}


# %% [markdown]
# ## 2. Normalidad multivariada: Mardia, Henze-Zirkler y Q-Q de Mahalanobis

# %%
def mahalanobis2(X: np.ndarray) -> np.ndarray:
    centro = X - X.mean(axis=0)
    S = np.cov(X, rowvar=False, bias=True)
    return np.einsum("ij,jk,ik->i", centro, np.linalg.inv(S), centro)


def mardia(X: np.ndarray) -> dict[str, float]:
    n, p = X.shape
    centro = X - X.mean(axis=0)
    S_inv = np.linalg.inv(np.cov(X, rowvar=False, bias=True))
    D = centro @ S_inv @ centro.T
    b1 = (D ** 3).sum() / n ** 2
    b2 = (np.diag(D) ** 2).sum() / n
    est_asim = n * b1 / 6
    gl = p * (p + 1) * (p + 2) / 6
    z_curt = (b2 - p * (p + 2)) / np.sqrt(8 * p * (p + 2) / n)
    return {"asimetria_b1": b1, "chi2_asimetria": est_asim, "gl": gl, "p_asimetria": float(stats.chi2.sf(est_asim, gl)),
            "curtosis_b2": b2, "curtosis_esperada": p * (p + 2), "z_curtosis": z_curt, "p_curtosis": float(2 * stats.norm.sf(abs(z_curt)))}


def henze_zirkler(X: np.ndarray) -> dict[str, float]:
    """Prueba de Henze-Zirkler (1990) con su aproximación log-normal del estadístico."""
    n, p = X.shape
    centro = X - X.mean(axis=0)
    S_inv = np.linalg.inv(np.cov(X, rowvar=False, bias=True))
    Dj = np.einsum("ij,jk,ik->i", centro, S_inv, centro)
    Djk = (np.einsum("ij,jk,ik->i", centro, S_inv, centro)[:, None] + Dj[None, :] - 2 * centro @ S_inv @ centro.T)
    b = (1 / np.sqrt(2)) * ((n * (2 * p + 1)) / 4) ** (1 / (p + 4))
    hz = (n * (1 / n ** 2 * np.exp(-(b ** 2) / 2 * Djk).sum()
               - 2 * (1 + b ** 2) ** (-p / 2) / n * np.exp(-(b ** 2) / (2 * (1 + b ** 2)) * Dj).sum()
               + (1 + 2 * b ** 2) ** (-p / 2)))
    w = (1 + b ** 2) * (1 + 3 * b ** 2)
    a = 1 + 2 * b ** 2
    mu = 1 - a ** (-p / 2) * (1 + p * b ** 2 / a + p * (p + 2) * b ** 4 / (2 * a ** 2))
    si2 = (2 * (1 + 4 * b ** 2) ** (-p / 2) + 2 * a ** (-p) * (1 + 2 * p * b ** 4 / a ** 2 + 3 * p * (p + 2) * b ** 8 / (4 * a ** 4))
           - 4 * w ** (-p / 2) * (1 + 3 * p * b ** 4 / (2 * w) + p * (p + 2) * b ** 8 / (2 * w ** 2)))
    pmu = np.log(np.sqrt(mu ** 4 / (si2 + mu ** 2)))
    psi = np.sqrt(np.log((si2 + mu ** 2) / mu ** 2))
    return {"HZ": float(hz), "p": float(stats.lognorm.sf(hz, psi, scale=np.exp(pmu)))}


def box_m(X: pd.DataFrame, grupos: pd.Series) -> dict[str, float]:
    p = X.shape[1]
    k = grupos.nunique()
    n_i = grupos.value_counts()
    S_p = sum((n_i[g] - 1) * X[grupos == g].cov() for g in n_i.index) / (len(X) - k)
    M = (len(X) - k) * np.log(np.linalg.det(S_p)) - sum((n_i[g] - 1) * np.log(np.linalg.det(X[grupos == g].cov())) for g in n_i.index)
    c = (sum(1 / (n_i - 1)) - 1 / (len(X) - k)) * (2 * p ** 2 + 3 * p - 1) / (6 * (p + 1) * (k - 1))
    gl = p * (p + 1) * (k - 1) / 2
    chi2 = M * (1 - c)
    return {"M": float(M), "chi2": float(chi2), "gl": gl, "p": float(stats.chi2.sf(chi2, gl))}


# %% [markdown]
# ## 3. Componentes principales sobre variables estandarizadas

# %%
def pca(X: pd.DataFrame) -> dict[str, Any]:
    Z = (X - X.mean()) / X.std(ddof=1)
    R = np.corrcoef(Z.to_numpy(), rowvar=False)
    valores, vectores = np.linalg.eigh(R)
    orden = np.argsort(valores)[::-1]
    valores, vectores = valores[orden], vectores[:, orden]
    # Signo convencional: la carga de mayor magnitud de cada componente es positiva.
    for j in range(vectores.shape[1]):
        if vectores[np.argmax(np.abs(vectores[:, j])), j] < 0:
            vectores[:, j] *= -1
    puntajes = Z.to_numpy() @ vectores
    cargas = pd.DataFrame(vectores * np.sqrt(valores), index=X.columns, columns=[f"CP{i + 1}" for i in range(len(valores))])
    return {"valores_propios": valores, "varianza_explicada": valores / valores.sum(),
            "acumulada": np.cumsum(valores) / valores.sum(), "vectores": vectores, "cargas": cargas,
            "puntajes": pd.DataFrame(puntajes, columns=cargas.columns), "kaiser": int((valores > 1).sum())}


# Nombres de negocio acordados tras leer las cargas; se aplican solo si el patrón de signos
# dominante (|carga| ≥ 0.5) sigue siendo el mismo. Si los datos cambian, se usa el nombre automático.
NOMBRES_NEGOCIO = {
    ("CP1", (("dispersion", -1), ("log_cotizaciones", -1), ("log_precio", 1))): "Índice de nicho: precio alto en un mercado delgado y estable",
    ("CP2", (("cambio_mensual", 1),)): "Índice de impulso: alza del precio frente al mes anterior",
    ("CP3", (("amplitud", 1),)): "Índice de margen de negociación: distancia entre cotización máxima y mínima",
}


def nombrar(cargas: pd.DataFrame, componente: str) -> str:
    """Nombre de negocio a partir de las cargas dominantes (|carga| ≥ 0.5)."""
    c = cargas[componente]
    patron = tuple(sorted((k, int(np.sign(v))) for k, v in c[c.abs() >= 0.5].items()))
    if (componente, patron) in NOMBRES_NEGOCIO:
        return NOMBRES_NEGOCIO[(componente, patron)]
    etiquetas = {"log_precio": "nivel de precio", "amplitud": "amplitud de cotización", "dispersion": "volatilidad dentro del mes",
                 "log_cotizaciones": "profundidad de mercado (n.º de cotizaciones)", "cambio_mensual": "movimiento mes a mes"}
    dominantes = c[c.abs() >= 0.5].sort_values(key=np.abs, ascending=False)
    if dominantes.empty:
        dominantes = c.reindex(c.abs().sort_values(ascending=False).index[:1])
    partes = [("+" if v > 0 else "−") + " " + etiquetas.get(k, k) for k, v in dominantes.items()]
    return "Índice de " + ", ".join(partes)


# %% [markdown]
# ## 4. MANOVA de un factor (producto) y contraste con ANOVA separados

# %%
def manova(datos: pd.DataFrame) -> dict[str, Any]:
    formula = " + ".join(VARIABLES) + " ~ C(cultivo)"
    res = MANOVA.from_formula(formula, data=datos).mv_test()
    tabla = res.results["C(cultivo)"]["stat"]
    stats_ = {k: {"valor": float(tabla.loc[k, "Value"]), "F": float(tabla.loc[k, "F Value"]),
                  "gl_num": float(tabla.loc[k, "Num DF"]), "gl_den": float(tabla.loc[k, "Den DF"]), "p": float(tabla.loc[k, "Pr > F"])}
              for k in tabla.index}
    return stats_


def pillai_permutacion(datos: pd.DataFrame, n_perm: int = PERMUTACIONES, semilla: int = SEMILLA) -> dict[str, float]:
    """Prueba de permutación de la traza de Pillai: no supone normalidad multivariada."""
    Y = datos[list(VARIABLES)].to_numpy()
    g = datos["cultivo"].to_numpy()

    def pillai(etiquetas):
        media = Y.mean(axis=0)
        H = np.zeros((Y.shape[1], Y.shape[1]))
        E = np.zeros_like(H)
        for nivel in np.unique(etiquetas):
            sub = Y[etiquetas == nivel]
            d = (sub.mean(axis=0) - media)[:, None]
            H += len(sub) * d @ d.T
            c = sub - sub.mean(axis=0)
            E += c.T @ c
        return float(np.trace(H @ np.linalg.inv(H + E)))

    observado = pillai(g)
    rng = np.random.default_rng(semilla)
    mayores = sum(pillai(rng.permutation(g)) >= observado for _ in range(n_perm))
    return {"pillai": observado, "permutaciones": n_perm, "p": (mayores + 1) / (n_perm + 1)}


def anovas_separados(datos: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for v in VARIABLES:
        t = anova_lm(ols(f"{v} ~ C(cultivo)", data=datos).fit(), typ=2)
        filas.append({"variable": v, "F": t.loc["C(cultivo)", "F"], "p": t.loc["C(cultivo)", "PR(>F)"]})
    out = pd.DataFrame(filas)
    out["p_bonferroni"] = np.minimum(out["p"] * len(out), 1)
    return out


def tasa_error_familia(m: int, alfa: float = ALFA) -> float:
    return 1 - (1 - alfa) ** m


# %% [markdown]
# ## 5. Figuras, informe y mapa para el tablero

# %%
COLORES = {"platano": "#c9a227", "limon": "#3a9d23", "papaya": "#e2711d", "guayaba": "#b5179e", "tamarindo": "#7f4f24"}


def figuras(datos: pd.DataFrame, X: pd.DataFrame, P: dict[str, Any], carpeta: Path) -> dict[str, Path]:
    import matplotlib.pyplot as plt
    out = {}
    d2 = mahalanobis2(X.to_numpy())
    teor = stats.chi2.ppf((np.arange(1, len(d2) + 1) - 0.5) / len(d2), X.shape[1])
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.scatter(teor, np.sort(d2), s=10); lim = max(teor.max(), d2.max())
    ax.plot([0, lim], [0, lim], "k--", lw=.8)
    ax.set_xlabel(f"cuantiles χ²({X.shape[1]})"); ax.set_ylabel("distancia de Mahalanobis² ordenada"); ax.set_title("Q-Q de Mahalanobis")
    out["qq"] = guardar_figura(fig, carpeta / "qq_mahalanobis.png")

    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    k = np.arange(1, len(P["valores_propios"]) + 1)
    ax.bar(k, P["varianza_explicada"] * 100, alpha=.7, label="% varianza")
    ax.plot(k, P["acumulada"] * 100, marker="o", color="k", label="% acumulado")
    ax.axhline(100 / len(k), color="r", ls=":", lw=1, label="criterio de Kaiser (λ = 1)")
    ax.set_xticks(k); ax.set_xlabel("componente"); ax.set_ylabel("%"); ax.set_title("Gráfica de sedimentación"); ax.legend(fontsize=8)
    out["scree"] = guardar_figura(fig, carpeta / "sedimentacion.png")

    pts = P["puntajes"]
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for g in GRUPOS:
        m = datos["cultivo"].eq(g).to_numpy()
        ax.scatter(pts.loc[m, "CP1"], pts.loc[m, "CP2"], s=12, alpha=.45, color=COLORES[g], label=g)
        ax.scatter(pts.loc[m, "CP1"].mean(), pts.loc[m, "CP2"].mean(), s=160, marker="X", color=COLORES[g], edgecolor="k")
    escala = np.abs(pts[["CP1", "CP2"]]).max().max() / np.abs(P["cargas"][["CP1", "CP2"]]).max().max() * 0.8
    for v, (c1, c2) in P["cargas"][["CP1", "CP2"]].iterrows():
        ax.arrow(0, 0, c1 * escala, c2 * escala, color="k", width=.01, head_width=.12, alpha=.8)
        ax.text(c1 * escala * 1.1, c2 * escala * 1.1, v, fontsize=9)
    ax.axhline(0, color="grey", lw=.5); ax.axvline(0, color="grey", lw=.5)
    ax.set_xlabel(f"CP1 ({P['varianza_explicada'][0] * 100:.1f} %)"); ax.set_ylabel(f"CP2 ({P['varianza_explicada'][1] * 100:.1f} %)")
    ax.set_title("Biplot: meses-serie por producto (X = centroide)"); ax.legend(fontsize=8)
    out["biplot"] = guardar_figura(fig, carpeta / "biplot.png")

    fig, ax = plt.subplots(figsize=(6, 4.6))
    corr = X.corr()
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=35, ha="right"); ax.set_yticks(range(len(corr)), corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax); ax.set_title("Matriz de correlaciones")
    out["correlacion"] = guardar_figura(fig, carpeta / "correlaciones.png")
    return out


def ejecutar(oro_path: Path, salida: Path, docs: Path) -> dict[str, Any]:
    oro = pd.read_csv(oro_path)
    datos = construir_matriz(oro)
    X = datos[list(VARIABLES)]
    desc = describir(X)
    mar, hz = mardia(X.to_numpy()), henze_zirkler(X.to_numpy())
    normal = mar["p_asimetria"] > ALFA and mar["p_curtosis"] > ALFA and hz["p"] > ALFA
    bm = box_m(X, datos["cultivo"])
    P = pca(X)
    nombres = {c: nombrar(P["cargas"], c) for c in P["cargas"].columns[:3]}
    mv = manova(datos)
    perm = pillai_permutacion(datos)
    sep = anovas_separados(datos)
    carpeta = docs / "multivariado"
    figs = figuras(datos, X, P, carpeta)
    centroides = pd.concat([datos[["cultivo"]], P["puntajes"][["CP1", "CP2"]]], axis=1).groupby("cultivo")[["CP1", "CP2"]].mean().reindex(GRUPOS)
    mapa = pd.concat([datos[["cultivo", "variante", "mercado", "origen", "fecha_mes"]].assign(fecha_mes=datos["fecha_mes"].dt.strftime("%Y-%m")),
                      P["puntajes"][["CP1", "CP2"]].round(4)], axis=1)
    salida.mkdir(parents=True, exist_ok=True)
    mapa.to_csv(salida / "mapa_componentes.csv", index=False)

    cc = oro[["precio_min_kg_mean", "precio_max_kg_mean", "precio_frecuente_kg_mean"]].corr().to_numpy()[np.triu_indices(3, 1)]
    corr = X.corr()
    pares = [(a, b, corr.loc[a, b]) for i, a in enumerate(corr.columns) for b in corr.columns[i + 1:]]
    par = max(pares, key=lambda t: abs(t[2]))
    resultado = {"colinealidad_min": float(cc.min()), "colinealidad_max": float(cc.max()), "par_mas_correlacionado": par, "n": len(datos), "grupos": datos["cultivo"].value_counts().reindex(GRUPOS).to_dict(),
                 "variables": VARIABLES, "media": desc["media"].to_dict(), "covarianza": desc["covarianza"].to_dict(),
                 "correlacion": desc["correlacion"].to_dict(), "mardia": mar, "henze_zirkler": hz, "normal_multivariada": normal,
                 "box_m": bm, "pca": {"valores_propios": P["valores_propios"], "varianza_explicada": P["varianza_explicada"],
                                      "acumulada": P["acumulada"], "kaiser": P["kaiser"], "cargas": P["cargas"].to_dict(), "nombres": nombres},
                 "manova": mv, "pillai_permutacion": perm, "anovas_separados": sep.to_dict("records"),
                 "tasa_error_familia_5_anovas": tasa_error_familia(len(VARIABLES)), "centroides": centroides.to_dict("index")}
    guardar_json(resultado, salida / "resultados.json")
    md = informe(datos, X, desc, resultado, P, sep, figs, docs)
    (docs / "multivariado.md").write_text(md, encoding="utf-8")
    return resultado


def interpretar_centroides(cent: pd.DataFrame, nombres: dict[str, str]) -> list[str]:
    lineas = []
    for eje in ("CP1", "CP2"):
        orden = cent[eje].sort_values()
        lineas.append(f"- En **{eje}** ({nombres[eje].lower()}), el producto más alto es **{orden.index[-1]}** ({fmt(orden.iloc[-1], 2)}) "
                 f"y el más bajo **{orden.index[0]}** ({fmt(orden.iloc[0], 2)}).")
    return lineas


def informe(datos, X, desc, r, P, sep, figs, docs: Path) -> str:
    carpeta = docs
    mar, hz, bm, mv, perm = r["mardia"], r["henze_zirkler"], r["box_m"], r["manova"], r["pillai_permutacion"]
    nombres = r["pca"]["nombres"]
    cargas = P["cargas"].iloc[:, :3].copy()
    cargas.insert(0, "variable", cargas.index)
    ve = pd.DataFrame({"componente": P["cargas"].columns, "valor propio": P["valores_propios"],
                       "% varianza": P["varianza_explicada"] * 100, "% acumulado": P["acumulada"] * 100})
    cent = pd.DataFrame(r["centroides"]).T
    lineas = ["# Laboratorio E3 · Mapa multivariado (normalidad multivariada, PCA y MANOVA)\n",
         "> Documento **generado** por `python -m laboratorio.e3_multivariado` desde `data/oro/panel_mensual.csv`. "
         "Resultados completos en `laboratorio/resultados/e3/resultados.json`; coordenadas del mapa en `laboratorio/resultados/e3/mapa_componentes.csv`.\n",
         "## 1. Matriz multivariada\n",
         f"Unidad de análisis: una serie de cotización (variante × plaza × origen × presentación) en un mes, con precio convertible a MXN/kg. "
         f"**n = {r['n']}** observaciones completas en {len(GRUPOS)} grupos (productos): "
         + ", ".join(f"{g} {r['grupos'][g]}" for g in GRUPOS) + ".\n",
         "| Variable | Definición |", "|---|---|", *[f"| `{k}` | {v} |" for k, v in VARIABLES.items()], "",
         f"Se excluyeron precio mínimo y máximo como variables separadas porque son casi colineales con el precio frecuente (correlaciones de {fmt(r['colinealidad_min'], 3)} a {fmt(r['colinealidad_max'], 3)} en Oro) y harían casi singular la matriz de covarianzas; su información entra en `amplitud`.\n",
         "Vector de medias:\n", tabla_md(desc["media"].rename("media").reset_index().rename(columns={"index": "variable"}), 4) + "\n",
         "Matriz de covarianzas:\n", tabla_md(desc["covarianza"].reset_index().rename(columns={"index": "variable"}), 4) + "\n",
         f"![Correlaciones]({rel(figs['correlacion'], carpeta)})\n",
         "## 2. Normalidad multivariada\n",
         f"- **Mardia** · asimetría b₁ = {fmt(mar['asimetria_b1'], 3)}, χ² = {fmt(mar['chi2_asimetria'], 1)} (gl {fmt(mar['gl'], 0)}), p = {fmt(mar['p_asimetria'], 4)}; "
         f"curtosis b₂ = {fmt(mar['curtosis_b2'], 2)} (esperada {fmt(mar['curtosis_esperada'], 0)}), z = {fmt(mar['z_curtosis'], 2)}, p = {fmt(mar['p_curtosis'], 4)}.",
         f"- **Henze-Zirkler** · HZ = {fmt(hz['HZ'], 3)}, p = {fmt(hz['p'], 4)}.",
         f"- Conclusión: {'no se rechaza' if r['normal_multivariada'] else '**se rechaza**'} la normalidad multivariada al 5 %.\n",
         f"![Q-Q Mahalanobis]({rel(figs['qq'], carpeta)})\n",
         "La gráfica Q-Q compara las distancias de Mahalanobis² con los cuantiles χ²; los puntos que se alejan arriba a la derecha son meses-serie atípicos (colas más pesadas que la normal).\n",
         "## 3. Componentes principales\n",
         "Las variables tienen escalas distintas (logaritmos, proporciones, cambios), por eso el PCA se hace sobre la **matriz de correlaciones** (variables estandarizadas).\n",
         tabla_md(ve, 3) + "\n",
         f"![Sedimentación]({rel(figs['scree'], carpeta)})\n",
         f"Criterio de Kaiser: {P['kaiser']} componentes con valor propio > 1; los dos primeros explican {fmt(P['acumulada'][1] * 100, 1)} % de la varianza.\n",
         "Cargas (correlación variable–componente):\n", tabla_md(cargas, 3) + "\n",
         "Nombres de negocio de los componentes (derivados de las cargas con |carga| ≥ 0.5):\n",
         *[f"- **{c}** · {n}" for c, n in nombres.items()], "",
         f"![Biplot]({rel(figs['biplot'], carpeta)})\n",
         "## 4. El mapa: interpretación para el cliente\n",
         "Centroides de cada producto en el plano CP1–CP2:\n",
         tabla_md(cent.reset_index().rename(columns={"index": "producto"}), 3) + "\n",
         *interpretar_centroides(cent, nombres), "",
         "Lectura para el comprador: productos cercanos en el mapa se comportan parecido en precio, estabilidad y profundidad de mercado, "
         "así que pueden gestionarse con la misma estrategia de compra; los alejados requieren reglas distintas (por ejemplo, contratos a precio fijo "
         "para los de mayor volatilidad). El mapa se publica en `tablero/laboratorio.html`.\n",
         "## 5. MANOVA: ¿los productos difieren en las cinco variables a la vez?\n",
         f"Supuesto de homogeneidad de matrices de covarianza (M de Box): χ² = {fmt(bm['chi2'], 1)}, gl = {fmt(bm['gl'], 0)}, p = {fmt(bm['p'], 4)} → "
         f"{'homogéneas' if bm['p'] > ALFA else '**no homogéneas**'}.\n",
         "| Estadístico | Valor | F aprox. | gl num | gl den | p |", "|---|---|---|---|---|---|",
         *[f"| {k} | {fmt(v['valor'], 4)} | {fmt(v['F'], 2)} | {fmt(v['gl_num'], 0)} | {fmt(v['gl_den'], 1)} | {fmt(v['p'], 6)} |" for k, v in mv.items()], "",
         f"Prueba de permutación de la traza de Pillai ({perm['permutaciones']} permutaciones, semilla fija): Pillai = {fmt(perm['pillai'], 4)}, p = {fmt(perm['p'], 4)}.\n",
         "**Puerta de calidad 3.** "
         + ("Los supuestos de normalidad multivariada y de covarianzas homogéneas se sostienen, así que Wilks es válido. "
            if r["normal_multivariada"] and bm["p"] > ALFA else
            "Como la normalidad multivariada y/o la homogeneidad de covarianzas no se cumplen, la conclusión se basa en la **traza de Pillai** "
            "(la más robusta a esas violaciones) y se confirma con la **prueba de permutación**, que no depende de la normalidad. "
            "Lambda de Wilks se reporta, pero no se usa como evidencia principal. ")
         + f"Conclusión: los cinco productos {'**sí difieren**' if perm['p'] < ALFA else 'no difieren significativamente'} en el vector de variables al 5 %.\n",
         "### ¿Por qué no basta con cinco ANOVA separados?\n",
         tabla_md(sep, 6) + "\n",
         f"- Correr 5 ANOVA al 5 % cada uno eleva la probabilidad de al menos un falso positivo a 1 − 0.95⁵ = {fmt(r['tasa_error_familia_5_anovas'] * 100, 1)} % si no se corrige.",
         f"- Los ANOVA separados ignoran las correlaciones entre variables (la más fuerte aquí es {r['par_mas_correlacionado'][0]} con {r['par_mas_correlacionado'][1]}, r = {fmt(r['par_mas_correlacionado'][2], 2)}); la MANOVA usa la matriz de covarianzas completa "
         "y puede detectar diferencias en combinaciones de variables que ninguna variable muestra por sí sola.",
         "- Por eso la MANOVA es la prueba global; los ANOVA con corrección de Bonferroni solo indican qué variables contribuyen.\n",
         "## Limitaciones\n",
         "- Las observaciones de una misma serie en meses consecutivos no son independientes; la permutación a nivel de mes-serie no corrige esa dependencia, así que los p-valores son optimistas.",
         "- Los grupos tienen tamaños distintos y mezclan plazas y orígenes; un diseño con plaza como segundo factor requeriría más series pareadas."]
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Laboratorio E3: PCA y MANOVA")
    ap.add_argument("--oro", type=Path, default=BASE_DIR / "data" / "oro" / "panel_mensual.csv")
    ap.add_argument("--salida", type=Path, default=RESULTADOS / "e3")
    ap.add_argument("--docs", type=Path, default=BASE_DIR / "docs" / "E3")
    a = ap.parse_args(argv)
    r = ejecutar(a.oro, a.salida, a.docs)
    print(f"E3: n={r['n']} normal={r['normal_multivariada']} Pillai p perm={r['pillai_permutacion']['p']:.4f} · {a.docs / 'multivariado.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
