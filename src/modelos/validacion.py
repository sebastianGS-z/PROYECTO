"""Funciones de validación y control de calidad para modelos comerciales del OAIC.

Implementa reglas de validación explícitas para clientes potenciales, proveedores,
cotizaciones, rutas logísticas, operaciones piloto y fichas de oportunidad,
impidiendo fallos silenciosos y garantizando integridad en la arquitectura de datos.
"""
from __future__ import annotations

from datetime import date

from src.modelos.comercial import (
    ClientePotencial,
    Cotizacion,
    FichaOportunidad,
    OperacionPiloto,
    Proveedor,
    RutaLogistica,
)
from src.modelos.enums import (
    EstatusEmbudo,
    EstatusVerificacion,
    Moneda,
    NivelEvidencia,
    Segmento,
    TipoCotizacion,
)


def validar_cliente(c: ClientePotencial) -> list[str]:
    """Valida la integridad de un registro de cliente potencial.

    Args:
        c: Instancia de ClientePotencial a validar.

    Returns:
        Lista de mensajes de error encontrados. Lista vacía si es válido.
    """
    errores: list[str] = []

    if not c.id or not c.id.strip():
        errores.append("El identificador del cliente no puede estar vacío.")

    if not c.razon_social or not c.razon_social.strip():
        errores.append("La razón social o nombre comercial es obligatoria.")

    if not isinstance(c.segmento, Segmento):
        errores.append(f"El segmento '{c.segmento}' no es un Segmento válido.")

    if not c.municipio or not c.municipio.strip():
        errores.append("El municipio es obligatorio.")

    if not c.estado or not c.estado.strip():
        errores.append("El estado de la república es obligatorio.")

    if not isinstance(c.fecha_identificacion, date):
        errores.append("La fecha de identificación debe ser una fecha válida.")

    if not isinstance(c.estatus, EstatusEmbudo):
        errores.append(f"El estatus '{c.estatus}' no es un EstatusEmbudo válido.")

    # Regla: fases avanzadas del embudo requieren evidencia y última verificación
    fases_avanzadas = {
        EstatusEmbudo.NECESIDAD_VERIFICADA,
        EstatusEmbudo.COTIZACION,
        EstatusEmbudo.PILOTO,
        EstatusEmbudo.NEGOCIACION,
        EstatusEmbudo.ACTIVO,
    }
    if c.estatus in fases_avanzadas:
        if not c.necesidad_declarada or not c.necesidad_declarada.strip():
            errores.append(
                f"El estatus '{c.estatus.value}' requiere una necesidad declarada por el comprador."
            )
        if not c.evidencia_verificacion or not c.evidencia_verificacion.strip():
            errores.append(
                f"El estatus '{c.estatus.value}' requiere evidencia de verificación documentada."
            )
        if c.ultima_verificacion is None:
            errores.append(
                f"El estatus '{c.estatus.value}' requiere registrar la fecha de última verificación."
            )

    # Prospecto activo no descartado debe tener próxima acción
    if c.estatus != EstatusEmbudo.DESCARTADO:
        if not c.proxima_accion or not c.proxima_accion.strip():
            errores.append("Un prospecto activo debe contar con una próxima acción definida.")

    if c.fecha_proxima_accion is not None:
        if not isinstance(c.fecha_proxima_accion, date):
            errores.append("La fecha de próxima acción debe ser una fecha válida.")
        elif isinstance(c.fecha_identificacion, date) and c.fecha_proxima_accion < c.fecha_identificacion:
            errores.append("La fecha de próxima acción no puede ser anterior a la fecha de identificación.")

    return errores


def validar_proveedor(p: Proveedor) -> list[str]:
    """Valida la integridad de un registro de proveedor agroalimentario.

    Args:
        p: Instancia de Proveedor a validar.

    Returns:
        Lista de mensajes de error encontrados. Lista vacía si es válido.
    """
    errores: list[str] = []

    if not p.id or not p.id.strip():
        errores.append("El identificador del proveedor no puede estar vacío.")

    if not p.razon_social or not p.razon_social.strip():
        errores.append("La razón social o nombre comercial del proveedor es obligatoria.")

    if not p.municipio or not p.municipio.strip():
        errores.append("El municipio del proveedor es obligatorio.")

    if not p.estado or not p.estado.strip():
        errores.append("El estado del proveedor es obligatorio.")

    if not p.producto or not p.producto.strip():
        errores.append("El producto agrícola ofertado es obligatorio.")

    if not p.fuente or not p.fuente.strip():
        errores.append("La procedencia o fuente del registro de proveedor es obligatoria.")

    if not isinstance(p.estatus, EstatusVerificacion):
        errores.append(f"El estatus '{p.estatus}' no es un EstatusVerificacion válido.")

    if p.estatus == EstatusVerificacion.VERIFICADO:
        if p.fecha_verificacion is None:
            errores.append("Un proveedor verificado debe tener fecha de verificación documentada.")
        if p.capacidad_confirmada_kg is None or p.capacidad_confirmada_kg <= 0:
            errores.append("Un proveedor verificado debe contar con capacidad confirmada en kg mayor a cero.")

    # Regla: datos comerciales con precio requieren unidad, moneda y vigencia
    if p.precio_unitario is not None:
        if p.precio_unitario <= 0:
            errores.append("El precio unitario cotizado debe ser mayor que cero.")
        if not isinstance(p.moneda, Moneda):
            errores.append("La cotización requiere una moneda válida (MXN o USD).")
        if not p.unidad_cotizacion or not p.unidad_cotizacion.strip():
            errores.append("La unidad de cotización del precio unitario es obligatoria.")
        if p.vigencia_cotizacion is None:
            errores.append("Una cotización con precio requiere vigencia de cotización documentada.")

    if p.peso_neto_kg is not None and p.peso_neto_kg <= 0:
        errores.append("El peso neto en kg debe ser mayor que cero.")

    if p.capacidad_confirmada_kg is not None and p.capacidad_confirmada_kg < 0:
        errores.append("La capacidad confirmada en kg no puede ser negativa.")

    if p.volumen_minimo_kg is not None and p.volumen_minimo_kg < 0:
        errores.append("El volumen mínimo en kg no puede ser negativo.")

    if p.merma_esperada_pct is not None and not (0.0 <= p.merma_esperada_pct <= 100.0):
        errores.append("El porcentaje de merma esperada debe ubicarse entre 0 y 100.")

    if p.tiempo_entrega_dias is not None and p.tiempo_entrega_dias < 0:
        errores.append("El tiempo de entrega en días no puede ser negativo.")

    return errores


def validar_cotizacion(c: Cotizacion) -> list[str]:
    """Valida la integridad y completitud de una cotización comercial.

    Rechaza explícitamente cualquier cotización sin unidad, moneda o vigencia.

    Args:
        c: Instancia de Cotizacion a validar.

    Returns:
        Lista de mensajes de error encontrados. Lista vacía si es válido.
    """
    errores: list[str] = []

    if not c.id or not c.id.strip():
        errores.append("El identificador de la cotización no puede estar vacío.")

    if not isinstance(c.tipo, TipoCotizacion):
        errores.append(f"El tipo de cotización '{c.tipo}' no es válido.")

    if not c.contraparte_id and not c.contraparte_nombre:
        errores.append("La cotización requiere identificar a la contraparte (id o nombre).")

    if not c.producto or not c.producto.strip():
        errores.append("El producto objeto de la cotización es obligatorio.")

    if c.precio_unitario is None or c.precio_unitario <= 0:
        errores.append("El precio unitario debe ser un valor positivo mayor que cero.")

    # Requisito mandatorio: rechazo explícito por falta de unidad
    if not c.unidad or not c.unidad.strip():
        errores.append("La unidad de medida es obligatoria y no puede estar vacía.")

    # Requisito mandatorio: rechazo explícito por falta de moneda
    if not c.moneda or not isinstance(c.moneda, Moneda):
        errores.append("La moneda es obligatoria y debe ser una divisa válida (MXN o USD).")

    # Requisito mandatorio: rechazo explícito por falta de vigencia
    if c.vigencia_inicio is None or not isinstance(c.vigencia_inicio, date):
        errores.append("La fecha de vigencia_inicio es obligatoria y debe ser una fecha válida.")

    if c.vigencia_fin is None or not isinstance(c.vigencia_fin, date):
        errores.append("La fecha de vigencia_fin es obligatoria y debe ser una fecha válida.")
    elif isinstance(c.vigencia_inicio, date) and c.vigencia_fin < c.vigencia_inicio:
        errores.append("La fecha de vigencia_fin no puede ser anterior a vigencia_inicio.")

    if not c.evidencia or not c.evidencia.strip():
        errores.append("La evidencia o respaldo de la cotización es obligatoria.")

    if not isinstance(c.nivel_evidencia, NivelEvidencia):
        errores.append(f"El nivel de evidencia '{c.nivel_evidencia}' no es válido.")

    if c.volumen_kg is not None and c.volumen_kg <= 0:
        errores.append("El volumen en kg debe ser mayor que cero cuando se declare.")

    return errores


def validar_ruta(r: RutaLogistica) -> list[str]:
    """Valida los datos de trazado y cotización de flete de una ruta logística.

    Args:
        r: Instancia de RutaLogistica a validar.

    Returns:
        Lista de mensajes de error encontrados. Lista vacía si es válido.
    """
    errores: list[str] = []

    if not r.id or not r.id.strip():
        errores.append("El identificador de la ruta no puede estar vacío.")

    if not r.origen_municipio or not r.origen_municipio.strip():
        errores.append("El municipio de origen es obligatorio.")

    if not r.origen_estado or not r.origen_estado.strip():
        errores.append("El estado de origen es obligatorio.")

    if not r.destino_municipio or not r.destino_municipio.strip():
        errores.append("El municipio de destino es obligatorio.")

    if not r.destino_estado or not r.destino_estado.strip():
        errores.append("El estado de destino es obligatorio.")

    if not r.tipo_vehiculo or not r.tipo_vehiculo.strip():
        errores.append("El tipo de vehículo para el transporte es obligatorio.")

    if not r.fuente or not r.fuente.strip():
        errores.append("La fuente de referencia o cotización de la ruta es obligatoria.")

    if not isinstance(r.nivel_evidencia, NivelEvidencia):
        errores.append(f"El nivel de evidencia '{r.nivel_evidencia}' no es válido.")

    if r.distancia_km is not None and r.distancia_km <= 0:
        errores.append("La distancia en km debe ser mayor que cero.")

    if r.tiempo_estimado_h is not None and r.tiempo_estimado_h <= 0:
        errores.append("El tiempo estimado en horas debe ser mayor que cero.")

    if r.peajes_estimados is not None and r.peajes_estimados < 0:
        errores.append("El costo estimado de peajes no puede ser negativo.")

    if r.cotizacion_flete is not None:
        if r.cotizacion_flete < 0:
            errores.append("La cotización de flete no puede ser negativa.")
        if not isinstance(r.moneda, Moneda):
            errores.append("La moneda de la cotización de flete debe ser válida (MXN o USD).")
        if r.cotizacion_flete > 0 and r.fecha_cotizacion is None:
            errores.append("Una cotización de flete requiere registrar la fecha de cotización.")

    return errores


def validar_piloto(p: OperacionPiloto) -> list[str]:
    """Valida la consistencia de una operación piloto comercial.

    Args:
        p: Instancia de OperacionPiloto a validar.

    Returns:
        Lista de mensajes de error encontrados. Lista vacía si es válido.
    """
    errores: list[str] = []

    if not p.id or not p.id.strip():
        errores.append("El identificador de la operación piloto no puede estar vacío.")

    if not p.oportunidad_id or not p.oportunidad_id.strip():
        errores.append("El identificador de oportunidad vinculado es obligatorio.")

    if not isinstance(p.fecha, date):
        errores.append("La fecha de ejecución del piloto debe ser una fecha válida.")

    if p.peso_recibido_kg <= 0:
        errores.append("El peso recibido en kg debe ser mayor que cero.")

    if p.peso_vendible_kg is not None:
        if p.peso_vendible_kg < 0:
            errores.append("El peso vendible en kg no puede ser negativo.")
        elif p.peso_vendible_kg > p.peso_recibido_kg:
            errores.append("El peso vendible no puede superar al peso recibido.")

    if p.merma_pct is not None and not (0.0 <= p.merma_pct <= 100.0):
        errores.append("El porcentaje de merma debe ubicarse entre 0 y 100.")

    if p.costo_compra < 0:
        errores.append("El costo de compra no puede ser negativo.")

    if not p.criterio_exito or not p.criterio_exito.strip():
        errores.append("El criterio de éxito del piloto es obligatorio.")

    if p.costo_limite is not None and p.costo_limite < 0:
        errores.append("El costo límite asignado al piloto no puede ser negativo.")

    return errores


def validar_oportunidad(f: FichaOportunidad) -> list[str]:
    """Valida los campos obligatorios y coherencia económica de una ficha de oportunidad.

    Args:
        f: Instancia de FichaOportunidad a validar.

    Returns:
        Lista de mensajes de error encontrados. Lista vacía si es válido.
    """
    errores: list[str] = []

    if not f.id or not f.id.strip():
        errores.append("El identificador de la oportunidad no puede estar vacío.")

    if not f.producto or not f.producto.strip():
        errores.append("El producto agroalimentario de la oportunidad es obligatorio.")

    if not f.especificacion or not f.especificacion.strip():
        errores.append("La especificación técnica de calidad y presentación es obligatoria.")

    if not f.necesidad_comprador or not f.necesidad_comprador.strip():
        errores.append("La necesidad declarada o problema del comprador es obligatoria.")

    if not isinstance(f.segmento_comprador, Segmento):
        errores.append(f"El segmento del comprador '{f.segmento_comprador}' no es válido.")

    if not f.ubicacion_comprador or not f.ubicacion_comprador.strip():
        errores.append("La ubicación geográfica del comprador es obligatoria.")

    if not isinstance(f.estatus_verificacion_comprador, EstatusVerificacion):
        errores.append(
            f"El estatus de verificación '{f.estatus_verificacion_comprador}' no es válido."
        )

    for etiqueta, valores in (
        ("proveedor", f.proveedor_ids),
        ("cotización de compra", f.cotizacion_compra_ids),
        ("cotización de venta", f.cotizacion_venta_ids),
    ):
        if len(valores) != len(set(valores)):
            errores.append(f"La lista de IDs de {etiqueta} contiene duplicados.")
        if any(not valor.strip() for valor in valores):
            errores.append(f"La lista de IDs de {etiqueta} contiene valores vacíos.")

    if not f.origen or not f.origen.strip():
        errores.append("La localidad u origen de abastecimiento es obligatorio.")

    if not f.destino or not f.destino.strip():
        errores.append("El punto de entrega o destino de la oportunidad es obligatorio.")

    if f.costos_completos_kg is not None and f.costos_completos_kg <= 0:
        errores.append("Los costos completos por kg deben ser mayores que cero.")

    if f.costo_transporte_kg is not None and f.costo_transporte_kg < 0:
        errores.append("El costo de transporte por kg no puede ser negativo.")

    if f.ingreso_esperado_kg is not None and f.ingreso_esperado_kg <= 0:
        errores.append("El ingreso esperado por kg debe ser mayor que cero.")

    # Validación de coherencia entre escenarios
    if f.escenario_conservador is not None and f.escenario_base is not None:
        if f.escenario_conservador > f.escenario_base:
            errores.append(
                f"El escenario conservador ({f.escenario_conservador}) no puede ser superior al escenario base ({f.escenario_base})."
            )

    if f.escenario_base is not None and f.escenario_favorable is not None:
        if f.escenario_base > f.escenario_favorable:
            errores.append(
                f"El escenario base ({f.escenario_base}) no puede ser superior al escenario favorable ({f.escenario_favorable})."
            )

    if not f.responsable_funcion or not f.responsable_funcion.strip():
        errores.append("El rol o función responsable del seguimiento es obligatorio.")

    if not f.siguiente_accion or not f.siguiente_accion.strip():
        errores.append("La siguiente acción definida en el proceso es obligatoria.")

    if not f.fuentes or not f.fuentes.strip():
        errores.append("Las fuentes documentales o de campo consultadas son obligatorias.")

    # Si se asocia piloto, validar requisitos de control
    if f.piloto_id:
        if not f.criterio_exito_piloto or not f.criterio_exito_piloto.strip():
            errores.append("Si existe un piloto asociado, el criterio de éxito del piloto es obligatorio.")
        if f.costo_limite_piloto is None or f.costo_limite_piloto <= 0:
            errores.append("Si existe un piloto asociado, el costo límite del piloto debe ser mayor que cero.")

    return errores


def es_vigente(cot: Cotizacion, fecha: date | None = None) -> bool:
    """Evalúa si una cotización se encuentra formalmente vigente en una fecha dada.

    Args:
        cot: Instancia de Cotizacion a validar.
        fecha: Fecha de corte para la verificación. Si es None, utiliza la fecha actual.

    Returns:
        True si ambas fechas de vigencia están presentes y la fecha se encuentra
        dentro del intervalo inclusivo [vigencia_inicio, vigencia_fin]; False en caso contrario.
    """
    if fecha is None:
        fecha = date.today()
    if not isinstance(fecha, date):
        return False
    if cot.vigencia_inicio is None or not isinstance(cot.vigencia_inicio, date):
        return False
    if cot.vigencia_fin is None or not isinstance(cot.vigencia_fin, date):
        return False
    return cot.vigencia_inicio <= fecha <= cot.vigencia_fin


def nivel_completitud(f: FichaOportunidad) -> dict[str, NivelEvidencia]:
    """Determina el grado de respaldo probatorio por dimensión para una ficha de oportunidad.

    Evalúa las ocho secciones clave de la oportunidad comercial:
    - comprador: necesidad, evidencia y verificación del cliente.
    - proveedor: abastecimiento identificado, capacidad y cotización.
    - logistica: trazado de ruta, costo de transporte y fuente de flete.
    - economia_unitaria: costos integrados, ingresos proyectados y márgenes.
    - calidad_especificacion: especificaciones de producto, empaque y normativa.
    - riesgos: contingencias, dependencias y plan de mitigación.
    - piloto: definición de experimento, presupuesto límite y decisión.
    - gobernanza: rol responsable, siguiente paso fechado y fuentes.

    Args:
        f: Instancia de FichaOportunidad.

    Returns:
        Diccionario con la dimensión como clave y su NivelEvidencia correspondiente.
    """
    completitud: dict[str, NivelEvidencia] = {}

    # 1. Comprador / Demanda
    verificado_comprador = f.estatus_verificacion_comprador == EstatusVerificacion.VERIFICADO
    tiene_evidencia_comprador = bool(f.evidencia_comprador and f.evidencia_comprador.strip())
    tiene_necesidad = bool(f.necesidad_comprador and f.necesidad_comprador.strip())
    tiene_ubicacion = bool(f.ubicacion_comprador and f.ubicacion_comprador.strip())

    if verificado_comprador and tiene_evidencia_comprador and tiene_necesidad:
        completitud["comprador"] = NivelEvidencia.CONFIRMADO
    elif f.estatus_verificacion_comprador == EstatusVerificacion.EN_PROCESO or (tiene_necesidad and tiene_evidencia_comprador):
        completitud["comprador"] = NivelEvidencia.ESTIMADO
    elif tiene_necesidad or tiene_ubicacion:
        completitud["comprador"] = NivelEvidencia.SUPUESTO
    else:
        completitud["comprador"] = NivelEvidencia.PENDIENTE

    # 2. Proveedor / Suministro
    tiene_proveedores = bool(f.proveedor_ids and len(f.proveedor_ids) > 0)
    tiene_capacidad_cot = bool(f.capacidad_cotizacion_vigente and f.capacidad_cotizacion_vigente.strip())
    tiene_alternativas_prov = bool(f.alternativas_compra and f.alternativas_compra.strip())

    if tiene_proveedores and tiene_capacidad_cot:
        completitud["proveedor"] = NivelEvidencia.CONFIRMADO
    elif tiene_proveedores or tiene_alternativas_prov:
        completitud["proveedor"] = NivelEvidencia.ESTIMADO
    elif tiene_capacidad_cot:
        completitud["proveedor"] = NivelEvidencia.SUPUESTO
    else:
        completitud["proveedor"] = NivelEvidencia.PENDIENTE

    # 3. Logística y Flete
    tiene_origen_destino = bool(f.origen and f.origen.strip() and f.destino and f.destino.strip())
    tiene_flete = f.costo_transporte_kg is not None and f.costo_transporte_kg > 0
    tiene_soporte_flete = bool((f.ruta_id and f.ruta_id.strip()) or (f.fuente_cotizacion_transporte and f.fuente_cotizacion_transporte.strip()))

    if tiene_origen_destino and tiene_flete and tiene_soporte_flete:
        completitud["logistica"] = NivelEvidencia.CONFIRMADO
    elif tiene_flete or (f.ruta_id and f.ruta_id.strip()):
        completitud["logistica"] = NivelEvidencia.ESTIMADO
    elif tiene_origen_destino:
        completitud["logistica"] = NivelEvidencia.SUPUESTO
    else:
        completitud["logistica"] = NivelEvidencia.PENDIENTE

    # 4. Economía Unitaria y Escenarios
    tiene_costos = f.costos_completos_kg is not None and f.costos_completos_kg > 0
    tiene_ingreso = f.ingreso_esperado_kg is not None and f.ingreso_esperado_kg > 0
    tiene_margen = f.margen_contribucion_kg is not None
    tiene_base = f.escenario_base is not None

    if tiene_costos and tiene_ingreso and tiene_margen and tiene_base:
        completitud["economia_unitaria"] = NivelEvidencia.CONFIRMADO
    elif (tiene_costos or tiene_ingreso) and tiene_margen:
        completitud["economia_unitaria"] = NivelEvidencia.ESTIMADO
    elif tiene_costos or tiene_ingreso or bool(f.supuestos_merma and f.supuestos_merma.strip()):
        completitud["economia_unitaria"] = NivelEvidencia.SUPUESTO
    else:
        completitud["economia_unitaria"] = NivelEvidencia.PENDIENTE

    # 5. Calidad y Especificación
    tiene_espec = bool(f.especificacion and f.especificacion.strip())
    tiene_empaque = bool(f.calidad_empaque_estandares and f.calidad_empaque_estandares.strip())
    tiene_documentacion = bool(f.documentacion_requerida and f.documentacion_requerida.strip())

    if tiene_espec and tiene_empaque and tiene_documentacion:
        completitud["calidad_especificacion"] = NivelEvidencia.CONFIRMADO
    elif tiene_espec and (tiene_empaque or tiene_documentacion):
        completitud["calidad_especificacion"] = NivelEvidencia.ESTIMADO
    elif tiene_espec:
        completitud["calidad_especificacion"] = NivelEvidencia.SUPUESTO
    else:
        completitud["calidad_especificacion"] = NivelEvidencia.PENDIENTE

    # 6. Riesgos y Contingencia
    tiene_riesgos = bool(f.riesgos and f.riesgos.strip())
    tiene_plan_alt = bool(f.plan_alternativo and f.plan_alternativo.strip())
    tiene_exposicion = f.exposicion_maxima is not None and f.exposicion_maxima > 0
    tiene_dependencia = bool(f.dependencia and f.dependencia.strip())

    if tiene_riesgos and tiene_plan_alt and tiene_exposicion:
        completitud["riesgos"] = NivelEvidencia.CONFIRMADO
    elif tiene_riesgos and (tiene_plan_alt or tiene_dependencia):
        completitud["riesgos"] = NivelEvidencia.ESTIMADO
    elif tiene_riesgos or tiene_dependencia:
        completitud["riesgos"] = NivelEvidencia.SUPUESTO
    else:
        completitud["riesgos"] = NivelEvidencia.PENDIENTE

    # 7. Piloto y Experimento
    tiene_piloto_id = bool(f.piloto_id and f.piloto_id.strip())
    tiene_criterio_piloto = bool(f.criterio_exito_piloto and f.criterio_exito_piloto.strip())
    tiene_costo_limite = f.costo_limite_piloto is not None and f.costo_limite_piloto > 0
    tiene_decision = bool(f.decision_piloto and f.decision_piloto.strip())

    if (tiene_piloto_id or tiene_decision) and tiene_criterio_piloto and tiene_costo_limite:
        completitud["piloto"] = NivelEvidencia.CONFIRMADO
    elif tiene_criterio_piloto and tiene_costo_limite:
        completitud["piloto"] = NivelEvidencia.ESTIMADO
    elif tiene_criterio_piloto or tiene_costo_limite or tiene_piloto_id:
        completitud["piloto"] = NivelEvidencia.SUPUESTO
    else:
        completitud["piloto"] = NivelEvidencia.PENDIENTE

    # 8. Gobernanza y Seguimiento
    tiene_resp = bool(f.responsable_funcion and f.responsable_funcion.strip())
    tiene_sig = bool(f.siguiente_accion and f.siguiente_accion.strip())
    tiene_revision = f.fecha_revision is not None and isinstance(f.fecha_revision, date)
    tiene_fuentes = bool(f.fuentes and f.fuentes.strip())

    if tiene_resp and tiene_sig and tiene_revision and tiene_fuentes:
        completitud["gobernanza"] = NivelEvidencia.CONFIRMADO
    elif tiene_resp and tiene_sig and tiene_fuentes:
        completitud["gobernanza"] = NivelEvidencia.ESTIMADO
    elif tiene_resp or tiene_sig:
        completitud["gobernanza"] = NivelEvidencia.SUPUESTO
    else:
        completitud["gobernanza"] = NivelEvidencia.PENDIENTE

    return completitud


__all__ = [
    "validar_cliente",
    "validar_proveedor",
    "validar_cotizacion",
    "validar_ruta",
    "validar_piloto",
    "validar_oportunidad",
    "es_vigente",
    "nivel_completitud",
]
