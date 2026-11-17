# Entrega E2 · Observatorio de Agro-Inteligencia Colimense

**Repositorio:** [sebastianGS-z/PROYECTO](https://github.com/sebastianGS-z/PROYECTO)
**Tag de entrega:** `e2` (se creará al cerrar y publicar esta etapa)
**Fecha de preparación:** 2026-11-17

## Entregables

### 1. Fuente especializada geoespacial

Se integra el servicio GeoJSON del Marco Geoestadístico municipal de INEGI para Colima, endpoint `https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/06`. La respuesta se conserva intacta en Bronce con manifiesto, sidecar y SHA-256. GeoPandas reproyecta la capa a EPSG:4326 para asignar la estación meteorológica configurada a su polígono municipal y a EPSG:32613 para estimar superficie. Las coordenadas de la estación vienen del catálogo oficial NOAA GHCN-Daily. El producto geoespacial municipal y el mapa se generan en el pipeline E2.

Captura integrada: run `20261117T134546Z-02486d`, **10 municipios**, archivo `inegi_marco__marco-municipal-colima__2026-11-17_2026-11-17__20261117T134546Z-02486d.geojson`, SHA-256 `a345fd583e0b9c35ecc84c1494c40b5999338c8a33b134c9ad28e4e1d2635571`, ingesta `2026-11-17T13:45:48Z`.

Archivos generados:

- Bronce: `data/bronce/inegi_marco/` (GeoJSON, metadatos y manifiesto).
- Plata: `data/plata/marco_geoestadistico_colima.csv`.
- Reporte de procesamiento: `data/plata/reporte_geoespacial_e2.json`.
- Oro: `data/oro/contexto_geoespacial_municipal.csv`.
- Mapa: [mapa del Marco Geoestadístico de Colima](mapa_marco_geoestadistico_colima.png).

El producto es una dimensión geográfica agregada. No se une población municipal a los precios por mercado porque las unidades territoriales y las unidades de cotización no son equivalentes.

### 2. Ética y legalidad

La declaración está en [docs/etica-datos.md](../etica-datos.md), con condiciones de uso, robots.txt, licencias/atribución, privacidad, minimización, sesgos y restricciones de interpretación para las tres fuentes.

### 3. Linaje de Oro

Cada agregación de precio de `data/oro/panel_mensual.csv` conserva `linaje_precios_bronce`: una lista de registros fuente con ruta, SHA-256, timestamp de ingesta UTC e índice de fila. El campo `linaje_clima_bronce` identifica de forma equivalente los registros meteorológicos asociados por estación y mes. Si se resolvieron duplicados, el linaje conserva las versiones consideradas. La última ejecución verificó **712 filas de Oro**, **14,338 referencias Bronce de precio** y **15,545 de clima**. La dimensión geoespacial de Oro identifica archivo de Bronce, hash, fecha de ingesta e índice `FeatureCollection.features[n]` de cada municipio. El reporte de Plata registra CRS, ediciones de fuente, asignación de estación y productos generados.

### 4. Ejecución y reproducibilidad

```bash
pip install -r requirements.txt
python main.py e2
```

`main.py e2` captura el GeoJSON oficial respetando robots.txt, lo almacena inmutable en Bronce, regenera Plata/Oro del pipeline E1 y construye el CSV municipal y el mapa. `python main.py e2 --solo-procesar` vuelve a generar los productos usando el GeoJSON más reciente ya guardado.

El workflow diario de GitHub Actions incorpora la ejecución E2 después de la captura diaria. Se creará el tag `e2` después de publicar los cambios y comprobar una ejecución remota exitosa. El enlace se registrará en el formulario oficial.
