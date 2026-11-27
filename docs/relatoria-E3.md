# Relatoría de etapa E3

**Fecha de elaboración:** 2026-11-20

**Proyecto:** Observatorio de Agro-Inteligencia Colimense

**Participantes:** Grageda Sandoval Sebastián y Jose Negrete Orozco

## Secuencia de trabajo

1. Se revisó la arquitectura acumulada de E0–E2 y se identificó `src/tdl_e1/pipeline.py` como el pipeline que convierte Bronce SNIIM/NOAA a Plata y Oro. La versión anterior quedó fijada por el tag `e2` y sus capturas Bronce existentes se conservaron como datos de entrada.
2. Se midió la línea base en procesos aislados y se perfiló una ejecución. El mayor costo detectado correspondió al parseo repetido de 1,672 páginas HTML con un árbol BeautifulSoup completo; también se observó iteración Python para reglas de calidad y grupos singleton en resolución de duplicados.
3. Se implementaron tres cambios acotados: restringir el parseo estructural a tablas, vectorizar reglas relacionales y hacer una comprobación rápida de existencia de duplicados. Se conservó el procesamiento anterior para grupos con duplicados reales.
4. Se agregaron pruebas de regresión para el camino sin duplicados y la cuarentena de reglas inválidas. La suite local terminó con **74 pruebas aprobadas y 2 pruebas de integración externas omitidas**; no se ejecutaron consultas contra servicios externos.
5. Se compararon la revisión del tag `e2` (`34b56a3`) y el código optimizado del tag `e3` (`e8d4014`) con las mismas 3,736 capturas Bronce (15,204 registros parseados). Una primera medición con tres procesos por versión dio 22.10 → 19.29 s (−12.74 %); como la variación entre corridas era grande, se repitió con **siete pares aislados** y orden aleatorizado dentro de cada par, que es la cifra oficial en [`benchmarks/comparativa.json`](../benchmarks/comparativa.json): mediana **33.82 → 21.49 s (−36.45 %)** y memoria máxima RSS **175.60 → 157.46 MiB (−10.33 %)**. Los rangos observados (e2: 21.49–37.46 s; e3: 19.01–32.81 s) se traslapan, así que el porcentaje depende de la carga de la máquina en cada corrida y debe leerse junto con el rango. Ambas versiones tuvieron cero errores, procesaron 15,204 registros, enviaron cero a cuarentena y produjeron 712 filas Oro. Los hashes de las cinco salidas CSV coinciden.
6. Se publicó como copia curada el panel mensual Oro en CSV con sus campos de linaje. Se añadió un datasheet que describe composición, variables, cobertura, métodos, nulos, usos y limitaciones, junto con una declaración de licencia por capas que preserva las condiciones de las fuentes.

## Organización y decisiones

La documentación E0 ya asignaba a Sebastián el rol de Data Engineer y a José el de Data Statistician. Se conservó esa distribución de responsabilidades para el pipeline y la revisión estadística del dataset. Las actividades de E3 se respaldan con los cambios y benchmarks del repositorio; no hay una bitácora PSP de esta etapa que permita atribuir horas por persona, así que no se inventan. No se alteraron originales Bronce ni se imputaron precios. La publicación conserva datos climáticos faltantes como nulos y no convierte presentaciones comerciales a kg sin peso comprobable.

Se mantuvo BeautifulSoup como dependencia existente y se limitó el árbol a tablas, evitando agregar un parser binario nuevo. La detección de duplicados usa una comprobación vectorizada; el camino previo sigue resolviendo los grupos repetidos y preservando las versiones fuente. La licencia CC BY 4.0 se limita a la contribución propia de selección/organización/agregación/documentación donde OAIC tiene derechos; no cambia los términos de SNIIM ni NOAA.

## Resultados y dificultades

La primera comparación mostró mejoras medibles pero moderadas: la mayor parte del costo corresponde a parsear una colección grande de capturas históricas; la optimización reduce creación de nodos HTML y trabajo Python accesorio, pero no evita leer los originales ni interpretar sus tablas. Se mantuvo el control de igualdad de hashes: el benchmark se detiene si cualquier CSV difiere entre la versión congelada y la optimizada.

La disponibilidad ambiental varía: algunos meses y variables NOAA no tienen cobertura completa. Se conservaron nulos y el conteo diario para que quien reutilice el dataset pueda evaluar cobertura. Las únicas comprobaciones de red de esta etapa fueron de documentación/licencia; el pipeline de pruebas no necesitó red.

## Aprendizajes y cierre

El perfilado evitó optimizar intuiciones: localizó el costo en el parser HTML y justificó reducir tanto construcción de árboles como bucles sobre filas. Una comparación útil requiere aislar procesos, mantener entradas y condiciones iguales y confirmar que el contenido no cambió. Las mejoras medidas aplican al inventario y entorno registrados; deben recalcularse al cambiar de equipo, dependencias o tamaño de datos.

La etapa quedó publicada en el tag `e3`, que apunta al commit de esta entrega. El integrante designado registra el enlace en Classroom; esta relatoría no afirma haber verificado ese formulario.

## Evidencias

- [Ficha técnica E3](E3/ENTREGA.md)
- [Datasheet](E3/datasheet.md)
- [Dataset curado](../data/publico/panel_mensual_e3.csv)
- [Gráfica de benchmark](E3/evidencias/comparativa.png)
- [Resultados reproducibles](../benchmarks/comparativa.json)

## Revisión del 2026-11-27 (antes de etiquetar E3)

Una revisión completa del repositorio contra la guía del proyecto encontró 14 hallazgos (1 crítico: el reproceso E2 fallaba al confundir la capa municipal con polígonos estatales). Detalle, acciones y estado en [auditoría interna](calidad/auditoria/auditoria_interna_2026-11-27.md) y [cierre de hallazgos](calidad/auditoria/cierre_hallazgos.md). En esa revisión se agregaron el laboratorio estadístico de E1–E3 (`laboratorio/`), la integración continua completa y la documentación de calidad (`docs/calidad/`).

## Uso de IA generativa

- 2026-11-27: Claude Code (asistente de programación) para revisar el repositorio contra la guía, escribir pruebas, el laboratorio estadístico, las métricas de calidad y borradores de la documentación de calidad. Todas las cifras de los informes se generan con código del repositorio; el equipo debe poder explicar cada análisis en la defensa.
- Etapas anteriores: **pendiente** que el equipo declare qué herramientas usó y para qué.

## Pendiente del equipo para cumplir la plantilla de relatoría

- Cronología con horas **por persona**: no hay registros PSP de E1–E3 (ver [retrospectiva PSP](calidad/retrospectiva_psp.md)); no se inventan.
- Un párrafo de aprendizaje por materia escrito por cada integrante.
