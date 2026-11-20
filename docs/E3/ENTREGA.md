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

Prueba con las mismas 3,736 capturas Bronce (37,463,948 bytes; inventario SHA-256 `e80946048bbf911f6be13ab49ec19a313dc808f0a47c97705e6ba84dc98ecea7`), Python 3.12.3 en Linux, límites de hilos iguales y tres procesos aislados por versión. Se reporta la mediana. Las cifras se generan por [`benchmarks/comparativa.py`](../../benchmarks/comparativa.py) y están respaldadas por [`comparativa.json`](../../benchmarks/comparativa.json), [`resultados.csv`](../../benchmarks/resultados.csv) y logs de cada corrida.

| Indicador | Original (`e2`) | Optimizado | Mejora |
|---|---:|---:|---:|
| Tiempo de ejecución | 22.10 s | 19.29 s | 12.74% menos |
| Memoria máxima RSS | 173.68 MiB | 155.47 MiB | 10.48% menos |
| Errores de ejecución | 0/3 | 0/3 | Diferencia absoluta: 0; porcentaje no aplicable desde cero |
| Registros Bronce procesados | 15,204 | 15,204 | Sin cambio |
| Filas en cuarentena | 0 | 0 | Diferencia absoluta: 0; porcentaje no aplicable desde cero |
| Agregaciones Oro | 712 | 712 | Sin cambio |
| Salidas CSV | — | — | Cinco SHA-256 idénticos entre versiones |

> Los resultados reales de cada ejecución están en `benchmarks/resultados.csv`; el gráfico comparativo se incluye en [evidencias](evidencias/comparativa.png). Baseline: commit `34b56a3` (tag `e2`). El hash SHA-256 del código optimizado está registrado en `benchmarks/comparativa.json`.

## 4. Dataset publicado

- CSV curado: [`data/publico/panel_mensual_e3.csv`](../../data/publico/panel_mensual_e3.csv), 712 × 48, noviembre de 2023–noviembre de 2026.
- Ficha para terceros: [`datasheet.md`](datasheet.md), con motivación, composición, diccionario de variables, recolección, preprocesamiento, calidad, limitaciones, usos y reproducción.
- Licencia y atribución: [`data/publico/LICENSE.md`](../../data/publico/LICENSE.md). CC BY 4.0 cubre la contribución de organización/agregación/documentación propia de OAIC en la medida de sus derechos; las fuentes conservan sus condiciones y atribución originales.
- Procedencia completa por fila: campos `linaje_precios_bronce` y `linaje_clima_bronce`; cada referencia contiene archivo, hash SHA-256, fecha UTC e índice original.
- No se publican datos personales. Los precios son referenciales y conservan su presentación comercial; no se convierten a kg sin base verificable.

## 5. Evidencias y reproducción

- [Gráfica antes/después](evidencias/comparativa.png).
- [Logs de las seis corridas](../../benchmarks/evidencias/).
- [Métricas en JSON](../../benchmarks/comparativa.json) y tabla de corridas en CSV.
- [Código optimizado](../../src/tdl_e1/pipeline.py) y parser SNIIM (`extractores/sniim_extractor.py`).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python main.py capas
cp data/oro/panel_mensual.csv data/publico/panel_mensual_e3.csv
python benchmarks/comparativa.py --repeticiones 3
```

La comparación requiere Git, el tag `e2`, las capturas Bronce versionadas localmente y las dependencias del proyecto. Las salidas de benchmark se generan en directorios temporales; logs, CSV de métricas, resumen y gráfica se conservan como evidencia.

## 6. Conclusiones

En esta muestra, la optimización redujo la mediana de tiempo y el máximo RSS sin cambiar los CSV, el número de registros aceptados, las filas Oro o los descartes. La mejora medida aplica a este conjunto de 3,481 capturas y a este equipo/entorno; no garantiza el mismo porcentaje con otros volúmenes, sistemas o versiones de Python. El dataset incluye atribución, limitaciones y linaje para facilitar su revisión y reutilización responsable.

**Referencia de entrega:** el tag `e3` debe apuntar al commit que contiene estos artefactos. El enlace del repositorio se registra en el formulario oficial de Classroom.
