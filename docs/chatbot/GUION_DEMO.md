# Guion de demostración · Asistente de venta (5 minutos)

**Preparación:** abrir `tablero/asistente.html` en un celular o en el navegador en tamaño de celular. Si ya se usó antes, en "Mis datos" elegir "Borrar todo de este teléfono" para empezar en limpio.

| # | Qué hacer | Qué se debe ver |
|---|---|---|
| 1 | Abrir el asistente | Saludo, alertas de hoy y botones de inicio. Aviso: "Sus datos se guardan solo en este teléfono" |
| 2 | Escribir `soy de tecoman` | "Anotado. Municipio: Tecomán" |
| 3 | Escribir con faltas: `a cuanto esta el limon` | Precio de hoy en las centrales más cercanas (Guadalajara ~260 km) y donde mejor pagan, con fecha, fuente SNIIM y el aviso de que en huerta se paga menos |
| 4 | Tocar **¿Vendo o espero?** | Probabilidad de que suba, con su % de confianza y qué hacer |
| 5 | Dictar con el micrófono (Chrome o Android) o escribir: `tengo ocho toneladas de limón número 5 para el lunes` | "Entendí: Limón #5 · 8 t · lunes …" y la pregunta de entrega |
| 6 | Tocar **La recogen en huerta** | Precio de referencia: mayoreo en Guadalajara, pronóstico y **rango en huerta** (lo que históricamente le llega al productor) |
| 7 | Tocar **Que propongan ellos** y luego **Sí, guardar** | Oferta guardada y tarjetas de compradores reales de Tecomán (empacadoras y mayoristas del DENUE, "Sin verificar") con botones WhatsApp, Llamar y Correo |
| 8 | Tocar **Ver ficha de oferta** | Ficha profesional lista para imprimir o guardar en PDF |
| 9 | Tocar **WhatsApp** en un comprador | Se abre WhatsApp con el mensaje de oferta ya escrito; el productor lo revisa y lo envía él mismo. *(En una demo pública no enviar el mensaje: son empresas reales.)* |
| 10 | Tocar **Anotar respuesta**, luego escribir `ofrece 9 pesos el kilo` | Evaluación: si está dentro, abajo o arriba de lo normal y una alternativa de central |
| 11 | Tocar **Aceptar $9.00** y **Ver acuerdo** | Acuerdo de compraventa con precio, cantidad, entrega, anticipo recomendado y firmas |
| 12 | **Registrar entrega**: `7800` · **Registrar cobro**: `70200` | Merma calculada, "Venta cerrada", precio logrado por kg |
| 13 | Cerrar el navegador y volver a abrir `asistente.html` | "Bienvenido de nuevo" y la oferta en **Mis ofertas** con sus 8 estados: **recuerda todo** sin servidor |

**Pruebas automáticas que respaldan la demo:** `node --test tests/js/motor.test.mjs` (154 frases, venta completa, cifras verificadas contra los datos) y `pytest tests/test_asistente.py` (directorio DENUE y paquete de datos).
