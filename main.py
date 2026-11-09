"""Punto de entrada único del sistema TDL.

    python main.py diaria     [--fecha AAAA-MM-DD] [--solo sniim|clima]
    python main.py historica  [--inicio ... --fin ...] [--dry-run]
    python main.py validar
    python main.py objetivos  [--desde ... --hasta ...]
    python main.py psp        <subcomando de calidad.psp>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta


def _objetivos(argv: list[str]) -> int:
    from calidad.objetivos import evaluar_objetivos
    from config.settings import get_settings
    ap = argparse.ArgumentParser(prog="main.py objetivos")
    ap.add_argument("--desde"); ap.add_argument("--hasta")
    a = ap.parse_args(argv)
    hasta = date.fromisoformat(a.hasta) if a.hasta else date.today()
    desde = date.fromisoformat(a.desde) if a.desde else hasta - timedelta(days=29)
    res = evaluar_objetivos(get_settings().bronze_dir, desde, hasta)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, resto = argv[0], argv[1:]
    if cmd == "diaria":
        from scripts.captura_diaria import main as f
    elif cmd == "historica":
        from scripts.captura_historica import main as f
    elif cmd == "validar":
        from scripts.validar_bronce import main as f
    elif cmd == "psp":
        from calidad.psp import main as f
    elif cmd == "objetivos":
        return _objetivos(resto)
    else:
        print(f"Comando desconocido: {cmd}\n{__doc__}", file=sys.stderr)
        return 2
    return f(resto)


if __name__ == "__main__":
    sys.exit(main())
