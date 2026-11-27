"""Preguntas de un productor de Colima respondidas con datos oficiales, nivel de confianza y acción sugerida.

    python main.py preguntas

Genera ``tablero/preguntas.html`` (por producto, con calculadora "¿me ofrecen un buen precio?") y
``docs/E4/preguntas_agricultor.md``. Cada respuesta incluye:

* **respuesta** con cifras calculadas en este corte (nunca texto fijo con números);
* **confianza** (alta, media o baja) y su **motivo**, derivado de una prueba estadística, de la validación
  fuera de muestra o de la naturaleza del dato (oficial y observado vs. inferido);
* **qué hacer** con la respuesta y sus **límites**;
* **fuente** y **fecha de los datos**.

Si un dato no existe, la respuesta lo dice. Lo que el observatorio no puede responder se lista aparte.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config.settings import BASE_DIR
from src.inteligencia.catalogo import FRUTAS
from src.inteligencia.comercial import MESES_LARGOS, REFERENCIA, mensual, mensual_referencia, nivel_de_pct
from src.tdl_e4.observatorio import MARKET_NAMES, _market_id

PRODUCTOS = {k: {"nombre": v["nombre"], "articulo": v["articulo"], "sniim": v["sniim"], "siap": v["siap"], "hs": v["hs"],
                 "hs_nota": v["hs_nota"], "claves": v["claves"]} for k, v in FRUTAS.items()}


def _de(df: pd.DataFrame, c: str) -> pd.DataFrame:
    """Filas de una fruta del catálogo (una fruta puede tener varias claves de cultivo, p. ej. mango)."""
    return df[df["cultivo"].isin(PRODUCTOS[c]["claves"])] if not df.empty and "cultivo" in df else df

NO_RESPONDE = [
    ("¿Qué plaga o enfermedad viene y cómo la controlo?", "El observatorio no captura datos fitosanitarios (SENASICA). Consulte a su técnico o junta local de sanidad vegetal."),
    ("¿Cuánto me van a costar los fertilizantes y el diésel?", "No hay fuente de costos de insumos integrada; el simulador de la vista de cliente acepta sus costos reales."),
    ("¿Quién me compra hoy y a qué precio exacto?", "Los precios son cotizaciones de plaza publicadas por el SNIIM, no ofertas de compradores. No se publican datos de personas ni empresas."),
    ("¿Va a llover o hacer frío la próxima semana?", "El observatorio usa clima observado (NOAA), no pronóstico meteorológico. Consulte al SMN de CONAGUA."),
    ("¿Me conviene un crédito o seguro agrícola?", "Fuera de alcance; no es asesoría financiera."),
]
ORDEN_CONFIANZA = {"alta": 0, "media": 1, "baja": 2, "no aplica": 3}


def _f(x: Any, nd: int = 2) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "—"
    return "—" if math.isnan(v) else f"{v:,.{nd}f}"


def _leer(base: Path, rel: str) -> pd.DataFrame:
    p = base / rel
    return pd.read_csv(p) if p.is_file() else pd.DataFrame()


def _json(base: Path, rel: str) -> dict[str, Any]:
    p = base / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def cargar(base: Path = BASE_DIR, corte: pd.Period | None = None) -> dict[str, Any]:
    gold = _leer(base, "data/oro/panel_mensual.csv")
    corte = corte or (pd.Period(pd.Timestamp.today(), freq="M") - 1)
    m = mensual(gold, corte) if not gold.empty else pd.DataFrame()
    if not m.empty:
        m = pd.concat([m, mensual_referencia(gold, corte, set(m["cultivo"].unique()))], ignore_index=True)
    return {
        "gold": gold, "corte": corte, "m": m,
        "pron": _leer(base, "data/publico/pronosticos_colima.csv"), "val": _leer(base, "data/publico/validaciones_pronostico_colima.csv"),
        "senales": _leer(base, "data/publico/senales_mercado.csv"), "cal": _leer(base, "data/publico/calendario_venta.csv"),
        "plazas": _leer(base, "data/publico/plazas_colima.csv"), "margen": _leer(base, "data/publico/margen_productor.csv"),
        "actuales": _leer(base, "data/publico/precios_sniim_actuales.csv"), "siap": _leer(base, "data/oro/produccion_municipal_siap_colima.csv"),
        "comercio": _leer(base, "data/oro/comercio_fruticola_mundial.csv"),
        "fiab": _json(base, "calidad/reportes/fiabilidad.json"), "iso": _json(base, "calidad/reportes/iso25012.json"),
        "e1": _json(base, "laboratorio/resultados/e1/resultados.json"),
        "export": _json(base, "data/publico/exportacion_resumen.json"),
    }


def _nota_base(df: pd.DataFrame) -> str:
    """Aclaración cuando el dato es referencia de mercado y no fruta de origen Colima."""
    if "base" in df and len(df) and str(df["base"].iloc[0]) == "todos los orígenes":
        return " (Referencia de mercado: no hay cotizaciones de esta fruta con origen Colima; se usa la fruta de todos los orígenes en la central.)"
    return ""


def _evidencia(n: float, objetivo: float, techo: float = 95) -> int:
    """Índice para datos observados o descriptivos: techo × (datos disponibles / datos deseables)."""
    return int(round(techo * min(1.0, n / objetivo)))


def _r(pregunta: str, respuesta: str, confianza: str | float, motivo: str, accion: str, fuente: str, actualizado: str = "—",
       veredicto: str | None = None) -> dict[str, Any]:
    """``veredicto``: la conclusión en una frase, para tarjetas y resúmenes (por defecto, la primera oración)."""
    primera = respuesta.split(". ")[0].rstrip(".") + "."
    pct = None
    if isinstance(confianza, (int, float)) and not isinstance(confianza, bool):
        pct = int(max(0, min(100, round(confianza))))
        confianza = nivel_de_pct(pct)
    return {"pregunta": pregunta, "respuesta": respuesta, "confianza": confianza, "confianza_pct": pct, "motivo": motivo,
            "accion": accion, "fuente": fuente, "actualizado": actualizado, "veredicto": veredicto or primera}


def _pronostico(d: dict[str, Any], c: str) -> pd.DataFrame:
    p = d["pron"]
    if p.empty:
        return p
    p = p[p["cultivo"].isin(PRODUCTOS[c]["claves"])]
    if "tipo_serie" in p and p["tipo_serie"].eq("origen_colima").any():
        p = p[p["tipo_serie"].eq("origen_colima")]
    return p


def _confianza_pronostico(r: pd.Series) -> tuple[int, str]:
    """Índice 0–100: 50 % precisión (1 − MAPE/40), 30 % acierto del rango de 80 % en meses no vistos,
    20 % historia disponible (meses / 120). Una serie de referencia de otro origen se descuenta 15 %."""
    mape = float(r.get("mape_backtest_pct", math.nan))
    cob = float(r.get("cobertura_80_holdout", math.nan))
    meses = float(r.get("meses_entrenamiento", 36) or 36)
    mape, cob = (40.0 if math.isnan(mape) else mape), (0.0 if math.isnan(cob) else cob)
    pct = 100 * (0.5 * max(0.0, 1 - mape / 40) + 0.3 * cob + 0.2 * min(1.0, meses / 120))
    if r.get("tipo_serie") == "referencia_mercado":
        pct *= 0.85
    return int(round(pct)), (f"error típico {mape:.0f} % en 6 meses no vistos; el rango de 80 % acertó en {cob * 100:.0f} % de esos meses; "
                             f"{int(meses)} meses de historia")


# --------------------------------------------------------------------------------------------------
# Respuestas
# --------------------------------------------------------------------------------------------------

def r_proximo_mes(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = f"¿A cuánto se va a pagar {PRODUCTOS[c]['articulo']} el próximo mes?"
    p = _pronostico(d, c)
    p = p[p["horizonte_meses"].eq(1)] if not p.empty else p
    if p.empty:
        return _r(q, f"Todavía no hay pronóstico para {PRODUCTOS[c]['articulo']}: se exigen 36 meses continuos de una misma serie y aún no se reúnen.",
                  "no aplica", "sin serie elegible", "Use el precio actual por central (pregunta 6) como referencia.", "Criterio de elegibilidad del observatorio")
    r = p.iloc[0]
    ref = r.get("tipo_serie") == "referencia_mercado"
    conf, motivo = _confianza_pronostico(r)
    texto = (f"En {r['nombre_mercado']} ({r['variante']}{', origen ' + str(r['origen']) if ref else ''}) se espera alrededor de "
             f"**{_f(r['precio_frecuente_mxn_kg'])} MXN/kg** para {r['fecha_pronostico']}. 4 de cada 5 veces el precio cae entre "
             f"{_f(r['li80_mxn_kg'])} y {_f(r['ls80_mxn_kg'])} MXN/kg; 19 de cada 20, entre {_f(r['li95_mxn_kg'])} y {_f(r['ls95_mxn_kg'])}.")
    if ref:
        texto += " No hay 36 meses de plátano de origen Colima en una central, así que es una **referencia del mercado** con fruta de otro origen."
    return _r(q, texto, conf, motivo, "Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.",
              f"SNIIM · modelo {r['modelo_elegido']}", str(r["fecha_ultimo_dato"]))


def r_vender_o_esperar(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿Me conviene vender ahora o esperar un mes?"
    p = _pronostico(d, c)
    p = p[p["horizonte_meses"].eq(1)] if not p.empty else p
    v = d["val"]
    if p.empty or v.empty:
        return _r(q, "No hay pronóstico validado para estimarlo.", "no aplica", "sin serie elegible", "Compare el precio de hoy con su historia (pregunta 2).", "—")
    r = p.iloc[0]
    sel = v[(v["variante_id"].astype(float) == float(r["variante_id"])) & (v["mercado"].map(_market_id) == _market_id(r["mercado"]))
            & (v["modelo"] == r["modelo_elegido"])].sort_values("mes_validacion")
    if sel.empty:
        return _r(q, "No hay errores de validación para estimarlo.", "no aplica", "sin validación", "—", "—")
    ultimo = float(sel["real_mxn_kg"].iloc[-1])
    escenarios = float(r["precio_frecuente_mxn_kg"]) - sel["error_mxn_kg"].to_numpy(dtype="float64")  # precio real = pronóstico − error histórico
    prob = float(np.mean(escenarios > ultimo))
    cambio = (float(r["precio_frecuente_mxn_kg"]) / ultimo - 1) * 100
    lectura = ("es más probable que suba" if prob >= 0.65 else "es más probable que baje" if prob <= 0.35 else "subir o bajar es casi igual de probable")
    conf, motivo = _confianza_pronostico(r)
    conf = min(conf, 45) if len(sel) < 12 else conf
    return _r(q, f"Último precio observado ({sel['mes_validacion'].iloc[-1]}) en {r['nombre_mercado']}: {_f(ultimo)} MXN/kg. Para {r['fecha_pronostico']} el pronóstico es "
                 f"{_f(r['precio_frecuente_mxn_kg'])} ({cambio:+.0f} %). Aplicando los {len(sel)} errores reales del modelo, en **{prob * 100:.0f} %** de los escenarios el precio "
                 f"queda por encima del actual: {lectura}.",
              conf, motivo + f"; probabilidad estimada con {len(sel)} errores históricos",
              "Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, "
              "vender por partes reduce el riesgo.",
              "SNIIM · pronóstico y validación fuera de muestra", str(r["fecha_ultimo_dato"]),
              veredicto=f"En **{prob * 100:.0f} %** de los escenarios el precio de {r['fecha_pronostico']} supera al actual ({_f(ultimo)} MXN/kg): {lectura}.")


def r_caro_o_barato(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿El precio de hoy está caro o barato comparado con otros años?"
    s = d["senales"]
    s = s[s["cultivo"].isin(PRODUCTOS[c]["claves"])] if not s.empty else s
    if s.empty:
        return _r(q, "No hay al menos 12 meses de historia de origen Colima para comparar.", "no aplica", "historia insuficiente", "—", "SNIIM")
    r = s.sort_values("meses_historia", ascending=False).iloc[0]
    n = int(r["meses_historia"])
    conf = _evidencia(n, 60) * (0.9 if str(r.get("base")) == "todos los orígenes" else 1)
    nota = _nota_base(s.loc[[r.name]])
    return _r(q, f"En {r['nombre_mercado']} el último precio ({r['ultimo_mes']}) fue {_f(r['ultimo_precio_mxn_kg'])} MXN/kg: más alto que el **{_f(r['percentil_historico'], 0)} %** "
                 f"de los últimos {n} meses. Lectura: {r['lectura']}.{nota}",
              conf, f"comparación directa con {n} meses observados", "Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.",
              "SNIIM · historia mensual de origen Colima", str(r["ultimo_mes"]))


def r_mejor_mes(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿En qué meses suele pagarse mejor?"
    cal = d["cal"]
    cal = cal[cal["cultivo"].isin(PRODUCTOS[c]["claves"]) & cal["mercado"].astype(str).eq(REFERENCIA)] if not cal.empty else cal
    if cal.empty:
        return _r(q, "Se necesitan al menos 24 meses en Guadalajara para estimar el patrón por mes; aún no se reúnen.", "no aplica", "historia insuficiente", "—", "SNIIM")
    orden = cal.sort_values("indice_estacional", ascending=False)
    altos = ", ".join(f"{MESES_LARGOS[int(x['mes']) - 1]} ({(x['indice_estacional'] - 1) * 100:+.0f} %)" for _, x in orden.head(3).iterrows())
    bajos = ", ".join(f"{MESES_LARGOS[int(x['mes']) - 1]} ({(x['indice_estacional'] - 1) * 100:+.0f} %)" for _, x in orden.tail(3).iloc[::-1].iterrows())
    conf = int(cal["confianza_pct"].iloc[0]) if "confianza_pct" in cal and pd.notna(cal["confianza_pct"].iloc[0]) else 30
    motivo = str(cal["motivo_confianza"].iloc[0]) if "motivo_confianza" in cal else "pocos años"
    texto = f"En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron {altos}; los que menos, {bajos}.{_nota_base(cal)}"
    if nivel_de_pct(conf) == "baja":
        texto += " **Pero con 3 años la diferencia entre meses no se distingue estadísticamente del azar**: no es un patrón comprobado."
    return _r(q, texto, conf, f"prueba de Kruskal-Wallis entre meses: {motivo}",
              "Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.",
              "SNIIM · índice estacional OAIC", str(d["corte"]))


def r_que_plaza(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿A qué central de abasto me conviene mandar mi fruta?"
    pl = d["plazas"]
    pl = pl[pl["cultivo"].isin(PRODUCTOS[c]["claves"]) & pl["evidencia"].eq("suficiente")] if not pl.empty else pl
    if pl.empty:
        return _r(q, "Todavía no hay al menos 3 meses en que dos centrales coticen el mismo producto de origen Colima. La captura diaria del catálogo nacional acumula esa historia.",
                  "no aplica", "sin meses pareados", "Mientras tanto compare precios del día por central (pregunta 6).", "SNIIM")
    ref = str(pl["plaza_referencia"].iloc[0]) if "plaza_referencia" in pl else "Guadalajara"
    sig = pl["confianza"].isin(["alta", "media"]) if "confianza" in pl else pd.Series(False, index=pl.index)
    mas = pl[sig & pl["diferencia_media_mxn_kg"].gt(0)].sort_values("diferencia_media_mxn_kg", ascending=False)
    menos = pl[sig & pl["diferencia_media_mxn_kg"].lt(0)].sort_values("diferencia_media_mxn_kg")
    dudosas = pl[~sig]
    periodo = f"{pl['desde'].min()} a {pl['hasta'].max()}" if "desde" in pl else "—"
    varias = pl["variante"].nunique() > 1 if "variante" in pl else False

    def etiqueta(x: pd.Series) -> str:
        return f"{x['nombre_mercado']}" + (f" ({str(x['variante']).replace(' - Primera', '')})" if varias else "")
    partes = []
    if not mas.empty:
        partes.append("Pagaron **más** que " + ref + ", con diferencia comprobada: " + "; ".join(
            f"{etiqueta(x)} +{_f(x['diferencia_media_mxn_kg'])} MXN/kg ({int(x['meses_pareados'])} meses, mayor en {_f(x['pct_meses_plaza_mayor'], 0)} % de ellos; "
            f"flete extra máximo {_f(x['flete_equilibrio_mxn_kg'])} MXN/kg)" for _, x in mas.head(3).iterrows()) + ".")
    else:
        partes.append(f"Ninguna de las {len(pl)} centrales comparadas pagó significativamente más que {ref}: **{ref} es la mejor opción comprobada** con estos datos.")
    if not menos.empty:
        partes.append("Pagaron significativamente **menos**: " + "; ".join(f"{etiqueta(x)} {_f(x['diferencia_media_mxn_kg'])}" for _, x in menos.head(5).iterrows()) + " MXN/kg.")
    if not dudosas.empty:
        partes.append(f"En {len(dudosas)} comparaciones la diferencia no se distingue del azar ({'; '.join(etiqueta(x) for _, x in dudosas.head(4).iterrows())}).")
    if not mas.empty:
        conf = int(mas.iloc[0]["confianza_pct"]) if "confianza_pct" in mas else 50
        motivo = str(mas.iloc[0]["motivo_confianza"])
        accion = (f"Pida a su transportista el costo por kilo a {mas.iloc[0]['nombre_mercado'].split(' · ')[0]} y réstele el costo a {ref.split(' · ')[0]}: si la diferencia es menor que "
                  "el \"flete extra máximo\", esa central le deja más. Sume mermas por más días de viaje y confirme comprador antes de enviar.")
    elif not menos.empty:
        conf = int(menos["confianza_pct"].min()) if "confianza_pct" in menos else 75
        motivo = f"{len(menos)} centrales pagan menos con diferencia comprobada (Wilcoxon / prueba de signos)"
        accion = f"Mantenga {ref.split(' · ')[0]} como destino principal; otra central solo conviene con un comprador que pague por arriba de lo publicado."
    else:
        conf, motivo = 30, "ninguna diferencia es estadísticamente distinguible del azar"
        accion = "Decida por costo de flete y por comprador confirmado; los precios publicados no separan a las centrales."
    if not mas.empty:
        top = mas.iloc[0]
        veredicto = f"**{etiqueta(top)}** pagó +{_f(top['diferencia_media_mxn_kg'])} MXN/kg más que {ref} en {int(top['meses_pareados'])} meses; conviene si el flete extra cuesta menos de {_f(top['flete_equilibrio_mxn_kg'])} MXN/kg."
    elif not menos.empty:
        veredicto = f"**{ref}** es la mejor opción comprobada: {len(menos)} centrales pagan significativamente menos."
    else:
        veredicto = "Los precios publicados no distinguen a las centrales; decida por flete y comprador."
    return _r(q, " ".join(partes), conf, motivo, accion, f"SNIIM · meses pareados contra {ref} (Wilcoxon / prueba de signos)", periodo, veredicto=veredicto)


def _margen_cultivo(d: dict[str, Any], c: str) -> pd.DataFrame:
    """Margen en Guadalajara; si no hay producto de Colima ahí, en la central con más meses cotizados."""
    mg = d["margen"]
    if mg.empty:
        return mg
    mg = mg[mg["cultivo"].isin(PRODUCTOS[c]["claves"]) & mg["meses_mayorista"].ge(6)]  # un año con pocos meses cotizados sesga el promedio
    ref = mg[mg["mercado"].astype(str).eq(REFERENCIA)]
    if not ref.empty:
        return ref.sort_values("anio")
    return mg.sort_values(["anio", "meses_mayorista"], ascending=False).head(1)


def r_cuanto_me_queda(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "De lo que paga la central, ¿cuánto le llega al productor?"
    mg = _margen_cultivo(d, c)
    if mg.empty:
        return _r(q, "No hay un año común entre el precio rural SIAP y cotizaciones de origen Colima en alguna central para este producto.", "no aplica", "sin año común", "—", "SIAP · SNIIM")
    r = mg.iloc[-1]
    meses = int(r["meses_mayorista"])
    return _r(q, f"En {int(r['anio'])} el productor de Colima recibió en promedio **{_f(r['precio_productor_mxn_kg'])} MXN/kg** (SIAP) y {r['nombre_mercado']} cotizó el producto de "
                 f"origen Colima en {_f(r['precio_mayorista_mxn_kg'])} MXN/kg: al productor le llegó el **{_f(r['participacion_productor_pct'], 0)} %**. Los otros "
                 f"{_f(r['diferencia_mxn_kg'])} MXN/kg cubren empaque, flete, mermas, comisiones e intermediación.",
              _evidencia(meses, 12, 85), f"promedios anuales oficiales; {meses} meses de cotización mayorista; no distingue calidades",
              "Use este porcentaje para revisar si una oferta en huerta está en línea con el mercado (calculadora de arriba).",
              "SIAP (precio medio rural) · SNIIM", str(int(r["anio"])))


def r_precio_hoy_otras(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿Cuánto se está pagando hoy en otras centrales del país?"
    a = d["actuales"]
    if a.empty:
        return _r(q, "No hay captura reciente del catálogo nacional.", "no aplica", "sin captura", "—", "SNIIM")
    a = a[a["producto"].astype(str).str.startswith(PRODUCTOS[c]["sniim"]) & a["precio_frecuente_mxn_kg"].notna()]
    col = a[a["origen"].astype(str).str.contains("Colima")]
    base = col if not col.empty else a
    if base.empty:
        return _r(q, "La última tabla nacional no trae cotizaciones por kilo de este producto.", "no aplica", "sin cotizaciones", "—", "SNIIM")
    g = base.groupby("mercado")["precio_frecuente_mxn_kg"].median().sort_values(ascending=False)
    fecha = str(base["fecha"].max())
    top = "; ".join(f"{m.split(':')[0]} {_f(v)}" for m, v in g.head(4).items())
    return _r(q, f"Cotizaciones del {fecha} ({'producto de origen Colima' if not col.empty else 'todos los orígenes'}; MXN/kg, mediana por central): más altas en {top}; "
                 f"la más baja, {g.index[-1].split(':')[0]} {_f(g.iloc[-1])}. Cotizó en {len(g)} centrales.",
              90 if len(g) >= 3 else 70, "dato oficial observado, pero de un solo día",
              "Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).", "SNIIM · catálogo nacional", fecha)


def r_riesgo(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿Qué tanto puede bajar el precio de un mes a otro?"
    m = d["m"]
    s = m[m["cultivo"].isin(PRODUCTOS[c]["claves"])] if not m.empty else m
    if s.empty:
        return _r(q, "No hay serie de origen Colima en ninguna central para medirlo.", "no aplica", "sin serie", "—", "SNIIM")
    plaza = REFERENCIA if s["mercado"].eq(REFERENCIA).any() else s.groupby("mercado")["mes"].nunique().idxmax()
    s = s[s["mercado"].eq(plaza)]
    nota = _nota_base(s)
    serie = s.groupby("mes")["precio_frecuente_kg"].mean().sort_index()
    cambios = serie.pct_change().dropna() * 100
    if len(cambios) < 6:
        return _r(q, f"Hay muy pocos meses ({len(cambios)}) para medir variaciones; se necesitan al menos 6.", "no aplica", f"{len(cambios)} cambios mensuales", "—", "SNIIM")
    peor = cambios.idxmin()
    n = len(cambios)
    return _r(q, f"En {MARKET_NAMES.get(plaza, plaza)} el precio cambió en promedio **{_f(cambios.abs().mean(), 0)} %** de un mes al siguiente. La peor caída fue de {_f(cambios.min(), 0)} % ({peor}); "
                 f"en {_f((cambios < -15).mean() * 100, 0)} % de los meses cayó más de 15 % y en {_f((cambios > 15).mean() * 100, 0)} % subió más de 15 %.{nota}",
              _evidencia(n, 60), f"{n} cambios mensuales observados (índice: meses / 60)",
              "No comprometa toda la cosecha a un solo precio o fecha: escalone ventas o acuerde parte del volumen a precio fijo.", "SNIIM · variación mensual", str(serie.index[-1]))


def r_competencia(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿De qué otros estados llega fruta a competir en Guadalajara?"
    g = d["gold"]
    if g.empty:
        return _r(q, "Sin datos.", "no aplica", "sin datos", "—", "SNIIM")
    g = g[g["cultivo"].isin(PRODUCTOS[c]["claves"]) & g["mercado"].map(_market_id).eq(REFERENCIA)].copy()
    if g.empty:
        return _r(q, "No hay cotizaciones de este producto en Guadalajara.", "no aplica", "sin datos", "—", "SNIIM")
    g["fecha_mes"] = pd.to_datetime(g["fecha_mes"])
    g = g[g["fecha_mes"] >= g["fecha_mes"].max() - pd.DateOffset(months=11)]
    part = (g.groupby("origen")["n_observaciones_precio"].sum() / g["n_observaciones_precio"].sum() * 100).sort_values(ascending=False)
    txt = ", ".join(f"{o} {v:.0f} %" for o, v in part.head(5).items())
    return _r(q, f"En los últimos 12 meses las cotizaciones de {PRODUCTOS[c]['nombre'].lower()} en Guadalajara se repartieron así por estado de origen: {txt}.",
              65, "mide presencia en cotizaciones publicadas, no toneladas vendidas",
              "Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.", "SNIIM · origen reportado", str(g["fecha_mes"].max().date()))


def r_mi_municipio(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿Cuánto se produce en mi municipio y a cuánto se pagó?"
    s = d["siap"]
    if s.empty:
        return _r(q, "Sin datos SIAP.", "no aplica", "sin datos", "—", "SIAP")
    s = s[s["Nomcultivo"].eq(PRODUCTOS[c]["siap"])]
    if s.empty:
        return _r(q, "SIAP no reporta este cultivo en Colima.", "no aplica", "sin datos", "—", "SIAP")
    anio = int(s["Anio"].max())
    s = s[s["Anio"].eq(anio)].sort_values("volumen_produccion", ascending=False)
    txt = "; ".join(f"{x['Nommunicipio']}: {x['volumen_produccion']:,.0f} t a {x['precio_medio_rural_mxn_unidad'] / 1000:.2f} MXN/kg" for _, x in s.head(4).iterrows())
    return _r(q, f"Cierre agrícola {anio}: {txt}. Total Colima: {s['volumen_produccion'].sum():,.0f} t.", 95, "estadística oficial anual de SADER-SIAP",
              "Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.", "SIAP · cierre de la producción agrícola", str(anio))


def r_historia_productor(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿Cómo ha cambiado lo que se le paga al productor en los últimos años?"
    s = d["siap"]
    s = s[s["Nomcultivo"].eq(PRODUCTOS[c]["siap"])] if not s.empty else s
    if s.empty or s["Anio"].nunique() < 3:
        return _r(q, "No hay al menos 3 años de cierres agrícolas SIAP para este cultivo.", "no aplica", "historia insuficiente", "—", "SIAP")
    g = s.groupby("Anio")[["valor_produccion_mxn", "volumen_produccion"]].sum()
    precio = (g["valor_produccion_mxn"] / g["volumen_produccion"] / 1000).dropna()
    ini, fin = int(precio.index.min()), int(precio.index.max())
    maxi, mini = int(precio.idxmax()), int(precio.idxmin())
    cambio = (precio.iloc[-1] / precio.iloc[0] - 1) * 100
    anual = ((precio.iloc[-1] / precio.iloc[0]) ** (1 / max(1, fin - ini)) - 1) * 100
    serie = ", ".join(f"{a}: {v:.2f}" for a, v in precio.items())
    vol = (g["volumen_produccion"].iloc[-1] / g["volumen_produccion"].iloc[0] - 1) * 100
    return _r(q, f"Precio medio rural en Colima (MXN/kg, SIAP): {serie}. De {ini} a {fin} cambió **{cambio:+.0f} %** ({anual:+.1f} % por año en promedio); "
                 f"el año más alto fue {maxi} ({precio.max():.2f}) y el más bajo {mini} ({precio.min():.2f}). La producción del estado cambió {vol:+.0f} % en el mismo periodo.",
              _evidencia(len(precio), 10), f"estadística oficial de {len(precio)} años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios",
              "Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.", "SIAP · cierres 2016 en adelante", str(fin))


def r_exportar(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿Podría exportar? ¿A qué países y cuánto pagan?"
    e = d.get("export", {}).get("frutas", {}).get(c)
    if not e or not e.get("disponible"):
        nota = (e or {}).get("nota") or PRODUCTOS[c]["hs_nota"] or "Sin datos de comercio exterior."
        return _r(q, f"No hay datos de exportación para {PRODUCTOS[c]['articulo']}: {nota}", "no aplica", "sin datos de UN Comtrade", "—", "UN Comtrade")
    dest = "; ".join(f"{x['pais']} (USD {x['valor_usd'] / 1e6:,.1f} millones, {_f(x['mxn_kg'])} MXN/kg"
                     + (f", {x['crecimiento_pct']:+.0f} % desde {e['anio_base_crecimiento']}" if x.get("crecimiento_pct") is not None else "") + ")"
                     for x in e["destinos"][:4])
    texto = (f"En {e['anio']} México exportó USD {e['exportaciones_mexico_usd'] / 1e6:,.1f} millones a {e['paises_destino']} países "
             f"(código HS {e['hs']}). Principales compradores: {dest}.")
    if e.get("prima_exportacion_pct") is not None:
        texto += (f" El valor promedio de exportación fue **{_f(e['valor_unitario_exportacion_mxn_kg'])} MXN/kg** frente a {_f(e['precio_mayorista_nacional_mxn_kg'])} "
                  f"MXN/kg en las centrales nacionales ({e['base_precio_nacional']}, últimos 12 meses): **{e['prima_exportacion_pct']:+.0f} %**.")
    if e.get("oportunidades"):
        texto += " Mercados grandes donde México vende poco: " + "; ".join(
            f"{o['pais']} (importa USD {o['importa_del_mundo_usd'] / 1e6:,.0f} millones; México tiene {o['participacion_mexico_pct']:.1f} %)" for o in e["oportunidades"][:3]) + "."
    if e.get("hs_nota"):
        texto += f" Nota: {e['hs_nota']}."
    pct = 70 if not e.get("hs_nota") else 55
    return _r(q, texto, pct, "dato oficial de aduanas; valor unitario aduanal (no precio al productor)" + ("; el código HS agrupa varias frutas" if e.get("hs_nota") else ""),
              "Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. "
              "Vea el detalle por país en la página de mercados extranjeros.", "UN Comtrade · tipo de cambio BCE", str(e["anio"]),
              veredicto=(f"Exportación {e['prima_exportacion_pct']:+.0f} % frente al mercado nacional; principal destino: {e['destinos'][0]['pais']}."
                         if e.get("prima_exportacion_pct") is not None and e["destinos"] else None))


def r_clima(d: dict[str, Any], c: str) -> dict[str, Any]:
    q = "¿El calor o la lluvia mueven el precio?"
    cc = next((x for x in d.get("e1", {}).get("correlacion_cruzada", []) if "temperatura" in x.get("variable", "")), None)
    if not cc or cc.get("estado") == "insuficiente":
        return _r(q, "Todavía no hay suficientes meses con clima y precio a la vez para medirlo.", "no aplica", "datos insuficientes", "—", "NOAA · laboratorio E1")
    sig = bool(cc.get("significativa"))
    texto = (f"Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue "
             f"{_f(cc['corr_max'])} con {abs(int(cc['rezago_max']))} meses de desfase ({cc['n']} meses de datos). ")
    texto += ("Es estadísticamente significativa." if sig else
              "**No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.")
    return _r(q, texto, _evidencia(cc["n"], 60, 80), f"correlación cruzada con banda de significancia ±{_f(cc.get('banda_95'), 2)}",
              "No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.", "NOAA · laboratorio E1")


def r_confianza(d: dict[str, Any], c: str) -> dict[str, Any]:
    v = d["fiab"].get("periodos", {}).get("ventana_sello_14_dias", {})
    comp = d["iso"].get("medidas", {}).get("completitud", {}).get("valor")
    return _r("¿Por qué debería creerle a estos números?",
              f"Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original "
              f"con su huella SHA-256. La captura funcionó el {_f((v.get('disponibilidad') or 0) * 100, 0)} % de los últimos {v.get('dias', 14)} días y el "
              f"{_f((comp or 0) * 100, 0)} % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.",
              int(round(50 * (v.get("disponibilidad") or 0) + 50 * (comp or 0))), "índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012", "Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.",
              "Métricas de calidad OAIC", str(v.get("hasta", "—")))


RESPUESTAS = [r_proximo_mes, r_vender_o_esperar, r_caro_o_barato, r_mejor_mes, r_que_plaza, r_precio_hoy_otras, r_cuanto_me_queda,
              r_historia_productor, r_riesgo, r_competencia, r_mi_municipio, r_exportar, r_clima, r_confianza]


def responder(d: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {c: [f(d, c) for f in RESPUESTAS] for c in PRODUCTOS}


def referencias_calculadora(d: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Valores para '¿me ofrecen un buen precio?' (precio en huerta)."""
    out = {}
    for c in PRODUCTOS:
        mg = _margen_cultivo(d, c)
        rural = float(mg.iloc[-1]["precio_productor_mxn_kg"]) if not mg.empty else None
        part = float(mg.iloc[-1]["participacion_productor_pct"]) / 100 if not mg.empty else None
        plaza = str(mg.iloc[-1]["mercado"]) if not mg.empty else REFERENCIA
        s = d["senales"]
        s = s[s["cultivo"].isin(PRODUCTOS[c]["claves"]) & s["mercado"].astype(str).eq(plaza)] if not s.empty else s
        mayorista = float(s.iloc[0]["ultimo_precio_mxn_kg"]) if not s.empty else None
        out[c] = {"plaza_referencia": MARKET_NAMES.get(plaza, plaza), "rural_anual": rural, "participacion": part, "mayorista_ultimo": mayorista,
                  "rural_estimado_hoy": round(mayorista * part, 2) if mayorista and part else None}
    return out


def _md_a_html(texto: str) -> str:
    partes = html.escape(texto).split("**")
    return "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(partes))


def html_preguntas(resp: dict[str, list[dict[str, Any]]], calc: dict[str, Any], corte: str) -> str:
    botones = "".join(f'<button data-p="{c}" aria-pressed="{str(i == 0).lower()}">{v["nombre"]}</button>' for i, (c, v) in enumerate(PRODUCTOS.items()))
    bloques = []
    for i, (c, lista) in enumerate(resp.items()):
        items = []
        for j, r in enumerate(lista, 1):
            items.append(f'<details {"open" if j <= 3 else ""}><summary><span class="n">{j}</span>{html.escape(r["pregunta"])}'
                         f'<span class="conf {r["confianza"].replace(" ", "-")}">{("Confianza " + str(r["confianza_pct"]) + " %") if r.get("confianza_pct") is not None else "Sin datos suficientes"}</span></summary>'
                         f'<p>{_md_a_html(r["respuesta"])}</p>'
                         f'<p class="accion"><b>Qué hacer:</b> {html.escape(r["accion"])}</p>'
                         f'<p class="meta">Por qué esta confianza: {html.escape(r["motivo"])} · Fuente: {html.escape(r["fuente"])} · Datos a: {html.escape(str(r["actualizado"]))}</p></details>')
        bloques.append(f'<section class="prod" data-p="{c}" {"" if i == 0 else "hidden"}>{"".join(items)}</section>')
    no = "".join(f"<li><b>{html.escape(q)}</b> {html.escape(a)}</li>" for q, a in NO_RESPONDE)
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Preguntas del productor · OAIC</title>
<style>
:root{{--ink:#17231f;--muted:#5f6d67;--line:#dde5df;--paper:#f4f7f3;--forest:#143d31;--lime:#d9ed8c;--gold:#c08a32}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
header{{background:var(--forest);color:#fff;padding:18px 16px}}header .in,main{{max-width:880px;margin:0 auto}}header a{{color:var(--lime)}}h1{{margin:6px 0;font-size:clamp(22px,4vw,30px)}}
main{{padding:16px 16px 48px}}.tabs{{display:flex;gap:8px;margin:8px 0 14px;flex-wrap:wrap}}.tabs button{{font:inherit;font-weight:700;border:2px solid var(--forest);background:#fff;color:var(--forest);border-radius:999px;padding:8px 18px;cursor:pointer}}
.tabs button[aria-pressed=true]{{background:var(--forest);color:#fff}}details{{background:#fff;border:1px solid var(--line);border-radius:12px;margin:0 0 10px;padding:4px 14px}}
summary{{font-weight:700;cursor:pointer;padding:10px 0;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}.n{{display:inline-grid;place-items:center;width:26px;height:26px;border-radius:50%;background:var(--forest);color:#fff;font-size:13px;flex:0 0 26px}}
.conf{{margin-left:auto;font-size:12px;border-radius:999px;padding:2px 10px;font-weight:700}}.conf.alta{{background:#dcefd3;color:#1f5a2c}}.conf.media{{background:#f6ecd3;color:#7a5a12}}.conf.baja{{background:#f4dcd5;color:#8a2f1d}}.conf.no-aplica{{background:#eceeed;color:#555}}
.accion{{background:#f3f8ef;border-left:4px solid var(--forest);padding:8px 10px;border-radius:6px}}.meta{{color:var(--muted);font-size:13px}}
.calc{{background:#fff;border:2px solid var(--gold);border-radius:14px;padding:14px 16px;margin:6px 0 18px}}.calc label{{font-weight:700}}
.calc input{{font:inherit;font-size:20px;width:8em;padding:6px 8px;border:1px solid var(--line);border-radius:8px;margin:0 6px}}#veredicto{{margin-top:10px;font-size:15px}}
.leyenda{{font-size:13px;color:var(--muted)}}h2{{font-size:18px;margin:22px 0 8px}}ul.no li{{margin-bottom:8px}}.muted{{color:var(--muted);font-size:13px}}
</style></head><body>
<header><div class="in"><a href="index.html">← Panel</a> · <a href="mapa.html">Mapa</a> · <a href="inteligencia.html">Reporte de inteligencia</a> · <a href="cliente.html">Vista de cliente</a>
<h1>Preguntas que se hace un productor de Colima</h1><div>Respuestas calculadas con datos oficiales · último mes cerrado {html.escape(corte)} · se actualiza cada día</div></div></header>
<main>
<div class="tabs" role="group" aria-label="Producto">{botones}</div>
<p class="leyenda"><b>Índice de confianza (0–100 %)</b>. Pronósticos: 50 % precisión en meses no vistos, 30 % acierto del rango, 20 % años de historia. Comparaciones: 60 % evidencia contra el azar (prueba estadística), 40 % cantidad de datos; si no es significativa al 5 %, no pasa de 60 %. Datos oficiales: según cobertura. ≥ 75 % alta, 50–74 % media, &lt; 50 % baja. Es un índice, no la probabilidad de acertar.</p>
<div class="calc"><label for="oferta">¿Me están ofreciendo un buen precio en la huerta?</label><br>
<span>Precio que le ofrecen:</span><input id="oferta" type="number" min="0" step="0.1" inputmode="decimal" placeholder="MXN/kg"> MXN/kg
<div id="veredicto" aria-live="polite">Escriba el precio por kilo que le ofrecen.</div>
<p class="muted">Compara con lo que normalmente llega al productor del precio mayorista actual y con el precio medio rural SIAP del último año. No conoce la calidad, el tamaño ni el costo de corte de su fruta.</p></div>
{''.join(bloques)}
<h2>Preguntas que este observatorio todavía no puede responder</h2>
<ul class="no">{no}</ul>
</main>
<script>
const REF={json.dumps(calc)};let actual="{next(iter(PRODUCTOS))}";
const fmt=v=>v==null?"—":v.toFixed(2);
function veredicto(){{const r=REF[actual],v=parseFloat(document.getElementById('oferta').value),o=document.getElementById('veredicto');
if(!(v>0)){{o.textContent="Escriba el precio por kilo que le ofrecen.";return;}}
if(r.rural_estimado_hoy==null&&r.rural_anual==null){{o.textContent="No hay referencia de precio al productor para este cultivo.";return;}}
const ref=r.rural_estimado_hoy??r.rural_anual,dif=(v-ref)/ref*100;
let t=dif>=10?"Está por ENCIMA de lo habitual":dif<=-10?"Está por DEBAJO de lo habitual: vale la pena negociar o comparar con otro comprador":"Está dentro de lo habitual";
o.innerHTML=`<b>${{t}}</b> (${{dif>=0?'+':''}}${{dif.toFixed(0)}} % frente a ${{fmt(ref)}} MXN/kg). Referencias: precio medio rural del último año ${{fmt(r.rural_anual)}} MXN/kg; mayorista actual en ${{r.plaza_referencia}} ${{fmt(r.mayorista_ultimo)}} MXN/kg, del que normalmente llega al productor ${{r.participacion?(r.participacion*100).toFixed(0):'—'}} %.`;}}
document.getElementById('oferta').addEventListener('input',veredicto);
const desdeHash=location.hash.slice(1);if(REF[desdeHash]){{actual=desdeHash;document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-pressed',x.dataset.p===actual));document.querySelectorAll('section.prod').forEach(s=>s.hidden=s.dataset.p!==actual);}}
document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{{actual=b.dataset.p;
document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-pressed',x===b));
document.querySelectorAll('section.prod').forEach(s=>s.hidden=s.dataset.p!==actual);veredicto();}}));
</script></body></html>
"""


def markdown_preguntas(resp: dict[str, list[dict[str, Any]]], corte: str) -> str:
    lineas = ["# Preguntas del productor que el observatorio responde\n",
              f"> Generado por `python main.py preguntas` (último mes cerrado {corte}). Versión interactiva con calculadora: [`tablero/preguntas.html`](../../tablero/preguntas.html).",
              "> Cada respuesta declara su nivel de confianza (alta, media o baja) y por qué.\n"]
    for c, lista in resp.items():
        lineas.append(f"## {PRODUCTOS[c]['nombre']}\n")
        for i, r in enumerate(lista, 1):
            lineas += [f"### {i}. {r['pregunta']}\n", r["respuesta"] + "\n",
                       f"- **Confianza:** {r['confianza']} — {r['motivo']}", f"- **Qué hacer:** {r['accion']}",
                       f"- **Fuente:** {r['fuente']} · **Datos a:** {r['actualizado']}\n"]
    lineas.append("## Lo que todavía no responde\n")
    lineas += [f"- **{q}** {a}" for q, a in NO_RESPONDE]
    return "\n".join(lineas) + "\n"


def ejecutar(base: Path = BASE_DIR, corte: pd.Period | None = None) -> dict[str, Any]:
    d = cargar(base, corte)
    resp = responder(d)
    calc = referencias_calculadora(d)
    (base / "tablero/preguntas.html").write_text(html_preguntas(resp, calc, str(d["corte"])), encoding="utf-8")
    (base / "docs/E4").mkdir(parents=True, exist_ok=True)
    (base / "docs/E4/preguntas_agricultor.md").write_text(markdown_preguntas(resp, str(d["corte"])), encoding="utf-8")
    resumen = {c: {r["pregunta"]: r["confianza"] for r in lista} for c, lista in resp.items()}
    (base / "data/publico/preguntas_productor.json").write_text(json.dumps({"corte": str(d["corte"]), "respuestas": resp}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"preguntas_por_producto": len(RESPUESTAS), "confianza": resumen}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corte")
    a = ap.parse_args(argv)
    print(json.dumps(ejecutar(corte=pd.Period(a.corte, freq="M") if a.corte else None), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
