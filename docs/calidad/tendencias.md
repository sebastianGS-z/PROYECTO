# Tendencia aplicada: observabilidad de datos (DataOps) en el OAIC

**Qué es.** La observabilidad de datos aplica a los *datos* lo que el monitoreo hace con los servidores: medir continuamente su **frescura** (¿llegó el dato de hoy?), **volumen** (¿llegaron tantos registros como se esperaba?), **esquema** (¿cambió la estructura?), **distribución** (¿los valores se salen de lo normal?) y **linaje** (¿de dónde viene cada cifra?). Es parte de DataOps: tratar los flujos de datos con las mismas prácticas de integración continua, pruebas y despliegue que el software.

**Por qué importa aquí.** El mayor riesgo del OAIC no es que el código falle, sino que **los datos dejen de llegar sin que nadie lo note**. Ya ocurrió: NOAA respondió correctamente pero sin datos nuevos en las 17 ejecuciones diarias programadas medidas (`calidad/reportes/fiabilidad.json`). El sistema lo registró como `sin_resultados` (no como fallo), así que ninguna alerta se disparó y la temperatura de Oro quedó meses atrasada.

## Los cinco pilares en el observatorio

| Pilar | Qué ya existe | Qué falta (acción) |
|---|---|---|
| Frescura | Bitácora con fecha de cada captura; `actualidad` en ISO/IEC 25012 | Alerta si una fuente acumula **N días seguidos** sin datos nuevos (NOAA: N = 7) aunque técnicamente esté "operativa" |
| Volumen | Conteo de registros por manifiesto | Comparar registros del día con la mediana de los últimos 28 días del mismo día de la semana; alertar si cae > 50 % |
| Esquema | Pandera estricto; parser que lanza `StructureChangedError` | Ya cubierto: un cambio de HTML deja la captura `fallida`, nunca datos inventados |
| Distribución | Detección de atípicos IQR/MAD en Plata | Publicar en el tablero la proporción de atípicos por semana como indicador |
| Linaje | Cada fila de Oro lista sus registros Bronce con SHA-256 | Ya cubierto (trazabilidad 100 %) |

## Propuesta concreta (implementable en un workflow)

1. Paso nuevo en `captura_diaria.yml` después de la captura: `python -m calidad.metricas` (ya corre en la CI) más una regla de frescura que falla el job con un aviso (`::warning::`) si `tasa_con_datos_nuevos` de una fuente es 0 en los últimos 7 días.
2. Un resumen de frescura por fuente en el `GITHUB_STEP_SUMMARY`, que ya se usa para los estados de captura.
3. En el tablero, un indicador "última fecha con dato nuevo" por fuente, para que el cliente vea la actualidad de cada cifra.

## Relación con otras tendencias

- **DevSecOps:** gitleaks y pip-audit en cada push ya son seguridad integrada al flujo.
- **Gobierno de IA (ISO/IEC 42001):** el observatorio no usa modelos de IA en producción; los asistentes de código se declaran en las relatorías. Si en el futuro se agrega un modelo de lenguaje para resumir reportes, 42001 pediría inventario del sistema de IA, evaluación de impacto y supervisión humana.
