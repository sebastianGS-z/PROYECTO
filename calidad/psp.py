"""Registro PSP: tiempo (con tiempo neto) y defectos, con validaciones.

Uso por línea de comandos (desde la raíz del repo):
    python -m calidad.psp tiempo  --archivo calidad/tiempo-integrante1.csv --fecha 2026-11-08 \
        --inicio 09:00 --fin 10:30 --interrupcion 10 --fase codigo --actividad "Extractor base"
    python -m calidad.psp defecto --archivo calidad/defectos-integrante1.csv --fecha 2026-11-08 \
        --tipo datos --introducido codigo --eliminado pruebas --minutos 15 --descripcion "..."
    python -m calidad.psp resumen --archivo calidad/tiempo-integrante1.csv
    python -m calidad.psp validar --tiempo calidad/tiempo-integrante1.csv --defectos calidad/defectos-integrante1.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

CALIDAD_DIR = Path(__file__).resolve().parent
CATALOGO_PATH = CALIDAD_DIR / "catalogo_defectos.json"

COLUMNAS_TIEMPO = ["fecha", "inicio", "fin", "interrupcion_min", "fase", "actividad"]
COLUMNAS_DEFECTOS = ["numero", "fecha", "tipo", "fase_introducido", "fase_eliminado",
                     "minutos_correccion", "defecto_origen", "descripcion"]
#: Fases con la escritura del Kit de arranque (minúsculas, sin acentos). Se aceptan sinónimos al capturar.
FASES = ["planeacion", "diseno", "codigo", "revision", "compilacion", "pruebas", "correccion", "documentacion"]
_SINONIMOS = {"codificacion": "codigo", "compilacion/ejecucion": "compilacion", "ejecucion": "compilacion",
              "compilacion o ejecucion": "compilacion", "planificacion": "planeacion", "pruebas unitarias": "pruebas"}


class PspError(ValueError):
    """Registro PSP inválido."""


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c)).strip().lower()


_FASES_NORM = {f: f for f in FASES} | _SINONIMOS


def normalizar_fase(fase: str) -> str:
    """Devuelve el nombre canónico de la fase o lanza PspError si no se reconoce."""
    canon = _FASES_NORM.get(_norm(fase or ""))
    if canon is None:
        raise PspError(f"Fase no reconocida: {fase!r}. Válidas: {', '.join(FASES)}")
    return canon


def cargar_catalogo(path: Path = CATALOGO_PATH) -> dict[str, dict[str, Any]]:
    tipos = json.loads(Path(path).read_text(encoding="utf-8"))["tipos"]
    ids = [t["id"] for t in tipos]
    if len(ids) != len(set(ids)):
        raise PspError("El catálogo de defectos tiene identificadores duplicados")
    return {t["id"]: t for t in tipos}


def _parse_fecha(valor: str) -> date:
    try:
        f = datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise PspError(f"Fecha inválida {valor!r}; use AAAA-MM-DD") from exc
    if f > date.today():
        raise PspError(f"La fecha {valor} es futura")
    return f


def _parse_hora(valor: str) -> datetime:
    try:
        return datetime.strptime(valor, "%H:%M")
    except (TypeError, ValueError) as exc:
        raise PspError(f"Hora inválida {valor!r}; use HH:MM") from exc


def _leer(path: Path, columnas: list[str]) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        lector = csv.DictReader(fh)
        if lector.fieldnames != columnas:
            raise PspError(f"Encabezados inesperados en {path}: {lector.fieldnames}")
        return list(lector)


def _agregar(path: Path, columnas: list[str], fila: dict[str, Any]) -> None:
    path = Path(path)
    nuevo = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas)
        if nuevo:
            w.writeheader()
        w.writerow(fila)


# --------------------------------------------------------------------- tiempo
def minutos_netos(inicio: str, fin: str, interrupcion_min: float) -> float:
    """Tiempo neto = (fin - inicio) - interrupciones, en minutos."""
    bruto = (_parse_hora(fin) - _parse_hora(inicio)).total_seconds() / 60
    if bruto <= 0:
        raise PspError("La hora de fin debe ser posterior a la de inicio (mismo día)")
    if interrupcion_min < 0:
        raise PspError("La interrupción no puede ser negativa")
    if interrupcion_min > bruto:
        raise PspError("La interrupción excede la duración del intervalo")
    return bruto - interrupcion_min


def validar_fila_tiempo(fila: dict[str, str]) -> dict[str, str]:
    _parse_fecha(fila["fecha"])
    try:
        interrupcion = float(fila["interrupcion_min"] or 0)
    except ValueError as exc:
        raise PspError(f"interrupcion_min no numérica: {fila['interrupcion_min']!r}") from exc
    minutos_netos(fila["inicio"], fila["fin"], interrupcion)
    if not (fila.get("actividad") or "").strip():
        raise PspError("La actividad no puede estar vacía")
    return {**fila, "fase": normalizar_fase(fila["fase"]), "interrupcion_min": f"{interrupcion:g}"}


def agregar_tiempo(path: Path, fecha: str, inicio: str, fin: str, interrupcion_min: float, fase: str, actividad: str) -> dict[str, str]:
    fila = validar_fila_tiempo({"fecha": fecha, "inicio": inicio, "fin": fin,
                                "interrupcion_min": str(interrupcion_min), "fase": fase, "actividad": actividad})
    _agregar(path, COLUMNAS_TIEMPO, fila)
    return fila


def resumen_tiempo(path: Path) -> dict[str, float]:
    """Minutos netos por fase y total."""
    totales: dict[str, float] = {}
    for fila in _leer(path, COLUMNAS_TIEMPO):
        f = validar_fila_tiempo(fila)
        neto = minutos_netos(f["inicio"], f["fin"], float(f["interrupcion_min"]))
        totales[f["fase"]] = totales.get(f["fase"], 0.0) + neto
    totales["TOTAL"] = sum(v for k, v in totales.items() if k != "TOTAL")
    return totales


# ------------------------------------------------------------------- defectos
def validar_fila_defecto(fila: dict[str, str], catalogo: dict[str, Any], numeros_previos: set[int]) -> dict[str, str]:
    try:
        numero = int(fila["numero"])
    except (TypeError, ValueError) as exc:
        raise PspError(f"Número de defecto inválido: {fila['numero']!r}") from exc
    if numero <= 0:
        raise PspError("El número de defecto debe ser positivo")
    if numero in numeros_previos:
        raise PspError(f"Número de defecto duplicado: {numero}")
    _parse_fecha(fila["fecha"])
    if fila["tipo"] not in catalogo:
        raise PspError(f"Tipo de defecto inexistente: {fila['tipo']!r}. Válidos: {', '.join(catalogo)}")
    try:
        minutos = float(fila["minutos_correccion"])
    except (TypeError, ValueError) as exc:
        raise PspError(f"minutos_correccion no numérico: {fila['minutos_correccion']!r}") from exc
    if minutos < 0:
        raise PspError("minutos_correccion no puede ser negativo")
    origen = (fila.get("defecto_origen") or "").strip()
    if origen:
        if not origen.isdigit() or int(origen) == numero or int(origen) not in numeros_previos:
            raise PspError(f"defecto_origen {origen!r} debe ser el número de un defecto previo distinto")
    if not (fila.get("descripcion") or "").strip():
        raise PspError("La descripción no puede estar vacía")
    return {**fila, "numero": str(numero), "minutos_correccion": f"{minutos:g}", "defecto_origen": origen,
            "fase_introducido": normalizar_fase(fila["fase_introducido"]),
            "fase_eliminado": normalizar_fase(fila["fase_eliminado"])}


def agregar_defecto(path: Path, fecha: str, tipo: str, fase_introducido: str, fase_eliminado: str,
                    minutos_correccion: float, descripcion: str, defecto_origen: str = "",
                    numero: int | None = None, catalogo_path: Path = CATALOGO_PATH) -> dict[str, str]:
    catalogo = cargar_catalogo(catalogo_path)
    previos = {int(f["numero"]) for f in _leer(path, COLUMNAS_DEFECTOS)} if Path(path).exists() else set()
    numero = numero if numero is not None else (max(previos) + 1 if previos else 1)
    fila = validar_fila_defecto({"numero": str(numero), "fecha": fecha, "tipo": tipo,
                                 "fase_introducido": fase_introducido, "fase_eliminado": fase_eliminado,
                                 "minutos_correccion": str(minutos_correccion), "defecto_origen": str(defecto_origen or ""),
                                 "descripcion": descripcion}, catalogo, previos)
    _agregar(path, COLUMNAS_DEFECTOS, fila)
    return fila


def validar_csv_defectos(path: Path, catalogo_path: Path = CATALOGO_PATH) -> int:
    """Valida todo el archivo (duplicados incluidos); devuelve el número de registros."""
    catalogo, vistos = cargar_catalogo(catalogo_path), set()
    for fila in _leer(path, COLUMNAS_DEFECTOS):
        validar_fila_defecto(fila, catalogo, vistos)
        vistos.add(int(fila["numero"]))
    return len(vistos)


def validar_csv_tiempo(path: Path) -> int:
    filas = _leer(path, COLUMNAS_TIEMPO)
    for f in filas:
        validar_fila_tiempo(f)
    return len(filas)


# ------------------------------------------------------------------------ CLI
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="psp", description="Registro PSP del equipo TDL")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tiempo")
    t.add_argument("--archivo", required=True); t.add_argument("--fecha", required=True)
    t.add_argument("--inicio", required=True); t.add_argument("--fin", required=True)
    t.add_argument("--interrupcion", type=float, default=0); t.add_argument("--fase", required=True)
    t.add_argument("--actividad", required=True)
    d = sub.add_parser("defecto")
    d.add_argument("--archivo", required=True); d.add_argument("--fecha", required=True)
    d.add_argument("--tipo", required=True); d.add_argument("--introducido", required=True)
    d.add_argument("--eliminado", required=True); d.add_argument("--minutos", type=float, required=True)
    d.add_argument("--origen", default=""); d.add_argument("--descripcion", required=True)
    r = sub.add_parser("resumen"); r.add_argument("--archivo", required=True)
    v = sub.add_parser("validar"); v.add_argument("--tiempo"); v.add_argument("--defectos")
    a = p.parse_args(argv)
    try:
        if a.cmd == "tiempo":
            f = agregar_tiempo(Path(a.archivo), a.fecha, a.inicio, a.fin, a.interrupcion, a.fase, a.actividad)
            print(f"Registrado: {f['fase']} — {minutos_netos(f['inicio'], f['fin'], float(f['interrupcion_min'])):g} min netos")
        elif a.cmd == "defecto":
            f = agregar_defecto(Path(a.archivo), a.fecha, a.tipo, a.introducido, a.eliminado, a.minutos, a.descripcion, a.origen)
            print(f"Defecto #{f['numero']} registrado ({f['tipo']})")
        elif a.cmd == "resumen":
            for k, val in resumen_tiempo(Path(a.archivo)).items():
                print(f"{k:24s} {val:8.1f} min")
        else:
            if a.tiempo:
                print(f"{a.tiempo}: {validar_csv_tiempo(Path(a.tiempo))} registros válidos")
            if a.defectos:
                print(f"{a.defectos}: {validar_csv_defectos(Path(a.defectos))} registros válidos")
    except PspError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
