# Relatoría de etapa E2

**Fecha:** 2026-11-17
**Proyecto:** Observatorio de Agro-Inteligencia Colimense

## Trabajo realizado

Se revisaron las opciones de fuente geoespacial. OpenStreetMap Overpass se descartó porque el `robots.txt` del endpoint consultado prohíbe `/api/`. En su lugar se eligió el servicio oficial GeoJSON del Marco Geoestadístico del INEGI, que proporciona límites municipales de Colima y atributos censales agregados. La selección sigue el principio de no automatizar consultas prohibidas.

Se agregó un extractor dedicado que verifica las reglas de acceso del host, valida la estructura FeatureCollection, guarda la respuesta original y emite un manifiesto. GeoPandas procesa los municipios, identifica en qué municipio cae el punto de la estación NOAA de Manzanillo, genera una tabla municipal para Plata/Oro y representa el estado, las tres áreas de interés y la estación en un mapa.

Se amplió el esquema interno de Bronce-Plata para retener el índice de cada registro dentro del archivo fuente. El panel mensual de Oro agrega esas referencias en campos de linaje para precios y clima, incluyendo archivo, hash, fecha UTC e índice de registro; en grupos con capturas duplicadas se listan todas las versiones revisadas. Al verificar el punto de estación contra los polígonos, se detectó que la coordenada previa era aproximada y caía fuera de Manzanillo. Se corrigió usando la ubicación publicada en el catálogo oficial NOAA GHCN-Daily: 19.0500° N, 104.3170° O, la cual cae dentro del municipio 06007.

La declaración ética cubre términos, robots.txt, atribución, minimización de datos, sesgos y diferencias de periodo entre la geometría de 2025 y los atributos de población del Censo 2020.

## Decisiones y limitaciones

- La capa municipal de INEGI se mantiene como dimensión geoespacial separada en Oro. No se adjunta población municipal a las cotizaciones de mercados de Guadalajara o CDMX porque esa unión daría una relación espacial falsa.
- El punto NOAA representa una estación meteorológica; no representa cada parcela del estado.
- El conteo poblacional corresponde al Censo 2020 y no debe leerse como población actual ni como producción agrícola.
- El tag `e2` se generará después de verificar la captura, productos y workflow publicados.

## Evidencias

- [Ficha técnica E2](E2/ENTREGA.md)
- [Declaración de ética y legalidad](etica-datos.md)
- [Mapa geoespacial E2](E2/mapa_marco_geoestadistico_colima.png)

## Pendientes de cierre

1. Ejecutar `python main.py e2` en el entorno con las dependencias instaladas y revisar el producto y el mapa resultantes.
2. Confirmar un workflow exitoso en GitHub Actions tras añadir el extractor INEGI y la integración de linaje.
3. Publicar los cambios y crear el tag `e2` apuntando al commit final.
4. Registrar el enlace del repositorio en el formulario oficial.
