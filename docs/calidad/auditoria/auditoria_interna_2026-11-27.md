# Auditoría interna · 2026-11-27

**Alcance:** repositorio completo (código, datos, documentación y proceso) contra la guía del Proyecto Integrador TDL, ISO/IEC 25010 y 25012.
**Método:** ejecución de pruebas y cobertura, linter, pip-audit, ejecución de cada comando del README, comparación de cifras entre documentos, revisión de la bitácora remota de capturas y del historial de Git.
**Realizada por:** revisión asistida por IA (Claude Code) a solicitud de Sebastián Grageda Sandoval. No sustituye la auditoría cruzada entre equipos.

## Hallazgos y evidencia

1. **INT-01 (crítico).** Al reprocesar E2 con los datos del 27-nov: `ValueError: La capa recibida no contiene municipios de Colima (cve_ent=06)`. Causa: `_latest_geojson` ordenaba todos los GeoJSON de `data/bronce/inegi_marco/` por fecha de modificación; el más reciente era `marco-estatal-32`.
2. **INT-02 (mayor).** `.github/workflows/validacion.yml` aparecía como archivo sin versionar y solo corría pytest; la puerta 2 de la guía pide pruebas, linter, cobertura mínima y secretos expuestos.
3. **INT-03 (mayor).** `pytest --cov` midiendo todos los paquetes: 38 %. Con `--cov=.` se obtenía 55 % porque los módulos nunca importados (comercial, economía, geoespacial) no aparecían en el reporte.
4. **INT-04 (mayor).** `pip-audit -r requirements.txt`: pytest 8.4.2, PYSEC-2026-1845 (corregida en 9.0.3).
5. **INT-05/06 (mayor).** Búsqueda en `docs/` y código: sin Dickey-Fuller, ACF/PACF, Ljung-Box, ANOVA, MANOVA, Mardia ni PCA; `laboratorio/` vacío.
6. **INT-07 (mayor).** `git log` con 17 commits de un integrante y 10 del bot; `calidad/tiempo-jose.csv` y `defectos-jose.csv` solo con encabezado.
7. **INT-08 (mayor).** `ENTREVISTA.m4a` versionado (22 MB).
8. **INT-09 (menor).** `config/settings.py:22` con `contacto: equipo@correo.mx`.
9. **INT-10 (menor).** Relatoría E3: 22.10 → 19.29 s (−12.74 %, 3 corridas). Ficha E3: 33.82 → 21.49 s (−36.45 %, 7 pares).
10. **INT-11 (menor).** `calidad/metricas.py` → comprensibilidad 0.727; 18 columnas `*_kg_*` sin documentar.
11. **INT-12 (menor).** Bitácora remota: NOAA 17 de 17 ejecuciones programadas `sin_resultados`.
12. **INT-13 (menor).** `ruff check` con reglas E, F, W, B, I: 41 avisos, entre ellos F811 (método redefinido) en `src/economia/costeo.py`.
13. **INT-14 (menor).** `git diff docs/E0/propuesta.md`: las preguntas 2 y 3 dejaron de ser experimento factorial y comparación multivariada.

## Observaciones positivas

- Bronce inmutable con SHA-256 y sidecar; las 889 referencias de linaje de Oro apuntan a archivos existentes.
- Cuarentena con motivo; cero pérdidas silenciosas de registros.
- 14 de 14 días operativos de captura programada (21–27 de noviembre incluidos en la bitácora remota).
- Benchmark E3 con verificación de igualdad SHA-256 de salidas.

Acciones y estado: [cierre_hallazgos.md](cierre_hallazgos.md).
