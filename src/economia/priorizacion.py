"""Motor de priorización y evaluación multicriterio de oportunidades comerciales.

Permite evaluar sistemáticamente oportunidades de abastecimiento, intermediación
o venta directa mediante ponderación fija de criterios de negocio, diferenciación
explícita del nivel de evidencia probatoria y detección temprana de incertidumbre.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

try:
    from src.modelos.enums import NivelEvidencia
except ImportError:
    try:
        from ..modelos.enums import NivelEvidencia  # type: ignore
    except (ImportError, ValueError):
        try:
            from modelos.enums import NivelEvidencia  # type: ignore
        except ImportError:
            from enum import StrEnum

            class CadenaEnum(StrEnum):
                pass

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


@dataclass(frozen=True)
class CriterioPriorizacion:
    """Criterio de evaluación ponderada para priorización de oportunidades.

    Atributos:
        nombre: Identificador canónico del criterio.
        peso: Ponderación en el modelo multicriterio (entre 0.0 y 1.0).
        descripcion: Definición del criterio y método de evaluación.
    """

    nombre: str
    peso: float
    descripcion: str

    def __post_init__(self) -> None:
        """Valida que el criterio tenga nombre y un peso en rango válido."""
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del criterio es obligatorio y no puede estar vacío")
        if not (0.0 <= self.peso <= 1.0):
            raise ValueError(
                f"El peso del criterio '{self.nombre}' debe estar en el rango [0.0, 1.0], recibido: {self.peso}"
            )


@dataclass
class PuntuacionCriterio:
    """Calificación otorgada a una oportunidad en un criterio específico.

    Atributos:
        criterio_nombre: Identificador del criterio calificado.
        valor: Calificación en escala de 0 a 10.
        nivel_evidencia: Grado de certeza documental o empírica del respaldo.
        justificacion: Evidencia documental o razonamiento de la calificación.
    """

    criterio_nombre: str
    valor: float
    nivel_evidencia: NivelEvidencia
    justificacion: str

    def __post_init__(self) -> None:
        """Valida rangos numéricos y normaliza tipos de datos."""
        if not self.criterio_nombre or not self.criterio_nombre.strip():
            raise ValueError("El nombre del criterio es obligatorio")
        self.criterio_nombre = self.criterio_nombre.strip()

        try:
            self.valor = float(self.valor)
        except (ValueError, TypeError):
            raise ValueError(f"El valor de puntuación debe ser numérico, recibido: {self.valor!r}") from None

        if not math.isfinite(self.valor):
            raise ValueError(f"El valor de puntuación debe ser finito, recibido: {self.valor}")
        if not (0.0 <= self.valor <= 10.0):
            raise ValueError(
                f"El valor de puntuación debe estar entre 0.0 y 10.0, recibido: {self.valor}"
            )

        if isinstance(self.nivel_evidencia, str):
            try:
                self.nivel_evidencia = NivelEvidencia(self.nivel_evidencia)
            except ValueError:
                self.nivel_evidencia = NivelEvidencia(self.nivel_evidencia.lower().strip())

        if not self.justificacion or not self.justificacion.strip():
            self.justificacion = "sin justificación documentada"
        else:
            self.justificacion = self.justificacion.strip()


#: Criterios de evaluación por defecto consensuados para el OAIC (pesos suman 1.0)
CRITERIOS_DEFAULT: list[CriterioPriorizacion] = [
    CriterioPriorizacion(
        nombre="necesidad_comprador_verificada",
        peso=0.20,
        descripcion="Demanda real del comprador confirmada mediante entrevista directa, volumen y especificación.",
    ),
    CriterioPriorizacion(
        nombre="margen_contribucion",
        peso=0.20,
        descripcion="Margen de contribución neto por kg y pedido considerando costos completos puestos en destino.",
    ),
    CriterioPriorizacion(
        nombre="continuidad_suministro",
        peso=0.15,
        descripcion="Capacidad confirmada del proveedor para mantener volumen, calidad y calendario estacional.",
    ),
    CriterioPriorizacion(
        nombre="compatibilidad_calidad",
        peso=0.10,
        descripcion="Ajuste entre especificaciones de cosecha/empaque y requisitos de aceptación del cliente.",
    ),
    CriterioPriorizacion(
        nombre="confiabilidad_transporte",
        peso=0.10,
        descripcion="Disponibilidad de flete, rutas cotizadas, tiempos de traslado y cadena de conservación.",
    ),
    CriterioPriorizacion(
        nombre="riesgo",
        peso=0.10,
        descripcion="Evaluación de riesgos de cobranza, fluctuación de precios, mermas y concentración.",
    ),
    CriterioPriorizacion(
        nombre="requisitos_regulatorios",
        peso=0.05,
        descripcion="Cumplimiento normativo, fitosanitario, fiscal y aduanal aplicable al origen y destino.",
    ),
    CriterioPriorizacion(
        nombre="facilidad_piloto",
        peso=0.10,
        descripcion="Viabilidad de ejecutar un embarque de prueba acotado con bajo compromiso y métricas claras.",
    ),
]


def validar_pesos(criterios: list[CriterioPriorizacion]) -> list[str]:
    """Valida que los pesos de los criterios estén normalizados y sumen exactamente 1.0.

    Reglas:
        - La lista de criterios no puede estar vacía.
        - No puede haber nombres de criterios duplicados.
        - Cada peso individual debe estar entre 0.0 y 1.0.
        - La suma de los pesos debe ser igual a 1.0 (tolerancia 1e-5).

    Parámetros:
        criterios: Lista de criterios a validar.

    Retorna:
        Lista de errores encontrados. Vacía si la configuración es válida.
    """
    errores: list[str] = []
    if not criterios:
        return ["La lista de criterios de priorización no puede estar vacía."]

    nombres: set[str] = set()
    for c in criterios:
        if c.nombre in nombres:
            errores.append(f"Criterio duplicado: '{c.nombre}'.")
        nombres.add(c.nombre)

        if not (0.0 <= c.peso <= 1.0):
            errores.append(
                f"El peso del criterio '{c.nombre}' ({c.peso}) está fuera del rango [0.0, 1.0]."
            )

    suma_pesos = sum(c.peso for c in criterios)
    if not math.isclose(suma_pesos, 1.0, rel_tol=1e-5, abs_tol=1e-5):
        errores.append(
            f"La suma de los pesos debe ser exactamente 1.0 (suma actual: {suma_pesos:.4f})."
        )

    return errores


def puntuar_oportunidad(
    puntuaciones: list[PuntuacionCriterio],
    criterios: list[CriterioPriorizacion] | None = None,
) -> dict[str, Any]:
    """Calcula la puntuación ponderada y el perfil de calidad de evidencia de una oportunidad.

    Reglas críticas:
        - Los pesos deben estar fijados y validados antes de puntuar (no ajustados a posteriori).
        - Separa explícitamente las evidencias por nivel: 'confirmado', 'estimado', 'supuesto' y 'pendiente'.
        - Activa una bandera de alerta de incertidumbre si más del 50% de las calificaciones
          provienen de 'supuesto' o 'pendiente'.

    Parámetros:
        puntuaciones: Lista de calificaciones por criterio.
        criterios: Lista de criterios con pesos acordados (por defecto CRITERIOS_DEFAULT).

    Retorna:
        Diccionario con puntuación ponderada, desglose detallado y resumen de calidad de datos.
    """
    crit_list = CRITERIOS_DEFAULT if criterios is None else criterios
    errores_pesos = validar_pesos(crit_list)
    if errores_pesos:
        raise ValueError(
            f"Los pesos de los criterios deben ser válidos antes de puntuar: {errores_pesos}"
        )

    crit_map = {c.nombre: c for c in crit_list}
    score_map: dict[str, PuntuacionCriterio] = {}

    for p in puntuaciones:
        if p.criterio_nombre in score_map:
            raise ValueError(f"Puntuación duplicada para el criterio '{p.criterio_nombre}'")
        score_map[p.criterio_nombre] = p

    faltantes = [nombre for nombre in crit_map if nombre not in score_map]
    if faltantes:
        raise ValueError(
            f"Faltan puntuaciones para los siguientes criterios obligatorios: {faltantes}"
        )

    desglose: list[dict[str, Any]] = []
    puntuacion_ponderada = 0.0

    # Separación explícita de evidencia por categoría
    confirmados: list[dict[str, Any]] = []
    estimados: list[dict[str, Any]] = []
    supuestos: list[dict[str, Any]] = []
    pendientes: list[dict[str, Any]] = []

    for nombre, c in crit_map.items():
        p = score_map[nombre]
        contrib = p.valor * c.peso
        puntuacion_ponderada += contrib

        ev_val = (
            p.nivel_evidencia.value
            if hasattr(p.nivel_evidencia, "value")
            else str(p.nivel_evidencia)
        ).lower().strip()

        detalle_criterio = {
            "criterio": nombre,
            "descripcion": c.descripcion,
            "peso": c.peso,
            "valor": p.valor,
            "ponderado": round(contrib, 4),
            "nivel_evidencia": ev_val,
            "justificacion": p.justificacion,
        }
        desglose.append(detalle_criterio)

        if ev_val == "confirmado":
            confirmados.append(detalle_criterio)
        elif ev_val == "estimado":
            estimados.append(detalle_criterio)
        elif ev_val == "supuesto":
            supuestos.append(detalle_criterio)
        elif ev_val == "pendiente":
            pendientes.append(detalle_criterio)
        else:
            supuestos.append(detalle_criterio)

    total_evaluados = len(crit_list)
    total_inciertos = len(supuestos) + len(pendientes)
    pct_inciertos = total_inciertos / total_evaluados if total_evaluados > 0 else 0.0
    alerta_incertidumbre = pct_inciertos > 0.50

    return {
        "puntuacion_ponderada": round(puntuacion_ponderada, 4),
        "total_criterios": total_evaluados,
        "desglose": desglose,
        "calidad_evidencia": {
            "confirmado": confirmados,
            "estimado": estimados,
            "supuesto": supuestos,
            "pendiente": pendientes,
            "conteo_confirmados": len(confirmados),
            "conteo_estimados": len(estimados),
            "conteo_supuestos": len(supuestos),
            "conteo_pendientes": len(pendientes),
            "pct_confirmado": round(len(confirmados) / total_evaluados, 4),
            "pct_estimado": round(len(estimados) / total_evaluados, 4),
            "pct_supuesto": round(len(supuestos) / total_evaluados, 4),
            "pct_pendiente": round(len(pendientes) / total_evaluados, 4),
            "pct_supuesto_o_pendiente": round(pct_inciertos, 4),
            "alerta_incertidumbre": alerta_incertidumbre,
            "motivo_alerta": (
                "Más del 50% de las puntuaciones corresponden a supuestos o datos pendientes. "
                "Se requiere validación empírica en campo antes de comprometer recursos."
                if alerta_incertidumbre
                else ""
            ),
        },
    }


def comparar_oportunidades(
    oportunidades: dict[str, list[PuntuacionCriterio]],
    criterios: list[CriterioPriorizacion] | None = None,
) -> list[dict[str, Any]]:
    """Compara y ordena un conjunto de oportunidades comerciales por su calificación ponderada.

    Parámetros:
        oportunidades: Diccionario {nombre_oportunidad: lista_puntuaciones}.
        criterios: Criterios a aplicar (por defecto CRITERIOS_DEFAULT).

    Retorna:
        Lista ordenada de mayor a menor puntuación ponderada, con ranking y diagnóstico de evidencia.
    """
    ranking: list[dict[str, Any]] = []

    for nombre, scores in oportunidades.items():
        res = puntuar_oportunidad(scores, criterios)
        calidad = res["calidad_evidencia"]
        ranking.append({
            "oportunidad": nombre,
            "puntuacion_ponderada": res["puntuacion_ponderada"],
            "alerta_incertidumbre": calidad["alerta_incertidumbre"],
            "pct_confirmado": calidad["pct_confirmado"],
            "pct_supuesto_o_pendiente": calidad["pct_supuesto_o_pendiente"],
            "calidad_evidencia": calidad,
            "desglose": res["desglose"],
        })

    # Ordenar por puntuación ponderada descendente; desempate por mayor % confirmado
    ranking.sort(
        key=lambda x: (x["puntuacion_ponderada"], x["pct_confirmado"]),
        reverse=True,
    )

    for idx, item in enumerate(ranking, start=1):
        item["ranking"] = idx

    return ranking


def matriz_priorizacion(
    oportunidades: dict[str, list[PuntuacionCriterio]],
    criterios: list[CriterioPriorizacion] | None = None,
) -> pd.DataFrame:
    """Genera una matriz comparativa tabular en formato pandas DataFrame.

    Parámetros:
        oportunidades: Diccionario {nombre_oportunidad: lista_puntuaciones}.
        criterios: Criterios a aplicar (por defecto CRITERIOS_DEFAULT).

    Retorna:
        DataFrame con cada oportunidad en filas y columnas de puntuación por criterio, total y alertas.
    """
    crit_list = CRITERIOS_DEFAULT if criterios is None else criterios
    nombres_criterios = [c.nombre for c in crit_list]

    columnas = [
        "oportunidad",
        *nombres_criterios,
        "puntuacion_ponderada",
        "ranking",
        "pct_confirmado",
        "pct_supuesto_o_pendiente",
        "alerta_incertidumbre",
        "estado_recomendacion",
    ]

    if not oportunidades:
        return pd.DataFrame(columns=columnas)

    ranking = comparar_oportunidades(oportunidades, criterios)
    filas: list[dict[str, Any]] = []

    for item in ranking:
        nombre_op = item["oportunidad"]
        scores_by_crit = {d["criterio"]: d["valor"] for d in item["desglose"]}

        punt = item["puntuacion_ponderada"]
        alerta = item["alerta_incertidumbre"]

        if alerta:
            estado = "Requiere validación (alta incertidumbre)"
        elif punt >= 7.5:
            estado = "Alta prioridad (candidata a piloto)"
        elif punt >= 5.0:
            estado = "Media prioridad (optimizar costos/suministro)"
        else:
            estado = "Baja prioridad (descartar o renegociar)"

        fila: dict[str, Any] = {
            "oportunidad": nombre_op,
            **{c_nom: scores_by_crit.get(c_nom) for c_nom in nombres_criterios},
            "puntuacion_ponderada": item["puntuacion_ponderada"],
            "ranking": item["ranking"],
            "pct_confirmado": item["pct_confirmado"],
            "pct_supuesto_o_pendiente": item["pct_supuesto_o_pendiente"],
            "alerta_incertidumbre": alerta,
            "estado_recomendacion": estado,
        }
        filas.append(fila)

    return pd.DataFrame(filas, columns=columnas)
