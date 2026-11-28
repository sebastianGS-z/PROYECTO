"""Directorio Estadístico Nacional de Unidades Económicas (DENUE, INEGI): descarga masiva oficial a Bronce.

    python main.py denue-captura                       # Colima, Jalisco, Michoacán, CDMX y Nuevo León
    python main.py denue-captura --estados 06 14

Descarga el CSV oficial comprimido por estado (no requiere token; la API del DENUE sí). Extractor ético:
robots.txt (fallo cerrado), User-Agent identificable y pausa por dominio. El ZIP original se guarda en
Bronce con su SHA-256; por su tamaño **no se versiona en Git** (se conserva su ``.meta.json``). El directorio
filtrado de compradores de fruta lo arma ``python main.py asistente``.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path

try:
    from scripts import _bootstrap  # noqa: F401
except ImportError:
    import _bootstrap  # type: ignore # noqa: F401

from almacenamiento.bronze_writer import BronzeWriter
from almacenamiento.manifest import new_run_id
from config.settings import get_settings, setup_logging
from extractores.base import BaseExtractor, RawCapture

URL = "https://www.inegi.org.mx/contenidos/masiva/denue/denue_{clave}_csv.zip"
ESTADOS = {"06": "Colima", "14": "Jalisco", "16": "Michoacán", "09": "Ciudad de México", "19": "Nuevo León"}


class DenueExtractor(BaseExtractor):
    fuente = "denue"

    def estado(self, clave: str) -> RawCapture:
        r = self.get(URL.format(clave=clave))
        if not r.content.startswith(b"PK"):
            raise ValueError(f"INEGI no devolvió un ZIP para el estado {clave}")
        with zipfile.ZipFile(BytesIO(r.content)) as z:
            csvs = [n for n in z.namelist() if n.lower().endswith(".csv") and "diccionario" not in n.lower()]
        return RawCapture(fuente=self.fuente, url=r.url, contenido=r.content, formato="zip", http_status=r.status_code,
                          registros=len(csvs), estado="ok",
                          metadatos={"etiqueta": f"denue-{clave}-{ESTADOS.get(clave, clave)}", "estado_clave": clave,
                                     "estado": ESTADOS.get(clave, clave), "archivos_csv": csvs,
                                     "nota": "Descarga masiva oficial del DENUE (INEGI). Información pública declarada por cada unidad económica."})


def zips(bronze: Path) -> dict[str, Path]:
    """Último ZIP capturado por estado: {clave: ruta}."""
    carpeta = bronze / "denue"
    res: dict[str, Path] = {}
    for p in sorted(carpeta.rglob("*.zip"), key=lambda x: x.name.rsplit("__", 1)[-1]) if carpeta.is_dir() else []:
        meta = Path(str(p) + ".meta.json")
        clave = json.loads(meta.read_text(encoding="utf-8")).get("metadatos", {}).get("estado_clave") if meta.is_file() else None
        res[clave or p.name.split("denue-")[-1][:2]] = p
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--estados", nargs="+", default=list(ESTADOS))
    a = ap.parse_args(argv)
    settings = get_settings()
    run_id = new_run_id()
    setup_logging(run_id, settings)
    ext, writer, salida = DenueExtractor(settings), BronzeWriter(settings.bronze_dir), {}
    for clave in a.estados:
        cap = ext.estado(clave)
        salida[clave] = {"archivo": str(writer.write(cap, run_id).ruta), "mb": round(len(cap.contenido) / 1e6, 1)}
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
