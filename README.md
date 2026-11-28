# TRUSTED DATA LAB (TDL) — Observatorio de Agro-Inteligencia Colimense (OAIC)

Proyecto **OAIC · E0–E4** · Captura, capas Medallion, analítica reproducible y tablero local.

## 1. Descripción
Sistema modular en Python que captura datos crudos de dos fuentes públicas y los guarda sin alterarlos, con trazabilidad e integridad (SHA-256):

* **SNIIM** (Secretaría de Economía): precios mayoristas de plátano, limón y papaya, más frutas regionales como mango, coco, tamarindo, guayaba, guanábana y sandía, consultados en Colima, Guadalajara, Ciudad de México y Morelia. La cobertura depende del producto, variante, origen y mercado; las nuevas combinaciones no implican historia larga.
* **NOAA NCEI** (GHCN-Daily, Access Data Service): temperatura media/máx/mín y precipitación de la estación de **Manzanillo, Colima**. No representa las huertas de Tecomán/Armería ni las plazas de Guadalajara/CDMX.

## 2. Objetivo
Alimentar la Capa Bronce de una arquitectura Medallion. **No** limpia, deduplica, imputa ni transforma: eso corresponde a capas posteriores.

## 3. Arquitectura
```
config → extractores (HTTP ético + parseo) → pipeline → almacenamiento (Bronce + manifiesto) → validación
                                                          └→ calidad (PSP, objetivos)
```
| Capa | Módulo | Responsabilidad |
|---|---|---|
| Configuración | `config/settings.py`, `localidades.json`, `fuentes.json` | UA, timeout, reintentos, pausa, rutas, coordenadas, fuentes |
| Transporte HTTP | `extractores/base.py` | robots.txt (fallo cerrado), Crawl-delay, pausa ≥1.5 s por dominio compartida entre instancias, reintentos con backoff, validación |
| Extracción | `sniim_extractor.py`, `weather_extractor.py` | Todo el conocimiento del HTML/JSON de cada fuente |
| Almacenamiento | `almacenamiento/bronze_writer.py` | Original intacto + sidecar `.meta.json`, creación exclusiva (inmutable) |
| Registro | `almacenamiento/manifest.py` | Manifiesto por ejecución y fuente con estado final |
| Integridad | `scripts/validar_bronce.py` | Recalcula SHA-256 y verifica manifiestos |
| Calidad PSP | `calidad/psp.py` | Tiempo neto, defectos, 10 tipos PSP, objetivos OQ1–OQ3 |

Estados de ejecución: `exitosa`, `parcial`, `sin_resultados`, `fallida`. Una fuente que falla **nunca** queda como exitosa. Códigos de salida: `0` exitosa/sin_resultados · `1` fallida · `2` parcial.

## 4. Estructura
```
tdl-equipo-agrocolima/
├── extractores/  almacenamiento/  calidad/  scripts/  config/  tests/  pipeline/   (estructura del Kit)
├── docs/E0/{propuesta,ENTREGA}.md   laboratorio/  tablero/  data/{bronce,plata,oro,cuarentena}/
├── data/bronce/{sniim,noaa_ncei}/<AAAA>/<MM>/…   y   …/manifests/
├── logs/   .github/workflows/captura_diaria.yml
├── pipeline/ (orquestación)   main.py (CLI)   requirements.txt   pytest.ini
```
Archivo Bronce: `data/bronce/<fuente>/<año>/<mes>/<fuente>__<etiqueta>__<ini>_<fin>__<run_id>.<html|json>` + `.meta.json`.

## 5–7. Instalación
Requisitos: Python 3.11+.
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
El pipeline E1 usa pandas, NumPy y Pandera para transformar Bronce y validar Plata.

## 8. Configuración
`cp .env.example .env` y ajusta. Parámetros: `TDL_USER_AGENT`, `TDL_TIMEOUT`, `TDL_MAX_RETRIES`, `TDL_BACKOFF_BASE`, `TDL_MIN_DELAY` (1.5 s), `TDL_DATA_DIR`, `TDL_LOG_LEVEL`, URLs de las fuentes. **Cambia el correo de contacto del User-Agent por el real del equipo.**
Coordenadas y mercados: `config/localidades.json` (aproximadas; verifíquenlas) y `config/fuentes.json`.

## 9. Captura diaria
```bash
python main.py diaria                       # ayer (hora de Colima), ambas fuentes
python main.py diaria --fecha 2026-11-06 --solo clima
```
NOAA NCEI puede tardar en publicar los días más recientes; los días sin dato no aparecen y no se rellenan.

## 10. Captura histórica (36 meses)
```bash
python main.py historica --dry-run                      # plan sin red
python main.py historica                                # últimos 36 meses completos
python main.py historica --productos platano --mercados cdmx --max-consultas 5   # prueba pequeña
python main.py historica --incluir-mercados-opcionales  # añade Colima y Felipe Ángeles
```
Genera `data/bronce/sniim/manifests/cobertura_<run_id>.{json,csv}`: un periodo (mes) cuenta **solo** si la fuente devolvió registros reales. Los meses sin datos o fallidos se listan; la existencia de 36 archivos no equivale a 36 periodos.
Datos sintéticos (solo pruebas): `python scripts/generar_sinteticos.py` → `data/sintetico/SINTETICO_*.csv`, nunca en `data/bronce`.

## Sitio público y vistas

Sitio: **<https://sebastiangs-z.github.io/PROYECTO/>** (se publica con GitHub Pages después de cada captura diaria).

| Vista | Para quién | Qué muestra |
|---|---|---|
| [`tablero/inicio.html`](tablero/inicio.html) | Cliente | Precio, pronóstico con rango y confianza por producto; hallazgos; accesos |
| [`tablero/preguntas.html`](tablero/preguntas.html) | Productor | 14 preguntas para cada una de las 10 frutas, con índice de confianza (0–100 %), qué hacer y calculadora de precio justo |
| [`tablero/mapa.html`](tablero/mapa.html) | Productor / comprador | Producción municipal por cultivo y año (SIAP 2016–2025), centrales con diferencia de precio comprobada frente a la referencia, y países que compran cada fruta a México |
| [`tablero/inteligencia.html`](tablero/inteligencia.html) | Cliente | Reporte imprimible: pronóstico, plazas, margen del productor, calendario, señales |
| [`tablero/cliente.html`](tablero/cliente.html) | Comprador | Comparación de plazas, simulador de margen y flete, mapa SIAP, comercio exterior |
| [`tablero/index.html`](tablero/index.html) | Analista | Serie, pronóstico con banda de 80 %, evaluación de modelos, calidad y linaje |
| [`tablero/laboratorio.html`](tablero/laboratorio.html) | Docentes / analista | Resultados de E1–E3 |
| [`tablero/admin.html`](tablero/admin.html) | Operador | Alertas, disponibilidad, estado por fuente, puerta de calidad, ISO/IEC 25012, salud de pronósticos, inventario de Bronce |

**Índice de confianza (0–100 %).** Pronósticos: 50 % precisión en meses no vistos (1 − MAPE/40), 30 % acierto del rango de 80 %, 20 % historia (meses/120). Comparaciones con prueba estadística: 60 % (1 − p) + 40 % datos (n/objetivo), con tope de 60 % si p ≥ 0.05 y de 40 % si p ≥ 0.20. Datos oficiales observados: según cobertura. ≥ 75 alta, 50–74 media, < 50 baja. Implementación: `src/inteligencia/comercial.py::confianza_pct` y `src/inteligencia/preguntas.py`.

**Catálogo de frutas.** `src/inteligencia/catalogo.py` es la fuente única: limón, papaya, plátano, mango, coco, tamarindo, guayaba, aguacate, sandía y guanábana, con su nombre en SIAP y su código HS. Cobertura de 10 años por fruta: `data/publico/cobertura_frutas.csv` y el panel de administración.

**Mercados extranjeros.** `python main.py comtrade-captura` (UN Comtrade 2019–2024: importaciones desde México, importaciones mundiales y exportadores, con pausa de 6 s por la cuota del API) y `python main.py exportacion` (destinos, crecimiento, oportunidades y prima de exportación en MXN/kg con tipo de cambio del BCE).

**Precios reales e historial de aciertos.** `python main.py inflacion-captura` guarda en Bronce el índice de precios al consumidor de México (Banco Mundial, FP.CPI.TOTL) para expresar precios e ingresos de años anteriores en pesos de hoy. `python main.py aciertos` publica qué tanto ha acertado el pronóstico (rango de 80 %, dirección y error, fuera de muestra) y agrega cada pronóstico emitido a `data/publico/historial_pronosticos.csv` para medir los aciertos reales mes a mes.

**Alertas.** `python main.py alertas` escribe `tablero/alertas.xml` (RSS 2.0) y `data/publico/alertas.json`: precio alto o bajo frente a su historia, pronóstico que se aleja del dato del mes, central que paga más con confianza alta, prima de exportación ≥ 20 % y fuentes sin datos nuevos. Cualquier lector de RSS o servicio de "RSS a correo" avisa sin que el observatorio guarde datos personales.

Regenerar todo desde Bronce: `python main.py capas && python main.py observatorio && python -m calidad.metricas && python main.py exportacion && python main.py aciertos && python main.py inteligencia && python main.py reporte && python main.py preguntas && python main.py alertas && python main.py mapa && python main.py portal`. Fuentes históricas adicionales: `python main.py siap-captura --anios 2016 ... 2025` (cierres agrícolas SIAP) y `python main.py historica --inicio 2016-11-01 ...` (SNIIM).

## Mapa de evidencias por materia

| Materia | Evidencia principal |
|---|---|
| Ingeniería de Datos | Pipeline Bronce → Plata → Oro (§12), geoespacial (§12.1), optimización y dataset (§12.3), [ética](docs/etica-datos.md), [datasheet](docs/E3/datasheet.md) |
| Análisis Estadístico | [Series de tiempo E1](docs/E1/laboratorio_series.md) · [Experimento factorial E2](docs/E2/experimento_factorial.md) · [PCA y MANOVA E3](docs/E3/multivariado.md) · código en `laboratorio/` (§12.4) |
| Calidad | [Plan SQA](docs/calidad/plan_sqa.md) · [Requerimientos](docs/calidad/requerimientos.md) · [Fiabilidad y seguridad](docs/calidad/fiabilidad_seguridad.md) · [ISO/IEC 25010](docs/calidad/iso25010.md) · [ISO/IEC 25012](docs/calidad/iso25012.md) · [Normas](docs/calidad/antecedentes_normativos.md) · [Auditoría](docs/calidad/auditoria/) · [Modelos de proceso](docs/calidad/modelos_proceso.md) · [Retrospectiva PSP](docs/calidad/retrospectiva_psp.md) · [Tendencias](docs/calidad/tendencias.md) · [Solicitud del Sello TDL](docs/calidad/sello_tdl.md) |

## 11. Validación de la Capa Bronce
```bash
python main.py validar            # SHA-256 de cada archivo + manifiestos
```

## 12. Pipeline E1: Bronce → Plata → Oro

```bash
python main.py capas
```

El pipeline lee únicamente capturas Bronce con sidecar y verifica su SHA-256 antes de parsear. Normaliza fechas y números de SNIIM y NOAA a un esquema común, valida tipos y rangos con Pandera y envía los registros inválidos a `data/cuarentena/registros_invalidos.csv` con archivo, hash, motivo y registro original. No modifica Bronce.

Salidas principales:

* `data/plata/precios_clima.csv`: registros validados, originales normalizados, atípicos señalados, versiones de análisis winsorizadas y variables Min-Max/Z-Score.
* `data/plata/clima_modelado.csv`: calendario diario de la estación con una copia de variables de temperatura interpoladas solo en huecos interiores de hasta dos días; conserva los valores observados y marca cada imputación. Precipitación y precios no se imputan.
* `data/plata/diagnostico_faltantes.json` y `reporte_calidad.json`: perfiles de faltantes, asociaciones descriptivas, decisiones de imputación y resumen de controles.
* `data/plata/conflictos_resueltos.csv`: claves repetidas con valores discrepantes; conserva en Plata la captura más reciente y mantiene todas las versiones originales en Bronce.
* `data/oro/panel_mensual.csv`: agregación mensual de precios por variante, plaza, origen y presentación, unida al resumen mensual de cada estación climática disponible. Cada fila lleva `linaje_precios_bronce` y `linaje_clima_bronce`: listas con ruta, SHA-256, fecha UTC de ingesta e índice del registro original. `data/plata/reporte_calidad.json` registra los conteos de la puerta de linaje.

Las capas Plata/Oro y la cuarentena se regeneran en cada ejecución. El workflow diario ejecuta `python main.py e2` para actualizar también la dimensión geoespacial; el workflow histórico usa `python main.py capas`. La publicación normal de `data/` conserva los resultados. Detalle E1: [docs/E1/ENTREGA.md](docs/E1/ENTREGA.md).

## 12.1 Integración geoespacial E2

```bash
python main.py e2                  # captura el Marco Geoestadístico de INEGI y regenera E1 + E2
python main.py e2 --solo-procesar  # usa el GeoJSON de INEGI ya guardado en Bronce
```

El proceso guarda la capa municipal de Colima en `data/bronce/inegi_marco/`, transforma atributos y geometría con GeoPandas en `data/plata/marco_geoestadistico_colima.csv`, publica la dimensión municipal en `data/oro/contexto_geoespacial_municipal.csv` y crea un mapa en `docs/E2/`. El reporte de proceso está en `data/plata/reporte_geoespacial_e2.json`. La dimensión geográfica permanece separada de los precios por mercado para evitar uniones entre unidades espaciales incompatibles. Términos, robots.txt, atribución, privacidad y sesgos: [docs/etica-datos.md](docs/etica-datos.md). Ficha: [docs/E2/ENTREGA.md](docs/E2/ENTREGA.md).

## 12.2 Pronóstico y tablero local

```bash
python main.py observatorio --horizonte 3
# repetir un corte previo: python main.py observatorio --horizonte 3 --corte 2026-11-20
python3 scripts/servir_tablero.py --port 8000
```

Abre `http://127.0.0.1:8000/tablero/`. El servidor local evita entregar versiones viejas desde caché y la página incluye un resumen precargado si JavaScript no se ejecuta. El proceso convierte cotizaciones a MXN/kg solo si SNIIM declara kilogramo o el peso de caja/arpilla. Filtra origen reportado Colima, exige 36 meses consecutivos sin imputación y compara suavizamiento simple, Holt, Holt-Winters aditivo y ARIMA(1,1,1). Elige con seis meses walk-forward y reporta MAE/RMSE/MAPE en seis meses holdout posteriores que no participan en la selección; luego reentrena con toda la serie para proyectar de 1 a 12 meses. Si no hay dos plazas con producto, variante, origen y meses coincidentes, no declara un mercado ganador.

El mes en curso se excluye del ajuste y de la comparación para no tratar una cotización parcial como un agregado mensual completo. `--corte AAAA-MM-DD` fija la fecha de referencia al reproducir una versión anterior.

Salidas: `data/oro/pronosticos_colima.csv`, métricas y predicciones de backtest, `comparativa_mercados_colima.csv`, cobertura y `reporte_observatorio_e4.json`; el panel, métricas, validaciones, cobertura y reporte también se publican en `data/publico/`. El tablero en `tablero/index.html` tiene navegación por áreas, filtros interactivos de producto y ventana temporal, evaluación de modelos, calidad, cobertura y descargas; su plantilla editable está en `tablero/plantilla.html`. `panel_mensual_e3.csv` se conserva como snapshot de E3. Guion y evidencia de defensa: [docs/E4/ENTREGA.md](docs/E4/ENTREGA.md) y [docs/E4/guion_defensa.md](docs/E4/guion_defensa.md).

La vista para compradores está en [`tablero/cliente.html`](tablero/cliente.html) y se publica en `/tablero/cliente.html`. Presenta filtros por producto, origen y plaza; historial y pronóstico; comparación de precios brutos en meses pareados; simulador de margen, merma, flete y punto de equilibrio a partir de costos ingresados por el cliente; mapa municipal de producción oficial SIAP; y contexto de comercio internacional con importadores que reportan a México como socio y exportadores globales por grupo HS. Las observaciones por pieza no se convierten artificialmente a kg. El precio mayorista más alto no se etiqueta como plaza más rentable: el orden neto se obtiene solo si se introducen costo de compra, flete, empaque y mermas por destino. El punto de equilibrio debe contrastarse con demanda confirmada.

El contexto agrícola municipal se integra con SIAP desde su CSV oficial anual; conserva el archivo original en Bronce y produce [`data/publico/produccion_municipal_colima.geojson`](data/publico/produccion_municipal_colima.geojson) y una tabla anual municipal. Ejecuta `python main.py siap` para regenerar el mapa desde las capturas disponibles. La producción pasada describe dónde se produjo y cuánto se cosechó en el año; no es inventario o disponibilidad actual.

El contexto internacional usa UN Comtrade para comercio anual reportado por país y grupos de frutas del Sistema Armonizado. Ejecuta `python main.py comercio-intl` para capturar los previews públicos, o `python main.py comercio-intl --solo-procesar` para regenerar las tablas desde Bronce. El API público limita las consultas a 500 filas; una consulta con 500 observaciones se marca con truncamiento posible. El valor USD/kg mostrado es aduanal (valor/peso neto), no una cotización mayorista o minorista. Los grupos HS de mango/guayaba/mangostán y limón/lima pueden combinar productos distintos. Para buscar compradores reales hace falta confirmar destino, demanda, logística, requisitos fitosanitarios, aranceles y contrato.

Más detalle de ecuaciones, límites y sentido comercial: [`docs/comercial/analitica_decisiones.md`](docs/comercial/analitica_decisiones.md).

## 12.3 Optimización y publicación E3

`src/tdl_e1/pipeline.py` aplica validación vectorizada de reglas y evita recorrer grupos singleton si no hay claves duplicadas. El parser SNIIM limita el árbol HTML a tablas. La medición antes/después se reproduce con el tag de línea base `e2` y el inventario Bronce versionado:

```bash
python benchmarks/comparativa.py --repeticiones 7 --semilla 20261120
```

El benchmark compara los tags congelados `e2` y `e3` en pares aislados, aleatoriza cuál corre primero dentro de cada par, exige igualdad SHA-256 de las salidas CSV y guarda cada corrida, logs y gráfica. El snapshot E3 está en [`data/publico/panel_mensual_e3.csv`](data/publico/panel_mensual_e3.csv); la publicación viva en `data/publico/panel_mensual_actual.csv`. Licencia y avisos en [`data/publico/LICENSE.md`](data/publico/LICENSE.md); diccionario E3 en [`docs/E3/datasheet.md`](docs/E3/datasheet.md); resultados en [`docs/E3/ENTREGA.md`](docs/E3/ENTREGA.md).

## 12.4 Laboratorio estadístico

Los tres laboratorios son módulos de Python en formato *percent* (`# %%`), que VS Code y Jupyter (con jupytext) abren como notebooks. Cada uno lee solo datos versionados, escribe cifras en `laboratorio/resultados/eN/` y regenera su informe en `docs/`:

```bash
python -m laboratorio.e1_series --corte 2026-10   # descomposición, ADF/KPSS, ACF/PACF, 4 modelos, Ljung-Box, intervalos
python -m laboratorio.e2_experimento              # 2³ con bloques, 3×2 con interacción, 2⁴⁻¹ y confirmación (≈ 4 min; no usar la máquina mientras corre)
python -m laboratorio.e3_multivariado             # Mardia, Henze-Zirkler, PCA, MANOVA y permutación
python -m laboratorio.tablero                     # publica tablero/laboratorio.html
```

El experimento E2 procesa copias locales de Bronce; no hace peticiones al SNIIM. Las métricas de calidad se calculan con `python -m calidad.metricas` (fiabilidad, frescura e ISO/IEC 25012 en `calidad/reportes/`).

## 12.5 Seguimiento de oportunidades comerciales

El módulo opcional `src/modelos/` y `scripts/comercial.py` organiza prospectos, proveedores, cotizaciones, rutas, oportunidades y operaciones piloto en CSV locales. Inicializa y valida las tablas, importa un CSV DENUE como prospectos **por verificar**, resume vigencias y evidencia faltante, y valida vínculos entre oportunidad, cliente, cotizaciones y ruta:

```bash
python main.py comercial inicializar
python main.py comercial validar
python main.py comercial importar-denue /ruta/al/denue.csv --estado-default Colima
python main.py comercial seguimiento
```

Los CSV con registros comerciales se excluyen de Git mediante `data/comercial/.gitignore`; esa exclusión no cifra archivos ni restringe acceso local. No se guardan teléfonos ni correos. Revisa [data/comercial/README.md](data/comercial/README.md) y las guías de [entrevista](docs/comercial/entrevista_comprador.md), [cotización](docs/comercial/solicitud_cotizacion.md) y [cierre de piloto](docs/comercial/cierre_piloto.md).

`src/economia/` aporta cálculo de costo puesto en destino, contribución, punto de equilibrio, escenarios y priorización multicriterio con niveles de evidencia. Son herramientas de análisis que requieren costos, pesos, cotizaciones y vigencias documentados; **no convierten automáticamente el pronóstico SNIIM en oferta ni acreditan rentabilidad**. Las tablas recién inicializadas estarán vacías hasta que el equipo registre evidencia real.

## 13. Sistema PSP
```bash
python -m calidad.psp tiempo --archivo calidad/tiempo-sebastian.csv --fecha 2026-11-08 \
    --inicio 09:00 --fin 10:30 --interrupcion 10 --fase Codificación --actividad "Extractor base"
python -m calidad.psp defecto --archivo calidad/defectos-sebastian.csv --fecha 2026-11-08 \
    --tipo datos --introducido Codificación --eliminado Pruebas --minutos 15 --descripcion "Parser ignora filas"
python -m calidad.psp resumen --archivo calidad/tiempo-sebastian.csv
python -m calidad.psp validar --tiempo calidad/tiempo-sebastian.csv --defectos calidad/defectos-sebastian.csv
```
Fases (estilo del Kit; se aceptan sinónimos con acentos): planeacion, diseno, codigo, revision, compilacion, pruebas, correccion, documentacion. Tiempo neto = fin − inicio − interrupción. En este corte Sebastián tiene 4 registros de tiempo y 3 defectos; los archivos de José solo tienen encabezados. No inventar actividades retroactivas.
Tipos de defecto (`calidad/catalogo_defectos.json`): los diez de PSP que exige el Kit: documentacion, sintaxis, construccion, asignacion, interfaz, verificacion, datos, funcion, sistema y entorno (cada uno con un ejemplo del proyecto).
Bitácora de capturas: `calidad/bitacora_capturas.csv` (una fila por ejecución y fuente; base de MTBF/MTTR/disponibilidad en E1).
Objetivos (`calidad/objetivos_calidad.json`): OQ1 disponibilidad ≥ 95 %, OQ2 cero fallos no detectados, OQ3 cobertura diaria 100 %. Evaluación: `python main.py objetivos --desde AAAA-MM-DD --hasta AAAA-MM-DD` (devuelve `sin_datos` si no hay manifiestos; no hay metas "alcanzadas" sin evidencia).

## 14. Pruebas
```bash
pip install -r requirements-dev.txt                    # pytest-cov, ruff, pip-audit
python -m pytest -q --cov                              # unitarias sin red con cobertura (umbral 60 % en pyproject.toml)
ruff check .                                           # linter
pip-audit -r requirements-dev.txt                      # vulnerabilidades conocidas
RUN_INTEGRATION=1 python -m pytest -m integration -s   # contra SNIIM y NOAA NCEI reales
```
Los HTML/JSON de las pruebas unitarias son *fixtures* controlados, no capturas reales.

## 15. GitHub Actions
`.github/workflows/validacion.yml` es la puerta de calidad 2: en cada push y pull request corre gitleaks sobre todo el historial, ruff, pip-audit, pruebas con cobertura mínima de 60 %, regenera Plata/Oro desde Bronce y falla si hay registros perdidos sin cuarentena, y calcula las métricas de fiabilidad e ISO/IEC 25012. Para reproducir exactamente: Python 3.12 y `pip install -r requirements-lock.txt`. Los workflows históricos y diarios actualizan las fuentes conforme a la política, ejecutan E1/E2/E4, refrescan el CSV público actual y el tablero, validan Bronce y publican con `GITHUB_TOKEN`. La captura diaria corre a las **03:00 UTC = 21:00 en Colima**; los schedules solo corren desde la rama por defecto.

## 16. Limitaciones conocidas
* **SNIIM sin API oficial**: se consulta el formulario público; fixtures unitarios cubren el parser y `pytest -m integration` permite validar el sitio actual. Cambios de estructura dejan captura fallida/parcial, no generan datos inventados.
* La URL de resultados usa el patrón observado; que acepte rangos mensuales y la paginación (`RegistrosPorPagina=500`) no está verificado: si la fuente reporta varias páginas, la captura queda `parcial`.
* Tecomán/Armería no son mercados del SNIIM; las zonas productoras se cubren con clima. "Colima: Centros de distribución" es opcional.
* "Ciudad de México" = Central de Abasto de Iztapalapa; "Guadalajara" = Mercado de Abasto (el Felipe Ángeles es opcional).
* GitHub Actions puede ser bloqueado por el sitio (IPs de centros de datos): quedaría registrado como fallida.
* El pronóstico exige 36 meses continuos; seis meses se usan para elegir el modelo y los seis meses cerrados siguientes quedan reservados como holdout para medir error fuera de muestra. En el corte local hay series para limón #5, papaya Maradol y tamarindo. Tamarindo tiene 27 meses comunes entre Colima y Guadalajara; la comparación es descriptiva y no alcanza para recomendar una plaza.
* NOAA NCEI: una estación (Manzanillo), no Tecomán. En el corte 2026-11-20, los registros útiles terminan el 2026-06-29; los nulos posteriores se conservan.

## 17. Consideraciones éticas
User-Agent identificable, robots.txt obligatorio (si no se puede leer, **no se hace scraping**), Crawl-delay y pausa ≥ 1.5 s por dominio, sin proxies ni evasión de protecciones y con volumen bajo. La declaración vigente de términos y límites de las tres fuentes está en [docs/etica-datos.md](docs/etica-datos.md).

## 18. Ejemplo de ejecución
```
$ python main.py diaria --fecha 2026-11-06
… RESUMEN run=20261108T090133Z-332bb7 fuente=sniim estado=fallida … solicitudes=2 registros=0 archivos=0 errores=1
… Fin captura diaria … estados={'sniim': 'fallida', 'noaa_ncei': 'fallida'} codigo_salida=1
```
(Ejemplo real ejecutado en un entorno **sin acceso a Internet**: demuestra que una fuente inaccesible queda registrada como fallida con manifiesto.)
