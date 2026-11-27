"""Genera ``tablero/laboratorio.html``: pronóstico con intervalo (E1), experimento (E2) y mapa PCA (E3).

La página es autocontenida (figuras incrustadas en base64) para que funcione igual en el servidor local
(`scripts/servir_tablero.py`) y publicada como sitio estático.

    python -m laboratorio.tablero
"""
from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path
from typing import Any

from laboratorio.comun import BASE_DIR, RESULTADOS, fmt


def _img(path: Path, alt: str) -> str:
    if not path.is_file():
        return f'<p class="empty">Figura no disponible: {html.escape(path.name)}</p>'
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f'<img src="data:image/png;base64,{data}" alt="{html.escape(alt)}" loading="lazy">'


def _tabla(filas: list[dict[str, Any]], columnas: list[tuple[str, str]], nd: int = 2) -> str:
    head = "".join(f"<th>{html.escape(t)}</th>" for _, t in columnas)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(fmt(f.get(k), nd) if isinstance(f.get(k), (int, float)) else str(f.get(k, '')))}</td>"
                                    for k, _ in columnas) + "</tr>" for f in filas)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _leer(path: Path) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def generar(resultados: Path = RESULTADOS, docs: Path = BASE_DIR / "docs", destino: Path = BASE_DIR / "tablero" / "laboratorio.html") -> Path:
    e1, e2, e3 = (_leer(resultados / e / "resultados.json") for e in ("e1", "e2", "e3"))
    secciones = []
    if e1:
        lim = e1["limon_c5"]
        pron = lim["pronostico"]
        secciones.append(f"""
<section id="pronostico"><h2>Pronóstico con intervalo de predicción</h2>
<p class="lead">{html.escape(lim['frase_cliente'])}</p>
<div class="kpis">
  <div class="kpi"><span>Modelo elegido por error</span><strong>{html.escape(lim['ganador'])}</strong><small>menor RMSE en 6 meses no vistos</small></div>
  <div class="kpi"><span>Error medio en prueba (MAE)</span><strong>{fmt(lim['comparacion_prueba'][0]['MAE'], 1)} MXN/kg</strong><small>MAPE {fmt(lim['comparacion_prueba'][0]['MAPE_pct'], 0)} %</small></div>
  <div class="kpi"><span>{html.escape(pron[0]['mes'])} · intervalo 80 %</span><strong>{fmt(pron[0]['li80'], 1)}–{fmt(pron[0]['ls80'], 1)}</strong><small>MXN/kg · punto {fmt(pron[0]['pronostico'], 1)}</small></div>
  <div class="kpi"><span>Supuestos de residuos</span><strong>{'Aprobados' if lim['supuestos_ok'] else 'No aprobados'}</strong><small>Ljung-Box, varianza estable</small></div>
</div>
<div class="card">{_img(docs / 'E1' / 'laboratorio' / 'limon_c5_pronostico.png', 'Pronóstico del limón con intervalos de 80 y 95 %')}</div>
{_tabla(pron, [('mes', 'Mes'), ('pronostico', 'Pronóstico'), ('li80', 'Mín 80 %'), ('ls80', 'Máx 80 %'), ('li95', 'Mín 95 %'), ('ls95', 'Máx 95 %'), ('metodo', 'Método del intervalo')])}
<h3>Comparación de los cuatro modelos (meses que el modelo no vio)</h3>
{_tabla(lim['comparacion_prueba'], [('modelo', 'Modelo'), ('MAE', 'MAE'), ('RMSE', 'RMSE'), ('MAPE_pct', 'MAPE %')])}
<p class="note">Cómo leerlo: el intervalo de 80 % es el rango donde esperamos el precio 4 de cada 5 meses. Es un apoyo para planear compras y ventas, no un precio garantizado.
Método completo: <a href="../docs/E1/laboratorio_series.md">laboratorio de series de tiempo</a>.</p>
</section>""")
        if "papaya_maradol" in e1:
            secciones.append(f"""<section><h3>Papaya Maradol · Colima → Guadalajara</h3><p class="lead">{html.escape(e1['papaya_maradol']['frase_cliente'])}</p>
{_tabla(e1['papaya_maradol']['pronostico'], [('mes', 'Mes'), ('pronostico', 'Pronóstico'), ('li80', 'Mín 80 %'), ('ls80', 'Máx 80 %'), ('metodo', 'Método del intervalo')])}</section>""")
    if e3:
        nombres = e3["pca"]["nombres"]
        cent = [{"producto": k, **v} for k, v in e3["centroides"].items()]
        orden = sorted(cent, key=lambda c: c["CP1"])
        derecha, izquierda = [c["producto"] for c in orden[-2:]][::-1], orden[0]["producto"]
        secciones.append(f"""
<section id="mapa"><h2>Mapa de productos (componentes principales)</h2>
<p class="lead">Cada punto es una serie de cotización en un mes; la X marca el centro de cada producto. Productos cercanos se comportan parecido en precio, estabilidad y profundidad de mercado.</p>
<div class="card">{_img(docs / 'E3' / 'multivariado' / 'biplot.png', 'Mapa de componentes principales por producto')}</div>
<ul class="axes"><li><b>Eje horizontal (CP1, {fmt(e3['pca']['varianza_explicada'][0] * 100, 0)} %):</b> {html.escape(nombres['CP1'])}.</li>
<li><b>Eje vertical (CP2, {fmt(e3['pca']['varianza_explicada'][1] * 100, 0)} %):</b> {html.escape(nombres['CP2'])}.</li></ul>
{_tabla(cent, [('producto', 'Producto'), ('CP1', 'CP1'), ('CP2', 'CP2')])}
<p class="note">Interpretación para el comprador: {html.escape(' y '.join(derecha))} se ubican a la derecha del mapa ({html.escape(nombres['CP1'].lower())});
{html.escape(izquierda)} queda en el extremo izquierdo, el opuesto en ese índice, por lo que conviene revisarlo con más frecuencia.
La MANOVA (traza de Pillai con prueba de permutación, p = {fmt(e3['pillai_permutacion']['p'], 3)}) confirma que los productos difieren en conjunto.
Detalle: <a href="../docs/E3/multivariado.md">laboratorio multivariado</a>.</p>
</section>""")
    if e2:
        conf = e2["confirmacion"]
        opt = ", ".join(f"{k} = {v}" for k, v in e2["optimo"].items())
        secciones.append(f"""
<section id="experimento"><h2>Experimento sobre el propio extractor</h2>
<div class="kpis">
  <div class="kpi"><span>Combinación óptima</span><strong class="small">{html.escape(opt)}</strong><small>sin errores de extracción</small></div>
  <div class="kpi"><span>Tiempo confirmado</span><strong>{fmt(conf['media_s'], 2)} s</strong><small>5 corridas de confirmación</small></div>
  <div class="kpi"><span>Mejora vs. producción</span><strong>{fmt(e2['mejora_vs_produccion_pct'], 1)} %</strong><small>misma muestra de capturas</small></div>
</div>
<p class="note">Diseño 2³ con 3 réplicas en bloques aleatorizados, diseño 3×2 con interacción y fraccionado 2⁴⁻¹. Detalle: <a href="../docs/E2/experimento_factorial.md">experimento factorial</a>.</p>
</section>""")
    cuerpo = "\n".join(secciones) or '<p class="empty">Ejecute primero los laboratorios: python -m laboratorio.e1_series, e2_experimento y e3_multivariado.</p>'
    pagina = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Laboratorio estadístico · OAIC</title>
<style>
:root{{--ink:#17231f;--muted:#66746e;--line:#e3e9e4;--paper:#f4f7f3;--surface:#fff;--forest:#143d31;--lime:#d9ed8c}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
header{{background:var(--forest);color:#fff;padding:22px 16px}}header .in,main{{max-width:1100px;margin:0 auto}}header a{{color:var(--lime)}}
h1{{margin:4px 0;font-size:clamp(22px,3vw,30px)}}main{{padding:8px 16px 48px}}section{{margin-top:28px}}h2{{font-size:20px;margin:0 0 8px}}h3{{font-size:15px;margin:20px 0 8px}}
.lead{{font-size:15px;background:#fff;border-left:4px solid var(--forest);padding:12px 14px;border-radius:8px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:12px 0}}
.kpi{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 14px}}.kpi span,.kpi small{{display:block;color:var(--muted);font-size:12px}}
.kpi strong{{display:block;font-size:21px;margin:3px 0}}.kpi strong.small{{font-size:14px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px}}img{{width:100%;height:auto;display:block}}
.table-wrap{{overflow-x:auto;margin:10px 0}}table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}th{{background:#f6f8f5;color:var(--muted)}}
.note{{color:var(--muted);font-size:13px}}.axes{{padding-left:18px}}.empty{{color:var(--muted)}}
</style></head><body>
<header><div class="in"><a href="index.html">← Panel principal</a><h1>Laboratorio estadístico</h1>
<div>Pronóstico con intervalo, mapa multivariado y experimento del extractor · generado desde <code>laboratorio/resultados/</code></div></div></header>
<main>{cuerpo}</main></body></html>
"""
    destino.write_text(pagina, encoding="utf-8")
    return destino


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--destino", type=Path, default=BASE_DIR / "tablero" / "laboratorio.html")
    a = ap.parse_args(argv)
    print(f"Tablero del laboratorio: {generar(destino=a.destino)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
