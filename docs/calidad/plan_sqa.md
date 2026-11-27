# Plan de Aseguramiento de la Calidad del Software (SQA) · OAIC

Observatorio de Agro-Inteligencia Colimense (OAIC) · TRUSTED DATA LAB
Estructura basada en IEEE 730 (*Software Quality Assurance Processes*). Versión 1.0 · 2026-11-27.

| Versión | Fecha | Cambio | Responsable |
|---|---|---|---|
| 1.0 | 2026-11-27 | Primera versión formal del plan; consolida los controles que ya operaban desde E0 | Equipo (revisión pendiente del Quality Lead de E3) |

> Este plan describe controles que **existen y se pueden verificar** en el repositorio. Donde un control todavía no opera, se marca como *pendiente*.

## 1. Propósito y alcance

**Propósito.** Asegurar que las cifras que publica el observatorio (precios mayoristas SNIIM, clima NOAA, marco geoestadístico INEGI y los análisis derivados) son trazables hasta su fuente, se validaron antes de publicarse y provienen de un sistema cuya disponibilidad está medida.

**Alcance.** Todo el ciclo de datos y código del repositorio `sebastianGS-z/PROYECTO`:

| Componente | Carpeta | Incluido |
|---|---|---|
| Captura (extractores éticos, programación) | `extractores/`, `pipeline/`, `scripts/`, `.github/workflows/` | Sí |
| Almacén medallion (Bronce, Plata, Oro, cuarentena) | `almacenamiento/`, `src/tdl_e1`, `src/tdl_e2`, `data/` | Sí |
| Laboratorio estadístico | `laboratorio/` | Sí |
| Pronóstico y tablero | `src/tdl_e4`, `tablero/` | Sí |
| Módulo comercial opcional | `src/modelos`, `src/economia`, `scripts/comercial.py` | Sí (pruebas), fuera de los hallazgos publicados |

Fuera de alcance: la infraestructura de GitHub y la disponibilidad de los sitios fuente (SNIIM, NOAA, INEGI), que se monitorean pero no se controlan.

## 2. Documentos de referencia

- IEEE 730-2014, ISO/IEC 25010:2023 (calidad de producto), ISO/IEC 25012:2008 (calidad de datos), ISO 9001:2015.
- Guía del Proyecto Integrador TDL (rúbricas E0–E4, Sello TDL).
- Internos: [requerimientos](requerimientos.md), [ética de datos](../etica-datos.md), [datasheet](../E3/datasheet.md), [objetivos de calidad](../../calidad/objetivos_calidad.json).

## 3. Roles y responsabilidades

| Rol | Persona | Responsabilidades de calidad |
|---|---|---|
| Data Engineer | Sebastián Grageda Sandoval | Captura, capas, puerta de datos, integración continua; corrige defectos de pipeline |
| Data Statistician | José Negrete Orozco | Laboratorio estadístico, puerta de supuestos (puerta 3); corrige defectos de análisis |
| Quality Lead (rotativo por entrega) | E0: José (consta en la propuesta). E1–E4: **por confirmar por el equipo**; propuesta: alternar (E3 Sebastián revisa a José, E4 José revisa a Sebastián) | Revisa el trabajo **del otro** con las listas de comprobación de la sección 7 antes de etiquetar la entrega |
| Auditor externo | Equipo asignado en la auditoría cruzada | Evalúa el observatorio con ISO/IEC 25010 y 25012 |

**Independencia del revisor.** Nadie aprueba su propio trabajo: el Quality Lead de cada entrega es la persona que no lo produjo. Con dos integrantes la independencia es parcial (ambos conocen el sistema); por eso la auditoría cruzada es el control independiente.

## 4. Estándares, prácticas y métricas

| Área | Estándar / práctica | Cómo se verifica |
|---|---|---|
| Código | Python 3.12, ruff (`pyproject.toml`), pruebas pytest sin red | CI: `ruff check .`, `pytest --cov` |
| Datos | Bronce inmutable con SHA-256 y sidecar; Pandera estricto en Plata; cuarentena con motivo | `python main.py validar`; `data/cuarentena/registros_invalidos.csv` |
| Análisis | Selección por error fuera de muestra; supuestos verificados antes de publicar | `docs/E1/laboratorio_series.md`, `docs/E2/experimento_factorial.md`, `docs/E3/multivariado.md` |
| Ética | robots.txt obligatorio, User-Agent identificable, pausa ≥ 1.5 s, cero datos personales | `extractores/base.py`, pruebas `tests/test_base.py` |
| Proceso | PSP: registro individual de tiempo y defectos | `calidad/tiempo-*.csv`, `calidad/defectos-*.csv` |

### Métricas y umbrales

| ID | Métrica | Umbral | Fuente | Frecuencia |
|---|---|---|---|---|
| OQ1 | Disponibilidad de la captura programada (14 días) | ≥ 95 % | `python -m calidad.metricas` → `calidad/reportes/fiabilidad.json` | Cada push (CI) y cierre de entrega |
| OQ2 | Fallos de captura no detectados | 0 | Manifiestos + bitácora | Semanal |
| OQ3 | Cobertura diaria de capturas | 100 % | Manifiestos | Semanal |
| M1 | Cobertura de pruebas automáticas | ≥ 60 % | `pytest --cov` (falla la CI si no se alcanza) | Cada push |
| M2 | Avisos del linter | 0 | `ruff check .` | Cada push |
| M3 | Vulnerabilidades conocidas en dependencias | 0 | `pip-audit` | Cada push |
| M4 | Secretos expuestos en el historial | 0 | gitleaks (historial completo) | Cada push |
| D1 | Completitud ISO/IEC 25012 de Oro (columnas obligatorias) | ≥ 95 % | `calidad/reportes/iso25012.json` | Cada push |
| D2 | Registros perdidos entre Bronce y Plata sin pasar por cuarentena | 0 | `data/plata/reporte_calidad.json` | Cada push |

## 5. Revisiones y auditorías

| Revisión | Cuándo | Quién | Evidencia |
|---|---|---|---|
| Revisión por pares con lista de comprobación | Antes de cada etiqueta `eN` | Quality Lead | Defectos encontrados en `calidad/defectos-<revisor>.csv` con fase `revision` |
| Revisión de supuestos estadísticos (puerta 3) | Antes de publicar un hallazgo | Data Statistician | Sección "Supuestos" de cada informe del laboratorio |
| Auditoría cruzada ISO/IEC 25010/25012 | 19–23 nov (E2) | Equipo auditor asignado | [`docs/calidad/auditoria/`](auditoria/) |
| Cierre de hallazgos | E3 | Equipo | [`auditoria/cierre_hallazgos.md`](auditoria/cierre_hallazgos.md) |

## 6. Pruebas

- **Unitarias y de integración sin red** (`pytest`, configuración en `pytest.ini`): extractores con sesiones HTTP falsas, pipeline Bronce → Oro de extremo a extremo con capturas *fixture*, geoespacial, métricas de calidad y laboratorio con datos sintéticos de propiedades conocidas.
- **Integración real opcional** (`RUN_INTEGRATION=1 pytest -m integration`): contra SNIIM y NOAA; no corre en CI para no cargar sitios ajenos.
- **Puerta de datos** en cada push: regeneración de Plata/Oro desde Bronce versionado y verificación de conteos.
- **Regresión de rendimiento**: `benchmarks/comparativa.py` exige igualdad SHA-256 de salidas entre versiones.

## 7. Reporte de problemas y acciones correctivas

1. Todo defecto encontrado se registra **en el registro PSP de quien lo encuentra** (`calidad/defectos-<nombre>.csv`) con tipo PSP, fase de inyección, fase de eliminación y minutos de corrección.
2. Las observaciones de los docentes llegan como *issues* con etiqueta `ing-datos`, `estadistica` o `calidad`; se cierran con el commit que las atiende.
3. Los hallazgos de auditoría se registran en `auditoria/cierre_hallazgos.md` con severidad, acción correctiva, evidencia y estado.
4. Un defecto que llega a datos publicados se trata como **crítico**: se corrige, se regenera Oro y se documenta en la relatoría de la etapa.

**Lista de comprobación del Quality Lead (antes de etiquetar):**

- [ ] CI en verde (lint, pruebas con cobertura, pip-audit, gitleaks, puerta de datos).
- [ ] `python main.py validar` sin errores.
- [ ] Los informes del laboratorio se regeneraron y sus cifras coinciden con las de la ficha de entrega y la relatoría.
- [ ] Cada afirmación de la relatoría tiene enlace a evidencia.
- [ ] Ningún archivo nuevo contiene datos personales.
- [ ] Defectos de la revisión registrados en el PSP del revisor.

## 8. Herramientas

pytest y pytest-cov · ruff · pip-audit · gitleaks (GitHub Action) · Pandera · GitHub Actions · `calidad/psp.py` (registro PSP) · `calidad/metricas.py` (fiabilidad e ISO/IEC 25012) · `scripts/validar_bronce.py` (integridad).

## 9. Control de versiones y configuración

- Rama única `main`; los workflows de captura publican datos con `GITHUB_TOKEN` (permiso `contents: write` solo en esos workflows; la CI de validación usa `contents: read`).
- Cada entrega se marca con una etiqueta `e0`–`e4`. Las capturas Bronce nunca se reescriben (creación exclusiva, archivos de solo lectura).
- Dependencias con versiones exactas en `requirements-lock.txt` (Python 3.12); rangos en `requirements.txt`.
- Respaldo de Bronce: el repositorio remoto en GitHub más la verificación SHA-256 de cada archivo ([prueba de restauración](fiabilidad_seguridad.md#respaldo)).

## 10. Riesgos

| Riesgo | Prob. | Impacto | Mitigación | Estado |
|---|---|---|---|---|
| SNIIM cambia su HTML | Media | Alto | Parser aislado; captura queda `fallida`/`parcial`, nunca datos inventados; pruebas con fixtures | Controlado |
| NOAA sin publicar datos recientes de la estación | Alta (observado) | Medio | Se reporta como `sin_resultados`; se documenta la actualidad en ISO/IEC 25012 | Abierto: evaluar segunda estación o fuente |
| GitHub retrasa los `schedule` (8 h de mediana observada) | Alta | Bajo | La unidad de disponibilidad es el día; se mide el retraso | Aceptado |
| Un integrante sin registros PSP | Alta (observado) | Alto en la evaluación PSP | Registro diario obligatorio desde 2026-11-27; revisión en cada entrega | Abierto |
| Publicar un hallazgo con supuestos violados | Media | Alto | Puerta 3: método robusto o no se publica | Controlado |
| Datos personales en fuentes comerciales (DENUE) | Media | Alto | No se importan teléfonos ni correos; CSV comerciales fuera de Git | Controlado |
