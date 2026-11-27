"""Pruebas de la integración geoespacial E2 y de la CLI, con GeoJSON FIXTURE (no son polígonos oficiales)."""
from __future__ import annotations

import json

import pandas as pd
import pytest

import main as cli
from almacenamiento.bronze_writer import BronzeWriter
from extractores.base import RawCapture
from scripts import captura_historica
from src.tdl_e2 import geoespacial as e2


def _poligono(x0, y0, d=0.2):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]]}


def _geojson(features):
    return json.dumps({"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                       "features": features}).encode("utf-8")


MUNICIPIOS = [
    # Manzanillo contiene la estación MXM00076654 (19.05, -104.317) configurada en localidades.json
    {"type": "Feature", "properties": {"cvegeo": "06007", "cve_ent": "06", "cve_mun": "007", "nomgeo": "Manzanillo"}, "geometry": _poligono(-104.4, 18.95)},
    {"type": "Feature", "properties": {"cvegeo": "06009", "cve_ent": "06", "cve_mun": "009", "nomgeo": "Tecomán"}, "geometry": _poligono(-103.9, 18.8)},
    {"type": "Feature", "properties": {"cvegeo": "06001", "cve_ent": "06", "cve_mun": "001", "nomgeo": "Armería"}, "geometry": _poligono(-104.1, 18.8)},
]


def _guardar(bronze, etiqueta, run_id, features):
    cap = RawCapture(fuente="inegi_marco", url="https://fixture.invalid/geo", contenido=_geojson(features), formato="geojson",
                     http_status=200, registros=len(features), estado="ok",
                     metadatos={"etiqueta": etiqueta, "fecha_ref_inicio": "2026-11-20", "fecha_ref_fin": "2026-11-20"})
    return BronzeWriter(bronze).write(cap, run_id).ruta


@pytest.fixture
def bronze(tmp_path):
    b = tmp_path / "bronce"
    _guardar(b, "marco-municipal-colima", "20261120T110000Z-aaaaaa", MUNICIPIOS)
    # Un polígono estatal más reciente NO debe confundirse con la capa municipal (regresión 2026-11-27)
    estado = [{"type": "Feature", "properties": {"cvegeo": "32", "cve_ent": "32", "nomgeo": "Zacatecas"}, "geometry": _poligono(-102, 23)}]
    _guardar(b, "marco-estatal-32", "20261127T040000Z-bbbbbb", estado)
    return b


def test_latest_geojson_ignora_poligonos_estatales(bronze):
    path, _, digest = e2._latest_geojson(bronze)
    assert "marco-municipal-colima" in path.name and len(digest) == 64


def test_procesar_genera_plata_oro_mapa_y_asigna_estacion(bronze, tmp_path):
    out = tmp_path / "data"
    reporte = e2.procesar(bronze, out, tmp_path / "mapa.png")
    assert reporte["municipios"] == 3
    assert reporte["estaciones"][0]["municipio_cvegeo"] == "06007"
    oro = pd.read_csv(out / "oro" / "contexto_geoespacial_municipal.csv")
    assert len(oro) == 3 and oro["source_sha256"].str.len().eq(64).all()
    assert (tmp_path / "mapa.png").stat().st_size > 0
    assert (out / "plata" / "reporte_geoespacial_e2.json").is_file()


def test_procesar_rechaza_hash_alterado(bronze, tmp_path):
    path, _, _ = e2._latest_geojson(bronze)
    path.chmod(0o644)
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA-256"):
        e2.procesar(bronze, tmp_path / "data", tmp_path / "m.png")


def test_sin_capa_municipal_falla(tmp_path):
    with pytest.raises(FileNotFoundError):
        e2._latest_geojson(tmp_path)


def test_fetch_estado_valida_clave(settings):
    ext = e2.INEGIMarcoExtractor(settings)
    for clave in ("1", "33", "ab"):
        with pytest.raises(ValueError):
            ext.fetch_estado(clave)


# --- CLI -----------------------------------------------------------------------------------------

def test_cli_ayuda_y_comando_desconocido(capsys):
    assert cli.main([]) == 0 and "python main.py" in capsys.readouterr().out
    assert cli.main(["no-existe"]) == 2


def test_cli_objetivos_sin_datos(capsys):
    assert cli.main(["objetivos", "--desde", "1999-01-01", "--hasta", "1999-01-02"]) == 0
    assert json.loads(capsys.readouterr().out)


def test_historica_dry_run_no_hace_red(capsys):
    assert captura_historica.main(["--dry-run", "--inicio", "2024-01-01", "--fin", "2024-12-31"]) == 0
    assert "12 periodos" in capsys.readouterr().out
