# Guion de defensa E4

## Mensaje de apertura

OAIC es un flujo reproducible de datos que conserva las fuentes originales, las valida, agrega precios a nivel mensual, integra contexto geográfico y clima disponible, y genera pronósticos exploratorios con trazabilidad y evaluación temporal. No estima ingresos en parcela ni garantiza decisiones comerciales.

## Demostración de 7 minutos

1. **Problema y alcance (1 min).** SNIIM publica cotizaciones por mercado, origen y presentación. La unidad se normaliza a MXN/kg solo cuando el kilogramo o el peso aparecen explícitamente en la presentación. El alcance pronosticable actual se limita a las series de origen Colima con 36 meses mensuales continuos.
2. **Captura y procedencia (1 min).** Mostrar una captura Bronce, su manifiesto y metadatos; explicar SHA-256, consulta ética y por qué una ausencia queda vacía. Los códigos SNIIM se leen del sidecar, no se interpretan por intuición: `140` es Guadalajara y `100` Iztapalapa.
3. **Puerta de calidad (1 min).** Mostrar esquema Pandera, conflicto/cuarentena y el reporte actual. El corte vigente no tuvo inválidos; las pruebas cubren reglas que sí mandan entradas inválidas a cuarentena.
4. **Transformación y linaje (1 min).** Mostrar una cotización de caja de 15 kg, la operación MXN por presentación ÷ 15 y la referencia desde Oro hasta el índice Bronce. No mezclar el precio con la estación como si fuera clima de la plaza.
5. **Pronóstico (1 min).** Abrir `tablero/index.html`; enseñar el histórico completo cerrado, el mes parcial excluido, horizonte, modelo elegido, MAE/RMSE/MAPE y selección walk-forward en seis meses y evaluación independiente en los seis meses posteriores (holdout). Explicar que el MAE reportado no participó en la selección y el modelo final se vuelve a ajustar con el historial cerrado completo.
6. **Cobertura (1 min).** El tablero muestra tres series con origen Colima. Tamarindo tiene 27 meses comunes entre plazas: suficiente para describir el par, pero no para convertirlo en recomendación comercial. Limón y papaya solo tienen una plaza coincidente en este corte.
7. **Decisión comercial y cierre (1 min).** En `tablero/cliente.html`, comparar plazas pareadas, ingresar costos y mostrar cómo el flete/merma puede cambiar o negar rentabilidad. Mostrar el mapa SIAP de municipios productores y el contexto comercial UN Comtrade 2024 para los grupos HS capturados. Aclarar que ninguna cifra internacional confirma precio de venta, comprador ni margen de exportación. Presentar E3 como mejora medida en el equipo y muestra registrados, con hashes de salida iguales.

## Respuestas que deben quedar claras

- **¿El precio está en kg?** Sí, para cotizaciones SNIIM cuya etiqueta declara kg o peso explícito; el campo conserva la regla usada. Presentaciones sin peso verificable quedan nulas y no entran a pronóstico.
- **¿El clima explica el precio?** No se ha probado causalidad. La única estación es Manzanillo y sus datos se presentan como contexto, no como observación de Guadalajara o CDMX.
- **¿Cuál es el mejor mercado?** La comparación de tamarindo cubre 27 meses comunes y es descriptiva; los precios reportados no incorporan costos de operación, calidad ni disponibilidad, así que no se afirma cuál conviene comprar o vender.
- **¿El simulador garantiza rentabilidad o define cuánto comprar?** No. Ordena plazas por el escenario calculado con los costos que se capturen y muestra punto de equilibrio. La cantidad debe limitarse a demanda/orden confirmada; el simulador no tiene compradores ni inventario conectados.
- **¿Qué significa el mapa?** Producción cosechada SIAP por municipio para 2025; no localiza parcelas, inventario o productores individuales. Los destinos nacionales son plazas observadas por SNIIM; el contexto extranjero es comercio agregado de tres grupos HS capturados, sin mapa de rutas ni precio mayorista internacional.
- **¿Qué significa el error?** MAE, RMSE y MAPE del modelo elegido se calculan en seis meses holdout que no se usaron para escogerlo. Son una muestra breve, no una probabilidad de acierto ni una garantía.
- **¿Por qué el dataset público cambia?** `panel_mensual_actual.csv`, pronósticos, comparaciones y tablero se regeneran junto al pipeline; `panel_mensual_e3.csv` permanece como la copia histórica de E3.

## Comandos de reproducción

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python main.py capas
python main.py observatorio --horizonte 3
python3 scripts/servir_tablero.py --port 8000
```

Abrir `http://localhost:8000/tablero/`. Para renovar fuentes con la política de captura, usar `python main.py e2`; la validación de CI y la generación analítica usan Bronce ya versionado y no hacen solicitudes de red.

## Evidencia de corte

El comando `python main.py observatorio` escribe `data/oro/reporte_observatorio_e4.json`, con fecha UTC, cobertura por serie, modelos intentados, criterios de elegibilidad, errores de ajuste, número de meses de entrenamiento y comparaciones pareadas. Presentar los valores de ese archivo luego de regenerar desde el Bronce actual, no reutilizar cifras de cortes anteriores.
