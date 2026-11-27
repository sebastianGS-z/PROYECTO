# Preguntas del productor que el observatorio responde

> Generado por `python main.py preguntas` (último mes cerrado 2026-10). Versión interactiva con calculadora: [`tablero/preguntas.html`](../../tablero/preguntas.html).
> Cada respuesta declara su nivel de confianza (alta, media o baja) y por qué.

## Limón

### 1. ¿A cuánto se va a pagar el limón el próximo mes?

En Guadalajara · Mercado de Abasto (Limón c/semilla # 5 - Primera) se espera alrededor de **21.76 MXN/kg** para 2026-11. 4 de cada 5 veces el precio cae entre 10.34 y 33.18 MXN/kg; 19 de cada 20, entre 10.34 y 33.18.

- **Confianza:** media — error típico 17 % en 6 meses no vistos; el rango de 80 % acertó en 100 % de esos meses
- **Qué hacer:** Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.
- **Fuente:** SNIIM · modelo arima_aic · **Datos a:** 2026-10

### 2. ¿Me conviene vender ahora o esperar un mes?

Último precio observado (2026-10) en Guadalajara · Mercado de Abasto: 23.65 MXN/kg. Para 2026-11 el pronóstico es 21.76 (-8 %). Aplicando los 12 errores reales del modelo, en **67 %** de los escenarios el precio queda por encima del actual: es más probable que suba.

- **Confianza:** media — error típico 17 % en 6 meses no vistos; el rango de 80 % acertó en 100 % de esos meses; probabilidad estimada con 12 errores históricos
- **Qué hacer:** Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, vender por partes reduce el riesgo.
- **Fuente:** SNIIM · pronóstico y validación fuera de muestra · **Datos a:** 2026-10

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En Guadalajara · Mercado de Abasto el último precio (2026-10) fue 23.65 MXN/kg: más alto que el **44 %** de los últimos 36 meses. Lectura: precio en rango normal.

- **Confianza:** alta — comparación directa con 36 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2026-10

### 4. ¿En qué meses suele pagarse mejor?

En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron septiembre (+32 %), marzo (+19 %), agosto (+19 %); los que menos, diciembre (-31 %), julio (-13 %), octubre (-13 %). **Pero con 3 años la diferencia entre meses no se distingue estadísticamente del azar**: no es un patrón comprobado.

- **Confianza:** baja — prueba de Kruskal-Wallis entre meses: no se distingue del azar (p = 0.311, 36 observaciones)
- **Qué hacer:** Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.
- **Fuente:** SNIIM · índice estacional OAIC · **Datos a:** 2026-10

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Ninguna de las 8 centrales comparadas pagó significativamente más que Guadalajara · Mercado de Abasto: **Guadalajara · Mercado de Abasto es la mejor opción comprobada** con estos datos. Pagaron significativamente **menos**: San Luis Potosí · Centro de Abasto -10.72; Guadalajara · Mercado Felipe Ángeles -10.49; Aguascalientes · Centro Comercial Agropecuario -9.51; Torreón · Central de Abasto de La Laguna -8.01; Monterrey · Mercado de Abasto Estrella -3.86 MXN/kg. En 3 comparaciones la diferencia no se distingue del azar (Cd. Obregón · Central de Abasto; Gómez Palacio · Centro de Distribución y Abasto; Hermosillo · Mercado de Abasto Francisco I. Madero).

- **Confianza:** alta — 5 centrales pagan menos con diferencia comprobada (Wilcoxon / prueba de signos)
- **Qué hacer:** Mantenga Guadalajara como destino principal; otra central solo conviene con un comprador que pague por arriba de lo publicado.
- **Fuente:** SNIIM · meses pareados contra Guadalajara · Mercado de Abasto (Wilcoxon / prueba de signos) · **Datos a:** 2025-11 a 2026-10

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (producto de origen Colima; MXN/kg, mediana por central): más altas en Veracruz 22.50; Sonora 22.00; Zacatecas 22.00; Jalisco 21.67; la más baja, Chihuahua 15.00. Cotizó en 14 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

En 2025 el productor de Colima recibió en promedio **9.80 MXN/kg** (SIAP) y Guadalajara · Mercado de Abasto cotizó el producto de origen Colima en 26.01 MXN/kg: al productor le llegó el **38 %**. Los otros 16.21 MXN/kg cubren empaque, flete, mermas, comisiones e intermediación.

- **Confianza:** media — promedios anuales oficiales; 12 meses de cotización mayorista; no distingue calidades
- **Qué hacer:** Use este porcentaje para revisar si una oferta en huerta está en línea con el mercado (calculadora de arriba).
- **Fuente:** SIAP (precio medio rural) · SNIIM · **Datos a:** 2025

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 5.35, 2017: 6.24, 2018: 7.14, 2019: 6.53, 2020: 6.58, 2021: 7.90, 2022: 10.22, 2023: 14.26, 2024: 10.32, 2025: 9.80. De 2016 a 2025 cambió **+83 %** (+7.0 % por año en promedio); el año más alto fue 2023 (14.26) y el más bajo 2016 (5.35). La producción del estado cambió +45 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En Guadalajara · Mercado de Abasto el precio cambió en promedio **22 %** de un mes al siguiente. La peor caída fue de -55 % (2023-12); en 26 % de los meses cayó más de 15 % y en 37 % subió más de 15 %.

- **Confianza:** alta — 35 cambios mensuales observados
- **Qué hacer:** No comprometa toda la cosecha a un solo precio o fecha: escalone ventas o acuerde parte del volumen a precio fijo.
- **Fuente:** SNIIM · variación mensual · **Datos a:** 2026-10

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de limón en Guadalajara se repartieron así por estado de origen: Colima 50 %, Jalisco 50 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-11-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Tecomán: 206,005 t a 9.46 MXN/kg; Armería: 77,844 t a 10.98 MXN/kg; Coquimatlán: 16,762 t a 9.51 MXN/kg; Manzanillo: 11,768 t a 8.37 MXN/kg. Total Colima: 324,350 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Hay mercado para exportar?

En 2024 los países que más reportaron importar limones y limas de México fueron: USA (USD 811.3 millones, 1.15 USD/kg); Canada (USD 45.5 millones, 1.49 USD/kg); Japan (USD 10.1 millones, 4.98 USD/kg); Netherlands (USD 5.9 millones, 1.97 USD/kg).

- **Confianza:** media — dato oficial, pero agrupa limones y limas de todo México y el valor es aduanal
- **Qué hacer:** Exportar exige certificación, empaque y un comprador confirmado; empiece por un empacador exportador de la zona.
- **Fuente:** UN Comtrade (HS 080550) · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** media — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — métricas medidas automáticamente (ISO/IEC 25012)
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Papaya

### 1. ¿A cuánto se va a pagar la papaya el próximo mes?

En Guadalajara · Mercado de Abasto (Papaya Maradol - Primera) se espera alrededor de **18.45 MXN/kg** para 2026-11. 4 de cada 5 veces el precio cae entre 14.91 y 22.00 MXN/kg; 19 de cada 20, entre 14.91 y 22.00.

- **Confianza:** media — error típico 12 % en 6 meses no vistos; el rango de 80 % acertó en 67 % de esos meses
- **Qué hacer:** Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.
- **Fuente:** SNIIM · modelo arima_aic · **Datos a:** 2026-10

### 2. ¿Me conviene vender ahora o esperar un mes?

Último precio observado (2026-10) en Guadalajara · Mercado de Abasto: 18.27 MXN/kg. Para 2026-11 el pronóstico es 18.45 (+1 %). Aplicando los 12 errores reales del modelo, en **25 %** de los escenarios el precio queda por encima del actual: es más probable que baje.

- **Confianza:** media — error típico 12 % en 6 meses no vistos; el rango de 80 % acertó en 67 % de esos meses; probabilidad estimada con 12 errores históricos
- **Qué hacer:** Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, vender por partes reduce el riesgo.
- **Fuente:** SNIIM · pronóstico y validación fuera de muestra · **Datos a:** 2026-10

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En Guadalajara · Mercado de Abasto el último precio (2026-10) fue 18.27 MXN/kg: más alto que el **50 %** de los últimos 36 meses. Lectura: precio en rango normal.

- **Confianza:** alta — comparación directa con 36 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2026-10

### 4. ¿En qué meses suele pagarse mejor?

En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron noviembre (+19 %), febrero (+12 %), octubre (+11 %); los que menos, julio (-16 %), junio (-12 %), marzo (-7 %). **Pero con 3 años la diferencia entre meses no se distingue estadísticamente del azar**: no es un patrón comprobado.

- **Confianza:** baja — prueba de Kruskal-Wallis entre meses: no se distingue del azar (p = 0.260, 36 observaciones)
- **Qué hacer:** Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.
- **Fuente:** SNIIM · índice estacional OAIC · **Datos a:** 2026-10

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Pagaron **más** que Guadalajara · Mercado de Abasto, con diferencia comprobada: Querétaro · Mercado de Abasto +5.44 MXN/kg (12 meses, mayor en 100 % de ellos; flete extra máximo 5.44 MXN/kg); Zacatecas · Mercado de Abasto +3.89 MXN/kg (12 meses, mayor en 100 % de ellos; flete extra máximo 3.89 MXN/kg); San Luis Potosí · Centro de Abasto +3.31 MXN/kg (12 meses, mayor en 92 % de ellos; flete extra máximo 3.31 MXN/kg). Pagaron significativamente **menos**: Guadalajara · Mercado Felipe Ángeles -0.63 MXN/kg.

- **Confianza:** alta — p = 0.000 con 12 observaciones
- **Qué hacer:** Pida a su transportista el costo por kilo a Querétaro y réstele el costo a Guadalajara: si la diferencia es menor que el "flete extra máximo", esa central le deja más. Sume mermas por más días de viaje y confirme comprador antes de enviar.
- **Fuente:** SNIIM · meses pareados contra Guadalajara · Mercado de Abasto (Wilcoxon / prueba de signos) · **Datos a:** 2025-11 a 2026-10

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (producto de origen Colima; MXN/kg, mediana por central): más altas en Querétaro 25.00; Zacatecas 25.00; Jalisco 21.50; San Luis Potosí 21.00; la más baja, Jalisco 20.50. Cotizó en 5 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

En 2025 el productor de Colima recibió en promedio **7.47 MXN/kg** (SIAP) y Guadalajara · Mercado de Abasto cotizó el producto de origen Colima en 18.21 MXN/kg: al productor le llegó el **41 %**. Los otros 10.74 MXN/kg cubren empaque, flete, mermas, comisiones e intermediación.

- **Confianza:** media — promedios anuales oficiales; 12 meses de cotización mayorista; no distingue calidades
- **Qué hacer:** Use este porcentaje para revisar si una oferta en huerta está en línea con el mercado (calculadora de arriba).
- **Fuente:** SIAP (precio medio rural) · SNIIM · **Datos a:** 2025

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 5.77, 2017: 5.67, 2018: 7.01, 2019: 7.06, 2020: 6.85, 2021: 6.89, 2022: 6.59, 2023: 7.75, 2024: 7.41, 2025: 7.47. De 2016 a 2025 cambió **+29 %** (+2.9 % por año en promedio); el año más alto fue 2023 (7.75) y el más bajo 2017 (5.67). La producción del estado cambió +45 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En Guadalajara · Mercado de Abasto el precio cambió en promedio **13 %** de un mes al siguiente. La peor caída fue de -32 % (2024-12); en 17 % de los meses cayó más de 15 % y en 23 % subió más de 15 %.

- **Confianza:** alta — 35 cambios mensuales observados
- **Qué hacer:** No comprometa toda la cosecha a un solo precio o fecha: escalone ventas o acuerde parte del volumen a precio fijo.
- **Fuente:** SNIIM · variación mensual · **Datos a:** 2026-10

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de papaya en Guadalajara se repartieron así por estado de origen: Chiapas 33 %, Colima 33 %, Jalisco 33 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-11-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Tecomán: 81,902 t a 7.70 MXN/kg; Ixtlahuacán: 32,256 t a 7.80 MXN/kg; Colima: 31,520 t a 6.45 MXN/kg; Manzanillo: 23,345 t a 8.34 MXN/kg. Total Colima: 211,671 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Hay mercado para exportar?

El observatorio todavía no integra datos de comercio exterior para este producto.

- **Confianza:** no aplica — sin datos
- **Qué hacer:** —
- **Fuente:** UN Comtrade · **Datos a:** —

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** media — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — métricas medidas automáticamente (ISO/IEC 25012)
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Plátano

### 1. ¿A cuánto se va a pagar el plátano el próximo mes?

En Guadalajara · Mercado de Abasto (Plátano Tabasco - Primera, origen Michoacán) se espera alrededor de **7.64 MXN/kg** para 2026-11. 4 de cada 5 veces el precio cae entre 1.52 y 13.76 MXN/kg; 19 de cada 20, entre 1.52 y 13.76. No hay 36 meses de plátano de origen Colima en una central, así que es una **referencia del mercado** con fruta de otro origen.

- **Confianza:** baja — error típico 20 % en 6 meses no vistos; el rango de 80 % acertó en 67 % de esos meses
- **Qué hacer:** Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.
- **Fuente:** SNIIM · modelo holt_winters_aditivo · **Datos a:** 2026-10

### 2. ¿Me conviene vender ahora o esperar un mes?

Último precio observado (2026-10) en Guadalajara · Mercado de Abasto: 13.89 MXN/kg. Para 2026-11 el pronóstico es 7.64 (-45 %). Aplicando los 12 errores reales del modelo, en **0 %** de los escenarios el precio queda por encima del actual: es más probable que baje.

- **Confianza:** baja — error típico 20 % en 6 meses no vistos; el rango de 80 % acertó en 67 % de esos meses; probabilidad estimada con 12 errores históricos
- **Qué hacer:** Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, vender por partes reduce el riesgo.
- **Fuente:** SNIIM · pronóstico y validación fuera de muestra · **Datos a:** 2026-10

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En La Paz · Unión de Comerciantes el último precio (2026-10) fue 22.25 MXN/kg: más alto que el **42 %** de los últimos 12 meses. Lectura: precio en rango normal.

- **Confianza:** baja — comparación directa con 12 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2026-10

### 4. ¿En qué meses suele pagarse mejor?

Se necesitan al menos 24 meses en Guadalajara para estimar el patrón por mes; aún no se reúnen.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Pagaron **más** que Querétaro · Mercado de Abasto, con diferencia comprobada: Tijuana · Central de Abasto INDIA (Plátano Dominico) +21.15 MXN/kg (12 meses, mayor en 100 % de ellos; flete extra máximo 21.15 MXN/kg). Pagaron significativamente **menos**: Zacatecas · Mercado de Abasto (Plátano Chiapas) -5.73 MXN/kg. En 2 comparaciones la diferencia no se distingue del azar (San Luis Potosí · Centro de Abasto (Plátano Tabasco); Tijuana · Central de Abasto INDIA (Plátano Chiapas)).

- **Confianza:** alta — p = 0.000 con 12 observaciones
- **Qué hacer:** Pida a su transportista el costo por kilo a Tijuana y réstele el costo a Querétaro: si la diferencia es menor que el "flete extra máximo", esa central le deja más. Sume mermas por más días de viaje y confirme comprador antes de enviar.
- **Fuente:** SNIIM · meses pareados contra Querétaro · Mercado de Abasto (Wilcoxon / prueba de signos) · **Datos a:** 2025-11 a 2026-10

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (producto de origen Colima; MXN/kg, mediana por central): más altas en Baja California  43.00; Querétaro 21.88; Baja California Sur 21.67; Zacatecas 14.00; la más baja, San Luis Potosí 10.50. Cotizó en 5 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

En 2025 el productor de Colima recibió en promedio **5.21 MXN/kg** (SIAP) y Tijuana · Central de Abasto INDIA cotizó el producto de origen Colima en 29.89 MXN/kg: al productor le llegó el **17 %**. Los otros 24.68 MXN/kg cubren empaque, flete, mermas, comisiones e intermediación.

- **Confianza:** baja — promedios anuales oficiales; 2 meses de cotización mayorista; no distingue calidades
- **Qué hacer:** Use este porcentaje para revisar si una oferta en huerta está en línea con el mercado (calculadora de arriba).
- **Fuente:** SIAP (precio medio rural) · SNIIM · **Datos a:** 2025

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 2.52, 2017: 3.63, 2018: 4.36, 2019: 5.56, 2020: 5.35, 2021: 5.31, 2022: 6.15, 2023: 5.95, 2024: 5.44, 2025: 5.21. De 2016 a 2025 cambió **+107 %** (+8.4 % por año en promedio); el año más alto fue 2022 (6.15) y el más bajo 2016 (2.52). La producción del estado cambió +91 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En La Paz · Unión de Comerciantes el precio cambió en promedio **10 %** de un mes al siguiente. La peor caída fue de -17 % (2026-06); en 9 % de los meses cayó más de 15 % y en 9 % subió más de 15 %.

- **Confianza:** media — 11 cambios mensuales observados
- **Qué hacer:** No comprometa toda la cosecha a un solo precio o fecha: escalone ventas o acuerde parte del volumen a precio fijo.
- **Fuente:** SNIIM · variación mensual · **Datos a:** 2026-10

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de plátano en Guadalajara se repartieron así por estado de origen: Veracruz 50 %, Chiapas 25 %, Michoacán 25 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-11-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Tecomán: 296,573 t a 4.89 MXN/kg; Manzanillo: 64,581 t a 6.79 MXN/kg; Armería: 9,921 t a 4.59 MXN/kg; Colima: 553 t a 3.81 MXN/kg. Total Colima: 373,069 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Hay mercado para exportar?

El observatorio todavía no integra datos de comercio exterior para este producto.

- **Confianza:** no aplica — sin datos
- **Qué hacer:** —
- **Fuente:** UN Comtrade · **Datos a:** —

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** media — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — métricas medidas automáticamente (ISO/IEC 25012)
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Lo que todavía no responde

- **¿Qué plaga o enfermedad viene y cómo la controlo?** El observatorio no captura datos fitosanitarios (SENASICA). Consulte a su técnico o junta local de sanidad vegetal.
- **¿Cuánto me van a costar los fertilizantes y el diésel?** No hay fuente de costos de insumos integrada; el simulador de la vista de cliente acepta sus costos reales.
- **¿Quién me compra hoy y a qué precio exacto?** Los precios son cotizaciones de plaza publicadas por el SNIIM, no ofertas de compradores. No se publican datos de personas ni empresas.
- **¿Va a llover o hacer frío la próxima semana?** El observatorio usa clima observado (NOAA), no pronóstico meteorológico. Consulte al SMN de CONAGUA.
- **¿Me conviene un crédito o seguro agrícola?** Fuera de alcance; no es asesoría financiera.
