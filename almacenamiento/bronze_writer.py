"""Escritor de la Capa Bronce: contenido original intacto + metadatos separados.

Cada captura produce dos archivos hermanos:
    <nombre>.<ext>        bytes originales, exactamente como los entregó la fuente
    <nombre>.<ext>.meta.json   metadatos técnicos añadidos por el sistema (incluye SHA-256)
Política de inmutabilidad: los archivos se crean en modo exclusivo ("xb"); nunca se sobrescriben.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from extractores.base import RawCapture

log = logging.getLogger("tdl.bronce")
META_SUFFIX = ".meta.json"


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "x"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for bloque in iter(lambda: fh.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


@dataclass
class BronzeFile:
    ruta: Path
    ruta_meta: Path
    sha256: str
    bytes: int
    colision: bool


class BronzeWriter:
    def __init__(self, bronze_dir: Path) -> None:
        self.bronze_dir = Path(bronze_dir)

    def _carpeta(self, cap: RawCapture) -> Path:
        ref = cap.metadatos.get("fecha_ref_inicio") or cap.fecha_captura[:10]
        anio, mes = ref[:4], ref[5:7]
        return self.bronze_dir / cap.fuente / anio / mes

    def _nombre(self, cap: RawCapture, run_id: str) -> str:
        ini = cap.metadatos.get("fecha_ref_inicio", cap.fecha_captura[:10])
        fin = cap.metadatos.get("fecha_ref_fin", ini)
        etiqueta = slug(str(cap.metadatos.get("etiqueta", "captura")))[:90]
        return f"{cap.fuente}__{etiqueta}__{ini}_{fin}__{run_id}"

    def write(self, cap: RawCapture, run_id: str) -> BronzeFile:
        carpeta = self._carpeta(cap)
        carpeta.mkdir(parents=True, exist_ok=True)
        base = self._nombre(cap, run_id)
        ext = cap.formato
        colision, version = False, 1
        while True:
            sufijo = "" if version == 1 else f"__v{version}"
            ruta = carpeta / f"{base}{sufijo}.{ext}"
            try:
                with open(ruta, "xb") as fh:
                    fh.write(cap.contenido)
                break
            except FileExistsError:
                colision, version = True, version + 1
                log.warning("Ya existe %s; no se sobrescribe, se genera nueva versión v%d", ruta.name, version)
        digest = cap.sha256
        meta = {
            "esquema": "tdl-bronce-meta/1",
            "contenido_original": {
                "archivo": ruta.name,
                "descripcion": "Bytes tal como los entregó la fuente; no se modifican.",
            },
            "metadatos_captura": {
                "fuente": cap.fuente, "fuente_url": cap.url, "fecha_captura": cap.fecha_captura,
                "identificador_ejecucion": run_id, "formato_original": cap.formato,
                "sha256": digest, "bytes": len(cap.contenido), "http_status": cap.http_status,
                "registros_detectados": cap.registros, "estado_captura": cap.estado,
                "advertencias": cap.advertencias, "colision_nombre": colision,
                **cap.metadatos,
            },
        }
        ruta_meta = ruta.with_name(ruta.name + META_SUFFIX)
        with open(ruta_meta, "xb") as fh:
            fh.write(json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"))
        for p in (ruta, ruta_meta):
            try:
                os.chmod(p, 0o444)
            except OSError:  # p. ej. sistemas de archivos sin permisos POSIX
                pass
        log.info("Bronce: %s (%d bytes, sha256=%s…)", ruta, len(cap.contenido), digest[:12])
        return BronzeFile(ruta, ruta_meta, digest, len(cap.contenido), colision)


def verificar_archivo(ruta_meta: Path) -> tuple[bool, str]:
    """Recalcula el SHA-256 del contenido y lo compara con el registrado en el sidecar."""
    try:
        meta = json.loads(Path(ruta_meta).read_text(encoding="utf-8"))
        esperado = meta["metadatos_captura"]["sha256"]
        archivo = Path(ruta_meta).with_name(meta["contenido_original"]["archivo"])
    except (OSError, ValueError, KeyError) as exc:
        return False, f"metadatos ilegibles: {exc}"
    if not archivo.is_file():
        return False, f"falta el archivo {archivo.name}"
    real = sha256_file(archivo)
    if real != esperado:
        return False, f"hash distinto en {archivo.name}: esperado {esperado[:12]}… real {real[:12]}…"
    return True, "ok"
