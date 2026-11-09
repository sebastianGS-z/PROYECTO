"""Manifiesto de captura por ejecución y fuente (evidencia verificable)."""
from __future__ import annotations

import csv
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("tdl.manifest")

EXITOSA, PARCIAL, SIN_RESULTADOS, FALLIDA = "exitosa", "parcial", "sin_resultados", "fallida"


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]


def derive_status(consultas: list[dict[str, Any]]) -> str:
    """Estado final a partir de las consultas; una falla nunca se oculta como éxito."""
    # Pasos auxiliares correctos (p. ej. descargar el formulario) no cuentan como datos obtenidos.
    consultas = [c for c in consultas if not (c.get("paso") and c["estado"] == "ok")]
    if not consultas:
        return SIN_RESULTADOS
    cuenta = {k: sum(c["estado"] == k for c in consultas) for k in ("ok", "sin_resultados", "parcial", "fallida")}
    total = len(consultas)
    if cuenta["fallida"] == total:
        return FALLIDA
    if cuenta["fallida"] or cuenta["parcial"]:
        return PARCIAL
    if cuenta["ok"] == 0:
        return SIN_RESULTADOS
    return EXITOSA


@dataclass
class Manifest:
    run_id: str
    fuente: str
    modo: str  # diaria | historica
    disparador: str = "local"
    inicio: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    fin: str | None = None
    duracion_s: float | None = None
    estado: str | None = None
    solicitudes: int = 0
    registros: int = 0
    consultas: list[dict[str, Any]] = field(default_factory=list)
    archivos: list[dict[str, Any]] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    parametros: dict[str, Any] = field(default_factory=dict)
    _t0: datetime = field(default_factory=lambda: datetime.now(timezone.utc), repr=False)

    def add_consulta(self, clave: dict[str, Any], estado: str, registros: int = 0,
                     archivo: str | None = None, error: str | None = None, advertencias: list[str] | None = None) -> None:
        self.consultas.append({**clave, "estado": estado, "registros": registros, "archivo": archivo,
                               "error": error, "advertencias": advertencias or []})
        self.registros += registros
        if error:
            self.errores.append(f"{clave}: {error}")

    def add_archivo(self, ruta: Path, sha256: str, url: str, tamano: int, base: Path | None = None) -> None:
        rel = ruta.relative_to(base).as_posix() if base else ruta.as_posix()
        self.archivos.append({"ruta": rel, "sha256": sha256, "url": url, "bytes": tamano})

    def finalizar(self) -> "Manifest":
        ahora = datetime.now(timezone.utc)
        self.fin = ahora.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.duracion_s = round((ahora - self._t0).total_seconds(), 2)
        self.estado = derive_status(self.consultas)
        return self

    def to_dict(self) -> dict[str, Any]:
        d = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        d["esquema"] = "tdl-manifest/1"
        d["archivos_generados"] = len(self.archivos)
        return d

    def save(self, manifests_dir: Path) -> Path:
        manifests_dir.mkdir(parents=True, exist_ok=True)
        ruta = manifests_dir / f"manifest_{self.run_id}.json"
        with open(ruta, "xb") as fh:  # inmutable: nunca se reescribe un manifiesto
            fh.write(json.dumps(self.to_dict(), ensure_ascii=False, indent=2).encode("utf-8"))
        log.info("Manifiesto %s (estado=%s, registros=%d, archivos=%d)", ruta.name, self.estado, self.registros, len(self.archivos))
        return ruta


BITACORA_COLUMNAS = ["run_id", "fuente", "modo", "disparador", "inicio_utc", "fin_utc", "duracion_s",
                     "estado", "solicitudes", "registros", "archivos", "errores", "primer_error"]


def append_bitacora(path: Path, m: Manifest) -> None:
    """Agrega una fila a la bitácora de ejecuciones (evidencia para fiabilidad: MTBF, MTTR, disponibilidad)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not path.exists() or path.stat().st_size == 0
    primer = (m.errores[0] if m.errores else "").replace("\n", " ")[:200]
    with path.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if nuevo:
            w.writerow(BITACORA_COLUMNAS)
        w.writerow([m.run_id, m.fuente, m.modo, m.disparador, m.inicio, m.fin, m.duracion_s, m.estado,
                    m.solicitudes, m.registros, len(m.archivos), len(m.errores), primer])
