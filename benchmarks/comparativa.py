#!/usr/bin/env python3
"""Compara los tags e2 y e3 con entradas Bronce idénticas.

Ejemplo: python benchmarks/comparativa.py --repeticiones 7 --semilla 20261120
Usa las mismas capturas Bronce, ejecuta cada versión en un proceso aislado,
aleatoriza qué versión corre primero en cada par y exige hashes de salida
idénticos. E3 permanece congelado aunque el pipeline evolucione después.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
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
OPTIMIZED_COMMIT = "e3"
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
spec = importlib.util.spec_from_file_location(f"benchmark_e1_{kind}", pipeline_file)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
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
            output_dir: Path, run_number: int, execution_order: int) -> dict[str, object]:
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
    return {"version": kind, "run": run_number, "orden_global": execution_order, "errors": 0, **result,
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
        (axes[0], values, "Tiempo de ejecución", f"Segundos (mediana de {summary['condiciones']['repeticiones_por_version']} pares)", "#3b6f8f"),
        (axes[1], memory, "Memoria máxima", f"MiB (mediana de {summary['condiciones']['repeticiones_por_version']} pares)", "#6f8d61"),
    ):
        bars = ax.bar(labels, data, color=[color] * len(labels), width=0.58)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        ax.bar_label(bars, fmt="%.1f", padding=3)
    fig.suptitle("Pipeline Bronce → Plata → Oro · misma entrada Bronce")
    fig.text(0.5, 0.01, f"Fuente: benchmarks/comparativa.json · {summary['condiciones']['plataforma']}, Python {summary['condiciones']['python']} · e2 vs e3, pares intercalados",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    target = ROOT / "docs" / "E3" / "evidencias" / "comparativa.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=180, bbox_inches="tight")
    plt.close(fig)


def summarize(rows: list[dict[str, object]], metric: str) -> float:
    return statistics.median(float(row[metric]) for row in rows)


def distribution(rows: list[dict[str, object]], metric: str) -> dict[str, float]:
    values = [float(row[metric]) for row in rows]
    quartiles = statistics.quantiles(values, n=4, method="inclusive")
    return {"minimo": min(values), "q1": quartiles[0], "mediana": statistics.median(values),
            "q3": quartiles[2], "maximo": max(values)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeticiones", type=int, default=7)
    parser.add_argument("--semilla", type=int, default=20261120)
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
    optimized_pipeline = subprocess.check_output(
        ["git", "show", f"{OPTIMIZED_COMMIT}:{PIPELINE_PATH}"], cwd=ROOT, text=True)
    optimized_parser = subprocess.check_output(
        ["git", "show", f"{OPTIMIZED_COMMIT}:{PARSER_PATH}"], cwd=ROOT, text=True)
    rows: list[dict[str, object]] = []
    baseline_outputs: dict[str, str] | None = None
    optimized_outputs: dict[str, str] | None = None
    with tempfile.TemporaryDirectory(prefix="tdl-e3-benchmark-") as temp:
        temp_path = Path(temp)
        baseline_file = temp_path / "pipeline_e2.py"
        parser_file = temp_path / "sniim_e2.py"
        optimized_file = temp_path / "pipeline_e3.py"
        optimized_parser_file = temp_path / "sniim_e3.py"
        baseline_file.write_text(baseline_pipeline, encoding="utf-8")
        parser_file.write_text(baseline_parser, encoding="utf-8")
        optimized_file.write_text(optimized_pipeline, encoding="utf-8")
        optimized_parser_file.write_text(optimized_parser, encoding="utf-8")
        rng = random.Random(args.semilla)
        run_numbers = {"base": 0, "optimizado": 0}
        for number in range(1, args.repeticiones + 1):
            pair_order = ["base", "optimizado"]
            rng.shuffle(pair_order)
            for kind in pair_order:
                run_numbers[kind] += 1
                output = temp_path / f"{kind}_{number}"
                output.mkdir()
                item = execute(kind, baseline_file if kind == "base" else optimized_file,
                               parser_file if kind == "base" else optimized_parser_file,
                               output, run_numbers[kind], len(rows) + 1)
                rows.append(item)
                if item["errors"]:
                    raise SystemExit(f"Falló {kind}, corrida {run_numbers[kind]}; consulta {item['log']}")
                hashes = csv_hashes(output)
                if kind == "base":
                    if baseline_outputs is not None and baseline_outputs != hashes:
                        raise SystemExit("Las salidas CSV del baseline cambiaron entre repeticiones")
                    baseline_outputs = hashes
                else:
                    if optimized_outputs is not None and optimized_outputs != hashes:
                        raise SystemExit("Las salidas CSV optimizadas cambiaron entre repeticiones")
                    optimized_outputs = hashes
                if baseline_outputs is not None and optimized_outputs is not None and baseline_outputs != optimized_outputs:
                    raise SystemExit("Las salidas CSV difieren entre los tags e2 y e3")
    baseline = [row for row in rows if row["version"] == "base"]
    optimized = [row for row in rows if row["version"] == "optimizado"]
    before_time, after_time = summarize(baseline, "seconds"), summarize(optimized, "seconds")
    before_memory, after_memory = summarize(baseline, "peak_rss_kib"), summarize(optimized, "peak_rss_kib")
    improvement = lambda before, after: round((before - after) / before * 100, 2) if before else None
    summary = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "baseline": {"referencia": BASELINE_COMMIT, "commit": subprocess.check_output(
            ["git", "rev-parse", f"{BASELINE_COMMIT}^{{commit}}"], cwd=ROOT, text=True).strip()},
        "optimizado": {"referencia": OPTIMIZED_COMMIT, "commit": subprocess.check_output(
            ["git", "rev-parse", f"{OPTIMIZED_COMMIT}^{{commit}}"], cwd=ROOT, text=True).strip(),
            "codigo_sha256": hashlib.sha256((optimized_pipeline + "\n" + optimized_parser).encode()).hexdigest()},
        "condiciones": {"repeticiones_por_version": args.repeticiones,
                        "python": sys.version.split()[0], "plataforma": sys.platform,
                        "semilla_orden": args.semilla,
                        "orden": "pares e2/e3; el orden dentro de cada par se aleatoriza con semilla fija",
                        "bronce": bronze,
                        "metricas_resumidas": "mediana, cuartiles y rango de procesos aislados pareados"},
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
        "distribucion": {
            "tiempo_segundos": {"e2": distribution(baseline, "seconds"),
                                "e3": distribution(optimized, "seconds")},
            "memoria_max_mib": {"e2": {k: v / 1024 for k, v in distribution(baseline, "peak_rss_kib").items()},
                                "e3": {k: v / 1024 for k, v in distribution(optimized, "peak_rss_kib").items()}},
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
