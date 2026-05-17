---
ext_id: F-CMP-04
slug: contratos-marco-vencimientos
track: F
dept: CMP
ord: 144
title: "Gestión de contratos marco (renovaciones, cláusulas, vencimientos)"
summary: "Indexa PDFs de contratos, extrae fechas y partes con parse_contract_pdf, alerta T-30/T-60/T-90 y detecta cláusulas riesgosas (auto-renew, exclusividad, penalidades) comparando contra la plantilla aprobada del tenant."
related_modules: [B02, C01, E01, E05]
industries_instanced: [servicios-fin, construccion]
tenants_in_examples: [cooppopular, andina]
big_corp_vendors: [Ironclad, Icertis, DocuSign CLM]
latam_tools: [excel, drive-shared, world_office]
key_concepts: [CLM, auto-renew, exclusividad, SLA-penalidades, T-30, parse-contract, delta-cláusulas]
estimated_minutes: 45
deterministic_share: 0.55
version: 1
---

## 1. Problema operativo

El gerente de operaciones de Constructora Andina tiene 35 contratos marco activos con subcontratistas y proveedores de materiales. Los contratos viven en una carpeta de Google Drive sin estructura, los vencimientos están en un Excel que alguien actualiza «cuando se acuerda». El mes pasado un contrato de arrendamiento de maquinaria se renovó automáticamente por un año completo porque nadie revisó la cláusula de auto-renovación a 60 días. Costo del descuido: $18.000 USD inmovilizados en un equipo que ya no necesitan. El jefe jurídico de Coop. Popular de Crédito tiene un problema diferente: contratos de servicios TI con cláusulas de exclusividad que bloquean cambiar de proveedor aunque el SLA no se cumpla. Nadie los revisó antes de firmar.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|--------|----------|-------------------|
| **Ironclad** | CLM completo: redacción colaborativa, workflows de aprobación, repositorio con búsqueda semántica, alertas configurables, análisis de riesgo con IA | 50–200 USD/usuario/mes; setup 20–80k USD |
| **Icertis** | CLM enterprise, integración SAP/Oracle, extracción de obligaciones, gestión de KPIs contractuales, compliance | 100–400k USD/año para empresa mediana |
| **DocuSign CLM** | Firma + gestión del ciclo de vida del contrato, repositorio centralizado, alertas de renovación, plantillas | 40–150 USD/usuario/mes |

La diferencia big corp vs. PYME no es la funcionalidad de alerta — es el **repositorio estructurado**. Ironclad sabe que un contrato tiene cláusulas porque el abogado las etiquetó al ingresarlo. PYME tiene PDFs sin etiquetar en Drive.

## 3. PYME LATAM realista

Andina guarda contratos en Drive con nombres como «contrato_ferrreteria_norte_v3_FIRMADO.pdf». Coop. Popular tiene contratos en correos de hace 3 años. No hay catálogo de vencimientos. El equipo jurídico es un abogado externo que factura por hora — revisar 35 contratos para hacer el inventario cuesta 5–8 horas de honorarios. El agente hace el inventario una vez, y desde ahí el mantenimiento es automático.

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Contratos en Drive / SharePoint | PDF (firmado), Word (borrador) | Ingesta inicial única + nuevos | 20–200 contratos/empresa |
| Plantilla maestra del tenant | Word o PDF del área jurídica | Estática (actualización anual) | 1–5 plantillas por tipo |
| Registro de vencimientos actual | Excel manual | Reactivo | mismas líneas que contratos |

**Ejemplo de ficha de contrato extraída:**

| campo | valor |
|-------|-------|
| tipo | Contrato de suministro de materiales |
| partes | Constructora Andina S.A.S. (cliente) / Ferretería El Norte Ltda. (proveedor) |
| fecha_inicio | 2024-03-01 |
| fecha_vencimiento | 2026-03-01 |
| auto_renew | Sí — 60 días de anticipación para no renovar |
| exclusividad | No |
| penalidad_incumplimiento | 5% del valor del pedido afectado |
| valor_mensual_estimado | COP 28.000.000 |

## 5. Tramos determinísticos

1. **Extracción de texto de PDF**: `parse_contract_pdf` con `pdfplumber` para PDF digital; fallback a OCR (Google Document AI) para escaneados. Retorna texto completo del contrato.
2. **Extracción de campos estructurados por regex + NER**: fechas en formatos `DD/MM/YYYY`, `D de Mes de AAAA`, `YYYY-MM-DD`; nombres de partes (NER determinístico sobre entidades nombradas); valor del contrato con moneda.
3. **Cálculo de alertas T-90/T-60/T-30**: dado `fecha_vencimiento`, calcular `dias_restantes = fecha_vencimiento - today`. Insertar en tabla `contract_alerts` con `alert_date` programada. Esto es un cálculo aritmético.
4. **Detección de auto-renew por keyword**: buscar en el texto frases como «se renovará automáticamente», «auto-renewal», «renovación automática», «se prorrogará». Si hay match, extraer el número de días de anticipación requerido con regex `(\d+) días? antes`.
5. **Comparación de estructura contra plantilla**: diff de secciones entre el contrato y la plantilla del tenant. Identificar secciones presentes en plantilla pero ausentes en contrato (y viceversa). Este paso es estructural, no semántico.

## 6. Tramos agénticos

1. **Identificación de cláusulas riesgosas**: el modelo lee cada sección del contrato y clasifica si contiene: auto-renew con condiciones desfavorables, exclusividad que limita al cliente, SLA con penalidades financieras, límites de responsabilidad anormalmente bajos, cláusulas de escalada de precio no acotadas. Justificación: la misma cláusula puede ser riesgosa o no según el contexto del negocio del tenant; no es una regla cerrada.
2. **Comparación semántica contra plantilla aprobada**: el modelo recibe la cláusula del contrato y la cláusula equivalente de la plantilla, y determina si el delta es: a) diferencia de estilo sin impacto, b) diferencia operacional menor, c) desviación significativa que requiere revisión legal. Justificación: «el proveedor limitará su responsabilidad» puede significar cosas muy distintas dependiendo del tipo de servicio y del sector.
3. **Resumen ejecutivo del contrato**: el modelo produce un resumen de 3–5 puntos clave en lenguaje de negocio (no jurídico), con los riesgos identificados y las fechas críticas. Justificación: salida para el gerente, no para el abogado.

> [!nota]
> El agente **no da consejo jurídico**. La sección de riesgos de cada contrato termina siempre con: «Estos hallazgos son informativos. Confirmar con el área jurídica antes de actuar sobre cláusulas marcadas como Riesgo Alto.»

## 7. Blueprint del workflow

```
START
  ↓
[ingest_contracts] → descarga todos los PDFs del bucket/Drive del tenant (determinístico)
  ↓
[parse_contracts] → extracción de texto + campos estructurados (determinístico, tool: parse_contract_pdf)
  ↓
[extract_dates_parties] → fechas, partes, valor con regex + NER (determinístico)
  ↓
[schedule_alerts] → calcular T-30/T-60/T-90 e insertar en alerts table (determinístico, tool: sql_query)
  ↓
[detect_auto_renew] → keyword search + extracción de plazo de notificación (determinístico)
  ↓
[identify_risky_clauses] → clasificar cláusulas riesgosas (agéntico)
  ↓
[compare_to_template] → delta semántico contra plantilla aprobada del tenant (agéntico)
  ↓
[draft_summary] → resumen ejecutivo en lenguaje de negocio (agéntico)
  ↓
[human_review] → área jurídica o gerencia revisa los contratos marcados como Riesgo Alto (siempre)
  ↓
[write_report + schedule_email_alerts] → repositorio + alertas programadas (determinístico, tool: write_report, send_email)
  ↓
END (mantenimiento: trigger diario para enviar alertas de vencimiento)
```

**Activities Temporal:**

- `ingest_new_contracts(tenant)` — detecta nuevos archivos en Drive/bucket y los procesa. Retry policy con backoff.
- `send_expiry_alerts(tenant, date)` — corre diariamente; envía alertas para contratos con `alert_date == today`. Idempotente: `idempotency_key = "alert:{tenant}:{contract_id}:{days}"`.

**Tools necesarias:**

- `parse_contract_pdf` — extracción de texto y campos
- `sql_query` — repositorio de contratos y alertas del tenant
- `write_report` — ficha de contrato + reporte de riesgos
- `send_email` — alertas de vencimiento (programadas)

## 8. Salida y entrega

1. **Repositorio de contratos** con tabla: nombre, partes, fecha inicio, fecha vencimiento, días restantes, auto-renew (sí/no + plazo), alertas programadas, nivel de riesgo.
2. **Reporte de riesgos** por contrato: cláusulas identificadas como riesgosas con cita textual y nivel (Alto/Medio/Bajo).
3. **Alertas por email** automáticas en T-90, T-60 y T-30 con el resumen del contrato y la acción recomendada.
4. **Resumen ejecutivo** de 1 página por contrato para la reunión de renovación.

Canal: panel en la app + emails programados vía Temporal.

**Mockup de repositorio:**

| Contrato | Proveedor | Vence | Días | Auto-renew | Riesgo | Alerta |
|----------|-----------|-------|------|------------|--------|--------|
| Suministro materiales | Ferretería El Norte | 2026-03-01 | 44 | ⚠ Sí, 60 días | Medio | T-60 enviada hoy |
| Arrendamiento grúa | Equipos Heavy | 2026-02-10 | 25 | ⚠ Sí, 30 días | Alto | 🔴 T-30 — acción urgente |
| Servicios contables | Revisoría ABC | 2026-07-15 | 180 | No | Bajo | T-90 en 90 días |

## 9. Cómo se vende

**Gancho**: «¿Cuánto te costó el último contrato que se renovó solo porque nadie miró la fecha? El agente indexa todos tus contratos hoy y nunca más se te pasa un vencimiento.»

**Diferencial**: no es solo un recordatorio de fechas — es la detección de cláusulas riesgosas que nadie leyó antes de firmar.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Básico | Hasta 50 contratos, indexación + alertas T-30/T-60/T-90, repositorio | 150–300 USD/mes |
| Estándar | Hasta 150 contratos, análisis de cláusulas riesgosas, comparación contra plantilla | 300–600 USD/mes |
| Avanzado | Ilimitado, integración Drive/SharePoint API, golden set jurídico del tenant, alerta Slack | 600–1200 USD/mes + setup 4–8k USD |

## 10. Riesgos

**1. Fecha de vencimiento mal extraída.**
*Síntoma*: el contrato tiene «vigencia de 2 años desde la firma» — el agente no calcula la fecha absoluta correctamente porque no encontró la fecha de firma.
*Mitigación*: si no puede calcularse la fecha de vencimiento como fecha absoluta, marcar como `fecha_vencimiento: PENDIENTE` y alertar al usuario para ingreso manual. No asumir.

**2. Cláusula riesgosa con falso negativo.**
*Síntoma*: el agente clasifica como «Riesgo Bajo» una cláusula de penalidad porque está redactada en términos inusuales.
*Mitigación*: golden set de 20–30 cláusulas clasificadas por el abogado del cliente. Re-evaluar el desempeño del modelo trimestralmente. El disclaimer jurídico es obligatorio en toda salida.

**3. Contrato confidencial procesado por el modelo.**
*Síntoma*: el texto completo de un contrato con información sensible de terceros se envía al API de Anthropic.
*Mitigación*: el tenant debe declarar explícitamente qué contratos pueden procesarse con LLM externo. Alternativa: despliegue con Claude en Bedrock (AWS) bajo BAA si el cliente lo requiere.

**4. Auto-renew detectado pero plazo de notificación mal calculado.**
*Síntoma*: el sistema detecta auto-renew a 60 días pero la fecha T-60 ya pasó; la alerta llega tarde.
*Mitigación*: al indexar un contrato nuevo, calcular inmediatamente si algún T ya pasó. Si T-60 o T-30 ya pasaron → alerta inmediata, no esperar al trigger diario.

## 11. Variantes por industria

### Instancia 1 — Servicios financieros (`cooppopular`)

**Datos típicos**: contratos con proveedores TI (core bancario, software de crédito), contratos de arrendamiento de locales, contratos laborales de personal directivo. Lenguaje legal más técnico. Regulación de la Superfinanciera (Colombia) sobre contratos con proveedores de servicios críticos.

**Delta determinístico**: para proveedores de servicios TI clasificados como «críticos» por la SFC, el sistema extrae automáticamente si el contrato incluye SLA documentado, plan de continuidad de negocio y cláusula de auditoría — campos exigidos por Circular Externa 007/2018. Regla cerrada: presencia/ausencia de cada cláusula.

**Delta agéntico**: evaluar si el SLA declarado en el contrato TI («disponibilidad 99%») es coherente con los SLA reales observados en los últimos 6 meses (consultando datos de monitoreo del tenant). El modelo une información del contrato con datos operativos.

**Regulación**: SFC exige comunicar cambios de proveedor crítico con 30 días de anticipación. El sistema monitorea contratos de proveedores críticos con alerta T-60 adicional para dar margen al trámite regulatorio.

**Precio orientativo**: 400–900 USD/mes; setup 6–10k USD por complejidad del catálogo jurídico.

### Instancia 2 — Construcción (`andina`)

**Datos típicos**: contratos de subcontratación (obra civil, eléctrico, hidráulico), arrendamiento de maquinaria, suministro de materiales. Alta heterogeneidad: algunos contratos son de 1 página, otros de 40 páginas con annexos técnicos.

**Delta determinístico**: los contratos de obra incluyen un «acta de inicio» como fecha real de comienzo (distinta de la fecha del contrato). Extraer `fecha_acta_inicio` con regex sobre «Acta No.» o «fecha de inicio de obra».

**Delta agéntico**: detectar si el alcance del contrato de subcontratación es compatible con el alcance del proyecto madre (ej: el subcontratista de eléctrico tiene exclusividad para «instalaciones de baja tensión» pero el contrato marco del cliente lo restringe a «instalaciones residenciales»). Requiere razonamiento sobre alcances superpuestos.

**Regulación**: contratos de obra en Colombia deben incluir cláusulas de responsabilidad por defectos ocultos (mínimo 10 años post-entrega, Ley 1564/2012). El sistema verifica presencia de esta cláusula.

**Precio orientativo**: 200–500 USD/mes; setup 3–5k USD.

## 12. Módulos técnicos relacionados

- **B02** (4 capas FastAPI): `POST /contracts/ingest` para subir nuevos contratos; `GET /contracts/{id}/risk-report` para el reporte de cláusulas. El servicio orquesta parse + análisis + persistencia.
- **C01** (SQLAlchemy async): tabla `contracts` con `tenant_id`, `expiry_date`, `auto_renew_days`, `risk_level`; tabla `contract_alerts` con `alert_date` indexada para el trigger diario.
- **E01** (Anthropic SDK): la comparación semántica de cláusulas contra la plantilla es el ejemplo canónico de prompt con dos documentos en contexto y output estructurado (`delta_type: Literal[...]`).
- **E05** (Temporal): el workflow `ContractAlertWorkflow` es el ejemplo de schedule durable: corre diariamente, es idempotente, resiste reinicios del servidor.

## Determinístico vs agéntico

| Tramo | Tipo | Por qué |
|-------|------|---------|
| Extracción de fechas con regex y NER | determinístico | Patrones de fecha bien definidos; NER sobre entidades nombradas estándar. |
| Cálculo de T-30/T-60/T-90 | determinístico | Aritmética de fechas. |
| Detección de auto-renew por keyword | determinístico | Frases explícitas en el texto; extracción del plazo con regex. |
| Identificación de cláusulas riesgosas | agéntico | El riesgo depende del contexto del negocio; misma cláusula puede ser OK o crítica. |
| Comparación semántica contra plantilla | agéntico | Diferencias de redacción pueden o no ser equivalentes funcionalmente; requiere interpretación. |
| Resumen ejecutivo en lenguaje de negocio | agéntico | Traducción de lenguaje jurídico a lenguaje de gestión; salida para humano. |

## 13. Errores típicos

**1. Contrato con fecha expresada como duración («12 meses desde la firma»).**
*Síntoma*: el agente no calcula la fecha de vencimiento y la alerta T-30 no se programa.
*Causa*: el extractor solo busca fechas absolutas; no maneja duraciones relativas.
*Arreglo*: si se detecta el patrón `N meses/años desde...`, buscar la fecha de firma en la misma página y calcular la fecha absoluta. Si la fecha de firma tampoco está disponible, marcar como `PENDIENTE` y pedir al usuario.

**2. Alerta enviada por un contrato ya renovado manualmente.**
*Síntoma*: el equipo ya renovó el contrato hace dos semanas pero el sistema sigue enviando alertas de T-30.
*Causa*: la fecha de vencimiento no se actualizó en el repositorio.
*Arreglo*: el botón «Marcar como renovado» en la UI actualiza `expiry_date` y cancela las alertas pendientes del contrato anterior.

**3. Cláusula riesgosa marcada como «Alto» pero es estándar del sector.**
*Síntoma*: todos los contratos de arrendamiento de maquinaria del sector construcción incluyen la misma cláusula de exclusividad y el sistema los marca todos como riesgo alto, creando fatiga de alertas.
*Mitigación*: el tenant puede marcar una cláusula como «aceptada para este tipo de contrato» y agregarla a su golden set de «cláusulas permitidas». El modelo no la volverá a marcar.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame cómo funciona la comparación semántica de cláusulas con un ejemplo concreto de una cláusula de penalidad.»
2. **Aplícalo a mi caso**: «Mis contratos están en Google Drive con nombres sin estructura. ¿Cómo diseñaría el proceso de ingesta inicial?»
3. **Por qué falló**: «El agente calculó mal la fecha de vencimiento de un contrato que decía "12 meses desde el acta de inicio". ¿Qué parte del extractor falló?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de indexación de contratos desde PDFs heterogéneos hasta un repositorio estructurado.
- Implementar el sistema de alertas T-30/T-60/T-90 como workflow Temporal durable e idempotente.
- Separar la extracción de campos estructurados (determinístico) del análisis de riesgo de cláusulas (agéntico).
- Configurar el golden set jurídico del tenant para reducir falsos positivos en la clasificación de riesgo.
- Cotizar y dimensionar el servicio para una PYME de construcción o servicios financieros regulados.

## 16. Módulos previos recomendados

| Módulo | Por qué te prepara para implementar esta ficha |
|--------|------------------------------------------------|
| A05   | El paquete `contract_parser` que agrupa `parse_contract_pdf`, el modelo `ContractRecord` y el extractor de cláusulas sigue el patrón de empaquetado con `__init__.py` y dependencias explícitas que A05 establece. |
| B02   | Los endpoints `POST /contracts/ingest` y `GET /contracts/{id}/risk-report` y el servicio que orquesta parse + análisis + persistencia se implementan con la arquitectura de 4 capas de B02. |
| C01   | Las tablas `contracts` y `contract_alerts` con `tenant_id` y el índice sobre `alert_date` para el trigger diario son el patrón de SQLAlchemy async con multitenancy que C01 enseña. |
| E01   | La comparación semántica de cláusulas contra la plantilla con `delta_type: Literal[...]` como output estructurado es el ejemplo canónico de prompt con dos documentos en contexto del SDK de Anthropic. |
| E05   | `ContractAlertWorkflow` que corre diariamente y envía alertas de vencimiento con `idempotency_key = "alert:{tenant}:{contract_id}:{days}"` es el caso de schedule durable que E05 introduce. |
