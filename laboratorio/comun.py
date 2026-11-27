"""Utilidades compartidas del laboratorio estadístico (rutas, figuras y JSON reproducible)."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTADOS = BASE_DIR / "laboratorio" / "resultados"
SEMILLA = 20261127


def limpiar(value: Any) -> Any:
    """Convierte tipos de NumPy/pandas a JSON estándar (NaN → None)."""
    if isinstance(value, dict):
        return {str(k): limpiar(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [limpiar(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return None if math.isnan(v) or math.isinf(v) else round(v, 6)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, pd.Period)):
        return str(value)
    if isinstance(value, np.ndarray):
        return limpiar(value.tolist())
    return value


def guardar_json(data: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(limpiar(data), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def guardar_figura(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=110, metadata={"Software": None, "CreationDate": None} if path.suffix == ".pdf" else {"Software": None})
    plt.close(fig)
    return path


def rel(path: Path, desde: Path) -> str:
    """Ruta relativa para enlaces Markdown desde ``desde`` (carpeta del documento)."""
    import os
    return Path(os.path.relpath(path, desde)).as_posix()


def fmt(x: Any, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, (int, np.integer)):
        return f"{int(x):,}"
    return f"{float(x):,.{nd}f}"


def tabla_md(df: pd.DataFrame, nd: int = 3) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        out.append("| " + " | ".join(fmt(v, nd) if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool) else str(v) for v in row) + " |")
    return "\n".join(out)
