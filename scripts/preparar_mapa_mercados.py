"""Prepara una cartografía nacional offline para las plazas cotizadas por SNIIM.

Los puntos corresponden al centro aproximado de la ciudad del mercado (geocodificado
una sola vez con Nominatim); los límites estatales proceden del Marco Geoestadístico
del INEGI. Las capturas originales se conservan en Bronce.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

from almacenamiento.bronze_writer import BronzeWriter, sha256_file
from almacenamiento.manifest import Manifest, new_run_id
from config.settings import BASE_DIR, get_settings
from extractores.base import RawCapture
from src.tdl_e2.geoespacial import INEGIMarcoExtractor

CITY_BY_MARKET = {
    "10": ("Aguascalientes", "Aguascalientes"), "33": ("Tijuana", "Baja California"),
    "20": ("La Paz", "Baja California Sur"), "40": ("Campeche", "Campeche"),
    "50": ("Torreón", "Coahuila"), "80": ("Colima", "Colima"),
    "70": ("Tuxtla Gutiérrez", "Chiapas"), "71": ("Tapachula", "Chiapas"),
    "61": ("Chihuahua", "Chihuahua"), "63": ("Ciudad Juárez", "Chihuahua"),
    "100": ("Iztapalapa, Ciudad de México", "Ciudad de México"), "102": ("Durango", "Durango"),
    "101": ("Gómez Palacio", "Durango"), "110": ("León", "Guanajuato"),
    "112": ("Celaya", "Guanajuato"), "111": ("Irapuato", "Guanajuato"),
    "121": ("Acapulco de Juárez", "Guerrero"), "122": ("Chilpancingo", "Guerrero"),
    "130": ("Pachuca de Soto", "Hidalgo"), "140": ("Guadalajara", "Jalisco"),
    "141": ("Guadalajara", "Jalisco"), "151": ("Ecatepec de Morelos", "México"),
    "150": ("Toluca de Lerdo", "México"), "160": ("Morelia", "Michoacán"),
    "170": ("Cuautla", "Morelos"), "172": ("Cuernavaca", "Morelos"),
    "180": ("Tepic", "Nayarit"), "181": ("Tepic", "Nayarit"),
    "190": ("San Nicolás de los Garza", "Nuevo León"), "200": ("Oaxaca de Juárez", "Oaxaca"),
    "210": ("Puebla", "Puebla"), "220": ("Santiago de Querétaro", "Querétaro"),
    "230": ("Chetumal", "Quintana Roo"), "231": ("Cancún", "Quintana Roo"),
    "240": ("San Luis Potosí", "San Luis Potosí"), "250": ("Culiacán Rosales", "Sinaloa"),
    "252": ("Mazatlán", "Sinaloa"), "261": ("Ciudad Obregón", "Sonora"),
    "260": ("Hermosillo", "Sonora"), "270": ("Villahermosa", "Tabasco"),
    "281": ("Reynosa", "Tamaulipas"), "280": ("Tampico", "Tamaulipas"),
    "301": ("Xalapa-Enríquez", "Veracruz"), "302": ("Minatitlán", "Veracruz"),
    "306": ("Veracruz", "Veracruz"), "310": ("Mérida", "Yucatán"),
    "311": ("Oxkutzcab", "Yucatán"), "312": ("Mérida", "Yucatán"),
    "320": ("Zacatecas", "Zacatecas"),
}


def _simplificar(geometria: dict, tolerancia: float = 0.01) -> dict:
    """Simplifica un polígono estatal (~1 km) para que el mapa web pese KB y no decenas de MB."""
    from shapely.geometry import mapping, shape
    geo = shape(geometria).simplify(tolerancia, preserve_topology=True)
    return json.loads(json.dumps(mapping(geo)), parse_float=lambda x: round(float(x), 4))


def _latest_state_files(bronze: Path) -> dict[str, Path]:
    found: dict[str, tuple[int, Path]] = {}
    for sidecar in (bronze / "inegi_marco").rglob("*.geojson.meta.json"):
        try:
            meta = json.loads(sidecar.read_text(encoding="utf-8"))["metadatos_captura"]
            if meta.get("tipo") != "marco-estatal":
                continue
            code = str(meta["cve_ent"]).zfill(2)
            content = sidecar.with_name(sidecar.name.removesuffix(".meta.json"))
            if content.is_file() and sha256_file(content) == meta.get("sha256"):
                if code not in found or content.stat().st_mtime_ns > found[code][0]:
                    found[code] = (content.stat().st_mtime_ns, content)
        except (OSError, ValueError, KeyError):
            continue
    return {key: value[1] for key, value in found.items()}


def _geocode(cities: dict[tuple[str, str], tuple[float, float]], wanted: list[tuple[str, str]]) -> dict:
    settings = get_settings(); run_id = new_run_id(); writer = BronzeWriter(settings.bronze_dir)
    features = []
    for index, (city, state) in enumerate(wanted):
        query = f"{city}, {state}, Mexico"
        params = urllib.parse.urlencode({"q": query, "format": "jsonv2", "limit": 1,
                                          "countrycodes": "mx", "accept-language": "es"})
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "OAIC-Observatorio/1.0 (educational market mapping)",
                                                   "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not payload:
                raise ValueError("Nominatim no encontró la localidad")
            location = payload[0]
            lon, lat = float(location["lon"]), float(location["lat"])
            cities[(city, state)] = (lon, lat)
            features.append({"type": "Feature", "properties": {"ciudad": city, "estado": state,
                            "consulta": query, "display_name": location.get("display_name", ""),
                            "fuente": "OpenStreetMap Nominatim", "url": url},
                            "geometry": {"type": "Point", "coordinates": [lon, lat]}})
            print(f"Geocodificada {city}, {state}", flush=True)
        except Exception as exc:
            print(f"No se pudo geocodificar {city}, {state}: {type(exc).__name__}: {exc}", flush=True)
        if index < len(wanted) - 1:
            time.sleep(1.1)  # política pública de Nominatim: máximo 1 solicitud por segundo
    collection = {"type": "FeatureCollection", "features": features}
    content = json.dumps(collection, ensure_ascii=False, separators=(",", ":")).encode()
    cap = RawCapture(fuente="nominatim_mercados", url="https://nominatim.openstreetmap.org/search",
                     contenido=content, formato="geojson", http_status=200, registros=len(features), estado="ok",
                     metadatos={"etiqueta": "centros-ciudades-mercados-sniim", "tipo": "geocodificacion",
                                "fuente": "OpenStreetMap Nominatim", "fecha_ref_inicio": datetime.now(timezone.utc).date().isoformat(),
                                "fecha_ref_fin": datetime.now(timezone.utc).date().isoformat(),
                                "politica": "máximo 1 solicitud por segundo; resultados cacheados para uso offline"})
    saved = writer.write(cap, run_id)
    return {"ciudades": cities, "features": features, "bronze": saved.ruta}


def preparar(capturar_fuentes: bool = True) -> dict:
    bronze = BASE_DIR / "data/bronce"
    current_path = BASE_DIR / "data/publico/precios_sniim_actuales.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    report = current["reporte"]
    markets = {str(c["mercado_id"]): c["mercado"] for c in report["capturas"]}
    market_ids = sorted(markets, key=lambda x: int(x))
    missing_city = [key for key in market_ids if key not in CITY_BY_MARKET]
    if missing_city:
        raise ValueError(f"Falta geocodificación de mercados: {missing_city}")
    wanted = sorted({CITY_BY_MARKET[key] for key in market_ids})
    city_points = {}
    location_meta = None
    geo_file = BASE_DIR / "data/publico/mercados_ciudad_sniim.geojson"
    if geo_file.is_file():
        geo = json.loads(geo_file.read_text(encoding="utf-8"))
        for f in geo.get("features", []):
            p = f.get("properties", {}); c = f.get("geometry", {}).get("coordinates", [])
            if len(c) >= 2: city_points[(p.get("ciudad"), p.get("estado"))] = (float(c[0]), float(c[1]))
    need = [c for c in wanted if c not in city_points]
    if need:
        if not capturar_fuentes:
            raise RuntimeError(f"Faltan coordenadas geográficas cacheadas: {len(need)}")
        geo_result = _geocode(city_points, need)
        city_features = []
        for (city, state), (lon, lat) in sorted(city_points.items()):
            source_feature = next((f for f in geo_result["features"]
                                   if f["properties"]["ciudad"] == city and f["properties"]["estado"] == state), None)
            props = source_feature["properties"] if source_feature else {"ciudad": city, "estado": state,
                       "fuente": "OpenStreetMap Nominatim", "nota": "coordenada previa cacheada"}
            city_features.append({"type": "Feature", "properties": props,
                                  "geometry": {"type": "Point", "coordinates": [lon, lat]}})
        geo_file.parent.mkdir(parents=True, exist_ok=True)
        geo_file.write_text(json.dumps({"type": "FeatureCollection", "features": city_features}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        location_meta = str(geo_result["bronze"])
    elif not geo_file.is_file():
        raise RuntimeError("No se dispone de coordenadas de ciudad para los mercados SNIIM")
    state_files = _latest_state_files(bronze)
    required_states = {f"{i:02d}" for i in range(1, 33)}
    missing_states = sorted(required_states - state_files.keys())
    if missing_states and capturar_fuentes:
        settings = get_settings(); run_id = new_run_id(); ext = INEGIMarcoExtractor(settings)
        manifest = Manifest(run_id, "inegi_marco", "mapa-mercados", "local",
                            parametros={"entidades": missing_states, "producto": "Marco Geoestadístico estatal"})
        writer = BronzeWriter(settings.bronze_dir)
        for code in missing_states:
            try:
                cap = ext.fetch_estado(code); saved = writer.write(cap, run_id)
                manifest.add_archivo(saved.ruta, saved.sha256, cap.url, saved.bytes,
                                     base=settings.data_dir.parent if settings.data_dir.parent in saved.ruta.parents else None)
                manifest.add_consulta({"cve_ent": code, "nombre": cap.metadatos.get("nombre_entidad")}, "ok", cap.registros, saved.ruta.name)
                state_files[code] = saved.ruta
                print(f"INEGI {code} {cap.metadatos.get('nombre_entidad')}: geometría archivada", flush=True)
            except Exception as exc:
                manifest.add_consulta({"cve_ent": code}, "fallida", error=f"{type(exc).__name__}: {exc}")
                raise
        manifest.solicitudes = ext.stats["solicitudes"]
        manifest.finalizar().save(settings.bronze_dir / "inegi_marco/manifests")
    if missing_states and not capturar_fuentes:
        raise RuntimeError(f"Faltan geometrías estatales INEGI: {len(missing_states)}")
    state_features = []
    for code, path in sorted(state_files.items()):
        meta = json.loads(path.with_name(path.name + ".meta.json").read_text(encoding="utf-8"))["metadatos_captura"]
        fc = json.loads(path.read_text(encoding="utf-8"))
        for feature in fc.get("features", []):
            state_features.append({"type": "Feature", "properties": {"cve_ent": code,
                                 "nombre": feature.get("properties", {}).get("nomgeo", meta.get("nombre_entidad")),
                                 "fuente": "INEGI · Marco Geoestadístico 2025"},
                                  "geometry": _simplificar(feature["geometry"])})
    city_by = city_points
    quote_counts = {str(c["mercado_id"]): int(c.get("filas", 0)) for c in report["capturas"]}
    market_features = []
    for key in market_ids:
        city, state = CITY_BY_MARKET[key]
        lon, lat = city_by[(city, state)]
        market_features.append({"type": "Feature", "properties": {"mercado_id": key, "mercado": markets[key],
                                "ciudad": city, "estado": state, "con_cotizaciones": quote_counts.get(key, 0) > 0,
                                "num_cotizaciones": quote_counts.get(key, 0), "fecha_corte": report["fechas_observadas"][-1] if report["fechas_observadas"] else None,
                                "precision": "coordenada del centro de ciudad; no del local comercial"},
                               "geometry": {"type": "Point", "coordinates": [lon, lat]}})
    out = {"type": "FeatureCollection", "properties": {"esquema": "oaic-mapa-mercados/1",
           "fuente_geometria": "INEGI · Marco Geoestadístico estatal 2025",
           "fuente_ciudades": "OpenStreetMap contributors · Nominatim",
           "fecha_corte_precios": report["fechas_observadas"][-1] if report["fechas_observadas"] else None,
           "nota": "Los límites estatales sirven como referencia cartográfica. Los puntos ubican el centro aproximado de la ciudad, no el inmueble exacto del mercado."},
           "features": state_features + market_features}
    out_path = BASE_DIR / "data/publico/mapa_mercados_sniim.geojson"
    out_path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"estados": len(state_features), "mercados": len(market_features),
            "mercados_con_precio": sum(f["properties"]["con_cotizaciones"] for f in market_features),
            "archivo": str(out_path), "coordenadas_bronce": location_meta}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo-procesar", action="store_true", help="No realiza llamadas externas; usa Bronce y caché")
    args = parser.parse_args(argv)
    print(json.dumps(preparar(not args.solo_procesar), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
