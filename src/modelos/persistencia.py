"""Persistencia CSV local para registros comerciales OAIC.

El módulo no incorpora datos de contacto personal. Los CSV se crean en el
directorio comercial local, que está excluido del control de versiones.
"""
from __future__ import annotations

import csv
import os
import tempfile
from dataclasses import fields
from datetime import date, datetime, timezone
from pathlib import Path

from src.modelos.comercial import (
    ClientePotencial,
    Cotizacion,
    FichaOportunidad,
    OperacionPiloto,
    Proveedor,
    RutaLogistica,
)
from src.modelos.validacion import (
    validar_cliente,
    validar_cotizacion,
    validar_oportunidad,
    validar_piloto,
    validar_proveedor,
    validar_ruta,
)

_TABLES = {
    "clientes_potenciales": (ClientePotencial, validar_cliente),
    "proveedores": (Proveedor, validar_proveedor),
    "cotizaciones": (Cotizacion, validar_cotizacion),
    "rutas_logisticas": (RutaLogistica, validar_ruta),
    "operaciones_piloto": (OperacionPiloto, validar_piloto),
    "fichas_oportunidad": (FichaOportunidad, validar_oportunidad),
}
_DATE_FIELDS = {
    "clientes_potenciales": {"fecha_identificacion", "ultima_verificacion", "fecha_proxima_accion", "fecha_registro"},
    "proveedores": {"vigencia_cotizacion", "fecha_verificacion", "fecha_registro"},
    "cotizaciones": {"vigencia_inicio", "vigencia_fin", "fecha_registro"},
    "rutas_logisticas": {"fecha_cotizacion", "fecha_registro"},
    "operaciones_piloto": {"fecha", "fecha_registro"},
    "fichas_oportunidad": {"fecha_revision", "fecha_registro"},
}
_REQUIRED_DATES = {
    "clientes_potenciales": {"fecha_identificacion"},
    "cotizaciones": {"vigencia_inicio"},
    "operaciones_piloto": {"fecha"},
}
_LEGACY_ADDITIONS = {
    "fichas_oportunidad": {"cliente_id", "cotizacion_compra_ids", "cotizacion_venta_ids"},
}


def esquemas() -> dict[str, tuple[str, ...]]:
    """Devuelve las columnas CSV autorizadas en el orden canónico."""
    return {
        nombre: tuple(field.name for field in fields(model))
        for nombre, (model, _) in _TABLES.items()
    }


class AlmacenComercial:
    """Lee y escribe las tablas comerciales locales con validación estricta."""

    def __init__(self, directorio: str | Path = "data/comercial") -> None:
        self.directorio = Path(directorio)

    def _tabla(self, nombre: str):
        try:
            return _TABLES[nombre]
        except KeyError:
            raise ValueError(f"Tabla comercial no permitida: {nombre}") from None

    def leer(self, nombre: str) -> list:
        modelo, validador = self._tabla(nombre)
        ruta = self.directorio / f"{nombre}.csv"
        if not ruta.exists():
            return []
        with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            esperadas = esquemas()[nombre]
            recibidas = tuple(lector.fieldnames or ())
            legacy = tuple(campo for campo in esperadas if campo not in _LEGACY_ADDITIONS.get(nombre, set()))
            if recibidas != esperadas and recibidas != legacy:
                raise ValueError(f"Esquema CSV inesperado en {ruta}; regenere desde una copia de respaldo.")
            filas = list(lector)
            for numero, fila in enumerate(filas, start=2):
                if None in fila:
                    raise ValueError(f"{ruta}:{numero}: la fila tiene más columnas que el encabezado.")
                for campo in _DATE_FIELDS[nombre]:
                    valor = (fila.get(campo) or "").strip()
                    if not valor:
                        if campo in _REQUIRED_DATES.get(nombre, set()):
                            raise ValueError(f"{ruta}:{numero}: falta la fecha obligatoria {campo}.")
                        continue
                    try:
                        datetime.fromisoformat(valor) if campo == "fecha_registro" else date.fromisoformat(valor)
                    except ValueError:
                        raise ValueError(f"{ruta}:{numero}: {campo} debe usar formato ISO 8601.") from None
            registros = [modelo.from_dict(fila) for fila in filas]
        for fila, registro in enumerate(registros, start=2):
            errores = validador(registro)
            if errores:
                raise ValueError(f"{ruta}:{fila}: " + "; ".join(errores))
        return registros

    def guardar(self, nombre: str, registros: list) -> Path:
        modelo, validador = self._tabla(nombre)
        encabezado = esquemas()[nombre]
        filas = []
        ids = set()
        for indice, registro in enumerate(registros, start=1):
            if not isinstance(registro, modelo):
                raise TypeError(f"Registro {indice} de {nombre} debe ser {modelo.__name__}.")
            errores = validador(registro)
            if errores:
                raise ValueError(f"Registro {indice} inválido: " + "; ".join(errores))
            if registro.id in ids:
                raise ValueError(f"Identificador duplicado en {nombre}: {registro.id}")
            ids.add(registro.id)
            filas.append(registro.to_dict())
        self.directorio.mkdir(parents=True, exist_ok=True)
        destino = self.directorio / f"{nombre}.csv"
        fd, temporal = tempfile.mkstemp(prefix=f".{nombre}.", suffix=".tmp", dir=self.directorio)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=encabezado, extrasaction="raise")
                escritor.writeheader()
                escritor.writerows(filas)
                archivo.flush()
                os.fsync(archivo.fileno())
            os.replace(temporal, destino)
        finally:
            if os.path.exists(temporal):
                os.unlink(temporal)
        return destino

    def inicializar(self) -> list[Path]:
        """Crea tablas vacías; no sobrescribe datos existentes."""
        self.directorio.mkdir(parents=True, exist_ok=True)
        creados = []
        for nombre in _TABLES:
            destino = self.directorio / f"{nombre}.csv"
            if not destino.exists():
                creados.append(self.guardar(nombre, []))
        return creados

    def registrar_correccion(
        self, tabla: str, registro_id: str, campo: str, valor_anterior: str,
        valor_nuevo: str, motivo: str, responsable: str,
    ) -> Path:
        """Agrega una corrección auditable sin modificar el registro por sí sola."""
        columnas = esquemas().get(tabla)
        if columnas is None:
            raise ValueError(f"Tabla comercial no permitida: {tabla}")
        if campo not in columnas:
            raise ValueError(f"Campo no permitido en {tabla}: {campo}")
        if not registro_id.strip() or not motivo.strip() or not responsable.strip():
            raise ValueError("registro_id, motivo y responsable son obligatorios")
        ruta = self.directorio / "historial_correcciones.csv"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        campos = ("fecha_utc", "tabla", "registro_id", "campo", "valor_anterior",
                  "valor_nuevo", "motivo", "responsable")
        filas = []
        if ruta.exists():
            with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
                lector = csv.DictReader(archivo)
                if tuple(lector.fieldnames or ()) != campos:
                    raise ValueError("Esquema inesperado en historial_correcciones.csv")
                filas.extend(lector)
        filas.append({
            "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tabla": tabla, "registro_id": registro_id, "campo": campo,
            "valor_anterior": valor_anterior, "valor_nuevo": valor_nuevo,
            "motivo": motivo, "responsable": responsable,
        })
        fd, temporal = tempfile.mkstemp(prefix=".correcciones.", suffix=".tmp", dir=self.directorio)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=campos, extrasaction="raise")
                escritor.writeheader()
                escritor.writerows(filas)
                archivo.flush()
                os.fsync(archivo.fileno())
            os.replace(temporal, ruta)
        finally:
            if os.path.exists(temporal):
                os.unlink(temporal)
        return ruta


__all__ = ["AlmacenComercial", "esquemas"]
