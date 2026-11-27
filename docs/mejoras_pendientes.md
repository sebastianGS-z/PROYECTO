# Ventanas de mejora detectadas (revisión del 2026-11-27)

Ordenadas por impacto en la confiabilidad y el valor para el cliente. Cada una indica qué falta y qué haría falta.

## Datos y fuentes

| # | Mejora | Por qué importa | Qué hace falta |
|---|---|---|---|
| 1 | **Precios reales de exportación en EE. UU.** (USDA AMS Market News: precios semanales de limón, papaya, aguacate y mango de México en mercados terminales) | Hoy el valor de exportación es aduanal anual; un exportador necesita el precio semanal en destino | API pública del USDA; capturador nuevo y conversión caja → kg |
| 2 | **10 años de historia en más centrales** (CDMX, Monterrey, Querétaro, Morelia) | La comparación de plazas solo tiene 12 meses fuera de Guadalajara | ~2–3 h de captura por central al ritmo ético |
| 3 | **Clima local** (estaciones automáticas del SMN en Tecomán, Armería, Coquimatlán) | NOAA solo tiene Manzanillo; por eso la relación clima-precio no es demostrable | Verificar términos de uso del SMN y su formato |
| 4 | **Precios reales (sin inflación)** con el INPC de INEGI | Comparar 2016 con 2026 sin deflactar exagera las alzas | Token gratuito de INEGI (lo debe tramitar el equipo) |
| 5 | **Precio al consumidor** (PROFECO Quién es Quién en los Precios) | Completa la cadena productor → mayoreo → consumidor | Descarga desde datos.gob.mx (archivo nacional grande) |
| 6 | **Coco por pieza** | El coco tiene 96 % de cobertura pero se cotiza por pieza y hoy no se pronostica | Soportar series en MXN/pieza en el pronóstico y las respuestas |
| 7 | **Comercio exterior mensual** (UN Comtrade con clave gratuita) | Permite ver en qué meses compra cada país | Registro gratuito en Comtrade; el API público solo da datos anuales |

## Modelos y confianza

| # | Mejora | Situación actual |
|---|---|---|
| 8 | **Pronóstico de limón** | 48 % de confianza: el SARIMA ganó la validación, pero el dato parcial de noviembre ya diverge. Probar variables externas (volumen SIAP, lluvia), transformación logarítmica y ventanas de validación de 12 + 12 meses ahora que hay 76 meses continuos |
| 9 | **Historial de aciertos** | Publicar cada mes el pronóstico frente a lo observado para medir la cobertura real del rango con el tiempo |
| 10 | **Mango y guanábana** (fruta de temporada) | No pueden tener 36 meses continuos; usar un modelo de temporada (mismo mes de años anteriores) |
| 11 | **Hueco de junio de 2020** | Todas las series de Guadalajara tienen un mes sin cotización ahí, y por eso los pronósticos usan 76 meses y no 120. Revisar si el SNIIM publica ese mes con otra consulta |

## Producto e interfaz

| # | Mejora | Detalle |
|---|---|---|
| 12 | **Alertas por WhatsApp o correo** | Las señales ya se calculan; falta el envío, con consentimiento de cada usuario |
| 13 | **Unificar el estilo** de `index.html` y `cliente.html` | Son las vistas más antiguas; las nuevas (inicio, preguntas, mapa, administración) comparten otro diseño |
| 14 | **Prueba de usabilidad** con 3 productores | Medir si encuentran el pronóstico, la calculadora y la central conveniente sin ayuda |
| 15 | **Peso de páginas** | `index.html` (548 KB) y `mapa.html` (405 KB) incrustan sus datos; cargarlos aparte acelera el celular |
| 16 | **Uso sin conexión** (PWA) | Consultar en campo sin señal |

## Calidad y operación

| # | Mejora | Detalle |
|---|---|---|
| 17 | **Tamaño del repositorio** | Bronce ya ocupa ~250 MB; evaluar Git LFS o publicar Bronce histórico como release |
| 18 | **Acciones de GitHub con Node 20** | GitHub avisa que se retiran; actualizar `actions/checkout`, `setup-python`, `upload-artifact` y `gitleaks-action` cuando salgan versiones nuevas |
| 19 | **Pruebas de los scripts antiguos** | `capturar_comercio_internacional.py`, `capturar_sniim_catalogo.py` y `preparar_mapa_mercados.py` tienen poca cobertura |
| 20 | **Pendientes del equipo** | Auditoría cruzada externa, registros PSP y commits de José, correo real en el User-Agent, decisión sobre borrar el audio del historial de Git, carta de un cliente |
