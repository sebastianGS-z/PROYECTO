# Cierre de hallazgos de auditoría

Estado al 2026-11-27. Hallazgos internos de la [auditoría interna](auditoria_interna_2026-11-27.md); los externos (`EXT-nn`) se agregan al incorporar la [auditoría recibida](auditoria_recibida.md).

| ID | Severidad | Hallazgo | Acción correctiva | Evidencia | Estado |
|---|---|---|---|---|---|
| INT-01 | Crítico | `python main.py e2` fallaba: tomaba como capa municipal el GeoJSON más reciente de la carpeta, que desde el 27-nov es un polígono estatal; la captura diaria en Actions se habría detenido en el paso E2 | Selección por etiqueta `marco-municipal-colima` y orden por `run_id`, no por fecha de modificación | `src/tdl_e2/geoespacial.py::_latest_geojson`; prueba `tests/test_geoespacial_cli.py::test_latest_geojson_ignora_poligonos_estatales` | Cerrado |
| INT-02 | Mayor | Integración continua sin linter, sin cobertura mínima, sin búsqueda de secretos ni auditoría de dependencias; el workflow de validación no estaba versionado | `validacion.yml` con ruff, pytest `--cov` (umbral 60 %), pip-audit, gitleaks y puerta de datos | `.github/workflows/validacion.yml`, `pyproject.toml` | Cerrado al publicar en `main` |
| INT-03 | Mayor | Cobertura real 38 % medida sobre todo el código (la cifra de 55 % omitía módulos sin importar) | Pruebas de extremo a extremo del pipeline, geoespacial, comercial, métricas y laboratorio | `pytest --cov` ≥ 60 % (ver [sello](../sello_tdl.md)) | Cerrado |
| INT-04 | Mayor | `pytest` 8.4.2 con vulnerabilidad PYSEC-2026-1845 | Rango actualizado a `pytest>=9.0.3` | `requirements.txt`; pip-audit sin hallazgos | Cerrado |
| INT-05 | Mayor | Faltaban Dickey-Fuller, ACF/PACF, Ljung-Box, ARIMA justificado por AIC e intervalo de predicción; el reporte del observatorio decía "sin intervalo predictivo validado" | Laboratorio E1 reproducible con intervalos 80/95 % y puerta de supuestos | `laboratorio/e1_series.py`, `docs/E1/laboratorio_series.md`, `tablero/laboratorio.html` | Cerrado |
| INT-06 | Mayor | No había experimento factorial, ANOVA ni PCA/MANOVA | Laboratorios E2 y E3 con corridas reales y supuestos verificados | `docs/E2/experimento_factorial.md`, `docs/E3/multivariado.md` | Cerrado |
| INT-07 | Mayor | Un integrante sin commits ni registros PSP | Registro diario obligatorio desde 2026-11-27 y commits propios del laboratorio | `calidad/tiempo-jose.csv`, historial de Git | **Abierto** (depende del integrante) |
| INT-08 | Mayor | Audio de entrevista (`ENTREVISTA.m4a`, 22 MB) versionado en un repositorio público: la voz es dato personal según la LFPDPPP | Se dejó de versionar y se agregó a `.gitignore`; se conserva la transcripción | `.gitignore` | **Parcial**: sigue en el historial de Git; eliminarlo de la historia requiere reescribirla (decisión del equipo) |
| INT-09 | Menor | User-Agent con contacto genérico `equipo@correo.mx` | Configurar `TDL_USER_AGENT` con el correo real del equipo | `config/settings.py`, `.env.example` | **Abierto** (requiere el correo que el equipo decida publicar) |
| INT-10 | Menor | Cifras de benchmark distintas entre la relatoría E3 (3 corridas) y la ficha E3 (7 pares) | Relatoría alineada con `benchmarks/comparativa.json` | `docs/relatoria-E3.md` | Cerrado |
| INT-11 | Menor | 18 columnas de Oro sin documentar en el datasheet (comprensibilidad ISO/IEC 25012 = 72.7 %) | Diccionario ampliado | `docs/E3/datasheet.md` | Cerrado |
| INT-12 | Menor | NOAA no trajo datos nuevos en ninguna ejecución diaria programada; nadie lo notó porque `sin_resultados` no es falla | Alerta de frescura en `calidad/metricas.py` (aviso en Actions) | `calidad/reportes/fiabilidad.json` → `frescura` | Mitigado; fuente alternativa pendiente |
| INT-13 | Menor | Código muerto (método duplicado) y 41 avisos de linter | Corregidos | `ruff check .` sin avisos | Cerrado |
| INT-14 | Menor | Preguntas analíticas de E0 reemplazadas en el árbol de trabajo por otras que no corresponden a experimento ni a comparación de grupos | Restauradas y actualizadas a lo ejecutado | `docs/E0/propuesta.md` §3 | Cerrado |

**Críticos abiertos: 0.** Mayores abiertos: 1 (INT-07). Parciales: 1 (INT-08).
