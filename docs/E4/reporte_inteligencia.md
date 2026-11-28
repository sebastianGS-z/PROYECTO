# Reporte de inteligencia · precios de frutas de Colima

> Generado por `python main.py reporte` (último mes cerrado 2026-10). Versión visual e imprimible: [`tablero/inteligencia.html`](../../tablero/inteligencia.html).

## Hallazgos principales

1. Tamarindo: el valor de exportación de México en 2024 (65.34 MXN/kg) superó en 27 % al precio mayorista nacional (51.50 MXN/kg); principal comprador: USA. Es valor aduanal: descuente certificación, empaque y logística antes de comparar. (HS 081340 agrupa tamarindo y otras frutas secas.)
2. Aguacate: el valor de exportación de México en 2024 (58.13 MXN/kg) superó en 46 % al precio mayorista nacional (39.75 MXN/kg); principal comprador: USA. Es valor aduanal: descuente certificación, empaque y logística antes de comparar.
3. Plátano 2021: el productor de Colima recibió en promedio 5.31 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 11.46 MXN/kg en Guadalajara: el productor capta 46 % del precio mayorista.
4. Mango 2023: el productor de Colima recibió en promedio 5.56 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 22.98 MXN/kg en Guadalajara: el productor capta 24 % del precio mayorista.
5. Guanábana 2023: el productor de Colima recibió en promedio 6.83 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 24.76 MXN/kg en Guadalajara: el productor capta 28 % del precio mayorista.
6. Aguacate 2025: el productor de Colima recibió en promedio 17.89 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 53.66 MXN/kg en Guadalajara: el productor capta 33 % del precio mayorista.
7. Tamarindo 2025: el productor de Colima recibió en promedio 10.91 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 57.38 MXN/kg en Guadalajara: el productor capta 19 % del precio mayorista.
8. Sandía 2025: el productor de Colima recibió en promedio 6.05 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 15.47 MXN/kg en Guadalajara: el productor capta 39 % del precio mayorista.
9. Papaya 2025: el productor de Colima recibió en promedio 7.47 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 18.21 MXN/kg en Guadalajara: el productor capta 41 % del precio mayorista.
10. Limón 2025: el productor de Colima recibió en promedio 9.80 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 26.01 MXN/kg en Guadalajara: el productor capta 38 % del precio mayorista.
11. Guayaba 2025: el productor de Colima recibió en promedio 5.53 MXN/kg (SIAP) mientras el mayorista de origen Colima se cotizó en 22.25 MXN/kg en Guadalajara: el productor capta 25 % del precio mayorista.
12. Papaya Maradol - Primera: Querétaro · Mercado de Abasto pagó en promedio 5.44 MXN/kg más que Guadalajara · Mercado de Abasto en 12 meses pareados (100 % de los meses). Conviene enviar ahí solo si el flete adicional cuesta menos de 5.44 MXN/kg. Confianza alta (p < 0.001 con 12 observaciones).
13. Plátano Dominico - Primera: Tijuana · Central de Abasto INDIA pagó en promedio 21.15 MXN/kg más que Querétaro · Mercado de Abasto en 12 meses pareados (100 % de los meses). Conviene enviar ahí solo si el flete adicional cuesta menos de 21.15 MXN/kg. Confianza alta (p < 0.001 con 12 observaciones).
14. Aguacate en Guadalajara: el mes que más pagó en promedio fue junio (+28 % frente a la tendencia) y el que menos diciembre (-21 % frente a la tendencia), con 9 a 10 años por mes; patrón con confianza alta (p = 0.000).
15. Guanábana en Guadalajara: el mes que más pagó en promedio fue enero (+7 % frente a la tendencia) y el que menos agosto (-8 % frente a la tendencia), con 6 a 8 años por mes; patrón con confianza alta (p = 0.012).
16. Guayaba en Guadalajara: el mes que más pagó en promedio fue abril (+25 % frente a la tendencia) y el que menos septiembre (-18 % frente a la tendencia), con 9 a 10 años por mes; patrón con confianza alta (p = 0.000).
17. Limón en Guadalajara: el mes que más pagó en promedio fue marzo (+36 % frente a la tendencia) y el que menos noviembre (-22 % frente a la tendencia), con 9 a 10 años por mes; patrón con confianza alta (p = 0.000).
18. Mango en Guadalajara: el mes que más pagó en promedio fue diciembre (+98 % frente a la tendencia) y el que menos junio (-22 % frente a la tendencia), con 1 a 9 años por mes; patrón con confianza alta (p = 0.000).
19. Papaya en Guadalajara: el mes que más pagó en promedio fue noviembre (+10 % frente a la tendencia) y el que menos julio (-11 % frente a la tendencia), con 9 a 10 años por mes; patrón con confianza alta (p = 0.001).
20. Plátano en Guadalajara: el mes que más pagó en promedio fue febrero (+23 % frente a la tendencia) y el que menos octubre (-20 % frente a la tendencia), con 4 a 6 años por mes; patrón con confianza alta (p = 0.001).
21. Sandía en Guadalajara: el mes que más pagó en promedio fue diciembre (+11 % frente a la tendencia) y el que menos julio (-6 % frente a la tendencia), con 9 a 10 años por mes; patrón con confianza alta (p = 0.015).
22. Tamarindo en Guadalajara: el mes que más pagó en promedio fue enero (+9 % frente a la tendencia) y el que menos septiembre (-5 % frente a la tendencia), con 8 a 10 años por mes; patrón con confianza media (p = 0.153).

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
