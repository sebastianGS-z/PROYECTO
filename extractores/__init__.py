"""Extractores de fuentes de datos (capa de transporte HTTP + extracción)."""
from extractores.base import (  # noqa: F401
    BaseExtractor,
    EmptyResponseError,
    ExtractorError,
    HttpError,
    RawCapture,
    RequestFailed,
    RobotsDisallowed,
    RobotsUnavailable,
    StructureChangedError,
)
