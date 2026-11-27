# Solicitud del Sello TDL · OAIC

Fecha de la evidencia: 2026-11-27. Todas las cifras se recalculan en la CI en cada push.

| Criterio | Umbral | Valor | Evidencia | Estado |
|---|---|---|---|---|
| Disponibilidad medida de la captura | ≥ 95 % en los últimos 14 días | **100 %** (14 de 14 días, 14 – 27 nov) | [`calidad/reportes/fiabilidad.json`](../../calidad/reportes/fiabilidad.json), [fiabilidad_seguridad.md](fiabilidad_seguridad.md) | ✅ |
| Completitud de la capa Oro (ISO/IEC 25012) | ≥ 95 % | **100 %** en columnas obligatorias (95.2 % en la tabla completa) | [`calidad/reportes/iso25012.json`](../../calidad/reportes/iso25012.json), [iso25012.md](iso25012.md) | ✅ |
| Cobertura de pruebas automáticas | ≥ 60 % | **69.3 %** sobre todo el código (132 pruebas) | `pytest --cov`; la CI falla por debajo de 60 % | ✅ |
| Secretos expuestos en el repositorio | 0 | **0** | gitleaks (historial completo) en CI + escaneo local | ✅ (gitleaks se confirma en la primera ejecución de la CI en GitHub) |
| Hallazgos críticos de auditoría abiertos | 0 | **0** en la auditoría interna | [cierre_hallazgos.md](auditoria/cierre_hallazgos.md) | ⚠️ Falta incorporar los hallazgos de la auditoría cruzada externa |
| Reproducibilidad | Un tercero clona y obtiene los mismos resultados | Clon limpio: Bronce íntegro y los 5 CSV de Plata/Oro con el mismo SHA-256 | [procedimiento](#reproducibilidad) | ✅ (falta la prueba por una persona ajena al equipo) |

## Reproducibilidad

Procedimiento para un tercero (Linux o macOS, Python 3.12):

```bash
git clone https://github.com/sebastianGS-z/PROYECTO.git && cd PROYECTO
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt
python main.py validar                              # "Capa Bronce íntegra."
python main.py capas --data-dir /tmp/oaic           # regenera Plata/Oro en otra carpeta
sha256sum data/oro/panel_mensual.csv /tmp/oaic/oro/panel_mensual.csv   # deben coincidir
python -m pytest -q --cov                           # ≥ 60 %
python -m laboratorio.e1_series --corte 2026-10     # mismas cifras que docs/E1/laboratorio_series.md
python -m laboratorio.e3_multivariado               # mismas cifras que docs/E3/multivariado.md
```

El experimento E2 mide tiempos, que dependen de la máquina: un tercero obtendrá otros segundos, pero debe obtener la misma conclusión (parser dominante, tasa de error 0, lxml + tablas como óptimo).

## Pendiente antes de presentar la solicitud

1. Cargar la auditoría cruzada recibida en [`auditoria/auditoria_recibida.md`](auditoria/auditoria_recibida.md) y cerrar cualquier hallazgo crítico.
2. Confirmar en GitHub que el primer run de `validacion.yml` termina en verde (gitleaks incluido).
3. Pedir a una persona ajena al equipo que siga el procedimiento de reproducibilidad y registrar el resultado aquí.
