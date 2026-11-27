"""Reporte de inteligencia para el cliente y API estática de datos.

    python main.py reporte

Genera:

* ``tablero/inteligencia.html`` — reporte imprimible (2 páginas en PDF desde el navegador) con los
  hallazgos, su evidencia y su incertidumbre, en lenguaje para un comprador o productor.
* ``docs/E4/reporte_inteligencia.md`` — la misma información en Markdown (entregable E4).
* ``data/publico/api/v1/*.json`` — API estática de solo lectura (datos como servicio) con un índice.

Todo sale de archivos ya calculados (Oro, pronósticos, inteligencia comercial, métricas de calidad);
este módulo no calcula cifras nuevas, solo las presenta.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import BASE_DIR
from src.inteligencia.comercial import MESES, NOMBRE_CULTIVO, REFERENCIA

API_FUENTES = {
    "pronosticos": ("data/publico/pronosticos_colima.csv", "Pronóstico mensual con intervalo de 80 % y 95 % por serie de origen Colima"),
    "plazas": ("data/publico/plazas_colima.csv", "Diferencia de precio de cada plaza frente a Guadalajara y flete de equilibrio"),
    "margen_productor": ("data/publico/margen_productor.csv", "Precio al productor (SIAP) frente al precio mayorista (SNIIM)"),
    "calendario_venta": ("data/publico/calendario_venta.csv", "Índice estacional por mes calendario"),
    "senales": ("data/publico/senales_mercado.csv", "Percentil histórico del último precio y lectura"),
    "panel_mensual": ("data/publico/panel_mensual_actual.csv", "Panel mensual completo con linaje a Bronce"),
    "precios_actuales": ("data/publico/precios_sniim_actuales.csv", "Última tabla nacional publicada por el SNIIM"),
}


def _leer(base: Path, rel: str) -> pd.DataFrame:
    p = base / rel
    return pd.read_csv(p) if p.is_file() else pd.DataFrame()


def _json_seguro(v: Any) -> Any:
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def construir_api(base: Path = BASE_DIR) -> dict[str, Any]:
    destino = base / "data/publico/api/v1"
    destino.mkdir(parents=True, exist_ok=True)
    indice = {"api": "OAIC · Observatorio de Agro-Inteligencia Colimense", "version": "v1",
              "licencia": "CC BY 4.0 para la contribución OAIC; las fuentes conservan sus términos (data/publico/LICENSE.md)",
              "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"), "recursos": {}}
    for nombre, (rel, desc) in API_FUENTES.items():
        df = _leer(base, rel)
        if df.empty:
            continue
        # El linaje completo (listas de archivos Bronce) se conserva en el CSV; en la API pesaría >10 MB.
        df = df.drop(columns=[c for c in df.columns if c.startswith("linaje_") or c in ("source_file", "source_sha256", "source_record_index")])
        registros = [{k: _json_seguro(v) for k, v in fila.items()} for fila in df.to_dict("records")]
        (destino / f"{nombre}.json").write_text(json.dumps({"recurso": nombre, "descripcion": desc, "fuente_csv": rel,
                                                            "filas": len(registros), "columnas": list(df.columns),
                                                            "linaje": f"columnas de linaje disponibles en {rel}", "datos": registros}, ensure_ascii=False, default=str), encoding="utf-8")
        indice["recursos"][nombre] = {"url": f"{nombre}.json", "descripcion": desc, "filas": len(registros), "columnas": list(df.columns)}
    (destino / "index.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")
    return indice


def _fmt(x: Any, nd: int = 2) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "—"
    return "—" if math.isnan(v) else f"{v:,.{nd}f}"


def _tabla(df: pd.DataFrame, cols: list[tuple[str, str]], nd: int = 2) -> str:
    if df.empty:
        return '<p class="muted">Sin datos suficientes en este corte.</p>'
    head = "".join(f"<th>{html.escape(t)}</th>" for _, t in cols)
    filas = []
    for _, r in df.iterrows():
        celdas = []
        for c, _ in cols:
            v = r.get(c)
            celdas.append(f"<td>{_fmt(v, nd) if isinstance(v, (int, float)) and not isinstance(v, bool) else html.escape(str(v if v is not None else '—'))}</td>")
        filas.append("<tr>" + "".join(celdas) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(filas)}</tbody></table>"


def datos_reporte(base: Path = BASE_DIR) -> dict[str, Any]:
    intel = json.loads((base / "data/publico/inteligencia.json").read_text(encoding="utf-8")) if (base / "data/publico/inteligencia.json").is_file() else {}
    fiab = json.loads((base / "calidad/reportes/fiabilidad.json").read_text(encoding="utf-8")) if (base / "calidad/reportes/fiabilidad.json").is_file() else {}
    iso = json.loads((base / "calidad/reportes/iso25012.json").read_text(encoding="utf-8")) if (base / "calidad/reportes/iso25012.json").is_file() else {}
    return {"intel": intel, "fiab": fiab, "iso": iso,
            "pron": _leer(base, "data/publico/pronosticos_colima.csv"), "plazas": _leer(base, "data/publico/plazas_colima.csv"),
            "margen": _leer(base, "data/publico/margen_productor.csv"), "cal": _leer(base, "data/publico/calendario_venta.csv"),
            "senales": _leer(base, "data/publico/senales_mercado.csv")}


def _calendario_html(cal: pd.DataFrame) -> str:
    ref = cal[cal["mercado"].astype(str).eq(REFERENCIA)] if not cal.empty else cal
    if ref.empty:
        return '<p class="muted">Sin series con 24 meses o más.</p>'
    filas = []
    for cultivo, g in ref.groupby("cultivo"):
        idx = g.set_index("mes")["indice_estacional"]
        celdas = []
        for m in range(1, 13):
            v = idx.get(m)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                celdas.append('<td class="c0">·</td>')
                continue
            pct = (v - 1) * 100
            clase = "c3" if pct >= 10 else "c2" if pct >= 3 else "c-3" if pct <= -10 else "c-2" if pct <= -3 else "c0"
            celdas.append(f'<td class="{clase}">{pct:+.0f}</td>')
        filas.append(f"<tr><th>{html.escape(NOMBRE_CULTIVO.get(cultivo, cultivo))}</th>{''.join(celdas)}</tr>")
    head = "".join(f"<th>{m}</th>" for m in MESES)
    conf = ", ".join(f"{NOMBRE_CULTIVO.get(c, c)}: {g['confianza_patron'].iloc[0]} (Kruskal-Wallis p = {g['p_estacionalidad_kruskal'].iloc[0]:.2f})"
                     for c, g in ref.groupby("cultivo") if "confianza_patron" in g)
    return (f'<table class="cal"><thead><tr><th></th>{head}</tr></thead><tbody>{"".join(filas)}</tbody></table>'
            f'<p class="muted">% frente a la tendencia, Guadalajara · Mercado de Abasto. Verde = pagó más en promedio; rojo = pagó menos. '
            f'Confianza del patrón: {html.escape(conf)}. Con confianza baja, la diferencia entre meses no se distingue del azar: úsese como pista.</p>')


def html_reporte(d: dict[str, Any]) -> str:
    intel, fiab, iso = d["intel"], d["fiab"], d["iso"]
    pron = d["pron"]
    prim = pron[pron["horizonte_meses"].eq(1)] if not pron.empty else pron
    plazas = d["plazas"]
    plazas_ok = plazas[plazas["evidencia"].eq("suficiente")] if not plazas.empty else plazas
    hallazgos = intel.get("hallazgos", [])
    ventana = fiab.get("periodos", {}).get("ventana_sello_14_dias", {})
    comp = iso.get("medidas", {}).get("completitud", {}).get("valor")
    corte = intel.get("ultimo_mes_cerrado", "—")
    hall_html = "".join(f"<li>{html.escape(h)}</li>" for h in hallazgos[:6]) or "<li>Sin hallazgos en este corte.</li>"
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reporte de inteligencia · OAIC</title>
<style>
:root{{--ink:#17231f;--muted:#5f6d67;--line:#dde5df;--paper:#f4f7f3;--forest:#143d31;--lime:#d9ed8c}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:14px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:980px;margin:0 auto;padding:20px 16px 48px}}header{{background:var(--forest);color:#fff;padding:18px 16px}}header .in{{max-width:980px;margin:0 auto}}
header a{{color:var(--lime)}}h1{{margin:4px 0;font-size:clamp(20px,3vw,28px)}}h2{{font-size:17px;margin:22px 0 8px;border-bottom:2px solid var(--forest);padding-bottom:3px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}}.kpi{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 12px}}
.kpi span,.kpi small{{display:block;color:var(--muted);font-size:12px}}.kpi strong{{font-size:19px}}
ol.hall li{{margin:0 0 8px}}table{{width:100%;border-collapse:collapse;background:#fff;font-size:12.5px;margin:6px 0}}th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}}
th{{background:#f1f5f1;color:var(--muted)}}.wrap{{overflow-x:auto}}.muted{{color:var(--muted);font-size:12px}}
table.cal td,table.cal th{{text-align:center;padding:5px 4px}}.c3{{background:#b9dba4}}.c2{{background:#e0efd4}}.c0{{background:#fff}}.c-2{{background:#f6dfd8}}.c-3{{background:#eab8aa}}
.note{{background:#fff;border-left:4px solid #c08a32;padding:8px 12px;border-radius:6px;font-size:12.5px}}
.print{{float:right;background:var(--lime);color:var(--forest);border:0;border-radius:8px;padding:7px 12px;font-weight:700;cursor:pointer}}
@media print{{body{{background:#fff;font-size:11px}}header{{background:#fff;color:#000;padding:0 0 6px;border-bottom:2px solid #000}}header a,.print{{display:none}}main{{padding:0}}
h2{{break-after:avoid}}table{{break-inside:avoid}}.kpi{{border-color:#999}}@page{{size:A4;margin:12mm}}}}
</style></head><body>
<header><div class="in"><button class="print" onclick="window.print()">Imprimir / PDF</button><a href="inicio.html">← Inicio</a> · <a href="mapa.html">Mapa</a> · <a href="preguntas.html">Preguntas</a>
<h1>Reporte de inteligencia · precios de frutas de Colima</h1>
<div>Corte: último mes cerrado {html.escape(str(corte))} · Fuentes oficiales: SNIIM (Secretaría de Economía), SIAP (SADER), NOAA, INEGI</div></div></header>
<main>
<div class="kpis">
<div class="kpi"><span>Disponibilidad de la captura (14 días)</span><strong>{_fmt((ventana.get('disponibilidad') or 0) * 100, 0)} %</strong><small>medida, no supuesta</small></div>
<div class="kpi"><span>Completitud de los datos</span><strong>{_fmt((comp or 0) * 100, 0)} %</strong><small>ISO/IEC 25012, columnas obligatorias</small></div>
<div class="kpi"><span>Series con pronóstico</span><strong>{prim['variante'].nunique() if not prim.empty else 0}</strong><small>con intervalo de 80 % y 95 %</small></div>
<div class="kpi"><span>Plazas comparadas</span><strong>{plazas['mercado'].nunique() if not plazas.empty else 0}</strong><small>frente a Guadalajara</small></div>
</div>
<h2>Hallazgos principales</h2>
<ol class="hall">{hall_html}</ol>
<h2>1. ¿A cuánto se venderá el próximo mes?</h2>
<div class="wrap">{_tabla(prim, [('variante', 'Producto'), ('nombre_mercado', 'Plaza'), ('fecha_pronostico', 'Mes'), ('precio_frecuente_mxn_kg', 'Pronóstico MXN/kg'), ('li80_mxn_kg', 'Mín. 80 %'), ('ls80_mxn_kg', 'Máx. 80 %'), ('mape_backtest_pct', 'Error típico %')])}</div>
<p class="note"><a href="preguntas.html">Respuestas por producto con nivel de confianza y calculadora de precio justo →</a><br>Cómo leerlo: 4 de cada 5 meses el precio cae dentro del rango de 80 %. "Error típico" es el error porcentual medio que tuvo el modelo en 6 meses que no conoció. Es una referencia para planear, no un precio garantizado.</p>
<h2>2. ¿A qué plaza conviene enviar?</h2>
<div class="wrap">{_tabla(plazas_ok.head(12), [('variante', 'Producto'), ('nombre_mercado', 'Plaza'), ('meses_pareados', 'Meses comparados'), ('diferencia_media_mxn_kg', 'Paga de más vs GDL (MXN/kg)'), ('pct_meses_plaza_mayor', '% meses que pagó más'), ('flete_equilibrio_mxn_kg', 'Flete extra máximo (MXN/kg)'), ('confianza', 'Confianza'), ('distancia_km_linea_recta', 'Km en línea recta')])}</div>
<p class="note">Regla práctica: si su cotización de flete adicional (frente a enviar a Guadalajara) por kg es menor que el "flete extra máximo", esa plaza le deja más. No incluye mermas por distancia ni comisiones distintas por plaza; agréguelas a su cotización.</p>
<h2>3. ¿Cuánto del precio llega al productor?</h2>
<div class="wrap">{_tabla(d['margen'][d['margen']['mercado'].astype(str).eq(REFERENCIA)] if not d['margen'].empty else d['margen'], [('anio', 'Año'), ('cultivo', 'Producto'), ('precio_productor_mxn_kg', 'Productor (SIAP)'), ('precio_mayorista_mxn_kg', 'Mayorista GDL (SNIIM)'), ('diferencia_mxn_kg', 'Diferencia'), ('participacion_productor_pct', '% que recibe el productor')])}</div>
<p class="muted">La diferencia cubre empaque, flete, mermas, comisiones e intermediación; no es la ganancia de un solo actor.</p>
<h2>4. ¿Qué meses suelen pagar más?</h2>
{_calendario_html(d['cal'])}
<h2>5. Señales del último mes</h2>
<div class="wrap">{_tabla(d['senales'].head(8), [('variante', 'Producto'), ('nombre_mercado', 'Plaza'), ('ultimo_mes', 'Mes'), ('ultimo_precio_mxn_kg', 'Precio MXN/kg'), ('percentil_historico', 'Percentil histórico'), ('lectura', 'Lectura')], 0)}</div>
<h2>Por qué confiar en estas cifras</h2>
<p>Cada cotización se descarga de la fuente oficial, se guarda sin modificar con su huella SHA-256 y pasa una puerta de calidad automática antes de entrar al análisis; los registros inválidos se apartan con su motivo. Cada cifra se puede rastrear hasta el archivo original. Los modelos se eligen por su error en meses que no vieron. Detalle técnico y metodología: <a href="laboratorio.html">laboratorio estadístico</a> y la documentación de calidad del repositorio.</p>
<p class="muted">Límites: precios mayoristas de plaza (no precio en huerta, salvo el SIAP anual); el clima de la estación de Manzanillo llega con ~2 semanas de rezago; la comparación de plazas usa solo meses en que ambas plazas cotizaron producto de origen Colima. No es asesoría financiera.</p>
</main></body></html>
"""


def markdown_reporte(d: dict[str, Any]) -> str:
    intel = d["intel"]
    lineas = ["# Reporte de inteligencia · precios de frutas de Colima\n",
              f"> Generado por `python main.py reporte` (último mes cerrado {intel.get('ultimo_mes_cerrado', '—')}). Versión visual e imprimible: [`tablero/inteligencia.html`](../../tablero/inteligencia.html).\n",
              "## Hallazgos principales\n", *[f"{i}. {h}" for i, h in enumerate(intel.get("hallazgos", []), 1)], "",
              "## Incertidumbre y límites\n",
              "- Los pronósticos se publican con intervalos de 80 % y 95 % construidos con errores fuera de muestra; su cobertura se audita en el holdout.",
              "- La comparación de plazas no incluye tarifas de flete inventadas: reporta el **flete de equilibrio** para que el cliente lo contraste con su cotización.",
              "- El precio al productor es el promedio anual SIAP ponderado por volumen de los municipios de Colima; no corresponde a un productor ni a una calidad específicos.",
              "- El calendario estacional usa 2–3 años por mes: indica una tendencia, no una regla.",
              "", "## Recomendaciones\n",
              "1. Planear compras y ventas con el rango de 80 %, no con el valor puntual.",
              "2. Antes de enviar a una plaza distinta de Guadalajara, pedir cotización de flete y compararla contra el flete de equilibrio de la tabla de plazas.",
              "3. Negociar contratos de precio fijo para el limón en los meses de índice estacional bajo, cuando el precio de plaza suele caer.",
              "4. Revisar las señales del último mes: un percentil ≥ 75 indica precio históricamente alto."]
    return "\n".join(lineas) + "\n"


def ejecutar(base: Path = BASE_DIR) -> dict[str, Any]:
    d = datos_reporte(base)
    (base / "tablero/inteligencia.html").write_text(html_reporte(d), encoding="utf-8")
    (base / "docs/E4").mkdir(parents=True, exist_ok=True)
    (base / "docs/E4/reporte_inteligencia.md").write_text(markdown_reporte(d), encoding="utf-8")
    api = construir_api(base)
    return {"html": "tablero/inteligencia.html", "markdown": "docs/E4/reporte_inteligencia.md", "api_recursos": sorted(api["recursos"])}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print(json.dumps(ejecutar(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
