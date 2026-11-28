# Plan: asistente de venta "OAIC Vende" (versión 2, ajustada)

Versión 2 · 2026-11-27 · Sustituye a la versión 1 (servidor con IA), que queda como fase posterior (sección 9).

**Estado (2026-11-28): implementado.** Ver `tablero/asistente.html`, `tablero/asistente/`, `src/inteligencia/asistente.py`, `scripts/capturar_denue.py`, pruebas en `tests/js/` y `tests/test_asistente.py`, y el [guion de demo](GUION_DEMO.md). Directorio: 2,913 empresas compradoras con contacto (1,235 con teléfono) en Colima, Jalisco, Michoacán, Ciudad de México y Nuevo León.

## 0. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Alcance | **Venta completa sin pagos**: consultar, ofrecer, encontrar compradores, contactarlos, negociar, cerrar el acuerdo, entregar y dar seguimiento. El pago va directo entre comprador y productor |
| Canal | **Dentro de la página** del observatorio: un chat privado para cada productor, con memoria |
| Plazo | **2 días** |
| IA | **Sin modelo de IA** en esta versión (ver sección 1) |

## 1. ¿Se puede sin modelo de IA? Sí

El asistente funciona con **reglas y flujos guiados**:
- reconoce la fruta, las cantidades, los precios, las fechas y los municipios dentro del texto (palabras clave, sinónimos, tolerancia a faltas de ortografía y números escritos como "ocho toneladas");
- ofrece **botones de respuesta rápida** en cada paso, para que el productor casi no tenga que escribir.

| | Sin IA (esta versión) | Con IA (fase posterior) |
|---|---|---|
| Costo por conversación | **$0** | ~USD 0.01–0.02 por turno |
| Servidor | **No hace falta** (funciona en GitHub Pages) | Sí, para proteger la clave de API |
| Precisión de cifras | **Exacta**: siempre sale de los datos | Exacta solo si se fuerza el uso de herramientas |
| Frases libres o raras ("¿y si me espero a que pase el norte?") | Limitada: responde con opciones | Muy buena |
| Privacidad | **Los datos nunca salen del teléfono** del productor | Pasan por el servidor y el proveedor de IA |
| Se puede demostrar sin internet ni cuentas | Sí | No |

Para la demo y para un productor real, la versión sin IA es más confiable y gratuita. La capa de IA se puede agregar después **sin rehacer nada**: usaría las mismas "herramientas" (funciones) que ya llaman los flujos.

## 2. Qué hace (funciones de la versión de 2 días)

1. **Chat privado con memoria**
   - Todo se guarda **en el navegador del productor** (IndexedDB): su perfil (nombre opcional, municipio, cultivos, hectáreas), conversaciones, ofertas, compradores contactados y respuestas.
   - Nada se envía al observatorio, así que se mantiene la política de **cero datos personales** del proyecto.
   - Botones "Exportar mi información" y "Importar" (archivo JSON) para cambiar de teléfono, y "Borrar todo".
2. **Preguntas**
   - Las 17 respuestas por fruta que ya calcula el observatorio, con fuente y % de confianza.
   - Ejemplos: "¿a cuánto está el limón?", "¿vendo o espero?", "¿qué central paga más?", "¿puedo exportar?".
3. **Centrales de abasto**
   - Precio actual y de los últimos meses en cada central y diferencia contra Guadalajara.
   - Distancia aproximada desde el municipio del productor y flete de equilibrio.
4. **Demanda**
   - **Lo que hay:** estacionalidad, compras de otros países (UN Comtrade), señales de precio alto o bajo, y cuántos mayoristas y empacadoras hay por ciudad (DENUE).
   - **Lo que no hay:** volúmenes de compra por central; esos datos no existen públicamente y el asistente lo dice.
5. **Directorio de compradores con teléfonos de empresas**
   - Viene del **DENUE de INEGI**, que es público: nombre del establecimiento, actividad, dirección, teléfono, correo y página web que la propia empresa declaró.
   - Filtrado a actividades compradoras de fruta:
     - comercio al por mayor de frutas y verduras;
     - empacadoras y procesadoras;
     - bodegas en centrales de abasto;
     - exportadoras.
   - Cubre Colima y los estados de las centrales que el observatorio sigue.
   - Solo establecimientos (empresas), nunca personas particulares. Cada registro muestra "fuente: DENUE, fecha" y la etiqueta **"sin verificar"** hasta que el productor confirme que el contacto sirvió.
6. **Contactar gente** sin servidor y sin que el sistema hable en nombre del productor:
   - botón **WhatsApp** (abre WhatsApp con el mensaje de oferta ya escrito para ese comprador, con `wa.me`);
   - botón **Llamar** (`tel:`) y botón **Correo** (`mailto:` con asunto y cuerpo listos);
   - el productor revisa y envía. El asistente registra "contactado el día X" en su memoria.
7. **Vender (flujo completo)**
   1. **Crear oferta.** El flujo guiado pide fruta, variedad o calidad, kg, fecha disponible, lugar de entrega y empaque.
   2. **Precio sugerido.** Rango basado en el precio actual, el pronóstico, la mejor central menos el flete y la prima de exportación, con la fuente de cada número.
   3. **Ficha de oferta profesional** para imprimir, guardar en PDF o compartir, con la referencia de precios del observatorio.
   4. **Compradores sugeridos.** Se ordenan por actividad, cercanía, tamaño del establecimiento y si ya respondieron antes.
   5. **Contacto** a uno o varios compradores (mensajes personalizados).
   6. **Seguimiento.** El productor anota la respuesta ("ofreció $X", "no le interesa", "pidió muestra"). El asistente compara la contraoferta con el precio de referencia y aconseja ("está 8 % debajo del mayoreo en Guadalajara; si su flete cuesta menos de $1.20/kg, le conviene más la central").
   7. **Cerrar el acuerdo.** El asistente genera el acuerdo de compraventa (precio, kg, calidad, fecha, lugar, forma de pago y anticipo recomendado) para imprimir o firmar y lo envía por WhatsApp.
   8. **Entrega y pago.** El productor registra el peso recibido, la merma y si ya cobró. Se calcula el ingreso real contra el esperado.
   9. **Historial.** Ventas cerradas, precio promedio logrado contra el mayoreo y los mejores compradores.
8. **Alertas** del observatorio de las frutas del productor, mostradas al abrir el chat.

**Máquina de estados** de cada oferta (en código, no "a criterio del bot"):
`borrador → lista → contactando → negociando → acordada → entregada → cobrada → cerrada` (más `cancelada`). Cada cambio guarda fecha y motivo.

## 3. Arquitectura (sin servidor)

```
GitHub Actions (diario)                         Navegador del productor
┌────────────────────────────┐                 ┌──────────────────────────────────────────┐
│ python main.py asistente   │  JSON compactos │ tablero/asistente.html                    │
│  · precios actuales        │ ──────────────► │  · motor de reglas (JS, sin dependencias) │
│  · pronósticos + aciertos  │  (~1–2 MB)      │  · flujos guiados + botones               │
│  · 17 respuestas × fruta   │                 │  · memoria local (IndexedDB)              │
│  · centrales + distancias  │                 │  · contacto: wa.me / tel: / mailto:       │
│  · exportación + alertas   │                 │  · ficha de oferta y acuerdo (imprimir)   │
│  · directorio DENUE        │                 │  · voz opcional (dictado del navegador)   │
└────────────────────────────┘                 └──────────────────────────────────────────┘
```

- **Datos:** `data/publico/asistente/*.json`, generados por un comando nuevo `python main.py asistente`, divididos por fruta para que el celular cargue poco.
- **Voz:** botón de micrófono con el dictado del navegador (Web Speech API, Chrome y Android). Es opcional. El texto dictado siempre se muestra para que el productor lo corrija antes de enviarlo. En Chrome el dictado lo procesa Google y así se avisa; quien no quiera puede escribir.
- **Sin dependencias externas** en el chat: funciona sin conexión después de la primera carga.

## 4. Fuente nueva: DENUE (directorio de empresas)

- **Qué:** descarga masiva oficial de INEGI en CSV por estado. Es información pública que declaran las propias unidades económicas. La descarga no pide token (la API del DENUE sí).
- **Cómo:**
  - un extractor nuevo con las mismas reglas éticas del proyecto: robots.txt, User-Agent identificable, pausa entre solicitudes, archivo original y SHA-256 en Bronce;
  - el filtro por código SCIAN y la limpieza van en Plata;
  - el directorio publicado va en `data/publico/asistente/compradores.json`.
- **Códigos SCIAN a incluir** (se confirman contra el catálogo al procesar):
  - comercio al por mayor de frutas y verduras frescas (4311);
  - comercio al por mayor de abarrotes (4311 y 4312) con frutas;
  - industria de conservación de frutas (3114);
  - almacenamiento con refrigeración (4931);
  - comercio al por menor en mercados y centrales (4611), solo establecimientos grandes.
- **Estados:** Colima, Jalisco, Michoacán, Ciudad de México y Nuevo León al inicio. El resto se agrega con el mismo comando.
- **Cuidados:**
  - se excluyen registros sin razón social, que pueden ser personas físicas;
  - no se publica nada que el DENUE no publique;
  - cada contacto lleva la fecha de corte del DENUE;
  - un botón "este número no sirve" lo marca en la memoria local del productor.

## 5. Calendario de 2 días

**Día 1: datos y motor**

| Bloque | Trabajo | Listo cuando |
|---|---|---|
| Mañana | Extractor DENUE, filtro SCIAN y directorio de compradores. `main.py asistente` genera los JSON compactos (precios, centrales con distancia, respuestas, exportación, alertas) | JSON validados con pruebas; directorio con ≥ 200 empresas compradoras en Colima y Jalisco |
| Tarde | Motor de reglas en JS: reconocimiento de fruta, cantidades, precios, fechas y municipios; intenciones (precio, pronóstico, central, exportar, vender, compradores, ayuda); flujos guiados; memoria en IndexedDB; máquina de estados | Pruebas en Node: ≥ 95 % de 150 frases de productores reconocidas con la intención y las cifras correctas |

**Día 2: venta, interfaz y demostración**

| Bloque | Trabajo | Listo cuando |
|---|---|---|
| Mañana | Flujo de venta completo: oferta, precio sugerido, ficha, compradores sugeridos, contacto (wa.me, tel y correo), seguimiento de respuestas, contraoferta comparada, acuerdo, entrega, cobro e historial | Prueba de extremo a extremo en el navegador que recorre los 8 estados |
| Tarde | Interfaz para celular, botón de micrófono, exportar/importar/borrar, enlace desde todas las páginas, integración en los flujos diario y de validación, documentación y guion de demo | Revisión en el navegador sin errores, prueba en tamaño de celular, CI en verde y demo grabable |

## 6. Cómo se demuestra que funciona

1. **Pruebas automáticas** en la integración continua:
   - Python: los JSON del asistente coinciden con las cifras del observatorio, el directorio solo trae actividades compradoras y no hay registros sin razón social;
   - Node: el reconocimiento de 150 frases reales de productor (con faltas de ortografía, números con letra y modismos), la máquina de estados y los mensajes de contacto;
   - navegador: una conversación completa de venta.
2. **Garantía de cifras:** una prueba recorre todas las respuestas del chat y comprueba que cada número aparece en los datos del observatorio. **El asistente no puede inventar un precio.**
3. **Guion de demo (5 minutos):**
   1. abrir el asistente desde el celular;
   2. preguntar "a cuanto esta el limon" (con faltas);
   3. preguntar "¿vendo o espero?";
   4. decir "tengo 8 toneladas para el lunes en Tecomán";
   5. ver el precio sugerido con su fuente;
   6. ver la ficha de oferta;
   7. ver 10 compradores reales de Colima y Jalisco;
   8. tocar WhatsApp: se abre con el mensaje listo;
   9. registrar una contraoferta y recibir el consejo;
   10. generar el acuerdo;
   11. registrar entrega y cobro;
   12. cerrar el navegador, volver a abrirlo y ver que **recuerda todo**.
4. **Prueba con productores reales** (después de los 2 días): 3 productores usan el asistente una semana. Se mide si contactaron compradores y si cerraron alguna venta, y se registra en `operaciones_piloto.csv` solo con ventas reales.

## 7. Límites honestos (se dicen en la interfaz)

- El directorio DENUE dice qué empresas existen y su teléfono público. **No dice si hoy están comprando.** La demanda real se confirma al contactarlas.
- El asistente **no envía mensajes solo**: prepara el mensaje y el productor lo manda desde su WhatsApp. Esto es una ventaja de confianza y de ley (no hace falta manejar datos de terceros ni la API de WhatsApp Business).
- La memoria vive en el navegador: si el productor borra los datos del navegador sin exportarlos, se pierde. Por eso hay un recordatorio para exportar.
- Sin IA, las frases muy libres reciben opciones en lugar de una respuesta exacta.

## 8. Estructura de código

```
scripts/capturar_denue.py         # descarga masiva DENUE → Bronce (ético, SHA-256)
src/inteligencia/asistente.py      # main.py asistente: JSON compactos + directorio
tablero/asistente.html             # interfaz del chat (sin dependencias)
tablero/asistente/motor.js         # reconocimiento, intenciones, flujos, estados
tablero/asistente/memoria.js       # IndexedDB, exportar, importar, borrar
tablero/asistente/documentos.js    # ficha de oferta y acuerdo (impresión / PDF)
data/publico/asistente/*.json      # datos por fruta + compradores.json
tests/test_asistente.py            # datos y directorio
tests/js/motor.test.mjs            # 150 frases + máquina de estados (node --test)
docs/chatbot/GUION_DEMO.md
```

## 9. Fase posterior (opcional): capa con IA y servidor

Cuando el equipo quiera conversación totalmente libre o que el sistema envíe mensajes por su cuenta:
- se agrega un servicio pequeño (FastAPI) que guarda la clave de API y usa Claude con las **mismas funciones** del motor como herramientas (consultar precio, crear oferta, buscar compradores, etc.);
- WhatsApp Business se integra para enviar plantillas a compradores que acepten recibirlas.

Esta fase requiere:
- hosting (~USD 10–25 al mes);
- cuenta de Anthropic (~USD 0.40 por venta completa con Opus 5.5);
- verificación de la empresa en Meta;
- aviso de privacidad, porque el servidor sí guardaría datos personales.

Nada de los 2 días se tira: la capa de IA solo reemplaza el "entendedor" de frases.

## 10. Lo que necesito del equipo para empezar

1. **Permiso para descargar el DENUE** de INEGI: archivos CSV oficiales por estado, comprimidos.
   - **Tamaño:** de pocos MB (Colima) a ~100 MB (Ciudad de México o Jalisco).
   - **Dónde:** se guardan en Bronce. Solo el directorio filtrado (unos cientos de KB) se publica.
2. Confirmar los **estados** del directorio. Propuesta: Colima, Jalisco, Michoacán, Ciudad de México y Nuevo León.
