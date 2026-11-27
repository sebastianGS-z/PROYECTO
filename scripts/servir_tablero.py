#!/usr/bin/env python3
"""Sirve el repositorio localmente sin conservar versiones antiguas en caché."""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="interfaz de red local")
    parser.add_argument("--port", type=int, default=8000, help="puerto HTTP")
    args = parser.parse_args()
    if not (ROOT / "tablero" / "index.html").is_file():
        parser.error("falta tablero/index.html; primero ejecuta python main.py observatorio")
    handler = partial(NoCacheHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"OAIC disponible en http://{args.host}:{args.port}/tablero/ (Ctrl+C para detener)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
