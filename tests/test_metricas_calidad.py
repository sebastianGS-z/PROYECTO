"""Pruebas de las métricas de fiabilidad e ISO/IEC 25012 con bitácoras y paneles FIXTURE."""
from __future__ import annotations

import json
from datetime import date

import pandas as pd
import pytest

from calidad import metricas as m

CAMPOS = "run_id,fuente,modo,disparador,inicio_utc,fin_utc,duracion_s,estado,solicitudes,registros,archivos,errores,primer_error"


def _bitacora(tmp_path, filas):
    p = tmp_path / "bitacora.csv"
    lineas = [CAMPOS]
    for i, (dia, fuente, estado, disparador) in enumerate(filas):
        lineas.append(f"R{i}-{dia},{fuente},diaria,{disparador},{dia}T10:00:00Z,{dia}T10:01:00Z,60,{estado},1,1,1,0,")
    p.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return m.cargar_bitacora(p)


def test_mtbf_mttr_con_y_sin_fallas():
    sin = m.mtbf_mttr([True] * 5)
    assert sin["n_fallas"] == 0 and sin["mtbf_h"] is None and sin["mtbf_cota_inferior_h"] == 120 and sin["disponibilidad"] == 1
    con = m.mtbf_mttr([True, True, False, True, False, False, True, True])
    assert con["n_fallas"] == 2
    assert con["mtbf_h"] == pytest.approx(5 * 24 / 2) and con["mttr_h"] == pytest.approx(1.5 * 24)
    assert con["disponibilidad_formula"] == pytest.approx(60 / (60 + 36), rel=1e-3)


def test_reporte_fiabilidad_sin_resultados_no_es_falla_pero_dia_sin_ejecucion_si(tmp_path):
    filas = [("2026-11-01", "sniim", "exitosa", "schedule"), ("2026-11-01", "noaa_ncei", "sin_resultados", "schedule"),
             ("2026-11-02", "sniim", "sin_resultados", "schedule"),
             # 2026-11-03 sin ejecución
             ("2026-11-04", "sniim", "fallida", "schedule"),
             ("2026-11-05", "sniim", "exitosa", "workflow_dispatch")]
    rep = m.reporte_fiabilidad(_bitacora(tmp_path, filas))
    p = rep["periodos"]["desde_primera_ejecucion_en_actions"]
    assert p["dias"] == 5 and p["dias_operativos"] == 3 and p["n_fallas"] == 1 and p["mttr_h"] == 48
    assert rep["por_fuente"]["sniim"]["tasa_exito_tecnico"] == pytest.approx(3 / 4)
    assert rep["por_fuente"]["noaa_ncei"]["tasa_con_datos_nuevos"] == 0
    assert rep["objetivo_OQ1"]["cumple"] is False  # menos de 14 días y disponibilidad < 95 %
    assert rep["puntualidad_schedule"]["retraso_h_mediana"] == pytest.approx(7.0)
    assert any("noaa_ncei" in a for a in rep["frescura"]["alertas"])
    assert rep["por_fuente"]["sniim"]["ultimo_dia_con_datos_nuevos"] == "2026-11-05"


def test_reporte_fiabilidad_sin_programadas(tmp_path):
    assert m.reporte_fiabilidad(_bitacora(tmp_path, [("2026-11-01", "sniim", "exitosa", "local")]))["estado"] == "sin_datos"


def _oro(n=3, **cambios):
    lin = json.dumps([{"archivo": "no/existe.html", "sha256": "a" * 64, "ingesta_utc": "x", "registro": 1}])
    base = {"cultivo": "limon", "variante": "Limón", "variante_id": 1, "mercado": 140, "origen": "Colima",
            "presentacion": "Kilogramo", "anio": 2026, "precio_frecuente_mean": 20.0, "precio_frecuente_median": 20.0,
            "precio_frecuente_min": 18.0, "precio_frecuente_max": 22.0, "precio_frecuente_count": 1,
            "precio_min_mean": 18.0, "precio_max_mean": 22.0, "n_observaciones_precio": 1, "linaje_precios_bronce": lin,
            "tavg_c_mean": 27.0}
    filas = []
    for i in range(n):
        fila = dict(base, mes=i + 1, fecha_mes=f"2026-{i + 1:02d}-01")
        filas.append(fila)
    frame = pd.DataFrame(filas)
    for k, v in cambios.items():
        frame.loc[0, k] = v
    return frame


def test_iso25012_mide_cada_caracteristica(tmp_path):
    ds = tmp_path / "datasheet.md"
    ds.write_text("`cultivo` `variante`", encoding="utf-8")
    rep = m.reporte_iso25012(_oro(), raiz=tmp_path, hoy=date(2026, 3, 15), datasheet=ds)
    med = rep["medidas"]
    assert med["completitud"]["valor"] == 1.0 and rep["cumple_sello_completitud"]
    assert med["exactitud_sintactica_y_semantica"]["valor"] == 1.0
    assert med["consistencia"]["valor"] == 1.0 and med["unicidad"]["duplicados"] == 0
    assert med["trazabilidad"]["valor"] == 1.0 and med["trazabilidad"]["archivos_bronce_presentes"] == 0
    assert med["actualidad"]["meses_de_atraso_precios"] == 0
    assert 0 < med["comprensibilidad"]["valor"] < 1


def test_iso25012_detecta_defectos():
    rep = m.reporte_iso25012(_oro(precio_frecuente_mean=50.0, linaje_precios_bronce=None, mes=2), verificar_archivos=False)
    med = rep["medidas"]
    assert med["exactitud_sintactica_y_semantica"]["valor"] < 1
    assert med["completitud"]["valor"] < 1
    assert med["unicidad"]["duplicados"] == 1
    assert med["consistencia"]["valor"] < 1


def test_main_escribe_reportes(tmp_path, capsys):
    b = tmp_path / "b.csv"
    b.write_text(CAMPOS + "\nR1,sniim,diaria,schedule,2026-11-01T03:00:00Z,2026-11-01T03:01:00Z,60,exitosa,1,1,1,0,\n", encoding="utf-8")
    o = tmp_path / "oro.csv"
    _oro().to_csv(o, index=False)
    assert m.main(["--bitacora", str(b), "--oro", str(o), "--salida", str(tmp_path / "rep"), "--datasheet", str(tmp_path / "x.md")]) == 0
    assert (tmp_path / "rep" / "fiabilidad.json").is_file() and (tmp_path / "rep" / "iso25012.json").is_file()
    assert json.loads(capsys.readouterr().out)["completitud_oro"] == 1.0
