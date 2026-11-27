# Laboratorio E3 · Mapa multivariado (normalidad multivariada, PCA y MANOVA)

> Documento **generado** por `python -m laboratorio.e3_multivariado` desde `data/oro/panel_mensual.csv`. Resultados completos en `laboratorio/resultados/e3/resultados.json`; coordenadas del mapa en `laboratorio/resultados/e3/mapa_componentes.csv`.

## 1. Matriz multivariada

Unidad de análisis: una serie de cotización (variante × plaza × origen × presentación) en un mes, con precio convertible a MXN/kg. **n = 825** observaciones completas en 5 grupos (productos): platano 325, limon 216, papaya 144, guayaba 70, tamarindo 70.

| Variable | Definición |
|---|---|
| `log_precio` | log del precio frecuente medio (MXN/kg) |
| `amplitud` | amplitud de cotización (máx − mín) / frecuente |
| `dispersion` | coeficiente de variación del precio frecuente dentro del mes |
| `log_cotizaciones` | log del número de cotizaciones del mes |
| `cambio_mensual` | cambio logarítmico del precio frente al mes anterior de la misma serie |

Se excluyeron precio mínimo y máximo como variables separadas porque son casi colineales con el precio frecuente (correlaciones de 0.949 a 0.996 en Oro) y harían casi singular la matriz de covarianzas; su información entra en `amplitud`.

Vector de medias:

| variable | media |
|---|---|
| log_precio | 2.9490 |
| amplitud | 0.1930 |
| dispersion | 0.0880 |
| log_cotizaciones | 2.9338 |
| cambio_mensual | -0.0028 |

Matriz de covarianzas:

| variable | log_precio | amplitud | dispersion | log_cotizaciones | cambio_mensual |
|---|---|---|---|---|---|
| log_precio | 0.2244 | -0.0096 | -0.0091 | -0.0491 | 0.0245 |
| amplitud | -0.0096 | 0.0304 | 0.0019 | 0.0080 | -0.0038 |
| dispersion | -0.0091 | 0.0019 | 0.0045 | 0.0046 | -0.0005 |
| log_cotizaciones | -0.0491 | 0.0080 | 0.0046 | 0.0849 | -0.0024 |
| cambio_mensual | 0.0245 | -0.0038 | -0.0005 | -0.0024 | 0.0468 |

![Correlaciones](multivariado/correlaciones.png)

## 2. Normalidad multivariada

- **Mardia** · asimetría b₁ = 20.021, χ² = 2,752.9 (gl 35), p = 0.0000; curtosis b₂ = 59.56 (esperada 35), z = 42.16, p = 0.0000.
- **Henze-Zirkler** · HZ = 23.747, p = 0.0000.
- Conclusión: **se rechaza** la normalidad multivariada al 5 %.

![Q-Q Mahalanobis](multivariado/qq_mahalanobis.png)

La gráfica Q-Q compara las distancias de Mahalanobis² con los cuantiles χ²; los puntos que se alejan arriba a la derecha son meses-serie atípicos (colas más pesadas que la normal).

## 3. Componentes principales

Las variables tienen escalas distintas (logaritmos, proporciones, cambios), por eso el PCA se hace sobre la **matriz de correlaciones** (variables estandarizadas).

| componente | valor propio | % varianza | % acumulado |
|---|---|---|---|
| CP1 | 1.739 | 34.788 | 34.788 |
| CP2 | 1.011 | 20.227 | 55.015 |
| CP3 | 0.918 | 18.356 | 73.371 |
| CP4 | 0.766 | 15.324 | 88.696 |
| CP5 | 0.565 | 11.304 | 100.000 |

![Sedimentación](multivariado/sedimentacion.png)

Criterio de Kaiser: 2 componentes con valor propio > 1; los dos primeros explican 55.0 % de la varianza.

Cargas (correlación variable–componente):

| variable | CP1 | CP2 | CP3 |
|---|---|---|---|
| log_precio | 0.752 | 0.138 | 0.337 |
| amplitud | -0.448 | 0.006 | 0.876 |
| dispersion | -0.620 | 0.358 | -0.009 |
| log_cotizaciones | -0.674 | 0.298 | -0.193 |
| cambio_mensual | 0.366 | 0.880 | 0.010 |

Nombres de negocio de los componentes (derivados de las cargas con |carga| ≥ 0.5):

- **CP1** · Índice de nicho: precio alto en un mercado delgado y estable
- **CP2** · Índice de impulso: alza del precio frente al mes anterior
- **CP3** · Índice de margen de negociación: distancia entre cotización máxima y mínima

![Biplot](multivariado/biplot.png)

## 4. El mapa: interpretación para el cliente

Centroides de cada producto en el plano CP1–CP2:

| producto | CP1 | CP2 |
|---|---|---|
| platano | -0.288 | 0.008 |
| limon | -0.676 | 0.155 |
| papaya | 0.161 | 0.022 |
| guayaba | 1.051 | -0.287 |
| tamarindo | 2.043 | -0.271 |

- En **CP1** (índice de nicho: precio alto en un mercado delgado y estable), el producto más alto es **tamarindo** (2.04) y el más bajo **limon** (-0.68).
- En **CP2** (índice de impulso: alza del precio frente al mes anterior), el producto más alto es **limon** (0.16) y el más bajo **guayaba** (-0.29).

Lectura para el comprador: productos cercanos en el mapa se comportan parecido en precio, estabilidad y profundidad de mercado, así que pueden gestionarse con la misma estrategia de compra; los alejados requieren reglas distintas (por ejemplo, contratos a precio fijo para los de mayor volatilidad). El mapa se publica en `tablero/laboratorio.html`.

## 5. MANOVA: ¿los productos difieren en las cinco variables a la vez?

Supuesto de homogeneidad de matrices de covarianza (M de Box): χ² = 1,432.5, gl = 60, p = 0.0000 → **no homogéneas**.

| Estadístico | Valor | F aprox. | gl num | gl den | p |
|---|---|---|---|---|---|
| Wilks' lambda | 0.3741 | 46.71 | 20 | 2,707.3 | 0.000000 |
| Pillai's trace | 0.7704 | 39.08 | 20 | 3,276.0 | 0.000000 |
| Hotelling-Lawley trace | 1.3107 | 53.40 | 20 | 1,787.8 | 0.000000 |
| Roy's greatest root | 0.9938 | 162.79 | 5 | 819.0 | 0.000000 |

Prueba de permutación de la traza de Pillai (999 permutaciones, semilla fija): Pillai = 0.7704, p = 0.0010.

**Puerta de calidad 3.** Como la normalidad multivariada y/o la homogeneidad de covarianzas no se cumplen, la conclusión se basa en la **traza de Pillai** (la más robusta a esas violaciones) y se confirma con la **prueba de permutación**, que no depende de la normalidad. Lambda de Wilks se reporta, pero no se usa como evidencia principal. Conclusión: los cinco productos **sí difieren** en el vector de variables al 5 %.

### ¿Por qué no basta con cinco ANOVA separados?

| variable | F | p | p_bonferroni |
|---|---|---|---|
| log_precio | 118.553605 | 0.000000 | 0.000000 |
| amplitud | 31.474884 | 0.000000 | 0.000000 |
| dispersion | 20.768289 | 0.000000 | 0.000000 |
| log_cotizaciones | 110.439558 | 0.000000 | 0.000000 |
| cambio_mensual | 0.337201 | 0.852950 | 1.000000 |

- Correr 5 ANOVA al 5 % cada uno eleva la probabilidad de al menos un falso positivo a 1 − 0.95⁵ = 22.6 % si no se corrige.
- Los ANOVA separados ignoran las correlaciones entre variables (la más fuerte aquí es log_precio con log_cotizaciones, r = -0.36); la MANOVA usa la matriz de covarianzas completa y puede detectar diferencias en combinaciones de variables que ninguna variable muestra por sí sola.
- Por eso la MANOVA es la prueba global; los ANOVA con corrección de Bonferroni solo indican qué variables contribuyen.

## Limitaciones

- Las observaciones de una misma serie en meses consecutivos no son independientes; la permutación a nivel de mes-serie no corrige esa dependencia, así que los p-valores son optimistas.
- Los grupos tienen tamaños distintos y mezclan plazas y orígenes; un diseño con plaza como segundo factor requeriría más series pareadas.
