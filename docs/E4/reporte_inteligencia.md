# Reporte de inteligencia · precios de frutas de Colima

> Generado por `python main.py reporte` (último mes cerrado 2026-10). Versión visual e imprimible: [`tablero/inteligencia.html`](../../tablero/inteligencia.html).

## Hallazgos principales

1. Limón 2025: el productor de Colima recibió en promedio 9.80 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 26.01 MXN/kg en Guadalajara: el productor capta 38 % del precio mayorista.
2. Limón 2024: el productor de Colima recibió en promedio 10.32 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 21.27 MXN/kg en Guadalajara: el productor capta 48 % del precio mayorista.
3. Papaya 2024: el productor de Colima recibió en promedio 7.41 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 19.80 MXN/kg en Guadalajara: el productor capta 37 % del precio mayorista.
4. Papaya 2025: el productor de Colima recibió en promedio 7.47 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 18.21 MXN/kg en Guadalajara: el productor capta 41 % del precio mayorista.
5. Papaya Maradol - Primera: Querétaro · Mercado de Abasto pagó en promedio 5.44 MXN/kg más que Guadalajara · Mercado de Abasto en 12 meses pareados (100 % de los meses). Conviene enviar ahí solo si el flete adicional cuesta menos de 5.44 MXN/kg. Confianza alta (p < 0.001 con 12 observaciones).
6. Plátano Dominico - Primera: Tijuana · Central de Abasto INDIA pagó en promedio 21.15 MXN/kg más que Querétaro · Mercado de Abasto en 12 meses pareados (100 % de los meses). Conviene enviar ahí solo si el flete adicional cuesta menos de 21.15 MXN/kg. Confianza alta (p < 0.001 con 12 observaciones).
7. Limón en Guadalajara: el mes que más pagó en promedio fue septiembre (+32 % frente a la tendencia) y el que menos diciembre (-30 % frente a la tendencia), con 3 años por mes; la prueba de Kruskal-Wallis no lo distingue del azar (p = 0.31), así que es una pista, no una regla.
8. Papaya en Guadalajara: el mes que más pagó en promedio fue noviembre (+19 % frente a la tendencia) y el que menos julio (-16 % frente a la tendencia), con 3 años por mes; la prueba de Kruskal-Wallis no lo distingue del azar (p = 0.26), así que es una pista, no una regla.
9. Tamarindo en Guadalajara: el mes que más pagó en promedio fue enero (+13 % frente a la tendencia) y el que menos septiembre (-7 % frente a la tendencia), con 2 a 3 años por mes; la prueba de Kruskal-Wallis no lo distingue del azar (p = 0.58), así que es una pista, no una regla.

## Incertidumbre y límites

- Los pronósticos se publican con intervalos de 80 % y 95 % construidos con errores fuera de muestra; su cobertura se audita en el holdout.
- La comparación de plazas no incluye tarifas de flete inventadas: reporta el **flete de equilibrio** para que el cliente lo contraste con su cotización.
- El precio al productor es el promedio anual SIAP ponderado por volumen de los municipios de Colima; no corresponde a un productor ni a una calidad específicos.
- El calendario estacional usa 2–3 años por mes: indica una tendencia, no una regla.

## Recomendaciones

1. Planear compras y ventas con el rango de 80 %, no con el valor puntual.
2. Antes de enviar a una plaza distinta de Guadalajara, pedir cotización de flete y compararla contra el flete de equilibrio de la tabla de plazas.
3. Negociar contratos de precio fijo para el limón en los meses de índice estacional bajo, cuando el precio de plaza suele caer.
4. Revisar las señales del último mes: un percentil ≥ 75 indica precio históricamente alto.
