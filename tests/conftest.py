"""Utilidades de prueba: sesión HTTP falsa, reloj falso y configuración aislada.

IMPORTANTE: todo el contenido de estas pruebas es FIXTURE controlado (no son capturas reales).
"""
from __future__ import annotations

from dataclasses import replace

import pytest
import requests

from config.settings import get_settings
from extractores import base


class FakeResponse:
    def __init__(self, status: int = 200, content: bytes | str = b"", url: str = "", headers: dict | None = None) -> None:
        self.status_code = status
        self.content = content.encode("utf-8") if isinstance(content, str) else content
        self.url = url
        self.headers = headers or {}

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


class FakeSession:
    """Sesión falsa: ``rutas`` mapea fragmento de URL → lista de respuestas/excepciones (se consumen en orden)."""

    def __init__(self, rutas: dict[str, list]) -> None:
        self.rutas = {k: list(v) for k, v in rutas.items()}
        self.headers: dict[str, str] = {}
        self.llamadas: list[tuple[str, str]] = []

    def request(self, method: str, url: str, timeout: float | None = None, **kw):
        self.llamadas.append((method, url))
        for fragmento, cola in self.rutas.items():
            if fragmento in url:
                item = cola.pop(0) if len(cola) > 1 else cola[0]
                if isinstance(item, Exception):
                    raise item
                item.url = url
                return item
        return FakeResponse(404, b"no ruta", url)


ROBOTS_OK = FakeResponse(200, "User-agent: *\nDisallow: /privado\n")


@pytest.fixture(autouse=True)
def reloj(monkeypatch):
    """Reloj y sleep falsos: las pruebas no esperan de verdad y registran las pausas."""
    estado = {"t": 1000.0, "pausas": []}
    monkeypatch.setattr(base, "_monotonic", lambda: estado["t"])

    def dormir(s: float) -> None:
        estado["pausas"].append(s)
        estado["t"] += s

    monkeypatch.setattr(base, "_sleep", dormir)
    base.BaseExtractor.reset_shared_state()
    yield estado
    base.BaseExtractor.reset_shared_state()


@pytest.fixture
def settings(tmp_path):
    return replace(get_settings(), data_dir=tmp_path / "data", log_dir=tmp_path / "logs", bitacora_path=tmp_path / "bitacora.csv",
                   max_retries=2, backoff_base=1.0, min_delay=1.5)
