# Requerimientos verificables del observatorio

Cada requerimiento se revisó contra las características de un buen requerimiento: **necesario** (se liga a una pregunta del cliente o a la rúbrica), **no ambiguo** (una sola interpretación, con umbral numérico cuando aplica), **verificable** (tiene una comprobación automática o un procedimiento repetible) y **rastreable** (indica su origen y dónde se implementa).

Origen: C = necesidad del cliente (entrevistas E0), P = guía del Proyecto Integrador, É = ética y legalidad.

## Funcionales

| ID | Requerimiento | Origen | Implementación | Verificación |
|---|---|---|---|---|
| RF-01 | El sistema captura diariamente precios SNIIM de los productos y plazas configurados en `config/fuentes.json` y guarda la respuesta original sin modificar. | P, C | `scripts/captura_diaria.py`, workflow `captura_diaria.yml` | Bitácora con ≥ 1 ejecución por día; `python main.py validar` sin errores |
| RF-02 | Cada archivo Bronce tiene un sidecar `.meta.json` con URL, fecha UTC de captura, estado HTTP y SHA-256. | P | `almacenamiento/bronze_writer.py` | `tests/test_bronze.py`; `scripts/validar_bronce.py` |
| RF-03 | Un registro que no cumple esquema, tipos, rangos o reglas de negocio no pasa a Plata y queda en `data/cuarentena/registros_invalidos.csv` con archivo, hash y motivo. | P | `src/tdl_e1/pipeline.py::puerta_calidad` | `tests/test_pipeline_e1_integracion.py::test_hash_alterado_va_a_cuarentena_con_motivo`, `tests/test_e3_optimization.py` |
| RF-04 | Los precios no se imputan; la temperatura solo se interpola en una copia de modelado, en huecos interiores de ≤ 2 días y con bandera. | P | `pipeline.py::construir_clima_modelado` | `test_plata_conserva_originales_y_agrega_derivadas` |
| RF-05 | Cada fila de Oro es rastreable hasta los registros Bronce que la originaron (archivo, SHA-256, fecha de ingesta, índice). | P | `pipeline.py::construir_oro`, `validar_linaje_oro` | ISO/IEC 25012 trazabilidad = 100 % (`calidad/reportes/iso25012.json`) |
| RF-06 | El pronóstico mensual se elige por menor error en meses que el modelo no vio y se publica con intervalo de predicción al 80 % y 95 %. | P, C | `laboratorio/e1_series.py`, `tablero/laboratorio.html` | `tests/test_laboratorio.py::test_analisis_completo_sobre_serie_estacional` (orden de intervalos) |
| RF-07 | Un hallazgo cuyo supuesto estadístico no se cumple se publica con un método que no dependa de él, o no se publica. | P | Puerta 3 en `laboratorio/e1_series.py`, `e2_experimento.py`, `e3_multivariado.py` | Sección "Supuestos" en cada informe del laboratorio |
| RF-08 | La comparación entre plazas solo se publica con meses pareados de la misma variante y origen. | C | `src/tdl_e4/observatorio.py::_comparar_mercados` | `tests/test_e4_observatorio.py` |
| RF-09 | El tablero muestra historial, pronóstico con intervalo, calidad de datos y el mapa de componentes principales con una interpretación para el cliente. | P, C | `tablero/index.html`, `tablero/laboratorio.html` | Verificación manual con la lista de la sección 7 del plan SQA |
| RF-10 | El dataset público se distribuye con licencia y ficha técnica que documenta todas sus columnas. | P | `data/publico/LICENSE.md`, `docs/E3/datasheet.md` | ISO/IEC 25012 comprensibilidad (columnas documentadas / columnas) |

## No funcionales

| ID | Requerimiento | Origen | Verificación |
|---|---|---|---|
| RNF-01 | Disponibilidad de la captura programada ≥ 95 % en los últimos 14 días (día operativo: ≥ 1 ejecución sin fuentes fallidas/parciales). | P (Sello) | `python -m calidad.metricas` → `periodos.ventana_sello_14_dias.disponibilidad` |
| RNF-02 | Completitud de las columnas obligatorias de Oro ≥ 95 %. | P (Sello) | `calidad/reportes/iso25012.json` → `medidas.completitud.valor` |
| RNF-03 | Cobertura de pruebas automáticas ≥ 60 % sobre todo el código del repositorio (incluye scripts y módulos opcionales). | P (Sello) | `pytest --cov` con `fail_under = 60` |
| RNF-04 | Cero secretos en el historial y cero vulnerabilidades conocidas en dependencias. | P (Sello) | gitleaks (historial completo) y pip-audit en CI |
| RNF-05 | Un tercero que clone el repositorio con Python 3.12 e instale `requirements-lock.txt` obtiene las mismas salidas de Plata/Oro (mismo SHA-256 de los CSV). | P (Sello) | Procedimiento de [reproducibilidad](sello_tdl.md#reproducibilidad) |
| RNF-06 | El procesamiento Bronce → Oro completo termina en menos de 5 minutos en el runner estándar de GitHub Actions. | P | Duración del paso "Puerta de datos" en la CI |
| RNF-07 | Ninguna petición al mismo dominio se hace con menos de 1.5 s de separación, y no se consulta una ruta prohibida por robots.txt (si robots.txt no se puede leer, no se consulta). | É | `tests/test_base.py` (pausas y robots) |
| RNF-08 | No se almacenan nombres de personas físicas, teléfonos ni correos en ninguna capa. | É | `tests/test_comercial_economia.py` (DENUE sin teléfonos ni correos); revisión del Quality Lead |

## Requerimientos revisados y reescritos

| Antes (ambiguo) | Problema | Ahora |
|---|---|---|
| "La captura debe ser confiable" | No verificable | RNF-01 con umbral y ventana |
| "Los datos deben estar limpios" | Ambiguo | RF-03 y RF-04 (reglas concretas) |
| "El pronóstico debe ser preciso" | Sin umbral ni método | RF-06 (selección por error fuera de muestra + intervalo) |
| "El sistema debe ser rápido" | Sin medida | RNF-06 (5 min en el runner estándar) |
