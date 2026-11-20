# Datasheet · Panel mensual agroclimático OAIC

## A. Identificación

- **Nombre:** Panel mensual agroclimático de precios mayoristas de frutas y clima de Manzanillo.
- **Versión:** 1.0.0 · **publicación:** 2026-11-20 · **última revisión:** 2026-11-20.
- **Responsables:** Grageda Sandoval Sebastián y Jose Negrete Orozco, Observatorio de Agro-Inteligencia Colimense (OAIC).
- **Archivo:** [`data/publico/panel_mensual_e3.csv`](../../data/publico/panel_mensual_e3.csv), UTF-8, CSV, 712 filas de datos y 48 columnas.
- **Descripción:** agregados mensuales de cotizaciones mayoristas observadas para plátano, limón y papaya en dos mercados, relacionados por año y mes con resúmenes diarios de la estación NOAA GHCN-Daily de Manzanillo. Cada fila conserva el linaje de las observaciones de precios y clima.
- **Fuentes:** Sistema Nacional de Información e Integración de Mercados (SNIIM), Secretaría de Economía; NOAA NCEI, GHCN-Daily. El Marco Geoestadístico de INEGI se entrega aparte en E2 y no se une a cotizaciones de plazas externas.
- **Licencia:** CC BY 4.0 para la contribución de selección, organización, agregación y documentación de OAIC, hasta donde OAIC tenga derechos para licenciarla. Los contenidos fuente conservan sus propios términos; ver [`data/publico/LICENSE.md`](../../data/publico/LICENSE.md) y [`docs/etica-datos.md`](../etica-datos.md).

## B. Motivación

El dataset se creó para estudiar la evolución mensual de precios mayoristas de frutas seleccionadas junto con las condiciones meteorológicas observadas en una estación de Colima. Sirve como producto reproducible del observatorio y como insumo exploratorio para análisis de series de tiempo. Sus usuarios potenciales son estudiantes, docentes y analistas que necesiten cotizaciones agregadas con referencias de procedencia. No representa precios pagados al productor.

## C. Composición

- **Tamaño:** 712 filas × 48 variables; una fila por cultivo, variante, mercado, origen, presentación, año y mes. No hay claves mensuales duplicadas en la versión publicada.
- **Periodo de los agregados:** noviembre de 2023 a noviembre de 2026. La disponibilidad por producto/mercado varía dentro del intervalo; no implica observación en todos los meses.
- **Cobertura:** mercados 100 (Mercado de Abasto de Guadalajara) y 140 (Central de Abasto de Iztapalapa, Ciudad de México), conforme al catálogo del proyecto; clima de la estación NOAA MXM00076654, Manzanillo, Colima. Los mercados no son municipios productores.
- **Cultivos:** plátano 337 filas, limón 225, papaya 150. Por mercado: código 100, 374 filas; código 140, 338.
- **Conteo de cotizaciones por agregado:** 1–23; mediana 21. El conteo de días climáticos observados está entre 21 y 31 cuando existe cobertura mensual.
- **Nulos observados:** 116 filas (16.3%) no tienen linaje/clima mensual asociado; 174 filas (24.4%) tienen `tavg_c_mean` ausente por cobertura o valores diarios faltantes. Los nulos significan dato no disponible, nunca cero. La desviación estándar de precio queda nula en grupos con una sola observación.
- **Datos personales:** no se recopilan ni publican identificadores de personas.

### Diccionario de variables

| Variable | Tipo lógico | Unidad / significado |
|---|---|---|
| `cultivo` | texto | Clave normalizada: `limon`, `platano` o `papaya`. |
| `variante` | texto | Nombre de producto/calidad comunicado por SNIIM. |
| `variante_id` | texto | Identificador de variante en el formulario SNIIM. |
| `mercado` | texto/código | Código de mercado SNIIM; consultar cobertura arriba. |
| `origen` | texto | Origen declarado en la cotización SNIIM. |
| `presentacion` | texto | Unidad comercial que declara SNIIM (por ejemplo, arpilla de 19 kg); puede variar entre filas. |
| `anio` | entero | Año calendario del agregado. |
| `mes` | entero | Mes calendario, 1–12. |
| `precio_min_mean` | decimal | Media mensual de precio mínimo, MXN por presentación comercial declarada. |
| `precio_min_median` | decimal | Mediana mensual de precio mínimo, MXN por presentación comercial. |
| `precio_min_min` | decimal | Mínimo observado en el mes, MXN por presentación comercial. |
| `precio_min_max` | decimal | Máximo observado en el mes, MXN por presentación comercial. |
| `precio_min_std` | decimal/nulo | Desviación estándar poblacional de cotizaciones de precio mínimo, MXN; nula si no se puede estimar. |
| `precio_min_count` | entero | Número de cotizaciones de precio mínimo incluidas. |
| `precio_max_mean` | decimal | Media mensual de precio máximo, MXN por presentación comercial. |
| `precio_max_median` | decimal | Mediana mensual de precio máximo, MXN por presentación comercial. |
| `precio_max_min` | decimal | Mínimo observado en el mes, MXN por presentación comercial. |
| `precio_max_max` | decimal | Máximo observado en el mes, MXN por presentación comercial. |
| `precio_max_std` | decimal/nulo | Desviación estándar poblacional de cotizaciones de precio máximo, MXN. |
| `precio_max_count` | entero | Número de cotizaciones de precio máximo incluidas. |
| `precio_frecuente_mean` | decimal | Media mensual del precio frecuente, MXN por presentación comercial. |
| `precio_frecuente_median` | decimal | Mediana mensual del precio frecuente, MXN por presentación comercial. |
| `precio_frecuente_min` | decimal | Mínimo mensual del precio frecuente, MXN por presentación comercial. |
| `precio_frecuente_max` | decimal | Máximo mensual del precio frecuente, MXN por presentación comercial. |
| `precio_frecuente_std` | decimal/nulo | Desviación estándar poblacional del precio frecuente, MXN. |
| `precio_frecuente_count` | entero | Número de cotizaciones de precio frecuente incluidas. |
| `linaje_precios_bronce` | JSON en texto | Lista de fuentes Bronce que alimentaron el agregado: archivo, SHA-256, ingesta UTC e índice original. |
| `n_observaciones_precio` | entero | Número de observaciones diarias/precios usadas para la fila. |
| `estacion` | texto/nulo | Identificador NOAA de estación; nulo si el mes no tiene registros climáticos asociados. |
| `tavg_c_mean` | decimal/nulo | Media mensual de temperaturas medias diarias observadas, °C. |
| `tavg_c_min` | decimal/nulo | Mínimo de las medias diarias observadas del mes, °C. |
| `tavg_c_max` | decimal/nulo | Máximo de las medias diarias observadas del mes, °C. |
| `tavg_c_count` | decimal/nulo | Número de días con temperatura media disponible. |
| `tmax_c_mean` | decimal/nulo | Media mensual de máximas diarias observadas, °C. |
| `tmax_c_min` | decimal/nulo | Mínimo de las máximas diarias disponibles en el mes, °C. |
| `tmax_c_max` | decimal/nulo | Máximo de las máximas diarias disponibles en el mes, °C. |
| `tmax_c_count` | decimal/nulo | Número de días con máxima disponible. |
| `tmin_c_mean` | decimal/nulo | Media mensual de mínimas diarias observadas, °C. |
| `tmin_c_min` | decimal/nulo | Mínimo de las mínimas diarias disponibles en el mes, °C. |
| `tmin_c_max` | decimal/nulo | Máximo de las mínimas diarias disponibles en el mes, °C. |
| `tmin_c_count` | decimal/nulo | Número de días con mínima disponible. |
| `prcp_mm_mean` | decimal/nulo | Media de precipitación diaria disponible del mes, mm/día; no es acumulado mensual. |
| `prcp_mm_min` | decimal/nulo | Mínimo diario de precipitación disponible, mm. |
| `prcp_mm_max` | decimal/nulo | Máximo diario de precipitación disponible, mm. |
| `prcp_mm_count` | decimal/nulo | Número de días con precipitación registrada. |
| `linaje_clima_bronce` | JSON en texto/nulo | Referencias de registros NOAA Bronce (archivo, SHA-256, ingesta UTC e índice); nulo cuando no se asocia clima. |
| `dias_clima_observados` | decimal/nulo | Días del mes con al menos una variable climática observada. |
| `fecha_mes` | fecha ISO | Primer día del mes agregado (`AAAA-MM-01`), índice temporal. |

Los conteos climáticos aparecen como decimales en la lectura CSV por la unión con meses sin observaciones; semánticamente son conteos enteros cuando no son nulos. Los precios conservan la presentación reportada: **no convertir a precio por kg** sin peso verificable.

## D. Recolección

SNIIM se consulta mediante su formulario público de precios mayoristas; NOAA NCEI se consulta mediante GHCN-Daily para la estación configurada. La descarga histórica captura meses/consultas disponibles y la actualización diaria se orquesta con GitHub Actions. El código y configuración viven en `extractores/`, `config/`, `pipeline/` y `src/tdl_e1/`. Cada archivo de origen se conserva sin modificar en Bronce, con sidecar, SHA-256, fecha UTC de captura y manifiesto. Los extractores revisan `robots.txt`, usan User-Agent identificable y pausa/reintentos. SNIIM declara los precios como información pública referencial y deja su uso bajo responsabilidad de quien la utiliza; NOAA se atribuye a NCEI. Véase [`docs/etica-datos.md`](../etica-datos.md).

## E. Preprocesamiento

1. Se comprueba el hash del archivo Bronce contra su sidecar antes de interpretar su contenido.
2. SNIIM y NOAA se normalizan a esquema común, fechas ISO y tipos numéricos; el esquema estricto y reglas de rango se validan con Pandera.
3. Las filas inválidas se escriben en cuarentena con archivo, hash, motivo y representación del registro original; no se descartan silenciosamente.
4. Duplicados se resuelven por captura más reciente, preservando referencias de todas las versiones. La publicación no tiene claves mensuales repetidas.
5. Se agregan estadísticos mensuales (media, mediana, extremos, desviación y conteos) a nivel cultivo × variante × mercado × origen × presentación. El resumen meteorológico es por estación × mes.
6. Precios y precipitación no se imputan. La interpolación de temperatura existe en una salida de Plata separada para modelado; no altera este panel mensual Oro ni los datos originales.
7. Se conservan los campos de linaje JSON. `data/plata/reporte_calidad.json` documenta validaciones, faltantes, cuarentena y agregación.

## F. Calidad y limitaciones

- El pipeline verifica hashes de Bronce; el validador de linaje de Oro exige ruta, hash, timestamp e índice. La comparación E3 verificó 15,147 registros procesados, cero cuarentenas y salidas CSV idénticas entre versiones.
- SNIIM refleja cotizaciones informadas, no todas las transacciones ni el precio recibido en parcela. Los precios son referenciales y la cobertura cambia por producto, presentación y mercado.
- Presentaciones heterogéneas no son comparables como unidad física común. No asumir MXN/kg salvo que la presentación y su peso lo justifiquen.
- Una estación NOAA en Manzanillo no representa condiciones de cada huerta ni todo Colima. No inferir causalidad precio-clima a partir de la coincidencia mensual.
- Los conteos y medias climáticas dependen de la disponibilidad diaria. Ausencia no equivale a precipitación cero o clima normal.
- El historial y las definiciones de proveedores pueden cambiar; los agregados pueden revisarse al regenerar desde nuevas capturas.
- No se recomienda usar el panel como cotización en tiempo real, valuación individual, asesoría de inversión, predicción garantizada o estimación del ingreso de productores.

## G. Usos recomendados

- Exploración de tendencia mensual por cultivo, presentación, origen y plaza.
- Ejercicios académicos de series temporales con validación temporal explícita.
- Comparaciones descriptivas entre mercados cuando coinciden cultivo, variante, presentación y periodo.
- Reproducción del proceso Medallion y auditoría de la procedencia mediante los campos de linaje.

## H. Usos no recomendados

- Sustituir cotizaciones vigentes, fijar precios de compra/venta o inferir precios en parcela.
- Comparar valores sin controlar presentación, calidad, origen, mercado y periodo.
- Atribuir cambios de precio al clima como relación causal.
- Extrapolar la única estación meteorológica a todas las localidades productoras.
- Inferir datos personales o características de productores; no existen tales variables en el dataset.

## I. Mantenimiento

El equipo OAIC mantiene el pipeline. La captura diaria se programa en `.github/workflows/captura_diaria.yml`; el dataset público de esta versión se regenera desde Plata/Oro y se versiona con Git. La revisión de esta ficha corresponde al 2026-11-20. Para reportar defectos, abrir un issue en [el repositorio](https://github.com/sebastianGS-z/PROYECTO/issues) indicando versión, campo y reproducción, sin adjuntar información personal. Cambios de esquema requieren una nueva versión del dataset y actualización del diccionario.

## J. Reproducibilidad

Desde la raíz del repositorio, con Python 3.11 o posterior:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py capas
cp data/oro/panel_mensual.csv data/publico/panel_mensual_e3.csv
```

El paso de captura actualizado es `python main.py e2`; requiere acceso de red y aplica las reglas éticas configuradas. `python main.py capas` regenera las capas usando los archivos Bronce existentes. Repositorio/código: [sebastianGS-z/PROYECTO](https://github.com/sebastianGS-z/PROYECTO). La versión curada publicada está disponible directamente en el enlace de archivo al inicio de esta ficha.
