"""Pruebas de inteligencia comercial, reporte y API con datos SINTÉTICOS de resultado conocido."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.inteligencia import comercial as ic
from src.inteligencia import reporte as rp
from src.tdl_e4.observatorio import _intervalo_empirico


def _m(precios_gdl, precios_otra=None, mercado_otro="190", cultivo="limon", vid=421, inicio="2024-01"):
    filas = []
    meses = pd.period_range(inicio, periods=len(precios_gdl), freq="M")
    for mes, p in zip(meses, precios_gdl, strict=True):
        filas.append({"cultivo": cultivo, "variante_id": vid, "variante": "Limón #5", "mercado": "140", "mes": mes,
                      "precio_frecuente_kg": p, "n_observaciones": 20})
    if precios_otra is not None:
        for mes, p in zip(meses, precios_otra, strict=True):
            if p is not None:
                filas.append({"cultivo": cultivo, "variante_id": vid, "variante": "Limón #5", "mercado": mercado_otro, "mes": mes,
                              "precio_frecuente_kg": p, "n_observaciones": 10})
    return pd.DataFrame(filas)


def test_haversine_y_distancias(tmp_path):
    assert ic._haversine(0, 0, 0, 1) == pytest.approx(111.2, abs=0.2)
    geo = tmp_path / "c.geojson"
    geo.write_text(json.dumps({"features": [{"properties": {"ciudad": "Guadalajara"}, "geometry": {"type": "Point", "coordinates": [-103.35, 20.67]}}]}))
    d = ic.distancias_km(geo)
    assert 180 < d["140"] < 230 and "190" not in d
    assert ic.distancias_km(tmp_path / "no.geojson") == {}


def test_flete_de_equilibrio_solo_con_meses_pareados():
    m = _m([20, 22, 24, 26], [25, None, 27, 30])  # otra plaza paga +5, +3, +4 en 3 meses pareados
    out = ic.comparar_plazas(m, {"140": 200.0, "190": 900.0})
    fila = out.iloc[0]
    assert fila["meses_pareados"] == 3 and fila["diferencia_media_mxn_kg"] == pytest.approx(4.0)
    assert fila["flete_equilibrio_mxn_kg"] == pytest.approx(4.0) and fila["pct_meses_plaza_mayor"] == 100
    assert fila["km_extra_vs_referencia"] == 700 and fila["flete_equilibrio_mxn_ton_km_extra"] == pytest.approx(4000 / 700, rel=1e-3)
    assert fila["evidencia"] == "suficiente" and fila["prueba"] == "prueba de signos" and fila["confianza"] in {"baja", "media"}
    barata = ic.comparar_plazas(_m([20, 20], [15, 15]), {})
    assert barata.iloc[0]["flete_equilibrio_mxn_kg"] == 0 and barata.iloc[0]["evidencia"].startswith("insuficiente")


def test_margen_productor_pondera_por_volumen():
    m = _m([30.0] * 12, inicio="2025-01")
    siap = pd.DataFrame([
        {"Anio": 2025, "Nomcultivo": "Limón", "Nomunidad": "Tonelada", "volumen_produccion": 300, "precio_medio_rural_mxn_unidad": 10000},
        {"Anio": 2025, "Nomcultivo": "Limón", "Nomunidad": "Tonelada", "volumen_produccion": 100, "precio_medio_rural_mxn_unidad": 6000},
        {"Anio": 2025, "Nomcultivo": "Maíz", "Nomunidad": "Tonelada", "volumen_produccion": 100, "precio_medio_rural_mxn_unidad": 5000},
    ])
    out = ic.margen_productor(m, siap)
    assert len(out) == 1
    r = out.iloc[0]
    assert r["precio_productor_mxn_kg"] == 9.0 and r["precio_mayorista_mxn_kg"] == 30.0 and r["participacion_productor_pct"] == 30.0
    assert ic.margen_productor(m.iloc[0:0], siap).empty


def test_calendario_detecta_mes_caro():
    meses = 36
    rng = np.random.default_rng(3)
    precios = [20 + 5 * np.sin(2 * np.pi * ((i % 12) - 5.5) / 12) + (3 if (i % 12) == 8 else 0) + rng.normal(0, 0.2) for i in range(meses)]  # septiembre, el más caro
    cal = ic.calendario_venta(_m(precios, inicio="2023-01"))
    sep = cal[cal["mes"].eq(9)].iloc[0]
    assert sep["indice_estacional"] > 1.2 and cal.loc[cal["indice_estacional"].idxmax(), "mes"] == 9
    assert sep["p_estacionalidad_kruskal"] < 0.05 and sep["confianza_patron"] in {"alta", "media"}
    assert ic.calendario_venta(_m([20] * 10)).empty


def test_senales_y_hallazgos():
    m = _m(list(range(10, 26)))  # último precio = máximo histórico
    pron = pd.DataFrame([{"variante_id": 421, "mercado": 140, "fecha_pronostico": "2025-05", "precio_frecuente_mxn_kg": 26.0,
                          "li80_mxn_kg": 22.0, "ls80_mxn_kg": 30.0}])
    s = ic.senales(m, pron).iloc[0]
    assert s["percentil_historico"] >= 90 and "alto" in s["lectura"] and s["rango_80_siguiente_mes"] == "22.0–30.0"
    h = ic.hallazgos({"margen_productor": pd.DataFrame(), "plazas_colima": ic.comparar_plazas(_m(list(range(20, 30)), list(range(24, 34))), {}),
                      "calendario_venta": pd.DataFrame()})
    assert any("flete" in x for x in h)


def test_intervalo_empirico_cobertura_y_cuantil():
    rng = np.random.default_rng(1)
    sel, hold = rng.normal(0, 1, 6), rng.normal(0, 1, 6)
    r = _intervalo_empirico(sel, hold)
    assert r["n_errores"] == 12 and 0 < r["q80"] <= r["q95"]
    assert 0 <= r["cobertura_80_holdout"] <= 1
    vacio = _intervalo_empirico(np.array([]), np.array([]))
    assert np.isnan(vacio["q80"])


def test_reporte_y_api_de_extremo_a_extremo(tmp_path):
    """Usa los productos reales del repositorio si existen; si no, comprueba que el reporte no falla vacío."""
    base = tmp_path
    (base / "data/publico").mkdir(parents=True)
    (base / "tablero").mkdir()
    m = _m([20, 22, 24, 26], [25, 26, 27, 30])
    ic.comparar_plazas(m, {}).to_csv(base / "data/publico/plazas_colima.csv", index=False)
    pd.DataFrame([{"variante": "Limón #5", "nombre_mercado": "GDL", "fecha_pronostico": "2026-11", "horizonte_meses": 1,
                   "precio_frecuente_mxn_kg": 21.0, "li80_mxn_kg": 15.0, "ls80_mxn_kg": 27.0, "mape_backtest_pct": 15.0,
                   "linaje_serie_sha256": "x"}]).to_csv(base / "data/publico/pronosticos_colima.csv", index=False)
    (base / "data/publico/inteligencia.json").write_text(json.dumps({"hallazgos": ["Hallazgo de prueba"], "ultimo_mes_cerrado": "2026-10"}))
    r = rp.ejecutar(base)
    texto = (base / "tablero/inteligencia.html").read_text(encoding="utf-8")
    assert "Hallazgo de prueba" in texto and "Flete extra máximo" in texto and "<title>Reporte de inteligencia · OAIC</title>" in texto
    assert "Hallazgo de prueba" in (base / "docs/E4/reporte_inteligencia.md").read_text(encoding="utf-8")
    indice = json.loads((base / "data/publico/api/v1/index.json").read_text(encoding="utf-8"))
    assert set(r["api_recursos"]) == set(indice["recursos"]) >= {"plazas", "pronosticos"}
    pron = json.loads((base / "data/publico/api/v1/pronosticos.json").read_text(encoding="utf-8"))
    assert "linaje_serie_sha256" not in pron["columnas"] and pron["datos"][0]["li80_mxn_kg"] == 15.0


def test_nivel_confianza_y_prueba_diferencia():
    assert ic.nivel_confianza(0.01, 12, 9, 3)[0] == "alta"
    assert ic.nivel_confianza(0.01, 4, 9, 3)[0] == "media"
    assert ic.nivel_confianza(0.10, 12, 9, 3)[0] == "media"
    assert ic.nivel_confianza(0.50, 12, 9, 3)[0] == "baja"
    assert ic.nivel_confianza(None, 2, 9, 3)[0] == "baja"
    p, nombre = ic.prueba_diferencia(pd.Series([2.0, 3, 1, 4, 2, 3, 5, 2]))
    assert nombre.startswith("Wilcoxon") and p < 0.05
    assert ic.prueba_diferencia(pd.Series([1.0, 0]))[0] is None
