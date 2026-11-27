# Reporte técnico final · Observatorio de Agro-Inteligencia Colimense (OAIC)

Equipo: Sebastián Grageda Sandoval (Data Engineer) y José Negrete Orozco (Data Statistician) · Repositorio: [sebastianGS-z/PROYECTO](https://github.com/sebastianGS-z/PROYECTO) · Sitio público: <https://sebastiangs-z.github.io/PROYECTO/>

Este documento permite a un tercero **entender, reproducir y operar** el observatorio. Las cifras citadas se regeneran con los comandos indicados; cuando un número cambia con cada captura diaria se remite al archivo que lo contiene.

## 1. Pregunta y cliente

¿Cuánto y cuándo pagarán las centrales de abasto por el limón, la papaya y el plátano de Colima, a qué plaza conviene enviarlos y cuánto de ese precio llega al productor? Clientes: empacadoras, asociaciones de productores y compradores mayoristas de la región (entrevistas en [docs/E0/entrevistas.md](../E0/entrevistas.md)). Modelo de negocio: [modelo_negocio.md](modelo_negocio.md).

## 2. Arquitectura

```
Fuentes oficiales ──► Extractores éticos ──► Bronce (inmutable, SHA-256) ──► Puerta 1 (Pandera + reglas) ──► Plata ──► Oro (linaje)
 SNIIM · NOAA · INEGI     robots.txt, UA,        sidecar .meta.json            cuarentena con motivo                  │
 SIAP · UN Comtrade       pausa ≥ 1.5 s                                                                                ▼
                                                           Laboratorio (puerta 3: supuestos) ◄── Pronóstico con intervalo · Inteligencia comercial
                                                                                                      │
              CI (puerta 2: ruff, pytest ≥ 60 %, pip-audit, gitleaks, puerta de datos) ──► Tablero público · Reporte · API JSON
```

| Capa | Código | Salida |
|---|---|---|
| Captura | `extractores/`, `pipeline/`, `scripts/captura_*.py`, `.github/workflows/captura_*.yml` | `data/bronce/<fuente>/<año>/<mes>/` + manifiestos y bitácora |
| Plata/Oro | `src/tdl_e1/pipeline.py` | `data/plata/`, `data/oro/panel_mensual.csv`, `data/cuarentena/` |
| Geoespacial | `src/tdl_e2/geoespacial.py`, `scripts/integrar_siap_colima.py` | Marco municipal INEGI, producción SIAP |
| Pronóstico | `src/tdl_e4/observatorio.py` | `data/oro/pronosticos_colima.csv` con intervalos 80/95 % |
| Inteligencia | `src/inteligencia/` | Margen del productor, plazas, calendario, señales, preguntas, reporte, API |
| Laboratorio | `laboratorio/` | Informes E1–E3 en `docs/` |
| Calidad | `calidad/` | Métricas de fiabilidad e ISO/IEC 25012, PSP, auditoría asistida |

## 3. Fuentes y ética

SNIIM (precios mayoristas, scraping ético; sin API), NOAA NCEI (clima diario, API), INEGI Marco Geoestadístico (GeoJSON), SIAP (cierre agrícola municipal, CSV) y UN Comtrade (comercio exterior, API pública). Términos, licencias, riesgos y sesgos por fuente: [docs/etica-datos.md](../etica-datos.md). Cero datos personales: el audio de la entrevista dejó de versionarse y el módulo comercial no guarda teléfonos ni correos.

**Corrección importante (2026-11-27):** NOAA publica con ~2 semanas de rezago y la captura diaria pedía solo "ayer"; por eso 17 de 17 ejecuciones quedaban sin datos. Ahora se consulta una ventana móvil de 30 días.

## 4. Limpieza, integración y puerta de calidad

Faltantes (precios y lluvia no se imputan; temperatura solo en copia de modelado), atípicos (IQR y MAD robusto, marcados, no borrados), normalización, discretización, jerarquías, reducción a panel mensual y resolución de duplicados entre capturas (gana la más reciente; versiones en Bronce). Detalle: [docs/E1/ENTREGA.md](../E1/ENTREGA.md). Contabilidad exacta verificada en CI: parseados = válidos + rechazados + duplicados descartados (`data/plata/reporte_calidad.json`). Las consultas de catálogo nacional (todos los productos a la vez) se procesan aparte y **no** entran al panel mensual porque mezclarían frutas.

## 5. Análisis estadísticos y sus supuestos

| Análisis | Resultado clave | Supuestos | Informe |
|---|---|---|---|
| Series de tiempo (limón #5 Colima → Guadalajara) | Estacionaria (ADF p = 0.005); ARIMA(2,0,0) gana en 6 meses no vistos (MAPE 15 %) | Ljung-Box, Levene, ARCH y Shapiro aprobados → intervalo paramétrico | [laboratorio_series.md](../E1/laboratorio_series.md) |
| Pronóstico operativo (todas las series) | ARIMA por AIC + suavizamientos; selección en 6 meses y holdout en otros 6 | Intervalo conformal empírico (no supone normalidad), cobertura auditada en holdout | `data/oro/pronosticos_colima.csv` |
| Experimento 2³ sobre el extractor | Parser explica 96 % de la variación; lxml + tablas −20.5 %, confirmado | Shapiro p = 0.20, Levene p = 0.91 | [experimento_factorial.md](../E2/experimento_factorial.md) |
| PCA y MANOVA (5 productos × 5 variables) | CP1 = índice de nicho; productos difieren (Pillai, permutación p = 0.001) | Normalidad multivariada rechazada → Pillai + permutación | [multivariado.md](../E3/multivariado.md) |
| Inteligencia comercial | Productor recibe 38 % (limón) y 41 % (papaya) del mayorista en Guadalajara (2025) | Promedios anuales SIAP ponderados por volumen | [reporte_inteligencia.md](reporte_inteligencia.md) |

## 6. Sistema de calidad

Plan SQA (IEEE 730), requerimientos verificables, métricas medidas en CI y documentación en [docs/calidad/](../calidad/). Estado del Sello TDL: [sello_tdl.md](../calidad/sello_tdl.md) — disponibilidad 100 % (14 días), completitud de Oro 100 %, cobertura ≥ 60 %, 0 secretos (gitleaks), reproducibilidad por SHA-256; **pendiente** cerrar la auditoría cruzada externa.

## 7. Cómo operarlo

```bash
python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements-lock.txt
python main.py diaria                    # captura del día (SNIIM + clima con ventana de 30 días)
python main.py precios-catalogo          # catálogo nacional de precios (todas las plazas)
python main.py capas                     # Bronce → Plata → Oro con puerta de calidad
python main.py observatorio --horizonte 3
python main.py inteligencia && python main.py reporte && python main.py preguntas
python -m calidad.metricas               # fiabilidad, frescura e ISO/IEC 25012
python scripts/servir_tablero.py --port 8000   # http://127.0.0.1:8000/tablero/
```

En producción todo lo anterior corre solo: `captura_diaria.yml` (diario), `validacion.yml` (cada push) y `pages.yml` (publica el sitio tras cada captura). Para la demo en vivo: Actions → "Captura diaria TDL" → *Run workflow*; al terminar, el sitio público se actualiza.

**Fallas conocidas y qué hacer:** si SNIIM cambia su HTML, la captura queda `fallida` y el parser guarda el HTML en `data/diagnostico/` para ajustar `extractores/sniim_extractor.py`. Si NOAA no publica, aparece un aviso de frescura en el resumen del job. Si la CI falla por cobertura, agregar pruebas antes de integrar.

## 8. Resultados de la auditoría

Auditoría interna con 14 hallazgos (1 crítico, cerrado): [cierre_hallazgos.md](../calidad/auditoria/cierre_hallazgos.md). Auditoría cruzada recibida: **pendiente de incorporar** en [auditoria_recibida.md](../calidad/auditoria/auditoria_recibida.md). Para la emitida, el borrador con evidencia se genera con `python -m calidad.auditar_repo <url-del-otro-equipo> --etiqueta e1`.

## 9. Lecciones aprendidas

1. **Medir antes de afirmar.** La cobertura "55 %" omitía módulos nunca importados (real: 38 %); el clima "sin publicar" era un error de nuestra ventana de consulta.
2. **Las reglas de rango no bastan.** 1,024 filas de Oro mezclaban frutas distintas y pasaban todas las validaciones; hacía falta una regla semántica (una fila = un producto).
3. **Los experimentos se contaminan.** Una corrida del experimento coincidió con otra carga en la máquina y produjo atípicos; se repitió completo sin carga.
4. **Un intervalo honesto vale más que un número exacto.** El limón varía 22 % al mes en promedio; un pronóstico sin rango engañaría al cliente.
5. **El proceso también se mide.** Los registros PSP se abandonaron después de E0 y no se pueden reconstruir; la retrospectiva lo documenta.
