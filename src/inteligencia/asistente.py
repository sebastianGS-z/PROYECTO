"""Datos del asistente de venta "OAIC Vende" (chat privado en tablero/asistente.html).

    python main.py asistente

Escribe JSON compactos en ``data/publico/asistente/``:

* ``base.json``: frutas y sinónimos, municipios de Colima, centrales con coordenadas, distancias aproximadas
  municipio → central, alertas y fecha de corte;
* ``fruta_<clave>.json``: precio de hoy por central, señal frente a su historia, pronóstico con rango y
  confianza, las 17 respuestas del productor, comparación de centrales, temporada y exportación;
* ``compradores.json``: directorio de **empresas** compradoras de fruta del DENUE (INEGI), solo con datos que el
  propio DENUE publica, sin personas físicas pequeñas sin razón social, y marcadas "sin verificar".

El asistente funciona sin servidor ni modelo de IA: todo número que muestra sale de estos archivos.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import BASE_DIR
from src.inteligencia.catalogo import FRUTAS, fruta_de

SALIDA = "data/publico/asistente"
FACTOR_CARRETERA = 1.3  # distancia en línea recta × 1.3 ≈ por carretera (aproximación declarada)

# Actividades SCIAN que compran fruta fresca. Para mayoreo de abarrotes y supermercados solo
# establecimientos grandes (51+ personas), que son los que compran por volumen.
CATEGORIAS = {
    "431130": ("mayorista", "Mayorista de frutas y verduras"),
    "115113": ("empacadora", "Empacadora / beneficio de productos agrícolas"),
    "311411": ("procesadora", "Congeladora de frutas y verduras"),
    "311421": ("procesadora", "Deshidratadora de frutas y verduras"),
    "311422": ("procesadora", "Conservas de frutas y verduras"),
    "493120": ("frio", "Almacén con refrigeración"),
    "431110": ("abarrotes", "Mayorista de abarrotes (grande)"),
    "462111": ("supermercado", "Supermercado / tienda de autoservicio (grande)"),
    "461130": ("fruteria", "Frutería con 6 o más empleados"),
}
GRANDES = ("51 a 100", "101 a 250", "251 y más")
SINONIMOS = {
    "limon": ["limon", "limón", "limones", "lima", "limon mexicano", "limon colima", "limon con semilla"],
    "papaya": ["papaya", "papayas", "maradol"],
    "platano": ["platano", "plátano", "platanos", "banana", "banano", "guineo", "macho", "dominico"],
    "mango": ["mango", "mangos", "ataulfo", "manila", "tommy", "haden"],
    "coco": ["coco", "cocos", "coco de agua"],
    "tamarindo": ["tamarindo", "tamarindos"],
    "guayaba": ["guayaba", "guayabas"],
    "aguacate": ["aguacate", "aguacates", "hass", "palta"],
    "sandia": ["sandia", "sandía", "sandias", "patilla"],
    "guanabana": ["guanabana", "guanábana", "guanabanas"],
}


def _leer(base: Path, rel: str) -> pd.DataFrame:
    p = base / rel
    return pd.read_csv(p) if p.is_file() else pd.DataFrame()


def _json(base: Path, rel: str) -> dict[str, Any]:
    p = base / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = math.radians
    a = math.sin(r(lat2 - lat1) / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def _centroide(geom: dict[str, Any]) -> tuple[float, float]:
    """Centro del polígono continental más grande (las islas Revillagigedo desplazarían el promedio cientos de km)."""
    poligonos = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    anillos = [pol[0] for pol in poligonos if pol and pol[0]]
    continentales = [a for a in anillos if sum(p[0] for p in a) / len(a) > -105.5] or anillos
    pts = max(continentales, key=len)
    return (sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts))


def _sin_acentos(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)).casefold()


def _f(x: Any, d: int = 2) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else round(v, d)


def _txt(x: Any) -> str | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) or not str(x).strip() else str(x).strip()


def _estado(t: Any) -> str:
    e = str(t).strip().title().replace(" De ", " de ")
    return {"Michoacán de Ocampo": "Michoacán"}.get(e, e)


def _telefono(t: Any) -> str | None:
    dig = re.sub(r"\D", "", str(t or ""))
    if dig.startswith("52") and len(dig) == 12:
        dig = dig[2:]
    return dig if len(dig) == 10 else None


def base_json(base: Path) -> dict[str, Any]:
    cen = _json(base, "data/publico/geo/centrales.geojson").get("features", [])
    mun = _json(base, "data/publico/geo/municipios_colima.geojson").get("features", [])
    centrales = [{"id": str(f["properties"]["mercado_id"]), "nombre": f["properties"]["mercado"], "ciudad": f["properties"]["ciudad"],
                  "estado": f["properties"]["estado"], "lat": round(f["geometry"]["coordinates"][1], 4),
                  "lon": round(f["geometry"]["coordinates"][0], 4)} for f in cen]
    municipios = []
    for f in mun:
        lat, lon = _centroide(f["geometry"])
        municipios.append({"nombre": f["properties"]["nomgeo"], "clave": _sin_acentos(f["properties"]["nomgeo"]), "lat": round(lat, 4), "lon": round(lon, 4),
                           "km": {c["id"]: round(_km(lat, lon, c["lat"], c["lon"]) * FACTOR_CARRETERA) for c in centrales}})
    alertas = _json(base, "data/publico/alertas.json")
    return {"esquema": "oaic-asistente/1", "corte": _json(base, "data/publico/preguntas_productor.json").get("corte"),
            "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
            "frutas": [{"clave": k, "nombre": v["nombre"], "articulo": v["articulo"], "sinonimos": SINONIMOS.get(k, [k])} for k, v in FRUTAS.items()],
            "municipios": municipios, "centrales": centrales,
            "nota_distancias": f"Distancia en línea recta × {FACTOR_CARRETERA}: aproximación a la distancia por carretera.",
            "alertas": alertas.get("alertas", [])}


def _precios_hoy(base: Path, clave: str) -> list[dict[str, Any]]:
    p = _leer(base, "data/publico/precios_sniim_actuales.csv")
    if p.empty:
        return []
    nombre = _sin_acentos(FRUTAS[clave]["sniim"])
    p = p[p["producto"].map(lambda x: _sin_acentos(str(x)).startswith(nombre))]
    col = "precio_frecuente_presentacion" if clave == "coco" else "precio_frecuente_mxn_kg"
    p = p[p[col].notna()]
    filas = []
    for (mid, mer, var), g in p.groupby(["mercado_id", "mercado", "variante"]):
        filas.append({"central": str(mid), "nombre": mer, "variante": var, "precio": _f(g[col].median()),
                      "unidad": "MXN/pieza" if clave == "coco" else "MXN/kg", "fecha": str(g["fecha"].max()),
                      "origenes": sorted({str(o) for o in g["origen"].dropna()})[:4]})
    return sorted(filas, key=lambda x: -(x["precio"] or 0))


def fruta_json(base: Path, clave: str, cal: pd.DataFrame, sen: pd.DataFrame, pron: pd.DataFrame, plazas: pd.DataFrame,
               preg: dict[str, Any], export: dict[str, Any], aciertos: dict[str, Any], demanda: dict[str, Any],
               margen: pd.DataFrame | None = None) -> dict[str, Any]:
    es = lambda df: df[df["cultivo"].map(fruta_de).eq(clave)] if df is not None and not df.empty and "cultivo" in df else pd.DataFrame()  # noqa: E731
    s = es(sen)
    p = es(pron)
    pl = es(plazas)
    c = es(cal)
    if not c.empty:  # temporada de la central de referencia (Guadalajara) si existe; si no, la de más historia
        ref = c[c["mercado"].astype(str).eq("140")]
        c = ref if not ref.empty else c[c["mercado"].eq(c.groupby("mercado")["anios_observados"].sum().idxmax())]
    serie_ac = {}
    for k, v in aciertos.get("por_serie", {}).items():
        serie_ac[k] = v
    pronos = []
    for _, r in (p.sort_values("horizonte_meses") if not p.empty else p).iterrows():
        k = f"{int(float(r['variante_id']))}|{r['mercado']}|{r.get('tipo_serie', 'origen_colima')}"
        pronos.append({"mes": str(r["fecha_pronostico"]), "horizonte": int(r["horizonte_meses"]), "variante": r["variante"], "central": r["nombre_mercado"],
                       "tipo": r.get("tipo_serie"), "precio": _f(r["precio_frecuente_mxn_kg"]), "min80": _f(r["li80_mxn_kg"]), "max80": _f(r["ls80_mxn_kg"]),
                       "error_pct": _f(r.get("mape_backtest_pct"), 1), "modelo": r.get("modelo_elegido"),
                       "aciertos_rango_pct": (serie_ac.get(k) or {}).get("aciertos_rango_80_pct"),
                       "aciertos_direccion_pct": (serie_ac.get(k) or {}).get("aciertos_direccion_pct")})
    return {
        "clave": clave, "nombre": FRUTAS[clave]["nombre"], "corte": preg.get("corte"),
        "hoy": _precios_hoy(base, clave),
        "senales": [{"variante": r["variante"], "central": r["nombre_mercado"], "base": r.get("base"), "mes": r["ultimo_mes"], "precio": _f(r["ultimo_precio_mxn_kg"]),
                     "percentil": _f(r["percentil_historico"], 0), "meses": int(r["meses_historia"]), "lectura": r["lectura"]} for _, r in s.iterrows()],
        "pronostico": pronos,
        "centrales": [{"central": r["nombre_mercado"], "id": str(r["mercado"]), "variante": r["variante"], "referencia": r["plaza_referencia"],
                       "precio": _f(r["precio_plaza_mxn_kg"]), "precio_ref": _f(r["precio_referencia_mxn_kg"]), "diferencia": _f(r["diferencia_media_mxn_kg"]),
                       "meses": int(r["meses_pareados"]), "flete_equilibrio": _f(r["flete_equilibrio_mxn_kg"]), "confianza": r["confianza"],
                       "confianza_pct": int(r["confianza_pct"]), "hasta": r["hasta"]} for _, r in pl.iterrows()],
        "temporada": [{"mes": int(r["mes"]), "indice": _f(r["indice_estacional"], 3), "confianza": r.get("confianza_patron"),
                       "confianza_pct": _f(r.get("confianza_pct"), 0), "central": r["nombre_mercado"]}
                      for _, r in c.groupby("mes", as_index=False).first().iterrows()] if not c.empty else [],
        "respuestas": preg.get("respuestas", {}).get(clave, []),
        "exportacion": export.get("frutas", {}).get(clave, {}),
        "demanda": demanda,
        # Lo que llega al productor (SIAP, precio medio rural) frente al mayoreo: base del precio sugerido "en huerta".
        "margen": [{"anio": int(r["anio"]), "central": r["nombre_mercado"], "productor": _f(r["precio_productor_mxn_kg"]),
                    "mayorista": _f(r["precio_mayorista_mxn_kg"]), "participacion_pct": _f(r["participacion_productor_pct"], 1)}
                   for _, r in es(margen).iterrows()] if margen is not None and not margen.empty else [],
    }


def compradores(base: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Directorio de empresas compradoras de fruta (DENUE) y conteo por estado y categoría (señal de demanda)."""
    from scripts.capturar_denue import zips

    lista: list[dict[str, Any]] = []
    conteo: dict[str, dict[str, int]] = {}
    corte = None
    for _clave_estado, ruta in sorted(zips(base / "data/bronce").items()):
        z = zipfile.ZipFile(ruta)
        meta = Path(str(ruta) + ".meta.json")
        fecha = json.loads(meta.read_text(encoding="utf-8")).get("fecha_captura", "")[:10] if meta.is_file() else ""
        for n in (x for x in z.namelist() if x.startswith("conjunto_de_datos") and x.endswith(".csv")):
            df = pd.read_csv(z.open(n), encoding="latin-1", dtype=str, low_memory=False)
            df = df[df["CODIGO_ACT"].isin(CATEGORIAS)]
            grande = df["PER_OCU"].fillna("").str.startswith(GRANDES)
            no_micro = ~df["PER_OCU"].fillna("0 a 5").str.startswith("0 a 5")
            df = df[~df["CODIGO_ACT"].isin(["431110", "462111"]) | grande]
            df = df[~df["CODIGO_ACT"].eq("461130") | no_micro.loc[df.index]]
            # Privacidad: un establecimiento muy pequeño sin razón social puede ser una persona física.
            df = df[df["RAZ_SOCIAL"].notna() | no_micro.loc[df.index]]
            for _, r in df.iterrows():
                cat, desc = CATEGORIAS[r["CODIGO_ACT"]]
                estado = _estado(r["ENTIDAD"])
                conteo.setdefault(estado, {}).setdefault(cat, 0)
                conteo[estado][cat] += 1
                tel, correo, www = _telefono(r.get("TELEFONO")), (_txt(r.get("CORREOELEC")) or "").lower() or None, (_txt(r.get("WWW")) or "").lower() or None
                if not (tel or correo or www):
                    continue
                central = (_txt(r.get("TIPOCENCOM")) or "").upper() == "CENTRAL DE ABASTO"
                lista.append({"id": r["CLEE"], "nombre": str(r["NOM_ESTAB"]).strip().title(), "razon": _txt(r["RAZ_SOCIAL"]),
                              "cat": cat, "actividad": desc, "personal": r["PER_OCU"], "estado": estado,
                              "municipio": str(r["MUNICIPIO"]).strip().title(), "central": central,
                              "lugar": (_txt(r.get("NOM_CENCOM")) or "").title() or None,
                              "tel": tel, "correo": correo, "www": www, "lat": _f(r["LATITUD"], 4), "lon": _f(r["LONGITUD"], 4)})
            corte = corte or (str(df["FECHA_ALTA"].dropna().max()) if "FECHA_ALTA" in df and len(df) else None)
        corte = fecha or corte
    return lista, {"por_estado": conteo, "fecha_descarga": corte}


def ejecutar(base: Path = BASE_DIR) -> dict[str, Any]:
    out = base / SALIDA
    out.mkdir(parents=True, exist_ok=True)
    b = base_json(base)
    lista, demanda = compradores(base)
    previo = _json(base, f"{SALIDA}/compradores.json")
    if not lista and previo.get("empresas"):
        # Los ZIP del DENUE no se versionan (pesan decenas de MB): sin ellos (p. ej. en GitHub Actions) se conserva
        # el directorio ya publicado en vez de borrarlo.
        lista, demanda = previo["empresas"], {"por_estado": previo.get("por_estado", {}), "fecha_descarga": previo.get("fecha_descarga")}
    preg = _json(base, "data/publico/preguntas_productor.json")
    export = _json(base, "data/publico/exportacion_resumen.json")
    aciertos = _json(base, "data/publico/aciertos_resumen.json")
    cal, sen = _leer(base, "data/publico/calendario_venta.csv"), _leer(base, "data/publico/senales_mercado.csv")
    pron, plazas = _leer(base, "data/publico/pronosticos_colima.csv"), _leer(base, "data/publico/plazas_colima.csv")
    margen = _leer(base, "data/publico/margen_productor.csv")
    b["directorio"] = {"empresas": len(lista), "fecha_descarga": demanda["fecha_descarga"],
                       "fuente": "DENUE, INEGI (descarga masiva oficial). Datos públicos declarados por cada establecimiento; sin verificar por el observatorio."}
    escribir = lambda nombre, obj: (out / nombre).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")  # noqa: E731
    escribir("base.json", b)
    for k in FRUTAS:
        escribir(f"fruta_{k}.json", fruta_json(base, k, cal, sen, pron, plazas, preg, export, aciertos, demanda["por_estado"], margen))
    escribir("compradores.json", {"fuente": b["directorio"]["fuente"], "fecha_descarga": demanda["fecha_descarga"], "por_estado": demanda["por_estado"],
                                  "categorias": {k: v[1] for k, v in CATEGORIAS.items()}, "empresas": lista})
    return {"frutas": len(FRUTAS), "centrales": len(b["centrales"]), "municipios": len(b["municipios"]), "compradores": len(lista),
            "con_telefono": sum(1 for x in lista if x["tel"]), "kb": {p.name: round(p.stat().st_size / 1024) for p in sorted(out.glob("*.json"))}}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print(json.dumps(ejecutar(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
