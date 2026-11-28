# Ventanas de mejora (revisión del 2026-11-27, actualizada tras la integración)

Estado: ✅ integrada · 🟡 parcial · ⏳ pendiente (con lo que hace falta).

## Datos y fuentes

| # | Mejora | Estado | Detalle |
|---|---|---|---|
| 1 | Precios semanales de exportación en EE. UU. (USDA AMS Market News) | ⏳ | El API de MARS pide una clave gratuita que debe tramitar el equipo; hoy el valor de exportación es aduanal anual (UN Comtrade) |
| 2 | 10 años de historia en más centrales | 🟡 | CDMX (Iztapalapa) completa 2016–2026 para limón, papaya, plátano, mango, aguacate y guayaba (mango subió de 55 % a 82 % de cobertura). Ojo: el SNIIM no reporta origen Colima en CDMX, así que sirve como referencia de mercado y no para comparar el limón de Colima; faltan Monterrey, Querétaro y Morelia (~2–3 h cada una al ritmo ético) |
| 3 | Clima local (SMN, estaciones de Tecomán y Armería) | ⏳ | El robots.txt del SMN responde error 500; por la política *fail-closed* no se captura hasta que responda o haya permiso escrito |
| 4 | Precios reales (sin inflación) | ✅ | IPC de México del Banco Mundial (sin token). Se usa en el cambio real de precios, ingreso por hectárea y comparación de cultivos. Es anual: deflactar meses es aproximado y así se declara |
| 5 | Precio al consumidor (PROFECO QQP) | ⏳ | Archivo nacional grande en datos.gob.mx |
| 6 | Coco por pieza | ✅ | Referencia del mismo mes en años anteriores en MXN/pieza (mediana y rango); sin pronóstico porque no hay peso por pieza verificable |
| 7 | Comercio exterior mensual (UN Comtrade con clave) | ⏳ | Registro gratuito en Comtrade |

## Modelos y confianza

| # | Mejora | Estado | Detalle |
|---|---|---|---|
| 8 | Pronóstico de limón | ✅ | Validación 12 + 12 meses en series de ≥ 60 meses, SARIMA en logaritmos y combinación de modelos; el dato parcial del mes resta confianza si diverge |
| 9 | Historial de aciertos | ✅ | `main.py aciertos`: rango, dirección y error fuera de muestra, más registro permanente de cada pronóstico emitido |
| 10 | Mango y guanábana (temporada) | ✅ | Referencia estacional del mismo mes en años anteriores y aviso de meses de temporada |
| 11 | Hueco de junio de 2020 en Guadalajara | ⏳ | Revisar si el SNIIM publica ese mes con otra consulta |

## Producto e interfaz

| # | Mejora | Estado | Detalle |
|---|---|---|---|
| 12 | Alertas | 🟡 | RSS y JSON públicos (`tablero/alertas.xml`) enlazados en el inicio; WhatsApp o correo directo requieren proveedor y consentimiento de cada usuario |
| 13 | Unificar `index.html` y `cliente.html` | 🟡 | Ya comparten la barra de navegación del portal; falta migrar su estilo visual |
| 14 | Prueba de usabilidad con 3 productores | ⏳ | Requiere al equipo en campo |
| 15 | Peso de páginas | ⏳ | `index.html` y `mapa.html` incrustan sus datos |
| 16 | Uso sin conexión (PWA) | ⏳ | — |

## Calidad y operación

| # | Mejora | Estado | Detalle |
|---|---|---|---|
| 17 | Tamaño del repositorio | ⏳ | Bronce crece con cada captura histórica; evaluar Git LFS o publicar Bronce histórico como release |
| 18 | Acciones de GitHub con Node 20 | ⏳ | Actualizar cuando salgan versiones nuevas |
| 19 | Pruebas de scripts antiguos | 🟡 | Los módulos nuevos (alertas, aciertos, inflación) ya tienen pruebas; faltan los capturadores antiguos |
| 20 | Pendientes del equipo | ⏳ | Auditoría cruzada externa, registros PSP y commits de José, correo real en el User-Agent, decisión sobre el audio del historial, carta de un cliente |
