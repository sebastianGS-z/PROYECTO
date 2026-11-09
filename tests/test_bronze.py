import hashlib
import json
import os
import stat
from pathlib import Path

import pytest

from almacenamiento.bronze_writer import BronzeWriter, META_SUFFIX, sha256_file, slug, verificar_archivo
from almacenamiento.manifest import (EXITOSA, FALLIDA, PARCIAL, SIN_RESULTADOS, Manifest, derive_status, new_run_id)
from extractores.base import RawCapture


def captura(contenido=b'{"daily":{"time":["2025-01-01"]}}', **meta):
    return RawCapture(fuente="noaa_ncei", url="https://x/api?a=1", contenido=contenido, formato="json",
                      http_status=200, registros=1, estado="ok", fecha_captura="2026-11-08T10:00:00Z",
                      metadatos={"etiqueta": "Tecomán-archive", "localidad": "Tecomán",
                                 "fecha_ref_inicio": "2025-01-01", "fecha_ref_fin": "2025-01-31", **meta})


def test_slug():
    assert slug("Plátano Tabasco — Primera") == "platano-tabasco-primera"


def test_escribe_original_intacto_y_organiza_por_anio_mes(tmp_path):
    cap = captura()
    bf = BronzeWriter(tmp_path).write(cap, "RUN1")
    assert bf.ruta.read_bytes() == cap.contenido  # original sin modificar
    assert bf.ruta.parent == tmp_path / "noaa_ncei" / "2025" / "01"
    assert bf.ruta.name.startswith("noaa_ncei__tecoman-archive__2025-01-01_2025-01-31__RUN1")


def test_hash_sha256_correcto(tmp_path):
    cap = captura()
    bf = BronzeWriter(tmp_path).write(cap, "RUN1")
    assert bf.sha256 == hashlib.sha256(cap.contenido).hexdigest() == sha256_file(bf.ruta)


def test_metadatos_separados_del_original(tmp_path):
    bf = BronzeWriter(tmp_path).write(captura(), "RUN1")
    meta = json.loads(bf.ruta_meta.read_text(encoding="utf-8"))
    m = meta["metadatos_captura"]
    for campo in ("fecha_captura", "fuente_url", "fuente", "identificador_ejecucion", "formato_original", "sha256", "localidad", "fecha_ref_inicio"):
        assert campo in m
    assert m["identificador_ejecucion"] == "RUN1" and "contenido_original" in meta
    assert b"identificador_ejecucion" not in bf.ruta.read_bytes()


def test_inmutabilidad_no_sobrescribe(tmp_path, caplog):
    w = BronzeWriter(tmp_path)
    primero = w.write(captura(b'{"v":1}'), "RUN1")
    segundo = w.write(captura(b'{"v":2}'), "RUN1")  # mismo nombre
    assert primero.ruta != segundo.ruta and segundo.colision is True and primero.colision is False
    assert primero.ruta.read_bytes() == b'{"v":1}'  # el original sigue intacto
    assert "no se sobrescribe" in caplog.text


def test_archivo_solo_lectura(tmp_path):
    bf = BronzeWriter(tmp_path).write(captura(), "RUN1")
    if os.name != "nt":
        assert not os.stat(bf.ruta).st_mode & stat.S_IWUSR


def test_verificacion_detecta_alteracion(tmp_path):
    bf = BronzeWriter(tmp_path).write(captura(), "RUN1")
    assert verificar_archivo(bf.ruta_meta) == (True, "ok")
    os.chmod(bf.ruta, 0o644)
    bf.ruta.write_bytes(b"alterado")
    ok, msg = verificar_archivo(bf.ruta_meta)
    assert not ok and "hash distinto" in msg


def test_verificacion_detecta_archivo_faltante(tmp_path):
    bf = BronzeWriter(tmp_path).write(captura(), "RUN1")
    os.chmod(bf.ruta, 0o644); bf.ruta.unlink()
    assert verificar_archivo(bf.ruta_meta)[0] is False


# ------------------------------------------------------------------ manifiestos
def test_estados_derivados():
    c = lambda e: {"estado": e}
    assert derive_status([]) == SIN_RESULTADOS
    assert derive_status([c("ok"), c("sin_resultados")]) == EXITOSA
    assert derive_status([c("sin_resultados")]) == SIN_RESULTADOS
    assert derive_status([c("ok"), c("fallida")]) == PARCIAL
    assert derive_status([c("ok"), c("parcial")]) == PARCIAL
    assert derive_status([c("fallida"), c("fallida")]) == FALLIDA


def test_manifiesto_contenido_y_unico(tmp_path):
    bf = BronzeWriter(tmp_path / "bronce").write(captura(), "RUN1")
    m = Manifest("RUN1", "noaa_ncei", "diaria")
    m.add_archivo(bf.ruta, bf.sha256, "https://x", bf.bytes, base=tmp_path)
    m.add_consulta({"localidad": "tecoman"}, "ok", 1, bf.ruta.name)
    m.add_consulta({"localidad": "colima"}, "fallida", error="HTTP 500")
    m.finalizar()
    ruta = m.save(tmp_path / "bronce" / "noaa_ncei" / "manifests")
    d = json.loads(ruta.read_text(encoding="utf-8"))
    assert d["estado"] == "parcial" and d["registros"] == 1 and d["archivos_generados"] == 1
    assert d["archivos"][0]["sha256"] == bf.sha256 and d["errores"] and d["duracion_s"] is not None
    with pytest.raises(FileExistsError):
        m.save(tmp_path / "bronce" / "noaa_ncei" / "manifests")  # no se reescribe


def test_run_id_unico():
    assert new_run_id() != new_run_id()
