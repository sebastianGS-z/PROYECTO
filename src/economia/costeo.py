"""Módulo de costeo y viabilidad económica para el OAIC.

Implementa la estructura de costeo total puesto en destino, el análisis de
contribución neta por kilogramo y por pedido, punto de equilibrio en volumen,
modelado comparativo por escenarios (conservador, base, favorable), análisis
de sensibilidad y funciones auxiliares para cálculo de merma y capital de trabajo.

Fórmulas base:
    Costo puesto en destino = compra del producto
                            + empaque y acondicionamiento
                            + acopio y almacenamiento
                            + carga, flete, peajes y seguro
                            + merma/rechazo esperado documentado
                            + comisiones y costos de operación
                            + impuestos, aduana y cumplimiento aplicables

    Contribución neta por kg = ingreso neto confirmado por kg - costo puesto en destino por kg
    Contribución por pedido = contribución neta por kg × kg vendibles
    Punto de equilibrio (kg) = costos fijos atribuibles / contribución neta por kg
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Any

try:
    from src.modelos.enums import Moneda, NivelEvidencia
except ImportError:
    try:
        from ..modelos.enums import Moneda, NivelEvidencia  # type: ignore
    except (ImportError, ValueError):
        try:
            from modelos.enums import Moneda, NivelEvidencia  # type: ignore
        except ImportError:
            from enum import StrEnum

            class CadenaEnum(StrEnum):
                pass

            class Moneda(CadenaEnum):
                MXN = "MXN"
                USD = "USD"

            class NivelEvidencia(CadenaEnum):
                CONFIRMADO = "confirmado"
                ESTIMADO = "estimado"
                SUPUESTO = "supuesto"
                PENDIENTE = "pendiente"

                # Alias en minúsculas
                confirmado = "confirmado"
                estimado = "estimado"
                supuesto = "supuesto"
                pendiente = "pendiente"


@dataclass
class ComponenteCosto:
    """Representa un componente individual de costo, ingreso o volumen.

    Atributos:
        valor: Magnitud numérica. Puede ser None si el dato está pendiente de captura.
        unidad: Unidad de medida explícita (ej. 'kg', 'pedido', 'viaje', 'ton').
        moneda: Divisa de la cotización (por defecto 'MXN').
        fuente: Origen documental o informante del dato.
        fecha: Fecha de la cotización u observación en formato ISO 8601.
        nivel_evidencia: Nivel de respaldo empírico o metodológico del dato.
    """

    valor: float | None = None
    unidad: str = "kg"
    moneda: str = "MXN"
    fuente: str = "no_especificada"
    fecha: date | None = None
    nivel_evidencia: NivelEvidencia = NivelEvidencia.PENDIENTE

    def __post_init__(self) -> None:
        """Valida y normaliza los atributos del componente."""
        if not isinstance(self.unidad, str) or not self.unidad.strip():
            raise ValueError("La unidad de medida es obligatoria y no puede estar vacía")
        self.unidad = self.unidad.strip()

        if not isinstance(self.moneda, str) or not self.moneda.strip():
            raise ValueError("La moneda es obligatoria y no puede estar vacía")
        self.moneda = self.moneda.strip().upper()

        if not isinstance(self.fuente, str) or not self.fuente.strip():
            self.fuente = "no_especificada"
        else:
            self.fuente = self.fuente.strip()

        # Normalizar nivel de evidencia
        if isinstance(self.nivel_evidencia, str):
            try:
                self.nivel_evidencia = NivelEvidencia(self.nivel_evidencia)
            except ValueError:
                self.nivel_evidencia = NivelEvidencia(self.nivel_evidencia.lower().strip())

        # Normalizar fecha si viene en cadena ISO
        if isinstance(self.fecha, str):
            s_fecha = self.fecha.strip()
            if not s_fecha:
                self.fecha = None
            else:
                s_clean = s_fecha.split("T")[0].split(" ")[0]
                self.fecha = date.fromisoformat(s_clean)

        # Validar valor numérico si no es None
        if self.valor is not None:
            try:
                self.valor = float(self.valor)
            except (ValueError, TypeError):
                raise ValueError(f"Valor numérico no válido: {self.valor!r}") from None
            if not math.isfinite(self.valor):
                raise ValueError(f"El valor debe ser finito, recibido: {self.valor}")
            if self.valor < 0:
                raise ValueError(f"El valor de un componente no puede ser negativo: {self.valor}")

    @property
    def is_pendiente(self) -> bool:
        """Indica si el componente carece de valor o su evidencia está pendiente."""
        if self.valor is None:
            return True
        if self.nivel_evidencia is None:
            return True
        ev_str = (
            self.nivel_evidencia.value
            if hasattr(self.nivel_evidencia, "value")
            else str(self.nivel_evidencia)
        )
        return ev_str.lower().strip() == "pendiente"

    def to_dict(self) -> dict[str, Any]:
        """Serializa el componente a un diccionario con tipos básicos."""
        return {
            "valor": self.valor,
            "unidad": self.unidad,
            "moneda": self.moneda,
            "fuente": self.fuente,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "nivel_evidencia": (
                self.nivel_evidencia.value
                if hasattr(self.nivel_evidencia, "value")
                else str(self.nivel_evidencia)
            ),
            "is_pendiente": self.is_pendiente,
        }


@dataclass
class CostoPuestoEnDestino:
    """Modelo de acumulación de costos hasta el punto de entrega en destino.

    Atributos:
        compra_producto: Costo de adquisición de la fruta o producto agrícola.
        empaque: Costo de materiales, empaque y acondicionamiento.
        acopio: Costo de recepción, almacenamiento, cuartos fríos o manejo local.
        flete_peajes_seguro: Costo de flete terrestre/marítimo, casetas y seguro.
        merma_rechazo: Costo esperado documentado por pérdida, descarte o rechazo.
        comisiones_operacion: Comisiones de intermediación, comercialización o gestión.
        impuestos_cumplimiento: Impuestos, aranceles, certificados sanitarios y aduanas.
    """

    compra_producto: ComponenteCosto
    empaque: ComponenteCosto
    acopio: ComponenteCosto
    flete_peajes_seguro: ComponenteCosto
    merma_rechazo: ComponenteCosto
    comisiones_operacion: ComponenteCosto
    impuestos_cumplimiento: ComponenteCosto

    def componentes(self) -> dict[str, ComponenteCosto]:
        """Retorna un diccionario con los 7 componentes de costo."""
        return {
            "compra_producto": self.compra_producto,
            "empaque": self.empaque,
            "acopio": self.acopio,
            "flete_peajes_seguro": self.flete_peajes_seguro,
            "merma_rechazo": self.merma_rechazo,
            "comisiones_operacion": self.comisiones_operacion,
            "impuestos_cumplimiento": self.impuestos_cumplimiento,
        }

    def componentes_pendientes(self) -> list[str]:
        """Retorna la lista de nombres de componentes que están pendientes."""
        return [nombre for nombre, comp in self.componentes().items() if comp.is_pendiente]

    def tiene_datos_completos(self) -> bool:
        """Indica si todos los componentes requeridos tienen datos válidos y no pendientes."""
        return len(self.componentes_pendientes()) == 0

    def desglose(self) -> dict[str, dict[str, Any]]:
        """Devuelve el desglose detallado de cada componente de costo con su evidencia."""
        return {nombre: comp.to_dict() for nombre, comp in self.componentes().items()}

    def total_por_kg(self, peso_neto_kg: float) -> float | None:
        """Calcula el costo total puesto en destino por kilogramo neto vendible.

        Reglas críticas:
            - Si algún componente requerido está pendiente o carece de valor, retorna None.
            - Nunca asume o trata un valor pendiente como cero.
            - Rechaza cálculos si hay discrepancias de divisas sin tipo de cambio.
            - Requiere unidades explícitas (por kg o por pedido/flete/viaje).

        Parámetros:
            peso_neto_kg: Kilogramos netos vendibles del pedido o embarque.

        Retorna:
            Costo total por kilogramo en la divisa homogénea del modelo, o None si falta información.
        """
        if peso_neto_kg <= 0:
            raise ValueError(
                f"El peso neto en kg debe ser estrictamente positivo, recibido: {peso_neto_kg}"
            )
        if not self.tiene_datos_completos():
            return None

        # Validar consistencia de monedas
        monedas = {comp.moneda.upper().strip() for comp in self.componentes().values()}
        if len(monedas) > 1:
            raise ValueError(
                f"Monedas no homogéneas entre componentes de costo sin tipo de cambio explícito: {sorted(monedas)}"
            )

        total = 0.0
        for nombre, comp in self.componentes().items():
            if comp.valor is None:
                return None
            u = comp.unidad.lower().strip()
            # Unidades expresadas directamente por kilogramo
            if u in {
                "kg", "kilogramo", "kilogramos", "kg_neto", "kg.", "mxn/kg",
                "usd/kg", "$/kg", "por_kg", "/kg", "por kg", "pesos/kg",
            }:
                total += comp.valor
            # Unidades por tonelada
            elif u in {"t", "ton", "tonelada", "toneladas"}:
                total += comp.valor / 1000.0
            # Unidades por pedido, viaje, flete o embarque completo
            elif u in {
                "pedido", "orden", "viaje", "flete", "embarque", "lote",
                "global", "total", "envio", "servicio", "fijo", "carrera",
            }:
                total += comp.valor / peso_neto_kg
            else:
                raise ValueError(
                    f"Unidad no soportada o sin factor de conversión explícito a kg: {comp.unidad!r} en '{nombre}'. "
                    f"Unidades admitidas: 'kg', 'ton', o basadas en pedido ('pedido', 'viaje', 'lote')."
                )
        return round(total, 4)


@dataclass
class Escenario:
    """Escenario de modelado económico (conservador, base o favorable).

    Atributos:
        nombre: Nombre del escenario ('conservador', 'base', 'favorable').
        ingreso_neto_kg: Ingreso neto confirmado o proyectado por kg.
        costo_puesto_kg: Costo total puesto en destino por kg.
        volumen_kg: Volumen vendible proyectado en kg.
        costos_fijos: Costos fijos atribuibles a la operación (opcional).
    """

    nombre: str
    ingreso_neto_kg: ComponenteCosto
    costo_puesto_kg: ComponenteCosto
    volumen_kg: ComponenteCosto
    costos_fijos: ComponenteCosto | None = None

    def __post_init__(self) -> None:
        """Normaliza el nombre y valida coherencia básica."""
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del escenario es obligatorio")
        self.nombre = self.nombre.strip().lower()

    def contribucion_neta_kg(self) -> float | None:
        """Calcula la contribución neta por kilogramo.

        Fórmula: ingreso neto confirmado por kg - costo puesto en destino por kg.
        Retorna None si cualquiera de los dos componentes está pendiente.
        """
        if self.ingreso_neto_kg.is_pendiente or self.costo_puesto_kg.is_pendiente:
            return None
        if self.ingreso_neto_kg.valor is None or self.costo_puesto_kg.valor is None:
            return None

        # Validar consistencia de monedas
        if self.ingreso_neto_kg.moneda != self.costo_puesto_kg.moneda:
            raise ValueError(
                f"Discrepancia de monedas en escenario '{self.nombre}': "
                f"ingreso en {self.ingreso_neto_kg.moneda} vs costo en {self.costo_puesto_kg.moneda}"
            )
        return round(self.ingreso_neto_kg.valor - self.costo_puesto_kg.valor, 4)

    def contribucion_pedido(self) -> float | None:
        """Calcula la contribución total por pedido.

        Fórmula: contribución neta por kg × kg vendibles.
        Retorna None si la contribución neta o el volumen están pendientes.
        """
        cn = self.contribucion_neta_kg()
        if cn is None or self.volumen_kg.is_pendiente or self.volumen_kg.valor is None:
            return None
        return round(cn * self.volumen_kg.valor, 4)

    def punto_equilibrio_kg(self) -> float | None:
        """Calcula el punto de equilibrio en volumen (kg).

        Fórmula: costos fijos atribuibles / contribución neta por kg.
        Retorna None si faltan datos o si la contribución neta es <= 0 (inviable).
        """
        cn = self.contribucion_neta_kg()
        if cn is None:
            return None
        if self.costos_fijos is not None and self.costos_fijos.is_pendiente:
            return None

        cf = (
            self.costos_fijos.valor
            if (self.costos_fijos is not None and self.costos_fijos.valor is not None)
            else 0.0
        )
        if self.costos_fijos is not None and self.costos_fijos.moneda != self.ingreso_neto_kg.moneda:
            raise ValueError(
                f"Discrepancia de monedas en costos fijos de escenario '{self.nombre}': "
                f"costos fijos en {self.costos_fijos.moneda} vs ingreso en {self.ingreso_neto_kg.moneda}"
            )

        if cn <= 0:
            return None  # Con margen cero o negativo no existe volumen de equilibrio positivo
        return round(cf / cn, 4)

    def es_viable(self) -> bool | None:
        """Determina si el escenario es comercial y operativamente viable.

        Criterios:
            - Si faltan datos requeridos (ingreso, costo o volumen pendientes): None.
            - Si los costos fijos están presentes pero pendientes: None.
            - Si la contribución neta por kg es <= 0: False (margen negativo).
            - Si el volumen vendible es <= 0: False.
            - Si existen costos fijos: volumen_kg debe ser >= punto de equilibrio.
            - Si no existen costos fijos (o son 0): True si contribución neta > 0.
        """
        if (
            self.ingreso_neto_kg.is_pendiente
            or self.costo_puesto_kg.is_pendiente
            or self.volumen_kg.is_pendiente
        ):
            return None
        if self.costos_fijos is not None and self.costos_fijos.is_pendiente:
            return None

        cn = self.contribucion_neta_kg()
        if cn is None:
            return None
        if cn <= 0:
            return False

        if self.volumen_kg.valor is None or self.volumen_kg.valor <= 0:
            return False

        cf = (
            self.costos_fijos.valor
            if (self.costos_fijos is not None and self.costos_fijos.valor is not None)
            else 0.0
        )
        if cf == 0.0:
            return True

        pe = self.punto_equilibrio_kg()
        if pe is None:
            return None
        return self.volumen_kg.valor >= pe

    def resumen(self) -> dict[str, Any]:
        """Genera un diccionario resumen con las métricas clave del escenario."""
        return {
            "nombre": self.nombre,
            "ingreso_neto_kg": self.ingreso_neto_kg.valor,
            "costo_puesto_kg": self.costo_puesto_kg.valor,
            "volumen_kg": self.volumen_kg.valor,
            "costos_fijos": self.costos_fijos.valor if self.costos_fijos else None,
            "moneda": self.ingreso_neto_kg.moneda,
            "contribucion_neta_kg": self.contribucion_neta_kg(),
            "contribucion_pedido": self.contribucion_pedido(),
            "punto_equilibrio_kg": self.punto_equilibrio_kg(),
            "es_viable": self.es_viable(),
            "datos_completos": not (
                self.ingreso_neto_kg.is_pendiente
                or self.costo_puesto_kg.is_pendiente
                or self.volumen_kg.is_pendiente
                or (self.costos_fijos is not None and self.costos_fijos.is_pendiente)
            ),
            "niveles_evidencia": {
                "ingreso_neto": (
                    self.ingreso_neto_kg.nivel_evidencia.value
                    if hasattr(self.ingreso_neto_kg.nivel_evidencia, "value")
                    else str(self.ingreso_neto_kg.nivel_evidencia)
                ),
                "costo_puesto": (
                    self.costo_puesto_kg.nivel_evidencia.value
                    if hasattr(self.costo_puesto_kg.nivel_evidencia, "value")
                    else str(self.costo_puesto_kg.nivel_evidencia)
                ),
                "volumen": (
                    self.volumen_kg.nivel_evidencia.value
                    if hasattr(self.volumen_kg.nivel_evidencia, "value")
                    else str(self.volumen_kg.nivel_evidencia)
                ),
                "costos_fijos": (
                    self.costos_fijos.nivel_evidencia.value
                    if (self.costos_fijos and hasattr(self.costos_fijos.nivel_evidencia, "value"))
                    else (str(self.costos_fijos.nivel_evidencia) if self.costos_fijos else None)
                ),
            },
        }


@dataclass
class ModeloEconomico:
    """Modelo económico tri-escenario para evaluación de oportunidades comerciales.

    Atributos:
        conservador: Escenario con hipótesis prudentes (menor precio, mayor costo).
        base: Escenario más probable según cotizaciones y evidencia actual.
        favorable: Escenario optimista (mejor precio de plaza, menores mermas/costos).
        nombre_oportunidad: Identificador o descripción de la oportunidad evaluada.
    """

    conservador: Escenario
    base: Escenario
    favorable: Escenario
    nombre_oportunidad: str = ""

    def validar(self) -> list[str]:
        """Realiza comprobaciones de coherencia lógica y metodológica del modelo.

        Verifica:
            - Nombres esperados de los tres escenarios.
            - Monedas homogéneas en todos los componentes.
            - Coherencia ordinal de precios: conservador <= base <= favorable.
            - Coherencia ordinal de costos: favorable <= base <= conservador.
            - Valores no negativos en volúmenes y precios.

        Retorna:
            Lista de cadenas con las inconsistencias o advertencias encontradas.
        """
        errores: list[str] = []

        # Nombres canónicos
        for esc, esperado in (
            (self.conservador, "conservador"),
            (self.base, "base"),
            (self.favorable, "favorable"),
        ):
            if esc.nombre != esperado:
                errores.append(
                    f"Nombre de escenario inesperado: '{esc.nombre}' (se esperaba '{esperado}')"
                )

        # Monedas homogéneas
        todas_monedas: set[str] = set()
        for esc in (self.conservador, self.base, self.favorable):
            todas_monedas.add(esc.ingreso_neto_kg.moneda)
            todas_monedas.add(esc.costo_puesto_kg.moneda)
            if esc.costos_fijos is not None:
                todas_monedas.add(esc.costos_fijos.moneda)
        if len(todas_monedas) > 1:
            errores.append(
                f"Discrepancia de monedas entre escenarios: {sorted(todas_monedas)}. "
                f"Se requiere homologación explícita."
            )

        # Coherencia ordinal en ingresos
        ing_c = self.conservador.ingreso_neto_kg.valor
        ing_b = self.base.ingreso_neto_kg.valor
        ing_f = self.favorable.ingreso_neto_kg.valor
        if ing_c is not None and ing_b is not None and ing_c > ing_b:
            errores.append(
                f"Inconsistencia ordinal: ingreso conservador ({ing_c}) > base ({ing_b})"
            )
        if ing_b is not None and ing_f is not None and ing_b > ing_f:
            errores.append(
                f"Inconsistencia ordinal: ingreso base ({ing_b}) > favorable ({ing_f})"
            )

        # Coherencia ordinal en costos
        cost_c = self.conservador.costo_puesto_kg.valor
        cost_b = self.base.costo_puesto_kg.valor
        cost_f = self.favorable.costo_puesto_kg.valor
        if cost_f is not None and cost_b is not None and cost_f > cost_b:
            errores.append(
                f"Inconsistencia ordinal: costo favorable ({cost_f}) > base ({cost_b})"
            )
        if cost_b is not None and cost_c is not None and cost_b > cost_c:
            errores.append(
                f"Inconsistencia ordinal: costo base ({cost_b}) > conservador ({cost_c})"
            )

        # Volúmenes no negativos
        for esc in (self.conservador, self.base, self.favorable):
            if esc.volumen_kg.valor is not None and esc.volumen_kg.valor < 0:
                errores.append(
                    f"Volumen negativo en escenario '{esc.nombre}': {esc.volumen_kg.valor}"
                )

        return errores

    def comparar_escenarios(self) -> dict[str, Any]:
        """Genera una comparación lado a lado de los tres escenarios."""
        return {
            "oportunidad": self.nombre_oportunidad,
            "conservador": self.conservador.resumen(),
            "base": self.base.resumen(),
            "favorable": self.favorable.resumen(),
            "metricas_comparativas": {
                "contribucion_neta_kg": {
                    "conservador": self.conservador.contribucion_neta_kg(),
                    "base": self.base.contribucion_neta_kg(),
                    "favorable": self.favorable.contribucion_neta_kg(),
                },
                "contribucion_pedido": {
                    "conservador": self.conservador.contribucion_pedido(),
                    "base": self.base.contribucion_pedido(),
                    "favorable": self.favorable.contribucion_pedido(),
                },
                "punto_equilibrio_kg": {
                    "conservador": self.conservador.punto_equilibrio_kg(),
                    "base": self.base.punto_equilibrio_kg(),
                    "favorable": self.favorable.punto_equilibrio_kg(),
                },
                "viabilidad": {
                    "conservador": self.conservador.es_viable(),
                    "base": self.base.es_viable(),
                    "favorable": self.favorable.es_viable(),
                },
                "todos_viables": all(
                    e.es_viable() is True for e in (self.conservador, self.base, self.favorable)
                ),
                "al_menos_uno_viable": any(
                    e.es_viable() is True for e in (self.conservador, self.base, self.favorable)
                ),
                "datos_incompletos": any(
                    e.es_viable() is None for e in (self.conservador, self.base, self.favorable)
                ),
            },
        }

    def sensibilidad(self, variable: str, rango_pct: float) -> list[dict[str, Any]]:
        """Realiza un análisis de sensibilidad sobre el escenario base.

        Parámetros:
            variable: Variable a sensibilizar ('ingreso', 'costo', 'volumen', 'costos_fijos').
            rango_pct: Rango porcentual de variación (ej. 0.20 para ±20% o 20.0 para 20%).

        Retorna:
            Lista de diccionarios con la evaluación de impacto en márgenes y viabilidad.
        """
        v_norm = variable.strip().lower()
        var_map = {
            "ingreso": "ingreso", "precio": "ingreso", "ingreso_neto_kg": "ingreso",
            "costo": "costo", "costo_puesto": "costo", "costo_puesto_kg": "costo",
            "volumen": "volumen", "volumen_kg": "volumen", "kg": "volumen",
            "costos_fijos": "costos_fijos", "fijos": "costos_fijos",
        }
        if v_norm not in var_map:
            raise ValueError(
                f"Variable de sensibilidad no reconocida: {variable!r}. "
                f"Opciones válidas: 'ingreso', 'costo', 'volumen', 'costos_fijos'."
            )
        var_canon = var_map[v_norm]

        pct = rango_pct / 100.0 if rango_pct > 1.0 else rango_pct
        if pct <= 0:
            raise ValueError(f"El rango porcentual debe ser mayor a 0, recibido: {rango_pct}")

        deltas = [-pct, -pct / 2.0, 0.0, pct / 2.0, pct]
        resultados: list[dict[str, Any]] = []
        b = self.base

        for delta in deltas:
            factor = 1.0 + delta

            ingreso_val = b.ingreso_neto_kg.valor
            costo_val = b.costo_puesto_kg.valor
            volumen_val = b.volumen_kg.valor
            fijos_val = b.costos_fijos.valor if b.costos_fijos else None

            if var_canon == "ingreso" and ingreso_val is not None:
                ingreso_val = round(ingreso_val * factor, 4)
            elif var_canon == "costo" and costo_val is not None:
                costo_val = round(costo_val * factor, 4)
            elif var_canon == "volumen" and volumen_val is not None:
                volumen_val = round(volumen_val * factor, 4)
            elif var_canon == "costos_fijos" and fijos_val is not None:
                fijos_val = round(fijos_val * factor, 4)

            nuevo_ingreso = ComponenteCosto(
                valor=ingreso_val,
                unidad=b.ingreso_neto_kg.unidad,
                moneda=b.ingreso_neto_kg.moneda,
                fuente=b.ingreso_neto_kg.fuente,
                fecha=b.ingreso_neto_kg.fecha,
                nivel_evidencia=b.ingreso_neto_kg.nivel_evidencia,
            )
            nuevo_costo = ComponenteCosto(
                valor=costo_val,
                unidad=b.costo_puesto_kg.unidad,
                moneda=b.costo_puesto_kg.moneda,
                fuente=b.costo_puesto_kg.fuente,
                fecha=b.costo_puesto_kg.fecha,
                nivel_evidencia=b.costo_puesto_kg.nivel_evidencia,
            )
            nuevo_volumen = ComponenteCosto(
                valor=volumen_val,
                unidad=b.volumen_kg.unidad,
                moneda=b.volumen_kg.moneda,
                fuente=b.volumen_kg.fuente,
                fecha=b.volumen_kg.fecha,
                nivel_evidencia=b.volumen_kg.nivel_evidencia,
            )
            nuevos_fijos = None
            if b.costos_fijos is not None:
                nuevos_fijos = ComponenteCosto(
                    valor=fijos_val,
                    unidad=b.costos_fijos.unidad,
                    moneda=b.costos_fijos.moneda,
                    fuente=b.costos_fijos.fuente,
                    fecha=b.costos_fijos.fecha,
                    nivel_evidencia=b.costos_fijos.nivel_evidencia,
                )

            esc_sim = Escenario(
                nombre=f"sim_{delta:+.1%}",
                ingreso_neto_kg=nuevo_ingreso,
                costo_puesto_kg=nuevo_costo,
                volumen_kg=nuevo_volumen,
                costos_fijos=nuevos_fijos,
            )

            val_variable = {
                "ingreso": ingreso_val,
                "costo": costo_val,
                "volumen": volumen_val,
                "costos_fijos": fijos_val,
            }[var_canon]

            resultados.append({
                "variable": var_canon,
                "variacion_pct": round(delta * 100.0, 2),
                "factor": round(factor, 4),
                "valor_variable": val_variable,
                "contribucion_neta_kg": esc_sim.contribucion_neta_kg(),
                "contribucion_pedido": esc_sim.contribucion_pedido(),
                "punto_equilibrio_kg": esc_sim.punto_equilibrio_kg(),
                "es_viable": esc_sim.es_viable(),
            })

        return resultados

    def to_dict(self) -> dict[str, Any]:
        """Serializa el modelo económico completo a diccionario."""
        return {
            "nombre_oportunidad": self.nombre_oportunidad,
            "conservador": self.conservador.resumen(),
            "base": self.base.resumen(),
            "favorable": self.favorable.resumen(),
            "comparacion": self.comparar_escenarios(),
            "validaciones": self.validar(),
        }

    def resumen_ejecutivo(self) -> str:
        """Genera un resumen ejecutivo en formato de texto claro."""
        lineas = [
            f"=== RESUMEN ECONÓMICO EJECUTIVO: {self.nombre_oportunidad or 'OPORTUNIDAD'} ===",
            "",
            f"{'Métrica':<28} | {'Conservador':<14} | {'Base':<14} | {'Favorable':<14}",
            "-" * 76,
        ]

        def _fmt(val: float | None, suffix: str = "") -> str:
            if val is None:
                return "PENDIENTE"
            return f"${val:,.2f}{suffix}" if suffix.startswith("/") else f"{val:,.2f} {suffix}".strip()

        moneda = self.base.ingreso_neto_kg.moneda
        lineas.append(
            f"{'Ingreso neto / kg':<28} | "
            f"{_fmt(self.conservador.ingreso_neto_kg.valor, f' {moneda}/kg'):<14} | "
            f"{_fmt(self.base.ingreso_neto_kg.valor, f' {moneda}/kg'):<14} | "
            f"{_fmt(self.favorable.ingreso_neto_kg.valor, f' {moneda}/kg'):<14}"
        )
        lineas.append(
            f"{'Costo puesto en destino / kg':<28} | "
            f"{_fmt(self.conservador.costo_puesto_kg.valor, f' {moneda}/kg'):<14} | "
            f"{_fmt(self.base.costo_puesto_kg.valor, f' {moneda}/kg'):<14} | "
            f"{_fmt(self.favorable.costo_puesto_kg.valor, f' {moneda}/kg'):<14}"
        )
        lineas.append(
            f"{'Contribución neta / kg':<28} | "
            f"{_fmt(self.conservador.contribucion_neta_kg(), f' {moneda}/kg'):<14} | "
            f"{_fmt(self.base.contribucion_neta_kg(), f' {moneda}/kg'):<14} | "
            f"{_fmt(self.favorable.contribucion_neta_kg(), f' {moneda}/kg'):<14}"
        )
        lineas.append(
            f"{'Contribución / pedido':<28} | "
            f"{_fmt(self.conservador.contribucion_pedido(), f' {moneda}'):<14} | "
            f"{_fmt(self.base.contribucion_pedido(), f' {moneda}'):<14} | "
            f"{_fmt(self.favorable.contribucion_pedido(), f' {moneda}'):<14}"
        )
        lineas.append(
            f"{'Punto de equilibrio':<28} | "
            f"{_fmt(self.conservador.punto_equilibrio_kg(), 'kg'):<14} | "
            f"{_fmt(self.base.punto_equilibrio_kg(), 'kg'):<14} | "
            f"{_fmt(self.favorable.punto_equilibrio_kg(), 'kg'):<14}"
        )

        def _viable_str(v: bool | None) -> str:
            if v is None:
                return "DATOS INCOMPL."
            return "SÍ (VIABLE)" if v else "NO (INVIABLE)"

        lineas.append(
            f"{'Viabilidad comercial':<28} | "
            f"{_viable_str(self.conservador.es_viable()):<14} | "
            f"{_viable_str(self.base.es_viable()):<14} | "
            f"{_viable_str(self.favorable.es_viable()):<14}"
        )
        lineas.append("-" * 76)

        errores = self.validar()
        if errores:
            lineas.append("ADVERTENCIAS DE VALIDACIÓN:")
            for err in errores:
                lineas.append(f"  * {err}")
        else:
            lineas.append("Validaciones: Modelo consistente sin alertas de coherencia lógica.")

        return "\n".join(lineas)


def calcular_costo_merma(precio_compra_kg: float, merma_pct: float) -> float:
    """Calcula el costo por kilogramo atribuible a merma o rechazo esperado.

    Parámetros:
        precio_compra_kg: Precio de compra por kilogramo.
        merma_pct: Porcentaje o fracción de merma (ej. 0.05 para 5% o 5.0 para 5%).

    Retorna:
        Costo unitario de merma en la misma moneda.
    """
    if precio_compra_kg < 0:
        raise ValueError(f"El precio de compra no puede ser negativo: {precio_compra_kg}")
    pct = merma_pct / 100.0 if merma_pct > 1.0 else merma_pct
    if not (0.0 <= pct <= 1.0):
        raise ValueError(
            f"El porcentaje de merma debe estar entre 0 y 1 (o entre 0 y 100), recibido: {merma_pct}"
        )
    return round(precio_compra_kg * pct, 4)


def calcular_capital_trabajo(costo_pedido: float, dias_cobro: int, dias_pago: int) -> float:
    """Calcula el capital de trabajo requerido para financiar el ciclo operativo de un pedido.

    Parámetros:
        costo_pedido: Costo total puesto en destino o compra del pedido.
        dias_cobro: Días que tarda el comprador en pagar la factura.
        dias_pago: Días otorgados por el proveedor para liquidar el pedido.

    Retorna:
        Monto de capital de trabajo necesario en la misma moneda.
        Si dias_cobro <= dias_pago, retorna 0.0 (no se requiere capital neto propio).
    """
    if costo_pedido < 0:
        raise ValueError(f"El costo del pedido no puede ser negativo: {costo_pedido}")
    if dias_cobro < 0 or dias_pago < 0:
        raise ValueError(
            f"Los días de cobro y pago no pueden ser negativos (cobro={dias_cobro}, pago={dias_pago})"
        )

    brecha_dias = dias_cobro - dias_pago
    if brecha_dias <= 0 or costo_pedido == 0.0:
        return 0.0
    if dias_cobro == 0:
        return 0.0

    proporcion_fondeo = brecha_dias / dias_cobro
    return round(costo_pedido * proporcion_fondeo, 4)
