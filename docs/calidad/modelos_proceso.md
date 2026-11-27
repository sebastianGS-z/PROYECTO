# Nuestro proceso frente a MoProSoft, CMMI, SPICE, ISO 9001 y PSP/TSP

> Autoevaluación del equipo OAIC (2 integrantes) con evidencia del repositorio al 2026-11-27. Las brechas se escriben como acciones concretas. **Pendiente:** que ambos integrantes revisen y firmen esta autoevaluación (la evidencia de José en el repositorio es limitada; ver brechas).

## 1. MoProSoft (NMX-I-059-NYCE)

MoProSoft organiza los procesos en tres categorías: **Alta Dirección** (DIR.1 Gestión de Negocio), **Gestión** (GES.1 Procesos, GES.2 Proyectos, GES.3 Recursos) y **Operación** (OPE.1 Administración de Proyectos Específicos, OPE.2 Desarrollo y Mantenimiento de Software). Los niveles de capacidad van de 1 (realizado) a 5 (optimizado). Para un equipo de dos personas aplican sobre todo OPE.1 y OPE.2.

| Proceso | Nivel estimado | Evidencia | Brecha concreta |
|---|---|---|---|
| OPE.1 Administración de Proyectos Específicos | 1 (realizado) | Entregas E0–E3 con fichas y etiquetas; cronograma de la guía | No hay plan propio con estimación de esfuerzo ni seguimiento semanal de avance contra plan. Acción: plan de E4 con horas estimadas por actividad y comparación real/estimado desde el PSP |
| OPE.2 Desarrollo y Mantenimiento: requerimientos | 2 (gestionado) | [Requerimientos verificables](requerimientos.md) con origen y verificación | Se formalizaron tarde (E3). Acción: versionar cambios de requerimientos en la ficha de cada entrega |
| OPE.2: análisis y diseño | 1 | README con arquitectura y capas | No hay documento de diseño separado ni decisiones registradas (ADR). Acción: registrar decisiones técnicas en las relatorías con alternativas descartadas |
| OPE.2: construcción y pruebas | 2 | CI con lint, cobertura ≥ 60 %, pruebas sin red, puerta de datos | Las pruebas se escribieron después del código en varias etapas (cobertura real era 38 % el 2026-11-27). Acción: prueba junto con cada cambio |
| OPE.2: integración y entrega | 2 | Workflows de captura y validación; etiquetas por entrega | Trabajo de E3/E4 estuvo días sin commitear. Acción: commits diarios y PR pequeños |
| GES.2 Gestión de Proyectos | 1 | Roles definidos en E0 | Sin métricas de proyecto más allá del PSP individual |
| GES.1 Gestión de Procesos | 1 | Plan SQA (2026-11-27) | Proceso definido muy tarde; sin mejora medida entre entregas |

**Nivel global estimado: 1, con prácticas de nivel 2 en pruebas, integración y requerimientos.**

## 2. CMMI (v2.0 / 3.0): áreas de práctica que aplican

| Área de práctica | Nivel de práctica alcanzado | Evidencia | Qué falta para el siguiente |
|---|---|---|---|
| Aseguramiento de la Calidad del Proceso (PQA) | 1 | Plan SQA, lista de comprobación del Quality Lead | Registrar las revisiones realizadas (fecha, revisor, hallazgos) |
| Verificación y Validación (VV) | 2 | Pruebas automáticas, puerta de datos, validación con entrevistados | Criterios de aceptación por requerimiento en la ficha de entrega |
| Revisión por Pares (PR) | 1 | Rol de Quality Lead definido | Evidencia de revisiones: defectos con fase `revision` en el PSP del revisor |
| Gestión de la Configuración (CM) | 2 | Git, etiquetas, Bronce inmutable con SHA-256, lock de dependencias | Política de ramas y PR revisados |
| Desarrollo de Requisitos y Gestión de Valor (RDM) | 2 | Requerimientos con origen y verificación | Trazabilidad requerimiento → prueba automatizada para todos |
| Estimación (EST) y Planificación (PLAN) | 1 | Cronograma externo | Estimaciones propias y su error (PSP PROBE) |
| Monitoreo y Control (MC) | 1 | Bitácora de capturas | Seguimiento de avance del proyecto, no solo del sistema |
| Gestión de Riesgos y Oportunidades (RSK) | 2 | Matriz de riesgos del plan SQA | Revisión periódica con fecha |
| Gestión del Rendimiento y Medición (MPM) | 2 | `calidad/metricas.py`, objetivos OQ1–OQ3 medidos en CI | Usar las métricas para decidir mejoras entre entregas |
| Causa Raíz (CAR) | 1 | Defectos con descripción | Análisis de causa raíz de los defectos más caros |

**Nivel de madurez equivalente: 1 (inicial).** El nivel 2 requiere que PLAN, MC, EST, CM, PQA, RDM y VV operen de forma gestionada; hoy CM, VV y RDM están cerca, PLAN/EST/MC no.

## 3. Tabla comparativa de modelos

| Aspecto | ISO 9001:2015 | MoProSoft | SPICE (ISO/IEC 15504 → ISO/IEC 33000) | CMMI | PSP / TSP |
|---|---|---|---|---|---|
| Qué evalúa | Sistema de gestión de calidad de cualquier organización | Procesos de empresas de software pequeñas y medianas | Capacidad de procesos (marco de evaluación) | Madurez/capacidad de procesos de desarrollo | Disciplina personal (PSP) y de equipo (TSP) |
| Origen | ISO (internacional) | México, NYCE / Secretaría de Economía (2005) | ISO/IEC | CMU-SEI, hoy ISACA | Watts Humphrey, SEI |
| Estructura | 10 cláusulas, ciclo PHVA | 3 categorías, 9 procesos | Dimensión de procesos + dimensión de capacidad (niveles 0–5) | Áreas de práctica; niveles de madurez 1–5 y de capacidad 0–3 | Niveles PSP0–PSP2.1; TSP con roles y lanzamientos |
| Certificable | Sí | Sí (NMX-I-059) | Evaluación formal (no certificación clásica) | Evaluación (appraisal) | Certificación individual |
| Tamaño ideal | Cualquiera | Micro y pequeñas empresas | Cualquiera | Medianas y grandes | Individuo / equipo pequeño |
| Aplicación en el OAIC | Enfoque a procesos y acciones correctivas | Autoevaluación de OPE.1/OPE.2 | Escala de capacidad para cada proceso | Áreas de práctica PQA, VV, CM | Registros individuales de tiempo y defectos |

## 4. Plan de mejora (E4)

1. Ambos integrantes registran tiempo y defectos **diariamente** con `python -m calidad.psp`.
2. El Quality Lead de E4 deja evidencia de su revisión (defectos con fase `revision`).
3. Cada cambio entra con su prueba; la CI bloquea cobertura < 60 %.
4. Relatoría E4 con cronología, horas por persona (del PSP) y decisiones con alternativas.
