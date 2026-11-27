# Entrega E3 · Optimización del pipeline y publicación del dataset

**Proyecto:** Observatorio de Agro-Inteligencia Colimense (OAIC)

**Equipo:** Grageda Sandoval Sebastián y Jose Negrete Orozco

**Objetivo:** medir mejoras del pipeline Bronce → Plata → Oro y publicar un panel mensual curado, trazable y documentado.

**Repositorio:** [sebastianGS-z/PROYECTO](https://github.com/sebastianGS-z/PROYECTO)

**Tag:** `e3`

**Fecha:** 2026-11-20

## 1. Pipeline original y diagnóstico

La línea base es el código congelado en el tag `e2`. El flujo de E1 verifica SHA-256 y sidecars de las capturas Bronce SNIIM/NOAA, parsea HTML/JSON, normaliza a un esquema común, aplica reglas de negocio y Pandera, cuarentena errores, resuelve duplicados, transforma y agrega registros a Oro. Las tecnologías principales son Python, pandas, NumPy, Pandera y BeautifulSoup.

Una ejecución de perfilado de la versión original sobre el inventario Bronce de esta entrega mostró como mayor costo la lectura de 1,672 capturas HTML SNIIM con BeautifulSoup construyendo un árbol de documento completo para extraer tablas; el perfil registró aproximadamente 23 s acumulados dentro del parser. También se detectó que la resolución de duplicados recorría cada grupo, incluso cuando todos eran singleton, y que la puerta de reglas de negocio inspeccionaba cada fila con `iterrows()`.

## 2. Optimizaciones implementadas

- El parser SNIIM obtiene texto mínimo para detectar estado/paginación y restringe el árbol BeautifulSoup a las tablas.
- La puerta de calidad evalúa las reglas relacionales mediante máscaras vectorizadas y solo prepara motivos para filas inválidas.
- La resolución de duplicados verifica primero si existe alguna clave repetida; en ausencia de duplicados devuelve el frame en orden y evita construir/recorrer miles de grupos singleton. El flujo de grupos duplicados conserva la estrategia anterior.
- Se agregaron pruebas para la ruta sin duplicados y para cuarentena de errores relacionales.

No se cambió el esquema ni la semántica de los datos publicados. La comparación calcula hashes de todas las salidas CSV y aborta si difieren.

### Fragmentos antes/después

Antes se construía un árbol para todo el HTML y se inspeccionaba una fila por iteración:

```python
soup = BeautifulSoup(html, "html.parser")
texto_norm = normalizar(soup.get_text(" "))
for index, row in df.iterrows():
    # comparar límites y agregar motivos
```

Ahora se restringe el árbol a tablas y se preparan máscaras de calidad en bloque:

```python
soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer("table"))
prices = df["tipo_registro"].eq("precio")
invalid = prices & df["precio_min"].gt(df["precio_max"])
```

Para las observaciones únicas, la versión anterior recorría todos los grupos de `groupby`. La versión actual corta ese recorrido cuando `df.duplicated(keys, keep=False).any()` es falso; si hay duplicados, mantiene el resolvedor original.

## 3. Comparativa cuantitativa

Prueba con las mismas capturas Bronce, Python 3.12.3 en Linux y límites de hilos iguales. Se comparan los códigos congelados en `e2` y `e3` en siete pares de procesos aislados; el orden dentro de cada par se aleatoriza con semilla registrada. Se reportan mediana, rango observado y resultados de cada ejecución. La versión E4 del árbol de trabajo no sustituye la referencia `e3`, pues incorpora cambios semánticos posteriores. Las cifras se generan por [`benchmarks/comparativa.py`](../../benchmarks/comparativa.py) y están respaldadas por [`comparativa.json`](../../benchmarks/comparativa.json), [`resultados.csv`](../../benchmarks/resultados.csv) y logs de cada corrida.

| Indicador | Original (`e2`) | Optimizado | Mejora |
|---|---:|---:|---:|
| Tiempo de ejecución (mediana, 7 pares) | 33.82 s | 21.49 s | 36.45% menos |
| Memoria máxima RSS (mediana, 7 pares) | 175.60 MiB | 157.46 MiB | 10.33% menos |
| Errores de ejecución | 0/7 | 0/7 | Diferencia absoluta: 0; porcentaje no aplicable desde cero |
| Registros Bronce procesados | 15,204 | 15,204 | Sin cambio |
| Filas en cuarentena | 0 | 0 | Diferencia absoluta: 0; porcentaje no aplicable desde cero |
| Agregaciones Oro | 712 | 712 | Sin cambio |
| Salidas CSV | — | — | Cinco SHA-256 idénticos entre versiones |

> Los resultados reales de cada ejecución están en `benchmarks/resultados.csv`; el gráfico comparativo se incluye en [evidencias](evidencias/comparativa.png). Baseline: commit `34b56a3` (tag `e2`); versión optimizada: tag `e3`. El hash SHA-256 del código comparado está registrado en `benchmarks/comparativa.json`.

## 4. Dataset publicado

- CSV curado: [`data/publico/panel_mensual_e3.csv`](../../data/publico/panel_mensual_e3.csv), 712 × 48, noviembre de 2023–noviembre de 2026.
- Ficha para terceros: [`datasheet.md`](datasheet.md), con motivación, composición, diccionario de variables, recolección, preprocesamiento, calidad, limitaciones, usos y reproducción.
- Licencia y atribución: [`data/publico/LICENSE.md`](../../data/publico/LICENSE.md). CC BY 4.0 cubre la contribución de organización/agregación/documentación propia de OAIC en la medida de sus derechos; las fuentes conservan sus condiciones y atribución originales.
- Procedencia completa por fila: campos `linaje_precios_bronce` y `linaje_clima_bronce`; cada referencia contiene archivo, hash SHA-256, fecha UTC e índice original.
- No se publican datos personales. Los precios son referenciales y conservan su presentación comercial; no se convierten a kg sin base verificable.

Este CSV es el snapshot E3 generado el 2026-11-20 y se conserva sin mutaciones para reproducir la entrega. El pipeline E4 publica el panel actual con campos derivados de MXN/kg cuando SNIIM declara el peso, en `data/publico/panel_mensual_actual.csv`; además genera pronósticos validados y el tablero local.

## 5. Evidencias y reproducción

- [Gráfica antes/después](evidencias/comparativa.png).
- [Logs de las catorce corridas](../../benchmarks/evidencias/).
- [Métricas en JSON](../../benchmarks/comparativa.json) y tabla de corridas en CSV.
- [Código optimizado](../../src/tdl_e1/pipeline.py) y parser SNIIM (`extractores/sniim_extractor.py`).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python main.py capas
python main.py observatorio --horizonte 3
python benchmarks/comparativa.py --repeticiones 7 --semilla 20261120
```

La comparación requiere Git, el tag `e2`, las capturas Bronce versionadas localmente y las dependencias del proyecto. Las salidas de benchmark se generan en directorios temporales; logs, CSV de métricas, resumen y gráfica se conservan como evidencia.

## 6. Conclusiones

En esta muestra, la optimización redujo la mediana de tiempo y memoria RSS sin cambiar los CSV, el número de registros aceptados, las filas Oro o los descartes. La mejora medida aplica a este conjunto de 3,736 capturas y a este equipo/entorno; no garantiza el mismo porcentaje con otros volúmenes, sistemas o versiones de Python. El dataset incluye atribución, limitaciones y linaje para facilitar su revisión y reutilización responsable.

**Referencia de entrega:** el tag `e3` debe apuntar al commit que contiene estos artefactos. El enlace del repositorio se registra en el formulario oficial de Classroom.

## 7. Análisis Estadístico (agregado el 2026-11-27)

| Criterio de la rúbrica | Evidencia | Nota del equipo |
|---|---|---|
| Matriz y normalidad multivariada | [multivariado.md §1–2](multivariado.md): 5 variables, vector de medias, covarianzas y correlaciones; Mardia, Henze-Zirkler y Q-Q de Mahalanobis | Normalidad rechazada → se usan métodos robustos |
| Componentes principales | [§3](multivariado.md): estandarización, sedimentación, varianza explicada, cargas, biplot y nombre de negocio de cada componente | CP1 = índice de nicho (precio alto, mercado delgado) |
| MANOVA | [§5](multivariado.md): Wilks, Pillai, Hotelling, Roy; M de Box; permutación de Pillai; contraste con 5 ANOVA y tasa de error por familia | Pillai p (permutación) = 0.001 |
| Mapa en el tablero | [`tablero/laboratorio.html`](../../tablero/laboratorio.html) con interpretación para el comprador | |

## 8. Calidad en los Sistemas de Información (agregado el 2026-11-27)

| Criterio de la rúbrica | Evidencia |
|---|---|
| Cierre de auditoría | [cierre_hallazgos.md](../calidad/auditoria/cierre_hallazgos.md): 0 críticos abiertos en la auditoría interna; **pendiente** cargar la auditoría externa recibida |
| Modelos de proceso | [modelos_proceso.md](../calidad/modelos_proceso.md): MoProSoft y CMMI con brechas concretas, tabla ISO 9001/MoProSoft/SPICE/CMMI/PSP-TSP |
| Retrospectiva PSP | [retrospectiva_psp.md](../calidad/retrospectiva_psp.md) (con los registros que existen; se documenta la falta de datos) |
| Tendencias | [tendencias.md](../calidad/tendencias.md): observabilidad de datos aplicada, con alerta de frescura implementada |
| Solicitud del Sello TDL | [sello_tdl.md](../calidad/sello_tdl.md) |

## 9. Optimización aplicada desde el experimento E2 (2026-11-27)

El [experimento factorial](../E2/experimento_factorial.md) identificó el parser como el factor dominante (96 % de la suma de cuadrados) y confirmó la combinación **lxml + solo tablas** con 5 corridas nuevas (1.161 s contra 1.460 s de la configuración previa en la misma muestra de 150 capturas, −20.5 %). Se aplicó a producción tras verificar el pipeline completo sobre todo Bronce:

| Indicador (una corrida por versión, misma máquina) | html.parser + tablas | lxml + tablas |
|---|---:|---:|
| Tiempo `python -m src.tdl_e1.pipeline` | 38.97 s | 33.68 s (−13.6 %) |
| Memoria máxima RSS | 253.0 MiB | 253.2 MiB |
| SHA-256 de las 5 salidas CSV | — | idénticos |

La mejora de extremo a extremo es menor que la del experimento porque el parseo es solo una parte del pipeline (validación, agregación y escritura no cambian). Es una sola corrida por versión; para un porcentaje con rango debe repetirse `benchmarks/comparativa.py`.
