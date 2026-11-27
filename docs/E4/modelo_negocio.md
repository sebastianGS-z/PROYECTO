# Modelo de negocio · OAIC

> Cifras de mercado tomadas de los datos del propio observatorio (SIAP, SNIIM). Los precios de venta y las tasas de conversión son **hipótesis a validar** con clientes; se marcan como tales.

## 1. Problema que se paga por resolver

En Colima se producen **324,350 t de limón, 211,700 t de papaya y 373,100 t de plátano al año** (SIAP, cierre 2025). El productor de limón recibió en promedio **9.80 MXN/kg**, mientras la central de Guadalajara cotizó el mismo limón de origen Colima en **26.01 MXN/kg**: le llegó el **38 %** del precio (papaya: 41 %). El precio del limón cambia en promedio **22 % de un mes a otro** y llegó a caer **55 %** en un mes. Quien decide cuándo cortar, a quién vender y a qué plaza mandar lo hace hoy con rumores o con un solo intermediario.

## 2. Propuesta de valor

| Necesidad del cliente | Qué entrega el OAIC | Evidencia |
|---|---|---|
| Saber a cuánto se venderá | Pronóstico mensual con rango de 80 % y 95 %, calificado con meses no vistos | `tablero/inteligencia.html`, API `pronosticos.json` |
| Saber si le ofrecen un precio justo | Calculadora contra precio rural SIAP y mayorista actual | `tablero/preguntas.html` |
| Elegir plaza | Diferencia pareada vs Guadalajara y **flete de equilibrio** | API `plazas.json` |
| Planear cortes y contratos | Calendario estacional (sept. +32 %, dic. −31 % en limón) | API `calendario_venta.json` |
| Confiar en la cifra | Fuente oficial, linaje SHA-256, disponibilidad y completitud medidas | `docs/calidad/sello_tdl.md` |

## 3. Clientes y cuánto valor reciben (cálculo ilustrativo)

| Segmento | Ejemplo de uso | Valor estimado (supuesto explícito) |
|---|---|---|
| Empacadora mediana de limón (Tecomán) | Mueve 2,000 t/año; usa el pronóstico y la elección de plaza para mejorar su precio promedio 0.25 MXN/kg (1 % del precio mayorista) | 2,000,000 kg × 0.25 = **500,000 MXN/año** |
| Asociación de productores | Negocia el precio de huerta con referencia pública; +0.20 MXN/kg sobre 10 % del volumen de un municipio (Armería, 7,800 t) | 7,800,000 kg × 0.20 = **1.56 millones MXN/año** repartidos entre socios |
| Comprador mayorista / cadena | Presupuesta compras con el rango de 80 % y evita comprar en meses de pico | Depende del volumen; reduce sobrecosto en compras de temporada |
| Gobierno estatal / SEDER | Observatorio público de precios para política agrícola | Convenio institucional |

Los supuestos (0.25 y 0.20 MXN/kg) equivalen a ~1 % del precio mayorista y a menos de la quinta parte de la variación mensual típica; deben validarse con un piloto.

## 4. Oferta y precios (hipótesis)

| Plan | Incluye | Precio propuesto | Por qué ese precio |
|---|---|---|---|
| **Público** | Tablero, preguntas del agricultor, reporte mensual | Gratis | Atrae productores; financiado por patrocinio o convenio |
| **Productor / asociación** | Alertas por WhatsApp o correo cuando el precio sale de su rango normal, reporte semanal por producto | 300 MXN/mes por productor o 4,000 MXN/mes por asociación | Menos de 0.1 % del valor de una sola tonelada de limón vendida por mes |
| **Empresa (empacadora / comprador)** | API de datos, plazas y flete de equilibrio por producto, reporte semanal a la medida, soporte | 6,000 – 12,000 MXN/mes | 1–3 % del valor estimado para una empacadora mediana |
| **Convenio institucional** | Operación del observatorio para una dependencia, nuevos productos y plazas | 250,000 – 400,000 MXN/año | Costo de un analista de medio tiempo más infraestructura |

## 5. Costo de operar

| Concepto | Costo actual | Fuente |
|---|---|---|
| Infraestructura (GitHub Actions, GitHub Pages, repositorio público) | **0 MXN** | Medido: ~3 min de captura diaria y ~2 min de CI por cambio, dentro del plan gratuito de repositorios públicos |
| Datos (SNIIM, SIAP, NOAA, INEGI, UN Comtrade) | **0 MXN** | Fuentes públicas |
| Dominio propio (opcional) | ~300 MXN/año | Supuesto |
| Mantenimiento técnico (ajustes si cambia el SNIIM, nuevos productos) | ~8 h/mes ≈ 2,400 MXN/mes a 300 MXN/h | Supuesto |
| Atención a clientes de pago | ~10 h/mes por cada 10 clientes empresa | Supuesto |
| Envío de alertas por WhatsApp Business | 0.5–1 MXN por mensaje | Supuesto; depende del proveedor |

**Punto de equilibrio:** con ~2,700 MXN/mes de costo fijo, **un cliente empresa** o **una asociación** cubre la operación.

## 6. Proyección del primer año (escenario conservador, hipótesis)

| Mes | Clientes empresa | Asociaciones | Ingreso mensual |
|---|---:|---:|---:|
| 1–3 (piloto gratuito) | 0 | 0 | 0 |
| 4–6 | 1 | 1 | 10,000 – 16,000 MXN |
| 7–12 | 3 | 2 | 26,000 – 44,000 MXN |

Ingreso del primer año estimado: **≈ 190,000 – 330,000 MXN**, más un posible convenio institucional.

## 7. Qué falta para vender (siguiente paso comercial)

1. **Piloto con una empacadora o asociación de Tecomán/Armería** durante 3 meses, midiendo si el precio que obtuvo mejoró frente a su promedio histórico. Una carta de intención vale además +5 puntos en E4.
2. **Alertas**: hoy el sistema calcula las señales (`senales_mercado.csv`); falta el envío por WhatsApp o correo, que requiere un proveedor y el consentimiento de cada usuario.
3. **Más productos y plazas**: la captura del catálogo nacional ya acumula historia diaria de 38 centrales; en 6–12 meses habrá comparación de plazas para más productos.
4. **Precio en huerta semanal**: SIAP es anual; un convenio con una asociación permitiría reportes semanales de precio en huerta (con consentimiento y sin datos personales).

## 8. Riesgos del negocio

| Riesgo | Mitigación |
|---|---|
| El SNIIM cambia su sitio o restringe el acceso | Captura modular, diagnóstico automático; respetar siempre robots.txt |
| El cliente espera un "precio exacto" | Comunicar siempre el rango y el error típico; no es asesoría financiera |
| Competencia de consultores con información privada | Diferenciarse por fuentes oficiales verificables y precio bajo |
| Dependencia de dos personas | Documentación de operación ([reporte técnico](reporte_tecnico.md)) y CI que detecta fallas |
