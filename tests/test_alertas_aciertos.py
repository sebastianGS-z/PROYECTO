"""Pruebas de alertas (RSS/JSON), historial de aciertos, deflactor y preguntas nuevas (datos FIXTURE)."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import pandas as pd

from scripts import capturar_inflacion as ci
from src.inteligencia import aciertos as ac
from src.inteligencia import alertas as al
from src.inteligencia import preguntas as pq


def _escribir(base, rel, obj):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(p, index=False)
    else:
        p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def _base_alertas(tmp_path):
    _escribir(tmp_path, "data/publico/senales_mercado.csv", pd.DataFrame([
        {"cultivo": "limon", "variante_id": 421, "variante": "Limón #5", "mercado": 140, "nombre_mercado": "Guadalajara · Abasto", "ultimo_mes": "2026-10",
         "ultimo_precio_mxn_kg": 30.0, "percentil_historico": 90, "meses_historia": 100, "lectura": "precio alto"},
        {"cultivo": "papaya", "variante_id": 500, "variante": "Papaya", "mercado": 140, "nombre_mercado": "Guadalajara · Abasto", "ultimo_mes": "2026-10",
         "ultimo_precio_mxn_kg": 8.0, "percentil_historico": 10, "meses_historia": 100, "lectura": "precio bajo"},
        {"cultivo": "guayaba", "variante_id": 600, "variante": "Guayaba", "mercado": 140, "nombre_mercado": "Guadalajara · Abasto", "ultimo_mes": "2026-10",
         "ultimo_precio_mxn_kg": 12.0, "percentil_historico": 50, "meses_historia": 100, "lectura": "normal"},
        {"cultivo": "mango_ataulfo", "variante_id": 700, "variante": "Mango", "mercado": 140, "nombre_mercado": "Guadalajara · Abasto", "ultimo_mes": "2026-05",
         "ultimo_precio_mxn_kg": 40.0, "percentil_historico": 99, "meses_historia": 50, "lectura": "precio alto"}]))
    _escribir(tmp_path, "data/publico/plazas_colima.csv", pd.DataFrame([
        {"cultivo": "limon", "variante_id": 421, "variante": "Limón #5", "mercado": 300, "nombre_mercado": "Monterrey · Estrella", "confianza": "alta",
         "diferencia_media_mxn_kg": 3.0, "meses_pareados": 12, "confianza_pct": 80, "flete_equilibrio_mxn_kg": 3.0, "plaza_referencia": "Guadalajara · Abasto", "hasta": "2026-10"},
        {"cultivo": "limon", "variante_id": 421, "variante": "Limón #5", "mercado": 301, "nombre_mercado": "Torreón", "confianza": "baja",
         "diferencia_media_mxn_kg": 5.0, "meses_pareados": 5, "confianza_pct": 20, "flete_equilibrio_mxn_kg": 5.0, "plaza_referencia": "Guadalajara · Abasto", "hasta": "2026-10"}]))
    _escribir(tmp_path, "data/publico/exportacion_resumen.json", {"frutas": {
        "aguacate": {"disponible": True, "nombre": "Aguacate", "prima_exportacion_pct": 35.0, "anio": 2024, "hs": "080440",
                     "valor_unitario_exportacion_mxn_kg": 50.0, "precio_mayorista_nacional_mxn_kg": 37.0, "destinos": [{"pais": "USA"}]},
        "limon": {"disponible": True, "nombre": "Limón", "prima_exportacion_pct": -10.0, "anio": 2024, "hs": "080550", "destinos": [{"pais": "USA"}]}}})
    _escribir(tmp_path, "calidad/reportes/fiabilidad.json", {"frescura": {"alertas": ["noaa sin datos desde hace 5 días"]}})
    (tmp_path / "tablero").mkdir()


def test_alertas_solo_recientes_y_con_evidencia(tmp_path):
    _base_alertas(tmp_path)
    alertas = al.generar(tmp_path)
    tipos = sorted(a["tipo"] for a in alertas)
    # mango (mayo) es viejo, guayaba está en percentil medio, Torreón tiene confianza baja y el limón no tiene prima
    assert tipos == ["central_conveniente", "exportacion", "frescura", "precio_alto", "precio_bajo"]
    bajo = next(a for a in alertas if a["tipo"] == "precio_bajo")
    assert "más bajo que el 90 %" in bajo["texto"] and bajo["enlace"].endswith("preguntas.html#papaya")
    assert len({a["id"] for a in alertas}) == len(alertas)
    assert al.generar(tmp_path)[0]["id"] == alertas[0]["id"]  # identificador estable entre corridas


def test_rss_valido_y_json(tmp_path):
    _base_alertas(tmp_path)
    res = al.ejecutar(tmp_path)
    assert res["alertas"] == 5
    canal = ET.fromstring((tmp_path / "tablero/alertas.xml").read_text(encoding="utf-8")).find("channel")
    assert len(canal.findall("item")) == 5 and canal.find("language").text == "es-mx"
    assert json.loads((tmp_path / "data/publico/alertas.json").read_text(encoding="utf-8"))["alertas"][0]["id"]
    xml = al.rss([{"id": "x", "tipo": "t", "titulo": "<b>&", "texto": "a < b", "enlace": "http://e"}], datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert "&lt;b&gt;&amp;" in xml and ET.fromstring(xml) is not None


def test_alertas_sin_datos_no_falla(tmp_path):
    assert al.generar(tmp_path) == []


def _base_aciertos(tmp_path):
    comun = {"variante_id": 421, "mercado": 140, "tipo_serie": "origen_colima"}
    _escribir(tmp_path, "data/oro/pronosticos_colima.csv", pd.DataFrame([
        {**comun, "horizonte_meses": 1, "variante": "Limón #5", "nombre_mercado": "GDL", "modelo_elegido": "holt", "precio_frecuente_mxn_kg": 20.0, "ls80_mxn_kg": 23.0},
        {**comun, "horizonte_meses": 2, "variante": "Limón #5", "nombre_mercado": "GDL", "modelo_elegido": "holt", "precio_frecuente_mxn_kg": 21.0, "ls80_mxn_kg": 26.0}]))
    reales = [10, 12, 11, 15, 14]
    prons = [10, 11, 13, 13, 20]
    _escribir(tmp_path, "data/oro/validaciones_pronostico_colima.csv", pd.DataFrame(
        [{**comun, "modelo": "holt", "mes_validacion": f"2026-0{i + 1}", "segmento": "holdout", "pronostico_mxn_kg": p, "real_mxn_kg": r}
         for i, (p, r) in enumerate(zip(prons, reales, strict=True))]
        + [{**comun, "modelo": "arima_aic", "mes_validacion": "2026-01", "segmento": "holdout", "pronostico_mxn_kg": 99, "real_mxn_kg": 10}]))


def test_validacion_mide_rango_direccion_y_error(tmp_path):
    _base_aciertos(tmp_path)
    v = ac.validacion(tmp_path)
    assert len(v) == 5 and set(v["modelo"]) == {"holt"}  # solo el modelo elegido
    # semiancho 3: el último (20 vs 14) queda fuera del rango
    assert v["dentro_rango_80"].tolist() == [True, True, True, True, False]
    # dirección: 11 vs 12 (sube/sube), 13 vs 11 (baja real, pronóstico sube) ...
    assert v["direccion_correcta"].tolist()[1:] == [True, False, True, False]
    assert pd.isna(v["direccion_correcta"].iloc[0])
    r = ac.resumen(v, pd.DataFrame())
    s = r["por_serie"]["421|140|origen_colima"]
    assert s["meses_evaluados"] == 5 and s["aciertos_rango_80_pct"] == 80 and s["aciertos_direccion_pct"] == 50
    assert r["registro_permanente"]["pronosticos_emitidos"] == 0


def test_deflactor_expresa_en_pesos_del_ultimo_anio(tmp_path):
    carpeta = tmp_path / "banco_mundial/2026/11"
    carpeta.mkdir(parents=True)
    datos = [{"page": 1}, [{"date": "2024", "value": 150.0}, {"date": "2025", "value": 165.0}, {"date": "2026", "value": None}]]
    (carpeta / "banco_mundial__ipc-mexico-2010-2026__20261127T000000Z.json").write_text(json.dumps(datos), encoding="utf-8")
    (carpeta / "banco_mundial__ipc-mexico-2010-2026__20261127T000000Z.json.meta.json").write_text("{}", encoding="utf-8")
    idx = ci.indice(tmp_path)
    assert idx == {2024: 150.0, 2025: 165.0}
    f = ci.a_pesos_de(idx)
    assert f[2025] == 1.0 and abs(f[2024] - 1.1) < 1e-9
    assert ci.a_pesos_de({}) == {} and ci.indice(tmp_path / "nada") == {}


def _siap():
    filas = []
    for anio, factor_precio in ((2021, 1.0), (2025, 1.5)):
        for cultivo, mun, sup, vol, valor in (("Limón", "Tecomán", 1000, 20000, 100e6), ("Limón", "Armería", 500, 7500, 40e6),
                                              ("Papaya", "Tecomán", 400, 30000, 120e6), ("Maíz grano", "Colima", 2000, 8000, 30e6)):
            filas.append({"Anio": anio, "Nomcultivo": cultivo, "Nommunicipio": mun, "Nomunidad": "Tonelada", "superficie_cosechada_ha": sup,
                          "volumen_produccion": vol, "valor_produccion_mxn": valor * factor_precio})
    return pd.DataFrame(filas)


def test_ingreso_por_hectarea_y_comparacion_de_cultivos():
    d = {"siap": _siap(), "deflactor": {2021: 1.5, 2025: 1.0}}
    r = pq.r_ingreso_ha(d, "limon")
    # 2025: (150 + 60) millones / 1500 ha = 140 000 por ha; en pesos de hoy no cambió desde 2021 (alza = inflación)
    assert "$140,000 de ingreso bruto" in r["respuesta"] and "+0 %" in r["respuesta"] and "bruto" in r["respuesta"]
    c = pq.r_cambiar_cultivo(d, "limon")
    assert "lugar 2 de 3" in c["veredicto"] and c["confianza_pct"] == 60
    assert pq.r_ingreso_ha({"siap": pd.DataFrame(), "deflactor": {}}, "limon")["confianza"] == "no aplica"


def test_aciertos_en_respuesta_del_productor():
    pron = pd.DataFrame([{"cultivo": "limon", "horizonte_meses": 1, "variante_id": 421, "mercado": 140, "tipo_serie": "origen_colima"}])
    serie = {"meses_evaluados": 24, "desde": "2024-11", "hasta": "2026-10", "aciertos_rango_80_pct": 88.0, "aciertos_direccion_pct": 87.0, "error_medio_abs_pct": 15.1}
    d = {"pron": pron, "aciertos": {"por_serie": {"421|140|origen_colima": serie}}}
    r = pq.r_aciertos(d, "limon")
    assert "**88 %**" in r["respuesta"] and "24 meses" in r["veredicto"] and r["confianza"] != "no aplica"
    assert pq.r_aciertos({"pron": pron, "aciertos": {}}, "limon")["confianza"] == "no aplica"


def test_referencia_estacional_mismo_mes():
    filas = [{"cultivo": "mango_ataulfo", "mercado": 140, "fecha_mes": f"{a}-12-01", "precio_frecuente_kg_mean": p, "precio_frecuente_count": 4, "presentacion": "kg"}
             for a, p in ((2022, 20.0), (2023, 30.0), (2024, 25.0))]
    filas.append({"cultivo": "mango_ataulfo", "mercado": 140, "fecha_mes": "2024-06-01", "precio_frecuente_kg_mean": 99.0, "precio_frecuente_count": 4, "presentacion": "kg"})
    d = {"gold": pd.DataFrame(filas), "corte": pd.Period("2026-11", freq="M")}
    r = pq.referencia_estacional(d, "mango")
    assert r["mes_nombre"].lower() == "diciembre" and r["anios"] == 3 and r["mediana"] == 25.0 and r["maximo"] == 30.0 and r["ultimo_anio"] == 2024
    assert pq.referencia_estacional({"gold": pd.DataFrame(filas[:1]), "corte": pd.Period("2026-11", freq="M")}, "mango") is None


def test_barra_del_portal_es_idempotente(tmp_path):
    from src.inteligencia import portal

    ruta = tmp_path / "index.html"
    ruta.write_text('<html><body class="x"><h1>Panel</h1></body></html>', encoding="utf-8")
    assert portal.inyectar_barra(ruta) and portal.inyectar_barra(ruta)
    t = ruta.read_text(encoding="utf-8")
    assert t.count('class="oaic-nav"') == 1 and t.index("oaic-nav") < t.index("<h1>") and "alertas.xml" in t
    assert not portal.inyectar_barra(tmp_path / "no_existe.html")


def test_mes_sin_cambio_no_cuenta_para_la_direccion(tmp_path):
    _base_aciertos(tmp_path)
    comun = {"variante_id": 421, "mercado": 140, "tipo_serie": "origen_colima", "modelo": "holt", "segmento": "holdout"}
    _escribir(tmp_path, "data/oro/validaciones_pronostico_colima.csv", pd.DataFrame(
        [{**comun, "mes_validacion": f"2026-0{i + 1}", "pronostico_mxn_kg": p, "real_mxn_kg": 10.0} for i, p in enumerate((10.0, 10.5, 9.5))]))
    v = ac.validacion(tmp_path)
    assert v["direccion_correcta"].isna().all()
    assert ac.resumen(v, pd.DataFrame())["por_serie"]["421|140|origen_colima"]["aciertos_direccion_pct"] is None
