# Entrega E0 · Observatorio de Agro-Inteligencia Colimense (OAIC)

Equipo: ⚠️ COMPLETAR (integrantes) · Etiqueta: `e0` · Tablero: no aplica en E0 (se publica desde E1)

## Resumen en tres líneas
1. Observatorio de precios mayoristas de limón, plátano y papaya (SNIIM) cruzados con clima de Tecomán y Colima (NOAA NCEI) para decidir cuándo vender.
2. Captura ética automática a la capa bronce con GitHub Actions, trazabilidad por SHA-256 y bitácora de ejecuciones.
3. Sistema de calidad inicial (PSP) con registros individuales y tres objetivos medibles.

> E0 tiene una sola rúbrica (100 puntos) que vale igual en las tres materias.

## Evidencia por criterio de la rúbrica

| Criterio (puntos) | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Pregunta y cliente (20) | [docs/E0/propuesta.md §1–2](propuesta.md) | ⚠️ COMPLETAR: entrevista real realizada |
| Preguntas analíticas (20) | [docs/E0/propuesta.md §3](propuesta.md) | Variable a pronosticar, factores del experimento y grupos a comparar |
| Plan de recopilación (20) | [docs/E0/propuesta.md §4](propuesta.md) | ⚠️ COMPLETAR: robots.txt y términos leídos con fecha |
| Captura y serie histórica (25) | [extractores/](../../extractores) · [.github/workflows/captura_diaria.yml](../../.github/workflows/captura_diaria.yml) · [data/bronce/](../../data/bronce) · reporte `data/bronce/sniim/manifests/cobertura_<run_id>.csv` | ⚠️ COMPLETAR: periodos reales con datos por producto/mercado y enlace a una ejecución exitosa de Actions |
| Arranque de calidad (15) | [calidad/tiempo-integrante1.csv](../../calidad/tiempo-integrante1.csv) · [calidad/defectos-integrante1.csv](../../calidad/defectos-integrante1.csv) · [calidad/tiempo-integrante2.csv](../../calidad/tiempo-integrante2.csv) · [calidad/defectos-integrante2.csv](../../calidad/defectos-integrante2.csv) · [calidad/bitacora_capturas.csv](../../calidad/bitacora_capturas.csv) · [calidad/objetivos_calidad.json](../../calidad/objetivos_calidad.json) | ⚠️ COMPLETAR: registros reales de ambos integrantes |

## Cómo reproducir
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
python main.py historica --dry-run
python main.py diaria
python main.py validar
```

## Lista de comprobación previa al tag `e0`
- [ ] Entrevista real registrada y propuesta sin marcas ⚠️.
- [ ] robots.txt y términos de ambas fuentes leídos, con fecha, en la propuesta.
- [ ] Serie histórica descargada y reporte de cobertura revisado (≥ 36 periodos o faltantes declarados).
- [ ] Workflow diario ejecutado al menos una vez con éxito (y programado en la rama por defecto).
- [ ] Registros PSP reales de ambos integrantes.
- [ ] Los 3 profesores agregados como colaboradores del repositorio.
- [ ] Tag `e0` creado antes del lunes 9-nov 23:59 (la tarea cierra a las 17:59) y enlace registrado en el formulario y en la tarea.

## Relatoría de etapa
No aplica en E0 (se entrega desde E1).

## Issues de la entrega anterior
No aplica (primera entrega).
