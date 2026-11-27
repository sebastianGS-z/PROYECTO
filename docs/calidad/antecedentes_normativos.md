# Antecedentes normativos: de ISO/IEC 9126 a SQuaRE, e ISO 9001

## ISO/IEC 9126 → familia ISO/IEC 25000 (SQuaRE)

ISO/IEC 9126 (1991, revisada en 2001 en cuatro partes) definió el primer modelo de calidad de producto de software ampliamente adoptado. La familia **ISO/IEC 25000 SQuaRE** (*Systems and software Quality Requirements and Evaluation*) la sustituyó a partir de 2005: unificó en un solo marco el modelo de calidad (9126) y el proceso de evaluación (ISO/IEC 14598), y agregó un modelo específico para la **calidad de los datos** (ISO/IEC 25012), que 9126 no tenía.

| ISO/IEC 9126-1:2001 | ISO/IEC 25010:2011 | ISO/IEC 25010:2023 (vigente) | Qué cambió |
|---|---|---|---|
| Funcionalidad | Adecuación funcional | Adecuación funcional | "Seguridad" e "interoperabilidad" salen de aquí y se vuelven características o subcaracterísticas propias |
| Fiabilidad | Fiabilidad | Fiabilidad | Se agrega *disponibilidad* como subcaracterística; 2023 agrega *ausencia de fallos* |
| Usabilidad | Usabilidad | Capacidad de interacción | 2023 cambia el nombre y agrega inclusividad y autodescripción |
| Eficiencia | Eficiencia de desempeño | Eficiencia de desempeño | Se agrega *capacidad* (límites máximos) |
| Mantenibilidad | Mantenibilidad | Mantenibilidad | Se agregan *modularidad* y *reusabilidad* |
| Portabilidad | Portabilidad | Flexibilidad | 2023 la renombra e incluye *escalabilidad* |
| (dentro de Funcionalidad) | Seguridad | Seguridad | Pasa a característica propia; 2023 agrega *resistencia* |
| (dentro de Funcionalidad: interoperabilidad) | Compatibilidad | Compatibilidad | Característica propia (coexistencia e interoperabilidad) |
| — | — | Protección (*safety*) | Nueva en 2023 |
| Calidad en uso (9126-4) | ISO/IEC 25010 (calidad en uso) | ISO/IEC 25019:2023 | La calidad en uso se separa en su propia norma |
| — | ISO/IEC 25012:2008 | ISO/IEC 25012:2008 | Modelo de calidad de datos: 15 características inherentes y/o dependientes del sistema |
| Métricas (9126-2/3/4) | ISO/IEC 25022, 25023, 25024 | ídem | Medidas de calidad en uso, de producto y de datos |
| Proceso de evaluación (ISO/IEC 14598) | ISO/IEC 25040 | ISO/IEC 25040:2024 | Evaluación integrada en SQuaRE |

Divisiones de SQuaRE: 2500n gestión de la calidad · 2501n modelo de calidad · 2502n medición · 2503n requisitos de calidad · 2504n evaluación.

> En este proyecto la rúbrica pide evaluar "con ISO/IEC 25010"; la [evaluación](iso25010.md) usa las ocho características de la versión 2011 que lista la guía del proyecto (adecuación funcional, eficiencia de desempeño, compatibilidad, capacidad de interacción, fiabilidad, seguridad, mantenibilidad y portabilidad), con el nombre "capacidad de interacción" de 2023.

## ISO 9001:2015 y su enfoque a procesos

ISO 9001 no evalúa un producto de software: certifica el **sistema de gestión de la calidad** de una organización. Su versión vigente (2015, con enmienda de 2024 sobre cambio climático) se basa en siete principios (enfoque al cliente, liderazgo, compromiso de las personas, **enfoque a procesos**, mejora, decisiones basadas en evidencia y gestión de las relaciones) y en el ciclo **PHVA** (planificar, hacer, verificar, actuar) con pensamiento basado en riesgos.

Relación con el observatorio:

| Requisito ISO 9001 | Cláusula | Cómo se refleja en el OAIC |
|---|---|---|
| Contexto y partes interesadas | 4 | Entrevistas E0 con productores y empacadores (`docs/E0/entrevistas.md`) |
| Planificación: riesgos y objetivos de calidad | 6 | Objetivos OQ1–OQ3 medibles y matriz de riesgos del [plan SQA](plan_sqa.md#10-riesgos) |
| Información documentada | 7.5 | Repositorio versionado, fichas de entrega, datasheet |
| Operación: control de salidas no conformes | 8.7 | Cuarentena con motivo; nada se publica sin pasar la puerta de calidad |
| Seguimiento, medición, análisis | 9.1 | `calidad/metricas.py` en cada push; bitácora de capturas |
| Auditoría interna | 9.2 | Auditoría cruzada entre equipos |
| No conformidad y acción correctiva | 10.2 | Registro PSP de defectos y cierre de hallazgos de auditoría |

## Diferencia clave

ISO/IEC 25010 y 25012 responden **"¿qué tan bueno es el producto y sus datos?"** (medidas sobre el sistema). ISO 9001 responde **"¿la organización trabaja de forma que produce resultados consistentes?"** (medidas sobre el proceso). Por eso el Sello TDL combina ambas: métricas de producto (cobertura, disponibilidad, completitud) y evidencias de proceso (auditoría, PSP, acciones correctivas).
