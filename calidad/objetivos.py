"""Evaluación de los objetivos de calidad OQ1-OQ3 sobre manifiestos REALES.

Sin manifiestos en el periodo, el resultado es 'sin_datos' (nunca se presenta una meta como alcanzada).
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

OK_STATES = {"exitosa", "sin_resultados"}


def _cargar(bronze_dir: Path, desde: date, hasta: date) -> dict[str, list[dict[str, Any]]]:
    por_fuente: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ruta in sorted(Path(bronze_dir).glob("*/manifests/manifest_*.json")):
        m = json.loads(ruta.read_text(encoding="utf-8"))
        if m.get("modo") != "diaria":
            continue
        dia = date.fromisoformat(m["inicio"][:10])
        if desde <= dia <= hasta:
            m["_dia"] = dia
            por_fuente[m["fuente"]].append(m)
    return por_fuente


def evaluar_objetivos(bronze_dir: Path, desde: date, hasta: date) -> dict[str, Any]:
    datos = _cargar(bronze_dir, desde, hasta)
    dias = [desde + timedelta(days=i) for i in range((hasta - desde).days + 1)]
    if not datos:
        return {"periodo": [desde.isoformat(), hasta.isoformat()], "estado": "sin_datos",
                "nota": "No hay manifiestos diarios en el periodo; no se reporta ningún objetivo como cumplido."}
    runs = [m for ms in datos.values() for m in ms]
    ok = sum(m["estado"] in OK_STATES for m in runs)
    oq1 = round(100 * ok / len(runs), 2)
    huecos, sin_error, cubiertos, listado_fallos = 0, 0, 0, []
    huecos_por_dia: set[date] = set()
    for fuente, ms in datos.items():
        vistos = {m["_dia"] for m in ms}
        cubiertos += len(vistos)
        for d in dias:
            if d not in vistos:
                huecos += 1
                huecos_por_dia.add(d)
        for m in ms:
            if m["estado"] not in OK_STATES:
                listado_fallos.append({"fuente": fuente, "dia": m["_dia"].isoformat(), "estado": m["estado"], "run_id": m["run_id"]})
                if not m.get("errores") and not any(c.get("advertencias") for c in m.get("consultas", [])):
                    sin_error += 1
    racha = mejor = 0
    for d in dias:
        racha = racha + 1 if d in huecos_por_dia else 0
        mejor = max(mejor, racha)
    programadas = len(dias) * len(datos)
    oq3 = round(100 * cubiertos / programadas, 2)
    return {
        "periodo": [desde.isoformat(), hasta.isoformat()], "fuentes": sorted(datos),
        "OQ1": {"valor": oq1, "meta": ">= 95", "cumple": oq1 >= 95, "ejecuciones": len(runs), "ok": ok},
        "OQ2": {"valor": huecos + sin_error, "meta": "== 0", "cumple": huecos + sin_error == 0,
                "dias_sin_manifiesto": huecos, "no_exitosas_sin_error_documentado": sin_error, "racha_maxima_huecos": mejor},
        "OQ3": {"valor": oq3, "meta": "== 100", "cumple": oq3 == 100, "programadas": programadas, "con_manifiesto": cubiertos},
        "ejecuciones_no_exitosas_identificadas": listado_fallos,
    }
