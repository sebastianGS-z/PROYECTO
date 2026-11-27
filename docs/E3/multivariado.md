# Laboratorio E3 · Mapa multivariado (normalidad multivariada, PCA y MANOVA)

> Documento **generado** por `python -m laboratorio.e3_multivariado` desde `data/oro/panel_mensual.csv`. Resultados completos en `laboratorio/resultados/e3/resultados.json`; coordenadas del mapa en `laboratorio/resultados/e3/mapa_componentes.csv`.

## 1. Matriz multivariada

Unidad de análisis: una serie de cotización (variante × plaza × origen × presentación) en un mes, con precio convertible a MXN/kg. **n = 1170** observaciones completas en 5 grupos (productos): platano 458, limon 356, papaya 216, guayaba 70, tamarindo 70.

| Variable | Definición |
|---|---|
| `log_precio` | log del precio frecuente medio (MXN/kg) |
| `amplitud` | amplitud de cotización (máx − mín) / frecuente |
| `dispersion` | coeficiente de variación del precio frecuente dentro del mes |
| `log_cotizaciones` | log del número de cotizaciones del mes |
| `cambio_mensual` | cambio logarítmico del precio frente al mes anterior de la misma serie |

Se excluyeron precio mínimo y máximo como variables separadas porque son casi colineales con el precio frecuente (correlaciones de 0.946 a 0.995 en Oro) y harían casi singular la matriz de covarianzas; su información entra en `amplitud`.

Vector de medias:

| variable | media |
|---|---|
| log_precio | 2.9971 |
| amplitud | 0.1553 |
| dispersion | 0.0831 |
| log_cotizaciones | 2.9530 |
| cambio_mensual | -0.0003 |

Matriz de covarianzas:

| variable | log_precio | amplitud | dispersion | log_cotizaciones | cambio_mensual |
|---|---|---|---|---|---|
| log_precio | 0.1953 | -0.0116 | -0.0077 | -0.0326 | 0.0211 |
| amplitud | -0.0116 | 0.0264 | 0.0020 | 0.0038 | -0.0031 |
| dispersion | -0.0077 | 0.0020 | 0.0046 | 0.0033 | -0.0005 |
| log_cotizaciones | -0.0326 | 0.0038 | 0.0033 | 0.0720 | -0.0014 |
| cambio_mensual | 0.0211 | -0.0031 | -0.0005 | -0.0014 | 0.0409 |

![Correlaciones](multivariado/correlaciones.png)

## 2. Normalidad multivariada

- **Mardia** · asimetría b₁ = 24.370, χ² = 4,752.1 (gl 35), p = 0.0000; curtosis b₂ = 67.96 (esperada 35), z = 67.38, p = 0.0000.
- **Henze-Zirkler** · HZ = 28.976, p = 0.0000.
- Conclusión: **se rechaza** la normalidad multivariada al 5 %.

![Q-Q Mahalanobis](multivariado/qq_mahalanobis.png)

La gráfica Q-Q compara las distancias de Mahalanobis² con los cuantiles χ²; los puntos que se alejan arriba a la derecha son meses-serie atípicos (colas más pesadas que la normal).

## 3. Componentes principales

Las variables tienen escalas distintas (logaritmos, proporciones, cambios), por eso el PCA se hace sobre la **matriz de correlaciones** (variables estandarizadas).

| componente | valor propio | % varianza | % acumulado |
|---|---|---|---|
| CP1 | 1.651 | 33.025 | 33.025 |
| CP2 | 1.013 | 20.264 | 53.289 |
| CP3 | 0.929 | 18.582 | 71.871 |
| CP4 | 0.779 | 15.588 | 87.460 |
| CP5 | 0.627 | 12.540 | 100.000 |

![Sedimentación](multivariado/sedimentacion.png)

Criterio de Kaiser: 2 componentes con valor propio > 1; los dos primeros explican 53.3 % de la varianza.

Cargas (correlación variable–componente):

| variable | CP1 | CP2 | CP3 |
|---|---|---|---|
| log_precio | 0.746 | 0.136 | 0.245 |
| amplitud | -0.492 | -0.014 | 0.759 |
| dispersion | -0.612 | 0.361 | 0.210 |
| log_cotizaciones | -0.567 | 0.390 | -0.487 |
| cambio_mensual | 0.395 | 0.844 | 0.109 |

Nombres de negocio de los componentes (derivados de las cargas con |carga| ≥ 0.5):

- **CP1** · Índice de nicho: precio alto en un mercado delgado y estable
- **CP2** · Índice de impulso: alza del precio frente al mes anterior
- **CP3** · Índice de margen de negociación: distancia entre cotización máxima y mínima

![Biplot](multivariado/biplot.png)

## 4. El mapa: interpretación para el cliente

Centroides de cada producto en el plano CP1–CP2:

| producto | CP1 | CP2 |
|---|---|---|
| platano | -0.147 | -0.005 |
| limon | -0.459 | 0.169 |
| papaya | 0.142 | 0.028 |
| guayaba | 0.884 | -0.479 |
| tamarindo | 1.970 | -0.434 |

- En **CP1** (índice de nicho: precio alto en un mercado delgado y estable), el producto más alto es **tamarindo** (1.97) y el más bajo **limon** (-0.46).
- En **CP2** (índice de impulso: alza del precio frente al mes anterior), el producto más alto es **limon** (0.17) y el más bajo **guayaba** (-0.48).

Lectura para el comprador: productos cercanos en el mapa se comportan parecido en precio, estabilidad y profundidad de mercado, así que pueden gestionarse con la misma estrategia de compra; los alejados requieren reglas distintas (por ejemplo, contratos a precio fijo para los de mayor volatilidad). El mapa se publica en `tablero/laboratorio.html`.

## 5. MANOVA: ¿los productos difieren en las cinco variables a la vez?

Supuesto de homogeneidad de matrices de covarianza (M de Box): χ² = 1,668.4, gl = 60, p = 0.0000 → **no homogéneas**.

| Estadístico | Valor | F aprox. | gl num | gl den | p |
|---|---|---|---|---|---|
| Wilks' lambda | 0.4826 | 47.31 | 20 | 3,851.6 | 0.000000 |
| Pillai's trace | 0.5996 | 41.05 | 20 | 4,656.0 | 0.000000 |
| Hotelling-Lawley trace | 0.9088 | 52.70 | 20 | 2,546.8 | 0.000000 |
| Roy's greatest root | 0.6999 | 162.94 | 5 | 1,164.0 | 0.000000 |

Prueba de permutación de la traza de Pillai (999 permutaciones, semilla fija): Pillai = 0.5996, p = 0.0010.

**Puerta de calidad 3.** Como la normalidad multivariada y/o la homogeneidad de covarianzas no se cumplen, la conclusión se basa en la **traza de Pillai** (la más robusta a esas violaciones) y se confirma con la **prueba de permutación**, que no depende de la normalidad. Lambda de Wilks se reporta, pero no se usa como evidencia principal. Conclusión: los cinco productos **sí difieren** en el vector de variables al 5 %.

### ¿Por qué no basta con cinco ANOVA separados?

| variable | F | p | p_bonferroni |
|---|---|---|---|
| log_precio | 89.452421 | 0.000000 | 0.000000 |
| amplitud | 24.502827 | 0.000000 | 0.000000 |
| dispersion | 21.744460 | 0.000000 | 0.000000 |
| log_cotizaciones | 126.634621 | 0.000000 | 0.000000 |
| cambio_mensual | 0.189258 | 0.944062 | 1.000000 |

- Correr 5 ANOVA al 5 % cada uno eleva la probabilidad de al menos un falso positivo a 1 − 0.95⁵ = 22.6 % si no se corrige.
- Los ANOVA separados ignoran las correlaciones entre variables (la más fuerte aquí es log_precio con log_cotizaciones, r = -0.27); la MANOVA usa la matriz de covarianzas completa y puede detectar diferencias en combinaciones de variables que ninguna variable muestra por sí sola.
- Por eso la MANOVA es la prueba global; los ANOVA con corrección de Bonferroni solo indican qué variables contribuyen.

## Limitaciones

- Las observaciones de una misma serie en meses consecutivos no son independientes; la permutación a nivel de mes-serie no corrige esa dependencia, así que los p-valores son optimistas.
- Los grupos tienen tamaños distintos y mezclan plazas y orígenes; un diseño con plaza como segundo factor requeriría más series pareadas.
