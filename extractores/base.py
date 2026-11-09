"""Clase base de extractores: transporte HTTP ético y reutilizable.

Responsabilidades: sesión Requests, User-Agent, robots.txt (fallo cerrado),
Crawl-delay, pausa mínima por dominio compartida entre instancias, reintentos con
backoff exponencial, timeout, validación de respuestas y logging.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib import robotparser
from urllib.parse import urlsplit

import requests

from config.settings import Settings, get_settings

RETRY_STATUS = {429, 500, 502, 503, 504}


def _monotonic() -> float:
    return time.monotonic()


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


# ---------------------------------------------------------------- excepciones
class ExtractorError(Exception):
    """Error base de extracción."""


class RobotsDisallowed(ExtractorError):
    """robots.txt no permite la URL solicitada."""


class RobotsUnavailable(ExtractorError):
    """No se pudo verificar robots.txt: política conservadora, no se hace scraping."""


class HttpError(ExtractorError):
    """Respuesta HTTP de error no recuperable."""

    def __init__(self, url: str, status: int, detalle: str = "") -> None:
        super().__init__(f"HTTP {status} en {url} {detalle}".strip())
        self.url, self.status = url, status


class RequestFailed(ExtractorError):
    """Se agotaron los reintentos (errores de conexión, timeout o HTTP transitorio)."""


class EmptyResponseError(ExtractorError):
    """La respuesta llegó vacía o sin contenido útil."""


class StructureChangedError(ExtractorError):
    """La estructura de la respuesta no corresponde con la esperada."""


# --------------------------------------------------------------------- datos
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class RawCapture:
    """Contenido crudo recibido de una fuente + metadatos técnicos de captura.

    ``contenido`` son los bytes originales sin modificar; ``metadatos`` y el resto de
    campos son añadidos por el sistema y se guardan separados del original.
    """

    fuente: str
    url: str
    contenido: bytes
    formato: str
    http_status: int
    registros: int
    estado: str  # ok | sin_resultados | parcial
    fecha_captura: str = field(default_factory=utc_now_iso)
    metadatos: dict[str, Any] = field(default_factory=dict)
    advertencias: list[str] = field(default_factory=list)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.contenido).hexdigest()


@dataclass
class _RobotsEntry:
    parser: robotparser.RobotFileParser | None
    allow_all: bool = False
    deny_all: bool = False

    def crawl_delay(self, ua: str) -> float | None:
        if self.parser is None:
            return None
        delay = self.parser.crawl_delay(ua)
        return float(delay) if delay is not None else None


# ----------------------------------------------------------------- extractor
class BaseExtractor:
    """Transporte HTTP común. Los extractores concretos heredan de esta clase."""

    fuente = "base"

    # Estado compartido entre TODAS las instancias (pausa por dominio y robots).
    _state_lock = threading.Lock()
    _domain_locks: dict[str, threading.Lock] = {}
    _last_request: dict[str, float] = {}
    _crawl_delays: dict[str, float] = {}
    _robots: dict[str, _RobotsEntry] = {}

    def __init__(self, settings: Settings | None = None, session: requests.Session | None = None) -> None:
        self.settings = settings or get_settings()
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": self.settings.user_agent})
        self.log = logging.getLogger(f"tdl.{self.fuente}")
        self.stats = {"solicitudes": 0, "reintentos": 0, "errores": 0}

    # -- estado compartido ----------------------------------------------
    @classmethod
    def reset_shared_state(cls) -> None:
        with cls._state_lock:
            cls._domain_locks.clear()
            cls._last_request.clear()
            cls._crawl_delays.clear()
            cls._robots.clear()

    @classmethod
    def _domain_lock(cls, domain: str) -> threading.Lock:
        with cls._state_lock:
            return cls._domain_locks.setdefault(domain, threading.Lock())

    def _respect_delay(self, domain: str) -> None:
        required = max(self.settings.min_delay, self._crawl_delays.get(domain, 0.0))
        last = self._last_request.get(domain)
        if last is None:
            return
        wait = required - (_monotonic() - last)
        if wait > 0:
            self.log.debug("Pausa de %.2fs antes de consultar %s", wait, domain)
            _sleep(wait)

    # -- robots.txt -------------------------------------------------------
    def _robots_entry(self, url: str) -> _RobotsEntry:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        with self._state_lock:
            cached = self._robots.get(origin)
        if cached is not None:
            return cached
        robots_url = f"{origin}/robots.txt"
        try:
            resp = self._http("GET", robots_url)
        except HttpError as exc:
            if exc.status == 404:
                entry = _RobotsEntry(None, allow_all=True)
                self.log.info("robots.txt no existe en %s (404): sin restricciones declaradas", origin)
            elif exc.status in (401, 403):
                entry = _RobotsEntry(None, deny_all=True)
                self.log.warning("robots.txt de %s devolvió %s: se trata como acceso denegado", origin, exc.status)
            else:
                raise RobotsUnavailable(f"No se pudo verificar robots.txt de {origin}: {exc}") from exc
        except RequestFailed as exc:
            raise RobotsUnavailable(f"No se pudo verificar robots.txt de {origin}: {exc}") from exc
        else:
            rp = robotparser.RobotFileParser()
            rp.parse(resp.text.splitlines())
            entry = _RobotsEntry(rp)
            delay = entry.crawl_delay(self.settings.user_agent)
            if delay:
                with self._state_lock:
                    self._crawl_delays[parts.netloc] = delay
                self.log.info("Crawl-delay de %s: %.1fs", origin, delay)
        with self._state_lock:
            self._robots[origin] = entry
        return entry

    def can_fetch(self, url: str) -> bool:
        """True solo si robots.txt permite ``url`` para nuestro User-Agent."""
        entry = self._robots_entry(url)
        if entry.deny_all:
            return False
        if entry.allow_all or entry.parser is None:
            return True
        return entry.parser.can_fetch(self.settings.user_agent, url)

    # -- HTTP ---------------------------------------------------------------
    def _send_once(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        domain = urlsplit(url).netloc
        with self._domain_lock(domain):
            self._respect_delay(domain)
            self.stats["solicitudes"] += 1
            try:
                return self.session.request(method, url, timeout=self.settings.timeout, **kwargs)
            finally:
                self._last_request[domain] = _monotonic()

    def _http(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Solicitud con reintentos y backoff exponencial (sin verificar robots)."""
        attempts = self.settings.max_retries + 1
        last_error = ""
        for attempt in range(1, attempts + 1):
            try:
                resp = self._send_once(method, url, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                self.log.warning("Intento %d/%d falló (%s) en %s", attempt, attempts, last_error, url)
            else:
                status = resp.status_code
                if status < 400:
                    return resp
                body = (resp.text or "")[:200].replace("\n", " ")
                if status not in RETRY_STATUS:
                    self.stats["errores"] += 1
                    raise HttpError(url, status, body)
                last_error = f"HTTP {status}"
                self.log.warning("Intento %d/%d recibió HTTP %s en %s", attempt, attempts, status, url)
            if attempt < attempts:
                self.stats["reintentos"] += 1
                _sleep(self.settings.backoff_base * (2 ** (attempt - 1)))
        self.stats["errores"] += 1
        raise RequestFailed(f"Agotados {attempts} intentos para {url}: {last_error}")

    def request(self, method: str, url: str, params: Any = None, **kwargs: Any) -> requests.Response:
        """Solicitud pública: robots.txt → pausa → reintentos → validación."""
        final_url = requests.Request(method, url, params=params).prepare().url or url
        if not self.can_fetch(final_url):
            raise RobotsDisallowed(f"robots.txt no permite {final_url}")
        resp = self._http(method, final_url, **kwargs)
        self.validate_response(resp)
        self.log.info("%s %s -> %s (%d bytes)", method, final_url, resp.status_code, len(resp.content or b""))
        return resp

    def get(self, url: str, params: Any = None, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, params=params, **kwargs)

    # -- validación -----------------------------------------------------------
    @staticmethod
    def validate_response(resp: requests.Response) -> None:
        if not resp.content or not resp.content.strip():
            raise EmptyResponseError(f"Respuesta vacía de {resp.url}")

    @staticmethod
    def parse_json(resp: requests.Response) -> Any:
        try:
            return json.loads(resp.content.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise StructureChangedError(f"JSON inválido desde {resp.url}: {exc}") from exc
