# Declaración de ética y legalidad de datos

**Proyecto:** Observatorio de Agro-Inteligencia Colimense (OAIC)
**Revisión:** 2026-11-17
**Alcance:** SNIIM, NOAA NCEI y Marco Geoestadístico de INEGI. Esta declaración describe la política operativa del proyecto; no sustituye asesoría legal.

## Fuentes, permisos y condiciones de acceso

| Fuente | Uso en OAIC | Términos/licencia y atribución | robots.txt y captura |
|---|---|---|---|
| SNIIM, Secretaría de Economía | Precios mayoristas de referencia por producto, mercado y presentación | El SNIIM informa que sus precios son referenciales, públicos y que el uso es responsabilidad de quien los utiliza. Se atribuye al Sistema Nacional de Información e Integración de Mercados / Secretaría de Economía. No se redistribuye la interfaz web. [Preguntas frecuentes](https://www.economia-sniim.gob.mx/nuevo/Preguntas%20Frecuentes.htm) | `https://www.economia-sniim.gob.mx/robots.txt`; la ruta utilizada no figura como prohibida. Se consulta antes de extraer, con pausa y User-Agent identificable. |
| NOAA NCEI, GHCN-Daily | Observaciones meteorológicas de la estación MXM00076654 | Los datos ambientales federales de NOAA son de acceso abierto salvo restricciones específicas; NCEI solicita reconocer la fuente. Atribución: NOAA National Centers for Environmental Information (NCEI), GHCN-Daily, estación y periodo consultados. Las coordenadas de estación se verifican contra el [catálogo GHCN-Daily](https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt). [Política de datos abiertos NCEI](https://www.ncei.noaa.gov/archive) | `https://www.ncei.noaa.gov/robots.txt`; se usa la ruta `/access/services/data/v1`, no incluida entre las rutas disallow del archivo revisado. No se consultan rutas bloqueadas. |
| INEGI, Marco Geoestadístico municipal | Polígonos municipales de Colima y atributos agregados del Censo 2020 para mapa y dimensión geográfica | Los términos del INEGI autorizan usar la información si se cita la fuente y prohíben comercializar el derecho de acceso al sitio. Atribución: “Fuente: Sitio del INEGI en Internet: www.inegi.org.mx”; OAIC identifica además Marco Geoestadístico, edición de geometría y edición de atributos. [Términos de uso](https://www.inegi.org.mx/inegi/terminos.html), [condiciones de uso](https://ci.inegi.org.mx/condiciones-de-uso/) | `https://gaia.inegi.org.mx/robots.txt` respondió 404 el 2026-11-17 (no hay archivo de reglas publicado en ese host). La consulta se limita a una petición por ejecución diaria a la capa `geo/mgem/06`; el transporte común aplica pausa mínima, reintentos limitados y User-Agent identificable. Si el host publica reglas o devuelve prohibición, la captura se detiene. |

**Nota sobre robots.txt:** una respuesta 404 solo significa que el host no publicó ese archivo en esa ruta; no se interpreta como licencia. Los términos publicados por el proveedor y las prácticas de consulta se evalúan por separado.

## Privacidad y minimización

- No se capturan nombres de personas, teléfonos, correos, domicilios particulares, perfiles sociales ni identificadores de productores.
- INEGI se usa a nivel municipal con población y vivienda agregadas, nunca microdatos censales. La geometría delimita unidades territoriales oficiales, no predios ni parcelas individuales.
- NOAA se limita a observaciones ambientales de una estación meteorológica y SNIIM a precios de referencia.
- Los archivos de origen conservan solo los campos devueltos por estas fuentes públicas. Los informes y mapas no incluyen información personal.

## Sesgos, límites y uso responsable

- SNIIM refleja mercados y presentaciones observados por sus informantes; no representa automáticamente el precio recibido en parcela ni todas las transacciones de Colima. Los precios por caja, ciento u otra presentación no se convierten a kg si no existe peso verificable.
- La estación meteorológica de Manzanillo no es una medición de Tecomán ni de cada huerta. No se extrapolan sus observaciones como si describieran uniformemente todo el estado.
- El Marco Geoestadístico aporta límites municipales; la población y viviendas provienen del Censo 2020, aunque la geometría reportada por el servicio sea de diciembre de 2025. Se mantienen ambos años de referencia explícitos para evitar presentar los atributos censales como actuales.
- El mapa destaca Tecomán, Armería y Manzanillo por ser áreas de interés del observatorio; el resaltado no significa que INEGI las identifique como zonas productoras ni que el conteo de población mida producción agrícola.
- Se documentan observaciones faltantes, procedencia y fecha de ingesta. No se sustituyen ausencias de fuente por ceros. Los modelos deben validarse temporalmente y sus resultados se presentan como apoyo, no como garantía de precio o rendimiento.

## Trazabilidad y retención

Los bytes originales se conservan en `data/bronce/` con sidecar que incluye URL, fuente, timestamp de captura, ejecución y SHA-256. Los productos de Plata y Oro incluyen referencia al archivo Bronce, hash, índice del registro de origen cuando aplica y fecha UTC de ingesta. El Marco Geoestadístico se mantiene como una dimensión geoespacial separada en Oro para no atribuir sus límites o población a una fila de precio con otra unidad geográfica.

Los originales no se sobrescriben. Una nueva captura crea una nueva versión; correcciones y transformaciones se vuelven a generar desde Bronce. Si una fuente cambia sus condiciones, su licencia o robots.txt, se suspende la extracción afectada hasta revisar el cambio.
