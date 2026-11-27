"""Auditoría cruzada asistida: mide el observatorio de otro equipo y redacta un borrador de hallazgos.

    python -m calidad.auditar_repo https://github.com/<equipo>/<repo> --etiqueta e1 --salida docs/calidad/auditoria/borrador_emitida.md

Qué hace (sin modificar el repositorio auditado):

1. Clona la etiqueta indicada en una carpeta temporal.
2. Verifica la presencia de los entregables que pide la guía (fichas, relatorías, ética, registros PSP, workflows).
3. Busca patrones de secretos en el árbol de trabajo.
4. Si existe ``requirements.txt``, crea un entorno aislado e intenta ``pytest`` con cobertura (con límite de tiempo).
5. Mide completitud y unicidad ISO/IEC 25012 de los CSV de su capa oro (``data/oro`` o ``data/gold``).

El resultado es un **borrador**: cada hallazgo trae su evidencia y una severidad sugerida que el equipo
auditor debe revisar antes de entregarlo. Nada se publica ni se envía al otro equipo.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ENTREGABLES = {
    "README.md": "README con descripción y cómo ejecutar",
    "docs/E0/ENTREGA.md": "Ficha de entrega E0", "docs/E1/ENTREGA.md": "Ficha de entrega E1",
    "docs/relatoria-E1.md": "Relatoría E1", "docs/etica-datos.md": "Declaración de ética (E2)",
}
PATRONES_SECRETOS = [r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{20,}",
                     r"-----BEGIN [A-Z ]*PRIVATE KEY", r"xox[baprs]-[A-Za-z0-9-]{10,}", r"AIza[0-9A-Za-z_-]{35}",
                     r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"]


@dataclass
class Hallazgo:
    id: str
    severidad: str
    caracteristica: str
    hallazgo: str
    evidencia: str
    recomendacion: str


def clonar(url: str, etiqueta: str | None, destino: Path) -> Path:
    cmd = ["git", "clone", "--depth", "1"] + (["--branch", etiqueta] if etiqueta else []) + [url, str(destino)]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
    return destino


def revisar_entregables(repo: Path) -> list[Hallazgo]:
    out = []
    for i, (rel, desc) in enumerate(ENTREGABLES.items(), 1):
        if not (repo / rel).is_file():
            out.append(Hallazgo(f"AUD-E{i:02d}", "mayor", "Adecuación funcional", f"No se encontró {desc}.", f"Ruta esperada `{rel}` ausente en la etiqueta auditada.",
                                f"Agregar `{rel}` según la plantilla del Kit."))
    psp = list((repo / "calidad").glob("defectos-*.csv")) + list((repo / "calidad").glob("tiempo-*.csv")) if (repo / "calidad").is_dir() else []
    vacios = [p.name for p in psp if sum(1 for _ in p.open(encoding="utf-8", errors="ignore")) <= 1]
    if not psp:
        out.append(Hallazgo("AUD-P01", "mayor", "Proceso (PSP)", "No hay registros PSP de defectos y tiempo.", "`calidad/defectos-*.csv` y `tiempo-*.csv` ausentes.", "Abrir un registro por integrante."))
    elif vacios:
        out.append(Hallazgo("AUD-P02", "menor", "Proceso (PSP)", f"Registros PSP sin datos: {', '.join(vacios)}.", "Solo contienen encabezado.", "Registrar tiempo y defectos de forma continua."))
    wf = list((repo / ".github/workflows").glob("*.yml")) if (repo / ".github/workflows").is_dir() else []
    texto_wf = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in wf)
    if "schedule" not in texto_wf:
        out.append(Hallazgo("AUD-C01", "crítico", "Fiabilidad", "No hay captura programada en GitHub Actions.", "Ningún workflow contiene `schedule:`.", "Programar la captura diaria."))
    for clave, nombre in (("pytest", "pruebas"), ("ruff", "linter"), ("cov", "cobertura mínima")):
        if clave not in texto_wf and not (clave == "ruff" and ("flake8" in texto_wf or "pylint" in texto_wf)):
            out.append(Hallazgo(f"AUD-C-{clave}", "mayor", "Mantenibilidad", f"La integración continua no ejecuta {nombre}.", f"`{clave}` no aparece en `.github/workflows/`.",
                                f"Agregar {nombre} a la CI en cada push."))
    return out


def buscar_secretos(repo: Path) -> list[Hallazgo]:
    encontrados = []
    for p in repo.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.stat().st_size > 2_000_000 or p.suffix.lower() in {".png", ".jpg", ".pdf", ".parquet", ".zip", ".m4a"}:
            continue
        texto = p.read_text(encoding="utf-8", errors="ignore")
        for pat in PATRONES_SECRETOS:
            if re.search(pat, texto):
                encontrados.append(str(p.relative_to(repo)))
                break
    if (repo / ".env").is_file():
        encontrados.append(".env (archivo de configuración local versionado)")
    if not encontrados:
        return []
    return [Hallazgo("AUD-S01", "crítico", "Seguridad", "Posibles secretos en el repositorio.", "Coincidencias en: " + ", ".join(encontrados[:10]),
                     "Revocar las credenciales, retirarlas del historial y usar secretos de GitHub.")]


def correr_pruebas(repo: Path, timeout: int = 900) -> tuple[list[Hallazgo], str]:
    req = repo / "requirements.txt"
    if not req.is_file():
        return [Hallazgo("AUD-R01", "mayor", "Portabilidad", "Sin `requirements.txt`: no se puede reproducir el entorno.", "Archivo ausente.", "Versionar dependencias con versiones.")], "sin requirements.txt"
    env_dir = repo.parent / "venv_auditoria"
    venv.EnvBuilder(with_pip=True).create(env_dir)
    py = env_dir / "bin" / "python"
    inst = subprocess.run([str(py), "-m", "pip", "install", "-q", "-r", str(req), "pytest", "pytest-cov"], cwd=repo, capture_output=True, text=True, timeout=timeout)
    if inst.returncode:
        return [Hallazgo("AUD-R02", "mayor", "Portabilidad", "Las dependencias no se instalan en un entorno limpio.", inst.stderr[-400:], "Fijar versiones compatibles (archivo de bloqueo).")], "instalación fallida"
    r = subprocess.run([str(py), "-m", "pytest", "-q", "--cov=.", "--cov-report=term", "-p", "no:cacheprovider"], cwd=repo, capture_output=True, text=True, timeout=timeout)
    salida = r.stdout[-3000:]
    cov = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", salida)
    out = []
    if r.returncode not in (0, 5):
        out.append(Hallazgo("AUD-T01", "mayor", "Adecuación funcional", "Las pruebas automáticas fallan en un clon limpio.", salida.strip().splitlines()[-1] if salida.strip() else r.stderr[-300:],
                            "Corregir las pruebas o el entorno antes de la siguiente entrega."))
    if cov and int(cov.group(1)) < 60:
        out.append(Hallazgo("AUD-T02", "mayor", "Mantenibilidad", f"Cobertura de pruebas {cov.group(1)} % (< 60 % del Sello TDL).", "pytest --cov=. en clon limpio.", "Agregar pruebas del pipeline y la puerta de calidad."))
    return out, salida


def medir_oro(repo: Path) -> tuple[list[Hallazgo], list[str]]:
    carpetas = [repo / "data/oro", repo / "data/gold"]
    csvs = [p for c in carpetas if c.is_dir() for p in c.glob("*.csv")]
    if not csvs:
        return [Hallazgo("AUD-D01", "mayor", "ISO/IEC 25012 · completitud", "No hay capa oro versionada para medir.", "`data/oro` y `data/gold` vacías o ausentes.", "Publicar la capa oro con diccionario.")], []
    out, notas = [], []
    for p in csvs:
        df = pd.read_csv(p, low_memory=False)
        comp = float(df.notna().to_numpy().mean()) if df.size else 0.0
        dup = int(df.duplicated().sum())
        notas.append(f"`{p.relative_to(repo)}`: {len(df)} filas, completitud de celdas {comp:.1%}, filas duplicadas {dup}")
        if comp < 0.95:
            out.append(Hallazgo(f"AUD-D-{p.stem}", "mayor", "ISO/IEC 25012 · completitud", f"Completitud de {p.name}: {comp:.1%} (< 95 %).", notas[-1], "Documentar nulos por diseño o completarlos en el pipeline."))
        if dup:
            out.append(Hallazgo(f"AUD-U-{p.stem}", "menor", "ISO/IEC 25012 · unicidad", f"{dup} filas duplicadas en {p.name}.", notas[-1], "Agregar regla de unicidad en la puerta de calidad."))
    return out, notas


def informe(url: str, etiqueta: str | None, hallazgos: list[Hallazgo], notas: list[str], pruebas: str) -> str:
    lineas = ["# Borrador de auditoría cruzada emitida", "",
         f"- Repositorio auditado: {url} · etiqueta `{etiqueta or 'rama por defecto'}`",
         "- Generado con `python -m calidad.auditar_repo`. **Borrador:** el equipo auditor revisa cada severidad y agrega los hallazgos de la revisión manual "
         "(tablero, pronóstico, relatoría) antes de entregarlo.", "",
         "## Mediciones", *[f"- {n}" for n in notas], "", "Salida de pruebas (final):", "", "```", pruebas.strip()[-1500:] or "(no ejecutadas)", "```", "",
         "## Hallazgos", "", "| ID | Severidad | Característica | Hallazgo | Evidencia | Recomendación |", "|---|---|---|---|---|---|"]
    orden = {"crítico": 0, "mayor": 1, "menor": 2}
    for h in sorted(hallazgos, key=lambda h: orden.get(h.severidad, 3)):
        lineas.append(f"| {h.id} | {h.severidad} | {h.caracteristica} | {h.hallazgo} | {h.evidencia.replace('|', '/')} | {h.recomendacion} |")
    if not hallazgos:
        lineas.append("| — | — | — | Sin hallazgos automáticos | — | Completar con revisión manual |")
    lineas += ["", "## Revisión manual pendiente (ISO/IEC 25010)", "",
          "- Capacidad de interacción: ¿un cliente entiende el tablero sin ayuda?",
          "- Adecuación funcional: ¿el pronóstico tiene intervalo y se eligió por error fuera de muestra?",
          "- Fiabilidad: ¿la bitácora demuestra 7 días o más de captura con MTBF/MTTR calculados?",
          "- Ética: ¿robots.txt, User-Agent identificable, cero datos personales?"]
    return "\n".join(lineas) + "\n"


def auditar(url: str, etiqueta: str | None = None, correr: bool = True) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        repo = clonar(url, etiqueta, Path(tmp) / "repo")
        hallazgos = revisar_entregables(repo) + buscar_secretos(repo)
        pruebas = ""
        if correr:
            h, pruebas = correr_pruebas(repo)
            hallazgos += h
        h, notas = medir_oro(repo)
        hallazgos += h
        return informe(url, etiqueta, hallazgos, notas, pruebas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--etiqueta", default="e1")
    ap.add_argument("--salida", type=Path, default=Path("docs/calidad/auditoria/borrador_emitida.md"))
    ap.add_argument("--sin-pruebas", action="store_true", help="no instalar dependencias ni correr pytest")
    a = ap.parse_args(argv)
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(auditar(a.url, a.etiqueta, correr=not a.sin_pruebas), encoding="utf-8")
    print(f"Borrador de auditoría: {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
