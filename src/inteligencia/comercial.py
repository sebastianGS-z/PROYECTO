"""Inteligencia comercial a partir de datos verificables (SNIIM, SIAP, NOAA).

Productos que genera (``python main.py inteligencia``):

* ``margen_productor.csv`` — precio medio rural SIAP (lo que se pagó al productor en Colima) frente al
  precio mayorista SNIIM de producto de origen Colima en cada plaza, mismo año.
* ``plazas_colima.csv`` — para cada plaza, diferencia de precio frente a Guadalajara en meses pareados y
  **flete de equilibrio**: cuánto puede costar de más el envío por kg para que esa plaza siga convenciendo.
  No se inventan tarifas de flete: el usuario compara su cotización real contra ese umbral.
* ``calendario_venta.csv`` — índice estacional por mes calendario (qué meses suelen pagar más).
* ``senales_mercado.csv`` — posición del último precio en su historia (percentil) y dirección del pronóstico.

Cada salida conserva el periodo, el número de meses y la fuente; todo cálculo es reproducible desde Oro.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from config.settings import BASE_DIR
from src.tdl_e4.observatorio import MARKET_NAMES, _market_id, _mensual_colima

REFERENCIA = "140"  # Guadalajara · Mercado de Abasto: plaza con 36 meses continuos de origen Colima
TECOMAN = (18.9089, -103.8747)  # cabecera municipal; principal zona productora de limón, plátano y papaya
CIUDAD_MERCADO = {
    "80": "Colima", "100": "Iztapalapa, Ciudad de México", "140": "Guadalajara", "141": "Guadalajara", "160": "Morelia",
    "180": "Tepic", "181": "Tepic", "10": "Aguascalientes", "20": "La Paz", "33": "Tijuana", "50": "Torreón",
    "61": "Chihuahua", "63": "Ciudad Juárez", "101": "Gómez Palacio", "190": "San Nicolás de los Garza",
    "220": "Santiago de Querétaro", "240": "San Luis Potosí", "260": "Hermosillo", "261": "Ciudad Obregón",
    "270": "Villahermosa", "306": "Veracruz",
}
SIAP_CULTIVO = {"Limón": "limon", "Papaya": "papaya", "Plátano": "platano"}
NOMBRE_CULTIVO = {"limon": "Limón", "platano": "Plátano", "papaya": "Papaya", "tamarindo": "Tamarindo", "guayaba": "Guayaba"}
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MIN_MESES_PAREADOS = 3
ALFA = 0.05


def nivel_confianza(p: float | None, n: int, n_alto: int, n_medio: int) -> tuple[str, str]:
    """Nivel de confianza de un resultado según su prueba estadística y la cantidad de evidencia.

    alta: significativo al 5 % y con evidencia ≥ n_alto · media: significativo con menos evidencia, o
    evidencia amplia sin significancia clara (p < 0.20) · baja: lo demás.
    """
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "baja", f"sin prueba estadística posible con {n} observaciones"
    if p < ALFA and n >= n_alto:
        return "alta", f"p = {p:.3f} con {n} observaciones"
    if p < ALFA and n >= n_medio:
        return "media", f"p = {p:.3f}, pero solo {n} observaciones"
    if p < 0.20 and n >= n_alto:
        return "media", f"tendencia no concluyente (p = {p:.3f}) con {n} observaciones"
    return "baja", f"no se distingue del azar (p = {p:.3f}, {n} observaciones)"


def prueba_diferencia(dif: pd.Series) -> tuple[float | None, str]:
    """Wilcoxon de rangos con signo (≥ 6 meses) o prueba de signos binomial (3–5 meses), bilateral."""
    dif = dif[dif != 0]
    if len(dif) >= 6:
        return float(stats.wilcoxon(dif).pvalue), "Wilcoxon de rangos con signo"
    if len(dif) >= 3:
        return float(stats.binomtest(int((dif > 0).sum()), len(dif), 0.5).pvalue), "prueba de signos"
    return None, "sin prueba (menos de 3 meses con diferencia)"


def _nombre(mercado: str) -> str:
    return MARKET_NAMES.get(str(mercado), f"Mercado SNIIM {mercado}")


def distancias_km(geojson: Path) -> dict[str, float]:
    """Distancia en línea recta (gran círculo) de Tecomán a la ciudad de cada mercado."""
    if not geojson.is_file():
        return {}
    data = json.loads(geojson.read_text(encoding="utf-8"))
    ciudades = {f["properties"]["ciudad"]: f["geometry"]["coordinates"] for f in data.get("features", [])
                if f.get("geometry", {}).get("type") == "Point"}
    out = {}
    for mercado, ciudad in CIUDAD_MERCADO.items():
        if ciudad in ciudades:
            lon, lat = ciudades[ciudad]
            out[mercado] = round(_haversine(TECOMAN[0], TECOMAN[1], lat, lon), 0)
    return out


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def mensual(gold: pd.DataFrame, corte: pd.Period) -> pd.DataFrame:
    """Precio frecuente mensual (MXN/kg) de producto de origen Colima por variante y plaza, meses cerrados."""
    m = _mensual_colima(gold)
    m = m[m["mes"].le(corte)].copy()
    m["mercado"] = m["mercado"].map(_market_id)
    return m[["cultivo", "variante_id", "variante", "mercado", "mes", "precio_frecuente_kg", "n_observaciones"]]


# --------------------------------------------------------------------------------------------------
# 1. Margen del productor
# --------------------------------------------------------------------------------------------------

def margen_productor(m: pd.DataFrame, siap: pd.DataFrame) -> pd.DataFrame:
    siap = siap[siap["Nomcultivo"].isin(SIAP_CULTIVO) & siap["Nomunidad"].str.casefold().eq("tonelada")].copy()
    if siap.empty or m.empty:
        return pd.DataFrame()
    filas = []
    for (anio, cultivo_siap), g in siap.groupby(["Anio", "Nomcultivo"]):
        cultivo = SIAP_CULTIVO[cultivo_siap]
        g = g[g["volumen_produccion"].gt(0) & g["precio_medio_rural_mxn_unidad"].gt(0)]
        if g.empty:
            continue
        productor = float(np.average(g["precio_medio_rural_mxn_unidad"], weights=g["volumen_produccion"])) / 1000
        anual = m[m["cultivo"].eq(cultivo) & m["mes"].map(lambda p: p.year).eq(int(anio))]
        for mercado, gm in anual.groupby("mercado"):
            meses = gm["mes"].nunique()
            mayorista = float(np.average(gm["precio_frecuente_kg"], weights=gm["n_observaciones"]))
            filas.append({"anio": int(anio), "cultivo": cultivo, "mercado": mercado, "nombre_mercado": _nombre(mercado),
                          "precio_productor_mxn_kg": round(productor, 2), "precio_mayorista_mxn_kg": round(mayorista, 2),
                          "diferencia_mxn_kg": round(mayorista - productor, 2),
                          "participacion_productor_pct": round(productor / mayorista * 100, 1),
                          "meses_mayorista": int(meses),
                          "volumen_colima_ton": round(float(g["volumen_produccion"].sum()), 1),
                          "nota": "SIAP: precio medio rural anual ponderado por volumen de los municipios de Colima; "
                                  "SNIIM: promedio anual ponderado de cotizaciones de origen Colima en la plaza. "
                                  "La diferencia incluye empaque, flete, mermas, comisiones e intermediación; no es la ganancia de un actor."})
    return pd.DataFrame(filas).sort_values(["cultivo", "meses_mayorista", "precio_mayorista_mxn_kg"], ascending=[True, False, False])


# --------------------------------------------------------------------------------------------------
# 2. Comparación de plazas y flete de equilibrio
# --------------------------------------------------------------------------------------------------

def comparar_plazas(m: pd.DataFrame, dist: dict[str, float], referencia: str = REFERENCIA) -> pd.DataFrame:
    filas = []
    for (cultivo, vid), g in m.groupby(["cultivo", "variante_id"]):
        piv = g.pivot_table(index="mes", columns="mercado", values="precio_frecuente_kg")
        if piv.shape[1] < 2:
            continue
        # Guadalajara es la referencia; si el producto de Colima no se cotiza ahí, la plaza con más meses.
        ref = referencia if referencia in piv else str(piv.notna().sum().idxmax())
        variante = g["variante"].iloc[0]
        for mercado in piv.columns:
            if mercado == ref:
                continue
            par = piv[[ref, mercado]].dropna()
            if len(par) < 1:
                continue
            dif = par[mercado] - par[ref]
            ultimos = dif.tail(3)
            p_dif, prueba = prueba_diferencia(dif)
            confianza, motivo = nivel_confianza(p_dif, len(par), 9, MIN_MESES_PAREADOS)
            d_ref, d_mer = dist.get(ref), dist.get(mercado)
            km_extra = (d_mer - d_ref) if d_ref is not None and d_mer is not None else None
            filas.append({
                "cultivo": cultivo, "variante_id": vid, "variante": variante, "mercado": mercado, "nombre_mercado": _nombre(mercado),
                "meses_pareados": int(len(par)), "desde": str(par.index.min()), "hasta": str(par.index.max()),
                "precio_plaza_mxn_kg": round(float(par[mercado].mean()), 2), "precio_referencia_mxn_kg": round(float(par[ref].mean()), 2),
                "plaza_referencia": _nombre(ref), "mercado_referencia": ref,
                "diferencia_media_mxn_kg": round(float(dif.mean()), 2),
                "diferencia_ultimos_3_meses_mxn_kg": round(float(ultimos.mean()), 2),
                "pct_meses_plaza_mayor": round(float((dif > 0).mean() * 100), 0),
                "flete_equilibrio_mxn_kg": round(max(0.0, float(dif.mean())), 2),
                "distancia_km_linea_recta": dist.get(mercado), "km_extra_vs_referencia": km_extra,
                "flete_equilibrio_mxn_ton_km_extra": round(float(dif.mean()) * 1000 / km_extra, 2) if km_extra and km_extra > 0 and dif.mean() > 0 else None,
                "evidencia": "suficiente" if len(par) >= MIN_MESES_PAREADOS else "insuficiente (menos de 3 meses pareados)",
                "prueba": prueba, "p_valor": round(p_dif, 4) if p_dif is not None else None,
                "confianza": confianza, "motivo_confianza": motivo,
            })
    out = pd.DataFrame(filas)
    if out.empty:
        return out
    return out.sort_values(["cultivo", "evidencia", "diferencia_media_mxn_kg"], ascending=[True, False, False]).reset_index(drop=True)


# --------------------------------------------------------------------------------------------------
# 3. Calendario de venta (estacionalidad) y 4. señales
# --------------------------------------------------------------------------------------------------

def calendario_venta(m: pd.DataFrame, min_meses: int = 24) -> pd.DataFrame:
    filas = []
    for (cultivo, vid, mercado), g in m.groupby(["cultivo", "variante_id", "mercado"]):
        s = g.set_index("mes")["precio_frecuente_kg"].sort_index()
        if len(s) < min_meses:
            continue
        # Índice: precio del mes / media móvil centrada de 12 meses (quita tendencia); promedio por mes calendario.
        ts = s.copy()
        ts.index = ts.index.to_timestamp()
        tendencia = ts.rolling(12, center=True, min_periods=6).mean()
        ratio = (ts / tendencia).dropna()
        por_mes = ratio.groupby(ratio.index.month).agg(["mean", "count"])
        grupos = [v.to_numpy() for _, v in ratio.groupby(ratio.index.month) if len(v) >= 2]
        p_est = float(stats.kruskal(*grupos).pvalue) if len(grupos) >= 3 else None
        confianza, motivo = nivel_confianza(p_est, len(ratio), 36, 24)
        for mes, fila in por_mes.iterrows():
            filas.append({"cultivo": cultivo, "variante_id": vid, "variante": g["variante"].iloc[0], "mercado": mercado,
                          "nombre_mercado": _nombre(mercado), "mes": int(mes), "mes_nombre": MESES[int(mes) - 1],
                          "indice_estacional": round(float(fila["mean"]), 3), "anios_observados": int(fila["count"]),
                          "lectura": f"{(fila['mean'] - 1) * 100:+.0f} % frente a la tendencia",
                          "p_estacionalidad_kruskal": round(p_est, 4) if p_est is not None else None,
                          "confianza_patron": confianza, "motivo_confianza": motivo})
    return pd.DataFrame(filas)


def senales(m: pd.DataFrame, pronosticos: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for (cultivo, vid, mercado), g in m.groupby(["cultivo", "variante_id", "mercado"]):
        s = g.set_index("mes")["precio_frecuente_kg"].sort_index()
        if len(s) < 12:
            continue
        ultimo = float(s.iloc[-1])
        pct = float((s < ultimo).mean() * 100)
        f = pronosticos[(pronosticos["variante_id"].astype(float) == float(vid)) & (pronosticos["mercado"].map(_market_id) == mercado)] if not pronosticos.empty else pd.DataFrame()
        prox = f.sort_values("fecha_pronostico").iloc[0] if len(f) else None
        if pct >= 75:
            lectura = "precio alto respecto a su historia: buen momento para vender, mal momento para comprar inventario"
        elif pct <= 25:
            lectura = "precio bajo respecto a su historia: conviene revisar si se puede esperar o almacenar"
        else:
            lectura = "precio en rango normal"
        filas.append({"cultivo": cultivo, "variante_id": vid, "variante": g["variante"].iloc[0], "mercado": mercado,
                      "nombre_mercado": _nombre(mercado), "ultimo_mes": str(s.index[-1]), "ultimo_precio_mxn_kg": round(ultimo, 2),
                      "percentil_historico": round(pct, 0), "meses_historia": int(len(s)), "lectura": lectura,
                      "pronostico_siguiente_mes": round(float(prox["precio_frecuente_mxn_kg"]), 2) if prox is not None else None,
                      "rango_80_siguiente_mes": f"{prox['li80_mxn_kg']:.1f}–{prox['ls80_mxn_kg']:.1f}" if prox is not None and "li80_mxn_kg" in prox else None})
    return pd.DataFrame(filas).sort_values("meses_historia", ascending=False) if filas else pd.DataFrame()


# --------------------------------------------------------------------------------------------------
# Ejecución
# --------------------------------------------------------------------------------------------------

def ejecutar(base: Path = BASE_DIR, corte: pd.Period | None = None) -> dict[str, Any]:
    gold = pd.read_csv(base / "data/oro/panel_mensual.csv")
    corte = corte or (pd.Period(date.today(), freq="M") - 1)
    m = mensual(gold, corte)
    siap_path = base / "data/oro/produccion_municipal_siap_colima.csv"
    siap = pd.read_csv(siap_path) if siap_path.is_file() else pd.DataFrame(columns=["Nomcultivo", "Nomunidad"])
    pron_path = base / "data/oro/pronosticos_colima.csv"
    pron = pd.read_csv(pron_path) if pron_path.is_file() else pd.DataFrame()
    dist = distancias_km(base / "data/publico/mercados_ciudad_sniim.geojson")
    productos = {
        "margen_productor": margen_productor(m, siap),
        "plazas_colima": comparar_plazas(m, dist),
        "calendario_venta": calendario_venta(m),
        "senales_mercado": senales(m, pron),
    }
    resumen: dict[str, Any] = {"esquema": "oaic-inteligencia/1", "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
                               "ultimo_mes_cerrado": str(corte), "plaza_referencia": _nombre(REFERENCIA), "archivos": {}}
    for nombre, df in productos.items():
        for carpeta in ("data/oro", "data/publico"):
            destino = base / carpeta / f"{nombre}.csv"
            destino.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(destino, index=False)
        resumen["archivos"][nombre] = {"filas": int(len(df)), "csv": f"data/publico/{nombre}.csv"}
    resumen["hallazgos"] = hallazgos(productos)
    (base / "data/publico/inteligencia.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return resumen | {"_productos": productos}


def hallazgos(p: dict[str, pd.DataFrame]) -> list[str]:
    out = []
    mg = p["margen_productor"]
    if not mg.empty:
        ref = mg[mg["mercado"].eq(REFERENCIA)]
        for _, r in ref.iterrows():
            out.append(f"{NOMBRE_CULTIVO.get(r['cultivo'], r['cultivo'])} {r['anio']}: el productor de Colima recibió en promedio {r['precio_productor_mxn_kg']:.2f} MXN/kg "
                       f"(SIAP) mientras el mayorista de origen Colima se cotizó en {r['precio_mayorista_mxn_kg']:.2f} MXN/kg en Guadalajara: "
                       f"el productor capta {r['participacion_productor_pct']:.0f} % del precio mayorista.")
    pl = p["plazas_colima"]
    if not pl.empty:
        sufic = pl[pl["evidencia"].eq("suficiente") & pl["diferencia_media_mxn_kg"].gt(0) & pl["confianza"].isin(["alta", "media"])] if "confianza" in pl else pl.iloc[0:0]
        for _cultivo, g in sufic.groupby("cultivo"):
            if "confianza" in g:
                g = g.assign(_o=g["confianza"].map({"alta": 0, "media": 1, "baja": 2})).sort_values(["_o", "diferencia_media_mxn_kg"], ascending=[True, False])
            r = g.iloc[0]
            conf = f" Confianza {r['confianza']} ({r['motivo_confianza']})." if "confianza" in r else ""
            out.append(f"{r['variante']}: {r['nombre_mercado']} pagó en promedio {r['diferencia_media_mxn_kg']:.2f} MXN/kg más que {r['plaza_referencia']} "
                       f"en {r['meses_pareados']} meses pareados ({r['pct_meses_plaza_mayor']:.0f} % de los meses). Conviene enviar ahí solo si el flete "
                       f"adicional cuesta menos de {r['flete_equilibrio_mxn_kg']:.2f} MXN/kg.{conf}")
    cal = p["calendario_venta"]
    if not cal.empty:
        for (cultivo, _mercado), g in cal[cal["mercado"].eq(REFERENCIA)].groupby(["cultivo", "mercado"]):
            alto, bajo = g.loc[g["indice_estacional"].idxmax()], g.loc[g["indice_estacional"].idxmin()]
            a_min, a_max = int(g["anios_observados"].min()), int(g["anios_observados"].max())
            anios = f"{a_max}" if a_min == a_max else f"{a_min} a {a_max}"
            conf = str(g["confianza_patron"].iloc[0]) if "confianza_patron" in g else "baja"
            prueba = (f"la prueba de Kruskal-Wallis no lo distingue del azar (p = {g['p_estacionalidad_kruskal'].iloc[0]:.2f}), así que es una pista, no una regla"
                      if conf == "baja" else f"patrón con confianza {conf} (p = {g['p_estacionalidad_kruskal'].iloc[0]:.3f})")
            out.append(f"{NOMBRE_CULTIVO.get(cultivo, cultivo)} en Guadalajara: el mes que más pagó en promedio fue {MESES_LARGOS[int(alto['mes']) - 1]} ({alto['lectura']}) "
                       f"y el que menos {MESES_LARGOS[int(bajo['mes']) - 1]} ({bajo['lectura']}), con {anios} años por mes; {prueba}.")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corte", help="último mes cerrado AAAA-MM (por defecto el mes anterior)")
    a = ap.parse_args(argv)
    r = ejecutar(corte=pd.Period(a.corte, freq="M") if a.corte else None)
    print(json.dumps({k: v for k, v in r.items() if not k.startswith("_")}, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
