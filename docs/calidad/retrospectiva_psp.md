# Retrospectiva PSP (E0 → E3)

> Fuente: `calidad/tiempo-sebastian.csv`, `calidad/defectos-sebastian.csv`, `calidad/tiempo-jose.csv`, `calidad/defectos-jose.csv` al 2026-11-27. **No se agregaron registros retroactivos**: un registro PSP reconstruido de memoria no mide nada.

## 1. Datos disponibles

| Integrante | Registros de tiempo | Minutos netos registrados | Defectos registrados | Periodo cubierto |
|---|---:|---:|---:|---|
| Sebastián | 4 | 84 | 3 | 2026-11-08 a 2026-11-09 (E0) |
| José | 0 | 0 | 0 | — |

Tiempo por fase (Sebastián): compilación/ejecución 75 min (89 %), pruebas 9 min (11 %). No hay tiempo registrado de planeación, diseño, código ni revisión.

Defectos (Sebastián):

| # | Tipo PSP | Inyectado en | Eliminado en | Minutos de corrección | Descripción resumida |
|---|---|---|---|---:|---|
| 1 | verificación | código | pruebas | 15 | Parser SNIIM no reconocía "NO HAY REGISTROS" |
| 2 | interfaz | diseño | pruebas | 30 | Open-Meteo y NASA POWER prohíben su API en robots.txt; cambio de fuente a NOAA |
| 3 | documentación | documentación | revisión | 5 | README con tipo de defecto obsoleto |

## 2. Métricas que piden los modelos y qué se puede calcular

| Métrica PSP | Valor | Comentario |
|---|---|---|
| Exactitud de estimación de tiempo | **No calculable** | No se registraron estimaciones antes de las tareas |
| Defectos inyectados por fase | código 1 · diseño 1 · documentación 1 | n = 3, sin valor estadístico |
| Defectos eliminados por fase | pruebas 2 · revisión 1 | |
| Rendimiento (*yield*) de revisión | 1 de 3 defectos (33 %) eliminados en revisión | El resto llegó a pruebas; el defecto de diseño (#2) costó 6 veces más que el de documentación |
| Costo medio de corrección | revisión 5 min · pruebas 22.5 min | Coherente con PSP: cuanto más tarde se detecta, más cuesta |
| Densidad de defectos | No calculable | No se registró tamaño (LOC) por cambio |
| Tendencia E0 → E3 | **No existe** | No hay registros después del 2026-11-09 |

## 3. Diagnóstico honesto

- El registro se abrió en E0 como pide la guía, pero **se abandonó después del 9 de noviembre**. Las etapas E1, E2 y E3 (pipeline, geoespacial, optimización) no tienen tiempo ni defectos registrados, aunque el historial de Git muestra trabajo y correcciones en esas fechas.
- José no tiene ningún registro y no tiene commits propios en el historial. Eso impide demostrar su participación con evidencia, y en la defensa individual puede reducir su calificación.
- Los defectos que sí se registraron muestran el patrón que PSP busca corregir: el más caro (#2, de diseño) se detectó en pruebas, no en revisión.

## 4. Defectos detectados en la revisión del 2026-11-27 (para registrar)

La revisión con asistencia de IA del 2026-11-27 encontró y corrigió estos defectos. Deben registrarse en el PSP **de quien hizo la revisión**, con los minutos reales que cada quien invierta:

| Tipo PSP sugerido | Inyectado | Descripción | Evidencia |
|---|---|---|---|
| función | código (E4) | `main.py e2` tomaba el GeoJSON más reciente de la carpeta, que desde el 27-nov es un polígono estatal, y fallaba | `src/tdl_e2/geoespacial.py::_latest_geojson`, prueba `test_latest_geojson_ignora_poligonos_estatales` |
| entorno | código | `pytest` 8.4.2 con vulnerabilidad PYSEC-2026-1845 | `requirements.txt` |
| asignación | código | Método `tiene_datos_completos` duplicado (código muerto) en `src/economia/costeo.py` | ruff F811 |
| función | código | Rutas de salida E2 exigían estar dentro del repositorio (`relative_to`) | `geoespacial.py::_rel` |
| documentación | documentación | Relatoría E3 y ficha E3 con cifras de benchmark distintas | `docs/relatoria-E3.md` |
| documentación | documentación | 18 columnas de Oro sin documentar en el datasheet | ISO/IEC 25012 comprensibilidad |

## 5. Compromisos para E4 (medibles)

1. Registro diario de tiempo de **ambos** integrantes con `python -m calidad.psp tiempo …`, incluida la fase de planeación con **estimación previa** en minutos para cada tarea (campo `actividad`: "estimado=NN").
2. Todo defecto encontrado en revisión o pruebas se registra el mismo día.
3. Meta E4: al menos 50 % de los defectos eliminados antes de pruebas (revisión), y error de estimación medido.
4. José hace commits propios del laboratorio estadístico (es el Data Statistician).
