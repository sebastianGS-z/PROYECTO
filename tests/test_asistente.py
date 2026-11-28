"""Pruebas de los datos del asistente de venta y del directorio DENUE (datos FIXTURE, sin red)."""
from __future__ import annotations

import io
import json
import zipfile

import pandas as pd

from scripts import capturar_denue as cd
from src.inteligencia import asistente as asi

COLUMNAS = ["ID", "CLEE", "NOM_ESTAB", "RAZ_SOCIAL", "CODIGO_ACT", "NOMBRE_ACT", "PER_OCU", "TIPOCENCOM", "NOM_CENCOM", "ENTIDAD", "MUNICIPIO",
            "TELEFONO", "CORREOELEC", "WWW", "LATITUD", "LONGITUD", "FECHA_ALTA"]


def _fila(clee, nombre, razon, codigo, personal, tel="3131234567", correo=None, central=None):
    return [clee, clee, nombre, razon, codigo, "x", personal, central, "Central" if central else None, "COLIMA", "Tecomán", tel, correo, None, "18.9", "-103.9", "2024-05"]


def _denue(tmp_path):
    filas = [
        _fila("A", "LIMONERA DEL VALLE", "LIMONERA SA DE CV", "115113", "11 a 30 personas"),            # empacadora con razón social
        _fila("B", "FRUTAS PEPE", None, "431130", "0 a 5 personas"),                                       # micro sin razón social: fuera (privacidad)
        _fila("C", "BODEGA 12", None, "431130", "6 a 10 personas", central="CENTRAL DE ABASTO"),          # mayorista en central
        _fila("D", "ABARROTES CHICO", "ABC SA", "431110", "11 a 30 personas"),                             # abarrotes no grande: fuera
        _fila("E", "SUPER GRANDE", "SG SA", "462111", "251 y más personas", tel=None, correo="compras@sg.mx"),
        _fila("F", "TALLER MECANICO", "TM SA", "811111", "11 a 30 personas"),                              # otra actividad: fuera
        _fila("G", "SIN CONTACTO", "SC SA", "431130", "11 a 30 personas", tel=None),                       # cuenta para demanda, no se lista
    ]
    csv = pd.DataFrame(filas, columns=COLUMNAS).to_csv(index=False).encode("latin-1")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("conjunto_de_datos/denue_inegi_06_.csv", csv)
        z.writestr("diccionario_de_datos/denue_diccionario_de_datos.csv", "x")
    carpeta = tmp_path / "data/bronce/denue/2026/11"
    carpeta.mkdir(parents=True)
    ruta = carpeta / "denue__denue-06-colima__2026-11-28_2026-11-28__20261128T000000Z-x.zip"
    ruta.write_bytes(buf.getvalue())
    (carpeta / (ruta.name + ".meta.json")).write_text(json.dumps({"fecha_captura": "2026-11-28T00:00:00Z", "metadatos": {"estado_clave": "06"}}), encoding="utf-8")


def test_directorio_solo_empresas_compradoras_con_contacto(tmp_path):
    _denue(tmp_path)
    assert set(cd.zips(tmp_path / "data/bronce")) == {"06"}
    lista, dem = asi.compradores(tmp_path)
    ids = {x["id"] for x in lista}
    assert ids == {"A", "C", "E"}
    c = next(x for x in lista if x["id"] == "C")
    assert c["central"] and c["cat"] == "mayorista" and c["tel"] == "3131234567" and c["estado"] == "Colima"
    assert next(x for x in lista if x["id"] == "E")["correo"] == "compras@sg.mx"
    # la señal de demanda cuenta también las empresas sin contacto público
    assert dem["por_estado"]["Colima"] == {"empacadora": 1, "mayorista": 2, "supermercado": 1}
    assert dem["fecha_descarga"] == "2026-11-28"


def test_telefono_y_estado_normalizados():
    assert asi._telefono("(313) 123-4567") == "3131234567"
    assert asi._telefono("52 313 123 4567") == "3131234567"
    assert asi._telefono("1234") is None and asi._telefono(float("nan")) is None
    assert asi._estado("MICHOACÁN DE OCAMPO") == "Michoacán" and asi._estado("CIUDAD DE MÉXICO") == "Ciudad de México"


def test_centroide_ignora_islas():
    isla = [[[-114.7, 18.3], [-114.6, 18.3], [-114.6, 18.4], [-114.7, 18.3]]]
    continente = [[[-103.9, 18.9], [-103.7, 18.9], [-103.7, 19.0], [-103.9, 19.0], [-103.9, 18.9]]]
    lat, lon = asi._centroide({"type": "MultiPolygon", "coordinates": [isla, continente]})
    assert -104 < lon < -103.6 and 18.8 < lat < 19.1


def test_paquete_publicado_es_coherente_con_el_observatorio():
    """Los JSON del asistente publicados en el repositorio: cifras iguales a las del observatorio."""
    from config.settings import BASE_DIR

    d = BASE_DIR / asi.SALIDA
    base = json.loads((d / "base.json").read_text(encoding="utf-8"))
    assert len(base["frutas"]) == 10 and len(base["municipios"]) == 10
    tecoman = next(m for m in base["municipios"] if m["nombre"] == "Tecomán")
    assert 200 < tecoman["km"]["140"] < 320  # Tecomán → Guadalajara por carretera ≈ 260 km
    limon = json.loads((d / "fruta_limon.json").read_text(encoding="utf-8"))
    pron = pd.read_csv(BASE_DIR / "data/publico/pronosticos_colima.csv")
    p1 = pron[pron["cultivo"].eq("limon") & pron["horizonte_meses"].eq(1)].iloc[0]
    assert round(float(p1["precio_frecuente_mxn_kg"]), 2) == limon["pronostico"][0]["precio"]
    assert len(limon["respuestas"]) == 17
    comp = json.loads((d / "compradores.json").read_text(encoding="utf-8"))
    assert "DENUE" in comp["fuente"] and all(x["tel"] or x["correo"] or x["www"] for x in comp["empresas"])
    assert all(x["razon"] or not str(x["personal"]).startswith("0 a 5") for x in comp["empresas"])


def test_sin_zips_conserva_el_directorio_publicado(tmp_path):
    out = tmp_path / asi.SALIDA
    out.mkdir(parents=True)
    (out / "compradores.json").write_text(json.dumps({"empresas": [{"id": "X", "tel": "3130000000"}], "por_estado": {"Colima": {"mayorista": 1}},
                                                     "fecha_descarga": "2026-11-28"}), encoding="utf-8")
    res = asi.ejecutar(tmp_path)
    assert res["compradores"] == 1
    assert json.loads((out / "compradores.json").read_text(encoding="utf-8"))["empresas"][0]["id"] == "X"
