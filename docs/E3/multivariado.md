# Laboratorio E3 · Mapa multivariado (normalidad multivariada, PCA y MANOVA)

> Documento **generado** por `python -m laboratorio.e3_multivariado` desde `data/oro/panel_mensual.csv`. Resultados completos en `laboratorio/resultados/e3/resultados.json`; coordenadas del mapa en `laboratorio/resultados/e3/mapa_componentes.csv`.

## 1. Matriz multivariada

Unidad de análisis: una serie de cotización (variante × plaza × origen × presentación) en un mes, con precio convertible a MXN/kg. **n = 1987** observaciones completas en 5 grupos (productos): platano 785, limon 438, papaya 462, guayaba 152, tamarindo 150.

| Variable | Definición |
|---|---|
| `log_precio` | log del precio frecuente medio (MXN/kg) |
| `amplitud` | amplitud de cotización (máx − mín) / frecuente |
| `dispersion` | coeficiente de variación del precio frecuente dentro del mes |
| `log_cotizaciones` | log del número de cotizaciones del mes |
| `cambio_mensual` | cambio logarítmico del precio frente al mes anterior de la misma serie |

Se excluyeron precio mínimo y máximo como variables separadas porque son casi colineales con el precio frecuente (correlaciones de 0.976 a 0.997 en Oro) y harían casi singular la matriz de covarianzas; su información entra en `amplitud`.

Vector de medias:

| variable | media |
|---|---|
| log_precio | 2.8846 |
| amplitud | 0.1382 |
| dispersion | 0.0710 |
| log_cotizaciones | 2.9761 |
| cambio_mensual | 0.0034 |

Matriz de covarianzas:

| variable | log_precio | amplitud | dispersion | log_cotizaciones | cambio_mensual |
|---|---|---|---|---|---|
| log_precio | 0.1912 | -0.0002 | -0.0017 | -0.0231 | 0.0154 |
| amplitud | -0.0002 | 0.0211 | 0.0018 | 0.0018 | -0.0023 |
| dispersion | -0.0017 | 0.0018 | 0.0043 | 0.0015 | -0.0003 |
| log_cotizaciones | -0.0231 | 0.0018 | 0.0015 | 0.0538 | -0.0011 |
| cambio_mensual | 0.0154 | -0.0023 | -0.0003 | -0.0011 | 0.0319 |

![Correlaciones](multivariado/correlaciones.png)

## 2. Normalidad multivariada

- **Mardia** · asimetría b₁ = 31.074, χ² = 10,290.6 (gl 35), p = 0.0000; curtosis b₂ = 85.51 (esperada 35), z = 134.56, p = 0.0000.
- **Henze-Zirkler** · HZ = 40.963, p = 0.0000.
- Conclusión: **se rechaza** la normalidad multivariada al 5 %.

![Q-Q Mahalanobis](multivariado/qq_mahalanobis.png)

La gráfica Q-Q compara las distancias de Mahalanobis² con los cuantiles χ²; los puntos que se alejan arriba a la derecha son meses-serie atípicos (colas más pesadas que la normal).

## 3. Componentes principales

Las variables tienen escalas distintas (logaritmos, proporciones, cambios), por eso el PCA se hace sobre la **matriz de correlaciones** (variables estandarizadas).

| componente | valor propio | % varianza | % acumulado |
|---|---|---|---|
| CP1 | 1.394 | 27.890 | 27.890 |
| CP2 | 1.119 | 22.388 | 50.277 |
| CP3 | 0.990 | 19.802 | 70.079 |
| CP4 | 0.802 | 16.037 | 86.116 |
| CP5 | 0.694 | 13.884 | 100.000 |

![Sedimentación](multivariado/sedimentacion.png)

Criterio de Kaiser: 2 componentes con valor propio > 1; los dos primeros explican 50.3 % de la varianza.

Cargas (correlación variable–componente):

| variable | CP1 | CP2 | CP3 |
|---|---|---|---|
| log_precio | 0.650 | 0.490 | -0.031 |
| amplitud | -0.420 | 0.658 | -0.216 |
| dispersion | -0.471 | 0.590 | 0.183 |
| log_cotizaciones | -0.579 | -0.209 | 0.599 |
| cambio_mensual | 0.489 | 0.236 | 0.742 |

Nombres de negocio de los componentes (derivados de las cargas con |carga| ≥ 0.5):

- **CP1** · Índice de + nivel de precio, − profundidad de mercado (n.º de cotizaciones)
- **CP2** · Índice de + amplitud de cotización, + volatilidad dentro del mes
- **CP3** · Índice de + movimiento mes a mes, + profundidad de mercado (n.º de cotizaciones)

![Biplot](multivariado/biplot.png)

## 4. El mapa: interpretación para el cliente

Centroides de cada producto en el plano CP1–CP2:

| producto | CP1 | CP2 |
|---|---|---|
| platano | -0.141 | -0.396 |
| limon | -0.390 | 0.801 |
| papaya | 0.073 | -0.239 |
| guayaba | 0.294 | 0.193 |
| tamarindo | 1.353 | 0.273 |

- En **CP1** (índice de + nivel de precio, − profundidad de mercado (n.º de cotizaciones)), el producto más alto es **tamarindo** (1.35) y el más bajo **limon** (-0.39).
- En **CP2** (índice de + amplitud de cotización, + volatilidad dentro del mes), el producto más alto es **limon** (0.80) y el más bajo **platano** (-0.40).

Lectura para el comprador: productos cercanos en el mapa se comportan parecido en precio, estabilidad y profundidad de mercado, así que pueden gestionarse con la misma estrategia de compra; los alejados requieren reglas distintas (por ejemplo, contratos a precio fijo para los de mayor volatilidad). El mapa se publica en `tablero/laboratorio.html`.

## 5. MANOVA: ¿los productos difieren en las cinco variables a la vez?

Supuesto de homogeneidad de matrices de covarianza (M de Box): χ² = 2,207.5, gl = 60, p = 0.0000 → **no homogéneas**.

| Estadístico | Valor | F aprox. | gl num | gl den | p |
|---|---|---|---|---|---|
| Wilks' lambda | 0.6037 | 53.91 | 20 | 6,561.2 | 0.000000 |
| Pillai's trace | 0.4570 | 51.11 | 20 | 7,924.0 | 0.000000 |
| Hotelling-Lawley trace | 0.5598 | 55.33 | 20 | 4,344.2 | 0.000000 |
| Roy's greatest root | 0.2890 | 114.50 | 5 | 1,981.0 | 0.000000 |

Prueba de permutación de la traza de Pillai (999 permutaciones, semilla fija): Pillai = 0.4570, p = 0.0010.

**Puerta de calidad 3.** Como la normalidad multivariada y/o la homogeneidad de covarianzas no se cumplen, la conclusión se basa en la **traza de Pillai** (la más robusta a esas violaciones) y se confirma con la **prueba de permutación**, que no depende de la normalidad. Lambda de Wilks se reporta, pero no se usa como evidencia principal. Conclusión: los cinco productos **sí difieren** en el vector de variables al 5 %.

### ¿Por qué no basta con cinco ANOVA separados?

| variable | F | p | p_bonferroni |
|---|---|---|---|
| log_precio | 106.773687 | 0.000000 | 0.000000 |
| amplitud | 63.231157 | 0.000000 | 0.000000 |
| dispersion | 64.007549 | 0.000000 | 0.000000 |
| log_cotizaciones | 58.133437 | 0.000000 | 0.000000 |
| cambio_mensual | 0.267103 | 0.899212 | 1.000000 |

- Correr 5 ANOVA al 5 % cada uno eleva la probabilidad de al menos un falso positivo a 1 − 0.95⁵ = 22.6 % si no se corrige.
- Los ANOVA separados ignoran las correlaciones entre variables (la más fuerte aquí es log_precio con log_cotizaciones, r = -0.23); la MANOVA usa la matriz de covarianzas completa y puede detectar diferencias en combinaciones de variables que ninguna variable muestra por sí sola.
- Por eso la MANOVA es la prueba global; los ANOVA con corrección de Bonferroni solo indican qué variables contribuyen.

## Limitaciones

- Las observaciones de una misma serie en meses consecutivos no son independientes; la permutación a nivel de mes-serie no corrige esa dependencia, así que los p-valores son optimistas.
- Los grupos tienen tamaños distintos y mezclan plazas y orígenes; un diseño con plaza como segundo factor requeriría más series pareadas.
