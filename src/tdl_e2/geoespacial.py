"""Captura y procesamiento del Marco Geoestadístico municipal de Colima."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from almacenamiento.bronze_writer import BronzeWriter, sha256_file
from almacenamiento.manifest import Manifest, append_bitacora, new_run_id
from config.settings import BASE_DIR, get_settings
from extractores.base import BaseExtractor, RawCapture

LOG = logging.getLogger("tdl.e2")
ENDPOINT = "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/06"


class INEGIMarcoExtractor(BaseExtractor):
    fuente = "inegi_marco"

    def fetch_colima(self) -> RawCapture:
        response = self.get(ENDPOINT, headers={"Accept": "application/geo+json, application/json"})
        payload = self.parse_json(response)
        if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
            raise ValueError("Respuesta del Marco Geoestadístico no es FeatureCollection GeoJSON")
        if not payload["features"]:
            raise ValueError("El servicio del INEGI devolvió una colección sin municipios")
        return RawCapture(
            fuente=self.fuente, url=response.url, contenido=response.content, formato="geojson",
            http_status=response.status_code, registros=len(payload["features"]), estado="ok",
            metadatos={"etiqueta": "marco-municipal-colima", "cve_ent": "06",
                       "nombre_entidad": "Colima", "producto": "Marco Geoestadístico municipal",
                       "edicion_geometria": payload.get("metadatos", {}).get("Fuente_informacion_vectorial"),
                       "edicion_atributos": payload.get("metadatos", {}).get("Fuente_informacion_estadistica"),
                       "fecha_ref_inicio": datetime.now(timezone.utc).date().isoformat(),
                       "fecha_ref_fin": datetime.now(timezone.utc).date().isoformat()},
        )

    def fetch_estado(self, clave: str) -> RawCapture:
        """Captura la geometría oficial de un estado para mapas nacionales de mercados."""
        if not clave.isdigit() or len(clave) != 2 or not 1 <= int(clave) <= 32:
            raise ValueError(f"Clave de entidad INEGI inválida: {clave!r}")
        endpoint = f"https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgee/{clave}"
        response = self.get(endpoint, headers={"Accept": "application/geo+json, application/json"})
        payload = self.parse_json(response)
        if payload.get("type") != "FeatureCollection" or not payload.get("features"):
            raise ValueError(f"El INEGI no devolvió el polígono estatal {clave}")
        name = str(payload["features"][0].get("properties", {}).get("nomgeo", clave))
        return RawCapture(fuente=self.fuente, url=response.url, contenido=response.content,
                          formato="geojson", http_status=response.status_code,
                          registros=len(payload["features"]), estado="ok",
                          metadatos={"etiqueta": f"marco-estatal-{clave}", "tipo": "marco-estatal",
                                     "cve_ent": clave, "nombre_entidad": name,
                                     "producto": "Marco Geoestadístico estatal",
                                     "edicion_geometria": payload.get("metadatos", {}).get("Fuente_informacion_vectorial"),
                                     "fecha_ref_inicio": datetime.now(timezone.utc).date().isoformat(),
                                     "fecha_ref_fin": datetime.now(timezone.utc).date().isoformat()})


def capturar(settings=None) -> tuple[Path, str]:
    settings = settings or get_settings()
    run_id = new_run_id()
    ext = INEGIMarcoExtractor(settings)
    manifest = Manifest(run_id, ext.fuente, "e2", "local o GitHub Actions",
                        parametros={"endpoint": ENDPOINT, "entidad": "06", "unidad": "municipios"})
    try:
        cap = ext.fetch_colima()
        saved = BronzeWriter(settings.bronze_dir).write(cap, run_id)
        manifest.add_archivo(saved.ruta, saved.sha256, cap.url, saved.bytes,
                              base=settings.data_dir.parent if settings.data_dir.parent in saved.ruta.parents else None)
        manifest.add_consulta({"entidad": "06", "producto": "Marco Geoestadístico municipal"}, "ok",
                              cap.registros, saved.ruta.name)
        path = saved.ruta
    except Exception as exc:
        manifest.add_consulta({"entidad": "06", "producto": "Marco Geoestadístico municipal"},
                              "fallida", error=f"{type(exc).__name__}: {exc}")
        manifest.solicitudes = ext.stats["solicitudes"]
        manifest.finalizar().save(settings.bronze_dir / ext.fuente / "manifests")
        append_bitacora(settings.bitacora_path, manifest)
        raise
    manifest.solicitudes = ext.stats["solicitudes"]
    manifest.finalizar().save(settings.bronze_dir / ext.fuente / "manifests")
    append_bitacora(settings.bitacora_path, manifest)
    return path, cap.fecha_captura


def _rel(path: Path) -> str:
    """Ruta relativa al repositorio cuando es posible (reproducible); absoluta si está fuera."""
    resolved = Path(path).resolve()
    return resolved.relative_to(BASE_DIR).as_posix() if resolved.is_relative_to(BASE_DIR) else str(resolved)


def _latest_geojson(bronze_dir: Path) -> tuple[Path, dict[str, Any], str]:
    # Solo la capa municipal de Colima: los polígonos estatales (marco-estatal-XX) comparten carpeta
    # y no deben confundirse con ella. Se ordena por nombre (incluye el run_id con fecha UTC), no por mtime,
    # que cambia al clonar el repositorio.
    files = sorted((bronze_dir / "inegi_marco").rglob("*__marco-municipal-colima__*.geojson"), key=lambda p: p.name.rsplit("__", 1)[-1])
    if not files:
        raise FileNotFoundError("No hay GeoJSON del Marco Geoestadístico en Bronce; ejecute primero la captura E2")
    path = files[-1]
    sidecar = path.with_name(path.name + ".meta.json")
    if not sidecar.is_file():
        raise ValueError(f"Falta el sidecar de trazabilidad: {sidecar}")
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))["metadatos_captura"]
    digest = sha256_file(path)
    if digest != metadata.get("sha256"):
        raise ValueError(f"SHA-256 no coincide para {path}")
    return path, metadata, digest


def procesar(bronze_dir: Path, data_dir: Path, mapa_path: Path | None = None) -> dict[str, Any]:
    """Valida origen, proyecta polígonos, localiza estaciones y produce mapa/tabla."""
    source_path, md, digest = _latest_geojson(bronze_dir)
    frame = gpd.read_file(source_path)
    if frame.empty or frame.crs is None:
        raise ValueError("GeoJSON vacío o sin CRS explícito; se rechaza para evitar ubicaciones incorrectas")
    frame["registro_bronce"] = [f"features[{index}]" for index in range(len(frame))]
    frame = frame.to_crs("EPSG:4326")
    if "cve_ent" not in frame.columns or "nomgeo" not in frame.columns:
        raise ValueError("La capa del INEGI cambió: faltan cve_ent o nomgeo")
    frame["cve_ent"] = frame["cve_ent"].astype(str).str.zfill(2)
    frame = frame.loc[frame["cve_ent"].eq("06")].copy()
    if frame.empty:
        raise ValueError("La capa recibida no contiene municipios de Colima (cve_ent=06)")
    # Nombres/códigos auditados contra el catálogo oficial; referencias de centroides
    # se usan solo para visualizar la zona de estudio, no como coordenadas censales.
    zonas = {"Tecomán": "06009", "Armería": "06001", "Manzanillo": "06007"}
    frame["zona_observatorio"] = frame["cvegeo"].astype(str).isin(zonas.values())
    frame["superficie_km2_aprox"] = frame.to_crs("EPSG:32613").geometry.area / 1_000_000

    localidades_path = BASE_DIR / "config" / "localidades.json"
    localidades = json.loads(localidades_path.read_text(encoding="utf-8"))["localidades"]
    stations = []
    for loc in localidades:
        point = Point(float(loc["longitud"]), float(loc["latitud"]))
        containing = frame.loc[frame.geometry.covers(point)]
        if containing.empty:
            stations.append({"estacion": loc["estacion"], "localidad_fuente": loc["nombre"],
                             "municipio_cvegeo": None, "municipio": None,
                             "estado": "fuera_de_poligonos_recibidos"})
        else:
            row = containing.iloc[0]
            stations.append({"estacion": loc["estacion"], "localidad_fuente": loc["nombre"],
                             "municipio_cvegeo": str(row["cvegeo"]), "municipio": str(row["nomgeo"]),
                             "estado": "asignacion_punto_en_poligono"})
    for station in stations:
        if station["municipio_cvegeo"] is None:
            continue
        station_mask = frame["cvegeo"].astype(str).eq(station["municipio_cvegeo"])
        frame["estacion_noaa"] = station_mask
        frame["id_estacion_noaa"] = None
        frame.loc[station_mask, "id_estacion_noaa"] = station["estacion"]

    columns = [c for c in ("cvegeo", "cve_ent", "cve_mun", "nomgeo", "cve_cab", "nom_cab",
                            "pob_total", "pob_femenina", "pob_masculina", "total_viviendas_habitadas",
                            "zona_observatorio", "superficie_km2_aprox", "estacion_noaa", "id_estacion_noaa",
                            "registro_bronce")
               if c in frame.columns]
    tabular = pd.DataFrame(frame[columns].drop(columns="geometry", errors="ignore"))
    tabular["fuente_geoespacial"] = "INEGI Marco Geoestadístico municipal"
    tabular["version_geometria"] = str(md.get("edicion_geometria") or "no informada")
    tabular["version_atributos"] = str(md.get("edicion_atributos") or "no informada")
    tabular["source_file"] = _rel(source_path)
    tabular["source_sha256"] = digest
    tabular["fecha_ingesta_utc"] = md.get("fecha_captura", "")
    silver_path = data_dir / "plata" / "marco_geoestadistico_colima.csv"
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    tabular.to_csv(silver_path, index=False, encoding="utf-8", na_rep="")

    gold = tabular.copy()
    gold["capa"] = "oro_contexto_geoespacial_municipal"
    gold_path = data_dir / "oro" / "contexto_geoespacial_municipal.csv"
    gold_path.parent.mkdir(parents=True, exist_ok=True)
    gold.to_csv(gold_path, index=False, encoding="utf-8", na_rep="")

    mapa_path = mapa_path or BASE_DIR / "docs" / "E2" / "mapa_marco_geoestadistico_colima.png"
    mapa_path.parent.mkdir(parents=True, exist_ok=True)
    report_path = data_dir / "plata" / "reporte_geoespacial_e2.json"
    report = {
        "esquema": "tdl-e2-geoespacial/1", "generado_utc": datetime.now(timezone.utc).isoformat(),
        "fuente": "INEGI Marco Geoestadístico municipal", "endpoint": md.get("fuente_url"),
        "edicion_geometria": md.get("edicion_geometria"), "edicion_atributos": md.get("edicion_atributos"),
        "registros_geojson": int(len(gpd.read_file(source_path))), "municipios_colima": int(len(gold)),
        "crs_salida": "EPSG:4326", "crs_superficie": "EPSG:32613",
        "bronce": {"archivo": tabular["source_file"].iloc[0], "sha256": digest,
                   "fecha_ingesta_utc": md.get("fecha_captura"),
                   "registros": "GeoJSON FeatureCollection.features[n]"},
        "asignacion_estacion": stations,
        "productos": {"plata_csv": _rel(silver_path), "oro_csv": _rel(gold_path), "mapa": _rel(mapa_path)},
        "nota": "Los límites y población municipal se entregan como dimensión separada; no se asocian directamente a mercados mayoristas fuera de Colima.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 9))
    frame.plot(ax=ax, color="#e8eef4", edgecolor="#526477", linewidth=0.7)
    focus = frame.loc[frame["zona_observatorio"]]
    if not focus.empty:
        focus.plot(ax=ax, color="#76b7a5", edgecolor="#20584a", linewidth=1.1)
        for _, row in focus.iterrows():
            center = row.geometry.representative_point()
            offsets = {"Manzanillo": (-0.045, 0.035), "Armería": (0.045, 0.015), "Tecomán": (0.025, -0.035)}
            dx, dy = offsets.get(str(row["nomgeo"]), (0.02, 0.02))
            ax.annotate(str(row["nomgeo"]), (center.x + dx, center.y + dy), ha="center", va="center", fontsize=8,
                        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.8})
    for loc in localidades:
        ax.scatter(loc["longitud"], loc["latitud"], marker="*", s=140, color="#c63d2f", edgecolor="white", linewidth=0.7,
                   label=f"Estación NOAA {loc['estacion']}")
    if localidades:
        ax.legend(loc="lower left", frameon=True)
    # El endpoint también incluye Revillagigedo; se enfoca el mapa en el territorio
    # continental donde están las localidades de estudio.
    ax.set_xlim(-104.65, -103.45)
    ax.set_ylim(18.65, 19.55)
    ax.set_title("Marco Geoestadístico municipal de Colima\nZonas del observatorio y estación meteorológica")
    ax.set_axis_off()
    fig.text(0.5, 0.025, "Fuente: INEGI, Marco Geoestadístico (ver metadatos); estación: NOAA GHCN-Daily. Elaboración propia con GeoPandas.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(mapa_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"municipios": len(gold), "estaciones": stations, "source_file": tabular["source_file"].iloc[0],
            "source_sha256": digest, "fecha_ingesta_utc": md.get("fecha_captura"),
            "plata_csv": str(silver_path), "oro_csv": str(gold_path), "reporte": str(report_path),
            "mapa": str(mapa_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo-procesar", action="store_true", help="No descargar; reprocesar GeoJSON ya guardado en Bronce")
    args = parser.parse_args(argv)
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        if not args.solo_procesar:
            path, captured = capturar(settings)
            LOG.info("INEGI guardado en Bronce: %s (ingesta %s)", path, captured)
        from src.tdl_e1.pipeline import ejecutar as ejecutar_e1
        report = ejecutar_e1(settings.bronze_dir, settings.data_dir)
        LOG.info("Pipeline integrado Bronce-Plata-Oro: %s", json.dumps(
            {k: report[k] for k in ("registros_plata_validos", "filas_oro")}, ensure_ascii=False))
        result = procesar(settings.bronze_dir, settings.data_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        LOG.exception("Integración geoespacial E2 fallida: %s", exc)
        print(f"ERROR E2: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
