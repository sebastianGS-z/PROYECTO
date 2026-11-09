"""Configuración centralizada del sistema TDL.

Todos los parámetros salen de aquí: variables de entorno (o archivo ``.env``),
con valores por defecto seguros. No hay rutas absolutas dependientes de la máquina.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import timedelta, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

#: Colima usa UTC-6 todo el año desde 2022 (México eliminó el horario de verano).
COLIMA_TZ = timezone(timedelta(hours=-6), "UTC-6")

DEFAULT_USER_AGENT = "TDL-Observatorio/1.0 (proyecto academico; contacto: equipo@correo.mx)"


def _load_dotenv(path: Path) -> None:
    """Carga pares CLAVE=valor de ``.env`` sin pisar variables ya definidas."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    """Parámetros de ejecución inmutables."""

    user_agent: str
    timeout: float
    max_retries: int
    backoff_base: float
    min_delay: float
    data_dir: Path
    log_dir: Path
    log_level: str
    sniim_base_url: str
    noaa_ncei_url: str
    bitacora_path: Path

    @property
    def bronze_dir(self) -> Path:
        return self.data_dir / "bronce"

    @property
    def diagnostic_dir(self) -> Path:
        return self.data_dir / "diagnostico"

    @property
    def synthetic_dir(self) -> Path:
        return self.data_dir / "sintetico"


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else BASE_DIR / p


def get_settings() -> Settings:
    """Construye la configuración leyendo entorno y ``.env`` en cada llamada."""
    _load_dotenv(BASE_DIR / ".env")
    env = os.environ.get
    return Settings(
        user_agent=env("TDL_USER_AGENT", DEFAULT_USER_AGENT),
        timeout=float(env("TDL_TIMEOUT", "30")),
        max_retries=int(env("TDL_MAX_RETRIES", "3")),
        backoff_base=float(env("TDL_BACKOFF_BASE", "1.0")),
        min_delay=float(env("TDL_MIN_DELAY", "1.5")),
        data_dir=_path(env("TDL_DATA_DIR", "data")),
        log_dir=_path(env("TDL_LOG_DIR", "logs")),
        log_level=env("TDL_LOG_LEVEL", "INFO").upper(),
        sniim_base_url=env("TDL_SNIIM_BASE_URL", "https://www.economia-sniim.gob.mx").rstrip("/"),
        noaa_ncei_url=env("TDL_NOAA_NCEI_URL", "https://www.ncei.noaa.gov/access/services/data/v1"),
        bitacora_path=_path(env("TDL_BITACORA", "calidad/bitacora_capturas.csv")),
    )


def cargar_localidades(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Devuelve las localidades climáticas indexadas por id."""
    data = json.loads((path or CONFIG_DIR / "localidades.json").read_text(encoding="utf-8"))
    return {loc["id"]: loc for loc in data["localidades"]}


def cargar_fuentes(path: Path | None = None) -> dict[str, Any]:
    """Devuelve la configuración de fuentes (productos, mercados, variables)."""
    return json.loads((path or CONFIG_DIR / "fuentes.json").read_text(encoding="utf-8"))


def setup_logging(run_id: str, settings: Settings | None = None) -> Path:
    """Configura logging a consola y a ``logs/captura_<run_id>.log``; devuelve la ruta del log."""
    settings = settings or get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = settings.log_dir / f"captura_{run_id}.log"
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.setLevel(getattr(logging, settings.log_level, logging.INFO))
    fmt = logging.Formatter("%(asctime)sZ %(levelname)s [%(name)s] %(message)s", "%Y-%m-%dT%H:%M:%S")
    fmt.converter = __import__("time").gmtime
    for handler in (logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")):
        handler.setFormatter(fmt)
        root.addHandler(handler)
    return log_path
