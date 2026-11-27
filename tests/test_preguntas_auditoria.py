"""Pruebas de las preguntas del agricultor y de la auditoría cruzada asistida (datos y repositorios FIXTURE)."""
from __future__ import annotations

import subprocess

import pandas as pd

from calidad import auditar_repo as au
from src.inteligencia import preguntas as pq


def _datos():
    meses = pd.period_range("2024-01", periods=24, freq="M")
    m = pd.DataFrame({"cultivo": "limon", "variante_id": 421, "variante": "Limón #5", "mercado": "140", "mes": meses,
                      "precio_frecuente_kg": [20 + (i % 12) for i in range(24)], "n_observaciones": 10})
    gold = pd.DataFrame({"cultivo": "limon", "mercado": 140, "origen": ["Colima", "Jalisco"] * 6,
                         "fecha_mes": [f"2025-{i:02d}-01" for i in range(1, 13)], "n_observaciones_precio": [30, 10] * 6})
    return {
        "gold": gold, "corte": pd.Period("2025-12", freq="M"), "m": m,
        "pron": pd.DataFrame([{"cultivo": "limon", "horizonte_meses": 1, "nombre_mercado": "GDL", "variante": "Limón #5", "precio_frecuente_mxn_kg": 21.0,
                               "fecha_pronostico": "2026-01", "li80_mxn_kg": 15.0, "ls80_mxn_kg": 27.0, "li95_mxn_kg": 12.0, "ls95_mxn_kg": 30.0,
                               "mape_backtest_pct": 15.0, "cobertura_80_holdout": 0.83, "tipo_serie": "origen_colima", "variante_id": 421, "mercado": 140,
                               "modelo_elegido": "arima_aic", "origen": "Colima", "fecha_ultimo_dato": "2025-12"}]),
        "val": pd.DataFrame([{"variante_id": 421, "mercado": 140, "modelo": "arima_aic", "mes_validacion": f"2025-{k:02d}", "real_mxn_kg": 18.0,
                              "error_mxn_kg": e} for k, e in zip(range(1, 13), [-4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7], strict=True)]),
        "senales": pd.DataFrame([{"cultivo": "limon", "mercado": 140, "nombre_mercado": "GDL", "ultimo_mes": "2025-12", "ultimo_precio_mxn_kg": 31.0,
                                  "percentil_historico": 95, "meses_historia": 24, "lectura": "precio alto"}]),
        "cal": pd.DataFrame([{"cultivo": "limon", "mercado": 140, "mes": k, "indice_estacional": 1 + (k - 6) / 20, "confianza_patron": "baja",
                              "motivo_confianza": "no se distingue del azar (p = 0.300, 36 observaciones)"} for k in range(1, 13)]),
        "plazas": pd.DataFrame([{"cultivo": "limon", "evidencia": "suficiente", "nombre_mercado": "Monterrey", "diferencia_media_mxn_kg": 3.5,
                                 "meses_pareados": 10, "pct_meses_plaza_mayor": 80, "flete_equilibrio_mxn_kg": 3.5, "confianza": "alta",
                                 "motivo_confianza": "p = 0.010 con 10 observaciones", "desde": "2025-01", "hasta": "2025-10", "plaza_referencia": "GDL"},
                                {"cultivo": "limon", "evidencia": "suficiente", "nombre_mercado": "Torreón · Central", "diferencia_media_mxn_kg": -8.0,
                                 "meses_pareados": 12, "pct_meses_plaza_mayor": 8, "flete_equilibrio_mxn_kg": 0.0, "confianza": "alta",
                                 "motivo_confianza": "p = 0.001", "desde": "2025-01", "hasta": "2025-12", "plaza_referencia": "GDL"}]),
        "margen": pd.DataFrame([{"cultivo": "limon", "mercado": 140, "anio": 2025, "nombre_mercado": "GDL", "precio_productor_mxn_kg": 10.0,
                                 "precio_mayorista_mxn_kg": 25.0, "participacion_productor_pct": 40.0, "diferencia_mxn_kg": 15.0, "meses_mayorista": 12},
                                {"cultivo": "platano", "mercado": 220, "anio": 2025, "nombre_mercado": "Querétaro", "precio_productor_mxn_kg": 5.0,
                                 "precio_mayorista_mxn_kg": 15.0, "participacion_productor_pct": 33.3, "diferencia_mxn_kg": 10.0, "meses_mayorista": 8}]),
        "actuales": pd.DataFrame([{"producto": "Limón c/semilla # 5", "origen": "Colima", "mercado": "Jalisco: GDL", "fecha": "2025-12-20", "precio_frecuente_mxn_kg": 22.0},
                                  {"producto": "Limón c/semilla # 5", "origen": "Colima", "mercado": "Sonora: Hermosillo", "fecha": "2025-12-20", "precio_frecuente_mxn_kg": 18.0}]),
        "siap": pd.DataFrame([{"Anio": 2025, "Nomcultivo": "Limón", "Nommunicipio": "Tecomán", "volumen_produccion": 1000.0, "precio_medio_rural_mxn_unidad": 9500.0}]),
        "comercio": pd.DataFrame([{"grupo_fruta": "limon", "tipo_consulta": "destinos_mexico", "anio": 2024, "pais_reportante": "USA",
                                   "valor_comercio_usd": 8e8, "valor_unitario_aduanal_usd_kg": 1.15}]),
        "fiab": {"periodos": {"ventana_sello_14_dias": {"disponibilidad": 1.0, "dias": 14, "hasta": "2025-12-31"}}}, "iso": {"medidas": {"completitud": {"valor": 1.0}}},
        "e1": {"correlacion_cruzada": [{"variable": "temperatura media", "n": 31, "corr_max": -0.26, "rezago_max": 4, "significativa": False}]},
    }


def test_todas_las_preguntas_responden_con_datos():
    d = _datos()
    resp = pq.responder(d)
    lim = {r["pregunta"]: r["respuesta"] for r in resp["limon"]}
    assert len(resp["limon"]) == len(pq.RESPUESTAS)
    assert any("15.00 y 27.00" in t for t in lim.values())
    todas = resp["limon"]
    assert all(r["confianza"] in {"alta", "media", "baja", "no aplica"} and r["accion"] and r["motivo"] for r in todas)
    # vender o esperar: precio real = 21 − error; supera al último real (18) cuando error < 3 → 7 de 12 escenarios
    assert any("**58 %**" in t for t in lim.values())
    # el calendario sin significancia se declara de baja confianza y lo dice
    cal = next(r for r in todas if "meses" in r["pregunta"] and "pagarse" in r["pregunta"])
    assert cal["confianza"] == "baja" and "no se distingue estadísticamente del azar" in cal["respuesta"]
    assert any("Monterrey" in t and "flete" in t for t in lim.values())
    assert any("40 %" in t for t in lim.values())
    assert any("USA" in t for t in lim.values())
    assert any("Colima 75 %" in t for t in lim.values())
    assert any("No es estadísticamente significativa" in t for t in lim.values())
    # sin datos, las respuestas lo dicen en vez de inventar
    pap = {r["pregunta"]: r["respuesta"] for r in resp["papaya"]}
    assert any("Todavía no hay pronóstico" in t for t in pap.values())


def test_calculadora_usa_plaza_con_datos_si_no_hay_guadalajara():
    d = _datos()
    calc = pq.referencias_calculadora(d)
    assert calc["limon"]["rural_estimado_hoy"] == round(31.0 * 0.40, 2)
    assert calc["platano"]["rural_anual"] == 5.0 and "Querétaro" in calc["platano"]["plaza_referencia"]


def test_html_y_markdown(tmp_path):
    d = _datos()
    resp = pq.responder(d)
    pagina = pq.html_preguntas(resp, pq.referencias_calculadora(d), "2025-12")
    assert "<title>Preguntas del productor · OAIC</title>" in pagina and "Confianza" in pagina and "Qué hacer" in pagina and 'id="oferta"' in pagina and "Plátano" in pagina
    md = pq.markdown_preguntas(resp, "2025-12")
    assert md.count("### ") == len(pq.RESPUESTAS) * len(pq.PRODUCTOS) and "**Confianza:**" in md and "Lo que todavía no responde" in md


def _repo(tmp_path, con_secreto=False):
    r = tmp_path / "otro"
    (r / "docs/E0").mkdir(parents=True)
    (r / "README.md").write_text("# Otro observatorio\n")
    (r / "data/oro").mkdir(parents=True)
    pd.DataFrame({"a": [1, None, 3, 3], "b": ["x", "y", None, None]}).to_csv(r / "data/oro/panel.csv", index=False)
    (r / "calidad").mkdir()
    (r / "calidad/tiempo-ana.csv").write_text("fecha,inicio\n")
    if con_secreto:
        (r / "config.py").write_text('API_KEY = "abcdefghijklmnopqrstuvwx"\n')
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)
    subprocess.run(["git", "-C", str(r), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
    subprocess.run(["git", "-C", str(r), "tag", "e1"], check=True)
    return r


def test_auditoria_detecta_faltantes_secretos_y_completitud(tmp_path):
    repo = _repo(tmp_path, con_secreto=True)
    ids = {h.id: h for h in au.revisar_entregables(repo) + au.buscar_secretos(repo) + au.medir_oro(repo)[0]}
    assert "AUD-C01" in ids and ids["AUD-C01"].severidad == "crítico"  # sin captura programada
    assert "AUD-S01" in ids and "config.py" in ids["AUD-S01"].evidencia
    assert "AUD-P02" in ids
    assert "AUD-D-panel" in ids and "AUD-U-panel" in ids
    sin_oro = tmp_path / "vacio"
    sin_oro.mkdir()
    assert au.medir_oro(sin_oro)[0][0].id == "AUD-D01"


def test_auditoria_de_extremo_a_extremo_sin_pruebas(tmp_path):
    repo = _repo(tmp_path)
    salida = tmp_path / "borrador.md"
    assert au.main([f"file://{repo}", "--etiqueta", "e1", "--sin-pruebas", "--salida", str(salida)]) == 0
    texto = salida.read_text(encoding="utf-8")
    assert "Borrador de auditoría cruzada" in texto and "AUD-C01" in texto and "Revisión manual pendiente" in texto
