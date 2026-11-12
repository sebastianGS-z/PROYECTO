# Entrega E1 · Limpieza estadística, integración y puerta de calidad

**Proyecto:** Observatorio de Agro-Inteligencia Colimense (OAIC) · TRUSTED DATA LAB

**Ponderación:** 40 % de la Unidad 3

**Etiqueta solicitada:** `e1`
**Estado:** implementación integrada y corrida local materializada; revisar outputs y publicar el tag tras el cierre.

## Objetivo

Automatizar el paso de capturas originales de la Capa Bronce a Plata y Oro. Cada registro que no cumple la puerta de calidad se conserva en cuarentena con una explicación; nunca se descarta silenciosamente ni se altera Bronce.

## Componentes y ejecución

```bash
pip install -r requirements.txt
python main.py capas
```

Implementación: [`src/tdl_e1/pipeline.py`](../../src/tdl_e1/pipeline.py). El comando se ejecuta después de las capturas diarias e históricas en GitHub Actions.

1. Lee HTML SNIIM y JSON NOAA acompañados de sidecar; comprueba el SHA-256 antes de usar el contenido.
2. Traduce ambos esquemas a columnas comunes: fecha, tipo de observación, producto/variante/mercado/origen/presentación o estación/localidad, campos numéricos, unidades, archivo e integridad de origen.
3. Normaliza fecha SNIIM (`dd/mm/aaaa`) y NOAA (ISO), convierte números a tipos numéricos, preserva faltantes y verifica rangos y relaciones entre campos.
4. Aplica Pandera con esquema estricto. Los inválidos van a `data/cuarentena/registros_invalidos.csv` con SHA-256, ruta, valor original y motivo.
5. Resuelve duplicados de igual clave. Si hay discrepancias entre capturas, prevalece la de `fecha_captura` más reciente y el conflicto se documenta en `data/plata/conflictos_resueltos.csv`; todas las fuentes originales permanecen en Bronce.
6. Produce Plata y su diagnóstico, y reduce a un panel mensual Oro.

## Decisiones de limpieza estadística

### Valores faltantes y mecanismo

`data/plata/diagnostico_faltantes.json` resume conteos y porcentajes por variable y por grupos observables (fuente, cultivo, mercado y estación). Si las tasas de faltantes difieren al menos 20 puntos porcentuales entre grupos, el patrón se marca **compatible con MAR**. Si no se observa esa diferencia, se marca **compatible con MCAR, sin demostrarlo, y MNAR no descartable**. Estos rótulos son diagnósticos descriptivos, no pruebas causales: con los datos observados no se puede identificar MNAR ni demostrar MCAR.

* **Precios:** no imputar. Una cotización ausente no se deduce de otras fechas, plazas o presentaciones.
* **Precipitación:** no imputar. Ausencia de reporte no equivale a cero lluvia.
* **Temperatura:** solo para una copia de modelado, interpolación lineal temporal en huecos interiores de hasta dos días. La columna original permanece intacta y cada valor interpolado lleva un indicador. Huecos más largos, extremos y datos no observados siguen vacíos.

La imputación lineal es una feature exploratoria, pues temperatura cambia gradualmente en intervalos cortos. No implica que el mecanismo de faltantes sea MCAR. En un modelo temporal real, la interpolación debe hacerse dentro de cada partición y solo con información disponible al predecir.

### Atípicos, normalización y discretización

* Detecta atípicos por grupo comparable (variante × mercado × presentación para precio; estación para clima) con IQR de 1.5× y Z robusto basado en MAD con umbral 3.5. Se requieren al menos ocho observaciones por grupo.
* Conserva el dato original. Para análisis añade `*_analisis`, winsorizado a los límites IQR; añade también marca y método de detección.
* Añade variables Min-Max y Z-Score poblacional por campo continuo. Las estadísticas aplicadas quedan en `reporte_calidad.json`. Se calculan para describir el lote; al entrenar modelos deben recalcularse solo con train para evitar fuga temporal.
* Discretiza el precio frecuente en terciles globales (bajo/medio/alto) y la temperatura media con rangos descriptivos: <18, 18–25, 25–32 y ≥32 °C. Los umbrales de temperatura son operativos, no recomendaciones agronómicas validadas.

### Jerarquías y reducción

Jerarquías: fecha → año/trimestre/mes/día; cultivo → variante → ID de formulario; estación → localidad. Oro agrega por mes y conserva número de observaciones, media, mediana, extremos, desviación estándar y conteos. Precios se mantienen separados por presentación y unidad de cotización; no se convierten a kilogramo sin un factor de empaque verificable. Clima se agrega por estación y mes, sin fusionar estaciones distintas.

## Esquema Plata y puerta de calidad

`precios_clima.csv` tiene esquema común estricto con `tipo_registro` (`precio` o `clima`), fecha, campos de origen, unidades de medida, atributos de trazabilidad, identificador y hash del archivo fuente. Pandera rechaza columnas desconocidas, tipos incompatibles, valores no finitos, coordenadas fuera de rango, precios/precipitación negativos y temperaturas fuera de −90 a 70 °C. Reglas relacionales envían a cuarentena precio mínimo mayor que máximo, precio frecuente fuera del rango y mínima mayor que máxima.

Un registro inválido no pasa a Plata/Oro. Se guarda en `registros_invalidos.csv` con `source_file`, `source_sha256`, `motivo` y `registro_original`. Errores de lectura, sidecars ausentes y hashes distintos también quedan en cuarentena. Si el propio pipeline no puede ejecutar la validación o materializar las salidas, el comando devuelve código distinto de cero y el workflow falla.

## Archivos generados

* `data/plata/precios_clima.csv`: registros normalizados, validados y enriquecidos con indicadores estadísticos.
* `data/plata/clima_modelado.csv`: serie diaria de clima, valores de origen y campos de temperatura auxiliares imputados con marca.
* `data/plata/diagnostico_faltantes.json`: perfil y decisión de imputación por campo.
* `data/plata/reporte_calidad.json`: resumen de corrida y transformaciones.
* `data/plata/conflictos_resueltos.csv`: conflictos entre versiones de la misma clave.
* `data/oro/panel_mensual.csv`: panel mensual de precios y clima por estación.
* `data/cuarentena/registros_invalidos.csv`: rechazos con razón y evidencia.

## Limitaciones conocidas

* La estación climática configurada es Manzanillo; no representa directamente todas las huertas de Tecomán y Armería.
* SNIIM entrega precio por presentación. La conversión a precio/kg necesita reglas de empaque y peso de cada variante, que no están en la fuente capturada.
* La resolución de versiones discrepantes adopta “captura más reciente” como regla determinista; no afirma cuál fuente es más correcta. Los conflictos deben revisarse antes de análisis de alto impacto.
* El diagnóstico MCAR/MAR/MNAR no sustituye una prueba estadística formal ni información sobre el proceso de ausencia.
* La winsorización solo crea una columna analítica derivada; los datos fuente permanecen sin modificar.

## Checklist de entrega

- [x] Pipeline en `src/` con integración de SNIIM y NOAA.
- [x] Puerta automática Pandera con cuarentena documentada.
- [x] Plata y Oro conectados a workflows diario e histórico.
- [x] Ficha técnica E1 y relatoría.
- [x] Ejecutar `python main.py capas` sobre los datos Bronce disponibles y revisar los reportes materializados.
- [ ] Crear y publicar tag `e1` después de revisar la corrida.
- [ ] Registrar el enlace de GitHub en el formulario oficial de E1.

## Resultado de la corrida local

Ejecución del 12 de noviembre de 2026 sobre los datos Bronce disponibles: **15,109** registros leídos y validados, **0** cuarentenados, **0** conflictos con diferencias y **712** filas mensuales en Oro. La estación presenta **791 de 1,098** días consultados con al menos una variable útil entre el 1-nov-2023 y el 8-nov-2026; los días sin observación permanecen faltantes. El reporte incluye detalle variable y cantidad de temperaturas auxiliares interpoladas.
