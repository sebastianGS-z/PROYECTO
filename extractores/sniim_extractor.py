"""Extractor SNIIM (precios mayoristas de frutas y hortalizas).

Estrategia basada en la estructura observada de la fuente oficial:

* Formulario: ``/nuevo/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ConsultaFrutasYHortalizas.aspx``
  con listas de producto, origen, mercado de destino y "Precios por".
* Resultados: ``.../ResultadosConsultaFechaFrutasYHortalizas.aspx`` con parámetros
  ``fechaInicio, fechaFinal, ProductoId, OrigenId, Origen, DestinoId, Destino, PreciosPorId,
  RegistrosPorPagina`` (fechas dd/mm/aaaa). La tabla trae producto, calidad, presentación,
  origen, precio mín/máx/frecuente y observaciones.

Los IDs numéricos NO se escriben a mano: se leen del formulario en tiempo de ejecución.
Todo el conocimiento del HTML vive en ``parse_formulario`` y ``parse_resultados``; si el
sitio cambia, solo se adaptan esas dos funciones.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from bs4 import BeautifulSoup

from extractores.base import BaseExtractor, RawCapture, StructureChangedError

FORM_PATH = "/nuevo/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ConsultaFrutasYHortalizas.aspx"
RESULT_PATH = "/nuevo/consultas/mercadosnacionales/preciosdemercado/agricolas/ResultadosConsultaFechaFrutasYHortalizas.aspx"
REGISTROS_POR_PAGINA = 500
NO_RESULT_PHRASES = ("no hay registros", "no se encontraron", "sin resultados", "no hay informacion", "no existen registros")


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y con espacios colapsados (solo para comparar)."""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


def decodificar_html(contenido: bytes) -> str:
    """Decodifica bytes de la fuente sin alterarlos (el original se guarda aparte)."""
    for enc in ("utf-8", "cp1252"):
        try:
            return contenido.decode(enc)
        except UnicodeDecodeError:
            continue
    return contenido.decode("latin-1", errors="replace")


@dataclass
class Opcion:
    etiqueta: str
    valor: str


@dataclass
class CatalogoFormulario:
    productos: list[Opcion] = field(default_factory=list)
    mercados: list[Opcion] = field(default_factory=list)
    precios_por: list[Opcion] = field(default_factory=list)

    def variantes_producto(self, busqueda: str) -> list[Opcion]:
        prefijo = normalizar(busqueda)
        return [o for o in self.productos if normalizar(o.etiqueta).startswith(prefijo)]

    def mercado(self, etiqueta: str) -> Opcion:
        objetivo = normalizar(etiqueta)
        for o in self.mercados:
            if normalizar(o.etiqueta) == objetivo:
                return o
        raise StructureChangedError(f"Mercado no encontrado en el formulario del SNIIM: {etiqueta!r}")

    def precio_por(self, clave: str) -> Opcion:
        prefijo = "presentacion" if clave == "presentacion" else "kilogramo"
        for o in self.precios_por:
            if normalizar(o.etiqueta).startswith(prefijo):
                return o
        raise StructureChangedError(f"Opción 'Precios por' no encontrada: {clave!r}")


def parse_formulario(html: str) -> CatalogoFormulario:
    """Extrae productos, mercados y 'Precios por' (con sus valores) del formulario."""
    soup = BeautifulSoup(html, "html.parser")
    cat = CatalogoFormulario()
    for sel in soup.find_all("select"):
        opciones = [Opcion(o.get_text(" ", strip=True), (o.get("value") or "").strip()) for o in sel.find_all("option")]
        normas = [normalizar(o.etiqueta) for o in opciones]
        if not cat.productos and any(n.endswith("- primera") for n in normas):
            cat.productos = opciones
        elif not cat.mercados and any(n.startswith("jalisco:") for n in normas) and any("central de abasto" in n for n in normas):
            cat.mercados = opciones
        elif not cat.precios_por and any(n.startswith("kilogramo") for n in normas):
            cat.precios_por = opciones
    faltan = [n for n, v in (("productos", cat.productos), ("mercados", cat.mercados), ("precios_por", cat.precios_por)) if not v]
    if faltan:
        raise StructureChangedError(f"El formulario del SNIIM cambió; no se encontraron listas: {', '.join(faltan)}")
    for lista in (cat.productos, cat.mercados, cat.precios_por):
        if any(not o.valor for o in lista):
            raise StructureChangedError("Opciones del formulario sin atributo value; no se pueden construir consultas")
    return cat


@dataclass
class ResultadoParseado:
    registros: list[dict[str, str]]
    pagina: tuple[int, int] | None
    sin_resultados: bool
    filas_no_interpretadas: int = 0


def _int_attr(celda, nombre: str) -> int:
    try:
        return max(1, int(celda.get(nombre, 1) or 1))
    except (TypeError, ValueError):
        return 1


def _rejilla(tabla) -> list[list[str]]:
    """Convierte una tabla HTML en filas de texto respetando rowspan y colspan.

    En el SNIIM, producto y calidad pueden venir combinados verticalmente (rowspan); la rejilla
    repite ese valor en cada fila para no perder columnas.
    """
    filas: list[list[str]] = []
    pendientes: dict[int, list] = {}  # columna -> [texto, filas restantes]
    for tr in tabla.find_all("tr"):
        if tr.find_parent("table") is not tabla:
            continue
        celdas = iter(tr.find_all(["td", "th"], recursive=False))
        fila: list[str] = []
        col = 0
        while True:
            if col in pendientes:
                texto, resto = pendientes[col]
                fila.append(texto)
                if resto > 1:
                    pendientes[col] = [texto, resto - 1]
                else:
                    del pendientes[col]
                col += 1
                continue
            celda = next(celdas, None)
            if celda is None:
                break
            texto, cs, rs = celda.get_text(" ", strip=True), _int_attr(celda, "colspan"), _int_attr(celda, "rowspan")
            for _ in range(cs):
                fila.append(texto)
                if rs > 1:
                    pendientes[col] = [texto, rs - 1]
                col += 1
        filas.append(fila)
    return filas


def parse_resultados(html: str) -> ResultadoParseado:
    """Interpreta la página de resultados. Los valores se conservan como texto original."""
    soup = BeautifulSoup(html, "html.parser")
    texto_norm = normalizar(soup.get_text(" "))
    m = re.search(r"pagina (\d+) de (\d+)", texto_norm)
    pagina = (int(m.group(1)), int(m.group(2))) if m else None

    tabla = None
    for tr in soup.find_all("tr"):
        normas = [normalizar(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"], recursive=False)]
        if any(n.startswith("precio min") and len(n) < 20 for n in normas) and any(n.startswith("precio max") and len(n) < 20 for n in normas):
            tabla = tr.find_parent("table")
            break
    if tabla is None:
        if any(frase in texto_norm for frase in NO_RESULT_PHRASES):
            return ResultadoParseado([], pagina, True)
        raise StructureChangedError("No se encontró la tabla de precios (encabezados 'Precio Mín/Máx/Frec.')")

    filas = _rejilla(tabla)
    idx = next(i for i, f in enumerate(filas) if any(normalizar(c).startswith("precio min") and len(normalizar(c)) < 20 for c in f))
    encabezados = filas[idx]
    claves: list[str] = []
    for h in encabezados:
        base, k = h or "columna", 2
        clave = base
        while clave in claves:
            clave, k = f"{base}_{k}", k + 1
        claves.append(clave)

    registros: list[dict[str, str]] = []
    omitidas = 0
    for fila in filas[idx + 1:]:
        if not any(fila) or fila == encabezados:
            continue
        if len(fila) > 1 and len(set(fila)) == 1:
            continue  # fila de sección (p. ej. "Frutas") con colspan
        if len(fila) == len(claves):
            registros.append(dict(zip(claves, fila)))
        elif len(fila) > 1:
            omitidas += 1  # forma inesperada: se reporta, no se inventa
    if not registros and omitidas:
        raise StructureChangedError(f"Se encontró la tabla pero {omitidas} filas no coinciden con el encabezado")
    return ResultadoParseado(registros, pagina, not registros, omitidas)


class SniimExtractor(BaseExtractor):
    fuente = "sniim"

    def __init__(self, *args: Any, precios_por: str = "presentacion", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.precios_por = precios_por
        self._catalogo: CatalogoFormulario | None = None
        self.formulario_captura: RawCapture | None = None

    def cargar_catalogo(self) -> CatalogoFormulario:
        """Descarga el formulario y descubre IDs de producto, mercado y 'Precios por'."""
        if self._catalogo is None:
            resp = self.get(self.settings.sniim_base_url + FORM_PATH)
            self._catalogo = parse_formulario(decodificar_html(resp.content))
            self.formulario_captura = RawCapture(
                fuente=self.fuente, url=resp.url, contenido=resp.content, formato="html",
                http_status=resp.status_code, registros=len(self._catalogo.productos), estado="ok",
                metadatos={"etiqueta": "catalogo-formulario", "tipo": "formulario"},
            )
            self.log.info("Catálogo SNIIM: %d productos, %d mercados", len(self._catalogo.productos), len(self._catalogo.mercados))
        return self._catalogo

    def variantes(self, busqueda: str) -> list[Opcion]:
        """Variantes del formulario para un producto (p. ej. 'Plátano' → Tabasco, Chiapas…)."""
        vs = self.cargar_catalogo().variantes_producto(busqueda)
        if not vs:
            raise StructureChangedError(f"El formulario no ofrece variantes para {busqueda!r}")
        return vs

    def fetch_precios(self, variante: Opcion, mercado_etiqueta: str, inicio: date, fin: date) -> RawCapture:
        """Una consulta: variante de producto × mercado × intervalo de fechas."""
        cat = self.cargar_catalogo()
        mercado = cat.mercado(mercado_etiqueta)
        precios_por = cat.precio_por(self.precios_por)
        params = [
            ("fechaInicio", inicio.strftime("%d/%m/%Y")),
            ("fechaFinal", fin.strftime("%d/%m/%Y")),
            ("ProductoId", variante.valor),
            ("OrigenId", "-1"),
            ("Origen", "Todos"),
            ("DestinoId", mercado.valor),
            ("Destino", mercado.etiqueta),
            ("PreciosPorId", precios_por.valor),
            ("RegistrosPorPagina", str(REGISTROS_POR_PAGINA)),
        ]
        resp = self.get(self.settings.sniim_base_url + RESULT_PATH, params=params)
        try:
            parsed = parse_resultados(decodificar_html(resp.content))
        except StructureChangedError as exc:
            exc.contenido, exc.url = resp.content, resp.url  # para diagnóstico en el pipeline
            raise
        advertencias: list[str] = []
        estado = "sin_resultados" if parsed.sin_resultados else "ok"
        if parsed.pagina and parsed.pagina[1] > 1:
            estado = "parcial"
            advertencias.append(f"La fuente reporta {parsed.pagina[1]} páginas; solo se capturó la primera")
        if parsed.filas_no_interpretadas:
            advertencias.append(f"{parsed.filas_no_interpretadas} filas con forma distinta a la del encabezado no se contaron")
        return RawCapture(
            fuente=self.fuente, url=resp.url, contenido=resp.content, formato="html",
            http_status=resp.status_code, registros=len(parsed.registros), estado=estado, advertencias=advertencias,
            metadatos={
                "etiqueta": f"{variante.etiqueta}__{mercado.etiqueta}",
                "producto": variante.etiqueta, "producto_id": variante.valor,
                "mercado": mercado.etiqueta, "mercado_id": mercado.valor,
                "fecha_ref_inicio": inicio.isoformat(), "fecha_ref_fin": fin.isoformat(),
                "parametros": dict(params),
            },
        )
