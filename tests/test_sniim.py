"""Pruebas del extractor SNIIM con HTML FIXTURE (no es una captura real).

Los fixtures imitan la estructura observada en la fuente (listas del formulario y tabla con
Producto/Calidad/Presentación/Origen/Precio Mín/Máx/Frec/Obs.). La validación contra el sitio real
está en tests/test_integracion_real.py (marcada 'integration').
"""
from datetime import date

import pytest

from extractores.base import StructureChangedError
from extractores.sniim_extractor import (SniimExtractor, normalizar, parse_formulario, parse_resultados)
from tests.conftest import FakeResponse, FakeSession

FORM = """<html><body><form>
<select name="p"><option value="-1">Todos</option><option value="101">Plátano Tabasco - Primera</option>
<option value="102">Plátano Macho - Primera</option><option value="201">Limón c/semilla # 4 - Primera</option>
<option value="301">Papaya Maradol - Primera</option><option value="400">Lima - Primera</option></select>
<select name="o"><option value="-1">Todos</option><option value="14">Chiapas</option></select>
<select name="d"><option value="-1">Todos</option><option value="150">México: Central de Abasto de Toluca</option>
<option value="55">Jalisco: Mercado de Abasto de Guadalajara</option><option value="9">DF: Central de Abasto de Iztapalapa DF</option></select>
<select name="pp"><option value="1">Presentación Comercial (encuestado)</option><option value="2">Kilogramo (calculado)</option></select>
</form></body></html>"""

RESULTADOS = """<html><body><table><tr><td>
<table><tr><td>Registros del 01/03/2026 al 31/03/2026</td></tr><tr><td>Página 1 de 1</td></tr></table>
<table>
<tr><td>Fecha</td><td>Producto</td><td>Calidad</td><td>Presentación</td><td>Origen</td><td>Precio Mín</td><td>Precio Max</td><td>Precio Frec</td><td>Obs.</td></tr>
<tr><td colspan="9">Frutas</td></tr>
<tr><td>02/03/2026</td><td>Plátano Tabasco</td><td>Primera</td><td>Caja de 18 kg.</td><td>Tabasco</td><td>22.22</td><td>25.00</td><td>22.22</td><td></td></tr>
<tr><td>03/03/2026</td><td>Plátano Tabasco</td><td>Primera</td><td>Caja de 18 kg.</td><td>Tabasco</td><td>23.00</td><td>25.00</td><td>24.00</td><td>N</td></tr>
</table></td></tr></table></body></html>"""

SIN = "<html><body><table><tr><td>Precio Mín</td><td>Precio Max</td><td>Precio Frec</td></tr></table></body></html>"


def test_normalizar():
    assert normalizar("  Plátano   Tabasco ") == "platano tabasco"


def test_parse_formulario_descubre_ids():
    cat = parse_formulario(FORM)
    assert [o.valor for o in cat.variantes_producto("Plátano")] == ["101", "102"]
    assert cat.variantes_producto("Limón")[0].valor == "201"
    assert cat.mercado("Jalisco: Mercado de Abasto de Guadalajara").valor == "55"
    assert cat.precio_por("presentacion").valor == "1" and cat.precio_por("kilogramo").valor == "2"
    assert all(o.etiqueta != "Lima - Primera" for o in cat.variantes_producto("Limón"))


def test_formulario_cambiado_falla_claro():
    with pytest.raises(StructureChangedError):
        parse_formulario("<html><body>mantenimiento</body></html>")


def test_parse_resultados_conserva_texto_original():
    r = parse_resultados(RESULTADOS)
    assert len(r.registros) == 2 and r.pagina == (1, 1)
    assert r.registros[0]["Precio Frec"] == "22.22" and r.registros[1]["Obs."] == "N"
    assert r.registros[0]["Presentación"] == "Caja de 18 kg."


def test_sin_resultados_con_tabla_vacia():
    r = parse_resultados(SIN)
    assert r.sin_resultados and r.registros == []


def test_estructura_inesperada():
    with pytest.raises(StructureChangedError):
        parse_resultados("<html><body><p>Error del servidor ASP.NET</p></body></html>")


def make(settings, resultados=RESULTADOS):
    s = FakeSession({"robots.txt": [FakeResponse(404, b"x")],
                     "ConsultaFrutasYHortalizas.aspx": [FakeResponse(200, FORM)],
                     "ResultadosConsulta": [FakeResponse(200, resultados)]})
    return SniimExtractor(settings, session=s), s


def test_fetch_precios_arma_url_y_metadatos(settings):
    e, s = make(settings)
    var = e.variantes("Plátano")[0]
    cap = e.fetch_precios(var, "Jalisco: Mercado de Abasto de Guadalajara", date(2026, 3, 1), date(2026, 3, 31))
    url = [u for _, u in s.llamadas if "ResultadosConsulta" in u][0]
    for frag in ("fechaInicio=01%2F03%2F2026", "fechaFinal=31%2F03%2F2026", "ProductoId=101", "DestinoId=55", "PreciosPorId=1"):
        assert frag in url
    assert cap.registros == 2 and cap.estado == "ok" and cap.formato == "html"
    assert cap.metadatos["producto"] == "Plátano Tabasco - Primera" and cap.url == url
    assert cap.contenido == RESULTADOS.encode("utf-8")


def test_fetch_sin_resultados(settings):
    e, _ = make(settings, SIN)
    cap = e.fetch_precios(e.variantes("Papaya")[0], "DF: Central de Abasto de Iztapalapa DF", date(2026, 3, 1), date(2026, 3, 31))
    assert cap.estado == "sin_resultados" and cap.registros == 0


def test_paginacion_multiple_marca_parcial(settings):
    e, _ = make(settings, RESULTADOS.replace("Página 1 de 1", "Página 1 de 3"))
    cap = e.fetch_precios(e.variantes("Plátano")[0], "DF: Central de Abasto de Iztapalapa DF", date(2026, 3, 1), date(2026, 3, 31))
    assert cap.estado == "parcial" and any("páginas" in a for a in cap.advertencias)


def test_mercado_inexistente(settings):
    e, _ = make(settings)
    with pytest.raises(StructureChangedError):
        e.fetch_precios(e.variantes("Plátano")[0], "Marte: Central", date(2026, 3, 1), date(2026, 3, 2))


ROWSPAN = """<table><tr><td>Página 1 de 1</td></tr></table>
<table><tr><td>Producto</td><td>Calidad</td><td>Presentación</td><td>Origen</td><td>Destino</td><td>Precio Mín</td><td>Precio Max</td><td>Precio Frec</td><td>Obs.</td></tr>
<tr><td colspan="9">Frutas</td></tr>
<tr><td rowspan="2">Naranja Valencia grande</td><td rowspan="2">Primera</td><td>Ciento</td><td>Yucatán</td><td>Campeche</td><td>140.00</td><td>150.00</td><td>140.00</td><td></td></tr>
<tr><td>Kilogramo</td><td>Veracruz</td><td>DF: Central de Abasto de Iztapalapa DF</td><td>15.00</td><td>16.00</td><td>15.50</td><td></td></tr></table>"""


def test_rowspan_y_colspan_no_pierden_columnas():
    r = parse_resultados(ROWSPAN)
    assert len(r.registros) == 2 and r.filas_no_interpretadas == 0
    assert r.registros[1]["Producto"] == "Naranja Valencia grande" and r.registros[1]["Calidad"] == "Primera"
    assert r.registros[1]["Destino"] == "DF: Central de Abasto de Iztapalapa DF" and r.registros[1]["Precio Frec"] == "15.50"


def test_filas_que_no_coinciden_no_se_confunden_con_sin_resultados():
    roto = "<table><tr><td>Precio Mín</td><td>Precio Max</td><td>Precio Frec</td></tr><tr><td>a</td><td>b</td></tr></table>"
    with pytest.raises(StructureChangedError):
        parse_resultados(roto)


NO_HAY = """<html><body><table><tr><td>Mercados Nacionales Agrícolas Frutas y Hortalizas Precios al mayoreo de Frutas y Hortalizas .
Pesos ($) por presentación comercial Registros del 26/10/2026 al 05/11/2026</td></tr>
<tr><td>NO HAY REGISTROS (cambie su consulta e intente nuevamente)</td></tr></table></body></html>"""


def test_mensaje_real_no_hay_registros_es_sin_resultados():
    """Texto observado en una respuesta real del SNIIM (2026-11-09) para Papaya Amarilla en Iztapalapa."""
    r = parse_resultados(NO_HAY)
    assert r.sin_resultados and r.registros == []
