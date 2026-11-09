# TRUSTED DATA LAB (TDL) — Observatorio de Agro-Inteligencia Colimense (OAIC)

Entrega **E0** · Componente: **Máquina de Captura (Capa Bronce) + Sistema de Calidad Inicial (PSP)**.

## 1. Descripción
Sistema modular en Python que captura datos crudos de dos fuentes públicas y los guarda sin alterarlos, con trazabilidad e integridad (SHA-256):

* **SNIIM** (Secretaría de Economía): precios mayoristas de **plátano, limón y papaya** en **Guadalajara** (Mercado de Abasto) y **Ciudad de México** (Central de Abasto de Iztapalapa).
* **NOAA NCEI** (GHCN-Daily, Access Data Service): temperatura media/máx/mín y precipitación de la estación de **Manzanillo, Colima** (la más cercana a las zonas productoras). *Open-Meteo y NASA POWER se descartaron porque su robots.txt prohíbe el acceso a sus APIs.*

## 2. Objetivo
Alimentar la Capa Bronce de una arquitectura Medallion. **No** limpia, deduplica, imputa ni transforma: eso corresponde a capas posteriores.

## 3. Arquitectura
```
config → extractores (HTTP ético + parseo) → pipeline → almacenamiento (Bronce + manifiesto) → validación
                                                          └→ calidad (PSP, objetivos)
```
| Capa | Módulo | Responsabilidad |
|---|---|---|
| Configuración | `config/settings.py`, `localidades.json`, `fuentes.json` | UA, timeout, reintentos, pausa, rutas, coordenadas, fuentes |
| Transporte HTTP | `extractores/base.py` | robots.txt (fallo cerrado), Crawl-delay, pausa ≥1.5 s por dominio compartida entre instancias, reintentos con backoff, validación |
| Extracción | `sniim_extractor.py`, `weather_extractor.py` | Todo el conocimiento del HTML/JSON de cada fuente |
| Almacenamiento | `almacenamiento/bronze_writer.py` | Original intacto + sidecar `.meta.json`, creación exclusiva (inmutable) |
| Registro | `almacenamiento/manifest.py` | Manifiesto por ejecución y fuente con estado final |
| Integridad | `scripts/validar_bronce.py` | Recalcula SHA-256 y verifica manifiestos |
| Calidad PSP | `calidad/psp.py` | Tiempo neto, defectos, catálogo D01–D10, objetivos OQ1–OQ3 |

Estados de ejecución: `exitosa`, `parcial`, `sin_resultados`, `fallida`. Una fuente que falla **nunca** queda como exitosa. Códigos de salida: `0` exitosa/sin_resultados · `1` fallida · `2` parcial.

## 4. Estructura
```
tdl-equipo-agrocolima/
├── extractores/  almacenamiento/  calidad/  scripts/  config/  tests/  pipeline/   (estructura del Kit)
├── docs/E0/{propuesta,ENTREGA}.md   laboratorio/  tablero/  data/{bronce,plata,oro,cuarentena}/
├── data/bronce/{sniim,noaa_ncei}/<AAAA>/<MM>/…   y   …/manifests/
├── logs/   .github/workflows/captura_diaria.yml
├── pipeline/ (orquestación)   main.py (CLI)   requirements.txt   pytest.ini
```
Archivo Bronce: `data/bronce/<fuente>/<año>/<mes>/<fuente>__<etiqueta>__<ini>_<fin>__<run_id>.<html|json>` + `.meta.json`.

## 5–7. Instalación
Requisitos: Python 3.11+.
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
(`pandas` no se usa: no es necesario para guardar crudos.)

## 8. Configuración
`cp .env.example .env` y ajusta. Parámetros: `TDL_USER_AGENT`, `TDL_TIMEOUT`, `TDL_MAX_RETRIES`, `TDL_BACKOFF_BASE`, `TDL_MIN_DELAY` (1.5 s), `TDL_DATA_DIR`, `TDL_LOG_LEVEL`, URLs de las fuentes. **Cambia el correo de contacto del User-Agent por el real del equipo.**
Coordenadas y mercados: `config/localidades.json` (aproximadas; verifíquenlas) y `config/fuentes.json`.

## 9. Captura diaria
```bash
python main.py diaria                       # ayer (hora de Colima), ambas fuentes
python main.py diaria --fecha 2026-11-06 --solo clima
```
NOAA NCEI puede tardar en publicar los días más recientes; los días sin dato no aparecen y no se rellenan.

## 10. Captura histórica (36 meses)
```bash
python main.py historica --dry-run                      # plan sin red
python main.py historica                                # últimos 36 meses completos
python main.py historica --productos platano --mercados cdmx --max-consultas 5   # prueba pequeña
python main.py historica --incluir-mercados-opcionales  # añade Colima y Felipe Ángeles
```
Genera `data/bronce/sniim/manifests/cobertura_<run_id>.{json,csv}`: un periodo (mes) cuenta **solo** si la fuente devolvió registros reales. Los meses sin datos o fallidos se listan; la existencia de 36 archivos no equivale a 36 periodos.
Datos sintéticos (solo pruebas): `python scripts/generar_sinteticos.py` → `data/sintetico/SINTETICO_*.csv`, nunca en `data/bronce`.

## 11. Validación de la Capa Bronce
```bash
python main.py validar            # SHA-256 de cada archivo + manifiestos
```

## 12. Sistema PSP
```bash
python -m calidad.psp tiempo --archivo calidad/tiempo-integrante1.csv --fecha 2026-11-08 \
    --inicio 09:00 --fin 10:30 --interrupcion 10 --fase Codificación --actividad "Extractor base"
python -m calidad.psp defecto --archivo calidad/defectos-integrante1.csv --fecha 2026-11-08 \
    --tipo D05 --introducido Codificación --eliminado Pruebas --minutos 15 --descripcion "Parser ignora filas"
python -m calidad.psp resumen --archivo calidad/tiempo-integrante1.csv
python -m calidad.psp validar --tiempo calidad/tiempo-integrante1.csv --defectos calidad/defectos-integrante1.csv
```
Fases (estilo del Kit; se aceptan sinónimos con acentos): planeacion, diseno, codigo, revision, compilacion, pruebas, correccion, documentacion. Tiempo neto = fin − inicio − interrupción. Los CSV están **vacíos** (solo encabezados): registren tiempos y defectos reales.
Tipos de defecto (`calidad/catalogo_defectos.json`): los diez de PSP que exige el Kit: documentacion, sintaxis, construccion, asignacion, interfaz, verificacion, datos, funcion, sistema y entorno (cada uno con un ejemplo del proyecto).
Bitácora de capturas: `calidad/bitacora_capturas.csv` (una fila por ejecución y fuente; base de MTBF/MTTR/disponibilidad en E1).
Objetivos (`calidad/objetivos_calidad.json`): OQ1 disponibilidad ≥ 95 %, OQ2 cero fallos no detectados, OQ3 cobertura diaria 100 %. Evaluación: `python main.py objetivos --desde AAAA-MM-DD --hasta AAAA-MM-DD` (devuelve `sin_datos` si no hay manifiestos; no hay metas "alcanzadas" sin evidencia).

## 13. Pruebas
```bash
python -m pytest -q                                    # unitarias, sin red (71)
RUN_INTEGRATION=1 python -m pytest -m integration -s   # contra SNIIM y NOAA NCEI reales
```
Los HTML/JSON de las pruebas unitarias son *fixtures* controlados, no capturas reales.

## 14. GitHub Actions
`.github/workflows/captura_historica.yml`: manual, descarga la serie de 36 meses en la nube. `.github/workflows/captura_diaria.yml`: diario a las **03:00 UTC = 21:00 en Colima** (UTC-6 todo el año desde 2022) y manual (`workflow_dispatch`). `concurrency` evita ejecuciones simultáneas; permisos mínimos `contents: write`; instala dependencias, corre pruebas, captura, valida, publica `data/` con `GITHUB_TOKEN` (sin PAT) aunque la captura falle (para dejar evidencia), sube logs como artefacto y falla el job si el código de salida ≠ 0. Habilita *Settings → Actions → Workflow permissions → Read and write*. Los `schedule` solo corren desde la rama por defecto.

## 15. Limitaciones conocidas
* **SNIIM sin API oficial**: se usa la consulta web pública. El parser (`parse_resultados`) se escribió según la estructura observada y **debe validarse con la primera ejecución real** (`pytest -m integration`). Si el sitio cambia, solo se ajustan `parse_formulario` y `parse_resultados`; un cambio de estructura produce estado `fallida`, nunca datos inventados.
* La URL de resultados usa el patrón observado; que acepte rangos mensuales y la paginación (`RegistrosPorPagina=500`) no está verificado: si la fuente reporta varias páginas, la captura queda `parcial`.
* Tecomán/Armería no son mercados del SNIIM; las zonas productoras se cubren con clima. "Colima: Centros de distribución" es opcional.
* "Ciudad de México" = Central de Abasto de Iztapalapa; "Guadalajara" = Mercado de Abasto (el Felipe Ángeles es opcional).
* GitHub Actions puede ser bloqueado por el sitio (IPs de centros de datos): quedaría registrado como fallida.
* NOAA NCEI: una sola estación (Manzanillo), no Tecomán; verificar el ID con `curl -s "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&stations=MXM00076654&startDate=2024-01-01&endDate=2024-01-05&dataTypes=TMAX,TMIN,PRCP&format=json&units=metric"`.

## 16. Consideraciones éticas
User-Agent identificable, robots.txt obligatorio (si no se puede leer, **no se hace scraping**), Crawl-delay y pausa ≥ 1.5 s por dominio, sin proxies, sin evadir protecciones, volumen bajo. NOAA NCEI: revisar términos, atribución y límites de uso antes de publicar resultados.

## 17. Ejemplo de ejecución
```
$ python main.py diaria --fecha 2026-11-06
… RESUMEN run=20261108T090133Z-332bb7 fuente=sniim estado=fallida … solicitudes=2 registros=0 archivos=0 errores=1
… Fin captura diaria … estados={'sniim': 'fallida', 'noaa_ncei': 'fallida'} codigo_salida=1
```
(Ejemplo real ejecutado en un entorno **sin acceso a Internet**: demuestra que una fuente inaccesible queda registrada como fallida con manifiesto.)
