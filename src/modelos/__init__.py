"""Módulo de modelos de datos e inteligencia comercial para el OAIC.

Proporciona entidades, enumeraciones compatibles con persistencia CSV y funciones
de validación para la gestión de clientes, proveedores, cotizaciones, logística
y viabilidad de oportunidades agroalimentarias.
"""
from __future__ import annotations

from src.modelos.comercial import (
    ClientePotencial,
    Cotizacion,
    FichaOportunidad,
    OperacionPiloto,
    Proveedor,
    RutaLogistica,
)
from src.modelos.enums import (
    CadenaEnum,
    EstatusEmbudo,
    EstatusVerificacion,
    Moneda,
    NivelEvidencia,
    Segmento,
    TipoCotizacion,
    TipoPrecio,
)
from src.modelos.persistencia import AlmacenComercial, esquemas
from src.modelos.validacion import (
    es_vigente,
    nivel_completitud,
    validar_cliente,
    validar_cotizacion,
    validar_oportunidad,
    validar_piloto,
    validar_proveedor,
    validar_ruta,
)

__all__ = [
    # Enums
    "CadenaEnum",
    "Segmento",
    "EstatusEmbudo",
    "TipoCotizacion",
    "NivelEvidencia",
    "EstatusVerificacion",
    "Moneda",
    "TipoPrecio",
    # Modelos
    "ClientePotencial",
    "Proveedor",
    "Cotizacion",
    "RutaLogistica",
    "OperacionPiloto",
    "FichaOportunidad",
    # Validaciones
    "validar_cliente",
    "validar_proveedor",
    "validar_cotizacion",
    "validar_ruta",
    "validar_piloto",
    "validar_oportunidad",
    "es_vigente",
    "nivel_completitud",
    "AlmacenComercial",
    "esquemas",
]
