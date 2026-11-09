# Propuesta del Observatorio de Agro-Inteligencia Colimense (OAIC) · E0

Proyecto Integrador TRUSTED DATA LAB · Equipo: Grageda Sandoval Sebastián y Jose Negrete Orozco · Fecha: 2026-11-09
Roles: Sebastián: Data Engineer · José: Data Statistician · Quality Lead de E0: José (revisa el trabajo de Sebastián) · Repositorio: https://github.com/sebastianGS-z/PROYECTO

---

## 1. Ficha del Observatorio

* **Sector:** Agroindustrial y Comercio Mayorista de Frutas y Hortalizas (Fruit & Produce).
* **Región:** Estado de Colima (Tecomán, Armería, Manzanillo) en comparación con las principales Centrales de Abasto de cobertura nacional (Guadalajara y CDMX).
* **Pregunta Detonadora:** ¿En qué periodo del año se maximiza el precio de venta por kilogramo del plátano, limón y papaya, y qué mercado mayorista ofrece el mejor precio a los productores de Colima?
* **Cliente Potencial:** Empacadoras locales, asociaciones de productores agrícolas (ej. Consejo Limonero, uniones plataneras) y comerciantes mayoristas de la región.
* **Justificación de pago:** Los clientes pagarían por una suscripción a reportes y tableros inteligentes con pronóstico de precios a 30 días, lo que les permite anticipar ventanas de escasez por clima/enfermedades, negociar mejores tarifas frente a la intermediación y decidir hacia qué plaza geográfica enviar sus fletes.

---

---

## 2. Entrevista de campo

Se entrevistó a tres ingenieros agrónomos de los cultivos del observatorio: limón (entrevista principal, abajo), plátano y papaya (texto completo en [`entrevistas.md`](entrevistas.md)). Las tres duraron más de 15 minutos.

### A. Entrevista Principal: Sector Limón
* **Entrevistado:** Ing. Agrónomo (retirado), especialista en huertas limoneras de Tecomán.
* **Ubicación:** Municipio de Tecomán, Colima.
* **Duración de la sesión:** 18 minutos.

* **Fecha y medio (presencial / llamada):** 2026-11-09, llamada
* **Entrevistó:** Jose Negrete Orozco

#### Parte II: Diagnóstico de Mercado, Clima y Validación de Precios

1. **¿Cómo consulta o fija el precio por caja/kilo de limón cada mañana en Tecomán y qué tanto le imponen la tarifa los empaques o intermediarios locales?**
   * *Respuesta:* Se dice que el precio lo decide la oferta y demanda, y esta es reportada por los bodegueros y los empaques. Y el productor la consulta cada día por medio de su organización de productores “Consejo Limonero” pero en la práctica, alrededor de las 12 del día se hablan entre ellos y preguntan quién está pagando mejor. Bajo esta circunstancia, para cada productor en particular el precio lo pone el intermediario dependiendo del precio que le ponga el empaque, y este a la vez depende del lugar a donde lo mande y el precio que le dé el bodeguero. Se comenta que por semana se reúnen los bodegueros en cada centro de abastos de las diferentes ciudades y acuerdan cuánto pagar esa semana.

2. **¿Cómo afecta al margen de ganancia del productor local la diferencia de precios entre el mercado de Colima y las Centrales de Abasto de Guadalajara o la CDMX?**
   * *Respuesta:* Las centrales de abasto sí tienen influencia sobre el precio; hay mercados de abasto que se caracterizan por pagar un mejor precio, pero con mejor calidad.

3. **¿En qué meses del año la variación de temperatura o los brotes de plagas (como el HLB / Dragón Amarillo) desploman la producción e impactan fuertemente el precio?**
   * *Respuesta:* Las condiciones climáticas de la región influyen significativamente en la estacionalidad de la producción de limón mexicano. Durante los meses de noviembre a abril, la producción disminuye y representa entre el 10 y el 30 % del volumen producido en los periodos de mayor disponibilidad. La mayor reducción se relaciona principalmente con la incidencia de antracnosis y las limitaciones para su control. Por lo anterior, la menor oferta de limón mexicano durante este periodo debería reflejarse en un incremento de su precio en el mercado.

4. **¿Qué tipo de alertas meteorológicas o comparativas de mercado en tiempo real le servirían a un productor para decidir si cortar limón hoy o aguantar la fruta unos días en el árbol?**
   * *Respuesta:* Como tal un productor se basa para su corte en la medida del limón y no en alertas meteorológicas, entonces está difícil de decidir cuáles serían las mejores.

5. **Si existiera una plataforma digital que pronostique el precio del limón con 95% de confianza estadística para las próximas semanas, ¿considera que un empaque o asociación limonera pagaría una suscripción por ella?**
   * *Respuesta:* Si existiera una plataforma que te diera ese pronóstico con esa cantidad de confiabilidad yo sí consideraría un paquete o algo para poder checar los precios.

---

### Resumen de las otras dos entrevistas
* **Plátano** (consultor de parcelas, Valle de Tecomán, 17 min): el precio se fija semanalmente con un mínimo y un máximo tomando como referencia el precio al consumidor en tiendas grandes; julio y agosto obligan a vender rápido por la maduración; pagaría por la herramienta solo si participa toda la cadena.
* **Papaya** (ex-asesor de empacadora, Armería y Tecomán, 16 min): cerca de 80 % se exporta y el precio nacional sigue a la exportación; la lluvia y la humedad afectan la calidad; valora contar con el clima histórico junto con los precios.

1. **Complejidad de la cadena comercial en el limón:** Los bodegueros acuerdan precios semanalmente en los centros de abasto y la tarifa se cascada hacia el empaque y el intermediario ("coyote"), quien finalmente impone el costo de compra en huerta al productor local.
2. **Estacionalidad y enfermedad fitosanitaria (Noviembre a Abril):** En el limón, la producción cae al 10%-30% del volumen habitual en invierno debido a las bajas temperaturas y a la antracnosis, lo que genera escasez y empuja alzas de precio que el modelo predictivo (E1) debe capturar.
3. **Calidad y segmentación de mercados:** Las centrales de abasto influyen de manera diferenciada; mercados más exigentes pagan sobreprecio por calidades superiores.
4. **Factores climáticos por cultivo (datos de NOAA NCEI):** En papaya las lluvias generan 100% de susceptibilidad a hongos/bacterias; en plátano el calor de julio/agosto acelera la maduración; y en limón el frío e infecciones de antracnosis contraen la oferta en invierno.
5. **Viabilidad comercial y red de actores:** Existe interés genuino de suscripción si la herramienta estadística ofrece 95% de confiabilidad, destacando que en el plátano se requiere la participación conjunta de la cadena (productores, empacadores y comerciantes) para evitar sesgos de datos.

---

---

## 3. Las 3 preguntas analíticas

1. **Pronóstico de serie de tiempo (Análisis Estadístico, E1).**
   * *Variable a pronosticar:* precio frecuente mensual del limón (promedio de los precios frecuentes diarios del SNIIM, por presentación comercial; la conversión a kg se hace en la capa plata) en la Central de Abasto de Iztapalapa. La variante exacta se fija con el reporte de cobertura (todas tienen 36 meses con datos).
   * *Pregunta:* ¿Cuál será la tendencia, la estacionalidad y el precio pronosticado para los meses de menor oferta (noviembre a abril), comparando suavizamiento simple, Holt, Holt-Winters y ARIMA/SARIMA por MAE, RMSE y MAPE? Se replica después para plátano y papaya.

2. **Diseño de experimentos factorial 2³ (Análisis Estadístico, E2, ruta ingeniería).**
   * *Pregunta:* ¿Qué combinación de procesos paralelos (1 vs. 4), pausa entre peticiones (1 s vs. 3 s) y formato de escritura (Parquet vs. CSV) minimiza el tiempo de procesamiento y la tasa de errores del extractor? El experimento se corre contra una **copia local de las páginas de la capa bronce**, nunca contra el sitio real, para no violar la regla de no saturar sitios ajenos.

3. **Análisis multivariado PCA y MANOVA (Análisis Estadístico, E3).**
   * *Pregunta:* ¿Difieren los tres cultivos (plátano, limón y papaya) en conjunto (Λ de Wilks y traza de Pillai) en precio mínimo, máximo y frecuente, volatilidad del precio (desviación estándar mensual) y temperatura media y precipitación mensual de la estación de Manzanillo? Unidad de análisis: producto × mercado × mes (≥ 5 variables numéricas).

---

## 4. Plan de recopilación de datos y análisis ético y legal

### Fuente 1: SNIIM (Sistema Nacional de Información e Integración de Mercados)
* **Datos:** precios diarios mayoristas (mínimo, máximo y frecuente) de plátano, limón y papaya, con presentación, origen y destino. Se captura **todos los orígenes** en los destinos Guadalajara (Mercado de Abasto) y CDMX (Central de Abasto de Iztapalapa); el filtro al origen Colima se aplica en la capa plata. Los precios vienen por **presentación comercial** (caja, ciento, etc.), no por kilogramo.
* **Estructura y formato:** consulta web HTML (formulario → página de resultados con tabla). Si no hay datos, la página dice "NO HAY REGISTROS".
* **Frecuencia:** el sitio publica de lunes a viernes; capturamos diario (GitHub Actions, 03:00 UTC = 21:00 en Colima).
* **Método:** scraping ético en Python (`requests` + `BeautifulSoup`); no hay API oficial.
* **Análisis ético y legal:** sitio público de la Secretaría de Economía que describe su información como disponible de forma gratuita al público. `robots.txt` consultado el 2026-11-09 (contenido en el Anexo): no prohíbe la ruta de consulta; el extractor lo verifica en cada ejecución y no hace scraping si no puede leerlo. Usa un User-Agent identificable con contacto del equipo, una pausa mínima de 1.5 s por dominio (y respeta `Crawl-delay` si existe) y reintentos con espera exponencial. Términos de uso: el sitio (https://www.economia-sniim.gob.mx) es público y gratuito; no se revisó un aviso legal específico antes de la entrega E0 y queda pendiente verificarlo en E1. Sin datos personales.

### Fuente 2: NOAA NCEI (GHCN-Daily, Access Data Service)
* **Datos:** temperatura media (TAVG), máxima (TMAX), mínima (TMIN) y precipitación (PRCP) diarias de la estación de **Manzanillo, Colima** (`MXM00076654`), la más cercana a las zonas productoras que se identificó (no es Tecomán). No se captura humedad relativa.
* **Estructura y formato:** JSON, lista de registros por día; los días o variables sin dato no aparecen y no se rellenan.
* **Frecuencia:** diaria; la estación ha tenido meses sin reporte (ver §5).
* **Método:** API pública sin llave (`https://www.ncei.noaa.gov/access/services/data/v1`).
* **Análisis ético y legal:** `robots.txt` consultado el 2026-11-09 (Anexo): prohíbe `/data*` y `/orders*` y algunas rutas de `/access/crn/`; la ruta usada (`/access/services/data/v1`) no aparece prohibida. Términos de uso y atribución: datos públicos de NOAA (https://www.ncei.noaa.gov); no se revisó una política de datos específica antes de la entrega E0 y queda pendiente verificarla y citar la fuente en E1. Sin datos personales.
* **Fuentes climáticas descartadas por `robots.txt`** (consultados el 2026-11-09): **Open-Meteo** (`Disallow: /` para todos los agentes) y **NASA POWER** (`Disallow: /api/`, donde está su API). En ambos casos el extractor se detuvo sin pedir datos, siguiendo la regla "si un sitio lo prohíbe, se busca otra fuente".

---

## 5. Máquina de captura (estado a la entrega)

* **Capa bronce:** cada captura guarda el contenido original sin modificar y un archivo `.meta.json` con fuente, URL, fecha, identificador de ejecución, formato y SHA-256; no se sobrescribe nada. Validación: `python main.py validar`.
* **Serie histórica SNIIM:** run `20261109T001830Z-2191be` (1,368 consultas, 69 min, exitosa): **36 de 36 meses con datos reales** para cada producto y mercado. Hubo 8 errores transitorios del servidor que se reintentaron solos. Evidencia: `data/bronce/sniim/manifests/cobertura_20261109T001830Z-2191be.csv`.
* **Clima NOAA NCEI:** run `20261109T100414Z-44eb79`: **28 de 36 meses con datos** (791 días); sin datos de dic-2025 a mar-2026 y de jul a oct-2026 porque la estación no reportó. No se rellenaron; se tratarán como valores faltantes en E1.
* **Captura automática:** workflow `captura_diaria.yml` de GitHub Actions ejecutado en verde el 2026-11-09 (captura del domingo 8, `sin_resultados` porque el SNIIM no publica ese día). Captura del viernes 2026-11-06 con SNIIM exitosa y 19 registros reales.
* **Bitácora de ejecuciones:** `calidad/bitacora_capturas.csv`.

---

## 6. Objetivos de calidad medibles (definidos en `calidad/objetivos_calidad.json`)

| ID | Objetivo | Fórmula | Meta |
|---|---|---|---|
| OQ1 | Disponibilidad de la captura | (ejecuciones exitosas o sin resultados) / ejecuciones diarias totales × 100 | ≥ 95 % |
| OQ2 | Continuidad: fallos sin detectar o sin registrar | días programados sin manifiesto + ejecuciones no exitosas sin error documentado | 0 |
| OQ3 | Cobertura de capturas diarias | días con manifiesto / días programados × 100 | 100 % |

Son metas, no resultados: se evalúan con `python main.py objetivos` sobre los manifiestos reales (los 7 días de bitácora para E1 se completan con el workflow diario). Objetivos adicionales que se formalizarán en el plan SQA de E1: **integridad** (100 % de los archivos con metadatos y SHA-256 válidos, verificable con `python main.py validar`) y **cero secretos expuestos** en el repositorio (escaneo con `gitleaks`).

---

## 7. Sistema de calidad inicial (PSP)

Registros individuales de tiempo y de defectos por integrante en `calidad/` (`tiempo-<nombre>.csv`, `defectos-<nombre>.csv`), con los diez tipos de defecto de PSP y las fases del Kit. Tiempo neto = fin − inicio − interrupciones. Archivos de José: `calidad/tiempo-jose.csv` y `calidad/defectos-jose.csv`.

## 8. Uso de IA generativa
Se usó Claude (Anthropic) para generar el código base del extractor, el almacenamiento, el sistema PSP, las pruebas y borradores de documentación; las entrevistas y su análisis son del equipo. Los integrantes revisaron el código y deben poder explicar cualquier parte. Sebastián ejecutó, probó y validó los extractores, la capa bronce, el workflow y la captura histórica. José realizó las entrevistas y revisó el código del extractor.

## Anexo: robots.txt consultados (2026-11-09)

### https://www.economia-sniim.gob.mx/robots.txt
```
User-agent: *
Disallow: /Analisis/
Disallow: /*.xls$
Disallow: /2010/
Disallow: /Sicia/
Disallow: /Sicia2/
Disallow: /SiciaAnt/
Disallow: /Sicia
Disallow: Sicia
# Allow: /

```

### https://www.ncei.noaa.gov/robots.txt
```
User-agent: *
Disallow: /data*
Disallow: /orders*

Allow: /data/oceans/coris/library*

#CRN
Disallow: /access/crn/*?
Disallow: /access/crn/ws/
Disallow: /access/crn/flex/
Disallow: /access/crn/error/
Disallow: /access/crn/new*
Disallow: /access/crn/xml*
```

### https://api.open-meteo.com/robots.txt
```
User-agent: *
Disallow: /```

### https://power.larc.nasa.gov/robots.txt
```
User-agent: *
Allow: /api/pages/
Disallow: /api/
Disallow: /beta/
Disallow: /classic/
Disallow: /healthz.html
Disallow: /common/
Disallow: /article/assets/
Disallow: /_next/
Disallow: /*.map$

# AI crawlers — block training data scraping
User-agent: GPTBot
Disallow: /

User-agent: ChatGPT-User
Disallow: /

User-agent: anthropic-ai
Disallow: /

User-agent: Claude-Web
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: Google-Extended
Disallow: /

Sitemap: https://power.larc.nasa.gov/sitemap.xml```
