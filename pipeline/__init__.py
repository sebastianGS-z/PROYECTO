"""Pipeline de datos. En E0: captura hacia la capa bronce (pipeline.captura).

Pendiente para E1 (según el Kit): bronce -> plata -> oro y puertas de calidad.
"""
from pipeline.captura import (  # noqa: F401
    EXIT_CODES, capturar_clima, capturar_sniim, disparador, exit_code, meses, ultimos_36_meses,
)
