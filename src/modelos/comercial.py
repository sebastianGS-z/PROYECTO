"""Modelos de datos para el sistema de inteligencia comercial del OAIC.

Define las entidades principales para clientes potenciales, proveedores,
cotizaciones, rutas logísticas, operaciones piloto y fichas de oportunidad,
con soporte para serialización y deserialización CSV.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, TypeVar

from src.modelos.enums import (
    EstatusEmbudo,
    EstatusVerificacion,
    Moneda,
    NivelEvidencia,
    Segmento,
    TipoCotizacion,
)

TEnum = TypeVar("TEnum", bound=Enum)


def _generar_uuid_corto() -> str:
    """Genera un identificador hexadecimal corto de 12 caracteres basado en UUID4."""
    return uuid.uuid4().hex[:12]


def _parse_str(val: Any, default: str = "") -> str:
    """Parsea una cadena limpiando espacios y valores nulos textuales."""
    if val is None:
        return default
    s = str(val).strip()
    if s.lower() in ("none", "null", "nan"):
        return default
    return s


def _parse_str_or_none(val: Any) -> str | None:
    """Parsea una cadena retornando None si está vacía o representa un nulo."""
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return None
    return s


def _parse_float(val: Any) -> float | None:
    """Parsea un número flotante de forma segura, retornando None si no es válido."""
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_int(val: Any) -> int | None:
    """Parsea un entero de forma segura admitiendo representación decimal (ej. '10.0')."""
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _parse_bool(val: Any) -> bool:
    """Parsea valores booleanos admitiendo representaciones comunes en texto."""
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("true", "1", "t", "yes", "si", "sí", "s", "verdadero")


def _parse_date(val: Any) -> date | None:
    """Parsea un valor a fecha en formato ISO (YYYY-MM-DD)."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return None
    if "T" in s or " " in s:
        s = s.split("T")[0].split(" ")[0]
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _parse_datetime(val: Any) -> datetime:
    """Parsea un valor a fecha y hora en formato ISO 8601."""
    if val is None:
        return datetime.now().replace(microsecond=0)
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return datetime.now().replace(microsecond=0)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return datetime.now().replace(microsecond=0)


def _parse_enum(enum_cls: type[TEnum], val: Any, default: TEnum | None = None) -> TEnum:
    """Parsea un valor a una enumeración, admitiendo mayúsculas o valor predeterminado."""
    if isinstance(val, enum_cls):
        return val
    if val is None:
        if default is not None:
            return default
        raise ValueError(f"Valor nulo no permitido para {enum_cls.__name__}")
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        if default is not None:
            return default
        raise ValueError(f"Valor vacío no permitido para {enum_cls.__name__}")
    try:
        return enum_cls(s)
    except ValueError:
        val_lower = s.lower()
        for member in enum_cls:
            if member.value.lower() == val_lower or member.name.lower() == val_lower:
                return member
        if default is not None:
            return default
        raise ValueError(f"'{val}' no es un valor válido para {enum_cls.__name__}") from None


def _parse_list_str(val: Any) -> list[str]:
    """Parsea una lista de cadenas separadas por coma."""
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return []
    return [part.strip() for part in s.split(",") if part.strip()]


@dataclass
class ClientePotencial:
    """Registro de cliente o comprador potencial en el embudo comercial."""

    id: str = field(default_factory=_generar_uuid_corto)
    razon_social: str = ""
    segmento: Segmento = Segmento.OTRO
    municipio: str = ""
    estado: str = ""
    actividad_economica: str = ""
    fuente_identificacion: str = ""
    fecha_identificacion: date = field(default_factory=date.today)
    necesidad_declarada: str = ""
    volumen_rango_kg: str = ""
    frecuencia: str = ""
    especificacion: str = ""
    estatus: EstatusEmbudo = EstatusEmbudo.POR_INVESTIGAR
    evidencia_verificacion: str = ""
    ultima_verificacion: date | None = None
    proxima_accion: str = ""
    fecha_proxima_accion: date | None = None
    notas: str = ""
    fecha_registro: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))

    @staticmethod
    def generar_id() -> str:
        """Genera un identificador único corto en formato hexadecimal basado en UUID4."""
        return _generar_uuid_corto()

    def __post_init__(self) -> None:
        """Normaliza tipos de datos tras la inicialización."""
        if not self.id:
            self.id = self.generar_id()
        if not isinstance(self.segmento, Segmento):
            self.segmento = _parse_enum(Segmento, self.segmento, Segmento.OTRO)
        if not isinstance(self.estatus, EstatusEmbudo):
            self.estatus = _parse_enum(EstatusEmbudo, self.estatus, EstatusEmbudo.POR_INVESTIGAR)
        if isinstance(self.fecha_identificacion, str):
            self.fecha_identificacion = _parse_date(self.fecha_identificacion) or date.today()
        if isinstance(self.ultima_verificacion, str):
            self.ultima_verificacion = _parse_date(self.ultima_verificacion)
        if isinstance(self.fecha_proxima_accion, str):
            self.fecha_proxima_accion = _parse_date(self.fecha_proxima_accion)
        if isinstance(self.fecha_registro, str):
            self.fecha_registro = _parse_datetime(self.fecha_registro)

    def to_dict(self) -> dict[str, Any]:
        """Serializa la entidad a diccionario para persistencia en CSV."""
        return {
            "id": self.id,
            "razon_social": self.razon_social,
            "segmento": self.segmento.value if hasattr(self.segmento, "value") else str(self.segmento),
            "municipio": self.municipio,
            "estado": self.estado,
            "actividad_economica": self.actividad_economica,
            "fuente_identificacion": self.fuente_identificacion,
            "fecha_identificacion": self.fecha_identificacion.isoformat() if self.fecha_identificacion else "",
            "necesidad_declarada": self.necesidad_declarada,
            "volumen_rango_kg": self.volumen_rango_kg,
            "frecuencia": self.frecuencia,
            "especificacion": self.especificacion,
            "estatus": self.estatus.value if hasattr(self.estatus, "value") else str(self.estatus),
            "evidencia_verificacion": self.evidencia_verificacion,
            "ultima_verificacion": self.ultima_verificacion.isoformat() if self.ultima_verificacion else "",
            "proxima_accion": self.proxima_accion,
            "fecha_proxima_accion": self.fecha_proxima_accion.isoformat() if self.fecha_proxima_accion else "",
            "notas": self.notas,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClientePotencial:
        """Crea una instancia a partir de un diccionario proveniente de CSV."""
        return cls(
            id=_parse_str(data.get("id")) or cls.generar_id(),
            razon_social=_parse_str(data.get("razon_social")),
            segmento=_parse_enum(Segmento, data.get("segmento"), Segmento.OTRO),
            municipio=_parse_str(data.get("municipio")),
            estado=_parse_str(data.get("estado")),
            actividad_economica=_parse_str(data.get("actividad_economica")),
            fuente_identificacion=_parse_str(data.get("fuente_identificacion")),
            fecha_identificacion=_parse_date(data.get("fecha_identificacion")) or date.today(),
            necesidad_declarada=_parse_str(data.get("necesidad_declarada")),
            volumen_rango_kg=_parse_str(data.get("volumen_rango_kg")),
            frecuencia=_parse_str(data.get("frecuencia")),
            especificacion=_parse_str(data.get("especificacion")),
            estatus=_parse_enum(EstatusEmbudo, data.get("estatus"), EstatusEmbudo.POR_INVESTIGAR),
            evidencia_verificacion=_parse_str(data.get("evidencia_verificacion")),
            ultima_verificacion=_parse_date(data.get("ultima_verificacion")),
            proxima_accion=_parse_str(data.get("proxima_accion")),
            fecha_proxima_accion=_parse_date(data.get("fecha_proxima_accion")),
            notas=_parse_str(data.get("notas")),
            fecha_registro=_parse_datetime(data.get("fecha_registro")),
        )


@dataclass
class Proveedor:
    """Registro de proveedor o productor agroalimentario y su oferta."""

    id: str = field(default_factory=_generar_uuid_corto)
    razon_social: str = ""
    ubicacion: str = ""
    municipio: str = ""
    estado: str = ""
    producto: str = ""
    variedad: str = ""
    presentacion: str = ""
    peso_neto_kg: float | None = None
    calendario_disponibilidad: str = ""
    capacidad_confirmada_kg: float | None = None
    volumen_minimo_kg: float | None = None
    precio_unitario: float | None = None
    moneda: Moneda = Moneda.MXN
    unidad_cotizacion: str = ""
    vigencia_cotizacion: date | None = None
    condiciones_pago: str = ""
    especificacion_calidad: str = ""
    merma_esperada_pct: float | None = None
    trazabilidad: str = ""
    documentacion: str = ""
    tiempo_entrega_dias: int | None = None
    dependencia_temporada: bool = False
    proveedor_alternativo_id: str | None = None
    fuente: str = ""
    fecha_verificacion: date | None = None
    estatus: EstatusVerificacion = EstatusVerificacion.SIN_VERIFICAR
    fecha_registro: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))

    @staticmethod
    def generar_id() -> str:
        """Genera un identificador único corto en formato hexadecimal basado en UUID4."""
        return _generar_uuid_corto()

    def __post_init__(self) -> None:
        """Normaliza tipos de datos tras la inicialización."""
        if not self.id:
            self.id = self.generar_id()
        if not isinstance(self.moneda, Moneda):
            self.moneda = _parse_enum(Moneda, self.moneda, Moneda.MXN)
        if not isinstance(self.estatus, EstatusVerificacion):
            self.estatus = _parse_enum(EstatusVerificacion, self.estatus, EstatusVerificacion.SIN_VERIFICAR)
        if isinstance(self.vigencia_cotizacion, str):
            self.vigencia_cotizacion = _parse_date(self.vigencia_cotizacion)
        if isinstance(self.fecha_verificacion, str):
            self.fecha_verificacion = _parse_date(self.fecha_verificacion)
        if isinstance(self.fecha_registro, str):
            self.fecha_registro = _parse_datetime(self.fecha_registro)
        if isinstance(self.dependencia_temporada, str):
            self.dependencia_temporada = _parse_bool(self.dependencia_temporada)

    def to_dict(self) -> dict[str, Any]:
        """Serializa la entidad a diccionario para persistencia en CSV."""
        return {
            "id": self.id,
            "razon_social": self.razon_social,
            "ubicacion": self.ubicacion,
            "municipio": self.municipio,
            "estado": self.estado,
            "producto": self.producto,
            "variedad": self.variedad,
            "presentacion": self.presentacion,
            "peso_neto_kg": self.peso_neto_kg if self.peso_neto_kg is not None else "",
            "calendario_disponibilidad": self.calendario_disponibilidad,
            "capacidad_confirmada_kg": self.capacidad_confirmada_kg if self.capacidad_confirmada_kg is not None else "",
            "volumen_minimo_kg": self.volumen_minimo_kg if self.volumen_minimo_kg is not None else "",
            "precio_unitario": self.precio_unitario if self.precio_unitario is not None else "",
            "moneda": self.moneda.value if hasattr(self.moneda, "value") else str(self.moneda),
            "unidad_cotizacion": self.unidad_cotizacion,
            "vigencia_cotizacion": self.vigencia_cotizacion.isoformat() if self.vigencia_cotizacion else "",
            "condiciones_pago": self.condiciones_pago,
            "especificacion_calidad": self.especificacion_calidad,
            "merma_esperada_pct": self.merma_esperada_pct if self.merma_esperada_pct is not None else "",
            "trazabilidad": self.trazabilidad,
            "documentacion": self.documentacion,
            "tiempo_entrega_dias": self.tiempo_entrega_dias if self.tiempo_entrega_dias is not None else "",
            "dependencia_temporada": "true" if self.dependencia_temporada else "false",
            "proveedor_alternativo_id": self.proveedor_alternativo_id if self.proveedor_alternativo_id else "",
            "fuente": self.fuente,
            "fecha_verificacion": self.fecha_verificacion.isoformat() if self.fecha_verificacion else "",
            "estatus": self.estatus.value if hasattr(self.estatus, "value") else str(self.estatus),
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Proveedor:
        """Crea una instancia a partir de un diccionario proveniente de CSV."""
        return cls(
            id=_parse_str(data.get("id")) or cls.generar_id(),
            razon_social=_parse_str(data.get("razon_social")),
            ubicacion=_parse_str(data.get("ubicacion")),
            municipio=_parse_str(data.get("municipio")),
            estado=_parse_str(data.get("estado")),
            producto=_parse_str(data.get("producto")),
            variedad=_parse_str(data.get("variedad")),
            presentacion=_parse_str(data.get("presentacion")),
            peso_neto_kg=_parse_float(data.get("peso_neto_kg")),
            calendario_disponibilidad=_parse_str(data.get("calendario_disponibilidad")),
            capacidad_confirmada_kg=_parse_float(data.get("capacidad_confirmada_kg")),
            volumen_minimo_kg=_parse_float(data.get("volumen_minimo_kg")),
            precio_unitario=_parse_float(data.get("precio_unitario")),
            moneda=_parse_enum(Moneda, data.get("moneda"), Moneda.MXN),
            unidad_cotizacion=_parse_str(data.get("unidad_cotizacion")),
            vigencia_cotizacion=_parse_date(data.get("vigencia_cotizacion")),
            condiciones_pago=_parse_str(data.get("condiciones_pago")),
            especificacion_calidad=_parse_str(data.get("especificacion_calidad")),
            merma_esperada_pct=_parse_float(data.get("merma_esperada_pct")),
            trazabilidad=_parse_str(data.get("trazabilidad")),
            documentacion=_parse_str(data.get("documentacion")),
            tiempo_entrega_dias=_parse_int(data.get("tiempo_entrega_dias")),
            dependencia_temporada=_parse_bool(data.get("dependencia_temporada")),
            proveedor_alternativo_id=_parse_str_or_none(data.get("proveedor_alternativo_id")),
            fuente=_parse_str(data.get("fuente")),
            fecha_verificacion=_parse_date(data.get("fecha_verificacion")),
            estatus=_parse_enum(EstatusVerificacion, data.get("estatus"), EstatusVerificacion.SIN_VERIFICAR),
            fecha_registro=_parse_datetime(data.get("fecha_registro")),
        )


@dataclass
class Cotizacion:
    """Registro formal de cotización de compra o venta con vigencia y condiciones."""

    id: str = field(default_factory=_generar_uuid_corto)
    tipo: TipoCotizacion = TipoCotizacion.COMPRA
    contraparte_id: str = ""
    contraparte_nombre: str = ""
    producto: str = ""
    variedad: str = ""
    presentacion: str = ""
    precio_unitario: float = 0.0
    moneda: Moneda = Moneda.MXN
    unidad: str = ""
    volumen_kg: float | None = None
    vigencia_inicio: date = field(default_factory=date.today)
    vigencia_fin: date | None = None
    condiciones_entrega: str = ""
    condiciones_pago: str = ""
    evidencia: str = ""
    nivel_evidencia: NivelEvidencia = NivelEvidencia.PENDIENTE
    fecha_registro: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))

    @staticmethod
    def generar_id() -> str:
        """Genera un identificador único corto en formato hexadecimal basado en UUID4."""
        return _generar_uuid_corto()

    def __post_init__(self) -> None:
        """Normaliza tipos de datos tras la inicialización."""
        if not self.id:
            self.id = self.generar_id()
        if not isinstance(self.tipo, TipoCotizacion):
            self.tipo = _parse_enum(TipoCotizacion, self.tipo, TipoCotizacion.COMPRA)
        if not isinstance(self.moneda, Moneda):
            self.moneda = _parse_enum(Moneda, self.moneda, Moneda.MXN)
        if not isinstance(self.nivel_evidencia, NivelEvidencia):
            self.nivel_evidencia = _parse_enum(NivelEvidencia, self.nivel_evidencia, NivelEvidencia.PENDIENTE)
        if isinstance(self.vigencia_inicio, str):
            self.vigencia_inicio = _parse_date(self.vigencia_inicio) or date.today()
        if isinstance(self.vigencia_fin, str):
            self.vigencia_fin = _parse_date(self.vigencia_fin)
        if isinstance(self.fecha_registro, str):
            self.fecha_registro = _parse_datetime(self.fecha_registro)

    def to_dict(self) -> dict[str, Any]:
        """Serializa la entidad a diccionario para persistencia en CSV."""
        return {
            "id": self.id,
            "tipo": self.tipo.value if hasattr(self.tipo, "value") else str(self.tipo),
            "contraparte_id": self.contraparte_id,
            "contraparte_nombre": self.contraparte_nombre,
            "producto": self.producto,
            "variedad": self.variedad,
            "presentacion": self.presentacion,
            "precio_unitario": self.precio_unitario if self.precio_unitario is not None else "",
            "moneda": self.moneda.value if hasattr(self.moneda, "value") else str(self.moneda),
            "unidad": self.unidad,
            "volumen_kg": self.volumen_kg if self.volumen_kg is not None else "",
            "vigencia_inicio": self.vigencia_inicio.isoformat() if self.vigencia_inicio else "",
            "vigencia_fin": self.vigencia_fin.isoformat() if self.vigencia_fin else "",
            "condiciones_entrega": self.condiciones_entrega,
            "condiciones_pago": self.condiciones_pago,
            "evidencia": self.evidencia,
            "nivel_evidencia": self.nivel_evidencia.value if hasattr(self.nivel_evidencia, "value") else str(self.nivel_evidencia),
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Cotizacion:
        """Crea una instancia a partir de un diccionario proveniente de CSV."""
        return cls(
            id=_parse_str(data.get("id")) or cls.generar_id(),
            tipo=_parse_enum(TipoCotizacion, data.get("tipo"), TipoCotizacion.COMPRA),
            contraparte_id=_parse_str(data.get("contraparte_id")),
            contraparte_nombre=_parse_str(data.get("contraparte_nombre")),
            producto=_parse_str(data.get("producto")),
            variedad=_parse_str(data.get("variedad")),
            presentacion=_parse_str(data.get("presentacion")),
            precio_unitario=_parse_float(data.get("precio_unitario")) or 0.0,
            moneda=_parse_enum(Moneda, data.get("moneda"), Moneda.MXN),
            unidad=_parse_str(data.get("unidad")),
            volumen_kg=_parse_float(data.get("volumen_kg")),
            vigencia_inicio=_parse_date(data.get("vigencia_inicio")) or date.today(),
            vigencia_fin=_parse_date(data.get("vigencia_fin")),
            condiciones_entrega=_parse_str(data.get("condiciones_entrega")),
            condiciones_pago=_parse_str(data.get("condiciones_pago")),
            evidencia=_parse_str(data.get("evidencia")),
            nivel_evidencia=_parse_enum(NivelEvidencia, data.get("nivel_evidencia"), NivelEvidencia.PENDIENTE),
            fecha_registro=_parse_datetime(data.get("fecha_registro")),
        )


@dataclass
class RutaLogistica:
    """Ruta de transporte de carga con estimaciones de costos, tiempos y peajes."""

    id: str = field(default_factory=_generar_uuid_corto)
    origen_municipio: str = ""
    origen_estado: str = ""
    destino_municipio: str = ""
    destino_estado: str = ""
    distancia_km: float | None = None
    tiempo_estimado_h: float | None = None
    peajes_estimados: float | None = None
    tipo_vehiculo: str = ""
    cotizacion_flete: float | None = None
    moneda: Moneda = Moneda.MXN
    operador: str | None = None
    fecha_cotizacion: date | None = None
    temporada: str = ""
    restricciones: str = ""
    fuente: str = ""
    nivel_evidencia: NivelEvidencia = NivelEvidencia.PENDIENTE
    fecha_registro: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))

    @staticmethod
    def generar_id() -> str:
        """Genera un identificador único corto en formato hexadecimal basado en UUID4."""
        return _generar_uuid_corto()

    def __post_init__(self) -> None:
        """Normaliza tipos de datos tras la inicialización."""
        if not self.id:
            self.id = self.generar_id()
        if not isinstance(self.moneda, Moneda):
            self.moneda = _parse_enum(Moneda, self.moneda, Moneda.MXN)
        if not isinstance(self.nivel_evidencia, NivelEvidencia):
            self.nivel_evidencia = _parse_enum(NivelEvidencia, self.nivel_evidencia, NivelEvidencia.PENDIENTE)
        if isinstance(self.fecha_cotizacion, str):
            self.fecha_cotizacion = _parse_date(self.fecha_cotizacion)
        if isinstance(self.fecha_registro, str):
            self.fecha_registro = _parse_datetime(self.fecha_registro)

    def to_dict(self) -> dict[str, Any]:
        """Serializa la entidad a diccionario para persistencia en CSV."""
        return {
            "id": self.id,
            "origen_municipio": self.origen_municipio,
            "origen_estado": self.origen_estado,
            "destino_municipio": self.destino_municipio,
            "destino_estado": self.destino_estado,
            "distancia_km": self.distancia_km if self.distancia_km is not None else "",
            "tiempo_estimado_h": self.tiempo_estimado_h if self.tiempo_estimado_h is not None else "",
            "peajes_estimados": self.peajes_estimados if self.peajes_estimados is not None else "",
            "tipo_vehiculo": self.tipo_vehiculo,
            "cotizacion_flete": self.cotizacion_flete if self.cotizacion_flete is not None else "",
            "moneda": self.moneda.value if hasattr(self.moneda, "value") else str(self.moneda),
            "operador": self.operador if self.operador else "",
            "fecha_cotizacion": self.fecha_cotizacion.isoformat() if self.fecha_cotizacion else "",
            "temporada": self.temporada,
            "restricciones": self.restricciones,
            "fuente": self.fuente,
            "nivel_evidencia": self.nivel_evidencia.value if hasattr(self.nivel_evidencia, "value") else str(self.nivel_evidencia),
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RutaLogistica:
        """Crea una instancia a partir de un diccionario proveniente de CSV."""
        return cls(
            id=_parse_str(data.get("id")) or cls.generar_id(),
            origen_municipio=_parse_str(data.get("origen_municipio")),
            origen_estado=_parse_str(data.get("origen_estado")),
            destino_municipio=_parse_str(data.get("destino_municipio")),
            destino_estado=_parse_str(data.get("destino_estado")),
            distancia_km=_parse_float(data.get("distancia_km")),
            tiempo_estimado_h=_parse_float(data.get("tiempo_estimado_h")),
            peajes_estimados=_parse_float(data.get("peajes_estimados")),
            tipo_vehiculo=_parse_str(data.get("tipo_vehiculo")),
            cotizacion_flete=_parse_float(data.get("cotizacion_flete")),
            moneda=_parse_enum(Moneda, data.get("moneda"), Moneda.MXN),
            operador=_parse_str_or_none(data.get("operador")),
            fecha_cotizacion=_parse_date(data.get("fecha_cotizacion")),
            temporada=_parse_str(data.get("temporada")),
            restricciones=_parse_str(data.get("restricciones")),
            fuente=_parse_str(data.get("fuente")),
            nivel_evidencia=_parse_enum(NivelEvidencia, data.get("nivel_evidencia"), NivelEvidencia.PENDIENTE),
            fecha_registro=_parse_datetime(data.get("fecha_registro")),
        )


@dataclass
class OperacionPiloto:
    """Ejecución de un embarque o prueba piloto con medición de mermas y costos reales."""

    id: str = field(default_factory=_generar_uuid_corto)
    oportunidad_id: str = ""
    fecha: date = field(default_factory=date.today)
    lote: str = ""
    peso_recibido_kg: float = 0.0
    peso_vendible_kg: float | None = None
    calidad_evaluacion: str = ""
    merma_kg: float | None = None
    merma_pct: float | None = None
    costo_compra: float = 0.0
    costo_empaque: float | None = None
    costo_flete: float | None = None
    costo_otros: float | None = None
    ingreso_total: float | None = None
    pago_recibido: float | None = None
    dias_cobro: int | None = None
    reclamaciones: str = ""
    resultado: str = ""
    criterio_exito: str = ""
    costo_limite: float | None = None
    notas: str = ""
    fecha_registro: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))

    @staticmethod
    def generar_id() -> str:
        """Genera un identificador único corto en formato hexadecimal basado en UUID4."""
        return _generar_uuid_corto()

    def __post_init__(self) -> None:
        """Calcula mermas si no se indicaron y normaliza campos."""
        if not self.id:
            self.id = self.generar_id()
        if isinstance(self.fecha, str):
            self.fecha = _parse_date(self.fecha) or date.today()
        if isinstance(self.fecha_registro, str):
            self.fecha_registro = _parse_datetime(self.fecha_registro)

        # Cálculo automático de merma si se conocen peso recibido y peso vendible
        if self.peso_vendible_kg is not None and self.peso_recibido_kg > 0:
            if self.merma_kg is None:
                self.merma_kg = max(0.0, round(self.peso_recibido_kg - self.peso_vendible_kg, 4))
            if self.merma_pct is None and self.peso_recibido_kg > 0:
                self.merma_pct = round((self.merma_kg / self.peso_recibido_kg) * 100.0, 2)

    def to_dict(self) -> dict[str, Any]:
        """Serializa la entidad a diccionario para persistencia en CSV."""
        return {
            "id": self.id,
            "oportunidad_id": self.oportunidad_id,
            "fecha": self.fecha.isoformat() if self.fecha else "",
            "lote": self.lote,
            "peso_recibido_kg": self.peso_recibido_kg if self.peso_recibido_kg is not None else "",
            "peso_vendible_kg": self.peso_vendible_kg if self.peso_vendible_kg is not None else "",
            "calidad_evaluacion": self.calidad_evaluacion,
            "merma_kg": self.merma_kg if self.merma_kg is not None else "",
            "merma_pct": self.merma_pct if self.merma_pct is not None else "",
            "costo_compra": self.costo_compra if self.costo_compra is not None else "",
            "costo_empaque": self.costo_empaque if self.costo_empaque is not None else "",
            "costo_flete": self.costo_flete if self.costo_flete is not None else "",
            "costo_otros": self.costo_otros if self.costo_otros is not None else "",
            "ingreso_total": self.ingreso_total if self.ingreso_total is not None else "",
            "pago_recibido": self.pago_recibido if self.pago_recibido is not None else "",
            "dias_cobro": self.dias_cobro if self.dias_cobro is not None else "",
            "reclamaciones": self.reclamaciones,
            "resultado": self.resultado,
            "criterio_exito": self.criterio_exito,
            "costo_limite": self.costo_limite if self.costo_limite is not None else "",
            "notas": self.notas,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OperacionPiloto:
        """Crea una instancia a partir de un diccionario proveniente de CSV."""
        return cls(
            id=_parse_str(data.get("id")) or cls.generar_id(),
            oportunidad_id=_parse_str(data.get("oportunidad_id")),
            fecha=_parse_date(data.get("fecha")) or date.today(),
            lote=_parse_str(data.get("lote")),
            peso_recibido_kg=_parse_float(data.get("peso_recibido_kg")) or 0.0,
            peso_vendible_kg=_parse_float(data.get("peso_vendible_kg")),
            calidad_evaluacion=_parse_str(data.get("calidad_evaluacion")),
            merma_kg=_parse_float(data.get("merma_kg")),
            merma_pct=_parse_float(data.get("merma_pct")),
            costo_compra=_parse_float(data.get("costo_compra")) or 0.0,
            costo_empaque=_parse_float(data.get("costo_empaque")),
            costo_flete=_parse_float(data.get("costo_flete")),
            costo_otros=_parse_float(data.get("costo_otros")),
            ingreso_total=_parse_float(data.get("ingreso_total")),
            pago_recibido=_parse_float(data.get("pago_recibido")),
            dias_cobro=_parse_int(data.get("dias_cobro")),
            reclamaciones=_parse_str(data.get("reclamaciones")),
            resultado=_parse_str(data.get("resultado")),
            criterio_exito=_parse_str(data.get("criterio_exito")),
            costo_limite=_parse_float(data.get("costo_limite")),
            notas=_parse_str(data.get("notas")),
            fecha_registro=_parse_datetime(data.get("fecha_registro")),
        )


@dataclass
class FichaOportunidad:
    """Documento unificado de evaluación comercial y viabilidad de una oportunidad."""

    id: str = field(default_factory=_generar_uuid_corto)
    producto: str = ""
    variedad: str = ""
    presentacion: str = ""
    especificacion: str = ""
    necesidad_comprador: str = ""
    evidencia_comprador: str = ""
    segmento_comprador: Segmento = Segmento.MAYORISTA
    ubicacion_comprador: str = ""
    estatus_verificacion_comprador: EstatusVerificacion = EstatusVerificacion.SIN_VERIFICAR
    cliente_id: str | None = None
    proveedor_ids: list[str] = field(default_factory=list)
    cotizacion_compra_ids: list[str] = field(default_factory=list)
    cotizacion_venta_ids: list[str] = field(default_factory=list)
    capacidad_cotizacion_vigente: str = ""
    alternativas_compra: str = ""
    alternativas_canal_venta: str = ""
    origen: str = ""
    destino: str = ""
    ruta_id: str | None = None
    costo_transporte_kg: float | None = None
    fuente_cotizacion_transporte: str = ""
    costos_completos_kg: float | None = None
    supuestos_merma: str = ""
    ingreso_esperado_kg: float | None = None
    margen_contribucion_kg: float | None = None
    escenario_conservador: float | None = None
    escenario_base: float | None = None
    escenario_favorable: float | None = None
    calidad_empaque_estandares: str = ""
    documentacion_requerida: str = ""
    riesgos: str = ""
    dependencia: str = ""
    plan_alternativo: str = ""
    exposicion_maxima: float | None = None
    piloto_id: str | None = None
    criterio_exito_piloto: str = ""
    costo_limite_piloto: float | None = None
    decision_piloto: str = ""
    responsable_funcion: str = ""
    siguiente_accion: str = ""
    fecha_revision: date | None = None
    fuentes: str = ""
    fecha_registro: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))

    @staticmethod
    def generar_id() -> str:
        """Genera un identificador único corto en formato hexadecimal basado en UUID4."""
        return _generar_uuid_corto()

    def __post_init__(self) -> None:
        """Normaliza tipos de datos y listas tras la inicialización."""
        if not self.id:
            self.id = self.generar_id()
        if not isinstance(self.segmento_comprador, Segmento):
            self.segmento_comprador = _parse_enum(Segmento, self.segmento_comprador, Segmento.MAYORISTA)
        if not isinstance(self.estatus_verificacion_comprador, EstatusVerificacion):
            self.estatus_verificacion_comprador = _parse_enum(
                EstatusVerificacion, self.estatus_verificacion_comprador, EstatusVerificacion.SIN_VERIFICAR
            )
        if isinstance(self.proveedor_ids, str):
            self.proveedor_ids = _parse_list_str(self.proveedor_ids)
        if isinstance(self.cotizacion_compra_ids, str):
            self.cotizacion_compra_ids = _parse_list_str(self.cotizacion_compra_ids)
        if isinstance(self.cotizacion_venta_ids, str):
            self.cotizacion_venta_ids = _parse_list_str(self.cotizacion_venta_ids)
        if isinstance(self.cliente_id, str):
            self.cliente_id = _parse_str_or_none(self.cliente_id)
        if isinstance(self.fecha_revision, str):
            self.fecha_revision = _parse_date(self.fecha_revision)
        if isinstance(self.fecha_registro, str):
            self.fecha_registro = _parse_datetime(self.fecha_registro)

        # Si no se calculó el margen pero se tienen ingresos y costos unitarios, calcularlo
        if (
            self.margen_contribucion_kg is None
            and self.ingreso_esperado_kg is not None
            and self.costos_completos_kg is not None
        ):
            self.margen_contribucion_kg = round(self.ingreso_esperado_kg - self.costos_completos_kg, 4)

    def to_dict(self) -> dict[str, Any]:
        """Serializa la entidad a diccionario para persistencia en CSV."""
        return {
            "id": self.id,
            "producto": self.producto,
            "variedad": self.variedad,
            "presentacion": self.presentacion,
            "especificacion": self.especificacion,
            "necesidad_comprador": self.necesidad_comprador,
            "evidencia_comprador": self.evidencia_comprador,
            "segmento_comprador": self.segmento_comprador.value if hasattr(self.segmento_comprador, "value") else str(self.segmento_comprador),
            "ubicacion_comprador": self.ubicacion_comprador,
            "estatus_verificacion_comprador": (
                self.estatus_verificacion_comprador.value
                if hasattr(self.estatus_verificacion_comprador, "value")
                else str(self.estatus_verificacion_comprador)
            ),
            "cliente_id": self.cliente_id or "",
            "proveedor_ids": ",".join(self.proveedor_ids) if self.proveedor_ids else "",
            "cotizacion_compra_ids": ",".join(self.cotizacion_compra_ids) if self.cotizacion_compra_ids else "",
            "cotizacion_venta_ids": ",".join(self.cotizacion_venta_ids) if self.cotizacion_venta_ids else "",
            "capacidad_cotizacion_vigente": self.capacidad_cotizacion_vigente,
            "alternativas_compra": self.alternativas_compra,
            "alternativas_canal_venta": self.alternativas_canal_venta,
            "origen": self.origen,
            "destino": self.destino,
            "ruta_id": self.ruta_id if self.ruta_id else "",
            "costo_transporte_kg": self.costo_transporte_kg if self.costo_transporte_kg is not None else "",
            "fuente_cotizacion_transporte": self.fuente_cotizacion_transporte,
            "costos_completos_kg": self.costos_completos_kg if self.costos_completos_kg is not None else "",
            "supuestos_merma": self.supuestos_merma,
            "ingreso_esperado_kg": self.ingreso_esperado_kg if self.ingreso_esperado_kg is not None else "",
            "margen_contribucion_kg": self.margen_contribucion_kg if self.margen_contribucion_kg is not None else "",
            "escenario_conservador": self.escenario_conservador if self.escenario_conservador is not None else "",
            "escenario_base": self.escenario_base if self.escenario_base is not None else "",
            "escenario_favorable": self.escenario_favorable if self.escenario_favorable is not None else "",
            "calidad_empaque_estandares": self.calidad_empaque_estandares,
            "documentacion_requerida": self.documentacion_requerida,
            "riesgos": self.riesgos,
            "dependencia": self.dependencia,
            "plan_alternativo": self.plan_alternativo,
            "exposicion_maxima": self.exposicion_maxima if self.exposicion_maxima is not None else "",
            "piloto_id": self.piloto_id if self.piloto_id else "",
            "criterio_exito_piloto": self.criterio_exito_piloto,
            "costo_limite_piloto": self.costo_limite_piloto if self.costo_limite_piloto is not None else "",
            "decision_piloto": self.decision_piloto,
            "responsable_funcion": self.responsable_funcion,
            "siguiente_accion": self.siguiente_accion,
            "fecha_revision": self.fecha_revision.isoformat() if self.fecha_revision else "",
            "fuentes": self.fuentes,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FichaOportunidad:
        """Crea una instancia a partir de un diccionario proveniente de CSV."""
        return cls(
            id=_parse_str(data.get("id")) or cls.generar_id(),
            producto=_parse_str(data.get("producto")),
            variedad=_parse_str(data.get("variedad")),
            presentacion=_parse_str(data.get("presentacion")),
            especificacion=_parse_str(data.get("especificacion")),
            necesidad_comprador=_parse_str(data.get("necesidad_comprador")),
            evidencia_comprador=_parse_str(data.get("evidencia_comprador")),
            segmento_comprador=_parse_enum(Segmento, data.get("segmento_comprador"), Segmento.MAYORISTA),
            ubicacion_comprador=_parse_str(data.get("ubicacion_comprador")),
            estatus_verificacion_comprador=_parse_enum(
                EstatusVerificacion, data.get("estatus_verificacion_comprador"), EstatusVerificacion.SIN_VERIFICAR
            ),
            cliente_id=_parse_str_or_none(data.get("cliente_id")),
            proveedor_ids=_parse_list_str(data.get("proveedor_ids")),
            cotizacion_compra_ids=_parse_list_str(data.get("cotizacion_compra_ids")),
            cotizacion_venta_ids=_parse_list_str(data.get("cotizacion_venta_ids")),
            capacidad_cotizacion_vigente=_parse_str(data.get("capacidad_cotizacion_vigente")),
            alternativas_compra=_parse_str(data.get("alternativas_compra")),
            alternativas_canal_venta=_parse_str(data.get("alternativas_canal_venta")),
            origen=_parse_str(data.get("origen")),
            destino=_parse_str(data.get("destino")),
            ruta_id=_parse_str_or_none(data.get("ruta_id")),
            costo_transporte_kg=_parse_float(data.get("costo_transporte_kg")),
            fuente_cotizacion_transporte=_parse_str(data.get("fuente_cotizacion_transporte")),
            costos_completos_kg=_parse_float(data.get("costos_completos_kg")),
            supuestos_merma=_parse_str(data.get("supuestos_merma")),
            ingreso_esperado_kg=_parse_float(data.get("ingreso_esperado_kg")),
            margen_contribucion_kg=_parse_float(data.get("margen_contribucion_kg")),
            escenario_conservador=_parse_float(data.get("escenario_conservador")),
            escenario_base=_parse_float(data.get("escenario_base")),
            escenario_favorable=_parse_float(data.get("escenario_favorable")),
            calidad_empaque_estandares=_parse_str(data.get("calidad_empaque_estandares")),
            documentacion_requerida=_parse_str(data.get("documentacion_requerida")),
            riesgos=_parse_str(data.get("riesgos")),
            dependencia=_parse_str(data.get("dependencia")),
            plan_alternativo=_parse_str(data.get("plan_alternativo")),
            exposicion_maxima=_parse_float(data.get("exposicion_maxima")),
            piloto_id=_parse_str_or_none(data.get("piloto_id")),
            criterio_exito_piloto=_parse_str(data.get("criterio_exito_piloto")),
            costo_limite_piloto=_parse_float(data.get("costo_limite_piloto")),
            decision_piloto=_parse_str(data.get("decision_piloto")),
            responsable_funcion=_parse_str(data.get("responsable_funcion")),
            siguiente_accion=_parse_str(data.get("siguiente_accion")),
            fecha_revision=_parse_date(data.get("fecha_revision")),
            fuentes=_parse_str(data.get("fuentes")),
            fecha_registro=_parse_datetime(data.get("fecha_registro")),
        )


__all__ = [
    "ClientePotencial",
    "Proveedor",
    "Cotizacion",
    "RutaLogistica",
    "OperacionPiloto",
    "FichaOportunidad",
]
