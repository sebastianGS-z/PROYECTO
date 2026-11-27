"""Mercados extranjeros: ¿a qué países se podría exportar cada fruta y cuánto pagan?

    python main.py exportacion

Lee todas las capturas de UN Comtrade en Bronce (varios años y tipos de consulta) y el tipo de cambio
USD/MXN anual, y escribe:

* ``data/publico/exportacion_destinos.csv`` — por fruta, país y año: importaciones desde México (USD, kg,
  USD/kg, MXN/kg), importaciones totales del mundo y participación de México en ese mercado.
* ``data/publico/exportacion_resumen.json`` — por fruta: principales destinos actuales, crecimiento,
  **oportunidades** (países que importan mucho del mundo y poco de México) y **prima de exportación**
  (valor aduanal en MXN/kg frente al precio mayorista nacional de origen Colima).

Límites que se declaran en cada salida: valores aduanales (no precio al productor), códigos HS que agrupan
frutas, y previsualización del API limitada a 500 filas por consulta.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import BASE_DIR
from src.inteligencia.catalogo import FRUTAS

# UN Comtrade usa algunos códigos propios distintos del ISO 3166 numérico (que usa el mapa mundial).
M49_A_ISO = {842: 840, 251: 250, 699: 356, 757: 756, 579: 578, 490: 158, 711: 710, 381: 380}
EXCLUIR = {0, 97, 899, 839, 838, 490}  # mundo, UE como bloque, áreas no especificadas


def _paises(bronze: Path) -> dict[int, str]:
    rutas = [p for p in (bronze / "un_comtrade").rglob("*lista-paises-reportantes*.json") if not p.name.endswith(".meta.json")]
    if not rutas:
        return {}
    data = json.loads(max(rutas, key=lambda p: p.name).read_text(encoding="utf-8"))
    return {int(r["id"]): r.get("text") for r in data.get("results", []) if str(r.get("id", "")).isdigit()}


def tipo_cambio(bronze: Path) -> dict[int, float]:
    out = {}
    for meta in (bronze / "tipo_cambio").rglob("*.meta.json"):
        md = json.loads(meta.read_text(encoding="utf-8"))["metadatos_captura"]
        datos = json.loads(meta.with_name(meta.name.removesuffix(".meta.json")).read_text(encoding="utf-8"))
        tasas = [v["MXN"] for v in datos.get("rates", {}).values() if "MXN" in v]
        if tasas:
            out[int(md["periodo"])] = round(sum(tasas) / len(tasas), 4)
    return out


def registros(bronze: Path) -> pd.DataFrame:
    """Una fila por (código HS, tipo, año, país) desde la captura más reciente de cada consulta."""
    ultimas: dict[str, tuple[str, Path, dict]] = {}
    for meta in (bronze / "un_comtrade").rglob("*.meta.json"):
        md = json.loads(meta.read_text(encoding="utf-8"))["metadatos_captura"]
        tipo, codigo = md.get("tipo_consulta"), str(md.get("codigo_hs", ""))
        if tipo not in {"destinos_mexico", "importadores_mundo", "exportadores"} or not codigo:
            continue
        anio = int(md.get("periodo") or str(md.get("fecha_ref_inicio", "0000"))[:4])
        clave = f"{tipo}|{codigo}|{anio}"
        run = meta.name.rsplit("__", 1)[-1]
        if clave not in ultimas or run > ultimas[clave][0]:
            ultimas[clave] = (run, meta.with_name(meta.name.removesuffix(".meta.json")), md)
    filas = []
    for clave, (_, ruta, md) in ultimas.items():
        tipo, codigo, anio = clave.split("|")
        for r in json.loads(ruta.read_text(encoding="utf-8")).get("data", []):
            filas.append({"tipo": tipo, "codigo_hs": codigo, "anio": int(r.get("refYear") or anio), "reporter": int(r.get("reporterCode") or 0),
                          "partner": int(r.get("partnerCode") or 0), "valor_usd": float(r.get("primaryValue") or 0),
                          "kg": float(r.get("netWgt") or 0), "archivo_bronce": ruta.relative_to(BASE_DIR).as_posix() if ruta.is_relative_to(BASE_DIR) else str(ruta),
                          "truncamiento_posible": bool(md.get("truncamiento_posible"))})
    return pd.DataFrame(filas)


def destinos(reg: pd.DataFrame, paises: dict[int, str], fx: dict[int, float]) -> pd.DataFrame:
    if reg.empty:
        return pd.DataFrame()
    mx = reg[reg["tipo"].eq("destinos_mexico") & ~reg["reporter"].isin(EXCLUIR)]
    mx = mx.groupby(["codigo_hs", "anio", "reporter"], as_index=False)[["valor_usd", "kg"]].sum()
    mundo = reg[reg["tipo"].eq("importadores_mundo") & ~reg["reporter"].isin(EXCLUIR)]
    mundo = mundo.groupby(["codigo_hs", "anio", "reporter"], as_index=False)[["valor_usd", "kg"]].sum().rename(columns={"valor_usd": "mundo_usd", "kg": "mundo_kg"})
    df = mundo.merge(mx, on=["codigo_hs", "anio", "reporter"], how="outer").fillna({"valor_usd": 0, "kg": 0})
    df["pais"] = df["reporter"].map(lambda c: paises.get(int(c), f"Área {int(c)}"))
    df["iso_numerico"] = df["reporter"].map(lambda c: M49_A_ISO.get(int(c), int(c)))
    df["usd_kg_desde_mexico"] = (df["valor_usd"] / df["kg"]).where(df["kg"] > 0)
    df["usd_kg_mundo"] = (df["mundo_usd"] / df["mundo_kg"]).where(df["mundo_kg"] > 0)
    df["tipo_cambio_usd_mxn"] = df["anio"].map(fx)
    df["mxn_kg_desde_mexico"] = df["usd_kg_desde_mexico"] * df["tipo_cambio_usd_mxn"]
    df["participacion_mexico_pct"] = (df["valor_usd"] / df["mundo_usd"] * 100).where(df["mundo_usd"] > 0)
    return df.sort_values(["codigo_hs", "anio", "valor_usd"], ascending=[True, True, False])


def _precio_nacional(base: Path, claves: list[str]) -> tuple[float | None, str]:
    p = base / "data/oro/panel_mensual.csv"
    if not p.is_file():
        return None, ""
    g = pd.read_csv(p, usecols=["cultivo", "origen", "fecha_mes", "precio_frecuente_kg_mean", "precio_frecuente_kg_count"])
    g = g[g["cultivo"].isin(claves) & g["precio_frecuente_kg_mean"].notna()]
    col = g[g["origen"].eq("Colima")]
    g = col if not col.empty else g
    if g.empty:
        return None, ""
    g["fecha_mes"] = pd.to_datetime(g["fecha_mes"])
    g = g[g["fecha_mes"] >= g["fecha_mes"].max() - pd.DateOffset(months=11)]
    w = g["precio_frecuente_kg_count"].clip(lower=1)
    return float((g["precio_frecuente_kg_mean"] * w).sum() / w.sum()), ("origen Colima" if not col.empty else "todos los orígenes")


def resumen(base: Path, df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for fruta, cfg in FRUTAS.items():
        hs = cfg.get("hs")
        if not hs or df.empty or hs not in set(df["codigo_hs"]):
            out[fruta] = {"nombre": cfg["nombre"], "hs": hs, "disponible": False, "nota": cfg["hs_nota"] or "Sin datos de UN Comtrade capturados para este código."}
            continue
        d = df[df["codigo_hs"].eq(hs)]
        anios_mx = sorted(d.loc[d["valor_usd"] > 0, "anio"].unique())
        if not anios_mx:
            out[fruta] = {"nombre": cfg["nombre"], "hs": hs, "disponible": False, "nota": "Ningún país reporta importaciones desde México para este código en los años capturados."}
            continue
        ult, pri = int(anios_mx[-1]), int(anios_mx[0])
        a = d[d["anio"].eq(ult)]
        total_mx = float(a["valor_usd"].sum())
        top = a[a["valor_usd"] > 0].sort_values("valor_usd", ascending=False).head(8)
        previo = d[d["anio"].eq(pri)].set_index("reporter")["valor_usd"]
        destinos_ = [{"pais": r["pais"], "iso": int(r["iso_numerico"]), "valor_usd": round(r["valor_usd"]), "toneladas": round(r["kg"] / 1000),
                      "usd_kg": _r(r["usd_kg_desde_mexico"]), "mxn_kg": _r(r["mxn_kg_desde_mexico"]), "participacion_mexico_pct": _r(r["participacion_mexico_pct"], 1),
                      "share_de_exportaciones_mx_pct": round(r["valor_usd"] / total_mx * 100, 1) if total_mx else None,
                      "crecimiento_pct": _r((r["valor_usd"] / previo.get(r["reporter"]) - 1) * 100, 0) if previo.get(r["reporter"]) else None}
                     for _, r in top.iterrows()]
        con_mundo = a[a["mundo_usd"].notna() & (a["mundo_usd"] > 0)]
        umbral = con_mundo["mundo_usd"].quantile(0.75) if len(con_mundo) >= 8 else 0
        opp = con_mundo[(con_mundo["mundo_usd"] >= umbral) & (con_mundo["participacion_mexico_pct"].fillna(0) < 10)].sort_values("mundo_usd", ascending=False).head(8)
        oportunidades = [{"pais": r["pais"], "iso": int(r["iso_numerico"]), "importa_del_mundo_usd": round(r["mundo_usd"]),
                          "usd_kg_mundo": _r(r["usd_kg_mundo"]), "mxn_kg_mundo": _r(r["usd_kg_mundo"] * r["tipo_cambio_usd_mxn"]) if pd.notna(r["tipo_cambio_usd_mxn"]) else None,
                          "participacion_mexico_pct": _r(r["participacion_mexico_pct"], 1) or 0.0} for _, r in opp.iterrows()]
        nacional, base_nac = _precio_nacional(base, cfg["claves"])
        valor_exp = (a["valor_usd"].sum() / a["kg"].sum()) if a["kg"].sum() > 0 else None
        fx = a["tipo_cambio_usd_mxn"].dropna()
        exp_mxn = valor_exp * float(fx.iloc[0]) if valor_exp and len(fx) else None
        out[fruta] = {"nombre": cfg["nombre"], "hs": hs, "hs_nota": cfg["hs_nota"], "disponible": True, "anio": ult, "anio_base_crecimiento": pri,
                      "exportaciones_mexico_usd": round(total_mx), "paises_destino": int((a["valor_usd"] > 0).sum()),
                      "valor_unitario_exportacion_usd_kg": _r(valor_exp), "valor_unitario_exportacion_mxn_kg": _r(exp_mxn),
                      "tipo_cambio_usd_mxn": float(fx.iloc[0]) if len(fx) else None,
                      "precio_mayorista_nacional_mxn_kg": _r(nacional), "base_precio_nacional": base_nac,
                      "prima_exportacion_pct": _r((exp_mxn / nacional - 1) * 100, 0) if exp_mxn and nacional else None,
                      "destinos": destinos_, "oportunidades": oportunidades,
                      "serie_exportaciones": {int(k): round(v) for k, v in d.groupby("anio")["valor_usd"].sum().items()},
                      "limites": ["Valores aduanales declarados por los países importadores; no son precio al productor ni precio de venta final.",
                                  cfg["hs_nota"] or "El código HS corresponde a la fruta.", "Exportar requiere certificación fitosanitaria, empaque, logística en frío y un comprador confirmado."]}
    return out


def _r(v: Any, nd: int = 2) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) or math.isinf(x) else round(x, nd)


def ejecutar(base: Path = BASE_DIR) -> dict[str, Any]:
    bronze = base / "data/bronce"
    reg = registros(bronze)
    df = destinos(reg, _paises(bronze), tipo_cambio(bronze))
    pub = base / "data/publico"
    pub.mkdir(parents=True, exist_ok=True)
    df.to_csv(pub / "exportacion_destinos.csv", index=False)
    res = resumen(base, df)
    meta = {"esquema": "oaic-exportacion/1", "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
            "fuente": "UN Comtrade (API pública) · tipo de cambio BCE vía Frankfurter", "anios": sorted(int(a) for a in df["anio"].unique()) if not df.empty else [],
            "consultas_con_posible_truncamiento": int(reg["truncamiento_posible"].sum()) if not reg.empty else 0, "frutas": res}
    (pub / "exportacion_resumen.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return {f: v.get("disponible") for f, v in res.items()}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print(json.dumps(ejecutar(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
