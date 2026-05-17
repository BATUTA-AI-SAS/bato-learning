---
ext_id: F-VTA-04
slug: churn-comercial
track: F
dept: VTA
ord: 4
title: "Análisis de churn comercial y campaña de retención"
summary: "Agente que detecta cuentas en riesgo de no renovar, clasifica el motivo probable y propone una oferta de retención diferenciada — sin dar descuento a quien se va por razón distinta al precio."
related_modules: [A06, B02, C01, D04, E01]
industries_instanced: [serv-prof, energia]
tenants_in_examples: [consultorabc, solenergy]
big_corp_vendors: [Gainsight, ChurnZero, Salesforce]
latam_tools: [hubspot, planilla-csv]
key_concepts: [NRR, GRR, cohort-analysis, leading-indicators, churn-motivo, retención-diferenciada]
estimated_minutes: 45
deterministic_share: 0.4
version: 1
---

## 1. Problema operativo

El socio director de Consultora ABC acaba de perder tres clientes en el mismo trimestre. Después de revisar los casos, descubrió que dos se fueron por falta de atención (nadie les hizo seguimiento después del entregable), y uno porque el contrato quedó desactualizado frente a sus necesidades nuevas. Los tres dieron señales con semanas de antelación que nadie vio. La tasa de churn del 15% anual destruye el crecimiento: cada nuevo cliente adquirido a costo de marketing compensa apenas al que se fue.

SolEnergy Distribuidora tiene el mismo problema a mayor escala: contratos de servicio con 80+ clientes industriales, renovaciones anuales. Un cliente que no renueva un contrato de 200 k USD es un hueco que tarda 6 meses en llenarse.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|---|---|---|
| **Gainsight** | Customer Success Management: health scoring, playbooks de retención, forecasting de renovaciones. Según IDC, 73–81% de precisión en predicción de churn con 12+ meses de datos. | Precios no públicos; estimado 20–30 k USD/año para equipos medianos |
| **ChurnZero** | Mid-market CS platform: ChurnScore en tiempo real, playbooks automatizados, journeys de cliente. Más rápido de implementar que Gainsight. | Precios no públicos; estimado 12–18 k USD/año |
| **Salesforce Success Cloud** | Integrado con el CRM: health scoring sobre datos Salesforce + Einstein AI para predicción de riesgo de renovación. | Incluido en algunos paquetes Enterprise; add-on desde 75 USD/user/mes |

Estas plataformas requieren datos limpios de uso del producto, historial de tickets, y al menos 1 año de historial de renovaciones/churns para calibrar. PYME LATAM normalmente no tiene eso en un sistema.

## 3. PYME LATAM realista

Consultora ABC no tiene un sistema de Customer Success. Los datos de retención viven en: el CRM (HubSpot/Pipedrive), con los deals de renovación como nuevos deals o como campos de «renewal date»; los tickets de soporte o consultas (a veces en un email inbox, a veces en un Notion); y la memoria del consultor asignado a la cuenta. No hay health score calculado. No hay alertas de uso. La señal más frecuente de que un cliente se va es que no respondió la propuesta de renovación.

SolEnergy tiene más datos — los contratos están en un ERP (World Office o un Excel estructurado) y hay historial de facturas pagadas — pero sin análisis de leading indicators.

## 4. Datos típicos

| Campo | Fuente | Frecuencia | Ejemplo de fila |
|---|---|---|---|
| `account_id` | CRM | por cuenta | `"ACC-2031"` |
| `account_name` | CRM | por cuenta | `"SolEnergy Distribuidora"` |
| `contract_start_date` | CRM / ERP | por contrato | `"2025-06-01"` |
| `contract_end_date` | CRM / ERP | por contrato | `"2026-05-31"` |
| `days_to_renewal` | calculado | diario | `15` |
| `mrr_usd` | CRM / ERP | mensual | `18500` |
| `tickets_last_90d` | CRM / soporte | batch semanal | `7` |
| `tickets_escalated_last_90d` | CRM / soporte | batch semanal | `2` |
| `last_meeting_date` | CRM | por actividad | `"2026-03-10"` |
| `nps_score` | encuesta (si existe) | trimestral | `6` (detractor) |
| `invoice_payment_delay_avg_days` | ERP | mensual | `22` (pago tardío = señal) |
| `feature_requests_unresolved` | soporte | por ticket | `3` |
| `notes_account_history` | CRM | batch diario | Texto libre, historial completo |
| `cohort_id` | calculado | por cuenta | `"2025-Q2"` — trimestre de adquisición |

**NRR (Net Revenue Retention)**: `(MRR inicio del período + expansiones - downgrades - churns) / MRR inicio`. Mide si la base de clientes crece o encoge ignorando nuevas adquisiciones.

**GRR (Gross Revenue Retention)**: NRR sin expansiones. Mide exclusivamente la retención. GRR < NRR siempre. Una empresa puede tener NRR > 100% (expansión) con GRR de 80% (pierde clientes pero los que quedan crecen).

## 5. Tramos determinísticos

1. **Cálculo de GRR y NRR por cohorte trimestral**: agrupar cuentas por `cohort_id`, sumar MRR en el momento de adquisición vs MRR actual. La tabla de cohortes es la métrica más importante de la sección — muestra si el churn es sistémico o específico de una cohorte.

2. **Identificación de cuentas próximas a renovación**: `days_to_renewal <= 90` → entran al análisis. Ordenadas por `mrr_usd DESC` (el mayor impacto financiero primero).

3. **Señales de riesgo estructuradas** (leading indicators): reglas fijas que asignan puntos de riesgo:
   - `tickets_escalated_last_90d >= 2` → +20 pts de riesgo
   - `nps_score <= 6` → +20 pts
   - `last_meeting_date > 60 días` → +15 pts
   - `invoice_payment_delay_avg_days > 15` → +10 pts
   - `feature_requests_unresolved >= 2` → +10 pts
   Total: `health_score = 100 - risk_points`. Cuenta con health_score < 60 → `at_churn_risk: true`.

4. **Segmentación de cuentas at_risk**: por MRR, por industria, por motivo de tickets (si hay categorización). Permite ver si el churn está concentrado en un segmento específico.

5. **Cálculo del «churn proyectado»**: si todas las cuentas at_risk efectivamente churnan, cuánto MRR se pierde. `projected_churn_mrr = sum(mrr for accounts with health_score < 60)`. Este número es el que ve el CFO.

## 6. Tramos agénticos

1. **Clasificación del motivo probable de churn por cuenta.**
   *Por qué no es regla*: hay múltiples causas con retenciones completamente distintas. «Cliente insatisfecho con el servicio» → acción: llamada ejecutiva, plan de mejora. «Cliente que creció y necesita más capacidad» → acción: proponer upgrade, no descuento. «Cliente que se va por precio» → acción: descuento o propuesta alternativa. «Cliente que se va porque el decisor cambió y el nuevo no tiene relación con nosotros» → acción: construcción de relación, no precio. Una regla basada en `tickets_count` no distingue estos casos. El modelo lee el historial de la cuenta y propone la hipótesis más probable.

2. **Propuesta de oferta de retención diferenciada.**
   *Por qué no es regla*: dar descuento a un cliente que se va por feature gap (no por precio) es desperdiciar el descuento y no resolver el problema real. El modelo propone una oferta apropiada al motivo clasificado: si el motivo es «falta de atención», propone un plan de QBR trimestral, no un descuento. Si es «precio», propone un renegociado del contrato. Si es «cambio de decisor», propone una reunión ejecutiva de presentación.

3. **Redacción del mensaje de retención por cuenta.**
   *Por qué no es regla*: el tono y el contenido del mensaje dependen de la relación histórica con el cliente, el perfil del contacto actual, y el motivo de riesgo. El modelo genera un borrador que el CSM ajusta antes de enviar.

> [!cuidado]
> El agente **nunca envía el mensaje de retención automáticamente**. El borrador siempre pasa por revisión del account manager o socio antes de salir. Una comunicación mal calibrada puede acelerar el churn en lugar de prevenirlo.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_accounts] → pull de cuentas + contratos + historial (determinístico)
  ↓
[compute_cohort_metrics] → GRR/NRR por cohorte trimestral (determinístico)
  ↓
[compute_health_scores] → risk_points por leading indicators (determinístico)
  ↓
[filter_at_churn_risk] → cuentas con health_score < 60 y days_to_renewal <= 90 (determinístico)
  ↓
[read_account_history] → notas + tickets + emails por cuenta at_risk (determinístico: I/O)
  ↓
[classify_churn_reason] → LLM clasifica motivo probable por cuenta (agéntico)
  ↓
[propose_retention_offer] → LLM propone oferta diferenciada por motivo (agéntico)
  ↓
[draft_retention_message] → LLM redacta borrador de mensaje (agéntico)
  ↓
[human_review?] → interrupt_before siempre — el CSM revisa antes de enviar
  ↓
[write_report] → reporte de churn risk + ofertas propuestas (determinístico)
  ↓
END
```

### Activities Temporal (job semanal)

- `pull_account_health(tenant, date)` — snapshot de health scores.
- `run_churn_analysis_agent(tenant, snapshot_id)` — ejecuta el grafo.
- `deliver_churn_report(tenant, week_date, payload)` — reporte al CSM + dirección.
  `idempotency_key = "churn-analysis:{tenant}:{week_date}"`

### Tools necesarias

- `sql_query` — cuentas + contratos + tickets desde DB del tenant.
- `fetch_excel` — si el CRM exporta a Sheets o si los contratos están en Excel.
- `erp_fetch_transactions` — historial de facturación y pagos (Siigo/World Office).
- `write_report` — PDF con cohortes + cuentas at_risk + propuestas de retención.
- `send_email` — borrador al CSM para revisión (sin envío automático al cliente).

## 8. Salida y entrega

### Reporte semanal (PDF + email al CSM)

```
CHURN RISK REPORT — Consultora ABC — Semana 20 / 2026

MÉTRICAS DE RETENCIÓN Q1 2026:
GRR: 82% (perdemos el 18% del MRR base cada año)
NRR: 94% (expansiones compensan parcialmente)
Churn proyectado si no se actúa: USD 44 500/mes MRR en riesgo

CUENTAS EN RIESGO ALTO (actúa en los próximos 7 días):

· Grupo Andina Servicios · MRR USD 8 200 · Renovación en 18 días · Health: 42/100
  Motivo probable: FALTA DE ATENCIÓN — sin reunión en 75 días, 2 escalaciones de tickets sin respuesta
  Oferta sugerida: NO descuento. Proponer QBR ejecutivo esta semana + asignar consultor senior.
  Borrador de mensaje: "Hola Roberto, notamos que tienen algunos temas pendientes de nuestro lado.
  Queremos agendarles una sesión de revisión con nuestro socio esta semana para asegurarnos
  de que el servicio esté al nivel que esperan..."
  ⚠ Revisar antes de enviar. Requiere aprobación del socio.

· SolEnergy Norte · MRR USD 18 500 · Renovación en 22 días · Health: 55/100
  Motivo probable: FEATURE GAP — 3 solicitudes de funcionalidad sin respuesta + NPS 5
  Oferta sugerida: NO descuento. Comprometer roadmap de entrega + call ejecutiva.
  Borrador de mensaje: [ver adjunto]

CUENTAS EN RIESGO MEDIO (monitorea en 30 días):
[lista de 4 cuentas con health 60-74]
```

**Canal**: PDF + email semanal al CSM + director comercial. Borrador de mensajes adjunto para cada cuenta crítica.

## 9. Cómo se vende

**Gancho**: «Estás perdiendo clientes que avisaron con semanas de anticipación. Este agente detecta la señal, clasifica el motivo, y te dice exactamente qué ofrecer — sin dar descuento donde no sirve.»

**Propuesta de valor**: pasar de reaccionar al churn (el cliente no renovó) a prevenirlo (el cliente dio señales hace 6 semanas). Con clasificación de motivo para no desperdiciar recursos de retención.

| Tier | Qué incluye | Precio orientativo |
|---|---|---|
| Básico | Health score determinístico + lista de cuentas at_risk | 150–250 USD/mes |
| Estándar | Clasificación de motivo + propuesta de retención + cohortes GRR/NRR | 400–700 USD/mes |
| Premium | Todo + borrador de mensaje personalizado + integración ERP para datos de pago | 700–1 400 USD/mes + setup 3–7 k USD |

Setup: 3–5 semanas. Incluye: mapeo de fuentes de datos (CRM + ERP + soporte), definición de umbrales de health score con el cliente, carga de historial de renovaciones (mínimo 2 años), golden set de 10 cuentas para validar clasificación de motivo.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Clasificación errónea del motivo**: el modelo diagnostica «precio» cuando el motivo real es «cambio de decisor». | El borrador de mensaje siempre va con la evidencia que usó el modelo (fragmentos de notas). El CSM puede ver si la hipótesis es sólida. |
| **Acción de retención que acelera el churn**: un mensaje mal redactado o una oferta inapropiada puede irritar al cliente. | El mensaje nunca sale sin revisión humana. Nunca. |
| **Datos insuficientes de uso del producto**: muchas PYMEs no tienen métricas de adopción del servicio. | El agente declara explícitamente qué leading indicators tiene disponibles. Si falta NPS o datos de uso, el health score usa solo los campos disponibles y lo indica. |
| **Sesgo hacia descuentos**: si el tenant configura que «todos los churns son por precio», el agente siempre propondrá descuento. | El tenant define las categorías de motivo en el setup. Si la categorización es incorrecta, el golden set lo detecta. |
| **PII en historial de cuentas**: datos de facturación, nombres de decisores, contenido de tickets. | Procesamiento solo dentro del entorno del tenant. Historial de notas no se loguea externamente. |

> [!cuidado]
> **Fallback humano**: si el agente no puede clasificar el motivo de churn (historial vacío, notas insuficientes, cuenta nueva sin datos), marca la cuenta como `motivo = desconocido — requiere entrevista directa` y recomienda una llamada de diagnóstico. No inventa un motivo.

## 11. Variantes por industria

### Instancia 1 — Servicios profesionales (`consultorabc`)

**Datos típicos**: 20–80 cuentas activas con contrato, MRR USD 3 000–20 000, contratos anuales. Los motivos de churn más frecuentes en este sector: falta de atención del consultor asignado, expectativas de entregables no cumplidas, cambio de decisor en el cliente.

**Delta determinístico**: el `last_meeting_date` tiene más peso en el health score (las relaciones de servicios profesionales dependen de contacto regular). Umbral agresivo: > 45 días sin reunión → flag inmediato.

**Delta agéntico**: el modelo detecta en los tickets si hay quejas sobre el consultor asignado específicamente vs quejas sobre el servicio en general. Esas dos situaciones tienen retenciones distintas (una pide cambio de consultor, la otra pide revisión de metodología).

**Regulación**: contratos de confidencialidad. No almacenar contenido de tickets en sistemas externos al tenant.

**Precio orientativo**: 400–800 USD/mes.

### Instancia 2 — Energía / Utilities (`solenergy`)

**Datos típicos**: 50–120 contratos de servicio (mantenimiento, monitoreo, instalación), MRR USD 8 000–30 000 por contrato, ciclos anuales o bianuales. Clientes industriales con alta presión de costo. Los motivos de churn frecuentes: precio (hay competencia agresiva), SLA incumplidos, cambio de proveedor por compra corporativa del cliente.

**Delta determinístico**: el `invoice_payment_delay_avg_days` tiene más peso en este sector (un cliente que empieza a pagar tarde está teniendo problemas de caja o está priorizando a otro proveedor). Umbral: > 30 días de delay promedio → +25 pts de riesgo.

**Delta agéntico**: el modelo detecta la diferencia entre un cliente que negocia precio agresivamente en cada renovación (comportamiento histórico) vs uno que lo hace por primera vez (señal de cambio de condiciones). El primero es negociación normal; el segundo es señal de riesgo real.

**Regulación**: contratos de suministro energético pueden tener cláusulas de penalidad por terminación anticipada. El agente no puede recomendar «aceptar la terminación» sin que el equipo legal revise las implicaciones contractuales.

**Precio orientativo**: 600–1 200 USD/mes + setup 4–8 k USD (incluye integración World Office/ERP para datos de facturación).

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de ese módulo |
|---|---|
| **A06** — Clases, dataclasses | `AccountHealth`, `ChurnSignal`, `RetentionOffer` como dataclasses. El health score es un cálculo composicional: varios leading indicators → una puntuación. |
| **B02** — FastAPI a profundidad | Endpoint que recibe webhooks de «contrato por renovar» del ERP o CRM y dispara el análisis de riesgo. Validación Pydantic del payload. |
| **C01** — SQLAlchemy async | `account_health_repo` persiste el health score histórico por `(tenant, account_id, date)`. La evolución del score en el tiempo es la métrica clave para detectar deterioro gradual. |
| **D04** — Observabilidad | Phoenix traza `classify_churn_reason` y `propose_retention_offer`. Medir si las propuestas generadas coinciden con lo que los CSMs aceptan (accuracy del agente). |
| **E01** — Anthropic SDK | Prompt caching: el system prompt con el catálogo de motivos de churn + perfil del equipo de CS del tenant es cacheable. El historial de la cuenta es dinámico. |

## 13. Errores típicos

**1. Sobre-confianza en el health score sin baseline de churn real.**
*Síntoma*: el agente marca 15 cuentas como «riesgo alto» cada semana; el CSM actúa en todas y descubre que el 70% no tenían intención de irse. El equipo pierde credibilidad en el sistema.
*Causa raíz*: los umbrales del health score no están calibrados contra el historial real de cuentas que churnearon vs las que renovaron. Sin baseline, el modelo no distingue «señal fuerte» de «señal moderada».
*Cómo evitarlo*: en el setup, construir un golden set con al menos 2 años de historial de renovaciones y churns, y calibrar el umbral de `health_score < 60` contra el percentil de riesgo que históricamente predijo churn real.

**2. Scoring fugado al futuro en la construcción del health score histórico.**
*Síntoma*: durante la evaluación del modelo, el health score predice churn con 90% de precisión en datos históricos; en producción, la precisión cae al 55%.
*Causa raíz*: al reconstruir los health scores históricos para el golden set, se usaron features que solo existen después del evento de churn (p. ej., `tickets_escalated` de la semana posterior al aviso de no renovación, o el último `nps_score` tomado después de que el cliente ya decidió irse).
*Cómo evitarlo*: al construir el health score histórico, usar exclusivamente datos disponibles en `t = 90 días antes del vencimiento del contrato`, no en `t = fecha del churn`. Aplicar un corte temporal estricto: cualquier feature generado después de ese punto de corte es data leakage y no puede usarse para calibrar ni evaluar el modelo.

**3. Propuesta de retención inapropiada por clasificación errónea del motivo.**
*Síntoma*: el agente clasifica como «motivo: precio» a un cliente que se va porque el consultor asignado no responde; el CSM ofrece un descuento y el cliente se va de todas formas, además de molesto.
*Causa raíz*: el historial de la cuenta tiene pocas notas; el modelo clasificó el motivo usando solo los features numéricos (tickets, NPS) sin evidencia textual que lo respalde.
*Cómo evitarlo*: el modelo incluye en su output la evidencia textual usada para la clasificación; si no hay notas, devuelve `motivo = desconocido — requiere entrevista directa`. El CSM valida la hipótesis antes de ejecutar la oferta.

**4. Mensaje de retención enviado automáticamente sin revisión.**
*Síntoma*: el borrador de retención sale directamente al cliente porque alguien configuró `auto_send: true` para agilizar el proceso; el mensaje tiene un tono incorrecto o información confidencial.
*Causa raíz*: el harness permitió habilitar el envío automático sin restricción.
*Cómo evitarlo*: el nodo `human_review` es no-removible en el workflow de retención. El sistema no expone la opción `auto_send` en ningún tier. El borrador siempre llega primero al CSM o al socio responsable de la cuenta.

**5. Churn proyectado comunicado al directorio sin intervalo de confianza.**
*Síntoma*: el CFO toma decisiones de contratación basado en «el churn proyectado es 44 500 USD/mes» cuando en realidad ese número es el peor caso (todas las cuentas at_risk efectivamente churnan).
*Causa raíz*: el reporte presenta el `projected_churn_mrr` como un número único, no como un rango.
*Cómo evitarlo*: el reporte presenta tres escenarios: pesimista (todas las cuentas at_risk churnan), base (las de health < 40 churnan), y optimista (solo las de renovación en < 30 días sin contacto). El CFO trabaja con el escenario base y sabe que el pesimista es el techo.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «¿Cuál es la diferencia entre GRR y NRR? Dame un ejemplo concreto de Consultora ABC donde NRR sea mayor a 100% pero GRR esté en 75%.»
2. **Aplícalo a mi caso**: «¿Cómo adaptaría el pipeline si el cliente no tiene sistema de tickets y la única señal cualitativa disponible son las notas del CRM, que se actualizan el 30% de las veces?»
3. **Por qué falló**: «El agente propuso descuento a tres cuentas que se fueron por feature gap, no por precio. ¿Cómo identifico el patrón de clasificación errónea en el golden set y cómo lo corrijo?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de análisis de churn con health score determinístico y clasificación agéntica del motivo.
- Construir el health score histórico sin data leakage, usando exclusivamente features disponibles 90 días antes del vencimiento del contrato.
- Implementar la oferta de retención diferenciada por motivo (QBR en lugar de descuento para falta de atención, roadmap en lugar de precio para feature gap).
- Configurar el `human_review` como nodo no-removible antes de cualquier comunicación al cliente.
- Presentar el churn proyectado en tres escenarios para que el directorio tome decisiones con contexto real de incertidumbre.

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|--------------------------------|
| **E04** — Memoria de sesión por SDR/cuenta | El historial completo de interacciones con cada cuenta es la base de la clasificación del motivo de churn; sin entender cómo se persiste la sesión por `account_id`, el agente no puede diferenciar el patrón de deterioro gradual del comportamiento histórico normal de esa cuenta. |
| **C01** — SQLAlchemy async | El `account_health_repo` persiste el health score histórico por `(tenant, account_id, date)`; la evolución del score en el tiempo es la métrica clave para detectar deterioro gradual, y requiere el patrón de repositorio async. |
| **A06** — Dataclasses y Pydantic | `AccountHealth`, `ChurnSignal` y `RetentionOffer` como dataclasses; la composición correcta de estos tipos es lo que permite el pipeline determinístico + agéntico sin mezclar la lógica de scoring con la de clasificación. |
| **D04** — Observabilidad | Medir si las propuestas de retención generadas coinciden con lo que los CSMs aceptan (accuracy del agente) requiere trazas en Phoenix; sin observabilidad no hay forma de mejorar el golden set de motivos. |
