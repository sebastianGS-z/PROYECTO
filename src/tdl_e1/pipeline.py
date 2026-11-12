"""Puerta de calidad y pipeline Bronce → Plata → Oro para E1.

Los originales Bronce nunca se modifican. Los datos inválidos se conservan en
cuarentena con su archivo de origen y las reglas que incumplieron.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

import numpy as np
import pandas as pd
import pandera.pandas as pa

from almacenamiento.bronze_writer import sha256_file
from config.settings import BASE_DIR, get_settings, cargar_fuentes
from extractores.base import StructureChangedError
from extractores.sniim_extractor import decodificar_html, parse_resultados

LOG = logging.getLogger("tdl.e1")
PRICE_FIELDS = ("precio_min", "precio_max", "precio_frecuente")
WEATHER_FIELDS = ("tavg_c", "tmax_c", "tmin_c", "prcp_mm")
NUMERIC_FIELDS = PRICE_FIELDS + WEATHER_FIELDS
STRING_FIELDS = (
    "fuente", "tipo_registro", "cultivo", "variante", "variante_id", "mercado", "origen",
    "presentacion", "estacion", "localidad", "source_file", "source_sha256", "capturado_en",
)
COLUMNS = (
    "fecha", *STRING_FIELDS, "latitud", "longitud", *NUMERIC_FIELDS, "versiones_observadas",
)


def _schema() -> pa.DataFrameSchema:
    columns: dict[str, pa.Column] = {
        "fecha": pa.Column("datetime64[ns]", nullable=False),
        "fuente": pa.Column(str, checks=pa.Check.isin(["sniim", "noaa_ncei"]), nullable=False),
        "tipo_registro": pa.Column(str, checks=pa.Check.isin(["precio", "clima"]), nullable=False),
        "cultivo": pa.Column(str, nullable=True), "variante": pa.Column(str, nullable=True),
        "variante_id": pa.Column(str, nullable=True), "mercado": pa.Column(str, nullable=True),
        "origen": pa.Column(str, nullable=True), "presentacion": pa.Column(str, nullable=True),
        "estacion": pa.Column(str, nullable=True), "localidad": pa.Column(str, nullable=True),
        "source_file": pa.Column(str, nullable=False), "source_sha256": pa.Column(str, nullable=False),
        "capturado_en": pa.Column(str, nullable=False),
        "latitud": pa.Column(float, checks=pa.Check.in_range(-90, 90), nullable=True),
        "longitud": pa.Column(float, checks=pa.Check.in_range(-180, 180), nullable=True),
        "versiones_observadas": pa.Column(int, checks=pa.Check.ge(1), nullable=False),
    }
    for field in PRICE_FIELDS:
        columns[field] = pa.Column(float, checks=pa.Check.ge(0), nullable=True)
    for field in WEATHER_FIELDS:
        check = pa.Check.ge(0) if field == "prcp_mm" else pa.Check.in_range(-90, 70)
        columns[field] = pa.Column(float, checks=check, nullable=True)
    return pa.DataFrameSchema(columns, strict=True, coerce=True, unique_column_names=True)


def _empty_record() -> dict[str, Any]:
    return {column: None for column in COLUMNS} | {"versiones_observadas": 1}


def _number(value: Any) -> float | None:
    if value is None:
        return None
    raw = str(value).strip().replace("$", "").replace(" ", "")
    if not raw or raw.lower() in {"n/d", "nd", "na", "n/a", "-", "null"}:
        return None
    # La fuente suele usar punto decimal; también se tolera coma decimal.
    if "," in raw and "." not in raw:
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        result = float(raw)
    except ValueError:
        raise ValueError(f"valor numérico inválido: {value!r}") from None
    if not math.isfinite(result):
        raise ValueError(f"valor no finito: {value!r}")
    return result


def _sidecar(path: Path) -> tuple[dict[str, Any], str]:
    meta_path = path.with_name(path.name + ".meta.json")
    if not meta_path.is_file():
        raise ValueError("falta el sidecar .meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    expected = meta["metadatos_captura"]["sha256"]
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"SHA-256 no coincide: esperado {expected}, recibido {actual}")
    return meta["metadatos_captura"], actual


def _bad(path: Path, reason: str, raw: Any = None, sha: str = "") -> dict[str, Any]:
    return {"source_file": _display_path(path), "source_sha256": sha, "motivo": reason,
            "registro_original": json.dumps(raw, ensure_ascii=False, default=str) if raw is not None else ""}


def _display_path(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(BASE_DIR).as_posix()
    except ValueError:
        return Path(path).name


def _parse_sniim(path: Path, metadata: dict[str, Any], sha: str, sources: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    md = metadata
    if md.get("tipo") == "formulario" or md.get("etiqueta") == "catalogo-formulario":
        return [], []
    catalog = sources["sniim"]
    crop = next((p["clave"] for p in catalog["productos"]
                 if md.get("producto", "").casefold().startswith(p["busqueda"].casefold())), "")
    try:
        parsed = parse_resultados(decodificar_html(path.read_bytes()))
    except StructureChangedError as exc:
        return [], [_bad(path, f"estructura SNIIM no reconocida: {exc}", sha=sha)]
    rows, quarantine = [], []
    for raw in parsed.registros:
        try:
            source_date = raw.get("Fecha")
            if not source_date:
                # Las páginas de consulta de un solo día omiten Fecha; se usa el
                # rango solicitado del sidecar, que es trazable y no ambiguo.
                start, end = md.get("fecha_ref_inicio"), md.get("fecha_ref_fin")
                if start and start == end:
                    source_date = start
                    day = pd.to_datetime(source_date, format="%Y-%m-%d", errors="raise")
                else:
                    raise ValueError("fila sin fecha y consulta con rango de varios días")
            else:
                day = pd.to_datetime(source_date, format="%d/%m/%Y", errors="raise")
            if pd.isna(day):
                raise ValueError(f"fecha inválida: {source_date!r}")
            prices = {"precio_min": _number(raw.get("Precio Mín")),
                      "precio_max": _number(raw.get("Precio Max")),
                      "precio_frecuente": _number(raw.get("Precio Frec"))}
            if not any(value is not None for value in prices.values()):
                raise ValueError("fila sin ningún precio interpretable")
            row = _empty_record() | {
                "fecha": day, "fuente": "sniim", "tipo_registro": "precio", "cultivo": crop or None,
                "variante": md.get("producto"), "variante_id": str(md.get("producto_id", "")) or None,
                "mercado": md.get("mercado_id") or md.get("mercado"), "origen": raw.get("Origen") or None,
                "presentacion": raw.get("Presentación") or None, "source_file": _display_path(path),
                "source_sha256": sha, "capturado_en": str(md.get("fecha_captura", "")), **prices,
            }
            if row["precio_min"] is not None and row["precio_max"] is not None and row["precio_min"] > row["precio_max"]:
                raise ValueError("precio_min mayor que precio_max")
            frequent = row["precio_frecuente"]
            if frequent is not None and row["precio_min"] is not None and frequent < row["precio_min"]:
                raise ValueError("precio_frecuente menor que precio_min")
            if frequent is not None and row["precio_max"] is not None and frequent > row["precio_max"]:
                raise ValueError("precio_frecuente mayor que precio_max")
            rows.append(row)
        except (ValueError, TypeError) as exc:
            quarantine.append(_bad(path, str(exc), raw, sha))
    for n in range(parsed.filas_no_interpretadas):
        quarantine.append(_bad(path, f"fila HTML {n + 1}: forma distinta al encabezado; no se pudo parsear", sha=sha))
    return rows, quarantine


def _parse_noaa(path: Path, metadata: dict[str, Any], sha: str) -> tuple[list[dict], list[dict]]:
    rows, quarantine = [], []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("respuesta NOAA no es una lista JSON")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return [], [_bad(path, f"JSON NOAA inválido: {exc}", sha=sha)]
    for raw in payload:
        try:
            if not isinstance(raw, dict):
                raise ValueError("registro NOAA no es un objeto")
            day = pd.to_datetime(raw.get("DATE"), format="%Y-%m-%d", errors="raise")
            if pd.isna(day):
                raise ValueError(f"fecha NOAA inválida: {raw.get('DATE')!r}")
            values = {"tavg_c": _number(raw.get("TAVG")), "tmax_c": _number(raw.get("TMAX")),
                      "tmin_c": _number(raw.get("TMIN")), "prcp_mm": _number(raw.get("PRCP"))}
            row = _empty_record() | {
                "fecha": day, "fuente": "noaa_ncei", "tipo_registro": "clima",
                "estacion": str(raw.get("STATION") or metadata.get("estacion") or ""),
                "localidad": metadata.get("localidad"), "latitud": _number(metadata.get("latitud")),
                "longitud": _number(metadata.get("longitud")), "source_file": _display_path(path),
                "source_sha256": sha, "capturado_en": str(metadata.get("fecha_captura", "")), **values,
            }
            if row["tmin_c"] is not None and row["tmax_c"] is not None and row["tmin_c"] > row["tmax_c"]:
                raise ValueError("tmin_c mayor que tmax_c")
            rows.append(row)
        except (ValueError, TypeError) as exc:
            quarantine.append(_bad(path, str(exc), raw, sha))
    return rows, quarantine


def leer_bronce(bronze_dir: Path) -> tuple[pd.DataFrame, list[dict[str, Any]], dict[str, set[pd.Timestamp]]]:
    sources = cargar_fuentes()
    records: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    climate_expected: dict[str, set[pd.Timestamp]] = defaultdict(set)
    files = sorted([*bronze_dir.rglob("*.html"), *bronze_dir.rglob("*.json")])
    files = [p for p in files if "/manifests/" not in p.as_posix() and not p.name.endswith(".meta.json")]
    for path in files:
        try:
            md, sha = _sidecar(path)
            if md.get("fuente") == "noaa_ncei":
                station = str(md.get("estacion", ""))
                start, end = md.get("fecha_ref_inicio"), md.get("fecha_ref_fin")
                if station and start and end:
                    climate_expected[station].update(pd.date_range(start, end, freq="D"))
            if md.get("fuente") == "sniim" and path.suffix.lower() == ".html":
                accepted, rejected = _parse_sniim(path, md, sha, sources)
            elif md.get("fuente") == "noaa_ncei" and path.suffix.lower() == ".json":
                accepted, rejected = _parse_noaa(path, md, sha)
            else:
                continue
            records.extend(accepted)
            quarantine.extend(rejected)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            quarantine.append(_bad(path, f"fallo de lectura/metadata: {exc}"))
    frame = pd.DataFrame(records, columns=COLUMNS)
    return frame, quarantine, climate_expected


def _as_types(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    for name in STRING_FIELDS:
        df[name] = df[name].map(lambda value: None if pd.isna(value) else str(value)).astype(object)
    for name in ("latitud", "longitud", *NUMERIC_FIELDS):
        df[name] = pd.to_numeric(df[name], errors="coerce")
    df["versiones_observadas"] = pd.to_numeric(df["versiones_observadas"], errors="coerce")
    return df.loc[:, COLUMNS]


def puerta_calidad(frame: pd.DataFrame, initial_quarantine: list[dict[str, Any]]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Valida con Pandera; filas que fallan se envían a cuarentena con evidencia."""
    df = _as_types(frame)
    quarantine = list(initial_quarantine)
    # Reglas relacionales que describen el significado de las variables de origen.
    business_reasons: dict[int, list[str]] = defaultdict(list)
    for index, row in df.iterrows():
        if row["tipo_registro"] == "precio":
            if row["precio_min"] is not None and row["precio_max"] is not None and row["precio_min"] > row["precio_max"]:
                business_reasons[index].append("precio_min mayor que precio_max")
            if row["precio_min"] is not None and row["precio_frecuente"] is not None and row["precio_frecuente"] < row["precio_min"]:
                business_reasons[index].append("precio_frecuente menor que precio_min")
            if row["precio_max"] is not None and row["precio_frecuente"] is not None and row["precio_frecuente"] > row["precio_max"]:
                business_reasons[index].append("precio_frecuente mayor que precio_max")
        if row["tipo_registro"] == "clima" and row["tmin_c"] is not None and row["tmax_c"] is not None and row["tmin_c"] > row["tmax_c"]:
            business_reasons[index].append("tmin_c mayor que tmax_c")
    bad_indexes = set(business_reasons)
    candidates = df.drop(index=list(bad_indexes)) if bad_indexes else df
    def append_business_quarantine() -> None:
        for index, reasons in business_reasons.items():
            if index in df.index:
                row = df.loc[index]
                raw = {k: (v.isoformat() if isinstance(v, pd.Timestamp) else v) for k, v in row.to_dict().items()}
                quarantine.append(_bad(Path(str(row["source_file"])), "; ".join(dict.fromkeys(reasons)), raw, str(row["source_sha256"] or "")))
    if candidates.empty:
        append_business_quarantine()
        return candidates.reset_index(drop=True), quarantine
    schema = _schema()
    try:
        validated = schema.validate(candidates, lazy=True)
    except pa.errors.SchemaErrors as exc:
        failures = exc.failure_cases
        for _, failure in failures.iterrows():
            ix = failure.get("index")
            if pd.notna(ix) and ix in candidates.index:
                bad_indexes.add(int(ix))
                business_reasons[int(ix)].append(str(failure.get("check", failure.get("failure_case", "esquema Pandera inválido"))))
            else:
                raise ValueError(f"Puerta de calidad: error global de esquema Pandera: {failure.to_dict()}") from exc
        remaining = df.drop(index=list(bad_indexes))
        validated = schema.validate(remaining, lazy=True) if not remaining.empty else remaining
    append_business_quarantine()
    return validated.reset_index(drop=True), quarantine


def resolver_duplicados(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Consolida observaciones repetidas; discrepancias se resuelven por captura más reciente."""
    df = frame.copy()
    if df.empty:
        return df, []
    keys = ["tipo_registro", "fecha", "variante_id", "mercado", "origen", "presentacion", "estacion"]
    value_columns = [*NUMERIC_FIELDS, "cultivo", "variante", "localidad", "latitud", "longitud"]
    conflicts: list[dict[str, Any]] = []
    retained: list[pd.Series] = []
    for _, group in df.groupby(keys, dropna=False, sort=False):
        if len(group) == 1:
            retained.append(group.iloc[0])
            continue
        group = group.sort_values(["capturado_en", "source_file"], kind="stable")
        chosen = group.iloc[-1].copy()
        distinct = group[value_columns].astype("string").drop_duplicates()
        changed = len(distinct) > 1
        chosen["versiones_observadas"] = int(group["versiones_observadas"].fillna(1).sum())
        if changed:
            conflicts.append({
                "clave": {k: (str(chosen[k]) if pd.notna(chosen[k]) else None) for k in keys},
                "archivos_candidatos": group["source_file"].tolist(),
                "columnas_discrepantes": [c for c in value_columns if group[c].astype("string").nunique(dropna=False) > 1],
                "resolucion": "se conserva la captura más reciente según capturado_en; el original de cada versión permanece en Bronce",
                "archivo_conservado": chosen["source_file"],
            })
        retained.append(chosen)
    result = pd.DataFrame(retained, columns=COLUMNS).reset_index(drop=True)
    return result, conflicts


def diagnostico_faltantes(frame: pd.DataFrame, expected_dates: dict[str, set[pd.Timestamp]] | None = None) -> dict[str, Any]:
    numeric = [*NUMERIC_FIELDS]
    report: dict[str, Any] = {"regla": "No se imputan precios ni precipitación. MAR/MCAR/MNAR no se prueban solo con valores observados; se reportan asociaciones descriptivas.", "variables": {}}
    strata = [name for name in ("tipo_registro", "cultivo", "mercado", "estacion") if frame[name].notna().any()]
    climate_days: list[pd.DataFrame] = []
    climate_source = frame[frame["tipo_registro"].eq("clima")]
    if not climate_source.empty or expected_dates:
        observed_groups = {str(station): group for station, group in climate_source.groupby("estacion", dropna=False)}
        stations = set(observed_groups) | set(expected_dates or {})
        for station in stations:
            group = observed_groups.get(station, pd.DataFrame(columns=["fecha", *WEATHER_FIELDS]))
            if not group.empty:
                observed = group.set_index("fecha")[list(WEATHER_FIELDS)].groupby(level=0).last()
            else:
                observed = pd.DataFrame(columns=WEATHER_FIELDS, index=pd.DatetimeIndex([], name="fecha"))
            expected = sorted((expected_dates or {}).get(station, set()))
            if not expected and len(observed.index):
                expected = list(pd.date_range(observed.index.min(), observed.index.max(), freq="D"))
            calendar = observed.reindex(pd.DatetimeIndex(expected))
            calendar.index.name = "fecha"
            calendar["estacion"] = station
            calendar["mes"] = calendar.index.month
            climate_days.append(calendar.reset_index())
    climate_calendar = pd.concat(climate_days, ignore_index=True) if climate_days else pd.DataFrame()
    for field in numeric:
        applicable = frame[frame["tipo_registro"].eq("precio")] if field in PRICE_FIELDS else frame[frame["tipo_registro"].eq("clima")]
        if field in WEATHER_FIELDS and not climate_calendar.empty:
            applicable = climate_calendar
        if applicable.empty:
            continue
        n = len(applicable)
        missing = int(applicable[field].isna().sum())
        groups: dict[str, Any] = {}
        spreads = []
        local_strata = [key for key in strata if key in applicable.columns]
        if field in WEATHER_FIELDS and "mes" in applicable.columns:
            local_strata.append("mes")
        for key in dict.fromkeys(local_strata):
            usable = applicable[applicable[key].notna()]
            if usable.empty:
                continue
            rates = usable.groupby(key, dropna=False)[field].apply(lambda s: float(s.isna().mean()))
            if len(rates):
                spreads.append(float(rates.max() - rates.min()))
            groups[key] = {str(k): round(float(v), 4) for k, v in rates.items()}
        spread = max(spreads, default=0.0)
        if missing == 0:
            mechanism = "sin_faltantes"
        elif spread >= 0.20:
            mechanism = "MAR_compatible_asociacion_con_variables_observadas"
        else:
            mechanism = "MCAR_compatible_sin_evidencia_descriptiva_de_grupos; MNAR_no_descartable"
        report["variables"][field] = {
            "n_aplicable": n, "faltantes": missing, "porcentaje": round(100 * missing / n, 2),
            "mecanismo": mechanism, "tasas_por_grupo": groups,
            "decision_imputacion": ("no_imputar: una cotización ausente no se deduce de las restantes" if field in PRICE_FIELDS else
                                    "no_imputar: precipitación es episódica; ausencia no significa cero" if field == "prcp_mm" else
                                    "solo feature de modelado: interpolación lineal interior de hasta 2 días, con indicador; nunca sobrescribe el valor original"),
        }
    if not climate_calendar.empty:
        observed_days = int(climate_calendar[list(WEATHER_FIELDS)].notna().any(axis=1).sum())
        days = climate_calendar["fecha"]
        report["calendario_climatico"] = {
            "inicio_observado": days.min().date().isoformat(), "fin_observado": days.max().date().isoformat(),
            "dias_estacion_esperados_en_rangos_observados": int(len(days)), "dias_con_algun_dato": observed_days,
            "dias_sin_registro_util": int(len(days) - observed_days),
            "nota": "Rango derivado de fechas válidas. No incluye posibles faltantes anteriores o posteriores al rango observado.",
        }
    return report


def transformar_estadisticamente(frame: pd.DataFrame, expected_dates: dict[str, set[pd.Timestamp]] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Añade atípicos, límites winsorizados, escalas, discretización y calendario."""
    df = frame.copy()
    report: dict[str, Any] = {"atipicos": {}, "escalado": {}, "discretizacion": {},
                              "jerarquias": {"fecha": ["anio", "trimestre", "mes", "dia"],
                                             "mercado": ["mercado"], "cultivo": ["cultivo", "variante", "variante_id"],
                                             "clima": ["estacion", "localidad"]}}
    df["anio"] = df["fecha"].dt.year
    df["trimestre"] = df["fecha"].dt.quarter
    df["mes"] = df["fecha"].dt.month
    df["dia"] = df["fecha"].dt.day
    df["atipico"] = False
    df["metodo_atipico"] = "ninguno"
    price_groups = ["variante_id", "mercado", "presentacion"]
    for field in NUMERIC_FIELDS:
        df[f"{field}_analisis"] = df[field]
        df[f"{field}_minmax"] = np.nan
        df[f"{field}_zscore"] = np.nan
        applicable = df[df[field].notna()]
        if applicable.empty:
            continue
        outlier_count, group_count = 0, 0
        group_cols = price_groups if field in PRICE_FIELDS else ["estacion"]
        for _, idx in applicable.groupby(group_cols, dropna=False).groups.items():
            values = df.loc[idx, field].dropna()
            if len(values) < 8:
                continue
            group_count += 1
            q1, q3 = values.quantile(0.25), values.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            median = values.median()
            mad = (values - median).abs().median()
            robust_z = (0.6745 * (values - median) / mad) if mad > 0 else pd.Series(0.0, index=values.index)
            flagged = (values.lt(lower) | values.gt(upper) | robust_z.abs().gt(3.5))
            outlier_index = values.index[flagged]
            if len(outlier_index):
                df.loc[outlier_index, "atipico"] = True
                df.loc[outlier_index, "metodo_atipico"] = "IQR_1.5_y_Z_robusto_3.5"
                # Se conserva el dato original y se limita una copia de análisis.
                df.loc[outlier_index, f"{field}_analisis"] = values.loc[outlier_index].clip(lower=lower, upper=upper)
                outlier_count += len(outlier_index)
        analysis = df.loc[applicable.index, f"{field}_analisis"].dropna()
        overall_min, overall_max = float(analysis.min()), float(analysis.max())
        overall_mean, overall_std = float(analysis.mean()), float(analysis.std(ddof=0))
        if overall_max > overall_min:
            df.loc[analysis.index, f"{field}_minmax"] = (analysis - overall_min) / (overall_max - overall_min)
        if overall_std > 0:
            df.loc[analysis.index, f"{field}_zscore"] = (analysis - overall_mean) / overall_std
        report["atipicos"][field] = {"filas_marcadas": outlier_count, "grupos_evaluados": group_count,
                                     "metodos": ["IQR 1.5×", "Z robusto (MAD) > 3.5"],
                                     "tratamiento": "se conserva el original; *_analisis aplica winsorización IQR para el modelado"}
        report["escalado"][field] = {"metodo": "Min-Max y Z-Score poblacional sobre *_analisis (original o winsorizado); parámetros completos en el reporte",
                                     "minimo": overall_min, "maximo": overall_max, "media": overall_mean, "desviacion": overall_std}
    price = df["tipo_registro"].eq("precio") & df["precio_frecuente"].notna()
    if price.sum() >= 3:
        ranks = df.loc[price, "precio_frecuente"].rank(method="first", pct=True)
        df.loc[price, "precio_frecuente_nivel"] = pd.cut(ranks, bins=[0, 1/3, 2/3, 1], labels=["bajo", "medio", "alto"], include_lowest=True).astype("string")
    climate = df["tipo_registro"].eq("clima") & df["tavg_c"].notna()
    df["temperatura_nivel"] = pd.NA
    df.loc[climate, "temperatura_nivel"] = pd.cut(df.loc[climate, "tavg_c"], bins=[-90, 18, 25, 32, 70], labels=["frio", "templado", "calido", "muy_calido"]).astype("string")
    report["discretizacion"] = {"precio_frecuente_nivel": "terciles empíricos globales; se conserva la variable continua", "temperatura_nivel": "frío <18°C, templado 18–25°C, cálido 25–32°C, muy cálido ≥32°C; límites operativos descriptivos, no umbrales agronómicos validados"}
    report["precaucion_modelado"] = "Escalas y límites atípicos se estiman sobre el lote completo para describir esta capa. En evaluación predictiva deben reajustarse solo con train para evitar fuga de información temporal."
    report["reduccion"] = "Oro agrega precios diarios por variante × mercado × origen × presentación y clima por estación × mes; mantiene conteos y dispersión. No se muestrean observaciones."
    model = construir_clima_modelado(df, expected_dates)
    return df, model, report


def construir_clima_modelado(frame: pd.DataFrame, expected_dates: dict[str, set[pd.Timestamp]] | None = None) -> pd.DataFrame:
    weather = frame[frame["tipo_registro"].eq("clima")].copy()
    columns = ["fecha", "estacion", "localidad", *WEATHER_FIELDS]
    if weather.empty and not expected_dates:
        return pd.DataFrame(columns=[*columns, "tavg_c_modelo", "tavg_c_imputado", "tmax_c_modelo", "tmax_c_imputado", "tmin_c_modelo", "tmin_c_imputado"])
    outputs = []
    weather_groups = {str(station): group for station, group in weather.groupby("estacion", dropna=False)}
    for station in set(weather_groups) | set(expected_dates or {}):
        group = weather_groups.get(station, pd.DataFrame(columns=[*COLUMNS]))
        if not group.empty:
            group = group.sort_values("fecha").drop_duplicates("fecha", keep="last").set_index("fecha")
        else:
            group = pd.DataFrame(columns=COLUMNS, index=pd.DatetimeIndex([], name="fecha"))
        calendar = sorted((expected_dates or {}).get(station, set()))
        if not calendar and len(group.index):
            calendar = list(pd.date_range(group.index.min(), group.index.max(), freq="D"))
        expanded = group.reindex(pd.DatetimeIndex(calendar))
        expanded.index.name = "fecha"
        expanded["estacion"] = station
        expanded["localidad"] = group["localidad"].dropna().iloc[-1] if group["localidad"].notna().any() else None
        for field in ("tavg_c", "tmax_c", "tmin_c"):
            expanded[f"{field}_modelo"] = expanded[field].interpolate(method="time", limit=2, limit_area="inside")
            expanded[f"{field}_imputado"] = expanded[field].isna() & expanded[f"{field}_modelo"].notna()
        outputs.append(expanded.reset_index()[["fecha", "estacion", "localidad", *WEATHER_FIELDS,
                                               "tavg_c_modelo", "tavg_c_imputado", "tmax_c_modelo", "tmax_c_imputado",
                                               "tmin_c_modelo", "tmin_c_imputado"]])
    return pd.concat(outputs, ignore_index=True)


def construir_oro(frame: pd.DataFrame) -> pd.DataFrame:
    prices = frame[frame["tipo_registro"].eq("precio")].copy()
    climate = frame[frame["tipo_registro"].eq("clima")].copy()
    if prices.empty:
        return pd.DataFrame()
    prices["anio"], prices["mes"] = prices["fecha"].dt.year, prices["fecha"].dt.month
    keys = ["cultivo", "variante", "variante_id", "mercado", "origen", "presentacion", "anio", "mes"]
    agg = {field: ["mean", "median", "min", "max", "std", "count"] for field in PRICE_FIELDS}
    gold_prices = prices.groupby(keys, dropna=False).agg(agg)
    gold_prices.columns = [f"{field}_{stat}" for field, stat in gold_prices.columns]
    gold_prices = gold_prices.reset_index()
    counts = prices.groupby(keys, dropna=False).size().rename("n_observaciones_precio").reset_index()
    gold_prices = gold_prices.merge(counts, on=keys, how="left", validate="one_to_one")
    if not climate.empty:
        climate["anio"], climate["mes"] = climate["fecha"].dt.year, climate["fecha"].dt.month
        climate_agg = {field: ["mean", "min", "max", "count"] for field in WEATHER_FIELDS}
        gold_climate = climate.groupby(["estacion", "anio", "mes"], dropna=False).agg(climate_agg)
        gold_climate.columns = [f"{field}_{stat}" for field, stat in gold_climate.columns]
        gold_climate = gold_climate.reset_index()
        observed_days = (climate[climate[list(WEATHER_FIELDS)].notna().any(axis=1)]
                         .groupby(["estacion", "anio", "mes"], dropna=False)["fecha"]
                         .nunique().rename("dias_clima_observados").reset_index())
        gold_climate = gold_climate.merge(observed_days, on=["estacion", "anio", "mes"], how="left", validate="one_to_one")
        # No se mezclan estaciones distintas: el panel queda replicado por estación de referencia.
        gold_prices = gold_prices.merge(gold_climate, on=["anio", "mes"], how="left", validate="many_to_many")
    else:
        gold_prices["dias_clima_observados"] = 0
    gold_prices["fecha_mes"] = pd.to_datetime(dict(year=gold_prices["anio"], month=gold_prices["mes"], day=1))
    return gold_prices.sort_values(["fecha_mes", "cultivo", "variante_id", "mercado"], kind="stable").reset_index(drop=True)


def _write_csv(frame: pd.DataFrame, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(fd)
    try:
        frame.to_csv(temp_name, index=False, encoding="utf-8", na_rep="")
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def ejecutar(bronze_dir: Path, data_dir: Path) -> dict[str, Any]:
    raw, quarantine, climate_expected = leer_bronce(bronze_dir)
    if raw.empty and not quarantine:
        raise RuntimeError(f"No se encontraron datos Bronce en {bronze_dir}")
    clean, quarantine = puerta_calidad(raw, quarantine)
    clean, conflicts = resolver_duplicados(clean)
    missing_report = diagnostico_faltantes(clean, climate_expected)
    transformed, climate_model, transform_report = transformar_estadisticamente(clean, climate_expected)
    gold = construir_oro(clean)
    silver_dir, gold_dir, quarantine_dir = data_dir / "plata", data_dir / "oro", data_dir / "cuarentena"
    _write_csv(transformed, silver_dir / "precios_clima.csv")
    _write_csv(climate_model, silver_dir / "clima_modelado.csv")
    _write_csv(gold, gold_dir / "panel_mensual.csv")
    _write_csv(pd.DataFrame(quarantine, columns=["source_file", "source_sha256", "motivo", "registro_original"]),
               quarantine_dir / "registros_invalidos.csv")
    _write_csv(pd.DataFrame(conflicts, columns=["clave", "archivos_candidatos", "columnas_discrepantes", "resolucion", "archivo_conservado"]),
               silver_dir / "conflictos_resueltos.csv")
    report = {
        "esquema": "tdl-e1-quality/1", "generado_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "bronce": _display_path(bronze_dir), "registros_bronce_parseados": len(raw), "registros_plata_validos": len(clean),
        "registros_cuarentena": len(quarantine), "conflictos_duplicados": len(conflicts),
        "filas_oro": len(gold), "integridad": "Pandera estricto; SHA-256 Bronce verificado antes de parsear",
        "faltantes": missing_report, "transformaciones": transform_report,
        "imputacion": {"precios": "ninguna", "precipitacion": "ninguna", "temperatura": "solo copia de modelado; interpolación lineal interior de hasta dos días, con flags; original intacto"},
        "jerarquias_conceptuales": transform_report["jerarquias"],
        "conflictos": "duplicados con valores distintos: se conserva la captura de mayor fecha_captura; los originales siguen en Bronce; detalle en conflictos_resueltos.csv",
        "cuarentena": "cada fila incluye ruta, hash cuando disponible, motivo y representación del registro original",
    }
    report_path = silver_dir / "reporte_calidad.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (silver_dir / "diagnostico_faltantes.json").write_text(json.dumps(missing_report, ensure_ascii=False, indent=2), encoding="utf-8")
    LOG.info("E1 terminado: Bronce parseado=%d Plata=%d cuarentena=%d Oro=%d", len(raw), len(clean), len(quarantine), len(gold))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bronze-dir", type=Path)
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args(argv)
    settings = get_settings()
    bronze_dir = args.bronze_dir or settings.bronze_dir
    data_dir = args.data_dir or settings.data_dir
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        result = ejecutar(bronze_dir, data_dir)
    except Exception as exc:
        LOG.exception("Puerta de calidad E1 no pudo completar el pipeline: %s", exc)
        print(f"ERROR E1: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({k: result[k] for k in ("registros_bronce_parseados", "registros_plata_validos", "registros_cuarentena", "conflictos_duplicados", "filas_oro")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
