#!/usr/bin/env python3
"""Compara la versión congelada en el tag e2 contra el pipeline actual.

Ejemplo: python benchmarks/comparativa.py --repeticiones 3
Usa las mismas capturas Bronce, ejecuta cada versión en un proceso aislado y
verifica que las salidas CSV sean idénticas antes de publicar métricas.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "bronce"
OUT = ROOT / "benchmarks"
LOGS = OUT / "evidencias"
BASELINE_COMMIT = "e2"
PIPELINE_PATH = "src/tdl_e1/pipeline.py"
PARSER_PATH = "extractores/sniim_extractor.py"

CHILD = r'''
import importlib, importlib.util, json, resource, sys, time
from pathlib import Path
kind, pipeline_file, parser_file, output_dir = sys.argv[1:]
if parser_file != "-":
    spec = importlib.util.spec_from_file_location("extractores.sniim_extractor", parser_file)
    parser = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = parser
    spec.loader.exec_module(parser)
if kind == "base":
    spec = importlib.util.spec_from_file_location("benchmark_e1_baseline", pipeline_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
else:
    module = importlib.import_module("src.tdl_e1.pipeline")
start = time.perf_counter()
result = module.ejecutar(Path("data/bronce"), Path(output_dir))
seconds = time.perf_counter() - start
print(json.dumps({"seconds": seconds,
                  "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  "records_parsed": result["registros_bronce_parseados"],
                  "records_valid": result["registros_plata_validos"],
                  "records_quarantined": result["registros_cuarentena"],
                  "gold_rows": result["filas_oro"],
                  "duplicate_conflicts": result["conflictos_duplicados"]}))
'''


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint_bronze() -> dict[str, object]:
    files = sorted(p for p in BRONZE.rglob("*") if p.is_file())
    return {"archivos": len(files), "bytes": sum(p.stat().st_size for p in files),
            "sha256_inventario": hashlib.sha256("\n".join(
                f"{p.relative_to(ROOT).as_posix()} {sha256(p)}" for p in files
            ).encode()).hexdigest()}


def execute(kind: str, module_path: Path, parser_path: Path | None,
            output_dir: Path, run_number: int) -> dict[str, object]:
    args = [sys.executable, "-c", CHILD, kind, str(module_path),
            str(parser_path) if parser_path else "-", str(output_dir)]
    env = os.environ.copy()
    env.update({"PYTHONPATH": str(ROOT), "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    started = time.perf_counter()
    completed = subprocess.run(args, cwd=ROOT, env=env, text=True, capture_output=True)
    wall_seconds = time.perf_counter() - started
    log_path = LOGS / f"{kind}_corrida_{run_number}.log"
    log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode:
        return {"version": kind, "run": run_number, "seconds": wall_seconds,
                "errors": 1, "records_parsed": 0, "records_valid": 0,
                "records_quarantined": 0, "gold_rows": 0, "duplicate_conflicts": 0,
                "peak_rss_kib": 0, "log": log_path.relative_to(ROOT).as_posix(),
                "stderr": completed.stderr[-2000:]}
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    return {"version": kind, "run": run_number, "errors": 0, **result,
            "log": log_path.relative_to(ROOT).as_posix()}


def csv_hashes(directory: Path) -> dict[str, str]:
    return {p.relative_to(directory).as_posix(): sha256(p)
            for p in sorted(directory.rglob("*.csv"))}


def make_chart(summary: dict[str, object]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = summary["metricas"]
    labels = ["Original (tag e2)", "Optimizado"]
    values = [metrics["tiempo_segundos"]["antes"], metrics["tiempo_segundos"]["despues"]]
    memory = [metrics["memoria_max_mib"]["antes"], metrics["memoria_max_mib"]["despues"]]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    for ax, data, title, ylabel, color in (
        (axes[0], values, "Tiempo de ejecución", "Segundos (mediana de 3 corridas)", "#3b6f8f"),
        (axes[1], memory, "Memoria máxima", "MiB (mediana de 3 procesos)", "#6f8d61"),
    ):
        bars = ax.bar(labels, data, color=[color] * len(labels), width=0.58)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        ax.bar_label(bars, fmt="%.1f", padding=3)
    fig.suptitle("Pipeline Bronce → Plata → Oro · misma entrada Bronce")
    fig.text(0.5, 0.01, "Fuente: benchmarks/comparativa.json · Linux, Python 3.12.3 · 3 ejecuciones aisladas por versión",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    target = ROOT / "docs" / "E3" / "evidencias" / "comparativa.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=180, bbox_inches="tight")
    plt.close(fig)


def summarize(rows: list[dict[str, object]], metric: str) -> float:
    return statistics.median(float(row[metric]) for row in rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeticiones", type=int, default=3)
    args = parser.parse_args()
    if args.repeticiones < 2:
        parser.error("usa al menos dos repeticiones por versión")
    OUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    bronze = fingerprint_bronze()
    if not bronze["archivos"]:
        raise SystemExit(f"No se encontraron archivos Bronce en {BRONZE}")
    baseline_pipeline = subprocess.check_output(
        ["git", "show", f"{BASELINE_COMMIT}:{PIPELINE_PATH}"], cwd=ROOT, text=True)
    baseline_parser = subprocess.check_output(
        ["git", "show", f"{BASELINE_COMMIT}:{PARSER_PATH}"], cwd=ROOT, text=True)
    rows: list[dict[str, object]] = []
    baseline_outputs: dict[str, str] | None = None
    optimized_outputs: dict[str, str] | None = None
    with tempfile.TemporaryDirectory(prefix="tdl-e3-benchmark-") as temp:
        temp_path = Path(temp)
        baseline_file = temp_path / "pipeline_e2.py"
        parser_file = temp_path / "sniim_e2.py"
        baseline_file.write_text(baseline_pipeline, encoding="utf-8")
        parser_file.write_text(baseline_parser, encoding="utf-8")
        for number in range(1, args.repeticiones + 1):
            for kind in ("base", "optimizado"):
                output = temp_path / f"{kind}_{number}"
                output.mkdir()
                item = execute(kind, baseline_file if kind == "base" else ROOT / PIPELINE_PATH,
                               parser_file if kind == "base" else None, output, number)
                rows.append(item)
                if item["errors"]:
                    raise SystemExit(f"Falló {kind}, corrida {number}; consulta {item['log']}")
                hashes = csv_hashes(output)
                if kind == "base":
                    baseline_outputs = hashes
                else:
                    optimized_outputs = hashes
                    if baseline_outputs != optimized_outputs:
                        raise SystemExit("Las salidas CSV difieren entre baseline y optimizado")
    baseline = [row for row in rows if row["version"] == "base"]
    optimized = [row for row in rows if row["version"] == "optimizado"]
    before_time, after_time = summarize(baseline, "seconds"), summarize(optimized, "seconds")
    before_memory, after_memory = summarize(baseline, "peak_rss_kib"), summarize(optimized, "peak_rss_kib")
    improvement = lambda before, after: round((before - after) / before * 100, 2) if before else None
    summary = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "baseline": {"referencia": BASELINE_COMMIT, "commit": subprocess.check_output(
            ["git", "rev-parse", f"{BASELINE_COMMIT}^{{commit}}"], cwd=ROOT, text=True).strip()},
        "optimizado": {"referencia": "working_tree", "codigo_sha256": hashlib.sha256(
            "\n".join(f"{path} {sha256(ROOT / path)}" for path in (PIPELINE_PATH, PARSER_PATH)).encode()
        ).hexdigest()},
        "condiciones": {"repeticiones_por_version": args.repeticiones,
                        "python": sys.version.split()[0], "plataforma": sys.platform,
                        "bronce": bronze, "metricas_resumidas": "mediana de procesos aislados"},
        "metricas": {
            "tiempo_segundos": {"antes": before_time, "despues": after_time,
                                "mejora_porcentaje": improvement(before_time, after_time)},
            "memoria_max_mib": {"antes": before_memory / 1024, "despues": after_memory / 1024,
                                "mejora_porcentaje": improvement(before_memory, after_memory)},
            "errores": {"antes": sum(int(r["errors"]) for r in baseline),
                        "despues": sum(int(r["errors"]) for r in optimized)},
            "registros_procesados": {"antes": int(baseline[0]["records_parsed"]),
                                     "despues": int(optimized[0]["records_parsed"])},
            "registros_cuarentena": {"antes": int(baseline[0]["records_quarantined"]),
                                     "despues": int(optimized[0]["records_quarantined"])},
            "filas_oro": {"antes": int(baseline[0]["gold_rows"]),
                          "despues": int(optimized[0]["gold_rows"])},
            "conflictos_duplicados": {"antes": int(baseline[0]["duplicate_conflicts"]),
                                      "despues": int(optimized[0]["duplicate_conflicts"])},
            "salidas_csv_identicas": baseline_outputs == optimized_outputs,
        },
        "corridas": rows,
        "archivos_salida_sha256": baseline_outputs,
    }
    (OUT / "comparativa.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "resultados.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    make_chart(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
