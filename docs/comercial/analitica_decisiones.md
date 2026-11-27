# OAIC · Comparación de destinos, costos y contexto internacional

## Qué puede responder hoy

El tablero comprador combina los precios frecuentes mayoristas mensuales de SNIIM con el cierre agrícola municipal anual de SIAP y estadísticas aduanales de UN Comtrade. Mantiene separadas sus unidades y escalas temporales.

| Pregunta | Evidencia usada | Interpretación permitida |
|---|---|---|
| ¿En qué plazas se observó mayor precio bruto? | SNIIM, misma variante, origen reportado y periodos mensuales pareados | Orden descriptivo de precio frecuente mayorista; muestra el periodo y número de meses comparados. |
| ¿En cuál destino queda más margen? | Precio bruto pareado + costo de compra, manejo, merma y flete por destino que introduce el usuario | Margen condicional del escenario. El sistema no confirma ni crea costos. |
| ¿Cuánto volumen cubre los costos fijos? | Margen de contribución estimado y costo fijo del lote | Punto de equilibrio en kg comprados. No es recomendación de compra: se debe verificar pedido/demanda, oferta, calidad y capital disponible. |
| ¿De dónde proviene la producción agrícola? | SIAP, municipio × cultivo × año; polígonos municipales INEGI | Mapa choropleth con volumen reportado y unidad oficial. No identifica huertas, productores ni existencia presente. |
| ¿Qué países participan en el comercio de esa fruta? | UN Comtrade, exportaciones a Mundo e importaciones que reportan a México como socio, anual 2024 | Detección de flujos y referencia aduanal para investigar. No acredita un comprador, precio final, acceso a mercado o rentabilidad. |

## Cómo se calcula el simulador

Para cada destino se usa el promedio de precios SNIIM en meses coincidentes con la plaza seleccionada. En la selección de origen, producto, variedad y periodo:

```text
kg vendibles = kg comprados × (1 − porcentaje de merma)
contribución por kg comprado = precio de destino × (1 − merma) − compra − empaque/manejo − flete
resultado del lote = contribución por kg comprado × kg comprados − costos fijos del lote
punto de equilibrio (kg comprados) = costos fijos del lote ÷ contribución por kg comprado
```

Si la contribución es cero o negativa, no existe punto de equilibrio positivo; el tablero lo marca como “No vender con estos costos”. Cuando falta un costo de compra o el flete para un destino, no calcula una utilidad. Los importes se expresan en MXN/kg; no mezclar una presentación por pieza o caja sin peso neto verificable. Los campos de flete se capturan por destino para que el costo logístico pueda alterar el orden de rentabilidad.

El cálculo no descuenta impuestos y aranceles, comisión, refrigeración, rechazo por calidad, costo financiero, cambio de moneda o demora, salvo que el usuario los agregue en manejo o costos fijos. Captura dichos gastos con evidencia y documenta la categoría usada. El valor de venta SNIIM es un precio frecuente mayorista referencial, no una oferta de compra vinculante. Para una operación comercial debe sustituirse por cotización directa y vigente del comprador.

## Cobertura territorial y mundial

- **SIAP:** cierre municipal anual 2025, Colima. El original descargado (5.5 MB) se conserva en `data/bronce/siap/` con hash SHA-256; el pipeline crea una tabla de 230 agregados municipales/cultivo y el mapa GeoJSON. La superficie y producción se agregan sin identificar unidades productivas individuales. En cada cultivo se conserva la unidad oficial del archivo.
- **INEGI:** límites municipales del Marco Geoestadístico guardados en Bronce; las geometrías solo se enlazan con municipio y no con mercados SNIIM ni coordenadas de parcelas.
- **UN Comtrade:** año 2024 para aguacate (HS 080440), grupo guayaba/mango/mangostán (HS 080450) y grupo limones/limas (HS 080550). Hay 479 filas de exportaciones a Mundo e importaciones reportadas cuyo socio comercial es México en la captura actual. Los países que reportan no tienen cobertura idéntica; revisa el archivo de consultas y el posible límite de 500 registros.
- **Huecos:** el extracto mundial inicial no cubre todavía coco, papaya, plátano, tamarindo o sandía. Para esos productos el tablero declara que no hay registro mundial capturado. Los importadores globales pueden señalar zonas a investigar; no equivalen a “los mejores países para vender”. Las estadísticas aduanales agregan categorías HS y no sustituyen precios de mercado por variedad, calidad, empaque o temporada.
- **SNIIM internacional:** la fuente ofrece cotizaciones en algunos mercados de Estados Unidos, Canadá y Europa, pero la actual captura OAIC todavía no extrae esas series. El tablero no las presenta como disponibles. La cobertura y las reglas de consulta deben integrarse por separado antes de afirmar una comparación mundial de precios mayoristas.

## Reproducir y actualizar

```bash
python main.py siap
python main.py comercio-intl
python main.py comercio-intl --solo-procesar
```

La primera orden reprocesa el último CSV SIAP existente en Bronce y el Marco Geoestadístico INEGI. La segunda consulta la API pública de UN Comtrade, guarda respuestas originales con sidecar y genera la exportación pública. Si hay limitación HTTP 429, no fuerza la cuota; revisa `data/publico/reporte_comercio_mundial.json` y reintenta después. La tercera regenera archivos publicados desde las respuestas que sí se guardaron. No se emiten precios/destinos cuando falta evidencia.

## Fuentes y avisos

- SIAP, [Datos abiertos de estadística de producción agrícola](https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php), nivel municipal, cierre 2025.
- UN Statistics Division, [UN Comtrade API docs](https://comtrade.un.org/en/api-docs) y [códigos M49](https://unstats.un.org/unsd/methodology/m49/overview).
- Secretaría de Economía, SNIIM, [Preguntas frecuentes](https://www.economia-sniim.gob.mx/nuevo/Preguntas%20Frecuentes.htm): sus precios son referencias públicas; la interpretación y el uso son responsabilidad de quien los usa.
- Revisa también [ética y legalidad de datos](../etica-datos.md).
