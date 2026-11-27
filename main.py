"""Punto de entrada único del sistema TDL.

    python main.py diaria     [--fecha AAAA-MM-DD] [--solo sniim|clima]
    python main.py historica  [--inicio ... --fin ...] [--dry-run]
    python main.py validar
    python main.py objetivos  [--desde ... --hasta ...]
    python main.py psp        <subcomando de calidad.psp>
    python main.py capas      [--bronze-dir ... --data-dir ...] (pipeline E1)
    python main.py e2         [--solo-procesar] (captura INEGI, E1 y productos geoespaciales)
    python main.py observatorio [--horizonte 3] (pronósticos, backtest, exportación y tablero)
    python main.py inteligencia [--corte AAAA-MM] (margen del productor, plazas, calendario y señales)
    python main.py reporte (reporte de inteligencia imprimible y API estática de datos)
    python main.py preguntas (preguntas del agricultor respondidas con datos y calculadora de precio)
    python main.py portal (página de inicio para clientes y panel de administración)
    python main.py mapa (mapa interactivo: producción municipal y centrales de abasto)
    python main.py exportacion (mercados extranjeros por fruta: destinos, oportunidades y prima de exportación)
    python main.py comtrade-captura [--anios ...] (UN Comtrade por fruta y año + tipo de cambio USD/MXN)
    python main.py comercial  <subcomando> (seguimiento local de oportunidades y costeo)
    python main.py siap [archivo.csv] (producción municipal SIAP + mapa INEGI)
    python main.py siap-captura --anios 2016 ... 2025 (cierres agrícolas anuales SIAP a Bronce)
    python main.py comercio-intl [--solo-procesar] (comercio mundial UN Comtrade)
    python main.py precios-catalogo [--fecha AAAA-MM-DD] [--solo-procesar] (frutas publicadas en SNIIM por mercado)
    python main.py mapa-mercados [--solo-procesar] (geografía de plazas nacionales)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Las series del observatorio son cortas: los hilos de BLAS/OpenMP solo agregan sobrecarga (y saturan los
# runners de GitHub Actions). Se fija un hilo antes de importar NumPy, salvo que el usuario lo defina.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")
from datetime import date, timedelta  # noqa: E402 - después de fijar los hilos


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
    elif cmd == "capas":
        from src.tdl_e1.pipeline import main as f
    elif cmd == "e2":
        from src.tdl_e2.geoespacial import main as f
    elif cmd == "exportacion":
        from src.inteligencia.exportacion import main as f
    elif cmd == "mapa":
        from src.inteligencia.mapa import main as f
    elif cmd == "portal":
        from src.inteligencia.portal import main as f
    elif cmd == "preguntas":
        from src.inteligencia.preguntas import main as f
    elif cmd == "reporte":
        from src.inteligencia.reporte import main as f
    elif cmd == "inteligencia":
        from src.inteligencia.comercial import main as f
    elif cmd == "observatorio":
        from src.tdl_e4.observatorio import main as f
    elif cmd == "comercial":
        from scripts.comercial import main as f
    elif cmd == "siap-captura":
        from scripts.capturar_siap import main as f
    elif cmd == "siap":
        from scripts.integrar_siap_colima import main as f
    elif cmd == "comtrade-captura":
        from scripts.capturar_comtrade import main as f
    elif cmd == "comercio-intl":
        from scripts.capturar_comercio_internacional import main as f
    elif cmd == "precios-catalogo":
        from scripts.capturar_sniim_catalogo import main as f
    elif cmd == "mapa-mercados":
        from scripts.preparar_mapa_mercados import main as f
    else:
        print(f"Comando desconocido: {cmd}\n{__doc__}", file=sys.stderr)
        return 2
    return f(resto)


if __name__ == "__main__":
    sys.exit(main())
