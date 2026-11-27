"""Prueba de extremo a extremo de la puerta de calidad E1 con Bronce FIXTURE (no son capturas reales).

Se generan capturas SNIIM y NOAA con sesiones HTTP falsas, se ejecuta Bronce → Plata → Oro y se
verifica que: la puerta acepta lo válido, cuarentena lo alterado (hash distinto) con motivo, Oro
conserva linaje y los reportes de calidad se materializan.
"""
from __future__ import annotations

import json
from datetime import date

import pandas as pd
import pytest

from extractores.sniim_extractor import SniimExtractor
from extractores.weather_extractor import WeatherExtractor
from pipeline import capturar_clima, capturar_sniim
from src.tdl_e1 import pipeline as e1
from tests.conftest import FakeResponse, FakeSession
from tests.test_sniim import FORM, RESULTADOS
from tests.test_weather import RUTA, payload


def _bronce(settings):
    s = FakeSession({"robots.txt": [FakeResponse(404, b"x")], "ConsultaFrutasYHortalizas.aspx": [FakeResponse(200, FORM)],
                     "ResultadosConsulta": [FakeResponse(200, RESULTADOS)]})
    m1 = capturar_sniim("RUNE1", "diaria", [(date(2025, 1, 1), date(2025, 1, 31))], settings,
                        productos=["platano"], mercados=["guadalajara"], extractor=SniimExtractor(settings, session=s))
    w = FakeSession({"robots.txt": [FakeResponse(404, b"x")], RUTA: [FakeResponse(200, json.dumps(payload(10)))]})
    m2 = capturar_clima("RUNE2", "diaria", date(2025, 1, 1), date(2025, 1, 10), settings,
                        extractor=WeatherExtractor(settings, session=w))
    assert m1.estado == "exitosa" and m2.estado == "exitosa"
    return settings.bronze_dir


@pytest.fixture
def corrida(settings, tmp_path):
    bronze = _bronce(settings)
    data_dir = tmp_path / "salida"
    reporte = e1.ejecutar(bronze, data_dir)
    return bronze, data_dir, reporte


def test_ejecutar_materializa_plata_oro_y_reportes(corrida):
    _, data_dir, reporte = corrida
    assert reporte["registros_bronce_parseados"] > 0
    assert reporte["registros_plata_validos"] == reporte["registros_bronce_parseados"]
    assert reporte["registros_cuarentena"] == 0
    for rel in ("plata/precios_clima.csv", "plata/clima_modelado.csv", "oro/panel_mensual.csv",
                "cuarentena/registros_invalidos.csv", "plata/conflictos_resueltos.csv",
                "plata/reporte_calidad.json", "plata/diagnostico_faltantes.json"):
        assert (data_dir / rel).is_file(), rel
    oro = pd.read_csv(data_dir / "oro" / "panel_mensual.csv")
    assert len(oro) == reporte["filas_oro"] > 0
    assert oro["linaje_precios_bronce"].notna().all()
    assert reporte["linaje_oro"]


def test_plata_conserva_originales_y_agrega_derivadas(corrida):
    _, data_dir, _ = corrida
    plata = pd.read_csv(data_dir / "plata" / "precios_clima.csv")
    assert set(plata["tipo_registro"]) == {"precio", "clima"}
    assert plata["source_sha256"].str.len().eq(64).all()
    # la precipitación no se imputa: los nulos del origen siguen siendo nulos
    clima = plata[plata["tipo_registro"].eq("clima")]
    assert clima["prcp_mm"].notna().sum() == 10
    assert clima["tavg_c"].notna().sum() == 1


def test_hash_alterado_va_a_cuarentena_con_motivo(settings, tmp_path):
    bronze = _bronce(settings)
    html = next(p for p in bronze.rglob("*.html") if "platano" in p.name)
    html.chmod(0o644)  # Bronce se escribe en solo lectura; la prueba simula una alteración externa
    html.write_bytes(html.read_bytes() + b"<!-- alterado -->")
    reporte = e1.ejecutar(bronze, tmp_path / "salida")
    assert reporte["registros_cuarentena"] >= 1
    cuarentena = pd.read_csv(tmp_path / "salida" / "cuarentena" / "registros_invalidos.csv")
    assert cuarentena["motivo"].str.contains("SHA|sha|hash", regex=True).any()


def test_bronce_vacio_falla_explicitamente(tmp_path):
    (tmp_path / "bronce").mkdir()
    with pytest.raises(RuntimeError):
        e1.ejecutar(tmp_path / "bronce", tmp_path / "salida")
    assert e1.main(["--bronze-dir", str(tmp_path / "bronce"), "--data-dir", str(tmp_path / "salida")]) == 1


def test_main_imprime_resumen(settings, tmp_path, capsys):
    bronze = _bronce(settings)
    assert e1.main(["--bronze-dir", str(bronze), "--data-dir", str(tmp_path / "salida")]) == 0
    resumen = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert resumen["filas_oro"] > 0


@pytest.mark.parametrize("valor, esperado", [("1,234.50", 1234.5), ("$ 12", 12.0), ("12,5", 12.5), ("", None), (None, None), ("N/D", None)])
def test_number_tolera_formatos(valor, esperado):
    assert e1._number(valor) == esperado


@pytest.mark.parametrize("valor", ["abc", "inf"])
def test_number_rechaza_texto_y_no_finitos(valor):
    with pytest.raises(ValueError):
        e1._number(valor)


@pytest.mark.parametrize("etiqueta, kg", [("Kilogramo", 1.0), ("Caja de 18 kg.", 18.0), ("Arpilla de 19 kg.", 19.0), ("Pieza", None)])
def test_peso_presentacion(etiqueta, kg):
    assert e1._peso_presentacion_kg(etiqueta)[0] == kg
