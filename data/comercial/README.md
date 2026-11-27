# Datos comerciales — Observatorio de Agro-Inteligencia Colimense

Este directorio contiene registros comerciales del proyecto. **Los datos reales
no se versionan en el repositorio** (ver `.gitignore`).

## Tablas disponibles

| Archivo | Contenido |
|---|---|
| `clientes_potenciales.csv` | Padrón de prospectos: segmento, municipio, necesidad, estatus embudo. |
| `proveedores.csv` | Productores, empacadoras y distribuidores con capacidad y cotización. |
| `cotizaciones.csv` | Cotizaciones de compra y venta con unidad, moneda, vigencia y evidencia. |
| `rutas_logisticas.csv` | Orígenes, destinos, distancias, fletes cotizados y operadores. |
| `operaciones_piloto.csv` | Resultados de envíos piloto: merma, costos, ingresos y aprendizajes. |
| `fichas_oportunidad.csv` | Fichas completas de oportunidad con los 12 campos documentados. |
| `historial_correcciones.csv` | Correcciones registradas con valor previo/nuevo, motivo, responsable y fecha UTC. |

Las seis tablas operativas se inicializan localmente con `AlmacenComercial("data/comercial").inicializar()`.
El almacenamiento valida el encabezado y cada fila al leer, valida entidades antes
de guardar y reemplaza archivos de forma atómica. Solo expone una lista permitida
de tablas y nunca guarda datos de contacto personal. Los archivos CSV reales
permanecen ignorados por Git.

Para importar un CSV exportado de DENUE como prospectos no verificados:

```bash
python main.py comercial importar-denue /ruta/al/denue.csv --estado-default Colima
python main.py comercial importar-denue /ruta/al/denue.csv --estado-default Colima --municipio Tecomán
python main.py comercial seguimiento
python main.py comercial vincular --oportunidad ID --cliente ID --proveedor ID --compra ID --venta ID --ruta ID
```

La importación conserva razón social, giro y ubicación; descarta filas sin ID,
nombre o municipio, deduplica por ID de DENUE y no persiste teléfono ni correo.
El reporte resume tareas vencidas, vigencia de cotizaciones y evidencia pendiente
por oportunidad. `vincular` valida existencia, tipo de cotización, contraparte y
producto; la ficha almacena los IDs relacionados. La decisión de piloto permanece
indeterminada mientras no existan campos estructurados para confirmar vigencia de
flete y conformidad regulatoria. El reporte no recomienda rentabilidad.

Las correcciones se agregan mediante `AlmacenComercial.registrar_correccion(...)`;
el método registra los cambios pero no modifica automáticamente la entidad. La
guía de entrevista, solicitud de cotización y cierre del piloto está en
`docs/comercial/`.

Los cálculos en `src/economia/costeo.py` exigen costos y precios por kg vendible,
merma documentada y costos adicionales desglosados. Si falta un dato, lo marcan
como pendiente en vez de asumir cero. No convierten unidades de caja/presentación;
esas conversiones necesitan peso neto y evidencia.

## Limitaciones actuales

- No hay importación de SIAP, integración de mapas, interfaz comercial ni
  gestión de usuarios/permisos. La carpeta `.privado` solo está excluida de Git;
  eso no equivale a cifrado ni control de acceso del sistema operativo.
- No hay retención automática, gestión de consentimiento/contacto ni auditoría
  de acceso. El historial no está protegido contra ediciones manuales y no usa
  bloqueo entre escritores concurrentes.
- Los modelos no implican que compradores, proveedores, cotizaciones o rutas hayan
  sido verificados. El equipo debe capturar evidencia real y vigente.

## Privacidad

- Datos de contacto personal se almacenan en `.privado/contactos.csv` con
  acceso restringido.
- Aplicar minimización: solo registrar datos necesarios para la operación.
- Registrar consentimiento y preferencia de contacto cuando aplique.
- No almacenar información personal innecesaria ni publicarla.
- Tratamiento conforme a la legislación aplicable de protección de datos.

## Retención

- Cotizaciones vencidas se conservan como historial; se marcan con `vigente=no`.
- Prospectos descartados se mantienen 12 meses y luego se eliminan.
- Datos de contacto se eliminan cuando la persona lo solicite o al cerrar la relación.
