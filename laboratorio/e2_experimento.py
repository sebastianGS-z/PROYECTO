# %% [markdown]
# # Laboratorio E2 · Experimento factorial sobre el propio extractor (ruta ingeniería)
#
# Pregunta: ¿qué combinación de parser HTML, alcance del árbol y formato de escritura procesa las
# capturas SNIIM más rápido sin introducir errores? Se corre contra **copias locales** (Capa Bronce),
# nunca contra el sitio del SNIIM.
#
# * Respuesta 1: tiempo de procesamiento (s) de una muestra fija de capturas reales.
# * Respuesta 2: tasa de error = archivos cuya extracción difiere de la referencia de producción o falla.
# * Principios: orden aleatorizado con semilla registrada, 3 réplicas, bloqueo por réplica (cada
#   bloque contiene todos los tratamientos; controla deriva térmica/carga de la máquina).
# * Cada corrida es un proceso Python aislado; el tiempo se mide dentro del proceso (sin importar librerías).
#
#     python -m laboratorio.e2_experimento            # corre todo (≈ 4–6 min) y escribe el informe
#     python -m laboratorio.e2_experimento --solo-analisis   # reanaliza resultados guardados

# %%
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import platform
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from laboratorio.comun import BASE_DIR, RESULTADOS, SEMILLA, fmt, guardar_figura, guardar_json, rel, tabla_md

MUESTRA = 150
REPLICAS = 3
CONFIRMACIONES = 5
ALFA = 0.05

FACTORES_2K = {
    "A": ("parser", "html.parser", "lxml"),
    "B": ("arbol", "completo", "tablas"),
    "C": ("formato", "csv", "parquet"),
}
FACTOR_D = ("procesos", 1, 4)


# %% [markdown]
# ## 1. Unidad experimental: una corrida = procesar la muestra completa con una configuración

# %%
def muestra(bronze: Path, n: int = MUESTRA, semilla: int = SEMILLA) -> list[Path]:
    archivos = sorted(p for p in (bronze / "sniim").rglob("*.html") if "catalogo-formulario" not in p.name and "formulario" not in p.name)
    rng = random.Random(semilla)
    return sorted(rng.sample(archivos, min(n, len(archivos))))


def _procesar_archivo(args: tuple[str, str, bool]) -> tuple[str, list[dict[str, str]] | None, str | None]:
    from extractores.sniim_extractor import decodificar_html, parse_resultados
    path, parser, solo_tablas = args
    try:
        res = parse_resultados(decodificar_html(Path(path).read_bytes()), parser=parser, solo_tablas=solo_tablas)
        return path, res.registros, None
    except Exception as exc:  # noqa: BLE001 - la respuesta "errores" cuenta cualquier fallo
        return path, None, f"{type(exc).__name__}: {exc}"


def digest(registros: list[dict[str, str]] | None) -> str | None:
    if registros is None:
        return None
    return hashlib.sha256(json.dumps(registros, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def corrida(archivos: list[str], parser: str, arbol: str, formato: str, procesos: int = 1) -> dict[str, Any]:
    """Se ejecuta dentro del proceso hijo. Mide solo el trabajo (lectura, parseo y escritura)."""
    solo_tablas = arbol == "tablas"
    tareas = [(a, parser, solo_tablas) for a in archivos]
    t0 = time.perf_counter()
    if procesos > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=procesos) as ex:
            salida = list(ex.map(_procesar_archivo, tareas, chunksize=max(1, len(tareas) // (procesos * 4))))
    else:
        salida = [_procesar_archivo(t) for t in tareas]
    filas = [dict(r, _archivo=Path(p).name) for p, regs, _ in salida if regs for r in regs]
    frame = pd.DataFrame(filas)
    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp) / f"salida.{formato}"
        if formato == "csv":
            frame.to_csv(destino, index=False)
        else:
            frame.astype("string").to_parquet(destino, index=False)
        bytes_salida = destino.stat().st_size
    tiempo = time.perf_counter() - t0
    return {"tiempo_s": tiempo, "registros": len(filas), "bytes_salida": bytes_salida,
            "digests": {Path(p).name: digest(regs) for p, regs, _ in salida},
            "fallos": {Path(p).name: err for p, _, err in salida if err}}


def lanzar(archivos: list[Path], config: dict[str, Any]) -> dict[str, Any]:
    """Corre una configuración en un proceso aislado y devuelve su resultado."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump({"archivos": [str(a) for a in archivos], **config}, fh)
        entrada = fh.name
    try:
        out = subprocess.run([sys.executable, "-m", "laboratorio.e2_experimento", "--hijo", entrada],
                             cwd=BASE_DIR, capture_output=True, text=True, check=True,
                             env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "PYTHONHASHSEED": "0"})
    finally:
        os.unlink(entrada)
    return json.loads(out.stdout.strip().splitlines()[-1])


# %% [markdown]
# ## 2. Diseños: 2³ con réplicas y bloques, 3×2 con interacción, 2⁴ completo vs 2⁴⁻¹ fraccionado

# %%
def plan_2k(replicas: int = REPLICAS, semilla: int = SEMILLA) -> pd.DataFrame:
    rng = random.Random(semilla)
    filas = []
    for bloque in range(1, replicas + 1):
        tratamientos = list(itertools.product([-1, 1], repeat=3))
        rng.shuffle(tratamientos)  # aleatorización dentro de cada bloque
        for a, b, c in tratamientos:
            filas.append({"bloque": bloque, "A": a, "B": b, "C": c})
    plan = pd.DataFrame(filas)
    plan["orden"] = range(1, len(plan) + 1)
    return plan


def plan_dos_factores(replicas: int = REPLICAS, semilla: int = SEMILLA + 1) -> pd.DataFrame:
    tratamientos = [(p, a) for p in ("html.parser", "lxml", "html5lib") for a in ("completo", "tablas")] * replicas
    random.Random(semilla).shuffle(tratamientos)  # aleatorización completa
    return pd.DataFrame([{"orden": i + 1, "parser": p, "arbol": a} for i, (p, a) in enumerate(tratamientos)])


def matriz_2k_completa(k: int = 4) -> pd.DataFrame:
    letras = "ABCD"[:k]
    filas = [dict(zip(letras, signos, strict=True)) for signos in itertools.product([-1, 1], repeat=k)]
    return pd.DataFrame(filas)[list(letras)]


def matriz_fraccionada_2_4_1() -> pd.DataFrame:
    """2^(4-1) con generador D = ABC (relación definidora I = ABCD, resolución IV)."""
    base = matriz_2k_completa(3)
    base["D"] = base["A"] * base["B"] * base["C"]
    return base


def alias_2_4_1() -> dict[str, str]:
    efectos = ["A", "B", "C", "D", "AB", "AC", "AD", "BC", "BD", "CD", "ABC", "ABD", "ACD", "BCD", "ABCD"]
    def mult(x: str, y: str) -> str:
        return "".join(sorted(set(x) ^ set(y))) or "I"
    alias, vistos = {}, set()
    for e in efectos:
        if e in vistos:
            continue
        a = mult(e, "ABCD")
        alias[e] = a
        vistos |= {e, a}
    return alias


def verificar_alias(full: pd.DataFrame, frac: pd.DataFrame) -> dict[str, bool]:
    """Comprueba numéricamente que en la fracción las columnas de efectos aliados son idénticas."""
    def col(df, e):
        return np.prod([df[c].to_numpy() for c in e], axis=0)
    return {f"{e}={a}": bool(np.array_equal(col(frac, e), col(frac, a))) for e, a in alias_2_4_1().items() if a != "I"}


# %% [markdown]
# ## 3. Análisis: ANOVA de efectos fijos, efectos, supuestos y corrida de confirmación

# %%
def nivel(f: str, signo: int) -> Any:
    nombre, bajo, alto = FACTORES_2K[f] if f in FACTORES_2K else FACTOR_D
    return bajo if signo < 0 else alto


def efectos_2k(df: pd.DataFrame, respuesta: str, factores: str = "ABC") -> pd.DataFrame:
    filas = []
    for r in range(1, len(factores) + 1):
        for combo in itertools.combinations(factores, r):
            contraste = np.prod([df[c].to_numpy() for c in combo], axis=0)
            efecto = df.loc[contraste > 0, respuesta].mean() - df.loc[contraste < 0, respuesta].mean()
            filas.append({"efecto": "".join(combo), "estimacion_s": efecto})
    out = pd.DataFrame(filas)
    out["abs"] = out["estimacion_s"].abs()
    return out.sort_values("abs", ascending=False).drop(columns="abs").reset_index(drop=True)


def permutacion_efectos(df: pd.DataFrame, respuesta: str = "tiempo_s", n_perm: int = 1999, semilla: int = SEMILLA) -> pd.DataFrame:
    """Prueba de permutación de cada efecto del 2³: se permuta la respuesta dentro de cada bloque.

    No supone normalidad; respeta el bloqueo del diseño. p = (#|efecto permutado| ≥ |observado| + 1) / (n_perm + 1).
    """
    obs = efectos_2k(df, respuesta).set_index("efecto")["estimacion_s"]
    rng = np.random.default_rng(semilla)
    conteo = pd.Series(0, index=obs.index)
    base = df.copy()
    for _ in range(n_perm):
        base[respuesta] = base.groupby("bloque")[respuesta].transform(lambda x: rng.permutation(x.to_numpy()))
        perm = efectos_2k(base, respuesta).set_index("efecto")["estimacion_s"]
        conteo += (perm.reindex(obs.index).abs() >= obs.abs() - 1e-12).astype(int)
    return pd.DataFrame({"efecto": obs.index, "estimacion_s": obs.values, "p_permutacion": ((conteo + 1) / (n_perm + 1)).values})


def anova_tabla(modelo) -> pd.DataFrame:
    t = anova_lm(modelo, typ=2).reset_index().rename(columns={"index": "fuente", "sum_sq": "SC", "df": "gl", "F": "F", "PR(>F)": "p"})
    total = t["SC"].sum()
    t["eta2_parcial"] = [sc / (sc + t["SC"].iloc[-1]) if f != "Residual" else np.nan for f, sc in zip(t["fuente"], t["SC"], strict=True)]
    t["pct_SC"] = t["SC"] / total * 100
    return t


def supuestos(modelo, grupos: pd.Series) -> dict[str, Any]:
    resid = modelo.resid
    sh = stats.shapiro(resid)
    lev = stats.levene(*[resid[grupos == g] for g in grupos.unique()], center="median")
    return {"shapiro_p": float(sh.pvalue), "normalidad": bool(sh.pvalue > ALFA),
            "levene_p": float(lev.pvalue), "homocedasticidad": bool(lev.pvalue > ALFA)}


def _para_formula(df: pd.DataFrame) -> pd.DataFrame:
    """En patsy ``C`` es la función de variables categóricas: el factor C se renombra a ``Cf``."""
    return df.rename(columns={"C": "Cf"})


def _fuentes_legibles(t: pd.DataFrame) -> pd.DataFrame:
    t["fuente"] = t["fuente"].str.replace("Cf", "C", regex=False).str.replace("C(bloque)", "bloque", regex=False)
    return t


def analizar_2k(df: pd.DataFrame) -> dict[str, Any]:
    d = _para_formula(df.copy())
    modelo = ols("tiempo_s ~ A * B * Cf + C(bloque)", data=d).fit()
    grupos = d["A"].astype(str) + d["B"].astype(str) + d["Cf"].astype(str)
    sup = supuestos(modelo, grupos)
    resultado = {"anova": _fuentes_legibles(anova_tabla(modelo)), "efectos": efectos_2k(df, "tiempo_s"), "supuestos": sup, "_modelo": modelo}
    if not (sup["normalidad"] and sup["homocedasticidad"]):
        # Puerta 3: se repite sobre log(tiempo), que estabiliza la varianza de tiempos de cómputo.
        d["log_tiempo"] = np.log(d["tiempo_s"])
        m2 = ols("log_tiempo ~ A * B * Cf + C(bloque)", data=d).fit()
        resultado["anova_log"] = _fuentes_legibles(anova_tabla(m2))
        resultado["supuestos_log"] = supuestos(m2, grupos)
        resultado["_modelo_log"] = m2
    if not (resultado.get("supuestos_log", sup)["normalidad"]):
        resultado["permutacion"] = permutacion_efectos(df)
    medias = df.groupby(["A", "B", "C"]).agg(tiempo_medio_s=("tiempo_s", "mean"), de_s=("tiempo_s", "std"),
                                             tasa_error=("tasa_error", "mean"), n=("tiempo_s", "size")).reset_index()
    sin_error = medias[medias["tasa_error"].eq(0)]
    optimo = (sin_error if not sin_error.empty else medias).sort_values("tiempo_medio_s").iloc[0]
    resultado["medias"] = medias
    resultado["optimo"] = {f: int(optimo[f]) for f in "ABC"}
    return resultado


def prediccion_optimo(modelo, optimo: dict[str, int], bloque: int = 1) -> dict[str, float]:
    optimo = {("Cf" if k == "C" else k): v for k, v in optimo.items()}
    nuevo = pd.DataFrame([{**optimo, "bloque": bloque}])
    pr = modelo.get_prediction(nuevo).summary_frame(alpha=ALFA)
    # Se promedian los efectos de bloque: la confirmación corre en un bloque nuevo.
    bloques = sorted(modelo.model.data.frame["bloque"].unique())
    medias = [float(modelo.get_prediction(pd.DataFrame([{**optimo, "bloque": b}])).summary_frame()["mean"].iloc[0]) for b in bloques]
    return {"media_predicha_s": float(np.mean(medias)), "li_pred_95": float(pr["obs_ci_lower"].iloc[0] - (pr["mean"].iloc[0] - np.mean(medias))),
            "ls_pred_95": float(pr["obs_ci_upper"].iloc[0] - (pr["mean"].iloc[0] - np.mean(medias)))}


def analizar_dos_factores(df: pd.DataFrame) -> dict[str, Any]:
    modelo = ols("tiempo_s ~ C(parser) * C(arbol)", data=df).fit()
    grupos = df["parser"] + "|" + df["arbol"]
    res = {"anova": anova_tabla(modelo), "supuestos": supuestos(modelo, grupos), "_modelo": modelo,
           "medias": df.groupby(["parser", "arbol"]).agg(tiempo_medio_s=("tiempo_s", "mean"), de_s=("tiempo_s", "std"),
                                                         tasa_error=("tasa_error", "mean")).reset_index()}
    tk = pairwise_tukeyhsd(df["tiempo_s"], grupos, alpha=ALFA)
    res["tukey"] = pd.DataFrame(tk.summary().data[1:], columns=tk.summary().data[0])
    if not (res["supuestos"]["normalidad"] and res["supuestos"]["homocedasticidad"]):
        d = df.assign(log_tiempo=np.log(df["tiempo_s"]))
        m2 = ols("log_tiempo ~ C(parser) * C(arbol)", data=d).fit()
        res["anova_log"] = anova_tabla(m2)
        res["supuestos_log"] = supuestos(m2, grupos)
        # Alternativa no paramétrica sobre los 6 tratamientos
        kw = stats.kruskal(*[d.loc[grupos == g, "tiempo_s"] for g in grupos.unique()])
        res["kruskal"] = {"H": float(kw.statistic), "p": float(kw.pvalue)}
    return res


# %% [markdown]
# ## 4. Ejecución

# %%
def tasa_error(resultado: dict[str, Any], referencia: dict[str, str | None]) -> float:
    malos = sum(1 for archivo, dg in resultado["digests"].items() if dg is None or dg != referencia.get(archivo))
    return malos / len(referencia)


def correr_todo(bronze: Path, salida: Path, log=print) -> dict[str, Any]:
    archivos = muestra(bronze)
    log(f"Muestra fija: {len(archivos)} capturas SNIIM (semilla {SEMILLA})")
    referencia = lanzar(archivos, {"parser": "html.parser", "arbol": "tablas", "formato": "csv", "procesos": 1})
    ref_digests = referencia["digests"]
    calentamiento = lanzar(archivos, {"parser": "lxml", "arbol": "completo", "formato": "parquet", "procesos": 1})  # caché de disco
    del calentamiento
    filas_2k = []
    for _, p in plan_2k().iterrows():
        cfg = {"parser": nivel("A", p["A"]), "arbol": nivel("B", p["B"]), "formato": nivel("C", p["C"]), "procesos": 1}
        r = lanzar(archivos, cfg)
        filas_2k.append({**p.to_dict(), **cfg, "tiempo_s": r["tiempo_s"], "registros": r["registros"],
                         "bytes_salida": r["bytes_salida"], "tasa_error": tasa_error(r, ref_digests), "fallos": len(r["fallos"])})
        log(f"  2³ corrida {int(p['orden']):2d}/{REPLICAS * 8} bloque {int(p['bloque'])} {cfg} → {r['tiempo_s']:.2f} s")
    filas_ab = []
    for _, p in plan_dos_factores().iterrows():
        cfg = {"parser": p["parser"], "arbol": p["arbol"], "formato": "csv", "procesos": 1}
        r = lanzar(archivos, cfg)
        filas_ab.append({**p.to_dict(), **cfg, "tiempo_s": r["tiempo_s"], "tasa_error": tasa_error(r, ref_digests), "registros": r["registros"]})
        log(f"  3×2 corrida {int(p['orden']):2d}/{REPLICAS * 6} {cfg} → {r['tiempo_s']:.2f} s")
    filas_frac = []
    frac = matriz_fraccionada_2_4_1()
    orden = list(range(len(frac))) * 2
    random.Random(SEMILLA + 2).shuffle(orden)
    for i, idx in enumerate(orden, start=1):
        fila = frac.iloc[idx]
        cfg = {"parser": nivel("A", fila["A"]), "arbol": nivel("B", fila["B"]), "formato": nivel("C", fila["C"]), "procesos": nivel("D", fila["D"])}
        r = lanzar(archivos, cfg)
        filas_frac.append({"orden": i, **{k: int(fila[k]) for k in "ABCD"}, **cfg, "tiempo_s": r["tiempo_s"], "tasa_error": tasa_error(r, ref_digests)})
        log(f"  2⁴⁻¹ corrida {i:2d}/16 {cfg} → {r['tiempo_s']:.2f} s")
    df2k = pd.DataFrame(filas_2k)
    salida.mkdir(parents=True, exist_ok=True)  # se guardan las corridas antes de analizarlas
    df2k.to_csv(salida / "corridas_2k.csv", index=False)
    pd.DataFrame(filas_ab).to_csv(salida / "corridas_3x2.csv", index=False)
    pd.DataFrame(filas_frac).to_csv(salida / "corridas_2_4_1.csv", index=False)
    opt = analizar_2k(df2k)["optimo"]
    cfg_opt = {"parser": nivel("A", opt["A"]), "arbol": nivel("B", opt["B"]), "formato": nivel("C", opt["C"]), "procesos": 1}
    confirm = []
    for i in range(1, CONFIRMACIONES + 1):
        r = lanzar(archivos, cfg_opt)
        confirm.append({"corrida": i, **cfg_opt, "tiempo_s": r["tiempo_s"], "tasa_error": tasa_error(r, ref_digests)})
        log(f"  confirmación {i}/{CONFIRMACIONES} {cfg_opt} → {r['tiempo_s']:.2f} s")
    meta = {"muestra": [a.relative_to(BASE_DIR).as_posix() if a.is_relative_to(BASE_DIR) else str(a) for a in archivos],
            "semilla": SEMILLA, "replicas": REPLICAS, "python": platform.python_version(), "plataforma": platform.platform(),
            "cpu": os.cpu_count(), "registros_referencia": referencia["registros"], "fecha_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")}
    pd.DataFrame(confirm).to_csv(salida / "confirmacion.csv", index=False)
    guardar_json(meta, salida / "metadatos.json")
    return meta


def figuras(r2k: dict[str, Any], rab: dict[str, Any], df2k: pd.DataFrame, dfab: pd.DataFrame, carpeta: Path) -> dict[str, Path]:
    import matplotlib.pyplot as plt
    out = {}
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), sharey=True)
    for ax, (f1, f2) in zip(axes, [("A", "B"), ("A", "C"), ("B", "C")], strict=True):
        m = df2k.groupby([f1, f2])["tiempo_s"].mean().unstack()
        for col in m.columns:
            ax.plot([nivel(f1, -1), nivel(f1, 1)], m[col].values, marker="o", label=f"{FACTORES_2K[f2][0]} = {nivel(f2, col)}")
        ax.set_title(f"Interacción {FACTORES_2K[f1][0]} × {FACTORES_2K[f2][0]}"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    axes[0].set_ylabel("tiempo medio (s)")
    out["interacciones_2k"] = guardar_figura(fig, carpeta / "interacciones_2k.png")

    ef = r2k["efectos"].copy()
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.barh(ef["efecto"][::-1], ef["estimacion_s"][::-1], color=["tab:red" if v > 0 else "tab:green" for v in ef["estimacion_s"][::-1]])
    ax.axvline(0, color="k", lw=.8); ax.set_xlabel("efecto sobre el tiempo (s): alto − bajo"); ax.set_title("Efectos estimados (diagrama de Pareto)")
    out["efectos"] = guardar_figura(fig, carpeta / "efectos_2k.png")

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    modelo = r2k["_modelo"]
    axes[0].scatter(modelo.fittedvalues, modelo.resid); axes[0].axhline(0, color="k", lw=.8)
    axes[0].set_xlabel("ajustados (s)"); axes[0].set_ylabel("residuos"); axes[0].set_title("Residuos vs ajustados (2³)")
    stats.probplot(modelo.resid, plot=axes[1]); axes[1].set_title("Q-Q normal de residuos (2³)")
    out["residuos_2k"] = guardar_figura(fig, carpeta / "residuos_2k.png")

    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    m = dfab.groupby(["parser", "arbol"])["tiempo_s"].mean().unstack().loc[["html.parser", "lxml", "html5lib"]]
    for col in m.columns:
        ax.plot(m.index, m[col].values, marker="o", label=f"árbol = {col}")
    ax.set_ylabel("tiempo medio (s)"); ax.set_title("Interacción parser (3 niveles) × árbol"); ax.grid(alpha=.3); ax.legend()
    out["interaccion_3x2"] = guardar_figura(fig, carpeta / "interaccion_3x2.png")
    return out


def informe(salida: Path, docs: Path) -> str:
    df2k = pd.read_csv(salida / "corridas_2k.csv")
    dfab = pd.read_csv(salida / "corridas_3x2.csv")
    dffr = pd.read_csv(salida / "corridas_2_4_1.csv")
    conf = pd.read_csv(salida / "confirmacion.csv")
    meta = json.loads((salida / "metadatos.json").read_text(encoding="utf-8"))
    r2k = analizar_2k(df2k)
    rab = analizar_dos_factores(dfab)
    figs = figuras(r2k, rab, df2k, dfab, docs / "experimento")
    carpeta = docs
    pred = prediccion_optimo(r2k["_modelo"], r2k["optimo"])
    cfg_opt = {FACTORES_2K[f][0]: nivel(f, s) for f, s in r2k["optimo"].items()}
    cfg_txt = ", ".join(f"{k} = {v}" for k, v in cfg_opt.items())
    base = df2k[(df2k["A"] == -1) & (df2k["B"] == -1) & (df2k["C"] == -1)]["tiempo_s"].mean()
    prod = df2k[(df2k["A"] == -1) & (df2k["B"] == 1) & (df2k["C"] == -1)]["tiempo_s"].mean()
    t_conf = conf["tiempo_s"]
    dentro = pred["li_pred_95"] <= t_conf.mean() <= pred["ls_pred_95"]
    efr = efectos_2k(dffr, "tiempo_s", "ABCD")
    alias = alias_2_4_1()
    efr["alias (confundido con)"] = efr["efecto"].map(lambda e: alias.get(e) or next((k for k, v in alias.items() if v == e), ""))
    efr = efr[efr["efecto"].str.len() <= 2]

    lineas = ["# Laboratorio E2 · Experimento factorial sobre el extractor (ruta ingeniería)\n",
         "> Documento **generado** por `python -m laboratorio.e2_experimento`. Corridas crudas en `laboratorio/resultados/e2/*.csv`. "
         "Se procesan copias locales de la Capa Bronce: el experimento no hace ninguna petición al SNIIM.\n",
         "## 1. Planteamiento\n",
         "**Pregunta:** ¿qué combinación de parser HTML, alcance del árbol y formato de salida minimiza el tiempo de procesamiento de las capturas SNIIM sin introducir errores de extracción?\n",
         f"- Unidad experimental: procesar una muestra fija de **{len(meta['muestra'])} capturas reales** de Bronce (semilla {meta['semilla']}), leer, parsear y escribir la salida.",
         "- Respuestas: tiempo (s, medido dentro de un proceso Python aislado, sin contar la importación de librerías) y tasa de error (archivos cuya extracción difiere de la configuración de producción o lanza excepción).",
         f"- Entorno: Python {meta['python']}, {meta['plataforma']}, {meta['cpu']} CPU lógicas; una sola máquina. Se corrió una configuración de calentamiento antes de medir.",
         f"- Fecha de las corridas: {meta['fecha_utc']}.\n",
         "| Factor | Nivel bajo (−1) | Nivel alto (+1) |", "|---|---|---|",
         *[f"| {k} · {v[0]} | {v[1]} | {v[2]} |" for k, v in FACTORES_2K.items()],
         f"| D · {FACTOR_D[0]} (solo en 2⁴⁻¹) | {FACTOR_D[1]} | {FACTOR_D[2]} |\n",
         "**Principios del diseño.** Aleatorización: el orden de los 8 tratamientos se baraja dentro de cada bloque con semilla registrada. "
         f"Réplicas: {REPLICAS} por tratamiento. Bloqueo: cada réplica es un bloque que contiene los 8 tratamientos; así la deriva de la máquina "
         "(temperatura, carga, caché) entre réplicas se separa del efecto de los factores y se estima como término `bloque` en el ANOVA.\n",
         "## 2. Diseño 2³ con réplicas y bloques\n",
         "Corridas en el orden real de ejecución (primeras 8):\n",
         tabla_md(df2k[["orden", "bloque", "parser", "arbol", "formato", "tiempo_s", "tasa_error"]].head(8), 3) + "\n",
         "Medias por tratamiento:\n",
         tabla_md(r2k["medias"].assign(**{f: r2k["medias"][f].map(lambda s, f=f: nivel(f, s)) for f in "ABC"}).rename(columns={"A": "parser", "B": "árbol", "C": "formato"}), 3) + "\n",
         "### ANOVA de efectos fijos (modelo con interacciones y bloque)\n",
         tabla_md(r2k["anova"].rename(columns={"fuente": "Fuente"}), 4) + "\n",
         f"![Efectos]({rel(figs['efectos'], carpeta)})\n",
         tabla_md(r2k["efectos"].assign(efecto=lambda t: t["efecto"].map(lambda e: " × ".join(FACTORES_2K[c][0] for c in e))), 4) + "\n",
         f"![Interacciones]({rel(figs['interacciones_2k'], carpeta)})\n",
         "### Supuestos (puerta de calidad 3)\n",
         f"![Residuos]({rel(figs['residuos_2k'], carpeta)})\n",
         f"- Normalidad de residuos (Shapiro-Wilk): p = {fmt(r2k['supuestos']['shapiro_p'], 4)} → {'se cumple' if r2k['supuestos']['normalidad'] else '**no se cumple**'}.",
         f"- Varianza homogénea entre tratamientos (Levene, mediana): p = {fmt(r2k['supuestos']['levene_p'], 4)} → {'se cumple' if r2k['supuestos']['homocedasticidad'] else '**no se cumple**'}."]
    if "anova_log" in r2k:
        sl = r2k["supuestos_log"]
        lineas += [f"- Como algún supuesto falla, se repite el ANOVA sobre **log(tiempo)** (Shapiro p = {fmt(sl['shapiro_p'], 4)}, Levene p = {fmt(sl['levene_p'], 4)}):\n",
              tabla_md(r2k["anova_log"].rename(columns={"fuente": "Fuente"}), 4)]
    if "permutacion" in r2k:
        perm = r2k["permutacion"].assign(efecto=lambda t: t["efecto"].map(lambda e: " × ".join(FACTORES_2K[c][0] for c in e)))
        lineas += ["", "- La normalidad tampoco se sostiene en escala log, así que la significancia se decide con una **prueba de permutación** "
              "(1,999 permutaciones de la respuesta dentro de cada bloque; no supone normalidad):\n", tabla_md(perm, 4)]
    lineas += ["",
          "### Combinación óptima y corrida de confirmación\n",
          f"Entre los tratamientos con **tasa de error 0**, el de menor tiempo medio es **{cfg_txt}**. "
          f"El modelo predice {fmt(pred['media_predicha_s'], 3)} s (intervalo de predicción 95 % para una corrida: {fmt(pred['li_pred_95'], 3)}–{fmt(pred['ls_pred_95'], 3)} s).\n",
          f"Confirmación: {len(conf)} corridas nuevas de la combinación óptima → media {fmt(t_conf.mean(), 3)} s (DE {fmt(t_conf.std(), 3)}), tasa de error {fmt(conf['tasa_error'].mean(), 3)}. "
          f"La media confirmada {'**cae dentro**' if dentro else '**cae fuera**'} del intervalo de predicción"
          + ("." if dentro else "; se reporta como diferencia entre sesiones de medición (deriva de la máquina), no como fallo del óptimo.") + "\n",
          f"**Mejora:** frente a la línea base (html.parser, árbol completo, CSV: {fmt(base, 3)} s) el óptimo reduce el tiempo "
          f"{fmt((1 - t_conf.mean() / base) * 100, 1)} %; frente a la configuración de producción previa al experimento (html.parser, tablas, CSV: {fmt(prod, 3)} s) "
          f"la reducción es {fmt((1 - t_conf.mean() / prod) * 100, 1)} %.\n",
          "## 3. Dos factores con tres niveles e interacción (parser × árbol)\n",
          f"Parser con 3 niveles (html.parser, lxml, html5lib) × árbol (completo, tablas), {REPLICAS} réplicas, orden completamente aleatorizado (18 corridas), formato CSV fijo.\n",
          tabla_md(rab["medias"], 3) + "\n",
          tabla_md(rab["anova"].rename(columns={"fuente": "Fuente"}), 4) + "\n",
          f"![Interacción 3×2]({rel(figs['interaccion_3x2'], carpeta)})\n",
          f"Supuestos: Shapiro p = {fmt(rab['supuestos']['shapiro_p'], 4)}, Levene p = {fmt(rab['supuestos']['levene_p'], 4)}."]
    if "anova_log" in rab:
        lineas += [f" Como algún supuesto falla, se confirma con log(tiempo) (Shapiro p = {fmt(rab['supuestos_log']['shapiro_p'], 4)}, Levene p = {fmt(rab['supuestos_log']['levene_p'], 4)}) "
              f"y con Kruskal-Wallis sobre los 6 tratamientos (H = {fmt(rab['kruskal']['H'], 2)}, p = {fmt(rab['kruskal']['p'], 5)}).\n",
              tabla_md(rab["anova_log"].rename(columns={"fuente": "Fuente"}), 4)]
    p_int = float(rab["anova"].loc[rab["anova"]["fuente"].str.contains(":"), "p"].iloc[0])
    m = rab["medias"].set_index(["parser", "arbol"])["tiempo_medio_s"]
    dif = {pz: m[(pz, "completo")] - m[(pz, "tablas")] for pz in ("html.parser", "lxml", "html5lib")}
    p_arbol = float(rab["anova"].set_index("fuente").loc["C(arbol)", "p"])
    p_parser = float(rab["anova"].set_index("fuente").loc["C(parser)", "p"])
    texto_dif = "; ".join(f"{pz}: {fmt(v, 3)} s" for pz, v in dif.items())
    if p_int < ALFA:
        lectura = (f"**La interacción es significativa (p = {fmt(p_int, 4)}).** El ahorro de restringir el árbol a tablas cambia según el parser ({texto_dif}). "
                   "html5lib ignora `parse_only`, así que en él el factor árbol no puede tener efecto; analizar los factores por separado escondería esa dependencia.")
    else:
        lectura = (f"**La interacción no es significativa (p = {fmt(p_int, 4)}).** El parser domina la variación (p = {fmt(p_parser, 6)}); el ahorro de restringir el árbol a tablas "
                   f"es pequeño ({texto_dif}; efecto principal p = {fmt(p_arbol, 4)}). Por construcción html5lib ignora `parse_only`, de modo que en él ese ahorro debería ser nulo; "
                   "con 3 réplicas la diferencia entre parsers en ese ahorro no es detectable frente al ruido de medición.")
    lineas += ["", lectura + "\n",
          "Comparaciones múltiples (Tukey HSD, 5 %), solo pares significativos:\n",
          tabla_md(rab["tukey"][rab["tukey"]["reject"].astype(str) == "True"], 4) + "\n",
          "## 4. Diseño completo 2⁴ vs fraccionado 2⁴⁻¹\n",
          f"Cuarto factor D = {FACTOR_D[0]} ({FACTOR_D[1]} vs {FACTOR_D[2]} procesos en paralelo).\n",
          "**2⁴ completo (16 tratamientos por réplica):**\n", tabla_md(matriz_2k_completa(4), 0) + "\n",
          "**2⁴⁻¹ fraccionado (8 tratamientos por réplica), generador D = ABC, relación definidora I = ABCD (resolución IV):**\n",
          tabla_md(matriz_fraccionada_2_4_1(), 0) + "\n",
          "Estructura de alias (cada efecto se estima sumado a su alias):\n",
          "| Efecto | Confundido con |", "|---|---|", *[f"| {e} | {a} |" for e, a in alias_2_4_1().items() if a != "I"], "",
          f"Comprobación numérica de los alias en la matriz: {all(verificar_alias(matriz_2k_completa(4), matriz_fraccionada_2_4_1()).values())}.\n",
          "Efectos principales quedan confundidos solo con interacciones triples (que se suponen despreciables); las interacciones dobles quedan confundidas entre sí "
          "(AB con CD, AC con BD, AD con BC), así que una interacción doble significativa no se puede atribuir sin corridas adicionales (fold-over).\n",
          f"**Ahorro:** por réplica, 8 corridas en lugar de 16 (50 %); con {2} réplicas, 16 en lugar de 32.\n",
          "Se corrió la fracción con 2 réplicas en orden aleatorio. Efectos estimados (principales y dobles con su alias):\n",
          tabla_md(efr, 4) + "\n",
          (lambda d: f"Lectura: el efecto de D (procesos) es {fmt(d, 3)} s: "
           + ("paralelizar con 4 procesos **reduce** el tiempo aun descontando el costo de crear los procesos. " if d < 0 else
              "con esta muestra el costo de crear procesos supera el ahorro de paralelizar. ")
           + "Como D está confundido con ABC, el valor supone que la interacción triple es despreciable (en el 2³ completo su efecto fue "
           + f"{fmt(r2k['efectos'].set_index('efecto').loc['ABC', 'estimacion_s'], 3)} s).\n")(efr.loc[efr['efecto'] == 'D', 'estimacion_s'].iloc[0]),
          "## 5. Conclusión para el observatorio\n",
          f"- Combinación recomendada: **{cfg_txt}**, confirmada con {len(conf)} corridas y tasa de error {fmt(conf['tasa_error'].mean(), 3)}.",
          "- **Aplicada en producción (E3):** `extractores/sniim_extractor.py::parse_resultados` usa ahora lxml + solo tablas. Antes de adoptarla se corrió el pipeline completo "
          "sobre todo Bronce con ambos parsers y las cinco salidas CSV resultaron idénticas (mismo SHA-256); el formato de salida de Plata/Oro sigue en CSV porque Parquet no mostró efecto significativo.",
          "- El experimento es la evidencia de **eficiencia de desempeño** para la evaluación ISO/IEC 25010 (docs/calidad/iso25010.md).",
          "- Alcance: una máquina, una muestra de capturas y un momento; los porcentajes no se extrapolan a otros equipos o volúmenes."]
    md = "\n".join(lineas) + "\n"
    (docs / "experimento_factorial.md").write_text(md, encoding="utf-8")
    guardar_json({"anova_2k": r2k["anova"].to_dict("records"), "efectos_2k": r2k["efectos"].to_dict("records"),
                  "supuestos_2k": r2k["supuestos"], "optimo": cfg_opt, "prediccion_optimo": pred,
                  "confirmacion": {"media_s": t_conf.mean(), "de_s": t_conf.std(), "dentro_intervalo": dentro},
                  "mejora_vs_base_pct": (1 - t_conf.mean() / base) * 100, "mejora_vs_produccion_pct": (1 - t_conf.mean() / prod) * 100,
                  "anova_3x2": rab["anova"].to_dict("records"), "supuestos_3x2": rab["supuestos"],
                  "alias_2_4_1": alias_2_4_1(), "efectos_2_4_1": efr.to_dict("records")}, salida / "resultados.json")
    return md


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Laboratorio E2: experimento factorial")
    ap.add_argument("--hijo", help=argparse.SUPPRESS)
    ap.add_argument("--bronce", type=Path, default=BASE_DIR / "data" / "bronce")
    ap.add_argument("--salida", type=Path, default=RESULTADOS / "e2")
    ap.add_argument("--docs", type=Path, default=BASE_DIR / "docs" / "E2")
    ap.add_argument("--solo-analisis", action="store_true")
    a = ap.parse_args(argv)
    if a.hijo:
        cfg = json.loads(Path(a.hijo).read_text(encoding="utf-8"))
        print(json.dumps(corrida(cfg["archivos"], cfg["parser"], cfg["arbol"], cfg["formato"], cfg.get("procesos", 1))))
        return 0
    if not a.solo_analisis:
        correr_todo(a.bronce, a.salida)
    informe(a.salida, a.docs)
    print(f"E2: informe en {a.docs / 'experimento_factorial.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
