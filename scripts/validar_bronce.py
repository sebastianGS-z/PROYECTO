"""Valida la Capa Bronce: SHA-256 de cada archivo y coherencia manifiesto ↔ archivos.

Código de salida: 0 todo íntegro · 1 hay inconsistencias · 3 no hay nada que validar (con --exigir-archivos).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

from almacenamiento.bronze_writer import META_SUFFIX, sha256_file, verificar_archivo
from config.settings import get_settings


def validar(bronze_dir: Path, run_id: str | None = None) -> tuple[int, list[str]]:
    errores: list[str] = []
    n = 0
    for meta in sorted(bronze_dir.rglob(f"*{META_SUFFIX}")):
        if run_id and run_id not in meta.name:
            continue
        n += 1
        ok, msg = verificar_archivo(meta)
        if not ok:
            errores.append(f"{meta.name}: {msg}")
    for man in sorted(bronze_dir.glob("*/manifests/manifest_*.json")):
        if run_id and run_id not in man.name:
            continue
        data = json.loads(man.read_text(encoding="utf-8"))
        raiz = man.parents[4]  # <raiz>/data/bronce/<fuente>/manifests/manifest.json -> <raiz>
        for arch in data.get("archivos", []):
            ruta = raiz / arch["ruta"]
            if not ruta.is_file():
                errores.append(f"{man.name}: falta {arch['ruta']}")
            elif sha256_file(ruta) != arch["sha256"]:
                errores.append(f"{man.name}: hash distinto en {arch['ruta']}")
        if data.get("estado") is None:
            errores.append(f"{man.name}: sin estado final")
    return n, errores


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id"); ap.add_argument("--exigir-archivos", action="store_true")
    a = ap.parse_args(argv)
    n, errores = validar(get_settings().bronze_dir, a.run_id)
    print(f"Archivos verificados: {n}")
    for e in errores:
        print(f"ERROR: {e}", file=sys.stderr)
    if errores:
        return 1
    if n == 0 and a.exigir_archivos:
        print("ERROR: no se generó ningún archivo Bronce", file=sys.stderr)
        return 3
    print("Capa Bronce íntegra.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
