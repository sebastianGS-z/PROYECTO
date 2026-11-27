"""Portal del observatorio: página de inicio para clientes y panel de administración.

    python main.py portal

* ``tablero/inicio.html`` — lo que le importa al cliente en una pantalla: por producto, último precio,
  pronóstico con rango y confianza, señal del mes y accesos a cada vista.
* ``tablero/admin.html`` — lo que le importa a quien opera el observatorio: estado y frescura de cada fuente,
  disponibilidad, alertas, contabilidad de la puerta de calidad, ISO/IEC 25012, salud de los pronósticos,
  evidencia de plazas e inventario de Bronce.

Solo lee archivos ya generados; no calcula cifras nuevas.
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

REPO = "https://github.com/sebastianGS-z/PROYECTO"
PRODUCTOS = {"limon": "Limón", "papaya": "Papaya", "platano": "Plátano"}
NAV = [("inicio.html", "Inicio"), ("preguntas.html", "Preguntas del productor"), ("inteligencia.html", "Reporte de inteligencia"),
       ("cliente.html", "Vista de cliente"), ("index.html", "Panel técnico"), ("laboratorio.html", "Laboratorio"), ("admin.html", "Administración")]

CSS = """
:root{--ink:#17231f;--muted:#5f6d67;--line:#dde5df;--paper:#f4f7f3;--surface:#fff;--forest:#143d31;--lime:#d9ed8c;--gold:#c08a32;--red:#a85242;--ok:#2e7d4f}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ink:#e7eee9;--muted:#a3b2aa;--line:#2c3a33;--paper:#0f1713;--surface:#16211b;--forest:#0b2a20}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:inherit}header{background:var(--forest);color:#fff;padding:16px}header .in,main,nav .in{max-width:1180px;margin:0 auto}
h1{margin:4px 0 2px;font-size:clamp(21px,3.4vw,30px)}header p{margin:0;color:#cfe0d6}
nav{background:var(--surface);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:3}nav .in{display:flex;gap:4px;overflow-x:auto;padding:6px 16px}
nav a{white-space:nowrap;text-decoration:none;padding:7px 11px;border-radius:8px;font-size:13px;font-weight:600;color:var(--muted)}nav a.on,nav a:hover{background:var(--paper);color:var(--ink)}
main{padding:18px 16px 48px}h2{font-size:17px;margin:26px 0 10px}.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px}.card h3{margin:0 0 6px;font-size:16px}
.big{font-size:28px;font-weight:750;letter-spacing:-.02em}.muted{color:var(--muted);font-size:13px}.row{display:flex;justify-content:space-between;gap:8px;padding:5px 0;border-bottom:1px dashed var(--line)}
.row:last-child{border:0}.pill{display:inline-block;border-radius:999px;padding:2px 9px;font-size:12px;font-weight:700}
.alta,.ok{background:#dcefd3;color:#1f5a2c}.media,.warn{background:#f6ecd3;color:#7a5a12}.baja,.bad{background:#f4dcd5;color:#8a2f1d}.na{background:#eceeed;color:#555}
table{width:100%;border-collapse:collapse;background:var(--surface);font-size:13px}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
th{color:var(--muted);font-weight:650}.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px}.kpi{font-size:24px;font-weight:750}
.alerta{background:#fff7e8;border:1px solid #ecd6a6;border-left:5px solid var(--gold);border-radius:10px;padding:10px 12px;margin:6px 0;color:#5b4511}
.cta{display:inline-block;margin-top:8px;background:var(--forest);color:#fff;text-decoration:none;border-radius:9px;padding:8px 12px;font-weight:700;font-size:13px}
.dias{display:flex;gap:3px;flex-wrap:wrap}.dia{width:22px;height:22px;border-radius:5px;display:grid;place-items:center;font-size:10px;color:#fff}
.dia.ok{background:var(--ok)}.dia.bad{background:var(--red)}
"""


def _f(x: Any, nd: int = 2) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "—"
    return "—" if math.isnan(v) else f"{v:,.{nd}f}"


def _csv(base: Path, rel: str) -> pd.DataFrame:
    p = base / rel
    return pd.read_csv(p, low_memory=False) if p.is_file() else pd.DataFrame()


def _js(base: Path, rel: str) -> dict[str, Any]:
    p = base / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _pagina(titulo: str, subtitulo: str, actual: str, cuerpo: str) -> str:
    nav = "".join(f'<a href="{h}" class="{"on" if h == actual else ""}">{html.escape(t)}</a>' for h, t in NAV)
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(titulo)}</title><style>{CSS}</style></head><body>'
            f'<header><div class="in"><h1>{html.escape(titulo)}</h1><p>{html.escape(subtitulo)}</p></div></header>'
            f'<nav aria-label="Secciones"><div class="in">{nav}</div></nav><main>{cuerpo}</main></body></html>')


def _pill(nivel: str) -> str:
    clase = {"alta": "alta", "media": "media", "baja": "baja"}.get(nivel, "na")
    return f'<span class="pill {clase}">Confianza {html.escape(nivel)}</span>'


# --------------------------------------------------------------------------------------------------
# Inicio (cliente)
# --------------------------------------------------------------------------------------------------

def inicio(base: Path = BASE_DIR) -> str:
    preg = _js(base, "data/publico/preguntas_productor.json")
    intel = _js(base, "data/publico/inteligencia.json")
    fiab = _js(base, "calidad/reportes/fiabilidad.json")
    pron = _csv(base, "data/publico/pronosticos_colima.csv")
    senales = _csv(base, "data/publico/senales_mercado.csv")
    tarjetas = []
    for c, nombre in PRODUCTOS.items():
        p = pron[pron["cultivo"].eq(c) & pron["horizonte_meses"].eq(1)] if not pron.empty else pron
        if "tipo_serie" in p and p["tipo_serie"].eq("origen_colima").any():
            p = p[p["tipo_serie"].eq("origen_colima")]
        s = senales[senales["cultivo"].eq(c)].sort_values("meses_historia", ascending=False) if not senales.empty else senales
        resp = {r["pregunta"]: r for r in preg.get("respuestas", {}).get(c, [])}
        conf_pron = next((r["confianza"] for q, r in resp.items() if "próximo mes" in q), "no aplica")
        filas = []
        if not s.empty:
            r = s.iloc[0]
            filas.append(f'<div class="row"><span>Último precio ({html.escape(str(r["ultimo_mes"]))})</span><b>{_f(r["ultimo_precio_mxn_kg"])} MXN/kg</b></div>')
            filas.append(f'<div class="row"><span>Frente a su historia</span><b>percentil {_f(r["percentil_historico"], 0)}</b></div>')
        if not p.empty:
            r = p.iloc[0]
            ref = " (referencia de mercado)" if r.get("tipo_serie") == "referencia_mercado" else ""
            filas.append(f'<div class="row"><span>Pronóstico {html.escape(str(r["fecha_pronostico"]))}{ref}</span><b>{_f(r["precio_frecuente_mxn_kg"])} MXN/kg</b></div>')
            filas.append(f'<div class="row"><span>Rango probable (80 %)</span><b>{_f(r["li80_mxn_kg"])} – {_f(r["ls80_mxn_kg"])}</b></div>')
            plaza = html.escape(str(r["nombre_mercado"]))
        else:
            plaza = "—"
            filas.append('<div class="row"><span>Pronóstico</span><b>sin serie elegible</b></div>')
        tarjetas.append(f'<article class="card"><h3>{nombre}</h3><div class="muted">{plaza}</div>{"".join(filas)}'
                        f'<p>{_pill(conf_pron)}</p><a class="cta" href="preguntas.html">13 respuestas sobre {nombre.lower()} →</a></article>')
    hallazgos = "".join(f"<li>{html.escape(h)}</li>" for h in intel.get("hallazgos", [])[:5])
    v = fiab.get("periodos", {}).get("ventana_sello_14_dias", {})
    cuerpo = (f'<h2>Precio por producto</h2><div class="grid">{"".join(tarjetas)}</div>'
              f'<h2>Hallazgos del mes</h2><div class="card"><ul>{hallazgos or "<li>Sin hallazgos en este corte.</li>"}</ul>'
              f'<a class="cta" href="inteligencia.html">Ver reporte completo (imprimible)</a></div>'
              '<h2>¿Qué quiere hacer?</h2><div class="grid">'
              '<div class="card"><h3>Saber si me ofrecen buen precio</h3><p class="muted">Calculadora en huerta contra precio rural y mayorista.</p><a class="cta" href="preguntas.html">Abrir calculadora</a></div>'
              '<div class="card"><h3>Comparar centrales y costos</h3><p class="muted">Simulador de margen, flete y punto de equilibrio con sus costos.</p><a class="cta" href="cliente.html">Abrir vista de cliente</a></div>'
              '<div class="card"><h3>Ver la serie y los modelos</h3><p class="muted">Historial, pronóstico con rango y evaluación de modelos.</p><a class="cta" href="index.html">Abrir panel técnico</a></div>'
              '<div class="card"><h3>Descargar los datos</h3><p class="muted">CSV y API JSON con licencia abierta.</p><a class="cta" href="../data/publico/api/v1/index.json">Abrir API</a></div></div>'
              f'<h2>Confianza del sistema</h2><div class="card"><div class="row"><span>Captura funcionando (últimos {v.get("dias", 14)} días)</span><b>{_f((v.get("disponibilidad") or 0) * 100, 0)} %</b></div>'
              f'<div class="row"><span>Datos al</span><b>{html.escape(str(v.get("hasta", "—")))}</b></div>'
              f'<p class="muted">Fuentes oficiales: SNIIM (Secretaría de Economía), SIAP (SADER), NOAA, INEGI, UN Comtrade. Cada cifra es rastreable a su archivo original. No es asesoría financiera.</p></div>')
    return _pagina("Observatorio de Agro-Inteligencia Colimense", "Precios, pronósticos y decisiones de venta para limón, papaya y plátano de Colima", "inicio.html", cuerpo)


# --------------------------------------------------------------------------------------------------
# Administración
# --------------------------------------------------------------------------------------------------

def inventario_bronce(base: Path) -> pd.DataFrame:
    filas = []
    raiz = base / "data/bronce"
    if not raiz.is_dir():
        return pd.DataFrame()
    for fuente in sorted(p for p in raiz.iterdir() if p.is_dir()):
        archivos = [p for p in fuente.rglob("*") if p.is_file() and not p.name.endswith(".meta.json") and "manifests" not in p.parts]
        if not archivos:
            continue
        mb = sum(p.stat().st_size for p in archivos) / 1e6
        ultimo = max(archivos, key=lambda p: p.name.rsplit("__", 1)[-1])
        filas.append({"fuente": fuente.name, "archivos": len(archivos), "MB": round(mb, 1), "última captura": ultimo.name.rsplit("__", 1)[-1].split(".")[0]})
    return pd.DataFrame(filas)


def _tabla(df: pd.DataFrame, cols: list[str] | None = None, nd: int = 2) -> str:
    if df.empty:
        return '<p class="muted">Sin datos.</p>'
    cols = cols or list(df.columns)
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
    def celda(v: Any) -> str:
        if isinstance(v, bool):
            return html.escape(str(v))
        if isinstance(v, int) or (hasattr(v, "dtype") and str(getattr(v, "dtype", "")).startswith("int")):
            return f"{int(v):,}"
        return _f(v, nd) if isinstance(v, float) else html.escape(str(v))
    body = "".join("<tr>" + "".join(f"<td>{celda(r[c])}</td>" for c in cols) + "</tr>" for _, r in df.iterrows())
    return f'<div class="wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def admin(base: Path = BASE_DIR) -> str:
    fiab = _js(base, "calidad/reportes/fiabilidad.json")
    iso = _js(base, "calidad/reportes/iso25012.json")
    cal = _js(base, "data/plata/reporte_calidad.json")
    pron = _csv(base, "data/publico/pronosticos_colima.csv")
    plazas = _csv(base, "data/publico/plazas_colima.csv")
    cuarentena = _csv(base, "data/cuarentena/registros_invalidos.csv")
    v = fiab.get("periodos", {}).get("ventana_sello_14_dias", {})
    alertas = list(fiab.get("frescura", {}).get("alertas", []))
    if v and (v.get("disponibilidad") or 0) < 0.95:
        alertas.append(f"Disponibilidad de 14 días {_f(v['disponibilidad'] * 100, 1)} % por debajo del objetivo de 95 %.")
    if cal.get("registros_cuarentena"):
        alertas.append(f"{cal['registros_cuarentena']} registros en cuarentena: revisar motivos.")
    alertas_html = "".join(f'<div class="alerta">⚠ {html.escape(a)}</div>' for a in alertas) or '<div class="card"><span class="pill ok">Sin alertas</span></div>'

    kpis = [("Disponibilidad 14 días", f'{_f((v.get("disponibilidad") or 0) * 100, 0)} %', "objetivo ≥ 95 %"),
            ("Fallas en 14 días", str(v.get("n_fallas", "—")), f'MTTR {_f(v.get("mttr_h"), 0)} h'),
            ("Retraso del cron (mediana)", f'{_f(fiab.get("puntualidad_schedule", {}).get("retraso_h_mediana"), 1)} h', "GitHub Actions"),
            ("Completitud Oro (ISO 25012)", f'{_f((iso.get("medidas", {}).get("completitud", {}).get("valor") or 0) * 100, 0)} %', "objetivo ≥ 95 %"),
            ("Registros en Plata", f'{cal.get("registros_plata_validos", 0):,}', f'de {cal.get("registros_bronce_parseados", 0):,} parseados'),
            ("Filas en Oro", f'{cal.get("filas_oro", 0):,}', "panel mensual con linaje")]
    kpi_html = "".join(f'<div class="card"><div class="muted">{html.escape(t)}</div><div class="kpi">{html.escape(val)}</div><div class="muted">{html.escape(n)}</div></div>' for t, val, n in kpis)

    fuentes = pd.DataFrame([{"fuente": k, "ejecuciones": x["ejecuciones"], "éxito técnico": f'{x["tasa_exito_tecnico"] * 100:.0f} %',
                             "con datos nuevos": f'{x["tasa_con_datos_nuevos"] * 100:.0f} %', "último dato nuevo": x.get("ultimo_dia_con_datos_nuevos") or "nunca",
                             "duración mediana (s)": x["duracion_s_mediana"]} for k, x in fiab.get("por_fuente", {}).items()])
    dias = fiab.get("detalle_diario", [])[-30:]
    cal_dias = "".join(f'<span class="dia {"ok" if d.get("operativo") else "bad"}" title="{html.escape(d["dia"])}: {html.escape(json.dumps(d.get("estados", {}), ensure_ascii=False))}">{d["dia"][-2:]}</span>' for d in dias)

    contab = pd.DataFrame([{"etapa": "Bronce parseado", "registros": cal.get("registros_bronce_parseados", 0)},
                           {"etapa": "Rechazados por reglas (cuarentena)", "registros": cal.get("registros_rechazados_por_reglas", cal.get("registros_cuarentena", 0))},
                           {"etapa": "Versiones duplicadas descartadas", "registros": cal.get("registros_duplicados_descartados", "—")},
                           {"etapa": "Válidos en Plata", "registros": cal.get("registros_plata_validos", 0)},
                           {"etapa": "Filas en Oro", "registros": cal.get("filas_oro", 0)}])
    medidas = pd.DataFrame([{"característica": k, "valor": f'{(m.get("valor") or 0) * 100:.1f} %' if isinstance(m.get("valor"), (int, float)) else "—",
                             "definición": m.get("definicion", "")} for k, m in iso.get("medidas", {}).items()])
    salud = pd.DataFrame()
    if not pron.empty:
        salud = pron[pron["horizonte_meses"].eq(1)][["variante", "nombre_mercado", "tipo_serie", "modelo_elegido", "meses_entrenamiento", "mape_backtest_pct", "cobertura_80_holdout", "fecha_ultimo_dato"]].copy()
        salud["cobertura_80_holdout"] = (salud["cobertura_80_holdout"] * 100).round(0).astype(str) + " %"
        salud.columns = ["serie", "plaza", "tipo", "modelo", "meses", "error % holdout", "acierto rango 80 %", "último dato"]
    pl = pd.DataFrame()
    if not plazas.empty and "confianza" in plazas:
        pl = plazas.groupby(["cultivo", "confianza"]).size().unstack(fill_value=0).reset_index()
    inv = inventario_bronce(base)
    motivos = cuarentena["motivo"].str.slice(0, 80).value_counts().head(8).rename_axis("motivo").reset_index(name="registros") if not cuarentena.empty and "motivo" in cuarentena else pd.DataFrame()
    cuerpo = (f'<h2>Alertas</h2>{alertas_html}<h2>Indicadores de operación</h2><div class="grid">{kpi_html}</div>'
              f'<h2>Captura diaria · últimos {len(dias)} días</h2><div class="card"><div class="dias">{cal_dias}</div>'
              '<p class="muted">Verde = día operativo (al menos una ejecución y ninguna fuente fallida); rojo = sin ejecución o con falla. Pase el cursor para ver el estado por fuente.</p></div>'
              f'<h2>Estado por fuente</h2>{_tabla(fuentes)}'
              f'<h2>Puerta de calidad · contabilidad Bronce → Oro</h2>{_tabla(contab)}'
              f'<h2>Motivos de cuarentena</h2>{_tabla(motivos)}'
              f'<h2>Calidad de datos · ISO/IEC 25012</h2>{_tabla(medidas)}'
              f'<h2>Salud de los pronósticos</h2>{_tabla(salud)}'
              f'<h2>Comparación de plazas · resultados por nivel de confianza</h2>{_tabla(pl)}'
              f'<h2>Inventario de Bronce</h2>{_tabla(inv, nd=1)}'
              f'<h2>Enlaces de operación</h2><div class="card"><div class="row"><span>Ejecuciones de GitHub Actions</span><a href="{REPO}/actions">Abrir</a></div>'
              f'<div class="row"><span>Lanzar captura manual (demo en vivo)</span><a href="{REPO}/actions/workflows/captura_diaria.yml">Run workflow</a></div>'
              f'<div class="row"><span>Integración continua (puerta 2)</span><a href="{REPO}/actions/workflows/validacion.yml">Ver</a></div>'
              f'<div class="row"><span>Hallazgos de auditoría</span><a href="{REPO}/blob/main/docs/calidad/auditoria/cierre_hallazgos.md">Ver</a></div>'
              f'<div class="row"><span>Solicitud del Sello TDL</span><a href="{REPO}/blob/main/docs/calidad/sello_tdl.md">Ver</a></div></div>')
    return _pagina("Administración del observatorio", f"Operación, calidad y salud de los datos · métricas al {fiab.get('generado_utc', '—')[:16]} UTC", "admin.html", cuerpo)


def ejecutar(base: Path = BASE_DIR) -> dict[str, str]:
    (base / "tablero/inicio.html").write_text(inicio(base), encoding="utf-8")
    (base / "tablero/admin.html").write_text(admin(base), encoding="utf-8")
    return {"inicio": "tablero/inicio.html", "admin": "tablero/admin.html"}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print(json.dumps(ejecutar(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
