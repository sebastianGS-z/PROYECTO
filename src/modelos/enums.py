"""Enumeraciones de cadena para el sistema de inteligencia comercial del OAIC.

Define tipos de datos categóricos compatibles con serialización CSV y comparaciones
insensibles a mayúsculas/minúsculas.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class CadenaEnum(str, Enum):
    """Clase base para enumeraciones de cadena compatibles con CSV."""

    @classmethod
    def _missing_(cls, value: object) -> Any:
        """Permite resolución flexible e insensible a mayúsculas/minúsculas."""
        if isinstance(value, str):
            val_norm = value.strip().lower()
            for member in cls:
                if member.value.lower() == val_norm or member.name.lower() == val_norm:
                    return member
        return super()._missing_(value)

    def __str__(self) -> str:
        """Representación en cadena usando el valor subyacente."""
        return self.value


class Segmento(CadenaEnum):
    """Segmentos de compradores o participantes en la cadena agroalimentaria."""

    MAYORISTA = "mayorista"
    RESTAURANTE = "restaurante"
    HOTEL = "hotel"
    EMPACADORA = "empacadora"
    PROCESADOR = "procesador"
    TIENDA = "tienda"
    DISTRIBUIDOR = "distribuidor"
    OTRO = "otro"


class EstatusEmbudo(CadenaEnum):
    """Fases del embudo de prospección y cierre comercial."""

    POR_INVESTIGAR = "por_investigar"
    IDENTIFICADO = "identificado"
    CONTACTO_SOLICITADO = "contacto_solicitado"
    CONVERSACION = "conversacion"
    NECESIDAD_VERIFICADA = "necesidad_verificada"
    COTIZACION = "cotizacion"
    PILOTO = "piloto"
    NEGOCIACION = "negociacion"
    ACTIVO = "activo"
    DESCARTADO = "descartado"


class TipoCotizacion(CadenaEnum):
    """Sentido o naturaleza de la cotización comercial."""

    COMPRA = "compra"
    VENTA = "venta"


class NivelEvidencia(CadenaEnum):
    """Grado de certeza o respaldo probatorio del dato registrado."""

    CONFIRMADO = "confirmado"
    ESTIMADO = "estimado"
    SUPUESTO = "supuesto"
    PENDIENTE = "pendiente"


class EstatusVerificacion(CadenaEnum):
    """Estado de validación de la información de participantes y cotizaciones."""

    SIN_VERIFICAR = "sin_verificar"
    EN_PROCESO = "en_proceso"
    VERIFICADO = "verificado"
    DESACTUALIZADO = "desactualizado"
    DESCARTADO = "descartado"


class Moneda(CadenaEnum):
    """Divisa de la cotización o transacción."""

    MXN = "MXN"
    USD = "USD"


class TipoPrecio(CadenaEnum):
    """Naturaleza y procedencia del dato de precio registrado."""

    MAYORISTA_SNIIM = "mayorista_sniim"
    PRODUCTOR = "productor"
    PROVEEDOR_COTIZADO = "proveedor_cotizado"
    CLIENTE_OFRECIDO = "cliente_ofrecido"
    OPERACION_CERRADA = "operacion_cerrada"


__all__ = [
    "CadenaEnum",
    "Segmento",
    "EstatusEmbudo",
    "TipoCotizacion",
    "NivelEvidencia",
    "EstatusVerificacion",
    "Moneda",
    "TipoPrecio",
]
