# E4 · Evidencia técnica para defensa

**Proyecto:** Observatorio de Agro-Inteligencia Colimense (OAIC)  
**Corte local:** 26 de noviembre de 2026  
**Propósito:** mostrar el flujo operativo, los datos observados, la interfaz del cliente y los límites de uso con evidencia reproducible.

## Qué hace el sistema y qué valor aporta

OAIC captura cotizaciones mayoristas públicas de SNIIM y observaciones climáticas NOAA, conserva los originales en Bronce con huellas SHA-256, valida y estandariza los registros en Plata, y agrega series mensuales en Oro. La vista de cliente presenta indicadores que un comprador puede interpretar, compara únicamente periodos y especificaciones coincidentes, separa precios por unidad cuando no se conoce el peso, y muestra estimaciones solo para series con historia suficiente.

Su valor es ofrecer contexto verificable para preparar preguntas y contrastar cotizaciones. No sustituye una cotización vigente, una inspección de calidad ni un cálculo de rentabilidad puesto en destino. El código económico complementario permite registrar costos y escenarios, pero requiere evidencia real de flete, merma, volumen y condiciones comerciales.

## Evidencia regenerada

La ejecución con capturas Bronce locales produjo:

- **18,963** registros Bronce parseados; **18,061** registros normalizados en Plata; **0** en cuarentena; **809** claves duplicadas con discrepancia resueltas según la regla documentada; **895** filas mensuales en Oro.
- **865** observaciones mensuales públicas comparables por kilogramo, de **13 cultivos**, **13 orígenes reportados** y **4 plazas**: Colima, Guadalajara, Ciudad de México y Morelia. Entre los productos capturados están limón, papaya y plátano, además de mango Ataulfo/Manila, aguacate Hass, coco, tamarindo, guayaba, guanábana y variedades identificadas de sandía.
- **3** precios de coco por pieza en octubre de 2026. Se muestran en su unidad reportada, aparte del análisis por kg; no se infiere peso por pieza ni se convierten a MXN/kg.
- **Tres series pronosticables** de origen reportado Colima y 36 meses cerrados entre noviembre de 2023 y octubre de 2026: limón c/semilla #5 y papaya Maradol en Guadalajara, y tamarindo en los Centros de distribución de Colima. El mes actual (noviembre) se excluye por estar incompleto. El umbral de elegibilidad de 36 meses permite separar entrenamiento, selección y evaluación; no se amplía el pronóstico a variedades con cobertura incompleta.
- **9 estimaciones** (3 meses por serie). Se elige el modelo con menor MAE en seis meses de selección y se mide el error reportado en otros seis meses holdout independientes. ARIMA(1,1,1) ganó para limón (MAE holdout 6.15 MXN/kg; MAPE 23.49 %); suavizamiento simple ganó para papaya (MAE 1.51; MAPE 8.89 %) y tamarindo (MAE 0.22; MAPE 0.53 %). Consulta los CSV para los errores exactos y todos los modelos evaluados.
- **1 comparación pareada** para una misma variante/origen Colima entre plazas: tamarindo tiene 27 meses comunes entre Colima y Guadalajara. Es descriptiva y no basta por sí sola para recomendar una plaza. La vista también muestra pares de otros orígenes cuando coinciden meses, identifica el tamaño de muestra y advierte que menos de 12 meses no sustenta una recomendación.
- El contexto climático procede de la estación de Manzanillo: 32 meses con observaciones, con el dato más reciente en octubre de 2026. No representa directamente las parcelas productoras ni las plazas mayoristas y no alimenta el pronóstico de precios.

Las nuevas frutas y plazas agregan amplitud de consulta, pero solo tamarindo reunió 36 meses consecutivos con origen Colima en la plaza local. Mango Ataulfo y guayaba incorporan observaciones históricas, aunque no reúnen los criterios de elegibilidad por origen/continuidad para un pronóstico. Otras combinaciones nuevas solo tienen octubre de 2026. No se extrapola un pronóstico ni se rellenan meses ausentes. Los pronósticos son estimaciones puntuales académicas, sin intervalo predictivo validado ni garantía; no modelan flete, calidad, volumen, precio en parcela o causalidad climática.

## Interfaz para clientes

- [`tablero/cliente.html`](../../tablero/cliente.html): consulta con filtros de producto/variedad, origen y plaza; historial mensual, variación, estimación, MAE, comparación entre plazas, tabla por unidad reportada y glosario.
- [`data/publico/resumen_cliente.json`](../../data/publico/resumen_cliente.json): fuente pública compacta de la interfaz. No incorpora rutas de linaje por registro ni datos comerciales privados.
- La página distingue precio observado (reporte histórico) de estimación (salida del modelo), explica origen reportado y MAE, y recomienda validar peso, calidad, volumen, vigencia, flete y condiciones de pago antes de operar.

### Funciones comerciales añadidas

- La interfaz compara precios brutos entre plazas únicamente cuando coinciden la variante, el origen reportado y los meses. La diferencia se calcula sobre esos mismos meses; el número de observaciones y la cobertura temporal quedan visibles.
- El simulador ordena las plazas por resultado estimado una vez que se capturan compra, manejo, merma, costos fijos, volumen y flete por destino. Calcula margen por kg comprado, neto del lote y punto de equilibrio. Es un escenario definido por el usuario, no recomienda comprar sin una orden/demanda confirmada.
- El mapa geográfico muestra la producción cosechada anual SIAP por municipio de Colima para el cultivo elegido. No es mapa de inventario, huertas ni proveedores.
- La comparación internacional usa UN Comtrade 2024. Al corte, la captura archivada integra tres grupos HS (aguacate; mango/guayaba/mangostán; limones/limas), 479 filas y 133 países reportantes entre importadores con México como socio y exportadores mundiales. Los previews públicos tienen límite de 500 filas por consulta. Son flujos agregados y valores unitarios aduanales; no son precios mayoristas/retail ni validan compradores. No hay cobertura capturada para toda fruta ni una capa cartográfica de rutas/destinos internacionales.
- El resultado depende de la cobertura real. Por ejemplo, Mango Ataulfo con origen Guerrero tiene una sola cotización mensual en este corte: se muestra el precio y la producción municipal, pero no se habilita pronóstico ni una comparación de plazas. Sin precio compatible no se recomienda destino.

Para verla localmente: `python3 scripts/servir_tablero.py --port 8000` y abrir `http://127.0.0.1:8000/tablero/cliente.html`.

## Archivos de evidencia

- [`data/oro/reporte_observatorio_e4.json`](../../data/oro/reporte_observatorio_e4.json): corte, cobertura, modelos, linaje de las series y límites.
- [`data/oro/metricas_backtest_colima.csv`](../../data/oro/metricas_backtest_colima.csv): MAE, RMSE y MAPE por modelo y segmento; solo holdout mide los meses reservados no usados para seleccionar.
- [`data/oro/validaciones_pronostico_colima.csv`](../../data/oro/validaciones_pronostico_colima.csv): valores observados y estimados con la etiqueta del segmento de selección u holdout.
- [`data/oro/pronosticos_colima.csv`](../../data/oro/pronosticos_colima.csv): estimaciones con fechas y huellas de linaje.
- [`data/oro/comparativa_mercados_colima.csv`](../../data/oro/comparativa_mercados_colima.csv): comparación de mercados para las series con origen Colima.
- [`data/publico/comparativa_plazas_cliente.csv`](../../data/publico/comparativa_plazas_cliente.csv): resumen comparativo para la consulta pública.
- [`data/plata/reporte_calidad.json`](../../data/plata/reporte_calidad.json): validaciones, cuarentena, faltantes y normalización.
- [`docs/comercial/`](../comercial/): formatos para solicitar cotizaciones y evaluar operaciones piloto; requiere completar evidencia real.

## Reproducción

```bash
python main.py historica --productos mango_ataulfo guayaba tamarindo --mercados colima guadalajara
python main.py capas
python main.py observatorio --horizonte 3 --corte 2026-11-26
python3 scripts/servir_tablero.py --port 8000
```

La captura histórica consulta 36 meses por mes y mercado, conserva cada respuesta y su estado (con datos, sin resultados o fallida) en los manifiestos. El flujo también descarga NOAA para Manzanillo. Respeta el retraso, robots.txt y reintentos del extractor.

La regeneración final reportó 18,963 registros Bronce parseados, 18,061 en Plata, cero en cuarentena, 895 filas Oro, tres series pronosticables y nueve estimaciones. La selección del modelo usa seis meses anteriores y la evaluación de error se reserva para los seis meses posteriores; sus fechas exactas se publican en el reporte por serie y en las predicciones de validación. La interfaz se revisó con tamarindo (MAE holdout y comparación pareada), mango (producción municipal y flujos internacionales) y una simulación de costos que señaló “No vender con estos costos” cuando el resultado neto era negativo. Los datos municipales SIAP y las tablas internacionales se regeneraron desde sus archivos Bronce.
