"""Mapa interactivo del observatorio (Leaflet): producción municipal en Colima y centrales de abasto.

    python main.py mapa

Escribe archivos geográficos ligeros en ``data/publico/geo/`` y la página ``tablero/mapa.html``:

* **Producción en Colima** (coropleta por municipio): cultivo y año seleccionables (SIAP 2016 en adelante),
  volumen, superficie cosechada, rendimiento y precio medio rural; ranking de municipios.
* **Centrales de abasto**: cada central con cotizaciones, ruta en línea recta desde Tecomán y color según cuánto
  pagó por el producto de Colima frente a la plaza de referencia en meses pareados (con su nivel de confianza).

Mapa base: CARTO (datos © OpenStreetMap). La biblioteca Leaflet se carga desde unpkg con versión fija.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from config.settings import BASE_DIR
from src.inteligencia.catalogo import FRUTAS, fruta_de
from src.inteligencia.comercial import TECOMAN, _haversine

CULTIVOS_MAPA = 14  # cultivos con más volumen que se ofrecen en el selector
PRIORITARIOS = ["Limón", "Papaya", "Plátano", "Mango", "Coco fruta", "Sandía", "Tamarindo", "Guayaba", "Aguacate", "Guanábana"]


def municipios(base: Path) -> dict[str, Any]:
    src = base / "data/publico/produccion_municipal_colima.geojson"
    gdf = gpd.read_file(src)[["cvegeo", "nomgeo", "geometry"]].drop_duplicates("cvegeo")
    gdf["geometry"] = gdf.geometry.simplify(0.0008, preserve_topology=True)
    return json.loads(gdf.to_json(drop_id=True))


def produccion(base: Path) -> dict[str, Any]:
    s = pd.read_csv(base / "data/oro/produccion_municipal_siap_colima.csv")
    s = s[s["Nomunidad"].eq("Tonelada")]
    vol = s.groupby("Nomcultivo")["volumen_produccion"].sum().sort_values(ascending=False)
    elegidos = [c for c in PRIORITARIOS if c in vol.index] + [c for c in vol.index if c not in PRIORITARIOS and "Pastos" not in c][:max(0, CULTIVOS_MAPA - 6)]
    elegidos = list(dict.fromkeys(elegidos))[:CULTIVOS_MAPA + 4]
    datos: dict[str, dict[str, dict[str, Any]]] = {}
    for (cultivo, anio), g in s[s["Nomcultivo"].isin(elegidos)].groupby(["Nomcultivo", "Anio"]):
        datos.setdefault(cultivo, {})[str(int(anio))] = {
            str(r["municipio_cvegeo"]).zfill(5): {"volumen_t": round(float(r["volumen_produccion"]), 1),
                                                  "cosechada_ha": round(float(r["superficie_cosechada_ha"]), 1),
                                                  "rendimiento_t_ha": round(float(r["volumen_produccion"] / r["superficie_cosechada_ha"]), 2) if r["superficie_cosechada_ha"] else None,
                                                  "precio_rural_mxn_kg": round(float(r["precio_medio_rural_mxn_unidad"]) / 1000, 2) if pd.notna(r["precio_medio_rural_mxn_unidad"]) else None,
                                                  "valor_mxn": round(float(r["valor_produccion_mxn"]), 0)}
            for _, r in g.iterrows()}
    anios = sorted({a for c in datos.values() for a in c})
    return {"cultivos": elegidos, "anios": anios, "datos": datos, "fuente": "SIAP · Cierre de la producción agrícola municipal",
            "fuente_bronce": sorted(s["archivo_bronce"].unique().tolist())}


def exportacion(base: Path) -> dict[str, Any]:
    """Por fruta: importaciones desde México por país (último año) y oportunidades, para el mapa mundial."""
    res_p, des_p = base / "data/publico/exportacion_resumen.json", base / "data/publico/exportacion_destinos.csv"
    if not res_p.is_file() or not des_p.is_file():
        return {}
    res = json.loads(res_p.read_text(encoding="utf-8"))["frutas"]
    des = pd.read_csv(des_p)
    out = {}
    for fruta, r in res.items():
        if not r.get("disponible"):
            out[fruta] = {"nombre": r["nombre"], "disponible": False, "nota": r.get("nota", "")}
            continue
        a = des[des["codigo_hs"].astype(str).str.zfill(6).eq(str(r["hs"])) & des["anio"].eq(r["anio"])]
        paises = {}
        for _, x in a.iterrows():
            paises[str(int(x["iso_numerico"])).zfill(3)] = {
                "pais": x["pais"], "desde_mexico_usd": round(float(x["valor_usd"])) if pd.notna(x["valor_usd"]) else 0,
                "toneladas": round(float(x["kg"]) / 1000) if pd.notna(x["kg"]) else 0,
                "mxn_kg": round(float(x["mxn_kg_desde_mexico"]), 2) if pd.notna(x["mxn_kg_desde_mexico"]) else None,
                "mundo_usd": round(float(x["mundo_usd"])) if pd.notna(x["mundo_usd"]) else None,
                "participacion_mexico_pct": round(float(x["participacion_mexico_pct"]), 1) if pd.notna(x["participacion_mexico_pct"]) else None}
        out[fruta] = {"nombre": r["nombre"], "disponible": True, "anio": r["anio"], "hs": r["hs"], "hs_nota": r.get("hs_nota", ""),
                      "prima_exportacion_pct": r.get("prima_exportacion_pct"), "valor_unitario_exportacion_mxn_kg": r.get("valor_unitario_exportacion_mxn_kg"),
                      "precio_mayorista_nacional_mxn_kg": r.get("precio_mayorista_nacional_mxn_kg"), "destinos": r["destinos"],
                      "oportunidades": r["oportunidades"], "paises": paises}
    return out


def centrales(base: Path) -> dict[str, Any]:
    g = json.loads((base / "data/publico/mapa_mercados_sniim.geojson").read_text(encoding="utf-8"))
    puntos = [f for f in g["features"] if f["geometry"]["type"] == "Point"]
    plazas = pd.read_csv(base / "data/publico/plazas_colima.csv") if (base / "data/publico/plazas_colima.csv").is_file() else pd.DataFrame()
    comparaciones: dict[str, list[dict[str, Any]]] = {}
    if not plazas.empty:
        for _, r in plazas.iterrows():
            comparaciones.setdefault(str(int(r["mercado"])), []).append({
                "cultivo": r["cultivo"], "producto": FRUTAS.get(fruta_de(r["cultivo"]), {}).get("nombre", r["cultivo"]), "variante": r["variante"],
                "referencia": r.get("plaza_referencia"), "diferencia_mxn_kg": r["diferencia_media_mxn_kg"], "meses": int(r["meses_pareados"]),
                "pct_mayor": r["pct_meses_plaza_mayor"], "flete_equilibrio_mxn_kg": r["flete_equilibrio_mxn_kg"],
                "confianza": r.get("confianza", "baja"), "confianza_pct": int(r["confianza_pct"]) if "confianza_pct" in r and pd.notna(r["confianza_pct"]) else None,
                "precio_plaza": r["precio_plaza_mxn_kg"], "precio_referencia": r.get("precio_referencia_mxn_kg"),
                "desde": r.get("desde"), "hasta": r.get("hasta")})
    feats = []
    for f in puntos:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {
            "mercado_id": str(p["mercado_id"]), "mercado": p["mercado"], "ciudad": p["ciudad"], "estado": p["estado"],
            "cotizaciones_ultimo_dia": p.get("num_cotizaciones", 0), "fecha_corte": p.get("fecha_corte"),
            "km_desde_tecoman": round(_haversine(TECOMAN[0], TECOMAN[1], lat, lon)), "comparaciones": comparaciones.get(str(p["mercado_id"]), [])}})
    return {"type": "FeatureCollection", "properties": {"origen": {"nombre": "Tecomán, Colima", "lat": TECOMAN[0], "lon": TECOMAN[1]},
                                                       "nota": "Ubicación aproximada: centro de la ciudad, no el inmueble del mercado. Distancia en línea recta."},
            "features": feats}


HTML = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mapa del observatorio · OAIC</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
<style>
:root{--ink:#17231f;--muted:#5f6d67;--line:#dde5df;--paper:#f4f7f3;--surface:#fff;--forest:#143d31;--lime:#d9ed8c}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ink:#e7eee9;--muted:#a3b2aa;--line:#2c3a33;--paper:#0f1713;--surface:#16211b;--forest:#0b2a20}}
*{box-sizing:border-box}html,body{margin:0;height:100%}body{background:var(--paper);color:var(--ink);font:14px/1.45 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;display:flex;flex-direction:column}
header{background:var(--forest);color:#fff;padding:12px 16px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}header h1{font-size:19px;margin:0}header a{color:var(--lime);font-weight:600;text-decoration:none}
.tabs{display:flex;gap:6px;margin-left:auto}.tabs button{font:inherit;font-weight:700;border:1px solid #ffffff55;background:transparent;color:#fff;border-radius:999px;padding:6px 14px;cursor:pointer}.tabs button[aria-pressed=true]{background:var(--lime);color:var(--forest);border-color:var(--lime)}
.layout{flex:1;display:grid;grid-template-columns:340px 1fr;min-height:0}aside{background:var(--surface);border-right:1px solid var(--line);padding:14px 16px;overflow:auto}
#map{min-height:420px}label{display:block;font-weight:700;font-size:12px;color:var(--muted);margin:10px 0 4px;text-transform:uppercase;letter-spacing:.05em}
select,input[type=range]{width:100%;font:inherit;padding:7px 8px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)}
.kpi{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0}.kpi div{border:1px solid var(--line);border-radius:10px;padding:8px 10px}.kpi b{display:block;font-size:18px}.kpi span{color:var(--muted);font-size:12px}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:8px}td,th{padding:5px 4px;border-bottom:1px solid var(--line);text-align:left}th{color:var(--muted)}
.legend{background:var(--surface);color:var(--ink);padding:8px 10px;border-radius:8px;box-shadow:0 1px 6px #0003;font-size:12px;line-height:1.5}.legend i{display:inline-block;width:14px;height:12px;margin-right:6px;vertical-align:-2px;border-radius:2px}
.muted{color:var(--muted);font-size:12px}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .base{filter:invert(1) hue-rotate(180deg) brightness(.85) contrast(.9)}}
.leaflet-popup-content{font:13px/1.45 Inter,system-ui,sans-serif}.leaflet-popup-content h4{margin:0 0 4px;font-size:14px}
.explica{background:#fff7e8;border:1px solid #ecd6a6;border-left:5px solid #c08a32;border-radius:10px;padding:9px 11px;margin:10px 0;color:#4d3b10;font-size:13px}
.pill{display:inline-block;border-radius:999px;padding:1px 8px;font-size:11px;font-weight:700}.alta{background:#dcefd3;color:#1f5a2c}.media{background:#f6ecd3;color:#7a5a12}.baja{background:#f4dcd5;color:#8a2f1d}
@media(max-width:820px){.layout{grid-template-columns:1fr;grid-template-rows:auto 60vh}aside{border-right:0;border-bottom:1px solid var(--line);max-height:none}#map{grid-row:2}.tabs{margin-left:0}}
</style></head><body>
<header><a href="inicio.html">← Inicio</a><h1>Mapa del observatorio</h1>
<div class="tabs" role="group" aria-label="Capa"><button id="t-prod" aria-pressed="true">Producción en Colima</button><button id="t-cen" aria-pressed="false">Centrales de abasto</button><button id="t-exp" aria-pressed="false">Exportación</button></div></header>
<div class="layout"><aside id="panel"></aside><div id="map" role="region" aria-label="Mapa interactivo"></div></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js"></script>
<script>
const MUN=__MUN__, PROD=__PROD__, CEN=__CEN__, EXP=__EXP__, SIN_COMP=__SINCOMP__;
const oscuro=matchMedia('(prefers-color-scheme: dark)').matches;
const map=L.map('map',{zoomControl:true,scrollWheelZoom:true,zoomSnap:0.25});
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,className:'base',
 attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · SIAP · SNIIM · INEGI'}).addTo(map);
// Colima continental: el municipio de Manzanillo incluye las Islas Revillagigedo (~ -114.7° de longitud),
// que harían que el encuadre abarque el Pacífico y el estado se vea diminuto.
const COLIMA=L.latLngBounds([18.62,-104.72],[19.55,-103.45]);
const fmt=(v,d=0)=>v==null||isNaN(v)?'—':Number(v).toLocaleString('es-MX',{maximumFractionDigits:d,minimumFractionDigits:d});
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const panel=document.getElementById('panel');let capaProd=null,capaCen=null,leyenda=null;
const escala=['#f1f7e8','#cfe6b4','#a3d07f','#6fb350','#3f8f33','#1d6b24','#0b4a17'];
function colorPor(v,max){if(!v)return oscuro?'#24302a':'#eef1ee';const i=Math.min(escala.length-1,Math.floor(Math.sqrt(v/max)*(escala.length-0.001)));return escala[i];}
function setLeyenda(html){if(leyenda)leyenda.remove();leyenda=L.control({position:'bottomright'});leyenda.onAdd=()=>{const d=L.DomUtil.create('div','legend');d.innerHTML=html;return d};leyenda.addTo(map);}
// ---------------- Producción ----------------
let cultivo=PROD.cultivos.includes('Limón')?'Limón':PROD.cultivos[0],anio=PROD.anios.at(-1);
function vistaProd(){
 const anios=Object.keys(PROD.datos[cultivo]||{}).sort();if(!anios.includes(anio))anio=anios.at(-1);
 const d=(PROD.datos[cultivo]||{})[anio]||{};const vals=Object.values(d).map(x=>x.volumen_t||0);const max=Math.max(1,...vals);const total=vals.reduce((a,b)=>a+b,0);
 const rank=Object.entries(d).sort((a,b)=>(b[1].volumen_t||0)-(a[1].volumen_t||0));
 const nombre=c=>(MUN.features.find(f=>f.properties.cvegeo===c)||{properties:{nomgeo:c}}).properties.nomgeo;
 const precioProm=(()=>{let v=0,w=0;for(const x of Object.values(d)){if(x.precio_rural_mxn_kg&&x.volumen_t){v+=x.precio_rural_mxn_kg*x.volumen_t;w+=x.volumen_t}}return w?v/w:null})();
 const serie=anios.map(a=>{const dd=PROD.datos[cultivo][a];const t=Object.values(dd).reduce((s,x)=>s+(x.volumen_t||0),0);return [a,t]});
 const maxS=Math.max(1,...serie.map(x=>x[1]));
 const spark=`<svg viewBox="0 0 300 70" width="100%" role="img" aria-label="Producción por año">${serie.map(([a,t],i)=>{const h=t/maxS*52,x=8+i*(284/Math.max(1,serie.length)),w=284/Math.max(1,serie.length)-4;return `<rect x="${x}" y="${60-h}" width="${w}" height="${h}" rx="2" fill="${a===anio?'#1d6b24':'#a3d07f'}"><title>${a}: ${fmt(t)} t</title></rect>`}).join('')}<text x="8" y="69" font-size="8" fill="currentColor">${anios[0]}</text><text x="292" y="69" font-size="8" text-anchor="end" fill="currentColor">${anios.at(-1)}</text></svg>`;
 panel.innerHTML=`<label for="s-cul">Cultivo</label><select id="s-cul">${PROD.cultivos.filter(c=>PROD.datos[c]).map(c=>`<option ${c===cultivo?'selected':''}>${esc(c)}</option>`).join('')}</select>
 <label for="s-anio">Año: <b>${anio}</b></label><input id="s-anio" type="range" min="0" max="${anios.length-1}" value="${anios.indexOf(anio)}" aria-valuetext="${anio}">
 <div class="kpi"><div><span>Producción en Colima</span><b>${fmt(total)} t</b></div><div><span>Precio medio rural</span><b>${fmt(precioProm,2)} MXN/kg</b></div></div>
 <div class="muted">Producción estatal por año (toneladas)</div>${spark}
 <table><thead><tr><th>Municipio</th><th>Toneladas</th><th>%</th><th>MXN/kg</th></tr></thead><tbody>${rank.map(([c,x])=>`<tr><td>${esc(nombre(c))}</td><td>${fmt(x.volumen_t)}</td><td>${fmt(x.volumen_t/total*100,1)}</td><td>${fmt(x.precio_rural_mxn_kg,2)}</td></tr>`).join('')}</tbody></table>
 <p class="muted">Fuente: ${esc(PROD.fuente)}. Producción cosechada en el año; no es inventario disponible ni ubicación de parcelas. El encuadre muestra Colima continental; las Islas Revillagigedo (municipio de Manzanillo) quedan fuera de la vista.</p>`;
 document.getElementById('s-cul').onchange=e=>{cultivo=e.target.value;vistaProd()};
 document.getElementById('s-anio').oninput=e=>{anio=anios[+e.target.value];vistaProd()};
 if(capaProd)capaProd.remove();
 capaProd=L.geoJSON(MUN,{style:f=>({color:oscuro?'#9fb7a9':'#3d5a4c',weight:1.2,fillOpacity:.82,fillColor:colorPor((d[f.properties.cvegeo]||{}).volumen_t,max)}),
  onEachFeature:(f,l)=>{const x=d[f.properties.cvegeo];l.bindTooltip(`<b>${esc(f.properties.nomgeo)}</b><br>${x?fmt(x.volumen_t)+' t':'sin producción reportada'}`,{sticky:true});
   l.bindPopup(`<h4>${esc(f.properties.nomgeo)} · ${esc(cultivo)} ${anio}</h4>${x?`Producción: <b>${fmt(x.volumen_t)} t</b> (${fmt(x.volumen_t/total*100,1)} % del estado)<br>Superficie cosechada: ${fmt(x.cosechada_ha)} ha<br>Rendimiento: ${fmt(x.rendimiento_t_ha,1)} t/ha<br>Precio medio rural: <b>${fmt(x.precio_rural_mxn_kg,2)} MXN/kg</b><br>Valor: $${fmt(x.valor_mxn)}`:'SIAP no reporta este cultivo en el municipio'}`);
   l.on('mouseover',()=>l.setStyle({weight:3}));l.on('mouseout',()=>capaProd.resetStyle(l));}}).addTo(map);
 const pasos=[0,.05,.15,.3,.5,.75,1].map(p=>p*max);
 setLeyenda(`<b>${esc(cultivo)} ${anio}</b> · toneladas<br>${escala.map((c,i)=>`<i style="background:${c}"></i>${i===0?'menos':i===escala.length-1?'más':''}`).join('<br>')}<br><span class="muted">máximo ${fmt(max)} t</span>`);
}
// ---------------- Centrales ----------------
const productosCen=[...new Set(CEN.features.flatMap(f=>f.properties.comparaciones.map(c=>c.producto)))].sort();let prodCen=productosCen.includes('Papaya')?'Papaya':productosCen[0];
function colorDif(c){if(!c)return '#8a9690';if(c.confianza==='baja')return '#c9b98a';return c.diferencia_mxn_kg>0?'#1d7a3a':'#b34a37';}
function vistaCen(){
 if(capaCen)capaCen.remove();capaCen=L.layerGroup().addTo(map);
 const o=CEN.properties.origen;L.circleMarker([o.lat,o.lon],{radius:9,color:'#fff',weight:2,fillColor:'#c08a32',fillOpacity:1}).bindTooltip('<b>Tecomán, Colima</b><br>origen de referencia').addTo(capaCen);
 const filas=[];
 for(const f of CEN.features){const p=f.properties,[lon,lat]=f.geometry.coordinates;
  const comps=p.comparaciones.filter(c=>c.producto===prodCen);const mejor=comps.sort((a,b)=>({alta:0,media:1,baja:2}[a.confianza]-({alta:0,media:1,baja:2}[b.confianza])))[0];
  const col=colorDif(mejor);const r=mejor?7+Math.min(10,Math.abs(mejor.diferencia_mxn_kg)):4;
  if(mejor)L.polyline([[o.lat,o.lon],[lat,lon]],{color:col,weight:mejor.confianza==='baja'?1:2.5,opacity:.6,dashArray:mejor.confianza==='baja'?'4 6':null}).addTo(capaCen);
  const html=`<h4>${esc(p.mercado)}</h4>${fmt(p.km_desde_tecoman)} km en línea recta desde Tecomán · ${fmt(p.cotizaciones_ultimo_dia)} cotizaciones el ${esc(p.fecha_corte)}<br>${comps.length?comps.map(c=>`<hr style="border:0;border-top:1px solid #ddd"><b>${esc(c.variante)}</b> de origen Colima, ${esc(c.desde)} a ${esc(c.hasta)}<br>Precio promedio aquí: <b>${fmt(c.precio_plaza,2)} MXN/kg</b><br>En ${esc(c.referencia)} (referencia), mismos meses: <b>${fmt(c.precio_referencia,2)} MXN/kg</b><br>Diferencia: <b>${c.diferencia_mxn_kg>0?'+':''}${fmt(c.diferencia_mxn_kg,2)} MXN/kg</b> en ${c.meses} meses (aquí pagó más en ${fmt(c.pct_mayor)} % de ellos)<br>Flete extra máximo para que convenga: ${fmt(c.flete_equilibrio_mxn_kg,2)} MXN/kg<br><span class="pill ${esc(c.confianza)}">confianza ${c.confianza_pct??'—'} % (${esc(c.confianza)})</span>`).join(''):'<br>Sin comparación pareada para este producto.'}`;
  L.circleMarker([lat,lon],{radius:r,color:'#fff',weight:1.5,fillColor:col,fillOpacity:mejor?.95:.55}).bindTooltip(esc(p.ciudad)).bindPopup(html).addTo(capaCen);
  if(mejor)filas.push({n:(p.mercado.split(':')[1]||p.mercado).trim(),d:mejor.diferencia_mxn_kg,c:mejor.confianza,pc:mejor.confianza_pct,pp:mejor.precio_plaza,pr:mejor.precio_referencia,k:p.km_desde_tecoman,ref:mejor.referencia,meses:mejor.meses});}
 filas.sort((a,b)=>b.d-a.d);
 const ref=filas[0]?.ref||'la plaza de referencia';
 panel.innerHTML=`<label for="s-pc">Fruta de origen Colima</label><select id="s-pc">${productosCen.map(p=>`<option ${p===prodCen?'selected':''}>${esc(p)}</option>`).join('')}</select>
 <div class="explica"><b>¿Contra qué se compara?</b> Contra <b>${esc(ref)}</b>. Para cada central se toman solo los meses en que ella y ${esc(ref)} cotizaron la misma variedad de ${esc(prodCen.toLowerCase())} de origen Colima (SNIIM), y se resta: <b>precio en la central − precio en ${esc(ref)}</b>. Verde: esa central pagó más; rojo: pagó menos. El porcentaje es la confianza de esa diferencia (prueba estadística y número de meses).</div>
 <table><thead><tr><th>Central</th><th>Ahí</th><th>${esc(ref.split(' · ')[0])}</th><th>Diferencia</th><th>Confianza</th></tr></thead><tbody>${filas.map(x=>`<tr><td>${esc(x.n)}<br><span class="muted">${fmt(x.k)} km · ${x.meses} meses</span></td><td>${fmt(x.pp,2)}</td><td>${fmt(x.pr,2)}</td><td style="color:${x.c==='baja'?'inherit':x.d>0?'#1d7a3a':'#b34a37'};font-weight:700">${x.d>0?'+':''}${fmt(x.d,2)}</td><td><span class="pill ${esc(x.c)}">${x.pc??'—'} %</span></td></tr>`).join('')||'<tr><td colspan="5">Sin comparaciones</td></tr>'}</tbody></table><p class="muted">Precios en MXN/kg, promedio de los meses comparados.</p>
 ${SIN_COMP.length?`<p class="muted"><b>Frutas sin comparación de centrales:</b> ${SIN_COMP.map(esc).join(', ')}. No hay al menos 3 meses en que dos centrales coticen la misma fruta de origen Colima.</p>`:''}
 <p class="muted">Una central conviene si su "flete extra máximo" (en la ventana emergente) es mayor que lo que de verdad cuesta enviar ahí frente a la plaza de referencia. ${esc(CEN.properties.nota)}</p>`;
 document.getElementById('s-pc').onchange=e=>{prodCen=e.target.value;vistaCen()};
 setLeyenda(`<b>${esc(prodCen)}</b>: precio en la central − precio en ${esc(ref.split(' · ')[0])}<br><i style="background:#1d7a3a"></i>paga más (comprobado)<br><i style="background:#b34a37"></i>paga menos (comprobado)<br><i style="background:#c9b98a"></i>no distinguible del azar<br><i style="background:#8a9690"></i>sin comparación<br><i style="background:#c08a32;border-radius:50%"></i>Tecomán`);
}
// ---------------- Exportación ----------------
const frutasExp=Object.entries(EXP).filter(([k,v])=>v.disponible).map(([k,v])=>k);let frutaExp=frutasExp.includes('limon')?'limon':frutasExp[0];let mundo=null,capaExp=null;
async function vistaExp(){
 if(!mundo){try{const t=await fetch('https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json').then(r=>r.json());mundo=topojson.feature(t,t.objects.countries);
   // Polígonos que cruzan el meridiano 180 (Rusia, Fiyi) dibujan bandas en Leaflet: se desplazan sus longitudes
   // negativas y se omite la Antártida.
   const corregir=c=>typeof c[0]==='number'?(c[0]<-150?[c[0]+360,c[1]]:c):c.map(corregir);
   mundo.features=mundo.features.filter(f=>String(f.id)!=='010').map(f=>['643','242'].includes(String(f.id))?{...f,geometry:{...f.geometry,coordinates:corregir(f.geometry.coordinates)}}:f);}catch(e){panel.innerHTML='<p>No se pudo cargar el mapa mundial (sin conexión a internet).</p>';return;}}
 const e=EXP[frutaExp]||{};const paises=e.paises||{};const opp=new Set((e.oportunidades||[]).map(o=>String(o.iso).padStart(3,'0')));
 const vals=Object.values(paises).map(x=>x.desde_mexico_usd||0);const max=Math.max(1,...vals);
 if(capaExp)capaExp.remove();
 capaExp=L.geoJSON(mundo,{style:f=>{const id=String(f.id).padStart(3,'0'),x=paises[id];const v=x?.desde_mexico_usd||0;
   return {color:opp.has(id)?'#2563eb':(oscuro?'#4b5a52':'#9aa8a0'),weight:opp.has(id)?2.2:.6,dashArray:opp.has(id)?'4 3':null,fillOpacity:v?.85:(opp.has(id)?.25:.1),fillColor:v?colorPor(v,max):(opp.has(id)?'#93c5fd':'#cbd5d0')}},
  onEachFeature:(f,l)=>{const id=String(f.id).padStart(3,'0'),x=paises[id];const nombre=x?.pais||f.properties.name;
   l.bindTooltip(`<b>${esc(nombre)}</b>${x?.desde_mexico_usd?'<br>USD '+fmt(x.desde_mexico_usd/1e6,1)+' millones desde México':''}`,{sticky:true});
   if(x)l.bindPopup(`<h4>${esc(nombre)} · ${esc(e.nombre)} ${e.anio}</h4>Compró a México: <b>USD ${fmt(x.desde_mexico_usd/1e6,2)} millones</b> (${fmt(x.toneladas)} t)<br>Valor por kilo: <b>${fmt(x.mxn_kg,2)} MXN/kg</b><br>Importó del mundo: USD ${fmt((x.mundo_usd||0)/1e6,1)} millones<br>Participación de México: <b>${fmt(x.participacion_mexico_pct,1)} %</b>${opp.has(id)?'<br><b style="color:#2563eb">Oportunidad: mercado grande donde México vende poco</b>':''}`);}}).addTo(map);
 const fila=x=>`<tr><td>${esc(x.pais)}</td><td>${fmt(x.valor_usd/1e6,1)}</td><td>${fmt(x.mxn_kg,2)}</td><td>${x.crecimiento_pct==null?'—':(x.crecimiento_pct>0?'+':'')+fmt(x.crecimiento_pct)+' %'}</td></tr>`;
 panel.innerHTML=`<label for="s-ef">Fruta</label><select id="s-ef">${frutasExp.map(k=>`<option value="${k}" ${k===frutaExp?'selected':''}>${esc(EXP[k].nombre)}</option>`).join('')}</select>
 <div class="explica"><b>¿Qué se ve?</b> Países que reportaron comprar ${esc((e.nombre||'').toLowerCase())} a México en ${e.anio} (UN Comtrade, código HS ${esc(e.hs)}). Más verde = compraron más. <span style="color:#2563eb;font-weight:700">Borde azul</span> = oportunidad: importan mucho del mundo y menos del 10 % viene de México.</div>
 <div class="kpi"><div><span>Valor de exportación</span><b>${fmt(e.valor_unitario_exportacion_mxn_kg,2)} MXN/kg</b></div><div><span>Mercado nacional</span><b>${fmt(e.precio_mayorista_nacional_mxn_kg,2)} MXN/kg</b></div></div>
 ${e.prima_exportacion_pct!=null?`<p>La exportación pagó <b>${e.prima_exportacion_pct>0?'+':''}${fmt(e.prima_exportacion_pct)} %</b> frente a las centrales nacionales.</p>`:''}
 <div class="muted">Principales compradores (USD millones, MXN/kg, crecimiento)</div><table><tbody>${(e.destinos||[]).map(fila).join('')}</tbody></table>
 ${(e.oportunidades||[]).length?`<div class="muted" style="margin-top:8px">Oportunidades (importan del mundo, USD millones · % de México)</div><table><tbody>${e.oportunidades.map(o=>`<tr><td>${esc(o.pais)}</td><td>${fmt(o.importa_del_mundo_usd/1e6,0)}</td><td>${fmt(o.participacion_mexico_pct,1)} %</td></tr>`).join('')}</tbody></table>`:''}
 <p class="muted">${esc(e.hs_nota||'')} Valores aduanales (no precio al productor). Exportar requiere certificación fitosanitaria, empaque, logística en frío y un comprador confirmado. Frutas sin datos: ${Object.entries(EXP).filter(([k,v])=>!v.disponible).map(([k,v])=>esc(v.nombre)).join(', ')||'ninguna'}.</p>`;
 document.getElementById('s-ef').onchange=ev=>{frutaExp=ev.target.value;vistaExp()};
 setLeyenda(`<b>${esc(e.nombre||'')} ${e.anio||''}</b> · compras a México<br>${escala.map((c,i)=>`<i style="background:${c}"></i>${i===0?'menos':i===escala.length-1?'más':''}`).join('<br>')}<br><i style="background:#93c5fd;border:2px dashed #2563eb"></i>oportunidad`);
}
function capa(c){for(const k of ['prod','cen','exp'])document.getElementById('t-'+k).setAttribute('aria-pressed',c===k);
 for(const l of [capaProd,capaCen,capaExp])if(l)l.remove();capaProd=capaCen=capaExp=null;map.invalidateSize();
 if(c==='prod'){vistaProd();map.fitBounds(COLIMA,{padding:[10,10]});}
 else if(c==='cen'){vistaCen();map.fitBounds(L.latLngBounds([16.5,-112],[30.5,-90]),{padding:[4,4]});}
 else{vistaExp();map.setView([25,-30],2);}
 try{history.replaceState(null,'','#'+c)}catch(e){}}
document.getElementById('t-prod').onclick=()=>capa('prod');document.getElementById('t-cen').onclick=()=>capa('cen');document.getElementById('t-exp').onclick=()=>capa('exp');
capa(['#cen','#exp'].includes(location.hash)?location.hash.slice(1):'prod');
</script></body></html>
"""


def ejecutar(base: Path = BASE_DIR) -> dict[str, Any]:
    geo = base / "data/publico/geo"
    geo.mkdir(parents=True, exist_ok=True)
    mun, prod, cen, exp = municipios(base), produccion(base), centrales(base), exportacion(base)
    con_comp = {c["producto"] for f in cen["features"] for c in f["properties"]["comparaciones"]}
    sin_comp = [v["nombre"] for v in FRUTAS.values() if v["nombre"] not in con_comp]
    for nombre, obj in (("municipios_colima.geojson", mun), ("produccion_municipal.json", prod), ("centrales.geojson", cen)):
        (geo / nombre).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pagina = (HTML.replace("__MUN__", json.dumps(mun, ensure_ascii=False, separators=(",", ":")))
              .replace("__PROD__", json.dumps(prod, ensure_ascii=False, separators=(",", ":")))
              .replace("__CEN__", json.dumps(cen, ensure_ascii=False, separators=(",", ":")))
              .replace("__EXP__", json.dumps(exp, ensure_ascii=False, separators=(",", ":")))
              .replace("__SINCOMP__", json.dumps(sin_comp, ensure_ascii=False)))
    (base / "tablero/mapa.html").write_text(pagina, encoding="utf-8")
    return {"municipios": len(mun["features"]), "cultivos": len(prod["cultivos"]), "anios": prod["anios"],
            "centrales": len(cen["features"]), "kb_pagina": round(len(pagina.encode()) / 1024)}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print(json.dumps(ejecutar(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
