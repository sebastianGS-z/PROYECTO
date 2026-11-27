"""Comandos locales para importar prospectos DENUE y dar seguimiento comercial."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

from src.modelos import (
    ClientePotencial,
    EstatusEmbudo,
    EstatusVerificacion,
    NivelEvidencia,
    Segmento,
    TipoCotizacion,
    es_vigente,
    nivel_completitud,
)
from src.modelos.persistencia import AlmacenComercial, esquemas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directorio", type=Path, default=Path("data/comercial"))
    commands = parser.add_subparsers(dest="comando", required=True)
    commands.add_parser("inicializar", help="crear tablas vacías sin sobrescribir datos")
    commands.add_parser("validar", help="validar esquema y filas de tablas existentes")
    denue = commands.add_parser("importar-denue", help="importar un CSV DENUE como prospectos por verificar")
    denue.add_argument("archivo", type=Path)
    denue.add_argument("--estado-default", help="estado que se asigna si el CSV no contiene el campo")
    denue.add_argument("--municipio", help="importar solo establecimientos de este municipio")
    commands.add_parser("seguimiento", help="resumir embudo, proveedores, cotizaciones y oportunidades")
    link = commands.add_parser("vincular", help="relacionar una oportunidad con cliente, cotizaciones, proveedor y ruta")
    link.add_argument("--oportunidad", required=True)
    link.add_argument("--cliente", required=True)
    link.add_argument("--proveedor", action="append")
    link.add_argument("--compra", action="append")
    link.add_argument("--venta", action="append")
    link.add_argument("--ruta")
    args = parser.parse_args(argv)
    store = AlmacenComercial(args.directorio)

    if args.comando == "inicializar":
        created = store.inicializar()
        print(f"Tablas comerciales inicializadas en {args.directorio}; nuevas: {len(created)}.")
        return 0

    if args.comando == "importar-denue":
        try:
            nuevos, omitidos = importar_denue(store, args.archivo, args.estado_default, args.municipio)
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            print(f"No se importó el archivo: {exc}", file=sys.stderr)
            return 1
        print(f"Importación DENUE: {nuevos} prospectos agregados, {omitidos} omitidos.")
        print("Los registros quedan como IDENTIFICADO; verificar necesidad, contacto y capacidad de compra.")
        return 0

    if args.comando == "seguimiento":
        try:
            resumen = generar_seguimiento(store)
        except (OSError, ValueError) as exc:
            print(f"No se pudo generar el seguimiento: {exc}", file=sys.stderr)
            return 1
        destino = store.directorio / "reporte_seguimiento.json"
        store.directorio.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
        print(f"Reporte guardado en {destino}")
        return 0

    if args.comando == "vincular":
        try:
            vincular_oportunidad(
                store, args.oportunidad, args.cliente, args.proveedor,
                args.compra, args.venta, args.ruta,
            )
        except (OSError, ValueError) as exc:
            print(f"No se pudieron validar o guardar los vínculos: {exc}", file=sys.stderr)
            return 1
        print(f"Vínculos actualizados para oportunidad {args.oportunidad}.")
        return 0

    failures = 0
    for table in esquemas():
        try:
            records = store.leer(table)
            print(f"OK {table}: {len(records)} registros")
        except (OSError, ValueError) as exc:
            failures += 1
            print(f"ERROR {table}: {exc}", file=sys.stderr)
    return 1 if failures else 0


def _normalizar_columna(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.strip().casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(value.replace("_", " ").split())


def _buscar(row: dict[str, str], *aliases: str) -> str:
    values = {_normalizar_columna(key): (value or "").strip() for key, value in row.items() if key}
    for alias in aliases:
        value = values.get(_normalizar_columna(alias), "")
        if value:
            return value
    return ""


def _segmento(actividad: str) -> Segmento:
    texto = _normalizar_columna(actividad)
    if any(word in texto for word in ("restaurante", "preparacion de alimentos", "alimentos para llevar")):
        return Segmento.RESTAURANTE
    if "hotel" in texto or "motel" in texto:
        return Segmento.HOTEL
    if any(word in texto for word in ("mayoreo", "comercio al por mayor", "central de abasto")):
        return Segmento.MAYORISTA
    if any(word in texto for word in ("abarrote", "comercio al por menor", "frutas y verduras", "supermercado")):
        return Segmento.TIENDA
    if any(word in texto for word in ("procesamiento", "conservacion", "elaboracion de alimentos")):
        return Segmento.PROCESADOR
    if "empaque" in texto or "empacadora" in texto:
        return Segmento.EMPACADORA
    if "distribucion" in texto or "distribuidor" in texto:
        return Segmento.DISTRIBUIDOR
    return Segmento.OTRO


def importar_denue(
    store: AlmacenComercial, archivo: Path, estado_default: str | None = None,
    municipio: str | None = None,
) -> tuple[int, int]:
    """Importa filas de un CSV DENUE como candidatos; no persiste teléfonos/correos."""
    contenido = archivo.read_bytes()
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = contenido.decode("cp1252")
    from io import StringIO
    with StringIO(texto, newline="") as stream:
        sample = stream.read(4096)
        stream.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(stream, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("El CSV no contiene encabezados")
        rows = list(reader)

    actuales = store.leer("clientes_potenciales")
    por_fuente = {c.fuente_identificacion for c in actuales if c.fuente_identificacion}
    nuevos, omitidos = [], 0
    hoy = date.today()
    municipio_objetivo = _normalizar_columna(municipio) if municipio else None
    for row in rows:
        source_id = _buscar(row, "Id", "ID", "CLEE", "Clave del establecimiento")
        nombre = _buscar(row, "Nombre", "Nombre de la unidad económica", "Razon_social", "Razón social")
        actividad = _buscar(row, "Actividad_economica", "Actividad económica", "Nombre de clase de actividad")
        municipio_row = _buscar(row, "Municipio", "Municipio de la unidad económica")
        estado = _buscar(row, "Entidad federativa", "Estado") or estado_default or ""
        if municipio_objetivo and _normalizar_columna(municipio_row) != municipio_objetivo:
            omitidos += 1
            continue
        if not source_id or not nombre or not municipio_row or not estado:
            omitidos += 1
            continue
        source_ref = f"DENUE ID={source_id}"
        if source_ref in por_fuente:
            omitidos += 1
            continue
        prospecto = ClientePotencial(
            razon_social=nombre,
            segmento=_segmento(actividad),
            municipio=municipio_row,
            estado=estado,
            actividad_economica=actividad,
            fuente_identificacion=source_ref,
            fecha_identificacion=hoy,
            estatus=EstatusEmbudo.IDENTIFICADO,
            proxima_accion="Verificar necesidad, especificación y proceso de compra",
            fecha_proxima_accion=hoy,
            notas="Registro de directorio público; no es cliente confirmado. Segmento inferido por actividad y pendiente de confirmar. No importar ni almacenar teléfonos/correos.",
        )
        nuevos.append(prospecto)
        por_fuente.add(source_ref)
    if nuevos:
        store.guardar("clientes_potenciales", [*actuales, *nuevos])
    return len(nuevos), omitidos


def generar_seguimiento(store: AlmacenComercial) -> dict[str, object]:
    """Resume estado, tareas vencidas y puertas pendientes sin inferir ventas."""
    clientes = store.leer("clientes_potenciales")
    proveedores = store.leer("proveedores")
    cotizaciones = store.leer("cotizaciones")
    rutas = store.leer("rutas_logisticas")
    oportunidades = store.leer("fichas_oportunidad")
    hoy = date.today()
    clientes_por_id = {c.id: c for c in clientes}
    proveedores_por_id = {p.id: p for p in proveedores}
    cotizaciones_por_id = {c.id: c for c in cotizaciones}
    rutas_por_id = {r.id: r for r in rutas}
    fichas = []
    for ficha in oportunidades:
        cliente = clientes_por_id.get(ficha.cliente_id or "")
        proveedores_link = [proveedores_por_id.get(pid) for pid in ficha.proveedor_ids]
        compra_link = [cotizaciones_por_id.get(qid) for qid in ficha.cotizacion_compra_ids]
        venta_link = [cotizaciones_por_id.get(qid) for qid in ficha.cotizacion_venta_ids]
        ruta = rutas_por_id.get(ficha.ruta_id or "")
        bloques = []
        estatus_con_necesidad = {
            EstatusEmbudo.NECESIDAD_VERIFICADA, EstatusEmbudo.COTIZACION,
            EstatusEmbudo.PILOTO, EstatusEmbudo.NEGOCIACION, EstatusEmbudo.ACTIVO,
        }
        if not cliente or cliente.estatus not in estatus_con_necesidad:
            bloques.append("comprador vinculado con necesidad verificada")
        if not proveedores_link or any(p is None or p.estatus != EstatusVerificacion.VERIFICADO for p in proveedores_link):
            bloques.append("proveedor y capacidad verificados")
        if not compra_link or any(q is None or q.tipo != TipoCotizacion.COMPRA or not es_vigente(q, hoy) for q in compra_link):
            bloques.append("cotización de compra vigente y relacionada")
        elif any(
            not _producto_coincide(q, ficha)
            or not (q.contraparte_id in ficha.proveedor_ids or any(
                not q.contraparte_id and pid in proveedores_por_id
                and q.contraparte_nombre.casefold() == proveedores_por_id[pid].razon_social.casefold()
                for pid in ficha.proveedor_ids
            ))
            for q in compra_link
        ):
            bloques.append("cotización de compra vinculada al producto y proveedor correctos")
        if not venta_link or any(q is None or q.tipo != TipoCotizacion.VENTA or not es_vigente(q, hoy) for q in venta_link):
            bloques.append("cotización de venta vigente y relacionada")
        elif any(
            not _producto_coincide(q, ficha)
            or not cliente
            or not (q.contraparte_id == cliente.id or (
                not q.contraparte_id and q.contraparte_nombre.casefold() == cliente.razon_social.casefold()
            ))
            for q in venta_link
        ):
            bloques.append("cotización de venta vinculada al producto y comprador correctos")
        if not ruta or ruta.cotizacion_flete is None or not ruta.fecha_cotizacion or ruta.nivel_evidencia != NivelEvidencia.CONFIRMADO:
            bloques.append("ruta con flete cotizado y evidencia confirmada")
        if ficha.costos_completos_kg is None or ficha.ingreso_esperado_kg is None or ficha.margen_contribucion_kg is None:
            bloques.append("economía unitaria completa")
        elif ficha.margen_contribucion_kg <= 0:
            bloques.append("contribución base positiva")
        quotes_presentes = [q for q in [*compra_link, *venta_link] if q]
        if len({q.moneda.value for q in quotes_presentes}) > 1:
            bloques.append("monedas comparables o tipo de cambio documentado")
        if any(q.unidad.casefold() != "kg" for q in quotes_presentes):
            bloques.append("conversión a kg respaldada por peso neto y evidencia")
        if not ficha.calidad_empaque_estandares or not ficha.documentacion_requerida:
            bloques.append("calidad, empaque y documentación definidos")
        if ficha.escenario_base is None:
            bloques.append("escenarios económicos documentados")
        if not ficha.criterio_exito_piloto or not ficha.costo_limite_piloto:
            bloques.append("límite de gasto y criterio de éxito del piloto")
        # Las tablas aún no guardan una fecha límite del flete ni el dictamen regulatorio.
        bloques.append("confirmación manual de vigencia del flete y requisitos sanitarios/comerciales")
        completeness = nivel_completitud(ficha)
        fichas.append({
            "id": ficha.id, "producto": ficha.producto, "origen": ficha.origen, "destino": ficha.destino,
            "cliente": {"id": cliente.id, "estado": cliente.estatus.value} if cliente else None,
            "proveedores": [{"id": p.id, "estado": p.estatus.value} for p in proveedores_link if p],
            "cotizaciones_compra": [_resumen_cotizacion(q, hoy) for q in compra_link if q],
            "cotizaciones_venta": [_resumen_cotizacion(q, hoy) for q in venta_link if q],
            "ruta": {"id": ruta.id, "flete": ruta.cotizacion_flete,
                     "fecha_cotizacion": ruta.fecha_cotizacion.isoformat() if ruta.fecha_cotizacion else None,
                     "evidencia": ruta.nivel_evidencia.value} if ruta else None,
            "completitud": {k: v.value for k, v in completeness.items()},
            "bloqueos_para_piloto": bloques,
            "lista_para_piloto": None,
            "estado_puerta_piloto": "indeterminado: faltan campos estructurados de vigencia de flete y conformidad regulatoria",
            "contribucion_kg_registrada": ficha.margen_contribucion_kg,
            "advertencia": "el reporte no valida documentos adjuntos ni sustituye autorización comercial/regulatoria",
        })
    return {
        "fecha": hoy.isoformat(),
        "clientes_por_estatus": _conteo(c.estatus.value for c in clientes),
        "clientes_por_municipio": _conteo(c.municipio for c in clientes),
        "clientes_por_segmento": _conteo(c.segmento.value for c in clientes),
        "clientes_con_accion_vencida": [
            {"id": c.id, "nombre_comercial": c.razon_social, "accion": c.proxima_accion,
             "fecha": c.fecha_proxima_accion.isoformat()}
            for c in clientes if c.fecha_proxima_accion and c.fecha_proxima_accion <= hoy
            and c.estatus != EstatusEmbudo.DESCARTADO
        ],
        "proveedores_por_verificacion": _conteo(p.estatus.value for p in proveedores),
        "proveedores_por_producto": _conteo(p.producto for p in proveedores),
        "cotizaciones": {
            "total": len(cotizaciones),
            "vigentes": sum(es_vigente(c, hoy) for c in cotizaciones),
            "vencidas": sum(not es_vigente(c, hoy) for c in cotizaciones),
            "vencidas_detalle": [
                {"id": q.id, "producto": q.producto, "tipo": q.tipo.value,
                 "vigencia_fin": q.vigencia_fin.isoformat() if q.vigencia_fin else None}
                for q in cotizaciones if not es_vigente(q, hoy)
            ],
        },
        "rutas_sin_cotizacion_documentada": [
            r.id for r in rutas if r.cotizacion_flete is None or r.fecha_cotizacion is None
        ],
        "oportunidades": fichas,
        "limite": "El reporte ordena evidencia registrada; no confirma demanda, oferta, rentabilidad ni cumplimiento regulatorio.",
    }


def vincular_oportunidad(
    store: AlmacenComercial, oportunidad_id: str, cliente_id: str,
    proveedor_ids: list[str] | None = None, compra_ids: list[str] | None = None,
    venta_ids: list[str] | None = None, ruta_id: str | None = None,
) -> None:
    """Asocia registros existentes con una ficha y valida existencia/tipo de cada vínculo."""
    fichas = store.leer("fichas_oportunidad")
    ficha = next((f for f in fichas if f.id == oportunidad_id), None)
    if ficha is None:
        raise ValueError(f"No existe la oportunidad {oportunidad_id}")
    cliente = next((c for c in store.leer("clientes_potenciales") if c.id == cliente_id), None)
    if cliente is None:
        raise ValueError(f"No existe el cliente {cliente_id}")
    proveedores = {p.id: p for p in store.leer("proveedores")}
    cotizaciones = {q.id: q for q in store.leer("cotizaciones")}
    rutas = {r.id: r for r in store.leer("rutas_logisticas")}
    if proveedor_ids is not None:
        missing = set(proveedor_ids) - proveedores.keys()
        if missing:
            raise ValueError(f"Proveedor(es) inexistente(s): {', '.join(sorted(missing))}")
        ficha.proveedor_ids = list(dict.fromkeys(proveedor_ids))
    if compra_ids is not None:
        proveedores_oportunidad = set(proveedor_ids) if proveedor_ids is not None else set(ficha.proveedor_ids)
        for qid in compra_ids:
            quote = cotizaciones.get(qid)
            if not quote or quote.tipo != TipoCotizacion.COMPRA:
                raise ValueError(f"La cotización {qid} no existe o no es de compra")
            if not _producto_coincide(quote, ficha):
                raise ValueError(f"La cotización {qid} corresponde a otro producto")
            proveedor_coincide = quote.contraparte_id in proveedores_oportunidad or any(
                not quote.contraparte_id
                and quote.contraparte_nombre.casefold() == proveedores[pid].razon_social.casefold()
                for pid in proveedores_oportunidad if pid in proveedores
            )
            if not proveedor_coincide:
                raise ValueError(f"La cotización {qid} no corresponde a un proveedor vinculado")
        ficha.cotizacion_compra_ids = list(dict.fromkeys(compra_ids))
    if venta_ids is not None:
        for qid in venta_ids:
            quote = cotizaciones.get(qid)
            if not quote or quote.tipo != TipoCotizacion.VENTA:
                raise ValueError(f"La cotización {qid} no existe o no es de venta")
            contra_coincide = quote.contraparte_id == cliente.id or (
                not quote.contraparte_id and quote.contraparte_nombre.casefold() == cliente.razon_social.casefold()
            )
            if not contra_coincide:
                raise ValueError(f"La cotización {qid} no corresponde al comprador {cliente.id}")
            if not _producto_coincide(quote, ficha):
                raise ValueError(f"La cotización {qid} corresponde a otro producto")
        ficha.cotizacion_venta_ids = list(dict.fromkeys(venta_ids))
    if ruta_id is not None:
        if ruta_id not in rutas:
            raise ValueError(f"No existe la ruta {ruta_id}")
        ficha.ruta_id = ruta_id
    ficha.cliente_id = cliente.id
    estatus_confirmados = {
        EstatusEmbudo.NECESIDAD_VERIFICADA, EstatusEmbudo.COTIZACION,
        EstatusEmbudo.PILOTO, EstatusEmbudo.NEGOCIACION, EstatusEmbudo.ACTIVO,
    }
    ficha.estatus_verificacion_comprador = (
        EstatusVerificacion.VERIFICADO if cliente.estatus in estatus_confirmados
        else EstatusVerificacion.EN_PROCESO if cliente.estatus == EstatusEmbudo.CONVERSACION
        else EstatusVerificacion.SIN_VERIFICAR
    )
    if not ficha.necesidad_comprador:
        ficha.necesidad_comprador = cliente.necesidad_declarada
    if not ficha.evidencia_comprador:
        ficha.evidencia_comprador = cliente.evidencia_verificacion
    if not ficha.ubicacion_comprador:
        ficha.ubicacion_comprador = f"{cliente.municipio}, {cliente.estado}"
    store.guardar("fichas_oportunidad", [f if f.id != ficha.id else ficha for f in fichas])


def _resumen_cotizacion(cotizacion, hoy: date) -> dict[str, object]:
    return {
        "id": cotizacion.id, "producto": cotizacion.producto, "precio": cotizacion.precio_unitario,
        "unidad": cotizacion.unidad, "moneda": cotizacion.moneda.value,
        "vigente": es_vigente(cotizacion, hoy),
        "vigencia_fin": cotizacion.vigencia_fin.isoformat() if cotizacion.vigencia_fin else None,
    }


def _producto_coincide(cotizacion, ficha) -> bool:
    return (
        _normalizar_columna(cotizacion.producto) == _normalizar_columna(ficha.producto)
        and (not cotizacion.variedad or _normalizar_columna(cotizacion.variedad) == _normalizar_columna(ficha.variedad))
    )


def _conteo(values) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return result


if __name__ == "__main__":
    raise SystemExit(main())
