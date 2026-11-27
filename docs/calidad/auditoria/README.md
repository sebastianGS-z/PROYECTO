# Auditorías del observatorio

| Documento | Qué contiene | Estado |
|---|---|---|
| [auditoria_recibida.md](auditoria_recibida.md) | Reporte de la auditoría cruzada que **otro equipo** hizo a este observatorio (estado E1, ISO/IEC 25010 y 25012) | **Pendiente de incorporar**: transcribir el reporte entregado por el equipo auditor, sin modificar sus hallazgos |
| [auditoria_emitida.md](auditoria_emitida.md) | Reporte de la auditoría que **este equipo** hizo al observatorio asignado | **Pendiente de incorporar** si no está en otro repositorio; enlazar la versión entregada |
| [auditoria_interna_2026-11-27.md](auditoria_interna_2026-11-27.md) | Revisión interna con evidencia y acciones correctivas | Realizada |
| [cierre_hallazgos.md](cierre_hallazgos.md) | Estado de cada hallazgo (interno y externo) con acción, evidencia y estado | Hallazgos internos cargados; externos pendientes |

**Regla:** ningún hallazgo crítico puede quedar abierto para solicitar el Sello TDL. Los hallazgos de la auditoría externa se copian tal como los redactó el equipo auditor y se agregan a la tabla de cierre con su propio identificador (`EXT-nn`).

## Clasificación de severidad

| Severidad | Criterio |
|---|---|
| Crítico | Produce cifras publicadas incorrectas, expone datos personales o secretos, o detiene la captura |
| Mayor | Incumple un requisito de la rúbrica o de una norma evaluada, sin afectar todavía cifras publicadas |
| Menor | Desviación de documentación, estilo o proceso que no afecta resultados |
