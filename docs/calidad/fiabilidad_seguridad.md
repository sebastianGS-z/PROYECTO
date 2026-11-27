# Fiabilidad, disponibilidad y seguridad

Medido el 2026-11-27 con `python -m calidad.metricas` sobre `calidad/bitacora_capturas.csv` (54 ejecuciones, incluidas las capturas diarias del 21 al 27 de noviembre publicadas por GitHub Actions). Cifras completas en [`calidad/reportes/fiabilidad.json`](../../calidad/reportes/fiabilidad.json); se recalculan en cada push.

## Definiciones operativas

- **Unidad:** día calendario UTC; la captura diaria debe ejecutarse una vez al día.
- **Día operativo:** hubo al menos una ejecución diaria programada (`schedule` o `workflow_dispatch`) y ninguna fuente quedó `fallida` o `parcial`.
- **`sin_resultados` no es falla:** la fuente respondió sin publicar datos nuevos (SNIIM no publica en fin de semana; NOAA tiene rezago). Afecta la *actualidad* de los datos y se mide aparte como frescura.
- **Falla:** inicio de una racha de días caídos. MTTR = duración media de las rachas; MTBF = horas operativas / número de fallas; A = MTBF / (MTBF + MTTR).

## Resultados

| Periodo | Días | Operativos | Fallas | MTBF | MTTR | Disponibilidad |
|---|---:|---:|---:|---:|---:|---:|
| Desde la primera ejecución en Actions (9 – 27 nov) | 19 | 16 | 1 | 384 h | 72 h | **84.2 %** |
| Desde la activación del `schedule` (14 – 27 nov) | 14 | 14 | 0 | ≥ 336 h (cota inferior) | 0 h | **100 %** |
| **Ventana del Sello: últimos 14 días** (14 – 27 nov) | 14 | 14 | 0 | ≥ 336 h | 0 h | **100 %** |

La única falla es la racha del 10 al 12 de noviembre: el workflow existía pero todavía no corría programado desde la rama por defecto (no hay ejecución esos días). Se reparó el 13 con una ejecución manual y desde el 14 corre solo todos los días.

**Objetivo OQ1 (≥ 95 % en 14 días): cumplido (100 %).** Si se cuenta todo el periodo desde la primera ejecución, la disponibilidad es 84.2 % y el objetivo no se habría cumplido; ambas cifras se reportan.

### Por fuente (ejecuciones programadas)

| Fuente | Ejecuciones | Éxito técnico | Con datos nuevos | Duración mediana | Último dato nuevo |
|---|---:|---:|---:|---:|---|
| SNIIM | 17 | 100 % | 58.8 % (10 de 17) | 102.8 s | 2026-11-27 |
| NOAA NCEI | 17 | 100 % | **0 %** | 2.0 s | nunca en ejecuciones diarias |

**Alerta de frescura activa:** NOAA no trajo datos nuevos en ninguna ejecución diaria; el clima de Oro llega hasta octubre de 2026 solo por la captura histórica. Riesgo abierto en el [plan SQA](plan_sqa.md#10-riesgos) y hallazgo INT-12.

### Puntualidad

El cron está a las 03:00 UTC (21:00 en Colima), pero GitHub Actions arrancó las 14 ejecuciones programadas con **8.3 h de retraso mediano (máximo 10.4 h)**. No afecta la disponibilidad diaria, pero sí el momento en que el tablero se actualiza.

## Seguridad

| Control | Resultado | Evidencia |
|---|---|---|
| Secretos en el historial | **0** coincidencias en un escaneo local con patrones de llaves (AWS, GitHub, Slack, Google, llaves privadas, asignaciones `token/password/api_key`) sobre todo el historial de código; gitleaks corre en cada push sobre el historial completo | `.github/workflows/validacion.yml` (job `secretos`) |
| Vulnerabilidades de dependencias | **0** con `pip-audit -r requirements-dev.txt` tras actualizar pytest (PYSEC-2026-1845 en 8.4.2) | Paso "pip-audit" de la CI |
| Archivos con credenciales | `.env` existe solo localmente y está en `.gitignore`; el repositorio publica `.env.example` sin valores | `git check-ignore .env` |
| Permisos mínimos de tokens | La CI de validación usa `contents: read`; solo los dos workflows que publican datos tienen `contents: write`, con el `GITHUB_TOKEN` efímero (sin tokens personales) | `permissions:` en cada workflow |
| Integridad de Bronce | Archivos de solo lectura, creación exclusiva y SHA-256 verificado antes de parsear | `python main.py validar` → "Capa Bronce íntegra." |
| Datos personales | El audio de la entrevista dejó de versionarse; el módulo comercial no guarda teléfonos ni correos | `.gitignore`; `tests/test_comercial_economia.py` |

**Confidencialidad, integridad y disponibilidad (CID):** no hay datos confidenciales en el repositorio (fuentes públicas); la integridad se garantiza con SHA-256 y validación Pandera; la disponibilidad se mide arriba.

### Respaldo

El respaldo de Bronce es el propio repositorio remoto (cada captura se publica con un commit) más la verificación SHA-256 de cada archivo contra su sidecar.

**Prueba de restauración (2026-11-27):** se clonó el repositorio en una carpeta vacía (`git clone`), se corrió `python main.py validar` en la copia (resultado: "Capa Bronce íntegra.") y se regeneró Plata/Oro desde el Bronce restaurado: los cinco CSV (`precios_clima`, `clima_modelado`, `panel_mensual`, `registros_invalidos`, `conflictos_resueltos`) tuvieron el **mismo SHA-256** que los del repositorio original. Limitación: el clon usó el mismo entorno de Python; la CI repite la regeneración en un runner limpio con `requirements-lock.txt`.
