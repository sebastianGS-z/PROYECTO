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
from src.inteligencia.comercial import NOMBRE_CULTIVO, TECOMAN, _haversine

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


def centrales(base: Path) -> dict[str, Any]:
    g = json.loads((base / "data/publico/mapa_mercados_sniim.geojson").read_text(encoding="utf-8"))
    puntos = [f for f in g["features"] if f["geometry"]["type"] == "Point"]
    plazas = pd.read_csv(base / "data/publico/plazas_colima.csv") if (base / "data/publico/plazas_colima.csv").is_file() else pd.DataFrame()
    comparaciones: dict[str, list[dict[str, Any]]] = {}
    if not plazas.empty:
        for _, r in plazas.iterrows():
            comparaciones.setdefault(str(int(r["mercado"])), []).append({
                "cultivo": r["cultivo"], "producto": NOMBRE_CULTIVO.get(r["cultivo"], r["cultivo"]), "variante": r["variante"],
                "referencia": r.get("plaza_referencia"), "diferencia_mxn_kg": r["diferencia_media_mxn_kg"], "meses": int(r["meses_pareados"]),
                "pct_mayor": r["pct_meses_plaza_mayor"], "flete_equilibrio_mxn_kg": r["flete_equilibrio_mxn_kg"],
                "confianza": r.get("confianza", "baja"), "precio_plaza": r["precio_plaza_mxn_kg"]})
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
.pill{display:inline-block;border-radius:999px;padding:1px 8px;font-size:11px;font-weight:700}.alta{background:#dcefd3;color:#1f5a2c}.media{background:#f6ecd3;color:#7a5a12}.baja{background:#f4dcd5;color:#8a2f1d}
@media(max-width:820px){.layout{grid-template-columns:1fr;grid-template-rows:auto 60vh}aside{border-right:0;border-bottom:1px solid var(--line);max-height:none}#map{grid-row:2}.tabs{margin-left:0}}
</style></head><body>
<header><a href="inicio.html">← Inicio</a><h1>Mapa del observatorio</h1>
<div class="tabs" role="group" aria-label="Capa"><button id="t-prod" aria-pressed="true">Producción en Colima</button><button id="t-cen" aria-pressed="false">Centrales de abasto</button></div></header>
<div class="layout"><aside id="panel"></aside><div id="map" role="region" aria-label="Mapa interactivo"></div></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
const MUN=__MUN__, PROD=__PROD__, CEN=__CEN__;
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
  const html=`<h4>${esc(p.mercado)}</h4>${fmt(p.km_desde_tecoman)} km en línea recta desde Tecomán · ${fmt(p.cotizaciones_ultimo_dia)} cotizaciones el ${esc(p.fecha_corte)}<br>${comps.length?comps.map(c=>`<hr style="border:0;border-top:1px solid #ddd"><b>${esc(c.variante)}</b><br>Frente a ${esc(c.referencia)}: <b>${c.diferencia_mxn_kg>0?'+':''}${fmt(c.diferencia_mxn_kg,2)} MXN/kg</b> en ${c.meses} meses (mayor en ${fmt(c.pct_mayor)} %)<br>Flete extra máximo: ${fmt(c.flete_equilibrio_mxn_kg,2)} MXN/kg · <span class="pill ${esc(c.confianza)}">confianza ${esc(c.confianza)}</span>`).join(''):'<br>Sin comparación pareada para este producto.'}`;
  L.circleMarker([lat,lon],{radius:r,color:'#fff',weight:1.5,fillColor:col,fillOpacity:mejor?.95:.55}).bindTooltip(esc(p.ciudad)).bindPopup(html).addTo(capaCen);
  if(mejor)filas.push({n:(p.mercado.split(':')[1]||p.mercado).trim(),d:mejor.diferencia_mxn_kg,c:mejor.confianza,k:p.km_desde_tecoman,ref:mejor.referencia});}
 filas.sort((a,b)=>b.d-a.d);
 panel.innerHTML=`<label for="s-pc">Producto de Colima</label><select id="s-pc">${productosCen.map(p=>`<option ${p===prodCen?'selected':''}>${esc(p)}</option>`).join('')}</select>
 <p class="muted">Diferencia promedio de precio frente a <b>${esc(filas[0]?.ref||'la plaza de referencia')}</b> en meses en que ambas cotizaron el producto de origen Colima.</p>
 <table><thead><tr><th>Central</th><th>Dif. MXN/kg</th><th>Conf.</th><th>km</th></tr></thead><tbody>${filas.map(x=>`<tr><td>${esc(x.n)}</td><td style="color:${x.c==='baja'?'inherit':x.d>0?'#1d7a3a':'#b34a37'};font-weight:700">${x.d>0?'+':''}${fmt(x.d,2)}</td><td><span class="pill ${esc(x.c)}">${esc(x.c)}</span></td><td>${fmt(x.k)}</td></tr>`).join('')||'<tr><td colspan="4">Sin comparaciones</td></tr>'}</tbody></table>
 <p class="muted">Una central conviene si su "flete extra máximo" (en la ventana emergente) es mayor que lo que de verdad cuesta enviar ahí frente a la plaza de referencia. ${esc(CEN.properties.nota)}</p>`;
 document.getElementById('s-pc').onchange=e=>{prodCen=e.target.value;vistaCen()};
 setLeyenda(`<b>${esc(prodCen)}</b> frente a la referencia<br><i style="background:#1d7a3a"></i>paga más (comprobado)<br><i style="background:#b34a37"></i>paga menos (comprobado)<br><i style="background:#c9b98a"></i>no distinguible del azar<br><i style="background:#8a9690"></i>sin comparación<br><i style="background:#c08a32;border-radius:50%"></i>Tecomán`);
}
function capa(c){document.getElementById('t-prod').setAttribute('aria-pressed',c==='prod');document.getElementById('t-cen').setAttribute('aria-pressed',c==='cen');
 if(c==='prod'){if(capaCen){capaCen.remove();capaCen=null}vistaProd();map.invalidateSize();map.fitBounds(COLIMA,{padding:[10,10]});}
 else{if(capaProd){capaProd.remove();capaProd=null}vistaCen();map.invalidateSize();map.fitBounds(L.latLngBounds([16.5,-112],[30.5,-90]),{padding:[4,4]});}
 try{history.replaceState(null,'','#'+c)}catch(e){}}
document.getElementById('t-prod').onclick=()=>capa('prod');document.getElementById('t-cen').onclick=()=>capa('cen');
capa(location.hash==='#cen'?'cen':'prod');
</script></body></html>
"""


def ejecutar(base: Path = BASE_DIR) -> dict[str, Any]:
    geo = base / "data/publico/geo"
    geo.mkdir(parents=True, exist_ok=True)
    mun, prod, cen = municipios(base), produccion(base), centrales(base)
    for nombre, obj in (("municipios_colima.geojson", mun), ("produccion_municipal.json", prod), ("centrales.geojson", cen)):
        (geo / nombre).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pagina = (HTML.replace("__MUN__", json.dumps(mun, ensure_ascii=False, separators=(",", ":")))
              .replace("__PROD__", json.dumps(prod, ensure_ascii=False, separators=(",", ":")))
              .replace("__CEN__", json.dumps(cen, ensure_ascii=False, separators=(",", ":"))))
    (base / "tablero/mapa.html").write_text(pagina, encoding="utf-8")
    return {"municipios": len(mun["features"]), "cultivos": len(prod["cultivos"]), "anios": prod["anios"],
            "centrales": len(cen["features"]), "kb_pagina": round(len(pagina.encode()) / 1024)}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    print(json.dumps(ejecutar(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
