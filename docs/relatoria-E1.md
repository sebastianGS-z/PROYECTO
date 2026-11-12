# Relatoría de etapa E1

## Propósito

Integrar la captura E0 con el procesamiento estadístico necesario para construir capas Plata y Oro, agregando una puerta de calidad que mantenga evidencia de los registros rechazados.

## Trabajo integrado

Se agregó `src/tdl_e1/pipeline.py` como implementación ejecutable del flujo Bronce → Plata → Oro. El pipeline comprueba los sidecars y sus hashes, parsea las observaciones SNIIM/NOAA, armoniza fechas y tipos, aplica reglas de esquema y rango, y dirige rechazos a cuarentena. Las acciones diarias e históricas ahora invocan el pipeline tras la captura; también existe el comando local `python main.py capas`.

Se añadieron el diagnóstico de faltantes, detección de atípicos por IQR y Z robusto, copias winsorizadas para análisis, escalado Min-Max/Z-Score, discretización, jerarquías temporales y de producto, agregación mensual y tratamiento explícito de duplicados discrepantes.

## Decisiones y aprendizajes

1. No se imputa precio ni precipitación: su ausencia no tiene un valor sustituto defendible en la fuente disponible.
2. Solo se interpola temperatura en una serie auxiliar de modelado para huecos interiores de hasta dos días. Mantener ambas columnas evita confundir observado con imputado.
3. No se afirma un mecanismo de ausencia solo por observar faltantes. Las etiquetas MCAR-compatible y MAR-compatible se acompañan de su límite de inferencia, y MNAR queda como posibilidad no descartada.
4. Los precios permanecen ligados a presentación, variante y plaza. Sin pesos de empaque confiables no se convierten a kilogramo.
5. Ante versiones duplicadas discrepantes, se selecciona de forma reproducible la captura más reciente y se registra el conflicto; los originales Bronce no se reemplazan.

## Archivos y operación

La ficha técnica está en [`docs/E1/ENTREGA.md`](E1/ENTREGA.md). Las salidas son `data/plata/precios_clima.csv`, `data/plata/clima_modelado.csv`, diagnósticos y conflictos bajo `data/plata/`, `data/oro/panel_mensual.csv` y `data/cuarentena/registros_invalidos.csv`.

Comando para generar o actualizar las capas:

```bash
python main.py capas
```

Corrida local materializada sobre el Bronce existente: 15,109 registros normalizados/validados en Plata, 0 registros inválidos en cuarentena, 0 conflictos discrepantes y 712 filas en Oro. Los datos NOAA abarcan 1,098 días consultados y 791 días con alguna variable climática; los faltantes se conservan y perfilan. Los reportes contienen el detalle por variable.

## Pendientes de cierre

* Revisar calidad y recuentos generados, especialmente conflictos y filas en cuarentena.
* Crear/publicar el tag `e1` sobre el commit aprobado.
* Registrar el enlace en el formulario oficial cuando se proporcione su URL.
