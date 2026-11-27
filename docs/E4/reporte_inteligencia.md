# Reporte de inteligencia · precios de frutas de Colima

> Generado por `python main.py reporte` (último mes cerrado 2026-10). Versión visual e imprimible: [`tablero/inteligencia.html`](../../tablero/inteligencia.html).

## Hallazgos principales

1. Tamarindo: el valor de exportación de México en 2024 (65.34 MXN/kg) superó en 27 % al precio mayorista nacional (51.50 MXN/kg); principal comprador: USA. Es valor aduanal: descuente certificación, empaque y logística antes de comparar. (HS 081340 agrupa tamarindo y otras frutas secas.)
2. Guayaba: el valor de exportación de México en 2024 (30.08 MXN/kg) superó en 27 % al precio mayorista nacional (23.66 MXN/kg); principal comprador: USA. Es valor aduanal: descuente certificación, empaque y logística antes de comparar. (HS 080450 agrupa guayaba, mango y mangostán.)
3. Aguacate: el valor de exportación de México en 2024 (58.13 MXN/kg) superó en 64 % al precio mayorista nacional (35.43 MXN/kg); principal comprador: USA. Es valor aduanal: descuente certificación, empaque y logística antes de comparar.
4. Plátano 2021: el productor de Colima recibió en promedio 5.31 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 11.46 MXN/kg en Guadalajara: el productor capta 46 % del precio mayorista.
5. Limón 2025: el productor de Colima recibió en promedio 9.80 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 26.01 MXN/kg en Guadalajara: el productor capta 38 % del precio mayorista.
6. Papaya 2025: el productor de Colima recibió en promedio 7.47 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 18.21 MXN/kg en Guadalajara: el productor capta 41 % del precio mayorista.
7. Papaya Maradol - Primera: Querétaro · Mercado de Abasto pagó en promedio 5.44 MXN/kg más que Guadalajara · Mercado de Abasto en 12 meses pareados (100 % de los meses). Conviene enviar ahí solo si el flete adicional cuesta menos de 5.44 MXN/kg. Confianza alta (p < 0.001 con 12 observaciones).
8. Plátano Dominico - Primera: Tijuana · Central de Abasto INDIA pagó en promedio 21.15 MXN/kg más que Querétaro · Mercado de Abasto en 12 meses pareados (100 % de los meses). Conviene enviar ahí solo si el flete adicional cuesta menos de 21.15 MXN/kg. Confianza alta (p < 0.001 con 12 observaciones).
9. Guayaba en Guadalajara: el mes que más pagó en promedio fue mayo (+35 % frente a la tendencia) y el que menos febrero (-21 % frente a la tendencia), con 3 años por mes; patrón con confianza media (p = 0.015).
10. Limón en Guadalajara: el mes que más pagó en promedio fue marzo (+36 % frente a la tendencia) y el que menos noviembre (-22 % frente a la tendencia), con 9 a 10 años por mes; patrón con confianza alta (p = 0.000).
11. Mango en Guadalajara: el mes que más pagó en promedio fue diciembre (+98 % frente a la tendencia) y el que menos junio (-23 % frente a la tendencia), con 1 a 8 años por mes; patrón con confianza alta (p = 0.000).
12. Papaya en Guadalajara: el mes que más pagó en promedio fue noviembre (+10 % frente a la tendencia) y el que menos julio (-11 % frente a la tendencia), con 9 a 10 años por mes; patrón con confianza alta (p = 0.001).
13. Plátano en Guadalajara: el mes que más pagó en promedio fue febrero (+23 % frente a la tendencia) y el que menos octubre (-20 % frente a la tendencia), con 4 a 6 años por mes; patrón con confianza alta (p = 0.001).
14. Tamarindo en Guadalajara: el mes que más pagó en promedio fue enero (+13 % frente a la tendencia) y el que menos septiembre (-7 % frente a la tendencia), con 2 a 3 años por mes; la prueba de Kruskal-Wallis no lo distingue del azar (p = 0.58), así que es una pista, no una regla.

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
