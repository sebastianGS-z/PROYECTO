"""Pruebas del módulo opcional de seguimiento comercial y costeo (datos FIXTURE, no operaciones reales)."""
from __future__ import annotations

import pytest

from scripts import comercial
from src.economia import (
    ComponenteCosto,
    CostoPuestoEnDestino,
    CriterioPriorizacion,
    Escenario,
    ModeloEconomico,
    PuntuacionCriterio,
    calcular_capital_trabajo,
    calcular_costo_merma,
    comparar_oportunidades,
    matriz_priorizacion,
    puntuar_oportunidad,
    validar_pesos,
)
from src.economia.priorizacion import CRITERIOS_DEFAULT
from src.modelos import AlmacenComercial, NivelEvidencia, Segmento, esquemas

C = NivelEvidencia.CONFIRMADO


def comp(valor, unidad="kg", ev=C, moneda="MXN"):
    return ComponenteCosto(valor=valor, unidad=unidad, moneda=moneda, fuente="cotización fixture", fecha="2026-11-20", nivel_evidencia=ev)


def costo(**cambios):
    base = dict(compra_producto=comp(10), empaque=comp(1), acopio=comp(0.5), flete_peajes_seguro=comp(5000, "viaje"),
                merma_rechazo=comp(0.8), comisiones_operacion=comp(0.2), impuestos_cumplimiento=comp(0))
    base.update(cambios)
    return CostoPuestoEnDestino(**base)


# --- Costeo ------------------------------------------------------------------------------------

def test_componente_valida_y_normaliza():
    c = ComponenteCosto(valor="3.5", unidad=" kg ", moneda="mxn", fuente=" ", fecha="2026-01-02T10:00", nivel_evidencia="ESTIMADO")
    assert c.valor == 3.5 and c.unidad == "kg" and c.moneda == "MXN" and c.fuente == "no_especificada"
    assert c.nivel_evidencia is NivelEvidencia.ESTIMADO and not c.is_pendiente
    assert ComponenteCosto().is_pendiente
    assert c.to_dict()["valor"] == 3.5
    for malo in ({"valor": -1}, {"valor": "x"}, {"valor": float("inf")}, {"unidad": ""}, {"moneda": " "}):
        with pytest.raises(ValueError):
            ComponenteCosto(**malo)


def test_costo_total_por_kg_prorratea_viaje_y_no_asume_cero():
    total = costo().total_por_kg(1000)
    assert total == pytest.approx(10 + 1 + 0.5 + 5 + 0.8 + 0.2)
    assert costo(compra_producto=comp(10000, "ton")).total_por_kg(1000) == pytest.approx(10 + 1 + 0.5 + 5 + 0.8 + 0.2)
    pendiente = costo(empaque=ComponenteCosto())
    assert pendiente.total_por_kg(1000) is None
    assert pendiente.componentes_pendientes() == ["empaque"] and not pendiente.tiene_datos_completos()
    assert set(costo().desglose()) == set(costo().componentes())
    with pytest.raises(ValueError):
        costo().total_por_kg(0)
    with pytest.raises(ValueError):
        costo(empaque=comp(1, moneda="USD")).total_por_kg(100)
    with pytest.raises(ValueError):
        costo(empaque=comp(1, "pieza")).total_por_kg(100)


def esc(nombre, ingreso, costo_kg, volumen=1000, fijos=2000):
    return Escenario(nombre, comp(ingreso), comp(costo_kg), comp(volumen), comp(fijos, "global"))


def test_escenario_contribucion_y_equilibrio():
    e = esc("Base", 20, 15)
    assert e.nombre == "base"
    assert e.contribucion_neta_kg() == 5 and e.contribucion_pedido() == 5000
    assert e.punto_equilibrio_kg() == pytest.approx(400)
    assert e.es_viable() is True
    assert esc("x", 10, 15).punto_equilibrio_kg() is None
    assert esc("x", 10, 15).es_viable() is False
    sin_dato = Escenario("x", ComponenteCosto(), comp(1), comp(1))
    assert sin_dato.contribucion_neta_kg() is None and sin_dato.contribucion_pedido() is None
    assert isinstance(e.resumen(), dict)
    with pytest.raises(ValueError):
        Escenario(" ", comp(1), comp(1), comp(1))
    with pytest.raises(ValueError):
        Escenario("x", comp(1, moneda="USD"), comp(1), comp(1)).contribucion_neta_kg()


def test_modelo_economico_compara_y_sensibiliza():
    m = ModeloEconomico(esc("conservador", 18, 16), esc("base", 20, 15), esc("favorable", 22, 14), "limón GDL")
    assert m.validar() == []
    comparacion = m.comparar_escenarios()
    assert isinstance(comparacion, dict) and comparacion
    for variable in ("ingreso", "costo", "volumen", "costos_fijos"):
        filas = m.sensibilidad(variable, 0.2)
        assert filas and all(isinstance(f, dict) for f in filas)
    with pytest.raises(ValueError):
        m.sensibilidad("clima", 0.1)
    assert m.to_dict()["nombre_oportunidad"] == "limón GDL"
    assert "limón GDL" in m.resumen_ejecutivo()
    incoherente = ModeloEconomico(esc("conservador", 25, 10), esc("base", 20, 15), esc("favorable", 15, 20))
    assert incoherente.validar()


def test_calculos_auxiliares():
    assert calcular_costo_merma(10, 5) == calcular_costo_merma(10, 0.05) == 0.5
    with pytest.raises(ValueError):
        calcular_costo_merma(10, 150)
    assert calcular_capital_trabajo(100000, 30, 0) > 0
    assert calcular_capital_trabajo(100000, 0, 30) == 0.0


# --- Priorización ------------------------------------------------------------------------------

def puntuaciones(valor, ev=C):
    return [PuntuacionCriterio(c.nombre, valor, ev, "fixture") for c in CRITERIOS_DEFAULT]


def test_priorizacion_ordena_y_alerta_incertidumbre():
    assert validar_pesos(CRITERIOS_DEFAULT) == []
    assert validar_pesos([CriterioPriorizacion("a", 0.3, "x")])
    with pytest.raises(ValueError):
        CriterioPriorizacion("a", 1.5, "x")
    alta = puntuar_oportunidad(puntuaciones(8))
    assert alta["puntuacion_ponderada"] > 0 and not alta["calidad_evidencia"]["alerta_incertidumbre"]
    supuesta = puntuar_oportunidad(puntuaciones(9, NivelEvidencia.SUPUESTO))
    assert supuesta["calidad_evidencia"]["alerta_incertidumbre"]
    ranking = comparar_oportunidades({"A": puntuaciones(5), "B": puntuaciones(8)})
    assert [r["oportunidad"] for r in ranking] == ["B", "A"] and ranking[0]["ranking"] == 1
    matriz = matriz_priorizacion({"A": puntuaciones(5), "B": puntuaciones(8)})
    assert len(matriz) == 2 and "puntuacion_ponderada" in matriz.columns


# --- Seguimiento comercial (CLI) ---------------------------------------------------------------

def test_cli_inicializa_valida_importa_y_resume(tmp_path, capsys):
    d = tmp_path / "comercial"
    assert comercial.main(["--directorio", str(d), "inicializar"]) == 0
    assert set(p.stem for p in d.glob("*.csv")) >= set(esquemas())
    assert comercial.main(["--directorio", str(d), "validar"]) == 0
    denue = tmp_path / "denue.csv"
    denue.write_text(
        "ID,Nombre de la unidad económica,Nombre de clase de actividad,Municipio,Entidad federativa,Teléfono,Correo electrónico\n"
        "1,Frutas Uno,Comercio al por mayor de frutas y verduras frescas,Colima,Colima,3120000000,a@b.mx\n"
        "2,Hotel Dos,Hoteles con otros servicios integrados,Manzanillo,Colima,,\n"
        "3,Sin municipio,Restaurantes,,Colima,,\n",
        encoding="utf-8")
    assert comercial.main(["--directorio", str(d), "importar-denue", str(denue)]) == 0
    # reimportar no duplica
    assert comercial.main(["--directorio", str(d), "importar-denue", str(denue)]) == 0
    clientes = AlmacenComercial(d).leer("clientes_potenciales")
    assert len(clientes) == 2
    assert {c.segmento for c in clientes} <= set(Segmento)
    contenido = (d / "clientes_potenciales.csv").read_text(encoding="utf-8")
    assert "3120000000" not in contenido and "a@b.mx" not in contenido  # cero datos personales
    assert comercial.main(["--directorio", str(d), "seguimiento"]) == 0
    assert capsys.readouterr().out


def test_importar_denue_filtra_municipio(tmp_path):
    store = AlmacenComercial(tmp_path)
    store.inicializar()
    f = tmp_path / "d.csv"
    f.write_text("CLEE;Nombre;Actividad económica;Municipio\n9;Tienda;Tiendas de abarrotes;Tecomán\n8;Otra;Restaurantes;Colima\n",
                 encoding="cp1252")
    nuevos, omitidos = comercial.importar_denue(store, f, estado_default="Colima", municipio="tecoman")
    assert (nuevos, omitidos) == (1, 1)


# --- Validaciones de entidades ------------------------------------------------------------------

def test_validaciones_detectan_registros_incompletos_y_aceptan_completos():
    from datetime import date, timedelta

    from src.modelos import (
        ClientePotencial,
        Cotizacion,
        FichaOportunidad,
        OperacionPiloto,
        Proveedor,
        RutaLogistica,
        es_vigente,
        nivel_completitud,
        validar_cliente,
        validar_cotizacion,
        validar_oportunidad,
        validar_piloto,
        validar_proveedor,
        validar_ruta,
    )
    from src.modelos.enums import Moneda, TipoCotizacion

    assert validar_cliente(ClientePotencial(razon_social="Frutas Uno", municipio="Colima", estado="Colima",
                                            proxima_accion="Verificar necesidad", fecha_proxima_accion=date(2026, 11, 30))) == []
    assert len(validar_cliente(ClientePotencial())) >= 3
    hoy = date(2026, 11, 20)
    cot = Cotizacion(tipo=TipoCotizacion.VENTA, contraparte_nombre="Frutas Uno", producto="limón", precio_unitario=18.5,
                     moneda=Moneda.MXN, unidad="kg", vigencia_inicio=hoy, vigencia_fin=hoy + timedelta(days=7),
                     evidencia="correo fixture", nivel_evidencia=NivelEvidencia.CONFIRMADO)
    assert validar_cotizacion(cot) == []
    assert es_vigente(cot, hoy + timedelta(days=3)) and not es_vigente(cot, hoy + timedelta(days=30))
    assert not es_vigente(Cotizacion(vigencia_fin=None), hoy)
    malo = Cotizacion(precio_unitario=0, unidad="", vigencia_fin=None)
    errores = validar_cotizacion(malo)
    assert any("unidad" in e for e in errores) and any("precio" in e for e in errores)
    for entidad, validador in ((Proveedor(), validar_proveedor), (RutaLogistica(), validar_ruta),
                               (OperacionPiloto(), validar_piloto), (FichaOportunidad(), validar_oportunidad)):
        assert validador(entidad), type(entidad).__name__  # vacíos: siempre reportan faltantes
        ida_vuelta = type(entidad).from_dict(entidad.to_dict())
        assert ida_vuelta.to_dict() == entidad.to_dict()
    completitud = nivel_completitud(FichaOportunidad())
    assert completitud and all(isinstance(v, NivelEvidencia) for v in completitud.values())
