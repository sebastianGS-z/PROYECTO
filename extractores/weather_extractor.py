"""Extractor climático: NOAA NCEI, Access Data Service v1 (GHCN-Daily, estaciones reales).

Se descartaron por robots.txt (consultado el 2026-11-09): Open-Meteo (``Disallow: /``) y
NASA POWER (``Disallow: /api/``). La regla del proyecto: si un sitio lo prohíbe, se busca otra fuente.

Variables diarias (units=metric): TAVG, TMAX, TMIN (°C) y PRCP (mm). Los días/variables sin dato
no aparecen en la respuesta; nunca se rellenan ni se convierten a cero.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from config.settings import cargar_fuentes
from extractores.base import BaseExtractor, RawCapture, StructureChangedError

MODO_DIARIO = "diario"


class WeatherExtractor(BaseExtractor):
    fuente = "noaa_ncei"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cfg = cargar_fuentes()["noaa_ncei"]
        self.variables: list[str] = cfg["variables_diarias"]
        self.dataset: str = cfg["dataset"]
        self.unidades: str = cfg["unidades"]

    def fetch(self, localidad: dict[str, Any], inicio: date, fin: date, modo: str = MODO_DIARIO) -> RawCapture:
        """Consulta la estación de una localidad en [inicio, fin] y devuelve la captura cruda."""
        if fin < inicio:
            raise ValueError("fin no puede ser anterior a inicio")
        params = [
            ("dataset", self.dataset), ("stations", localidad["estacion"]),
            ("startDate", inicio.isoformat()), ("endDate", fin.isoformat()),
            ("dataTypes", ",".join(self.variables)), ("units", self.unidades), ("format", "json"),
        ]
        resp = self.get(self.settings.noaa_ncei_url, params=params)
        payload = self.parse_json(resp)
        registros, advertencias = self.validar_estructura(payload, inicio, fin)
        return RawCapture(
            fuente=self.fuente, url=resp.url, contenido=resp.content, formato="json",
            http_status=resp.status_code, registros=registros,
            estado="ok" if registros else "sin_resultados", advertencias=advertencias,
            metadatos={
                "etiqueta": f"{localidad['id']}-{modo}",
                "localidad": localidad["nombre"], "localidad_id": localidad["id"], "estacion": localidad["estacion"],
                "latitud": localidad["latitud"], "longitud": localidad["longitud"],
                "fecha_ref_inicio": inicio.isoformat(), "fecha_ref_fin": fin.isoformat(),
                "modo": modo, "parametros": dict(params),
                "unidades": "TAVG/TMAX/TMIN en °C, PRCP en mm (units=metric)",
            },
        )

    def validar_estructura(self, payload: Any, inicio: date, fin: date) -> tuple[int, list[str]]:
        """Valida el JSON; devuelve (días con al menos una variable, advertencias)."""
        if not isinstance(payload, list) or any(not isinstance(r, dict) or "DATE" not in r for r in payload):
            raise StructureChangedError("El JSON de NCEI no es una lista de registros con 'DATE'")
        con_dato = [r for r in payload if any(v in r and r[v] not in ("", None) for v in self.variables)]
        advertencias: list[str] = []
        for var in self.variables:
            n = sum(1 for r in con_dato if r.get(var) not in (None, ""))
            if con_dato and n < len(con_dato):
                advertencias.append(f"{var}: presente en {n} de {len(con_dato)} días (los ausentes no se rellenan)")
        esperados = (fin - inicio).days + 1
        if payload and len(payload) != esperados:
            advertencias.append(f"Se esperaban {esperados} días y la fuente devolvió {len(payload)}")
        if not payload:
            advertencias.append("La fuente devolvió una lista vacía (sin datos para la estación y fechas)")
        return len(con_dato), advertencias
