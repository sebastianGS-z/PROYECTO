# Propuesta del Observatorio · E0

**Observatorio de Agro-Inteligencia Colimense (OAIC)** · Proyecto Integrador TRUSTED DATA LAB
Equipo: ⚠️ COMPLETAR (integrante 1 — Data Engineer · integrante 2 — Data Statistician) · Fecha: ⚠️ COMPLETAR

> **Cómo usar este documento.** Todo lo marcado con ⚠️ COMPLETAR requiere información real del equipo (sobre todo la entrevista). No se debe entregar con esas marcas ni con datos inventados.

---

## 1. Ficha del observatorio

| Campo | Contenido |
|---|---|
| **Sector** | Agroindustria y comercialización mayorista de frutas (limón, plátano y papaya). |
| **Región** | Colima: zonas productoras de Tecomán y Armería. Mercados de destino observados: Mercado de Abasto de Guadalajara y Central de Abasto de Iztapalapa (Ciudad de México). |
| **Pregunta detonadora (borrador, confirmar con la entrevista)** | ¿En qué meses y bajo qué condiciones de clima conviene vender limón, plátano y papaya de Colima en Guadalajara y la Ciudad de México, y cuánto cambia su precio mayorista de un mes a otro? |
| **Cliente potencial** | Productores, empacadores y comercializadores de Tecomán y Armería, y asociaciones de productores de la región. Contacto real: ⚠️ COMPLETAR (nombre, rol, organización). |
| **Por qué pagarían** | Decidir cuándo cosechar, empacar y enviar con un pronóstico del precio mensual y su incertidumbre, en lugar de hacerlo por rumores o por el precio del día anterior. |

Los datos públicos del precio mayorista existen en el SNIIM pero están dispersos en consultas manuales por producto y mercado; el observatorio los reúne, los certifica y los cruza con el clima local.

## 2. Entrevista de campo (mínimo 15 minutos)

⚠️ **Sección pendiente: debe hacerse con una persona real del sector. No se puede inventar ni redactar por otra persona.** Es el punto con más peso de la rúbrica de E0 junto con las preguntas analíticas (20 puntos cada uno).

| Dato | Valor |
|---|---|
| Entrevistado/a (nombre, rol, organización) | ⚠️ COMPLETAR |
| Fecha, medio y duración (≥ 15 min) | ⚠️ COMPLETAR |
| Entrevistó | ⚠️ COMPLETAR |

Cinco preguntas sugeridas (el equipo puede cambiarlas, pero deben ser 5 y registrar la respuesta real):

| # | Pregunta | Respuesta (resumen fiel) | Aprendizaje para el observatorio |
|---|---|---|---|
| 1 | ¿Cómo decide hoy cuándo cosechar y vender, y qué precios de referencia consulta? | ⚠️ COMPLETAR | ⚠️ COMPLETAR |
| 2 | ¿A qué mercados vende y cuál le importa más (Guadalajara, Ciudad de México, otro)? | ⚠️ COMPLETAR | ⚠️ COMPLETAR |
| 3 | ¿Cuánto influyen la lluvia y la temperatura en su volumen y calidad, y con cuánto desfase? | ⚠️ COMPLETAR | ⚠️ COMPLETAR |
| 4 | ¿Qué decisión cambiaría si supiera el precio esperado del próximo mes? ¿Cuánto vale eso para usted? | ⚠️ COMPLETAR | ⚠️ COMPLETAR |
| 5 | ¿En qué formato le serviría la información (reporte, mensaje, tablero) y cuánto pagaría por ella? | ⚠️ COMPLETAR | ⚠️ COMPLETAR |

Conclusión de la entrevista y ajustes a la pregunta detonadora: ⚠️ COMPLETAR.

## 3. Las tres preguntas analíticas (borradores)

| Entrega | Pregunta medible | Técnica |
|---|---|---|
| **E1 · Variable a pronosticar** | ¿Cuál será el precio frecuente mensual (promedio de los precios frecuentes diarios, en pesos por kilogramo) del limón con semilla en la Central de Abasto de Iztapalapa en los próximos 6 meses? La variante y el mercado definitivos se fijan con el reporte de cobertura de la serie histórica: se elige la serie con más periodos reales. | Suavizamiento simple, Holt, Holt-Winters y ARIMA/SARIMA, elegido por MAE, RMSE y MAPE en datos de prueba. |
| **E2 · Factores a experimentar** | Ruta ingeniería (propuesta; se confirma en E1): ¿qué combinación de número de procesos (1 vs. 4), parser (`html.parser` vs. `lxml`) y formato de escritura (CSV vs. Parquet) minimiza el tiempo de procesamiento y la tasa de error del extractor? Se ejecuta contra una copia local de las páginas de la capa bronce, sin saturar sitios ajenos. | Diseño factorial 2³ con aleatorización, réplicas y ANOVA. |
| **E3 · Grupos multivariados** | ¿Los tres productos (plátano, limón y papaya) tienen perfiles distintos en conjunto? Unidad de análisis: producto × mercado × mes. Variables numéricas (≥ 5): precio mínimo, máximo y frecuente, amplitud de precio, temperatura media, máxima, mínima y precipitación acumulada del mes. | PCA y MANOVA (Wilks y Pillai). |

## 4. Plan de recopilación de datos

| | **Fuente 1: SNIIM (Secretaría de Economía)** | **Fuente 2: NOAA NCEI (GHCN-Daily)** |
|---|---|---|
| **Qué aporta** | Precios mayoristas mínimo, máximo y frecuente de frutas y hortalizas en centrales de abasto, con presentación, origen y destino. | Clima diario de estación real: temperatura media (TAVG), máxima (TMAX), mínima (TMIN) y precipitación (PRCP). Estación: Manzanillo, Colima (GHCN `MXM00076654`), la más cercana a las zonas productoras que se identificó; **no es Tecomán**. |
| **Acceso** | Scraping de la consulta pública por HTTP GET (formulario → página de resultados). No hay API oficial. | API pública sin llave: `https://www.ncei.noaa.gov/access/services/data/v1` (dataset `daily-summaries`, formato JSON, `units=metric`). |
| **Estructura y formato** | HTML. Formulario con listas de producto, origen, mercado de destino y tipo de precio; resultados en tabla (producto, calidad, presentación, origen, destino, precio mín./máx./frec., observaciones). Si no hay datos, la página dice "NO HAY REGISTROS". | JSON: lista de registros por día (`DATE`, `STATION`, `TAVG`, `TMAX`, `TMIN`, `PRCP`). Los días o variables sin dato no aparecen y no se rellenan. |
| **Frecuencia de actualización** | Días hábiles, de lunes a viernes. | Diaria, con retraso variable. |
| **Nuestra frecuencia de captura** | Diaria (GitHub Actions, 03:00 UTC = 21:00 en Colima) + serie histórica de 36 meses. | Igual. |
| **Términos de uso** | El propio sitio describe la información como disponible de manera gratuita al público. ⚠️ COMPLETAR: enlace y fecha de lectura del aviso legal/términos del SNIIM. | ⚠️ COMPLETAR: enlace y fecha de lectura de la política de uso/licencia de datos de NOAA NCEI; citar la fuente en el tablero. |
| **robots.txt** | ⚠️ COMPLETAR: pegar el contenido y la fecha de consulta de `https://www.economia-sniim.gob.mx/robots.txt` y concluir qué rutas están permitidas. El extractor lo consulta antes de cada ejecución. | Consultado el 2026-11-09 (`https://www.ncei.noaa.gov/robots.txt`): prohíbe `/data*` y `/orders*` y algunas rutas de `/access/crn/`; la ruta usada (`/access/services/data/v1`) no aparece prohibida. ⚠️ COMPLETAR: pegar el archivo completo. El extractor lo vuelve a verificar en cada ejecución. |
| **Datos personales** | Ninguno (precios de productos agrícolas). | Ninguno (variables meteorológicas). |
| **Limitaciones conocidas** | Sin API; el HTML puede cambiar (un cambio de estructura se registra como captura fallida, no como dato). Tecomán y Armería no son mercados del SNIIM. | Una sola estación (Manzanillo), a unos 50–60 km de Tecomán: es una aproximación al clima de la región. Puede tener días o variables faltantes. |

**Fuentes climáticas descartadas por robots.txt** (consultados el 2026-11-09): **Open-Meteo** (`api.open-meteo.com` y `archive-api.open-meteo.com` devolvieron `User-agent: *` y `Disallow: /`) y **NASA POWER** (`power.larc.nasa.gov` prohíbe `/api/`, donde vive su API de datos). En ambos casos el extractor se detuvo sin pedir datos. Siguiendo la regla del proyecto ("si un sitio lo prohíbe, se busca otra fuente"), se eligió NOAA NCEI.

**Medidas éticas del extractor** (`extractores/base.py`): User-Agent identificable, lectura obligatoria de robots.txt con política conservadora, respeto de Crawl-delay, pausa mínima de 1.5 s por dominio compartida entre extractores, reintentos con espera exponencial, sin proxies ni evasión de protecciones.

## 5. Máquina de captura (estado)

* Capa bronce: cada captura guarda el contenido original sin modificar más un archivo `.meta.json` con fuente, URL, fecha, identificador de ejecución, formato y SHA-256; los archivos nunca se sobrescriben y se organizan por fuente/año/mes.
* Automatización: `.github/workflows/captura_diaria.yml` (diaria y manual) y `captura_historica.yml` (manual).
* Evidencia de ejecuciones: manifiesto por ejecución y `calidad/bitacora_capturas.csv`.
* Serie histórica: ⚠️ COMPLETAR con el resultado real: periodos con datos por producto y mercado según `data/bronce/sniim/manifests/cobertura_<run_id>.csv` (meta: ≥ 36). Si no se alcanza, declarar los periodos faltantes y la causa.

## 6. Objetivos de calidad medibles

Definidos en `calidad/objetivos_calidad.json`:

| ID | Objetivo | Meta |
|---|---|---|
| OQ1 | Disponibilidad de captura = (ejecuciones exitosas o sin resultados) / ejecuciones diarias totales | ≥ 95 % |
| OQ2 | Fallos no detectados o no registrados (días sin manifiesto + ejecuciones no exitosas sin error documentado) | 0 |
| OQ3 | Cobertura de capturas diarias = días con manifiesto / días programados | 100 % |

Son metas, no resultados: se evalúan con `python main.py objetivos` sobre los manifiestos reales.

## 7. Sistema de calidad inicial (PSP)

Registros individuales abiertos en `calidad/` (tiempo y defectos por integrante) con los diez tipos de defecto de PSP y las fases del Kit. Tiempo neto = fin − inicio − interrupciones. ⚠️ COMPLETAR: número de registros de tiempo y de defectos de cada integrante al momento de la entrega.

## 8. Roles, cronograma y uso de IA generativa

* Data Engineer: ⚠️ COMPLETAR · Data Statistician: ⚠️ COMPLETAR · Quality Lead de E0 (revisa el trabajo del otro): ⚠️ COMPLETAR.
* Siguientes pasos: E1 (13-nov) limpieza, puerta de calidad y pronóstico; E2 (23-nov) experimento y fuente especializada; E3 (30-nov) PCA/MANOVA y Sello TDL.
* **Uso de IA generativa:** se usó Claude (Anthropic) para generar el código base del extractor, el almacenamiento, el sistema PSP, las pruebas y borradores de documentación. El equipo revisó el código y debe poder explicar cualquier parte en la defensa. ⚠️ COMPLETAR: qué revisó y modificó cada integrante.
