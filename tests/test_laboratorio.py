"""Pruebas del laboratorio estadístico con datos SINTÉTICOS de propiedades conocidas."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from laboratorio import e1_series as e1
from laboratorio import e2_experimento as e2
from laboratorio import e3_multivariado as e3
from laboratorio.comun import fmt, limpiar, tabla_md
from tests.test_sniim import RESULTADOS

RNG = np.random.default_rng(7)


def _serie(valores):
    return pd.Series(valores, index=pd.period_range("2023-11", periods=len(valores), freq="M"), dtype="float64")


# --- E1 -------------------------------------------------------------------------------------------

def test_estacionariedad_diferencia_una_caminata_aleatoria():
    caminata = _serie(50 + np.cumsum(RNG.normal(0, 1, 60)))
    assert e1.estacionariedad(caminata)["d_recomendado"] >= 1
    ruido = _serie(20 + RNG.normal(0, 1, 60))
    assert e1.estacionariedad(ruido)["d_recomendado"] == 0


def test_autocorrelacion_detecta_ar1():
    x = np.zeros(80)
    for t in range(1, 80):
        x[t] = 0.8 * x[t - 1] + RNG.normal()
    a = e1.autocorrelacion(_serie(x + 10), 0)
    assert 1 in a["rezagos_significativos_pacf"] and a["p_sugerido"] >= 1


def test_metricas_de_error():
    m = e1.metricas(np.array([10.0, 20.0]), np.array([12.0, 18.0]))
    assert m["MAE"] == 2 and m["RMSE"] == 2 and m["MAPE_pct"] == pytest.approx(15)


def test_analisis_completo_sobre_serie_estacional():
    t = np.arange(36)
    s = _serie(25 + 0.2 * t + 4 * np.sin(2 * np.pi * t / 12) + RNG.normal(0, 1, 36))
    r = e1.analizar(s, "Sintética", "la serie sintética")
    assert r["descomposicion"]["modelo_elegido"] in {"aditivo", "multiplicativo"}
    assert len(r["comparacion"]) == 4 and r["ganador"] in set(r["comparacion"]["modelo"])
    f = r["pronostico"]
    assert len(f) == e1.HORIZONTE and (f["li95"] <= f["li80"]).all() and (f["li80"] <= f["pronostico"]).all() and (f["pronostico"] <= f["ls80"]).all()
    assert "la serie sintética" in e1.frase_cliente(r)


def test_correlacion_cruzada_encuentra_rezago():
    base = RNG.normal(0, 1, 40).cumsum()
    x = _serie(base)
    y = _serie(np.roll(base, -2))  # y adelanta a x en 2 meses
    cc = e1.correlacion_cruzada(x, y, "y")
    assert cc["rezago_max"] == 2 and cc["significativa"]
    assert e1.correlacion_cruzada(x.iloc[:5], y.iloc[:5], "y")["estado"] == "insuficiente"


# --- E2 -------------------------------------------------------------------------------------------

def test_planes_aleatorizados_y_balanceados():
    p = e2.plan_2k(replicas=3)
    assert len(p) == 24 and p.groupby(["A", "B", "C"]).size().eq(3).all()
    assert p.groupby("bloque").size().eq(8).all()
    assert not p.sort_values(["bloque", "A", "B", "C"])["orden"].tolist() == p["orden"].tolist()  # no está en orden estándar
    d = e2.plan_dos_factores(replicas=3)
    assert len(d) == 18 and d.groupby(["parser", "arbol"]).size().eq(3).all()


def test_fraccion_2_4_1_y_alias():
    full, frac = e2.matriz_2k_completa(4), e2.matriz_fraccionada_2_4_1()
    assert len(full) == 16 and len(frac) == 8
    assert (frac["D"] == frac["A"] * frac["B"] * frac["C"]).all()
    alias = e2.alias_2_4_1()
    assert alias["A"] == "BCD" and alias["AB"] == "CD" and alias["ABCD"] == "I"
    assert all(e2.verificar_alias(full, frac).values())
    # todas las filas de la fracción están en el diseño completo
    assert len(frac.merge(full, on=list("ABCD"))) == 8


def test_efectos_y_anova_recuperan_un_efecto_conocido():
    p = e2.plan_2k(replicas=3)
    p["tiempo_s"] = 2.0 - 0.5 * p["A"] + RNG.normal(0, 0.01, len(p))  # efecto A = −1.0 s
    p["tasa_error"] = 0.0
    ef = e2.efectos_2k(p, "tiempo_s")
    assert ef.iloc[0]["efecto"] == "A" and ef.iloc[0]["estimacion_s"] == pytest.approx(-1.0, abs=0.02)
    r = e2.analizar_2k(p)
    fila_a = r["anova"].set_index("fuente").loc["A"]
    assert fila_a["p"] < 1e-6
    assert r["optimo"]["A"] == 1
    pred = e2.prediccion_optimo(r["_modelo"], r["optimo"])
    assert pred["li_pred_95"] < pred["media_predicha_s"] < pred["ls_pred_95"]


def test_corrida_real_sobre_fixture(tmp_path):
    archivos = []
    for i in range(3):
        f = tmp_path / f"sniim_{i}.html"
        f.write_text(RESULTADOS, encoding="utf-8")
        archivos.append(str(f))
    ref = e2.corrida(archivos, "html.parser", "tablas", "csv")
    assert ref["registros"] > 0 and not ref["fallos"] and ref["bytes_salida"] > 0
    for parser, arbol, formato in (("lxml", "completo", "parquet"), ("html5lib", "tablas", "csv")):
        r = e2.corrida(archivos, parser, arbol, formato)
        assert e2.tasa_error(r, ref["digests"]) == 0.0
    malo = tmp_path / "malo.html"
    malo.write_text("<html><body>sin tabla</body></html>", encoding="utf-8")
    r = e2.corrida([str(malo)], "html.parser", "tablas", "csv")
    assert r["fallos"] and e2.tasa_error(r, {"malo.html": "x"}) == 1.0


# --- E3 -------------------------------------------------------------------------------------------

def test_mardia_y_henze_zirkler_no_rechazan_normal_y_rechazan_sesgada():
    normal = RNG.multivariate_normal(np.zeros(3), np.eye(3), size=300)
    assert e3.mardia(normal)["p_asimetria"] > 0.01 and e3.henze_zirkler(normal)["p"] > 0.01
    sesgada = RNG.exponential(1, size=(300, 3))
    assert e3.mardia(sesgada)["p_asimetria"] < 0.001 and e3.henze_zirkler(sesgada)["p"] < 0.001
    d2 = e3.mahalanobis2(normal)
    assert d2.mean() == pytest.approx(3, rel=0.01)  # E[D²] = p con covarianza muestral sesgada


def test_pca_propiedades():
    X = pd.DataFrame(RNG.normal(size=(200, 4)), columns=list("abcd"))
    X["e"] = X["a"] * 2 + RNG.normal(0, 0.1, 200)
    P = e3.pca(X)
    assert P["acumulada"][-1] == pytest.approx(1) and np.all(np.diff(P["valores_propios"]) <= 1e-12)
    assert P["valores_propios"].sum() == pytest.approx(5)
    assert abs(P["cargas"].loc["a", "CP1"]) > 0.9 and abs(P["cargas"].loc["e", "CP1"]) > 0.9
    assert e3.nombrar(P["cargas"], "CP1").startswith("Índice")


def _oro_sintetico(n_mes=14):
    filas = []
    for g, base in zip(e3.GRUPOS, (10, 20, 15, 30, 40), strict=True):
        for mercado in (100, 140):
            for m in range(n_mes):
                precio = base * np.exp(RNG.normal(0, 0.1))
                filas.append({"cultivo": g, "variante": g, "variante_id": hash(g) % 1000, "mercado": mercado, "origen": "Colima",
                              "presentacion": "Kilogramo", "fecha_mes": str(pd.Period("2025-01", freq="M") + m) + "-01",
                              "precio_frecuente_kg_mean": precio, "precio_min_kg_mean": precio * 0.9, "precio_max_kg_mean": precio * (1.1 + RNG.uniform(0, .2)),
                              "precio_frecuente_kg_std": precio * RNG.uniform(.01, .1), "precio_frecuente_kg_count": 10,
                              "n_observaciones_precio": int(RNG.integers(5, 30)) + (20 if g == "limon" else 0)})
    return pd.DataFrame(filas)


def test_manova_y_permutacion_detectan_grupos(tmp_path):
    datos = e3.construir_matriz(_oro_sintetico())
    assert set(datos["cultivo"]) == set(e3.GRUPOS) and datos[list(e3.VARIABLES)].notna().all().all()
    mv = e3.manova(datos)
    assert mv["Pillai's trace"]["p"] < 0.001
    assert e3.pillai_permutacion(datos, n_perm=99)["p"] <= 0.02
    assert e3.tasa_error_familia(5) == pytest.approx(0.2262, abs=1e-4)
    assert len(e3.anovas_separados(datos)) == 5
    bm = e3.box_m(datos[list(e3.VARIABLES)], datos["cultivo"])
    assert 0 <= bm["p"] <= 1


def test_ejecutar_e3_genera_informe(tmp_path):
    oro = tmp_path / "oro.csv"
    _oro_sintetico().to_csv(oro, index=False)
    r = e3.ejecutar(oro, tmp_path / "res", tmp_path / "docs")
    assert (tmp_path / "docs" / "multivariado.md").is_file() and (tmp_path / "res" / "mapa_componentes.csv").is_file()
    assert r["n"] > 0 and "CP1" in r["pca"]["nombres"]


# --- comunes --------------------------------------------------------------------------------------

def test_utilidades_comunes():
    assert limpiar({"a": np.float64("nan"), "b": np.int64(2), "c": [np.bool_(True)]}) == {"a": None, "b": 2, "c": [True]}
    assert fmt(None) == "—" and fmt(1234) == "1,234" and fmt(1.23456, 2) == "1.23"
    assert tabla_md(pd.DataFrame({"x": [1.5], "y": ["z"]})).startswith("| x | y |")


def test_tablero_laboratorio_se_genera_con_y_sin_resultados(tmp_path):
    from laboratorio import tablero
    vacio = tablero.generar(resultados=tmp_path / "nada", docs=tmp_path, destino=tmp_path / "vacio.html")
    assert "Ejecute primero" in vacio.read_text(encoding="utf-8")
    real = tablero.generar(destino=tmp_path / "lab.html")
    texto = real.read_text(encoding="utf-8")
    assert "<title>Laboratorio estadístico · OAIC</title>" in texto
    assert tablero.main(["--destino", str(tmp_path / "otro.html")]) == 0
