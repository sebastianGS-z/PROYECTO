# Entrega E0 · Observatorio de Agro-Inteligencia Colimense (OAIC)

Equipo: Grageda Sandoval Sebastián y Jose Negrete Orozco · Etiqueta: `e0` · Tablero: no aplica en E0 (se publica desde E1)

## Resumen en tres líneas
1. Observatorio de precios mayoristas de limón, plátano y papaya (SNIIM) cruzados con clima de Tecomán y Colima (NOAA NCEI) para decidir cuándo vender.
2. Captura ética automática a la capa bronce con GitHub Actions, trazabilidad por SHA-256 y bitácora de ejecuciones.
3. Sistema de calidad inicial (PSP) con cuatro archivos individuales inicializados, registros de Sebastián, registros de José pendientes y tres objetivos medibles.

> E0 tiene una sola rúbrica (100 puntos) que vale igual en las tres materias.

## Evidencia por criterio de la rúbrica

| Criterio (puntos) | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Pregunta y cliente (20) | [docs/E0/propuesta.md §1–2](propuesta.md) | Tres entrevistas a ingenieros agrónomos (ver entrevistas.md) |
| Preguntas analíticas (20) | [docs/E0/propuesta.md §3](propuesta.md) | Variable a pronosticar, factores del experimento y grupos a comparar |
| Plan de recopilación (20) | [docs/E0/propuesta.md §4](propuesta.md) | robots.txt de las fuentes evaluadas en el Anexo de la propuesta (2026-11-09) |
| Captura y serie histórica (25) | [extractores/](../../extractores) · [.github/workflows/captura_diaria.yml](../../.github/workflows/captura_diaria.yml) · [data/bronce/](../../data/bronce) · reporte `data/bronce/sniim/manifests/cobertura_<run_id>.csv` | SNIIM 36/36 meses por producto y mercado; clima 28/36 meses (propuesta §5). Actions: https://github.com/sebastianGS-z/PROYECTO/actions |
| Arranque de calidad (15) | [calidad/tiempo-sebastian.csv](../../calidad/tiempo-sebastian.csv) · [calidad/defectos-sebastian.csv](../../calidad/defectos-sebastian.csv) · [calidad/tiempo-jose.csv](../../calidad/tiempo-jose.csv) · [calidad/defectos-jose.csv](../../calidad/defectos-jose.csv) · [calidad/bitacora_capturas.csv](../../calidad/bitacora_capturas.csv) · [calidad/objetivos_calidad.json](../../calidad/objetivos_calidad.json) | Objetivos definidos y cuatro archivos abiertos; los dos archivos de José siguen sin registros y requieren sus datos reales. |

## Cómo reproducir
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
python main.py historica --dry-run
python main.py diaria
python main.py validar
```

## Estado de cierre de E0 (revisión 2026-11-13)
- [x] Propuesta con ficha, tres preguntas analíticas y tres entrevistas documentadas; la entrevista principal contiene cinco preguntas y duración de 18 minutos.
- [x] robots.txt y condiciones de uso revisadas para ambas fuentes y documentadas con fecha en la propuesta.
- [x] SNIIM: 36/36 meses por producto/mercado. NOAA: 28/36 meses; los meses faltantes están declarados y no se rellenaron.
- [ ] Captura programada estable: las cuatro ejecuciones programadas más recientes fallaron antes de capturar porque una prueba buscaba archivos PSP con nombres obsoletos. La expectativa de nombres ya se corrigió localmente y la suite pasó con 72 pruebas; falta publicar el cambio y confirmar una nueva ejecución verde en GitHub Actions.
- [ ] PSP de ambos integrantes: Sebastián tiene entradas. Los archivos de José están creados, pero vacíos; faltan sus registros reales de tiempo y defectos.
- [ ] Invitación de los tres profesores: GitHub muestra un colaborador aceptado y una invitación pendiente además del dueño; hace falta confirmar que corresponden a los tres profesores y completar las invitaciones faltantes.
- [x] Tag `e0` creado el 2026-11-09 17:24 (hora local, antes del límite de 23:59).
- [ ] Registro de la URL del repositorio en Classroom: no hay evidencia en el repositorio; falta confirmar la tarea de Classroom y realizar/validar el envío.

## Relatoría de etapa
No aplica en E0 (se entrega desde E1).

## Issues de la entrega anterior
No aplica (primera entrega).
