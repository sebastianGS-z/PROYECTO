"""Módulo de economía y costeo del OAIC.

Proporciona modelos de cálculo de costo puesto en destino, análisis de
contribución y viabilidad económica por escenarios, y motor de priorización
de oportunidades comerciales para la cadena agroalimentaria de Colima.
"""
from __future__ import annotations

from .costeo import (
    ComponenteCosto,
    CostoPuestoEnDestino,
    Escenario,
    ModeloEconomico,
    calcular_capital_trabajo,
    calcular_costo_merma,
)
from .priorizacion import (
    CRITERIOS_DEFAULT,
    CriterioPriorizacion,
    PuntuacionCriterio,
    comparar_oportunidades,
    matriz_priorizacion,
    puntuar_oportunidad,
    validar_pesos,
)

__all__ = [
    "ComponenteCosto",
    "CostoPuestoEnDestino",
    "Escenario",
    "ModeloEconomico",
    "calcular_costo_merma",
    "calcular_capital_trabajo",
    "CriterioPriorizacion",
    "PuntuacionCriterio",
    "CRITERIOS_DEFAULT",
    "validar_pesos",
    "puntuar_oportunidad",
    "comparar_oportunidades",
    "matriz_priorizacion",
]
