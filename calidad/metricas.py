"""Métricas de calidad medidas (no supuestas) del observatorio.

1. Fiabilidad y disponibilidad de la captura programada a partir de ``calidad/bitacora_capturas.csv``:
   tasa de éxito por ejecución, MTBF, MTTR, disponibilidad A = MTBF / (MTBF + MTTR) y la ventana
   de 14 días que exige el Sello TDL.
2. Calidad de datos ISO/IEC 25012 medida sobre la capa Oro (``data/oro/panel_mensual.csv``).

Definiciones operativas (documentadas también en docs/calidad/fiabilidad.md):

* Unidad de observación: el día calendario UTC. La captura diaria debe ejecutarse una vez al día.
* Un día está **operativo** si existe al menos una ejecución de captura diaria y ninguna fuente quedó
  ``fallida`` o ``parcial``. ``sin_resultados`` NO es falla del sistema: significa que la fuente
  respondió correctamente sin publicar datos nuevos (fines de semana de SNIIM, rezago de NOAA). Se
  reporta aparte como "días con datos nuevos" porque sí afecta la actualidad de los datos.
* Un día está **caído** si no hubo ejecución o alguna fuente quedó ``fallida``/``parcial``.
* Una **falla** es el inicio de una racha de días caídos. MTTR = duración media de esas rachas;
  MTBF = horas operativas / número de fallas. Sin fallas observadas, MTBF se reporta como cota
  inferior (">= horas observadas") y la disponibilidad es la proporción de días operativos.

    python -m calidad.metricas [--bitacora ...] [--oro ...] [--hasta AAAA-MM-DD] [--salida calidad/reportes]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
FALLA = {"fallida", "parcial"}
EXITO_CON_DATOS = {"exitosa"}
DISPAROS_PROGRAMADOS = {"schedule", "workflow_dispatch"}
VENTANA_SELLO = 14
DIAS_ALERTA_FRESCURA = 7


# --------------------------------------------------------------------------------------------------
# Fiabilidad
# --------------------------------------------------------------------------------------------------

def cargar_bitacora(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"run_id": str})
    frame["inicio_utc"] = pd.to_datetime(frame["inicio_utc"], utc=True)
    frame["fin_utc"] = pd.to_datetime(frame["fin_utc"], utc=True)
    frame["dia"] = frame["inicio_utc"].dt.date
    return frame.drop_duplicates(subset=["run_id", "fuente"], keep="last")


def estado_diario(bitacora: pd.DataFrame, desde: date, hasta: date) -> pd.DataFrame:
    """Una fila por día con el estado operativo de la captura diaria programada."""
    diaria = bitacora[bitacora["modo"].eq("diaria") & bitacora["disparador"].isin(DISPAROS_PROGRAMADOS)]
    filas = []
    dia = desde
    while dia <= hasta:
        del_dia = diaria[diaria["dia"].eq(dia)]
        estados = set(del_dia["estado"])
        filas.append({
            "dia": dia.isoformat(),
            "ejecuciones": int(del_dia["run_id"].nunique()),
            "operativo": bool(len(del_dia)) and not (estados & FALLA),
            "fuentes_con_datos_nuevos": sorted(del_dia.loc[del_dia["estado"].isin(EXITO_CON_DATOS), "fuente"].unique().tolist()),
            "estados": {f: e for f, e in zip(del_dia["fuente"], del_dia["estado"], strict=True)},
            "motivo_caida": None if (len(del_dia) and not (estados & FALLA)) else ("sin ejecución" if del_dia.empty else "fuente fallida/parcial"),
        })
        dia += timedelta(days=1)
    return pd.DataFrame(filas)


def mtbf_mttr(operativo: list[bool]) -> dict[str, Any]:
    """MTBF/MTTR en horas sobre una secuencia diaria de estados (True = operativo)."""
    horas_dia = 24.0
    rachas_caida, actual = [], 0
    for ok in operativo:
        if ok:
            if actual:
                rachas_caida.append(actual)
            actual = 0
        else:
            actual += 1
    if actual:
        rachas_caida.append(actual)
    n_fallas = len(rachas_caida)
    horas_operativas = sum(operativo) * horas_dia
    horas_total = len(operativo) * horas_dia
    disponibilidad_observada = sum(operativo) / len(operativo) if operativo else None
    if n_fallas == 0:
        return {"n_fallas": 0, "mtbf_h": None, "mtbf_cota_inferior_h": horas_operativas, "mttr_h": 0.0,
                "disponibilidad": disponibilidad_observada, "disponibilidad_formula": None,
                "horas_observadas": horas_total,
                "nota": "Sin fallas en el periodo: MTBF no estimable, se reporta su cota inferior (horas operativas observadas)."}
    mtbf = horas_operativas / n_fallas
    mttr = float(np.mean(rachas_caida)) * horas_dia
    return {"n_fallas": n_fallas, "mtbf_h": round(mtbf, 2), "mtbf_cota_inferior_h": None, "mttr_h": round(mttr, 2),
            "disponibilidad": disponibilidad_observada, "disponibilidad_formula": round(mtbf / (mtbf + mttr), 4),
            "horas_observadas": horas_total, "nota": "A = MTBF / (MTBF + MTTR), granularidad diaria."}


def reporte_fiabilidad(bitacora: pd.DataFrame, hasta: date | None = None) -> dict[str, Any]:
    programadas = bitacora[bitacora["modo"].eq("diaria") & bitacora["disparador"].isin(DISPAROS_PROGRAMADOS)]
    if programadas.empty:
        return {"estado": "sin_datos", "motivo": "La bitácora no tiene ejecuciones diarias programadas"}
    primera = programadas["dia"].min()
    primera_schedule = programadas.loc[programadas["disparador"].eq("schedule"), "dia"].min()
    hasta = hasta or bitacora["dia"].max()
    diario = estado_diario(bitacora, primera, hasta)
    periodos = {
        "desde_primera_ejecucion_en_actions": (primera, hasta),
        "desde_activacion_del_schedule": (primera_schedule, hasta) if pd.notna(primera_schedule) else None,
        "ventana_sello_14_dias": (max(primera, hasta - timedelta(days=VENTANA_SELLO - 1)), hasta),
    }
    resultados: dict[str, Any] = {}
    for nombre, rango in periodos.items():
        if not rango:
            continue
        ini, fin = rango
        sub = diario[(diario["dia"] >= ini.isoformat()) & (diario["dia"] <= fin.isoformat())]
        resultados[nombre] = {"desde": ini.isoformat(), "hasta": fin.isoformat(), "dias": int(len(sub)),
                              "dias_operativos": int(sub["operativo"].sum()),
                              **mtbf_mttr(sub["operativo"].tolist())}

    por_fuente = {}
    alertas = []
    for fuente, grupo in programadas.groupby("fuente"):
        ultima = grupo.loc[grupo["estado"].isin(EXITO_CON_DATOS), "dia"].max()
        dias_sin = (hasta - ultima).days if pd.notna(ultima) else None
        recientes = grupo[grupo["dia"] > hasta - timedelta(days=DIAS_ALERTA_FRESCURA)]
        if len(recientes) and not recientes["estado"].isin(EXITO_CON_DATOS).any():
            alertas.append(f"{fuente}: sin datos nuevos en las ejecuciones de los últimos {DIAS_ALERTA_FRESCURA} días"
                           + (f" (último dato nuevo: {ultima.isoformat()})" if pd.notna(ultima) else " (nunca en ejecuciones programadas)"))
        por_fuente[fuente] = {
            "ejecuciones": int(len(grupo)),
            "tasa_exito_tecnico": round(float((~grupo["estado"].isin(FALLA)).mean()), 4),
            "tasa_con_datos_nuevos": round(float(grupo["estado"].isin(EXITO_CON_DATOS).mean()), 4),
            "estados": {k: int(v) for k, v in grupo["estado"].value_counts().items()},
            "duracion_s_mediana": round(float(grupo["duracion_s"].median()), 2),
            "duracion_s_max": round(float(grupo["duracion_s"].max()), 2),
            "ultimo_dia_con_datos_nuevos": ultima.isoformat() if pd.notna(ultima) else None,
            "dias_desde_ultimo_dato_nuevo": dias_sin,
        }
    # Puntualidad: el cron está a las 03:00 UTC; GitHub Actions puede retrasar los schedule.
    sched = programadas[programadas["disparador"].eq("schedule")].drop_duplicates("run_id")
    retraso_h = (sched["inicio_utc"].dt.hour + sched["inicio_utc"].dt.minute / 60 - 3.0)
    ventana = resultados["ventana_sello_14_dias"]
    return {
        "esquema": "oaic-fiabilidad/1",
        "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
        "definiciones": {"operativo": "≥1 ejecución diaria programada y ninguna fuente fallida/parcial",
                         "falla": "inicio de una racha de días caídos (sin ejecución o con fuente fallida/parcial)",
                         "sin_resultados": "no es falla: la fuente respondió sin datos nuevos; se mide aparte"},
        "periodos": resultados,
        "por_fuente": por_fuente,
        "frescura": {"regla": f"alerta si una fuente no trae datos nuevos en {DIAS_ALERTA_FRESCURA} días de ejecuciones", "alertas": alertas},
        "puntualidad_schedule": {"cron_utc": "03:00", "ejecuciones": int(len(sched)),
                                 "retraso_h_mediana": round(float(retraso_h.median()), 2) if len(sched) else None,
                                 "retraso_h_max": round(float(retraso_h.max()), 2) if len(sched) else None},
        "objetivo_OQ1": {"meta": 0.95, "medido_ventana_14d": ventana["disponibilidad"],
                         "cumple": bool(ventana["disponibilidad"] is not None and ventana["disponibilidad"] >= 0.95
                                        and ventana["dias"] >= VENTANA_SELLO)},
        "detalle_diario": diario.to_dict("records"),
    }


# --------------------------------------------------------------------------------------------------
# ISO/IEC 25012
# --------------------------------------------------------------------------------------------------

OBLIGATORIAS = ["cultivo", "variante", "variante_id", "mercado", "origen", "presentacion", "anio", "mes",
                "precio_frecuente_mean", "precio_frecuente_median", "precio_frecuente_count",
                "n_observaciones_precio", "linaje_precios_bronce", "fecha_mes"]
CLAVE_ORO = ["variante_id", "mercado", "origen", "presentacion", "anio", "mes"]


def _linaje(valor: Any) -> list[dict[str, Any]]:
    if not isinstance(valor, str) or not valor.strip():
        return []
    try:
        data = json.loads(valor)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def reporte_iso25012(oro: pd.DataFrame, raiz: Path = BASE_DIR, hoy: date | None = None,
                     datasheet: Path | None = None, verificar_archivos: bool = True) -> dict[str, Any]:
    hoy = hoy or date.today()
    n = len(oro)
    medidas: dict[str, Any] = {}

    obligatorias = [c for c in OBLIGATORIAS if c in oro.columns]
    faltan_columnas = sorted(set(OBLIGATORIAS) - set(obligatorias))
    celdas = oro[obligatorias].notna().to_numpy()
    medidas["completitud"] = {
        "definicion": "celdas no nulas en las columnas obligatorias de Oro / celdas totales de esas columnas",
        "valor": round(float(celdas.mean()), 4) if celdas.size else 0.0,
        "columnas_obligatorias_ausentes": faltan_columnas,
        "completitud_tabla_completa": round(float(oro.notna().to_numpy().mean()), 4),
        "nota": "Las columnas de clima pueden ser nulas por diseño (NOAA sin publicación); se reportan en la completitud de tabla completa.",
        "por_columna_clima": {c: round(float(oro[c].notna().mean()), 4) for c in ("tavg_c_mean", "prcp_mm_mean") if c in oro},
    }

    reglas = []
    if {"precio_frecuente_min", "precio_frecuente_max", "precio_frecuente_mean"} <= set(oro.columns):
        reglas.append(("precio_frecuente_min <= mean <= max",
                       oro["precio_frecuente_min"].le(oro["precio_frecuente_mean"] + 1e-9)
                       & oro["precio_frecuente_mean"].le(oro["precio_frecuente_max"] + 1e-9)))
    if {"precio_min_mean", "precio_max_mean"} <= set(oro.columns):
        reglas.append(("precio_min_mean <= precio_max_mean", oro["precio_min_mean"].le(oro["precio_max_mean"] + 1e-9)))
    precios = [c for c in oro.columns if c.startswith("precio_") and c.endswith(("_mean", "_min", "_max", "_median"))]
    if precios:
        reglas.append(("precios positivos", (oro[precios].fillna(1) > 0).all(axis=1)))
    if "tavg_c_mean" in oro:
        reglas.append(("temperatura media en [-10, 50] °C", oro["tavg_c_mean"].isna() | oro["tavg_c_mean"].between(-10, 50)))
    if {"anio", "mes"} <= set(oro.columns):
        reglas.append(("mes 1..12 y año >= 2000", oro["mes"].between(1, 12) & oro["anio"].ge(2000)))
    medidas["exactitud_sintactica_y_semantica"] = {
        "definicion": "filas que cumplen todas las reglas de rango y dominio / filas",
        "valor": round(float(np.logical_and.reduce([m.to_numpy() for _, m in reglas]).mean()), 4) if reglas and n else None,
        "por_regla": {nombre: round(float(m.mean()), 4) for nombre, m in reglas},
    }

    consist = []
    if {"precio_frecuente_count", "n_observaciones_precio"} <= set(oro.columns):
        consist.append(("precio_frecuente_count <= n_observaciones_precio", oro["precio_frecuente_count"].le(oro["n_observaciones_precio"])))
    if {"anio", "mes", "fecha_mes"} <= set(oro.columns):
        esperado = oro["anio"].astype(int).astype(str) + "-" + oro["mes"].astype(int).astype(str).str.zfill(2)
        consist.append(("fecha_mes coincide con anio/mes", oro["fecha_mes"].astype(str).str[:7].eq(esperado)))
    lin_n = oro["linaje_precios_bronce"].map(lambda v: len(_linaje(v))) if "linaje_precios_bronce" in oro else None
    if lin_n is not None and "n_observaciones_precio" in oro:
        consist.append(("referencias de linaje == observaciones agregadas", lin_n.eq(oro["n_observaciones_precio"])))
    medidas["consistencia"] = {
        "definicion": "filas sin contradicciones internas entre campos relacionados / filas",
        "valor": round(float(np.logical_and.reduce([m.to_numpy() for _, m in consist]).mean()), 4) if consist and n else None,
        "por_regla": {nombre: round(float(m.mean()), 4) for nombre, m in consist},
    }

    duplicados = int(oro.duplicated(subset=[c for c in CLAVE_ORO if c in oro.columns]).sum()) if n else 0
    medidas["unicidad"] = {"definicion": "1 - filas con clave (variante, mercado, origen, presentación, año, mes) repetida / filas",
                           "valor": round(1 - duplicados / n, 4) if n else None, "duplicados": duplicados}

    referencias, existentes, muestras = 0, 0, 0
    if lin_n is not None:
        con_linaje = lin_n.gt(0)
        if verificar_archivos:
            archivos = {ref.get("archivo") for v in oro["linaje_precios_bronce"] for ref in _linaje(v)}
            referencias = len(archivos)
            existentes = sum(1 for a in archivos if a and (raiz / a).is_file())
            muestras = referencias
        medidas["trazabilidad"] = {
            "definicion": "filas con linaje a Bronce (archivo, SHA-256, ingesta, índice) / filas",
            "valor": round(float(con_linaje.mean()), 4) if n else None,
            "archivos_bronce_referenciados": referencias,
            "archivos_bronce_presentes": existentes,
            "proporcion_archivos_presentes": round(existentes / muestras, 4) if muestras else None,
        }
        medidas["credibilidad"] = {
            "definicion": "filas cuyo origen es una fuente oficial (SNIIM/NOAA) verificable por linaje y hash / filas",
            "valor": round(float(con_linaje.mean()), 4) if n else None,
            "nota": "La credibilidad se apoya en la fuente oficial y la verificación SHA-256 de Bronce (python main.py validar).",
        }

    if {"anio", "mes"} <= set(oro.columns) and n:
        ultimo_mes = pd.Period(year=int(oro["anio"].max()), month=int(oro.loc[oro["anio"].eq(oro["anio"].max()), "mes"].max()), freq="M")
        meses_atraso = (pd.Period(hoy, freq="M") - ultimo_mes).n
        clima_ultimo = None
        if "tavg_c_mean" in oro and oro["tavg_c_mean"].notna().any():
            clima = oro[oro["tavg_c_mean"].notna()]
            clima_ultimo = str(pd.Period(year=int(clima["anio"].max()), month=int(clima.loc[clima["anio"].eq(clima["anio"].max()), "mes"].max()), freq="M"))
        medidas["actualidad"] = {"definicion": "meses entre el último mes con precios en Oro y la fecha de medición",
                                 "ultimo_mes_precios": str(ultimo_mes), "meses_de_atraso_precios": int(meses_atraso),
                                 "ultimo_mes_con_clima": clima_ultimo, "valor": 1.0 if meses_atraso <= 1 else 0.0}

    if datasheet and datasheet.is_file():
        texto = datasheet.read_text(encoding="utf-8")
        documentadas = [c for c in oro.columns if f"`{c}`" in texto or c in texto]
        medidas["comprensibilidad"] = {"definicion": "columnas de Oro descritas en el datasheet / columnas",
                                       "valor": round(len(documentadas) / len(oro.columns), 4),
                                       "no_documentadas": sorted(set(oro.columns) - set(documentadas))}

    medidas["portabilidad"] = {"definicion": "formato abierto, UTF-8, sin dependencias propietarias", "valor": 1.0,
                               "evidencia": "CSV UTF-8 + licencia CC BY 4.0 (data/publico/LICENSE.md)"}
    return {"esquema": "oaic-iso25012/1", "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
            "fecha_medicion": hoy.isoformat(), "filas_oro": n, "columnas_oro": int(oro.shape[1]),
            "medidas": medidas,
            "umbral_sello_completitud": 0.95,
            "cumple_sello_completitud": bool(medidas["completitud"]["valor"] >= 0.95)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bitacora", type=Path, default=BASE_DIR / "calidad" / "bitacora_capturas.csv")
    ap.add_argument("--oro", type=Path, default=BASE_DIR / "data" / "oro" / "panel_mensual.csv")
    ap.add_argument("--datasheet", type=Path, default=BASE_DIR / "docs" / "E3" / "datasheet.md")
    ap.add_argument("--hasta", help="último día (UTC) a evaluar; por defecto el último de la bitácora")
    ap.add_argument("--salida", type=Path, default=BASE_DIR / "calidad" / "reportes")
    a = ap.parse_args(argv)
    a.salida.mkdir(parents=True, exist_ok=True)
    fiab = reporte_fiabilidad(cargar_bitacora(a.bitacora), date.fromisoformat(a.hasta) if a.hasta else None)
    iso = reporte_iso25012(pd.read_csv(a.oro), datasheet=a.datasheet)
    (a.salida / "fiabilidad.json").write_text(json.dumps(fiab, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (a.salida / "iso25012.json").write_text(json.dumps(iso, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    resumen = {
        "disponibilidad_14d": fiab.get("periodos", {}).get("ventana_sello_14_dias", {}).get("disponibilidad"),
        "completitud_oro": iso["medidas"]["completitud"]["valor"],
        "salidas": [str(a.salida / "fiabilidad.json"), str(a.salida / "iso25012.json")],
    }
    print(json.dumps(resumen, ensure_ascii=False))
    for alerta in fiab.get("frescura", {}).get("alertas", []):
        # Formato de anotación de GitHub Actions: aparece como aviso en el resumen del job sin fallarlo.
        print(f"::warning title=Frescura de datos::{alerta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
