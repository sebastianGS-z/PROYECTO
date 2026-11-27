"""Captura referencias de comercio mundial de frutas con UN Comtrade.

La unidad USD/kg es valor unitario aduanal (valor comercial / peso neto), no
precio de anaquel ni cotización de un comprador. La API pública limita previews
a 500 filas por consulta; cualquier respuesta truncada se señala explícitamente.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from almacenamiento.bronze_writer import BronzeWriter
from almacenamiento.manifest import new_run_id
from config.settings import get_settings
from extractores.base import RawCapture

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
REPORTERS = "https://comtradeapi.un.org/files/v1/app/reference/Reporters.json"
FRUITS = {
    "080440": ("Aguacate", "aguacate"),
    "080450": ("Guayaba, mango y mangostán (grupo HS)", "mango_guayaba"),
    "080550": ("Limones y limas (grupo HS)", "limon"),
    "080119": ("Cocos frescos (grupo HS)", "coco"),
    "080720": ("Papaya", "papaya"),
    "080390": ("Plátanos (grupo HS)", "platano"),
    "081340": ("Tamarindo y otras frutas secas (grupo HS)", "tamarindo"),
    "080711": ("Sandías", "sandia"),
}


def _capture(writer: BronzeWriter, code: str, kind: str, session: requests.Session, run: str,
             headers: dict) -> tuple[dict, Path]:
    params = {"period": "2024", "cmdCode": code, "flowCode": "X", "maxRecords": 500}
    params["partnerCode"] = "0" if kind == "exportadores" else "484"
    if kind == "destinos_mexico":
        params["flowCode"] = "M"
    response = session.get(BASE, params=params, headers=headers, timeout=(15, 90))
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    count = int(payload.get("count", len(payload.get("data", []))))
    now = datetime.now(timezone.utc).date().isoformat()
    cap = RawCapture("un_comtrade", response.url, response.content, "json", response.status_code,
                     count, "ok" if count else "sin_resultados", metadatos={
        "etiqueta": f"{kind}-{code}-2024", "fecha_ref_inicio": "2024-01-01", "fecha_ref_fin": "2024-12-31",
        "codigo_hs": code, "tipo_consulta": kind, "periodo": 2024, "limite_preview": 500,
        "truncamiento_posible": count >= 500, "fecha_captura_utc": now,
        "nota": "Datos aduanales de comercio de mercancías; no equivalen a cotizaciones mayoristas/minoristas ni a oportunidad rentable."})
    saved = writer.write(cap, run)
    return payload, saved.ruta


def capturar(periodo: int = 2024) -> dict:
    if periodo != 2024:
        raise ValueError("Esta versión del producto mantiene el corte anual comparable 2024")
    settings = get_settings()
    writer = BronzeWriter(settings.bronze_dir)
    run = new_run_id()
    session = requests.Session()
    headers = {"Accept": "application/json", "User-Agent": settings.user_agent}
    reporter_response = session.get(REPORTERS, headers=headers, timeout=(15, 60))
    reporter_response.raise_for_status()
    reporter_payload = reporter_response.content
    ref_cap = RawCapture("un_comtrade", REPORTERS, reporter_payload, "json", reporter_response.status_code,
        len(reporter_payload), "ok", metadatos={"etiqueta":"lista-paises-reportantes",
        "fecha_ref_inicio":datetime.now(timezone.utc).date().isoformat(),
        "fecha_ref_fin":datetime.now(timezone.utc).date().isoformat(),
        "nota":"Códigos oficiales de reporter countries/areas de UN Comtrade."})
    writer.write(ref_cap, run)
    # UN Comtrade documents a 500-row public-preview cap; wait between requests.
    rows, sources, queries = [], [], []
    halt_on_quota = False
    for index, code in enumerate(FRUITS):
        for kind in ("exportadores", "destinos_mexico"):
            if halt_on_quota:
                break
            if index or kind == "destinos_mexico":
                time.sleep(1.5)
            try:
                payload, path = _capture(writer, code, kind, session, run, headers)
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 429:
                    queries.append({"codigo_hs": code, "consulta": kind, "filas": 0,
                                    "truncamiento_posible": False,
                                    "error": "limite_api_429; reintentar en siguiente corrida, no se fuerza la cuota"})
                    halt_on_quota = True
                    break
                raise
            sources.append(path)
            queries.append({"codigo_hs": code, "consulta": kind, "filas": int(payload.get("count", 0)),
                            "truncamiento_posible": int(payload.get("count", 0)) >= 500,
                            "error": payload.get("error", "")})
            for record in payload.get("data", []):
                net = float(record.get("netWgt") or 0)
                value = float(record.get("primaryValue") or 0)
                rows.append({"fruta": FRUITS[code][0], "grupo_fruta": FRUITS[code][1], "codigo_hs": code,
                             "anio": int(record.get("refYear", 2024)), "tipo_consulta": kind,
                             "reporter_code_m49": int(record.get("reporterCode", 0)),
                             "partner_code_m49": int(record.get("partnerCode", 0)),
                             "valor_comercio_usd": value, "peso_neto_kg": net,
                             "valor_unitario_aduanal_usd_kg": value / net if net > 0 else None,
                             "qty": record.get("qty"), "qty_unit_code": record.get("qtyUnitCode"),
                             "estimacion_peso": bool(record.get("isNetWgtEstimated", False)),
                             "valor_reportado": bool(record.get("isReported", False)),
                             "sha256_payload": None})
    country_data = json.loads(reporter_payload)
    country_rows = country_data.get("results", country_data if isinstance(country_data, list) else [])
    countries = {int(r.get("id")): (r.get("text") or r.get("textShort") or str(r.get("id")))
                 for r in country_rows if str(r.get("id", "")).isdigit()}
    for row in rows:
        row["pais_reportante"] = countries.get(row["reporter_code_m49"], f"Área {row['reporter_code_m49']}")
        row["socio_comercial"] = countries.get(row["partner_code_m49"], "Mundo" if row["partner_code_m49"] == 0 else f"Área {row['partner_code_m49']}")
        row["sha256_payload"] = next((p.with_suffix(p.suffix + ".meta.json").exists() and
                                      json.loads(p.with_suffix(p.suffix + ".meta.json").read_text()).get("metadatos_captura",{}).get("sha256")
                                      for p in sources if p.name.find(row["codigo_hs"]) >= 0), None)
    result = pd.DataFrame(rows)
    public = ROOT / "data/publico"; oro = ROOT / "data/oro"
    public.mkdir(exist_ok=True, parents=True); oro.mkdir(exist_ok=True, parents=True)
    result.to_csv(oro / "comercio_fruticola_mundial.csv", index=False, encoding="utf-8")
    result.to_csv(public / "comercio_fruticola_mundial.csv", index=False, encoding="utf-8")
    report = {"fuente":"UN Comtrade API pública", "anio":2024, "filas":len(result),
              "codigos_hs":FRUITS, "consultas":queries,
              "capturas_bronce":[p.resolve().relative_to(ROOT).as_posix() for p in sources],
              "metodo":"USD/kg = valor comercial declarado / peso neto declarado cuando peso > 0",
              "limitaciones":["Los códigos HS agrupan productos y calidades; no equivalen siempre a una fruta/variedad exacta.",
                  "USD/kg es valor unitario de comercio exterior, no precio de venta local, minorista o de compra al productor.",
                  "La API pública limita previews a 500 filas; respuestas con 500 filas pueden estar truncadas.",
                  "Importaciones que declaran México como socio identifican flujos comerciales, no demanda disponible ni compradores confirmados.",
                  "No se incorpora tipo de cambio de conversión; valores se conservan en USD."]}
    (public / "reporte_comercio_mundial.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def procesar_bronce() -> dict:
    """Regenera salidas desde las capturas inmutables ya disponibles."""
    root = get_settings().bronze_dir / "un_comtrade"
    countries_path = [p for p in root.rglob("*lista-paises-reportantes*.json")
                      if not p.name.endswith(".meta.json")]
    if not countries_path:
        raise FileNotFoundError("Falta la tabla de referencia de países de UN Comtrade en Bronce")
    refs = json.loads(max(countries_path, key=lambda p: p.stat().st_mtime_ns).read_text(encoding="utf-8"))
    country_rows = refs.get("results", [])
    countries = {int(r.get("id")): r.get("text") for r in country_rows if str(r.get("id", "")).isdigit()}
    rows, queries, sources = [], [], []
    latest = {}
    for path in root.rglob("*.json"):
        if path.name.endswith(".meta.json") or "lista-paises" in path.name:
            continue
        meta_path = path.with_name(path.name+".meta.json")
        if not meta_path.exists():
            continue
        md = json.loads(meta_path.read_text(encoding="utf-8"))["metadatos_captura"]
        code, kind = str(md.get("codigo_hs", "")), str(md.get("tipo_consulta", ""))
        if code not in FRUITS or kind not in {"exportadores", "destinos_mexico"}:
            continue
        key = (code, kind)
        if key not in latest or path.stat().st_mtime_ns > latest[key][0]:
            latest[key] = (path.stat().st_mtime_ns, path, md)
    for _, path, md in sorted(latest.values(), key=lambda x: (x[2].get("codigo_hs", ""), x[2].get("tipo_consulta", ""))):
        code, kind = str(md.get("codigo_hs", "")), str(md.get("tipo_consulta", ""))
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources.append(path.resolve().relative_to(ROOT).as_posix())
        queries.append({"codigo_hs":code,"consulta":kind,"filas":int(payload.get("count",0)),
                        "truncamiento_posible":int(payload.get("count",0))>=500,
                        "error":payload.get("error","")})
        for r in payload.get("data",[]):
            net=float(r.get("netWgt") or 0); value=float(r.get("primaryValue") or 0)
            reporter=int(r.get("reporterCode",0)); partner=int(r.get("partnerCode",0))
            rows.append({"fruta":FRUITS[code][0],"grupo_fruta":FRUITS[code][1],"codigo_hs":code,
                "anio":int(r.get("refYear",2024)),"tipo_consulta":kind,"reporter_code_m49":reporter,
                "pais_reportante":countries.get(reporter,f"Área {reporter}"),"partner_code_m49":partner,
                "socio_comercial":countries.get(partner,"Mundo" if partner==0 else f"Área {partner}"),
                "valor_comercio_usd":value,"peso_neto_kg":net,
                "valor_unitario_aduanal_usd_kg":value/net if net>0 else None,
                "qty":r.get("qty"),"qty_unit_code":r.get("qtyUnitCode"),
                "estimacion_peso":bool(r.get("isNetWgtEstimated",False)),
                "valor_reportado":bool(r.get("isReported",False)),"archivo_bronce":path.resolve().relative_to(ROOT).as_posix(),
                "sha256_bronce":md.get("sha256")})
    frame=pd.DataFrame(rows)
    if frame.empty: raise ValueError("No hay datos de comercio procesables en Bronce")
    public=ROOT/"data/publico";oro=ROOT/"data/oro";public.mkdir(exist_ok=True,parents=True);oro.mkdir(exist_ok=True,parents=True)
    frame.to_csv(oro/"comercio_fruticola_mundial.csv",index=False,encoding="utf-8")
    frame.to_csv(public/"comercio_fruticola_mundial.csv",index=False,encoding="utf-8")
    report={"fuente":"UN Comtrade API pública","anio":2024,"filas":len(frame),"codigos_hs":FRUITS,
        "consultas":queries,"capturas_bronce":sources,
        "metodo":"USD/kg = valor comercial declarado / peso neto declarado cuando peso > 0",
        "limitaciones":["Los códigos HS agrupan productos y calidades; no equivalen siempre a una fruta/variedad exacta.",
            "USD/kg es valor unitario aduanal, no precio de anaquel, cotización mayorista ni precio al productor.",
            "La API pública permite previews de hasta 500 filas; 500 filas indica posible truncamiento.",
            "Importaciones que declaran México como socio señalan flujos comerciales agregados, no demanda disponible ni compradores confirmados.",
            "Se comparan los registros reportados por países; no hay ajuste cambiario, calidad o logística."]}
    (public/"reporte_comercio_mundial.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--anio",type=int,default=2024);p.add_argument("--solo-procesar",action="store_true");a=p.parse_args(argv)
    if a.solo_procesar: result=procesar_bronce()
    else:
        capturar(a.anio)
        result=procesar_bronce()
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0


if __name__ == "__main__":
    raise SystemExit(main())
