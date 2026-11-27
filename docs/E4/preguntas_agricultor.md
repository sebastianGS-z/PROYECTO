# Preguntas del productor que el observatorio responde

> Generado por `python main.py preguntas` (último mes cerrado 2026-10). Versión interactiva con calculadora: [`tablero/preguntas.html`](../../tablero/preguntas.html).
> Cada respuesta declara su nivel de confianza (alta, media o baja) y por qué.

## Limón

### 1. ¿A cuánto se va a pagar el limón el próximo mes?

En Guadalajara · Mercado de Abasto (Limón c/semilla # 5 - Primera) se espera alrededor de **11.81 MXN/kg** para 2026-11. 4 de cada 5 veces el precio cae entre 2.06 y 21.56 MXN/kg; 19 de cada 20, entre 2.06 y 21.56.

- **Confianza:** media — error típico 16 % en 6 meses no vistos; el rango de 80 % acertó en 83 % de esos meses; 76 meses de historia
- **Qué hacer:** Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.
- **Fuente:** SNIIM · modelo sarima_aic · **Datos a:** 2026-10

### 2. ¿Me conviene vender ahora o esperar un mes?

Último precio observado (2026-10) en Guadalajara · Mercado de Abasto: 23.65 MXN/kg. Para 2026-11 el pronóstico es 11.81 (-50 %). Aplicando los 12 errores reales del modelo, en **0 %** de los escenarios el precio queda por encima del actual: es más probable que baje.

- **Confianza:** media — error típico 16 % en 6 meses no vistos; el rango de 80 % acertó en 83 % de esos meses; 76 meses de historia; probabilidad estimada con 12 errores históricos
- **Qué hacer:** Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, vender por partes reduce el riesgo.
- **Fuente:** SNIIM · pronóstico y validación fuera de muestra · **Datos a:** 2026-10

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En Guadalajara · Mercado de Abasto el último precio (2026-10) fue 23.65 MXN/kg: más alto que el **50 %** de los últimos 117 meses. Lectura: precio en rango normal.

- **Confianza:** alta — comparación directa con 117 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2026-10

### 4. ¿En qué meses suele pagarse mejor?

En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron marzo (+36 %), abril (+26 %), septiembre (+12 %); los que menos, diciembre (-22 %), noviembre (-22 %), junio (-15 %).

- **Confianza:** alta — prueba de Kruskal-Wallis entre meses: p < 0.001 con 117 observaciones
- **Qué hacer:** Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.
- **Fuente:** SNIIM · índice estacional OAIC · **Datos a:** 2026-10

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Ninguna de las 8 centrales comparadas pagó significativamente más que Guadalajara · Mercado de Abasto: **Guadalajara · Mercado de Abasto es la mejor opción comprobada** con estos datos. Pagaron significativamente **menos**: San Luis Potosí · Centro de Abasto -10.72; Guadalajara · Mercado Felipe Ángeles -10.49; Aguascalientes · Centro Comercial Agropecuario -9.51; Torreón · Central de Abasto de La Laguna -8.01; Monterrey · Mercado de Abasto Estrella -3.86 MXN/kg. En 3 comparaciones la diferencia no se distingue del azar (Cd. Obregón · Central de Abasto; Gómez Palacio · Centro de Distribución y Abasto; Hermosillo · Mercado de Abasto Francisco I. Madero).

- **Confianza:** media — 5 centrales pagan menos con diferencia comprobada (Wilcoxon / prueba de signos)
- **Qué hacer:** Mantenga Guadalajara como destino principal; otra central solo conviene con un comprador que pague por arriba de lo publicado.
- **Fuente:** SNIIM · meses pareados contra Guadalajara · Mercado de Abasto (Wilcoxon / prueba de signos) · **Datos a:** 2025-11 a 2026-10

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (producto de origen Colima; MXN/kg, mediana por central): más altas en Veracruz 22.50; Sonora 22.00; Zacatecas 22.00; Jalisco 21.67; la más baja, Chihuahua 15.00. Cotizó en 14 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

En 2025 el productor de Colima recibió en promedio **9.80 MXN/kg** (SIAP) y Guadalajara · Mercado de Abasto cotizó el producto de origen Colima en 26.01 MXN/kg: al productor le llegó el **38 %**. Los otros 16.21 MXN/kg cubren empaque, flete, mermas, comisiones e intermediación.

- **Confianza:** alta — promedios anuales oficiales; 12 meses de cotización mayorista; no distingue calidades
- **Qué hacer:** Use este porcentaje para revisar si una oferta en huerta está en línea con el mercado (calculadora de arriba).
- **Fuente:** SIAP (precio medio rural) · SNIIM · **Datos a:** 2025

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 5.35, 2017: 6.24, 2018: 7.14, 2019: 6.53, 2020: 6.58, 2021: 7.90, 2022: 10.22, 2023: 14.26, 2024: 10.32, 2025: 9.80. De 2016 a 2025 cambió **+83 %** (+7.0 % por año en promedio); el año más alto fue 2023 (14.26) y el más bajo 2016 (5.35). La producción del estado cambió +45 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En Guadalajara · Mercado de Abasto el precio cambió en promedio **21 %** de un mes al siguiente. La peor caída fue de -55 % (2023-12); en 20 % de los meses cayó más de 15 % y en 29 % subió más de 15 %.

- **Confianza:** alta — 116 cambios mensuales observados (índice: meses / 60)
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

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 885.8 millones a 50 países (código HS 080550). Principales compradores: USA (USD 811.3 millones, 21.06 MXN/kg, +50 % desde 2019); Canada (USD 45.5 millones, 27.27 MXN/kg, +22 % desde 2019); Japan (USD 10.1 millones, 91.17 MXN/kg, +0 % desde 2019); Netherlands (USD 5.9 millones, 36.15 MXN/kg, -82 % desde 2019). El valor promedio de exportación fue **21.73 MXN/kg** frente a 24.94 MXN/kg en las centrales nacionales (origen Colima, últimos 12 meses): **-13 %**. Mercados grandes donde México vende poco: Germany (importa USD 428 millones; México tiene 0.5 %); Netherlands (importa USD 270 millones; México tiene 2.2 %); France (importa USD 245 millones; México tiene 0.9 %). Nota: HS 080550 agrupa limones y limas.

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor); el código HS agrupa varias frutas
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Papaya

### 1. ¿A cuánto se va a pagar la papaya el próximo mes?

En Guadalajara · Mercado de Abasto (Papaya Maradol - Primera) se espera alrededor de **17.97 MXN/kg** para 2026-11. 4 de cada 5 veces el precio cae entre 14.69 y 21.25 MXN/kg; 19 de cada 20, entre 14.69 y 21.25.

- **Confianza:** alta — error típico 3 % en 6 meses no vistos; el rango de 80 % acertó en 100 % de esos meses; 76 meses de historia
- **Qué hacer:** Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.
- **Fuente:** SNIIM · modelo arima_aic · **Datos a:** 2026-10

### 2. ¿Me conviene vender ahora o esperar un mes?

Último precio observado (2026-10) en Guadalajara · Mercado de Abasto: 18.27 MXN/kg. Para 2026-11 el pronóstico es 17.97 (-2 %). Aplicando los 12 errores reales del modelo, en **25 %** de los escenarios el precio queda por encima del actual: es más probable que baje.

- **Confianza:** alta — error típico 3 % en 6 meses no vistos; el rango de 80 % acertó en 100 % de esos meses; 76 meses de historia; probabilidad estimada con 12 errores históricos
- **Qué hacer:** Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, vender por partes reduce el riesgo.
- **Fuente:** SNIIM · pronóstico y validación fuera de muestra · **Datos a:** 2026-10

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En Guadalajara · Mercado de Abasto el último precio (2026-10) fue 18.27 MXN/kg: más alto que el **84 %** de los últimos 119 meses. Lectura: precio alto respecto a su historia: buen momento para vender, mal momento para comprar inventario.

- **Confianza:** alta — comparación directa con 119 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2026-10

### 4. ¿En qué meses suele pagarse mejor?

En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron noviembre (+10 %), febrero (+8 %), octubre (+6 %); los que menos, julio (-10 %), junio (-9 %), marzo (-5 %).

- **Confianza:** alta — prueba de Kruskal-Wallis entre meses: p = 0.001 con 119 observaciones
- **Qué hacer:** Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.
- **Fuente:** SNIIM · índice estacional OAIC · **Datos a:** 2026-10

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Pagaron **más** que Guadalajara · Mercado de Abasto, con diferencia comprobada: Querétaro · Mercado de Abasto +5.44 MXN/kg (12 meses, mayor en 100 % de ellos; flete extra máximo 5.44 MXN/kg); Zacatecas · Mercado de Abasto +3.89 MXN/kg (12 meses, mayor en 100 % de ellos; flete extra máximo 3.89 MXN/kg); San Luis Potosí · Centro de Abasto +3.31 MXN/kg (12 meses, mayor en 92 % de ellos; flete extra máximo 3.31 MXN/kg). Pagaron significativamente **menos**: Guadalajara · Mercado Felipe Ángeles -0.63 MXN/kg.

- **Confianza:** alta — p < 0.001 con 12 observaciones
- **Qué hacer:** Pida a su transportista el costo por kilo a Querétaro y réstele el costo a Guadalajara: si la diferencia es menor que el "flete extra máximo", esa central le deja más. Sume mermas por más días de viaje y confirme comprador antes de enviar.
- **Fuente:** SNIIM · meses pareados contra Guadalajara · Mercado de Abasto (Wilcoxon / prueba de signos) · **Datos a:** 2025-11 a 2026-10

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (producto de origen Colima; MXN/kg, mediana por central): más altas en Querétaro 25.00; Zacatecas 25.00; Jalisco 21.50; San Luis Potosí 21.00; la más baja, Jalisco 20.50. Cotizó en 5 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

En 2025 el productor de Colima recibió en promedio **7.47 MXN/kg** (SIAP) y Guadalajara · Mercado de Abasto cotizó el producto de origen Colima en 18.21 MXN/kg: al productor le llegó el **41 %**. Los otros 10.74 MXN/kg cubren empaque, flete, mermas, comisiones e intermediación.

- **Confianza:** alta — promedios anuales oficiales; 12 meses de cotización mayorista; no distingue calidades
- **Qué hacer:** Use este porcentaje para revisar si una oferta en huerta está en línea con el mercado (calculadora de arriba).
- **Fuente:** SIAP (precio medio rural) · SNIIM · **Datos a:** 2025

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 5.77, 2017: 5.67, 2018: 7.01, 2019: 7.06, 2020: 6.85, 2021: 6.89, 2022: 6.59, 2023: 7.75, 2024: 7.41, 2025: 7.47. De 2016 a 2025 cambió **+29 %** (+2.9 % por año en promedio); el año más alto fue 2023 (7.75) y el más bajo 2017 (5.67). La producción del estado cambió +45 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En Guadalajara · Mercado de Abasto el precio cambió en promedio **10 %** de un mes al siguiente. La peor caída fue de -32 % (2024-12); en 9 % de los meses cayó más de 15 % y en 15 % subió más de 15 %.

- **Confianza:** alta — 118 cambios mensuales observados (índice: meses / 60)
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

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 153.9 millones a 12 países (código HS 080720). Principales compradores: USA (USD 135.4 millones, 12.43 MXN/kg, +47 % desde 2019); Canada (USD 17.4 millones, 27.10 MXN/kg, +61 % desde 2019); Germany (USD 1.0 millones, 49.36 MXN/kg, +93 % desde 2019); Netherlands (USD 0.0 millones, 52.14 MXN/kg, -61 % desde 2019). El valor promedio de exportación fue **13.32 MXN/kg** frente a 20.40 MXN/kg en las centrales nacionales (origen Colima, últimos 12 meses): **-35 %**. Mercados grandes donde México vende poco: Portugal (importa USD 34 millones; México tiene 0.0 %); Germany (importa USD 26 millones; México tiene 4.0 %); Spain (importa USD 22 millones; México tiene 0.0 %).

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor)
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Plátano

### 1. ¿A cuánto se va a pagar el plátano el próximo mes?

En Guadalajara · Mercado de Abasto (Plátano Tabasco - Primera, origen Michoacán) se espera alrededor de **8.09 MXN/kg** para 2026-11. 4 de cada 5 veces el precio cae entre 2.98 y 13.20 MXN/kg; 19 de cada 20, entre 2.98 y 13.20. No hay 36 meses de plátano de origen Colima en una central, así que es una **referencia del mercado** con fruta de otro origen.

- **Confianza:** baja — error típico 19 % en 6 meses no vistos; el rango de 80 % acertó en 67 % de esos meses; 50 meses de historia
- **Qué hacer:** Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.
- **Fuente:** SNIIM · modelo holt_winters_aditivo · **Datos a:** 2026-10

### 2. ¿Me conviene vender ahora o esperar un mes?

Último precio observado (2026-10) en Guadalajara · Mercado de Abasto: 13.89 MXN/kg. Para 2026-11 el pronóstico es 8.09 (-42 %). Aplicando los 12 errores reales del modelo, en **0 %** de los escenarios el precio queda por encima del actual: es más probable que baje.

- **Confianza:** baja — error típico 19 % en 6 meses no vistos; el rango de 80 % acertó en 67 % de esos meses; 50 meses de historia; probabilidad estimada con 12 errores históricos
- **Qué hacer:** Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, vender por partes reduce el riesgo.
- **Fuente:** SNIIM · pronóstico y validación fuera de muestra · **Datos a:** 2026-10

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En Guadalajara · Mercado de Abasto el último precio (2021-11) fue 11.53 MXN/kg: más alto que el **87 %** de los últimos 60 meses. Lectura: precio alto respecto a su historia: buen momento para vender, mal momento para comprar inventario.

- **Confianza:** alta — comparación directa con 60 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2021-11

### 4. ¿En qué meses suele pagarse mejor?

En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron febrero (+23 %), marzo (+16 %), julio (+14 %); los que menos, octubre (-20 %), diciembre (-19 %), septiembre (-17 %).

- **Confianza:** alta — prueba de Kruskal-Wallis entre meses: p < 0.001 con 60 observaciones
- **Qué hacer:** Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.
- **Fuente:** SNIIM · índice estacional OAIC · **Datos a:** 2026-10

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Pagaron **más** que Querétaro · Mercado de Abasto, con diferencia comprobada: Tijuana · Central de Abasto INDIA (Plátano Dominico) +21.15 MXN/kg (12 meses, mayor en 100 % de ellos; flete extra máximo 21.15 MXN/kg). Pagaron significativamente **menos**: Zacatecas · Mercado de Abasto (Plátano Chiapas) -5.73 MXN/kg. En 1 comparaciones la diferencia no se distingue del azar (Tijuana · Central de Abasto INDIA (Plátano Chiapas)).

- **Confianza:** alta — p < 0.001 con 12 observaciones
- **Qué hacer:** Pida a su transportista el costo por kilo a Tijuana y réstele el costo a Querétaro: si la diferencia es menor que el "flete extra máximo", esa central le deja más. Sume mermas por más días de viaje y confirme comprador antes de enviar.
- **Fuente:** SNIIM · meses pareados contra Querétaro · Mercado de Abasto (Wilcoxon / prueba de signos) · **Datos a:** 2025-11 a 2026-10

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (producto de origen Colima; MXN/kg, mediana por central): más altas en Baja California  43.00; Querétaro 21.88; Baja California Sur 21.67; Zacatecas 14.00; la más baja, San Luis Potosí 10.50. Cotizó en 5 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

En 2021 el productor de Colima recibió en promedio **5.31 MXN/kg** (SIAP) y Guadalajara · Mercado de Abasto cotizó el producto de origen Colima en 11.46 MXN/kg: al productor le llegó el **46 %**. Los otros 6.15 MXN/kg cubren empaque, flete, mermas, comisiones e intermediación.

- **Confianza:** alta — promedios anuales oficiales; 11 meses de cotización mayorista; no distingue calidades
- **Qué hacer:** Use este porcentaje para revisar si una oferta en huerta está en línea con el mercado (calculadora de arriba).
- **Fuente:** SIAP (precio medio rural) · SNIIM · **Datos a:** 2021

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 2.52, 2017: 3.63, 2018: 4.36, 2019: 5.56, 2020: 5.35, 2021: 5.31, 2022: 6.15, 2023: 5.95, 2024: 5.44, 2025: 5.21. De 2016 a 2025 cambió **+107 %** (+8.4 % por año en promedio); el año más alto fue 2022 (6.15) y el más bajo 2016 (2.52). La producción del estado cambió +91 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En Guadalajara · Mercado de Abasto el precio cambió en promedio **14 %** de un mes al siguiente. La peor caída fue de -26 % (2017-08); en 17 % de los meses cayó más de 15 % y en 19 % subió más de 15 %.

- **Confianza:** alta — 59 cambios mensuales observados (índice: meses / 60)
- **Qué hacer:** No comprometa toda la cosecha a un solo precio o fecha: escalone ventas o acuerde parte del volumen a precio fijo.
- **Fuente:** SNIIM · variación mensual · **Datos a:** 2021-11

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

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 299.0 millones a 21 países (código HS 080390). Principales compradores: USA (USD 197.9 millones, 12.27 MXN/kg, -19 % desde 2019); Japan (USD 62.3 millones, 17.95 MXN/kg, +30 % desde 2019); Canada (USD 24.4 millones, 17.56 MXN/kg, +24 % desde 2019); China (USD 13.3 millones, 16.86 MXN/kg). El valor promedio de exportación fue **13.68 MXN/kg** frente a 21.56 MXN/kg en las centrales nacionales (origen Colima, últimos 12 meses): **-37 %**. Mercados grandes donde México vende poco: USA (importa USD 2,829 millones; México tiene 7.0 %); Germany (importa USD 1,090 millones; México tiene 0.0 %); Japan (importa USD 973 millones; México tiene 6.4 %). Nota: HS 080390 son plátanos frescos o secos, excepto plátano macho.

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor); el código HS agrupa varias frutas
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Mango

### 1. ¿A cuánto se va a pagar el mango el próximo mes?

Todavía no hay pronóstico para el mango: se exigen 36 meses continuos de una misma serie y aún no se reúnen.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Use el precio actual por central (pregunta 6) como referencia.
- **Fuente:** Criterio de elegibilidad del observatorio · **Datos a:** —

### 2. ¿Me conviene vender ahora o esperar un mes?

No hay pronóstico validado para estimarlo.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Compare el precio de hoy con su historia (pregunta 2).
- **Fuente:** — · **Datos a:** —

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En Guadalajara · Mercado de Abasto el último precio (2026-08) fue 38.74 MXN/kg: más alto que el **95 %** de los últimos 63 meses. Lectura: precio alto respecto a su historia: buen momento para vender, mal momento para comprar inventario. (Referencia de mercado: no hay cotizaciones de esta fruta con origen Colima; se usa la fruta de todos los orígenes en la central.)

- **Confianza:** alta — comparación directa con 63 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2026-08

### 4. ¿En qué meses suele pagarse mejor?

En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron diciembre (+98 %), enero (+55 %), febrero (+15 %); los que menos, junio (-23 %), mayo (-17 %), julio (-10 %). (Referencia de mercado: no hay cotizaciones de esta fruta con origen Colima; se usa la fruta de todos los orígenes en la central.)

- **Confianza:** alta — prueba de Kruskal-Wallis entre meses: p < 0.001 con 63 observaciones
- **Qué hacer:** Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.
- **Fuente:** SNIIM · índice estacional OAIC · **Datos a:** 2026-10

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Todavía no hay al menos 3 meses en que dos centrales coticen el mismo producto de origen Colima. La captura diaria del catálogo nacional acumula esa historia.

- **Confianza:** no aplica — sin meses pareados
- **Qué hacer:** Mientras tanto compare precios del día por central (pregunta 6).
- **Fuente:** SNIIM · **Datos a:** —

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (todos los orígenes; MXN/kg, mediana por central): más altas en Quintana Roo 53.00; Michoacán 47.00; Veracruz 45.00; Coahuila 43.43; la más baja, Sonora 21.67. Cotizó en 12 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

No hay un año común entre el precio rural SIAP y cotizaciones de origen Colima en alguna central para este producto.

- **Confianza:** no aplica — sin año común
- **Qué hacer:** —
- **Fuente:** SIAP · SNIIM · **Datos a:** —

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 3.42, 2017: 3.77, 2018: 3.68, 2019: 4.14, 2020: 4.09, 2021: 3.84, 2022: 5.78, 2023: 5.56, 2024: 4.97, 2025: 5.23. De 2016 a 2025 cambió **+53 %** (+4.8 % por año en promedio); el año más alto fue 2022 (5.78) y el más bajo 2016 (3.42). La producción del estado cambió +28 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En Guadalajara · Mercado de Abasto el precio cambió en promedio **17 %** de un mes al siguiente. La peor caída fue de -51 % (2023-02); en 16 % de los meses cayó más de 15 % y en 21 % subió más de 15 %. (Referencia de mercado: no hay cotizaciones de esta fruta con origen Colima; se usa la fruta de todos los orígenes en la central.)

- **Confianza:** alta — 62 cambios mensuales observados (índice: meses / 60)
- **Qué hacer:** No comprometa toda la cosecha a un solo precio o fecha: escalone ventas o acuerde parte del volumen a precio fijo.
- **Fuente:** SNIIM · variación mensual · **Datos a:** 2026-08

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de mango en Guadalajara se repartieron así por estado de origen: Nayarit 100 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-08-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Manzanillo: 30,022 t a 5.38 MXN/kg; Tecomán: 20,666 t a 4.91 MXN/kg; Armería: 6,149 t a 6.33 MXN/kg; Coquimatlán: 3,537 t a 4.11 MXN/kg. Total Colima: 63,376 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 725.1 millones a 54 países (código HS 080450). Principales compradores: USA (USD 571.3 millones, 27.37 MXN/kg, +53 % desde 2019); Canada (USD 101.1 millones, 38.75 MXN/kg, +47 % desde 2019); Spain (USD 13.8 millones, 101.09 MXN/kg, +85 % desde 2019); Germany (USD 10.6 millones, 72.55 MXN/kg, +572 % desde 2019). El valor promedio de exportación fue **30.08 MXN/kg** frente a 30.49 MXN/kg en las centrales nacionales (todos los orígenes, últimos 12 meses): **-1 %**. Mercados grandes donde México vende poco: China (importa USD 676 millones; México tiene 0.0 %); Netherlands (importa USD 309 millones; México tiene 0.6 %); United Kingdom (importa USD 285 millones; México tiene 1.7 %). Nota: HS 080450 agrupa guayaba, mango y mangostán.

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor); el código HS agrupa varias frutas
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Coco

### 1. ¿A cuánto se va a pagar el coco el próximo mes?

Todavía no hay pronóstico para el coco: se exigen 36 meses continuos de una misma serie y aún no se reúnen.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Use el precio actual por central (pregunta 6) como referencia.
- **Fuente:** Criterio de elegibilidad del observatorio · **Datos a:** —

### 2. ¿Me conviene vender ahora o esperar un mes?

No hay pronóstico validado para estimarlo.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Compare el precio de hoy con su historia (pregunta 2).
- **Fuente:** — · **Datos a:** —

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

No hay al menos 12 meses de historia de origen Colima para comparar.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 4. ¿En qué meses suele pagarse mejor?

Se necesitan al menos 24 meses en Guadalajara para estimar el patrón por mes; aún no se reúnen.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Todavía no hay al menos 3 meses en que dos centrales coticen el mismo producto de origen Colima. La captura diaria del catálogo nacional acumula esa historia.

- **Confianza:** no aplica — sin meses pareados
- **Qué hacer:** Mientras tanto compare precios del día por central (pregunta 6).
- **Fuente:** SNIIM · **Datos a:** —

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

La última tabla nacional no trae cotizaciones por kilo de este producto.

- **Confianza:** no aplica — sin cotizaciones
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 7. De lo que paga la central, ¿cuánto le llega al productor?

No hay un año común entre el precio rural SIAP y cotizaciones de origen Colima en alguna central para este producto.

- **Confianza:** no aplica — sin año común
- **Qué hacer:** —
- **Fuente:** SIAP · SNIIM · **Datos a:** —

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 3.15, 2017: 4.73, 2018: 5.30, 2019: 4.25, 2022: 6.09, 2023: 5.81, 2024: 7.06, 2025: 7.70. De 2016 a 2025 cambió **+145 %** (+10.5 % por año en promedio); el año más alto fue 2025 (7.70) y el más bajo 2016 (3.15). La producción del estado cambió +45 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 8 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

No hay serie de origen Colima en ninguna central para medirlo.

- **Confianza:** no aplica — sin serie
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de coco en Guadalajara se repartieron así por estado de origen: Colima 100 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-10-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Manzanillo: 5,876 t a 7.76 MXN/kg; Coquimatlán: 1,047 t a 7.42 MXN/kg; Colima: 200 t a 7.34 MXN/kg. Total Colima: 7,123 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 31.1 millones a 4 países (código HS 080119). Principales compradores: USA (USD 30.9 millones, 15.92 MXN/kg, +89 % desde 2019); Canada (USD 0.3 millones, 30.48 MXN/kg, +10 % desde 2019); Honduras (USD 0.0 millones, 47.13 MXN/kg, -75 % desde 2019); Hungary (USD 0.0 millones, 179.22 MXN/kg). Mercados grandes donde México vende poco: Thailand (importa USD 138 millones; México tiene 0.0 %); Malaysia (importa USD 78 millones; México tiene 0.0 %); Singapore (importa USD 23 millones; México tiene 0.0 %). Nota: HS 080119: cocos frescos.

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor); el código HS agrupa varias frutas
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Tamarindo

### 1. ¿A cuánto se va a pagar el tamarindo el próximo mes?

En Colima · Centros de distribución (Tamarindo - Primera) se espera alrededor de **42.19 MXN/kg** para 2026-11. 4 de cada 5 veces el precio cae entre 40.97 y 43.41 MXN/kg; 19 de cada 20, entre 40.97 y 43.41.

- **Confianza:** alta — error típico 1 % en 6 meses no vistos; el rango de 80 % acertó en 100 % de esos meses; 36 meses de historia
- **Qué hacer:** Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.
- **Fuente:** SNIIM · modelo suavizamiento_simple · **Datos a:** 2026-10

### 2. ¿Me conviene vender ahora o esperar un mes?

Último precio observado (2026-10) en Colima · Centros de distribución: 42.22 MXN/kg. Para 2026-11 el pronóstico es 42.19 (-0 %). Aplicando los 12 errores reales del modelo, en **17 %** de los escenarios el precio queda por encima del actual: es más probable que baje.

- **Confianza:** alta — error típico 1 % en 6 meses no vistos; el rango de 80 % acertó en 100 % de esos meses; 36 meses de historia; probabilidad estimada con 12 errores históricos
- **Qué hacer:** Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, vender por partes reduce el riesgo.
- **Fuente:** SNIIM · pronóstico y validación fuera de muestra · **Datos a:** 2026-10

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En Colima · Centros de distribución el último precio (2026-10) fue 42.22 MXN/kg: más alto que el **89 %** de los últimos 36 meses. Lectura: precio alto respecto a su historia: buen momento para vender, mal momento para comprar inventario.

- **Confianza:** media — comparación directa con 36 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2026-10

### 4. ¿En qué meses suele pagarse mejor?

En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron enero (+13 %), diciembre (+8 %), noviembre (+4 %); los que menos, septiembre (-7 %), marzo (-4 %), abril (-3 %). **Pero con 3 años la diferencia entre meses no se distingue estadísticamente del azar**: no es un patrón comprobado.

- **Confianza:** baja — prueba de Kruskal-Wallis entre meses: no se distingue del azar (p = 0.577, 27 observaciones)
- **Qué hacer:** Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.
- **Fuente:** SNIIM · índice estacional OAIC · **Datos a:** 2026-10

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Ninguna de las 1 centrales comparadas pagó significativamente más que Guadalajara · Mercado de Abasto: **Guadalajara · Mercado de Abasto es la mejor opción comprobada** con estos datos. Pagaron significativamente **menos**: Colima · Centros de distribución -12.26 MXN/kg.

- **Confianza:** alta — 1 centrales pagan menos con diferencia comprobada (Wilcoxon / prueba de signos)
- **Qué hacer:** Mantenga Guadalajara como destino principal; otra central solo conviene con un comprador que pague por arriba de lo publicado.
- **Fuente:** SNIIM · meses pareados contra Guadalajara · Mercado de Abasto (Wilcoxon / prueba de signos) · **Datos a:** 2023-11 a 2026-01

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (producto de origen Colima; MXN/kg, mediana por central): más altas en Jalisco 92.50; Zacatecas 70.00; Coahuila 67.00; Nuevo León 60.00; la más baja, San Luis Potosí 58.00. Cotizó en 5 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

No hay un año común entre el precio rural SIAP y cotizaciones de origen Colima en alguna central para este producto.

- **Confianza:** no aplica — sin año común
- **Qué hacer:** —
- **Fuente:** SIAP · SNIIM · **Datos a:** —

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 6.82, 2017: 6.22, 2018: 6.18, 2019: 6.23, 2022: 9.92, 2023: 13.23, 2024: 10.80, 2025: 10.91. De 2016 a 2025 cambió **+60 %** (+5.4 % por año en promedio); el año más alto fue 2023 (13.23) y el más bajo 2018 (6.18). La producción del estado cambió +3 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 8 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En Guadalajara · Mercado de Abasto el precio cambió en promedio **7 %** de un mes al siguiente. La peor caída fue de -10 % (2024-05); en 0 % de los meses cayó más de 15 % y en 12 % subió más de 15 %.

- **Confianza:** baja — 26 cambios mensuales observados (índice: meses / 60)
- **Qué hacer:** No comprometa toda la cosecha a un solo precio o fecha: escalone ventas o acuerde parte del volumen a precio fijo.
- **Fuente:** SNIIM · variación mensual · **Datos a:** 2026-01

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de tamarindo en Guadalajara se repartieron así por estado de origen: Jalisco 65 %, Colima 19 %, Baja California Sur 16 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-10-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Coquimatlán: 4,941 t a 11.28 MXN/kg; Colima: 2,426 t a 8.00 MXN/kg; Tecomán: 1,333 t a 13.71 MXN/kg; Ixtlahuacán: 1,251 t a 15.14 MXN/kg. Total Colima: 12,622 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 5.1 millones a 22 países (código HS 081340). Principales compradores: USA (USD 4.4 millones, 58.83 MXN/kg, -30 % desde 2019); Canada (USD 0.5 millones, 273.91 MXN/kg, -43 % desde 2019); Saudi Arabia (USD 0.1 millones, 123.20 MXN/kg); United Kingdom (USD 0.1 millones, 107.53 MXN/kg). El valor promedio de exportación fue **65.34 MXN/kg** frente a 51.50 MXN/kg en las centrales nacionales (origen Colima, últimos 12 meses): **+27 %**. Mercados grandes donde México vende poco: USA (importa USD 208 millones; México tiene 2.1 %); China (importa USD 196 millones; México tiene 0.0 %); Germany (importa USD 127 millones; México tiene 0.0 %). Nota: HS 081340 agrupa tamarindo y otras frutas secas.

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor); el código HS agrupa varias frutas
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Guayaba

### 1. ¿A cuánto se va a pagar la guayaba el próximo mes?

En Guadalajara · Mercado de Abasto (Guayaba - Primera, origen Michoacán) se espera alrededor de **21.92 MXN/kg** para 2026-11. 4 de cada 5 veces el precio cae entre 15.84 y 28.01 MXN/kg; 19 de cada 20, entre 15.84 y 28.01. No hay 36 meses de plátano de origen Colima en una central, así que es una **referencia del mercado** con fruta de otro origen.

- **Confianza:** media — error típico 6 % en 6 meses no vistos; el rango de 80 % acertó en 100 % de esos meses; 36 meses de historia
- **Qué hacer:** Planee con el rango, no con el número exacto; si su costo de producción está cerca del mínimo del rango, asegure parte del volumen con un acuerdo de precio.
- **Fuente:** SNIIM · modelo arima_aic · **Datos a:** 2026-10

### 2. ¿Me conviene vender ahora o esperar un mes?

Último precio observado (2026-10) en Guadalajara · Mercado de Abasto: 21.59 MXN/kg. Para 2026-11 el pronóstico es 21.92 (+2 %). Aplicando los 12 errores reales del modelo, en **58 %** de los escenarios el precio queda por encima del actual: subir o bajar es casi igual de probable.

- **Confianza:** media — error típico 6 % en 6 meses no vistos; el rango de 80 % acertó en 100 % de esos meses; 36 meses de historia; probabilidad estimada con 12 errores históricos
- **Qué hacer:** Esperar solo tiene sentido si la fruta aguanta en el árbol sin perder calidad y si la probabilidad es claramente mayor a 50 %; si es cercana a 50 %, vender por partes reduce el riesgo.
- **Fuente:** SNIIM · pronóstico y validación fuera de muestra · **Datos a:** 2026-10

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

En Colima · Centros de distribución el último precio (2026-10) fue 25.00 MXN/kg: más alto que el **0 %** de los últimos 36 meses. Lectura: precio bajo respecto a su historia: conviene revisar si se puede esperar o almacenar. (Referencia de mercado: no hay cotizaciones de esta fruta con origen Colima; se usa la fruta de todos los orígenes en la central.)

- **Confianza:** media — comparación directa con 36 meses observados
- **Qué hacer:** Por encima del percentil 75 es buen momento para vender; por debajo del 25, evalúe esperar o almacenar.
- **Fuente:** SNIIM · historia mensual de origen Colima · **Datos a:** 2026-10

### 4. ¿En qué meses suele pagarse mejor?

En Guadalajara, frente a su tendencia, los meses que más pagaron en promedio fueron mayo (+34 %), abril (+23 %), junio (+19 %); los que menos, febrero (-21 %), enero (-19 %), diciembre (-13 %). (Referencia de mercado: no hay cotizaciones de esta fruta con origen Colima; se usa la fruta de todos los orígenes en la central.)

- **Confianza:** media — prueba de Kruskal-Wallis entre meses: p = 0.015 con 36 observaciones
- **Qué hacer:** Úselo como pista para planear, no para decidir sola la fecha de corte; combine con el pronóstico del próximo mes.
- **Fuente:** SNIIM · índice estacional OAIC · **Datos a:** 2026-10

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Todavía no hay al menos 3 meses en que dos centrales coticen el mismo producto de origen Colima. La captura diaria del catálogo nacional acumula esa historia.

- **Confianza:** no aplica — sin meses pareados
- **Qué hacer:** Mientras tanto compare precios del día por central (pregunta 6).
- **Fuente:** SNIIM · **Datos a:** —

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (todos los orígenes; MXN/kg, mediana por central): más altas en Quintana Roo 49.00; Guerrero 40.00; Chihuahua 40.00; Baja California Sur 36.36; la más baja, México 9.23. Cotizó en 28 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

No hay un año común entre el precio rural SIAP y cotizaciones de origen Colima en alguna central para este producto.

- **Confianza:** no aplica — sin año común
- **Qué hacer:** —
- **Fuente:** SIAP · SNIIM · **Datos a:** —

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 4.95, 2017: 5.48, 2018: 5.66, 2019: 5.64, 2020: 5.82, 2021: 5.22, 2022: 4.39, 2023: 5.14, 2024: 5.59, 2025: 5.53. De 2016 a 2025 cambió **+12 %** (+1.2 % por año en promedio); el año más alto fue 2020 (5.82) y el más bajo 2022 (4.39). La producción del estado cambió +122 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

En Guadalajara · Mercado de Abasto el precio cambió en promedio **14 %** de un mes al siguiente. La peor caída fue de -32 % (2024-08); en 14 % de los meses cayó más de 15 % y en 29 % subió más de 15 %. (Referencia de mercado: no hay cotizaciones de esta fruta con origen Colima; se usa la fruta de todos los orígenes en la central.)

- **Confianza:** media — 35 cambios mensuales observados (índice: meses / 60)
- **Qué hacer:** No comprometa toda la cosecha a un solo precio o fecha: escalone ventas o acuerde parte del volumen a precio fijo.
- **Fuente:** SNIIM · variación mensual · **Datos a:** 2026-10

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de guayaba en Guadalajara se repartieron así por estado de origen: Michoacán 100 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-10-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Comala: 301 t a 5.47 MXN/kg; Ixtlahuacán: 75 t a 5.64 MXN/kg; Colima: 10 t a 6.27 MXN/kg. Total Colima: 386 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 725.1 millones a 54 países (código HS 080450). Principales compradores: USA (USD 571.3 millones, 27.37 MXN/kg, +53 % desde 2019); Canada (USD 101.1 millones, 38.75 MXN/kg, +47 % desde 2019); Spain (USD 13.8 millones, 101.09 MXN/kg, +85 % desde 2019); Germany (USD 10.6 millones, 72.55 MXN/kg, +572 % desde 2019). El valor promedio de exportación fue **30.08 MXN/kg** frente a 23.66 MXN/kg en las centrales nacionales (todos los orígenes, últimos 12 meses): **+27 %**. Mercados grandes donde México vende poco: China (importa USD 676 millones; México tiene 0.0 %); Netherlands (importa USD 309 millones; México tiene 0.6 %); United Kingdom (importa USD 285 millones; México tiene 1.7 %). Nota: HS 080450 agrupa guayaba, mango y mangostán.

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor); el código HS agrupa varias frutas
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Aguacate

### 1. ¿A cuánto se va a pagar el aguacate el próximo mes?

Todavía no hay pronóstico para el aguacate: se exigen 36 meses continuos de una misma serie y aún no se reúnen.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Use el precio actual por central (pregunta 6) como referencia.
- **Fuente:** Criterio de elegibilidad del observatorio · **Datos a:** —

### 2. ¿Me conviene vender ahora o esperar un mes?

No hay pronóstico validado para estimarlo.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Compare el precio de hoy con su historia (pregunta 2).
- **Fuente:** — · **Datos a:** —

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

No hay al menos 12 meses de historia de origen Colima para comparar.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 4. ¿En qué meses suele pagarse mejor?

Se necesitan al menos 24 meses en Guadalajara para estimar el patrón por mes; aún no se reúnen.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Todavía no hay al menos 3 meses en que dos centrales coticen el mismo producto de origen Colima. La captura diaria del catálogo nacional acumula esa historia.

- **Confianza:** no aplica — sin meses pareados
- **Qué hacer:** Mientras tanto compare precios del día por central (pregunta 6).
- **Fuente:** SNIIM · **Datos a:** —

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (todos los orígenes; MXN/kg, mediana por central): más altas en Sinaloa 94.00; Sinaloa 93.00; Tamaulipas 90.00; Guerrero 75.00; la más baja, Campeche 17.12. Cotizó en 37 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

No hay un año común entre el precio rural SIAP y cotizaciones de origen Colima en alguna central para este producto.

- **Confianza:** no aplica — sin año común
- **Qué hacer:** —
- **Fuente:** SIAP · SNIIM · **Datos a:** —

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 15.78, 2017: 15.06, 2018: 16.58, 2019: 16.88, 2020: 16.01, 2021: 17.77, 2022: 19.52, 2023: 17.47, 2024: 17.35, 2025: 17.89. De 2016 a 2025 cambió **+13 %** (+1.4 % por año en promedio); el año más alto fue 2022 (19.52) y el más bajo 2017 (15.06). La producción del estado cambió +19 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

Hay muy pocos meses (0) para medir variaciones; se necesitan al menos 6.

- **Confianza:** no aplica — 0 cambios mensuales
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de aguacate en Guadalajara se repartieron así por estado de origen: Jalisco 50 %, Michoacán 50 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-10-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Comala: 3,405 t a 17.47 MXN/kg; Cuauhtémoc: 2,294 t a 17.39 MXN/kg; Manzanillo: 781 t a 17.46 MXN/kg; Minatitlán: 771 t a 20.57 MXN/kg. Total Colima: 8,043 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 4,024.2 millones a 56 países (código HS 080440). Principales compradores: USA (USD 3,494.3 millones, 60.03 MXN/kg, +38 % desde 2019); Canada (USD 284.7 millones, 50.20 MXN/kg, +27 % desde 2019); Japan (USD 107.8 millones, 55.56 MXN/kg, -50 % desde 2019); Honduras (USD 27.8 millones, 36.77 MXN/kg, +94 % desde 2019). El valor promedio de exportación fue **58.13 MXN/kg** frente a 35.43 MXN/kg en las centrales nacionales (todos los orígenes, últimos 12 meses): **+64 %**. Mercados grandes donde México vende poco: Netherlands (importa USD 1,299 millones; México tiene 0.4 %); France (importa USD 696 millones; México tiene 0.7 %); Spain (importa USD 665 millones; México tiene 1.2 %).

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor)
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Sandía

### 1. ¿A cuánto se va a pagar la sandía el próximo mes?

Todavía no hay pronóstico para la sandía: se exigen 36 meses continuos de una misma serie y aún no se reúnen.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Use el precio actual por central (pregunta 6) como referencia.
- **Fuente:** Criterio de elegibilidad del observatorio · **Datos a:** —

### 2. ¿Me conviene vender ahora o esperar un mes?

No hay pronóstico validado para estimarlo.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Compare el precio de hoy con su historia (pregunta 2).
- **Fuente:** — · **Datos a:** —

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

No hay al menos 12 meses de historia de origen Colima para comparar.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 4. ¿En qué meses suele pagarse mejor?

Se necesitan al menos 24 meses en Guadalajara para estimar el patrón por mes; aún no se reúnen.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Todavía no hay al menos 3 meses en que dos centrales coticen el mismo producto de origen Colima. La captura diaria del catálogo nacional acumula esa historia.

- **Confianza:** no aplica — sin meses pareados
- **Qué hacer:** Mientras tanto compare precios del día por central (pregunta 6).
- **Fuente:** SNIIM · **Datos a:** —

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (todos los orígenes; MXN/kg, mediana por central): más altas en Guerrero 28.00; Durango 22.50; Campeche 22.00; Quintana Roo 22.00; la más baja, Sonora 9.00. Cotizó en 33 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

No hay un año común entre el precio rural SIAP y cotizaciones de origen Colima en alguna central para este producto.

- **Confianza:** no aplica — sin año común
- **Qué hacer:** —
- **Fuente:** SIAP · SNIIM · **Datos a:** —

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 3.89, 2017: 4.38, 2018: 4.02, 2019: 4.13, 2020: 4.26, 2021: 3.98, 2022: 4.46, 2023: 5.44, 2024: 6.02, 2025: 6.05. De 2016 a 2025 cambió **+56 %** (+5.0 % por año en promedio); el año más alto fue 2025 (6.05) y el más bajo 2016 (3.89). La producción del estado cambió -35 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 10 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

Hay muy pocos meses (0) para medir variaciones; se necesitan al menos 6.

- **Confianza:** no aplica — 0 cambios mensuales
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

En los últimos 12 meses las cotizaciones de sandía en Guadalajara se repartieron así por estado de origen: Sonora 100 %.

- **Confianza:** media — mide presencia en cotizaciones publicadas, no toneladas vendidas
- **Qué hacer:** Si otro estado domina, su fruta compite por precio: diferénciese por calidad o por calendario.
- **Fuente:** SNIIM · origen reportado · **Datos a:** 2026-10-01

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Armería: 7,557 t a 6.56 MXN/kg; Manzanillo: 7,066 t a 6.25 MXN/kg; Tecomán: 4,093 t a 6.43 MXN/kg; Colima: 2,788 t a 3.23 MXN/kg. Total Colima: 23,933 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

En 2024 México exportó USD 413.1 millones a 10 países (código HS 080711). Principales compradores: USA (USD 371.0 millones, 10.35 MXN/kg, +9 % desde 2019); Canada (USD 41.6 millones, 13.06 MXN/kg, +18 % desde 2019); Japan (USD 0.4 millones, 26.60 MXN/kg, +594 % desde 2019); Antigua and Barbuda (USD 0.0 millones, 93.39 MXN/kg, +1461 % desde 2019). El valor promedio de exportación fue **10.58 MXN/kg** frente a 16.94 MXN/kg en las centrales nacionales (origen Colima, últimos 12 meses): **-38 %**. Mercados grandes donde México vende poco: Germany (importa USD 389 millones; México tiene 0.0 %); France (importa USD 170 millones; México tiene 0.0 %); United Kingdom (importa USD 168 millones; México tiene 0.0 %).

- **Confianza:** media — dato oficial de aduanas; valor unitario aduanal (no precio al productor)
- **Qué hacer:** Exportar exige certificación fitosanitaria, empaque, logística en frío y un comprador confirmado; empiece con un empacador exportador de la zona. Vea el detalle por país en la página de mercados extranjeros.
- **Fuente:** UN Comtrade · tipo de cambio BCE · **Datos a:** 2024

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Guanábana

### 1. ¿A cuánto se va a pagar la guanábana el próximo mes?

Todavía no hay pronóstico para la guanábana: se exigen 36 meses continuos de una misma serie y aún no se reúnen.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Use el precio actual por central (pregunta 6) como referencia.
- **Fuente:** Criterio de elegibilidad del observatorio · **Datos a:** —

### 2. ¿Me conviene vender ahora o esperar un mes?

No hay pronóstico validado para estimarlo.

- **Confianza:** no aplica — sin serie elegible
- **Qué hacer:** Compare el precio de hoy con su historia (pregunta 2).
- **Fuente:** — · **Datos a:** —

### 3. ¿El precio de hoy está caro o barato comparado con otros años?

No hay al menos 12 meses de historia de origen Colima para comparar.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 4. ¿En qué meses suele pagarse mejor?

Se necesitan al menos 24 meses en Guadalajara para estimar el patrón por mes; aún no se reúnen.

- **Confianza:** no aplica — historia insuficiente
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 5. ¿A qué central de abasto me conviene mandar mi fruta?

Todavía no hay al menos 3 meses en que dos centrales coticen el mismo producto de origen Colima. La captura diaria del catálogo nacional acumula esa historia.

- **Confianza:** no aplica — sin meses pareados
- **Qué hacer:** Mientras tanto compare precios del día por central (pregunta 6).
- **Fuente:** SNIIM · **Datos a:** —

### 6. ¿Cuánto se está pagando hoy en otras centrales del país?

Cotizaciones del 2026-11-25 (todos los orígenes; MXN/kg, mediana por central): más altas en Michoacán 50.00; Nayarit 37.00; Nayarit 37.00; la más baja, Nayarit 37.00. Cotizó en 3 centrales.

- **Confianza:** alta — dato oficial observado, pero de un solo día
- **Qué hacer:** Sirve para saber dónde está el precio hoy; para decidir destino use la comparación de varios meses (pregunta 5).
- **Fuente:** SNIIM · catálogo nacional · **Datos a:** 2026-11-25

### 7. De lo que paga la central, ¿cuánto le llega al productor?

No hay un año común entre el precio rural SIAP y cotizaciones de origen Colima en alguna central para este producto.

- **Confianza:** no aplica — sin año común
- **Qué hacer:** —
- **Fuente:** SIAP · SNIIM · **Datos a:** —

### 8. ¿Cómo ha cambiado lo que se le paga al productor en los últimos años?

Precio medio rural en Colima (MXN/kg, SIAP): 2016: 6.90, 2017: 5.61, 2018: 6.73, 2019: 7.16, 2022: 7.38, 2023: 6.83, 2024: 7.18, 2025: 7.35. De 2016 a 2025 cambió **+7 %** (+0.7 % por año en promedio); el año más alto fue 2022 (7.38) y el más bajo 2017 (5.61). La producción del estado cambió -62 % en el mismo periodo.

- **Confianza:** alta — estadística oficial de 8 años (cierres agrícolas SIAP), ponderada por volumen de todos los municipios
- **Qué hacer:** Compare su precio de venta de cada año con esta serie; para comparar contra la inflación use el INPC de INEGI.
- **Fuente:** SIAP · cierres 2016 en adelante · **Datos a:** 2025

### 9. ¿Qué tanto puede bajar el precio de un mes a otro?

Hay muy pocos meses (0) para medir variaciones; se necesitan al menos 6.

- **Confianza:** no aplica — 0 cambios mensuales
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 10. ¿De qué otros estados llega fruta a competir en Guadalajara?

No hay cotizaciones de este producto en Guadalajara.

- **Confianza:** no aplica — sin datos
- **Qué hacer:** —
- **Fuente:** SNIIM · **Datos a:** —

### 11. ¿Cuánto se produce en mi municipio y a cuánto se pagó?

Cierre agrícola 2025: Coquimatlán: 393 t a 6.42 MXN/kg; Colima: 226 t a 6.47 MXN/kg; Manzanillo: 190 t a 9.14 MXN/kg; Tecomán: 93 t a 7.99 MXN/kg. Total Colima: 975 t.

- **Confianza:** alta — estadística oficial anual de SADER-SIAP
- **Qué hacer:** Compare su rendimiento y precio con el promedio de su municipio; el mapa por municipio está en la vista de cliente.
- **Fuente:** SIAP · cierre de la producción agrícola · **Datos a:** 2025

### 12. ¿Podría exportar? ¿A qué países y cuánto pagan?

No hay datos de exportación para la guanábana: UN Comtrade no tiene un código HS propio para guanábana

- **Confianza:** no aplica — sin datos de UN Comtrade
- **Qué hacer:** —
- **Fuente:** UN Comtrade · **Datos a:** —

### 13. ¿El calor o la lluvia mueven el precio?

Para el limón en Guadalajara, la mayor correlación entre los cambios de temperatura mensual (estación de Manzanillo) y los cambios de precio fue -0.26 con 4 meses de desfase (31 meses de datos). **No es estadísticamente significativa**: con una estación y 3 años no se puede demostrar que el clima mueva el precio; por eso el pronóstico no lo usa.

- **Confianza:** baja — correlación cruzada con banda de significancia ±0.35
- **Qué hacer:** No base decisiones de precio en el clima de la costa; las alertas climáticas para su huerta deben venir del SMN.
- **Fuente:** NOAA · laboratorio E1 · **Datos a:** —

### 14. ¿Por qué debería creerle a estos números?

Vienen de fuentes oficiales (SNIIM de la Secretaría de Economía y SIAP de Agricultura), se descargan solos cada día y cada cifra se puede rastrear al archivo original con su huella SHA-256. La captura funcionó el 100 % de los últimos 14 días y el 100 % de los datos obligatorios está completo. Cada respuesta de esta página declara su nivel de confianza.

- **Confianza:** alta — índice = 50 % disponibilidad de la captura + 50 % completitud ISO/IEC 25012
- **Qué hacer:** Si una respuesta dice confianza baja, úsela como pista y no como base de una decisión grande.
- **Fuente:** Métricas de calidad OAIC · **Datos a:** 2026-11-27

## Lo que todavía no responde

- **¿Qué plaga o enfermedad viene y cómo la controlo?** El observatorio no captura datos fitosanitarios (SENASICA). Consulte a su técnico o junta local de sanidad vegetal.
- **¿Cuánto me van a costar los fertilizantes y el diésel?** No hay fuente de costos de insumos integrada; el simulador de la vista de cliente acepta sus costos reales.
- **¿Quién me compra hoy y a qué precio exacto?** Los precios son cotizaciones de plaza publicadas por el SNIIM, no ofertas de compradores. No se publican datos de personas ni empresas.
- **¿Va a llover o hacer frío la próxima semana?** El observatorio usa clima observado (NOAA), no pronóstico meteorológico. Consulte al SMN de CONAGUA.
- **¿Me conviene un crédito o seguro agrícola?** Fuera de alcance; no es asesoría financiera.
