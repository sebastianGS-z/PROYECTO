# Relatoría de etapa E3

**Fecha de elaboración:** 2026-11-20

**Proyecto:** Observatorio de Agro-Inteligencia Colimense

**Participantes:** Grageda Sandoval Sebastián y Jose Negrete Orozco

## Secuencia de trabajo

1. Se revisó la arquitectura acumulada de E0–E2 y se identificó `src/tdl_e1/pipeline.py` como el pipeline que convierte Bronce SNIIM/NOAA a Plata y Oro. La versión anterior quedó fijada por el tag `e2` y sus capturas Bronce existentes se conservaron como datos de entrada.
2. Se midió la línea base en procesos aislados y se perfiló una ejecución. El mayor costo detectado correspondió al parseo repetido de 1,672 páginas HTML con un árbol BeautifulSoup completo; también se observó iteración Python para reglas de calidad y grupos singleton en resolución de duplicados.
3. Se implementaron tres cambios acotados: restringir el parseo estructural a tablas, vectorizar reglas relacionales y hacer una comprobación rápida de existencia de duplicados. Se conservó el procesamiento anterior para grupos con duplicados reales.
4. Se agregaron pruebas de regresión para el camino sin duplicados y la cuarentena de reglas inválidas. La suite local terminó con **74 pruebas aprobadas y 2 pruebas de integración externas omitidas**; no se ejecutaron consultas contra servicios externos.
5. Se compararon la revisión del tag `e2` (`34b56a3`) y el código optimizado con las mismas 3,736 capturas (15,204 registros parseados), tres procesos independientes por versión y límites de hilos equivalentes. La mediana pasó de 22.10 s a 19.29 s (12.74% menos) y la memoria máxima RSS de 173.68 MiB a 155.47 MiB (10.48% menos). Ambas versiones tuvieron cero errores, procesaron 15,204 registros, enviaron cero a cuarentena y produjeron 712 filas Oro. Los hashes de las cinco salidas CSV coinciden.
6. Se publicó como copia curada el panel mensual Oro en CSV con sus campos de linaje. Se añadió un datasheet que describe composición, variables, cobertura, métodos, nulos, usos y limitaciones, junto con una declaración de licencia por capas que preserva las condiciones de las fuentes.

## Organización y decisiones

La documentación E0 ya asignaba a Sebastián el rol de Data Engineer y a José el de Data Statistician. Se conservó esa distribución de responsabilidades para el pipeline y la revisión estadística del dataset. Las actividades de E3 se respaldan con los cambios y benchmarks del repositorio; no hay una bitácora PSP de esta etapa que permita atribuir horas por persona, así que no se inventan. No se alteraron originales Bronce ni se imputaron precios. La publicación conserva datos climáticos faltantes como nulos y no convierte presentaciones comerciales a kg sin peso comprobable.

Se mantuvo BeautifulSoup como dependencia existente y se limitó el árbol a tablas, evitando agregar un parser binario nuevo. La detección de duplicados usa una comprobación vectorizada; el camino previo sigue resolviendo los grupos repetidos y preservando las versiones fuente. La licencia CC BY 4.0 se limita a la contribución propia de selección/organización/agregación/documentación donde OAIC tiene derechos; no cambia los términos de SNIIM ni NOAA.

## Resultados y dificultades

La primera comparación mostró mejoras medibles pero moderadas: la mayor parte del costo corresponde a parsear una colección grande de capturas históricas; la optimización reduce creación de nodos HTML y trabajo Python accesorio, pero no evita leer los originales ni interpretar sus tablas. Se mantuvo el control de igualdad de hashes: el benchmark se detiene si cualquier CSV difiere entre la versión congelada y la optimizada.

La disponibilidad ambiental varía: algunos meses y variables NOAA no tienen cobertura completa. Se conservaron nulos y el conteo diario para que quien reutilice el dataset pueda evaluar cobertura. Las únicas comprobaciones de red de esta etapa fueron de documentación/licencia; el pipeline de pruebas no necesitó red.

## Aprendizajes y cierre

El perfilado evitó optimizar intuiciones: localizó el costo en el parser HTML y justificó reducir tanto construcción de árboles como bucles sobre filas. Una comparación útil requiere aislar procesos, mantener entradas y condiciones iguales y confirmar que el contenido no cambió. Las mejoras medidas aplican al inventario y entorno registrados; deben recalcularse al cambiar de equipo, dependencias o tamaño de datos.

La etapa queda lista para revisión cuando los cambios estén en el repositorio remoto, el tag `e3` apunte al commit de esta entrega y se registre el enlace en el formulario oficial.

## Evidencias

- [Ficha técnica E3](E3/ENTREGA.md)
- [Datasheet](E3/datasheet.md)
- [Dataset curado](../data/publico/panel_mensual_e3.csv)
- [Gráfica de benchmark](E3/evidencias/comparativa.png)
- [Resultados reproducibles](../benchmarks/comparativa.json)
