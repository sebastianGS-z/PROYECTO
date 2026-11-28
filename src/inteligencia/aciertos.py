"""Historial de aciertos del pronóstico: ¿qué tanto ha acertado el observatorio?

    python main.py aciertos

1. **Validación mes a mes** (``validaciones_pronostico_colima.csv``): para el modelo elegido de cada serie, en cada
   mes de selección y holdout se compara el pronóstico a un mes con el precio real: error %, si el precio cayó en
   el rango de 80 % y si se acertó la dirección (sube / baja frente al mes anterior).
2. **Registro permanente** (``historial_pronosticos.csv``): cada corrida agrega sus pronósticos (una fila por
   serie, mes pronosticado y mes de emisión). Cuando llega el dato real se marca el resultado. Así el historial
   crece con pronósticos emitidos de verdad, no reconstruidos.

Salidas en ``data/publico/``: ``aciertos_pronostico.csv`` (detalle), ``aciertos_resumen.json`` y el registro.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config.settings import BASE_DIR
from src.tdl_e4.observatorio import _market_id, _mensual_colima

CLAVE_SERIE = ["variante_id", "mercado", "tipo_serie"]


def _clave(df: pd.DataFrame) -> pd.Series:
    return df["variante_id"].astype(float).astype(int).astype(str) + "|" + df["mercado"].map(_market_id) + "|" + df.get("tipo_serie", "origen_colima").astype(str)


def validacion(base: Path) -> pd.DataFrame:
    pron = pd.read_csv(base / "data/oro/pronosticos_colima.csv")
    val = pd.read_csv(base / "data/oro/validaciones_pronostico_colima.csv")
    if pron.empty or val.empty:
        return pd.DataFrame()
    pron["serie"], val["serie"] = _clave(pron), _clave(val)
    h1 = pron[pron["horizonte_meses"].eq(1)].drop_duplicates("serie")
    filas = []
    for _, p in h1.iterrows():
        v = val[val["serie"].eq(p["serie"]) & val["modelo"].eq(p["modelo_elegido"])].sort_values("mes_validacion")
        if v.empty:
            continue
        ancho = float(p["ls80_mxn_kg"]) - float(p["precio_frecuente_mxn_kg"])  # semiancho del rango a 1 mes
        previo = v["real_mxn_kg"].shift(1)
        for i, x in enumerate(v.itertuples()):
            prev = previo.iloc[i]
            filas.append({"serie": p["serie"], "variante": p["variante"], "plaza": p["nombre_mercado"], "modelo": p["modelo_elegido"],
                          "mes": x.mes_validacion, "segmento": x.segmento, "pronostico_mxn_kg": round(x.pronostico_mxn_kg, 2),
                          "real_mxn_kg": round(x.real_mxn_kg, 2), "error_pct": round((x.pronostico_mxn_kg / x.real_mxn_kg - 1) * 100, 1),
                          "dentro_rango_80": bool(abs(x.pronostico_mxn_kg - x.real_mxn_kg) <= ancho),
                          # Un mes sin cambio real no tiene dirección que acertar: se excluye en vez de contarlo como fallo.
                          "direccion_correcta": (bool(np.sign(x.pronostico_mxn_kg - prev) == np.sign(x.real_mxn_kg - prev))
                                                 if pd.notna(prev) and abs(x.real_mxn_kg - prev) > 0.005 * prev else None)})
    return pd.DataFrame(filas)


def registrar(base: Path) -> pd.DataFrame:
    """Agrega los pronósticos de esta corrida al registro permanente y marca los que ya tienen dato real."""
    pub = base / "data/publico"
    ruta = pub / "historial_pronosticos.csv"
    pron = pd.read_csv(base / "data/oro/pronosticos_colima.csv")
    reporte = json.loads((base / "data/oro/reporte_observatorio_e4.json").read_text(encoding="utf-8")) if (base / "data/oro/reporte_observatorio_e4.json").is_file() else {}
    emitido = str(reporte.get("ultimo_mes_cerrado_usado") or pd.Timestamp.today().to_period("M") - 1)
    nuevos = pron.assign(serie=_clave(pron), emitido_con_datos_hasta=emitido)[
        ["serie", "variante", "nombre_mercado", "emitido_con_datos_hasta", "fecha_pronostico", "horizonte_meses", "modelo_elegido",
         "precio_frecuente_mxn_kg", "li80_mxn_kg", "ls80_mxn_kg"]]
    hist = pd.read_csv(ruta) if ruta.is_file() else pd.DataFrame(columns=nuevos.columns)
    hist = pd.concat([hist, nuevos], ignore_index=True).drop_duplicates(["serie", "emitido_con_datos_hasta", "fecha_pronostico"], keep="first")
    # Dato real (mes cerrado) para los pronósticos cuyo mes ya pasó.
    gold = pd.read_csv(base / "data/oro/panel_mensual.csv")
    reales = {}
    for origen in ("Colima", None):
        m = _mensual_colima(gold, origen_objetivo=origen)
        m["mercado"] = m["mercado"].map(_market_id)
        if origen is None:
            m["_v"] = m["precio_frecuente_kg"] * m["n_observaciones"]
            m = m.groupby(["variante_id", "mercado", "mes"], as_index=False).agg(_v=("_v", "sum"), n=("n_observaciones", "sum"))
            m["precio_frecuente_kg"] = m["_v"] / m["n"]
        tipo = "origen_colima" if origen else "referencia_mercado"
        for _, r in m.iterrows():
            reales[(f"{int(float(r['variante_id']))}|{r['mercado']}|{tipo}", str(r["mes"]))] = float(r["precio_frecuente_kg"])
    cerrado = str(pd.Period(pd.Timestamp.today(), freq="M") - 1)
    hist["real_mxn_kg"] = [reales.get((s, f)) if f <= cerrado else None for s, f in zip(hist["serie"], hist["fecha_pronostico"].astype(str), strict=True)]
    hist["dentro_rango_80"] = [(None if pd.isna(r) else bool(li <= r <= ls)) for r, li, ls in zip(hist["real_mxn_kg"], hist["li80_mxn_kg"], hist["ls80_mxn_kg"], strict=True)]
    hist.to_csv(ruta, index=False)
    return hist


def resumen(val: pd.DataFrame, hist: pd.DataFrame) -> dict[str, Any]:
    por_serie = {}
    for serie, g in val.groupby("serie"):
        d = g["direccion_correcta"].dropna()
        por_serie[serie] = {"variante": g["variante"].iloc[0], "plaza": g["plaza"].iloc[0], "modelo": g["modelo"].iloc[0], "meses_evaluados": int(len(g)),
                            "error_medio_abs_pct": round(float(g["error_pct"].abs().mean()), 1),
                            "aciertos_rango_80_pct": round(float(g["dentro_rango_80"].mean() * 100), 0),
                            "aciertos_direccion_pct": round(float(d.mean() * 100), 0) if len(d) else None,
                            "desde": str(g["mes"].min()), "hasta": str(g["mes"].max())}
    evaluados = hist[hist["real_mxn_kg"].notna()] if not hist.empty else hist
    return {"esquema": "oaic-aciertos/1", "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
            "metodo": "Pronóstico a un mes fuera de muestra (walk-forward) del modelo elegido, comparado con el precio real del mes.",
            "advertencia": ("El ancho del rango de 80 % se calibró con estos mismos errores, así que su porcentaje de acierto aquí es optimista; "
                            "la cobertura real se mide con el registro permanente. El error y la dirección sí son fuera de muestra. "
                            "Los meses en que el precio no cambió (menos de 0.5 %) no cuentan para la dirección."),
            "por_serie": por_serie,
            "registro_permanente": {"pronosticos_emitidos": int(len(hist)), "ya_evaluados": int(len(evaluados)),
                                    "aciertos_rango_80_pct": round(float(evaluados["dentro_rango_80"].astype(bool).mean() * 100), 0) if len(evaluados) else None,
                                    "nota": "El registro empezó el 2026-11-27; se llena conforme llegan los meses pronosticados."}}


def ejecutar(base: Path = BASE_DIR) -> dict[str, Any]:
    val = validacion(base)
    pub = base / "data/publico"
    val.to_csv(pub / "aciertos_pronostico.csv", index=False)
    hist = registrar(base)
    res = resumen(val, hist)
    (pub / "aciertos_resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    r = ejecutar()
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ("variante", "aciertos_rango_80_pct", "aciertos_direccion_pct", "error_medio_abs_pct")}
                      for k, v in r["por_serie"].items()}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
