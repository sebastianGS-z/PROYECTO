"""Orquestación: conecta extractores → escritor Bronce → manifiesto → estado final."""
from __future__ import annotations

import calendar
import json
import logging
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from almacenamiento.bronze_writer import BronzeWriter
from almacenamiento.manifest import Manifest, append_bitacora
from config.settings import Settings, cargar_fuentes, cargar_localidades
from extractores.base import BaseExtractor, ExtractorError, RobotsDisallowed, RobotsUnavailable
from extractores.sniim_extractor import SniimExtractor
from extractores.weather_extractor import MODO_DIARIO, WeatherExtractor

log = logging.getLogger("tdl.pipeline")


def disparador() -> str:
    return os.environ.get("GITHUB_EVENT_NAME", "local")


def meses(inicio: date, fin: date) -> list[tuple[date, date]]:
    """Divide [inicio, fin] en periodos mensuales (el primero y el último se recortan)."""
    out, actual = [], date(inicio.year, inicio.month, 1)
    while actual <= fin:
        ultimo = date(actual.year, actual.month, calendar.monthrange(actual.year, actual.month)[1])
        out.append((max(actual, inicio), min(ultimo, fin)))
        actual = ultimo + timedelta(days=1)
    return out


def ultimos_36_meses(hoy: date | None = None) -> tuple[date, date]:
    """36 meses calendario completos que terminan el mes anterior al actual."""
    hoy = hoy or date.today()
    fin = date(hoy.year, hoy.month, 1) - timedelta(days=1)
    m = fin.year * 12 + fin.month - 1 - 35
    return date(m // 12, m % 12 + 1, 1), fin


def _resolver(fuentes: dict[str, Any], productos: list[str] | None, mercados: list[str] | None,
              incluir_opcionales: bool) -> tuple[list[dict], list[dict]]:
    cfg = fuentes["sniim"]
    prods = [p for p in cfg["productos"] if not productos or p["clave"] in productos]
    if mercados:
        mers = [m for m in cfg["mercados"] + cfg["mercados_opcionales"] if m["clave"] in mercados]
    else:
        mers = cfg["mercados"] + (cfg["mercados_opcionales"] if incluir_opcionales else [])
    if not prods or not mers:
        raise ValueError("La selección de productos/mercados quedó vacía; revise config/fuentes.json")
    return prods, mers


def capturar_sniim(run_id: str, modo: str, periodos: list[tuple[date, date]], settings: Settings,
                   productos: list[str] | None = None, mercados: list[str] | None = None,
                   incluir_opcionales: bool = False, extractor: SniimExtractor | None = None,
                   max_consultas: int | None = None) -> Manifest:
    fuentes = cargar_fuentes()
    ext = extractor or SniimExtractor(settings, precios_por=fuentes["sniim"].get("precios_por", "presentacion"))
    writer = BronzeWriter(settings.bronze_dir)
    prods, mers = _resolver(fuentes, productos, mercados, incluir_opcionales)
    man = Manifest(run_id, "sniim", modo, disparador(),
                   parametros={"productos": [p["clave"] for p in prods], "mercados": [m["clave"] for m in mers],
                               "periodos": [[a.isoformat(), b.isoformat()] for a, b in periodos]})
    hechas = 0
    try:
        cat_ok = True
        try:
            ext.cargar_catalogo()
        except RobotsDisallowed as exc:
            raise
        except ExtractorError as exc:
            man.add_consulta({"paso": "catalogo_formulario"}, "fallida", error=str(exc))
            log.error("No se pudo cargar el catálogo del formulario SNIIM: %s", exc)
            cat_ok = False
        if cat_ok and ext.formulario_captura is not None:
            _guardar(man, writer, ext.formulario_captura, run_id, settings, {"paso": "catalogo_formulario"})
        for prod in (prods if cat_ok else []):
            try:
                variantes = ext.variantes(prod["busqueda"])
            except ExtractorError as exc:
                man.add_consulta({"producto_clave": prod["clave"], "paso": "variantes"}, "fallida", error=str(exc))
                continue
            for var in variantes:
                for mer in mers:
                    for ini, fin in periodos:
                        if max_consultas is not None and hechas >= max_consultas:
                            raise StopIteration
                        hechas += 1
                        clave = {"producto_clave": prod["clave"], "producto": var.etiqueta, "mercado_clave": mer["clave"],
                                 "inicio": ini.isoformat(), "fin": fin.isoformat()}
                        try:
                            cap = ext.fetch_precios(var, mer["etiqueta_formulario"], ini, fin)
                        except (RobotsDisallowed, RobotsUnavailable):
                            raise
                        except ExtractorError as exc:
                            log.error("Consulta fallida %s: %s", clave, exc)
                            _diagnostico(settings, run_id, clave, exc)
                            man.add_consulta(clave, "fallida", error=f"{type(exc).__name__}: {exc}")
                            continue
                        _guardar(man, writer, cap, run_id, settings, clave)
    except StopIteration:
        log.warning("Límite --max-consultas alcanzado (%s)", max_consultas)
    except (RobotsDisallowed, RobotsUnavailable) as exc:
        log.critical("Ejecución abortada por robots.txt: %s", exc)
        man.add_consulta({"paso": "robots"}, "fallida", error=f"{type(exc).__name__}: {exc}")
    return _cerrar(man, ext, settings)


def capturar_clima(run_id: str, modo: str, inicio: date, fin: date, settings: Settings,
                   localidades: list[str] | None = None, extractor: WeatherExtractor | None = None,
                   por_mes: bool = True) -> Manifest:
    locs = cargar_localidades()
    elegidas = [locs[k] for k in (localidades or locs)]
    ext = extractor or WeatherExtractor(settings)
    writer = BronzeWriter(settings.bronze_dir)
    man = Manifest(run_id, "noaa_ncei", modo, disparador(),
                   parametros={"localidades": [l["id"] for l in elegidas], "inicio": inicio.isoformat(), "fin": fin.isoformat()})
    tramos = meses(inicio, fin) if por_mes else [(inicio, fin)]
    try:
        for loc in elegidas:
            for a, b in tramos:
                clave = {"localidad": loc["id"], "inicio": a.isoformat(), "fin": b.isoformat(), "modo": MODO_DIARIO}
                try:
                    cap = ext.fetch(loc, a, b, MODO_DIARIO)
                except (RobotsDisallowed, RobotsUnavailable):
                    raise
                except ExtractorError as exc:
                    log.error("Consulta de clima fallida %s: %s", clave, exc)
                    _diagnostico(settings, run_id, clave, exc)
                    man.add_consulta(clave, "fallida", error=f"{type(exc).__name__}: {exc}")
                    continue
                _guardar(man, writer, cap, run_id, settings, clave)
    except (RobotsDisallowed, RobotsUnavailable) as exc:
        log.critical("Ejecución abortada por robots.txt: %s", exc)
        man.add_consulta({"paso": "robots"}, "fallida", error=f"{type(exc).__name__}: {exc}")
    return _cerrar(man, ext, settings)


def _diagnostico(settings: Settings, run_id: str, clave: dict, exc: Exception) -> None:
    """Si el parser no entendió una página, guarda el HTML/JSON crudo para poder diagnosticar (no es bronce)."""
    contenido = getattr(exc, "contenido", None)
    if not contenido:
        return
    try:
        settings.diagnostic_dir.mkdir(parents=True, exist_ok=True)
        n = len(list(settings.diagnostic_dir.glob(f"{run_id}__*")))
        ruta = settings.diagnostic_dir / f"{run_id}__{n + 1}.bin"
        ruta.write_bytes(contenido)
        log.warning("Respuesta no interpretada guardada para diagnóstico: %s (%s)", ruta, clave)
    except OSError as exc2:
        log.error("No se pudo guardar el diagnóstico: %s", exc2)


def _guardar(man: Manifest, writer: BronzeWriter, cap, run_id: str, settings: Settings, clave: dict) -> None:
    try:
        bf = writer.write(cap, run_id)
    except OSError as exc:
        log.error("No se pudo escribir en Bronce %s: %s", clave, exc)
        man.add_consulta(clave, "fallida", error=f"Error de almacenamiento: {exc}")
        return
    man.add_archivo(bf.ruta, bf.sha256, cap.url, bf.bytes, base=settings.data_dir.parent if settings.data_dir.parent in bf.ruta.parents else None)
    man.add_consulta(clave, cap.estado, 0 if clave.get("paso") else cap.registros, bf.ruta.name, advertencias=cap.advertencias)


def _cerrar(man: Manifest, ext: BaseExtractor, settings: Settings) -> Manifest:
    man.solicitudes = ext.stats["solicitudes"]
    man.finalizar()
    man.save(settings.bronze_dir / man.fuente / "manifests")
    try:
        append_bitacora(settings.bitacora_path, man)
    except OSError as exc:
        log.error("No se pudo escribir la bitácora de capturas: %s", exc)
    nivel = logging.INFO if man.estado in ("exitosa", "sin_resultados") else logging.ERROR
    log.log(nivel, "RESUMEN run=%s fuente=%s estado=%s inicio=%s fin=%s duracion=%.1fs solicitudes=%d registros=%d archivos=%d errores=%d",
            man.run_id, man.fuente, man.estado, man.inicio, man.fin, man.duracion_s, man.solicitudes,
            man.registros, len(man.archivos), len(man.errores))
    return man


EXIT_CODES = {"exitosa": 0, "sin_resultados": 0, "parcial": 2, "fallida": 1}


def exit_code(manifests: list[Manifest]) -> int:
    """Código de salida del proceso: la peor situación entre las fuentes."""
    codes = [EXIT_CODES[m.estado or "fallida"] for m in manifests]
    return 1 if 1 in codes else (2 if 2 in codes else 0)
