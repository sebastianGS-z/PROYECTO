"""Alertas del observatorio en formatos a los que cualquiera se puede suscribir (RSS y JSON).

    python main.py alertas

Escribe ``tablero/alertas.xml`` (RSS 2.0) y ``data/publico/alertas.json``. Un lector de RSS o un servicio de
"RSS a correo" avisa al productor cuando aparece una alerta nueva, sin cuentas ni datos personales en el
observatorio. Cada alerta tiene un identificador estable (no se repite si la condición sigue igual).

Reglas (solo con evidencia ya calculada por el observatorio):

* precio en el percentil ≥ 75 (alto, buen momento para vender) o ≤ 25 (bajo) de su historia;
* el dato parcial del mes se aleja del pronóstico (sale del rango de 80 % o se desvía 30 % o más);
* una central paga más que la referencia con confianza alta;
* la exportación pagó 20 % o más que el mercado nacional;
* una fuente de datos dejó de traer datos nuevos (frescura).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import BASE_DIR
from src.inteligencia.catalogo import FRUTAS, fruta_de

SITIO = "https://sebastiangs-z.github.io/PROYECTO/tablero/"


def _leer(base: Path, rel: str) -> pd.DataFrame:
    p = base / rel
    return pd.read_csv(p) if p.is_file() else pd.DataFrame()


def _json(base: Path, rel: str) -> dict[str, Any]:
    p = base / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _alerta(tipo: str, fruta: str, titulo: str, texto: str, enlace: str, clave: str) -> dict[str, Any]:
    ident = hashlib.sha1(f"{tipo}|{clave}".encode()).hexdigest()[:16]
    return {"id": ident, "tipo": tipo, "fruta": fruta, "titulo": titulo, "texto": texto, "enlace": SITIO + enlace}


def generar(base: Path = BASE_DIR) -> list[dict[str, Any]]:
    alertas: list[dict[str, Any]] = []
    sen = _leer(base, "data/publico/senales_mercado.csv")
    if not sen.empty:
        # Solo señales recientes: una alerta de un precio de hace meses ya no sirve para decidir.
        reciente = pd.Period(str(sen["ultimo_mes"].max()), freq="M") - 1
        sen = sen[sen["ultimo_mes"].astype(str).map(lambda m: pd.Period(m, freq="M") >= reciente)]
    for _, r in sen.iterrows():
        nombre = FRUTAS.get(fruta_de(r["cultivo"]), {}).get("nombre", r["cultivo"])
        if r["percentil_historico"] >= 75 or r["percentil_historico"] <= 25:
            alto = r["percentil_historico"] >= 75
            alertas.append(_alerta("precio_alto" if alto else "precio_bajo", nombre,
                                   f"{nombre}: precio {'alto' if alto else 'bajo'} en {r['nombre_mercado'].split(' · ')[0]} ({r['ultimo_mes']})",
                                   f"{r['variante']} se cotizó en {r['ultimo_precio_mxn_kg']:.2f} MXN/kg, "
                                   + (f"más alto que el {r['percentil_historico']:.0f} %" if alto else f"más bajo que el {100 - r['percentil_historico']:.0f} %")
                                   + f" de los últimos {int(r['meses_historia'])} meses. {r['lectura'].capitalize()}.", "preguntas.html#" + fruta_de(r["cultivo"]),
                                   f"{r['variante_id']}|{r['mercado']}|{r['ultimo_mes']}|{alto}"))
    preg = _json(base, "data/publico/preguntas_productor.json").get("respuestas", {})
    for fruta, lista in preg.items():
        for q in lista:
            if "próximo mes" in q["pregunta"] and "se aleja del pronóstico" in q["respuesta"]:
                alertas.append(_alerta("pronostico_divergente", FRUTAS[fruta]["nombre"], f"{FRUTAS[fruta]['nombre']}: el precio del mes se aleja del pronóstico",
                                       q["respuesta"].replace("**", ""), "preguntas.html#" + fruta, f"{fruta}|{q['actualizado']}"))
    pl = _leer(base, "data/publico/plazas_colima.csv")
    if not pl.empty and "confianza" in pl:
        for _, r in pl[pl["confianza"].eq("alta") & pl["diferencia_media_mxn_kg"].gt(0)].iterrows():
            nombre = FRUTAS.get(fruta_de(r["cultivo"]), {}).get("nombre", r["cultivo"])
            alertas.append(_alerta("central_conveniente", nombre, f"{nombre}: {r['nombre_mercado'].split(' · ')[0]} paga más que {r['plaza_referencia'].split(' · ')[0]}",
                                   f"{r['variante']} de origen Colima: +{r['diferencia_media_mxn_kg']:.2f} MXN/kg en {int(r['meses_pareados'])} meses (confianza "
                                   f"{int(r['confianza_pct'])} %). Conviene si el flete extra cuesta menos de {r['flete_equilibrio_mxn_kg']:.2f} MXN/kg.",
                                   "mapa.html#cen", f"{r['variante_id']}|{r['mercado']}|{r['hasta']}"))
    for v in _json(base, "data/publico/exportacion_resumen.json").get("frutas", {}).values():
        if v.get("disponible") and (v.get("prima_exportacion_pct") or 0) >= 20 and v.get("destinos"):
            alertas.append(_alerta("exportacion", v["nombre"], f"{v['nombre']}: la exportación pagó {v['prima_exportacion_pct']:+.0f} % frente al mercado nacional",
                                   f"Valor de exportación {v['anio']}: {v['valor_unitario_exportacion_mxn_kg']:.2f} MXN/kg contra {v['precio_mayorista_nacional_mxn_kg']:.2f} "
                                   f"MXN/kg nacional. Principal comprador: {v['destinos'][0]['pais']}. Valor aduanal: descuente certificación y logística.",
                                   "mapa.html#exp", f"{v['hs']}|{v['anio']}|{v['nombre']}"))
    for a in _json(base, "calidad/reportes/fiabilidad.json").get("frescura", {}).get("alertas", []):
        alertas.append(_alerta("frescura", "Sistema", "Fuente sin datos nuevos", a, "admin.html", a))
    return alertas


def rss(alertas: list[dict[str, Any]], ahora: datetime) -> str:
    items = "".join(f"<item><title>{html.escape(a['titulo'])}</title><link>{html.escape(a['enlace'])}</link>"
                    f"<guid isPermaLink=\"false\">{a['id']}</guid><category>{html.escape(a['tipo'])}</category>"
                    f"<description>{html.escape(a['texto'])}</description><pubDate>{format_datetime(ahora)}</pubDate></item>" for a in alertas)
    return ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>OAIC · Alertas de precios de frutas de Colima</title>'
            f"<link>{SITIO}inicio.html</link><description>Alertas calculadas con datos oficiales (SNIIM, SIAP, UN Comtrade). No es asesoría financiera.</description>"
            f"<language>es-mx</language><lastBuildDate>{format_datetime(ahora)}</lastBuildDate>{items}</channel></rss>\n")


def ejecutar(base: Path = BASE_DIR) -> dict[str, Any]:
    alertas = generar(base)
    ahora = datetime.now(timezone.utc).replace(microsecond=0)
    (base / "tablero/alertas.xml").write_text(rss(alertas, ahora), encoding="utf-8")
    (base / "data/publico/alertas.json").write_text(json.dumps({"generado_utc": ahora.isoformat(), "alertas": alertas}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"alertas": len(alertas), "por_tipo": pd.Series([a["tipo"] for a in alertas]).value_counts().to_dict() if alertas else {}}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print(json.dumps(ejecutar(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
