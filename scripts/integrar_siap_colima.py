"""Integra el cierre municipal agrícola del SIAP con el marco municipal INEGI.

El archivo SIAP original se conserva en Bronce. La salida es contexto de oferta
histórica, no inventario disponible ni pronóstico de cosecha actual.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _colima_por_anio(siap: Path) -> pd.DataFrame:
    """Lee un cierre anual SIAP original y devuelve el agregado municipal de Colima con su linaje."""
    source_sha = _sha(siap)
    df = pd.read_csv(siap, encoding="cp1252", low_memory=False)
    # Los cierres 2016–2020 nombran la columna "Nomcultivo Sin Um"; se normaliza al leer (Bronce no cambia).
    if "Nomcultivo" not in df.columns and "Nomcultivo Sin Um" in df.columns:
        df = df.rename(columns={"Nomcultivo Sin Um": "Nomcultivo"})
    required = {"Anio", "Idestado", "Nomestado", "Idmunicipio", "Nommunicipio",
                "Nomunidad", "Nomcultivo", "Sembrada", "Cosechada", "Volumenproduccion",
                "Valorproduccion"}
    if not required.issubset(df.columns):
        raise ValueError(f"El archivo SIAP no contiene campos requeridos: {sorted(required-set(df.columns))}")
    df = df[(pd.to_numeric(df.Idestado, errors="coerce") == 6) & df.Nomestado.eq("Colima")].copy()
    if df.empty:
        raise ValueError("No se localizaron registros municipales del estado de Colima")
    df["municipio_cvegeo"] = "06" + pd.to_numeric(df.Idmunicipio, errors="raise").astype(int).astype(str).str.zfill(3)
    numeric = ["Sembrada", "Cosechada", "Volumenproduccion", "Valorproduccion"]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    # Conserva unidad en la clave de agrupación; no suma unidades incompatibles.
    grouped = df.groupby(["Anio", "municipio_cvegeo", "Nommunicipio", "Nomcultivo", "Nomunidad"],
                         as_index=False).agg(
        superficie_sembrada_ha=("Sembrada", "sum"),
        superficie_cosechada_ha=("Cosechada", "sum"),
        volumen_produccion=("Volumenproduccion", "sum"),
        valor_produccion_mxn=("Valorproduccion", "sum"),
    )
    grouped["precio_medio_rural_mxn_unidad"] = grouped.valor_produccion_mxn.div(
        grouped.volumen_produccion.where(grouped.volumen_produccion.ne(0)))
    grouped["fuente"] = "SIAP · Cierre de la Producción Agrícola municipal"
    grouped["archivo_bronce"] = siap.resolve().relative_to(ROOT).as_posix()
    grouped["sha256_bronce"] = source_sha
    grouped["limitacion"] = "Producción anual cosechada; no representa inventario actual, oferta exportable ni productor individual."
    grouped.attrs["unidades"] = sorted(df.Nomunidad.dropna().astype(str).unique())
    return grouped


def integrar(archivos: list[Path] | Path, marco: Path | None = None) -> dict:
    """Integra uno o varios cierres anuales; si hay varias capturas del mismo año gana la más reciente."""
    archivos = [archivos] if isinstance(archivos, Path) else list(archivos)
    por_anio: dict[int, pd.DataFrame] = {}
    for siap in sorted(archivos, key=lambda p: p.name.rsplit("__", 1)[-1]):
        g = _colima_por_anio(siap)
        por_anio[int(g["Anio"].max())] = g
    grouped = pd.concat(por_anio.values(), ignore_index=True).sort_values(["Anio", "municipio_cvegeo", "Nomcultivo"])
    units = sorted({u for g in por_anio.values() for u in g.attrs.get("unidades", [])})
    ultimo = grouped[grouped["Anio"].eq(grouped["Anio"].max())]
    source_sha = str(ultimo["sha256_bronce"].iloc[0])
    public = ROOT / "data" / "publico"
    public.mkdir(parents=True, exist_ok=True)
    gold = ROOT / "data" / "oro"
    gold.mkdir(parents=True, exist_ok=True)
    out = gold / "produccion_municipal_siap_colima.csv"
    grouped.to_csv(out, index=False, encoding="utf-8")
    grouped.to_csv(public / "produccion_municipal_siap_colima.csv", index=False, encoding="utf-8")

    if marco is None:
        choices = sorted(glob.glob(str(ROOT / "data/bronce/inegi_marco/**/*.geojson"), recursive=True))
        if not choices:
            raise FileNotFoundError("Falta Marco Geoestadístico INEGI en Bronce")
        marco = Path(choices[-1])
    gdf = gpd.read_file(marco)
    if gdf.crs is None or not {"cvegeo", "nomgeo"}.issubset(gdf.columns):
        raise ValueError("El marco INEGI no contiene geometría CRS, cvegeo y nomgeo")
    gdf = gdf.to_crs("EPSG:4326")
    gdf["cvegeo"] = gdf.cvegeo.astype(str).str.zfill(5)
    gdf = gdf.merge(ultimo, left_on="cvegeo", right_on="municipio_cvegeo", how="left")  # el mapa muestra el último año
    # Una geometría por cultivo y municipio para que el cliente filtre la capa.
    cols = ["cvegeo", "nomgeo", "Anio", "Nomcultivo", "Nomunidad", "superficie_sembrada_ha",
            "superficie_cosechada_ha", "volumen_produccion", "valor_produccion_mxn",
            "precio_medio_rural_mxn_unidad", "fuente", "archivo_bronce", "sha256_bronce", "limitacion", "geometry"]
    geo = gdf[[c for c in cols if c in gdf.columns]].dropna(subset=["Nomcultivo"]).copy()
    geo_path = public / "produccion_municipal_colima.geojson"
    geo.to_file(geo_path, driver="GeoJSON")
    report = {"fuente": "SIAP", "anio": int(grouped.Anio.max()), "anios": sorted(int(a) for a in por_anio), "registros_colima": len(grouped),
              "cultivos": sorted(grouped.Nomcultivo.unique().tolist()), "unidades": units,
              "archivo_bronce": str(ultimo.archivo_bronce.iloc[0]), "sha256_bronce": source_sha,
              "marco_geoestadistico": marco.resolve().relative_to(ROOT).as_posix(),
              "limitacion": "Los municipios señalan producción histórica anual; no se interpretan como disponibilidad en tiempo real ni coordenadas de predios."}
    (public / "reporte_produccion_siap.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"anios": sorted(int(a) for a in por_anio), "registros": len(grouped), "cultivos": len(report["cultivos"]), "municipios": int(geo.cvegeo.nunique()),
            "csv": str(out), "geojson": str(geo_path), "sha256": source_sha}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archivo", nargs="?", help="CSV SIAP original municipal; por defecto busca el último en Bronce")
    a = p.parse_args(argv)
    files = [Path(a.archivo)] if a.archivo else [Path(x) for x in sorted(glob.glob(str(ROOT / "data/bronce/siap/**/*.csv"), recursive=True))]
    if not files:
        raise SystemExit("No existe captura SIAP en Bronce. Descargue el cierre municipal oficial y consérvelo allí antes de procesar.")
    print(json.dumps(integrar(files), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
