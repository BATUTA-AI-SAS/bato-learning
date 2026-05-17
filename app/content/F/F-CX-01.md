---
ext_id: F-CX-01
slug: triage-tickets
track: F
dept: CX
ord: 240
title: "Triage automático de tickets (clasificación, prioridad, ruta)"
summary: "Pipeline que clasifica tickets de soporte por intent, producto y urgencia, aplica reglas duras de SLA y enruta automáticamente, con escalación agéntica para casos de alto riesgo."
related_modules: [A06, B02, C03, E01, E03]
industries_instanced: [retail, servicios-fin]
tenants_in_examples: [tiendabox, cooppopular]
big_corp_vendors: [Zendesk AI, ServiceNow, Salesforce Service Cloud]
latam_tools: [freshdesk, helpscout, hubspot-service]
key_concepts: [clasificacion-multi-label, SLA, routing-rules, escalation, fallback-humano]
estimated_minutes: 45
deterministic_share: 0.4
version: 1
---

## 1. Problema operativo

La jefa de CX de **TiendaBox** recibe 300–500 tickets diarios por email, WhatsApp Business y el formulario del sitio. Hoy los leen dos agentes y los asignan manualmente. El 40% de los tickets urgentes (devoluciones con fecha límite, errores de pago) esperan más de 4 horas porque llegaron en la madrugada o un agente los clasificó mal. El cliente que mandó «me cobraron dos veces y quiero mi dinero ya» entra en la cola de «consulta general» junto con alguien que pregunta «¿cuándo llega mi pedido?». El resultado: SLA roto, CSAT cayendo, y los dos agentes gastando el 30% de su tiempo en clasificar en lugar de resolver.

---

## 2. Hoy en big corps

| Vendor | Qué hace | Precio orientativo |
|--------|----------|--------------------|
| **Zendesk AI** | Clasificación automática de tickets + routing + sugerencia de respuesta; 80% de resolución autónoma según Zendesk | 1 USD/resolución automática sobre plan Suite (55–115 USD/agente/mes) |
| **ServiceNow** | ITSM + clasificación ML; routing avanzado con skills matching | 100–250 USD/agente/mes; impl. 100 k+ USD |
| **Salesforce Service Cloud + Einstein** | Case routing ML + Einstein Service Agent para resolución autónoma; integra CRM para contexto de cliente | 80–300 USD/agente/mes; tier con Einstein desde 150 USD |

En 2026, Zendesk AI Agents resuelven tickets de alta frecuencia (estado de pedido, reset de contraseña, políticas de devolución) sin agente humano. El triage inteligente no es diferenciador: es el piso mínimo para un CX competitivo.

---

## 3. PYME LATAM realista

**TiendaBox** (e-commerce, 80 empleados, 300–500 tickets/día) y **Coop. Popular de Crédito** (servicios financieros, 90 empleados, 50–150 tickets/día por WhatsApp + email) operan con:

- **Freshdesk** (plan gratuito o Growth: 15–49 USD/agente/mes) o **HelpScout** (12–25 USD/mes): herramientas de ticketing accesibles, sin ML integrado.
- **WhatsApp Business API** (via Twilio o proveedor local): canal principal de CX en LATAM; los mensajes de WhatsApp llegan como tickets al helpdesk.
- Clasificación manual: un agente lee y etiqueta. Sin reglas de routing automatizadas más allá de «si el asunto dice "urgente"».
- Zero integración entre el CRM y el helpdesk: el agente no sabe si el cliente que escribió tiene 3 tickets abiertos o es un cliente VIP.

---

## 4. Datos típicos

| Campo | Formato | Fuente | Frecuencia | Volumen |
|-------|---------|--------|------------|---------|
| Mensaje del ticket | Texto libre (20–500 palabras) | Email / WhatsApp / formulario | Continuo | 50–500/día |
| Canal de entrada | Enum (email, whatsapp, web, phone) | Webhook de Freshdesk | Continuo | Por ticket |
| Datos del cliente | JSON (id, nombre, plan, tickets abiertos, valor LTV) | CRM del tenant | Por ticket | 1 fila/cliente |
| Historial de tickets | JSON array (últimos 10 tickets del cliente) | Helpdesk API | Por ticket | 0–10 tickets |
| SLA por categoría | YAML (categoría → tiempo_primera_respuesta, tiempo_resolución) | Config del tenant | Estático | 5–20 reglas |

**Ejemplo de ticket**:

```json
{
  "ticket_id": "TB-29041",
  "channel": "whatsapp",
  "text": "Me cobraron dos veces el pedido #P-8821. Quiero que me devuelvan el dinero. Esto es un robo.",
  "customer_id": "C-4412",
  "customer_ltv_usd": 840,
  "customer_plan": "gold",
  "open_tickets_count": 2,
  "created_at": "2026-04-15T02:34:00Z"
}
```

---

## 5. Tramos determinísticos

1. **Clasificación por keywords/regex (primera capa)** — términos exactos en el texto determinan categorías duras: «cobro doble», «pago duplicado» → categoría `billing_dispute`; «no llega», «tracking», «dónde está» → `shipping_status`. Cubre el 40–50% de los tickets con alta precisión y cero costo de LLM.
2. **Enriquecimiento del ticket** — lookup del `customer_id` en el CRM para añadir: plan, LTV, tickets abiertos, historial. Determinístico: join por ID.
3. **Aplicación de reglas duras de SLA** — si `customer_plan == "gold"` → cola premium (SLA 1h). Si `billing_dispute` → cola financiera (SLA 2h). Si `open_tickets_count > 3` → flag `recurrente` y notificación al supervisor. Todas son reglas cerradas.
4. **Routing inicial** — asignación al agente correcto por área de especialidad según la categoría determinística. Sin LLM.
5. **SLA timer** — el momento de entrada del ticket activa un timer; si no hay primera respuesta en el tiempo de SLA, el sistema escala automáticamente.

---

## 6. Tramos agénticos

1. **Clasificación de tickets que no matchean keywords** — el modelo lee el texto completo y determina intent, producto afectado, y urgencia para el 50–60% de tickets con redacción ambigua o mixta. _Por qué no es regla_: «Mi pedido llegó roto y además me están cobrando el seguro que no pedí» combina `product_damage` + `billing_dispute` + `unwanted_charge`; no hay regex que extraiga los tres intents simultáneamente con su peso relativo.

2. **Priorización según contexto de alto riesgo** — el modelo decide si un ticket necesita escalación inmediata a supervisor humano basándose en: lenguaje legal («voy a demandar», «ya hablé con mi abogado»), amenaza pública («voy a publicar esto en redes»), daño económico potencial alto, cliente VIP con frustración creciente. _Por qué no es regla_: el riesgo de «voy a publicar esto» depende del LTV del cliente, del número de seguidores inferido del canal, y del tono general — no es detectable solo por la frase.

3. **Sugerencia de respuesta inicial** — para tickets simples donde la KB tiene la respuesta, el modelo redacta un borrador de respuesta para que el agente la revise y apruebe con un clic. _Por qué no es regla_: el tono apropiado de la respuesta depende del historial del cliente, del tono de su mensaje, y de las instrucciones de comunicación del tenant.

> [!cuidado]
> El agente nunca envía una respuesta al cliente sin revisión humana. El «send» siempre requiere un clic del agente. El modelo puede preparar el borrador; el humano lo envía.

---

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest] → recibe ticket desde webhook Freshdesk/WhatsApp (determinístico)
  ↓
[enrich] → lookup CRM + historial de tickets (determinístico, tool: sql_query)
  ↓
[classify_deterministic] → keywords/regex → categoría + SLA (determinístico)
  ↓
[classify_agent?] → ¿clasificación determinística suficiente?
    no → [classify_agent] → LLM clasifica intent + producto + urgencia (agéntico)
  ↓
[apply_routing_rules] → asigna cola + agente + SLA timer (determinístico)
  ↓
[risk_check] → ¿lenguaje legal/amenaza/VIP crítico? (agéntico)
    sí → [escalate_human] → interrupt + notifica supervisor (tool: post_slack_message)
  ↓
[draft_response?] → ¿ticket simple con KB match? (determinístico)
    sí → [draft_agent] → borrador de respuesta (agéntico)
  ↓
[human_review] → agente revisa borrador y envía (siempre)
  ↓
END
```

### Activities Temporal (para SLA monitoring continuo)

- `watch_sla_timers(tenant)` — corre como schedule cada 5 min; escala tickets vencidos.
- `process_ticket(tenant, ticket_id)` — corre el grafo por ticket; idempotente por `ticket_id`.

### Tools necesarias

- `sql_query` — lookup CRM + historial de tickets del tenant.
- `post_slack_message` — notificación de escalación al supervisor.
- `write_report` — reporte diario de SLA + clasificaciones.

---

## 8. Salida y entrega

**Dashboard diario** (enviado al jefe de CX):

```
## CX Daily Report — TiendaBox · 2026-04-15

Tickets recibidos: 412
  - Resueltos autónomamente (KB match): 87 (21%)
  - Asignados con borrador: 198 (48%)
  - Asignados sin borrador: 112 (27%)
  - Escalados a supervisor: 15 (4%)

SLA primera respuesta:
  - Cumplidos: 389/412 (94%) ← meta: 90%
  - Incumplidos: 23 (top causa: llegaron entre 2–5 AM, sin agente nocturno)

Categorías más frecuentes:
  1. shipping_status (38%)
  2. billing_dispute (22%)
  3. product_damage (14%)
  4. account_access (11%)

Tickets con alerta de escalación: 15
  - 8 por lenguaje de reclamo legal
  - 7 por cliente VIP con > 3 tickets abiertos
```

---

## 9. Cómo se vende

**Gancho**: «El 40% de los tickets urgentes esperan 4 horas porque alguien los clasificó mal. Nosotros los clasificamos en 3 segundos y los escalamos antes de que el cliente pierda la paciencia».

**Propuesta de valor**: SLA cumplido sistemáticamente, liberación del 30% del tiempo de clasificación manual, y detección de tickets de alto riesgo antes de que lleguen a redes sociales.

| Tier | Condiciones | Precio |
|------|-------------|--------|
| Starter | ≤ 200 tickets/día, 1 canal (email o WhatsApp) | 200–400 USD/mes |
| Growth | ≤ 800 tickets/día, multi-canal | 500–1000 USD/mes |
| Enterprise | > 800 tickets/día + integración CRM profunda | 1000–2500 USD/mes |
| Setup | Integración Freshdesk/HelpScout + calibración SLA | 1000–3000 USD |

---

## 10. Riesgos

**1. Clasificación incorrecta que retrasa un ticket urgente.**
*Síntoma*: un ticket de «fraude en mi cuenta» se clasifica como `billing_inquiry` y espera 4 horas.
*Mitigación*: la lista de keywords de escalación inmediata (fraude, robo, accidente, daño grave, legal) es determinística y no configurable por el cliente sin aprobación del harness. Falla por exceso (falsos positivos de escalación) no por defecto.

**2. PII de clientes en logs de clasificación.**
*Síntoma*: el texto del ticket (que puede incluir número de tarjeta, DNI, o datos de salud) se guarda en los logs del pipeline sin cifrar.
*Mitigación*: los logs del nodo `classify_agent` solo guardan el `ticket_id` y la clasificación resultante, no el texto del cliente. El texto permanece en el sistema de tickets del tenant. Ley 1581 (Colombia): datos financieros de usuarios son datos sensibles con protección reforzada.

**3. Deriva de la clasificación agéntica.**
*Síntoma*: con el tiempo, la distribución de categorías detectadas por el LLM se desvía de la realidad (el modelo «se acostumbra» a patrones que ya no son los actuales).
*Mitigación*: revisión mensual de una muestra de 100 tickets clasificados por el agente vs. la clasificación que haría un humano (golden set). Si la precisión cae < 85%, se recalibra el prompt.

**4. Dependencia del canal WhatsApp.**
*Síntoma*: un cambio en la API de WhatsApp Business o en el plan de Meta corta el canal principal de entrada.
*Mitigación*: el webhook de ingesta es independiente del canal; si WhatsApp falla, los tickets entran por email de fallback. El tenant tiene un número alternativo para crisis.

---

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 300–500 tickets/día; canal dominante WhatsApp (60%) + email (30%) + web (10%); picos en Black Friday, día de la madre, diciembre; categorías: shipping, devoluciones, billing, producto.

**Delta determinístico**: integración con el sistema de tracking de paquetes; el ticket de «¿dónde está mi pedido?» se responde automáticamente con el estado del tracking sin LLM ni agente humano (deflection rate objetivo: 30%).

**Delta agéntico**: en picos de volumen (Black Friday), el modelo detecta tickets que son quejas sobre el mismo problema sistémico (ej: «todos los pedidos de la zona norte llegaron rotos») y los agrupa en un incidente, notificando al equipo de operaciones en lugar de responderlos individualmente.

**Regulación**: LFPDPPP México / Ley 1581 Colombia: los datos del cliente (dirección, compras) son datos personales; el agente no los menciona en el borrador de respuesta sin necesidad.

**Precio orientativo**: 400–900 USD/mes según volumen.

### Instancia 2 — Servicios financieros (`cooppopular`)

**Datos típicos**: 50–150 tickets/día; canal WhatsApp (80%) + presencial convertido a ticket; categorías: movimientos de cuenta, crédito, aportes, fraude; lenguaje de los socios varía entre formal y coloquial.

**Delta determinístico**: los tickets de «no reconozco este movimiento» se clasifican automáticamente como `possible_fraud` y disparan un bloqueo preventivo de la cuenta mientras un agente humano confirma — esto es una regla dura, no agéntica, para minimizar el riesgo de fraude real.

**Delta agéntico**: el modelo detecta si el socio expresa confusión sobre un producto financiero (no un problema operativo) y sugiere agendar una llamada de asesoría en lugar de resolver por texto, porque el riesgo de malinterpretación en temas financieros es alto.

**Regulación**: Colombia — Superfinanciera exige tiempos máximos de respuesta a peticiones, quejas y recursos (PQR): 15 días hábiles para PQR formal. El pipeline registra la fecha de entrada y avisa si el SLA regulatorio está en riesgo. LGPD Brasil si la coop opera allá.

**Precio orientativo**: 300–700 USD/mes; setup con integración core bancario 3000–8000 USD.

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de él |
|--------|-----------------|
| **A06** — Pydantic | El schema `TicketPayload` valida el webhook de entrada; si un campo requerido falta (ej: `customer_id`), el ticket se encola para revisión manual antes de entrar al pipeline. |
| **B02** — FastAPI routing + deps | El endpoint `POST /tickets/ingest` es el webhook receptor; el `Depends(get_tenant)` garantiza que el routing rules del tenant correcto se aplica. |
| **C03** — Multitenancy | Las reglas de SLA, la lista de keywords de escalación, y la cola de agentes son configuraciones por tenant almacenadas con `tenant_id`; sin `tenant_id` en cada query, un ticket de TiendaBox podría ver las reglas de Coop. Popular. |
| **E01** — Anthropic SDK | El nodo `classify_agent` usa `cache_control: ttl:"1h"` sobre el system prompt con las reglas de clasificación del tenant (estático); el texto del ticket va sin cache (dinámico). |
| **E03** — Skills por tenant | El tono de los borradores de respuesta, el glosario de productos, y las instrucciones de escalación se inyectan como skill por tenant; el mismo agente redacta en tono formal para Coop. Popular y en tono cercano para TiendaBox. |
| **A07** — Async + concurrencia | En picos de volumen, múltiples tickets se procesan concurrentemente con `asyncio.gather`; el módulo enseña el patrón de semáforo para no saturar el rate limit del LLM. |
| **D04** — Observabilidad | Cada ticket procesado genera un span en Phoenix: latencia de clasificación, tokens usados, categoría asignada, y si fue escalado. El reporte diario de SLA (sección 8) se construye sobre estas métricas. Si la tasa de re-clasificación manual supera el 15%, la traza lo detecta y alerta para recalibrar el prompt. |

## 13. Errores típicos

**1. PII en el texto del ticket guardado en los logs del pipeline.**
*Síntoma*: la transcripción completa del mensaje de WhatsApp (con número de tarjeta o datos de salud del cliente) queda en los logs de clasificación accesibles a toda la plataforma.
*Causa raíz*: el nodo `classify_agent` guarda el payload completo del ticket en el log de trazas sin aplicar el PII scrubber antes.
*Cómo evitarlo*: los logs del nodo de clasificación solo persisten `{ticket_id, category, confidence, escalated}`; el texto del cliente permanece exclusivamente en el sistema de tickets del tenant. Ley 1581 (Colombia) y LGPD (Brasil) clasifican los datos financieros y de salud como datos sensibles con protección reforzada; una fuga implica notificación obligatoria a la autoridad de protección de datos.

**2. El agente nunca escala porque nadie configuró la lista de keywords de riesgo.**
*Síntoma*: tickets con «voy a demandar» o «fraude» pasan por la cola general y esperan 4 horas.
*Causa raíz*: el tenant dejó vacía la sección `escalation_keywords` en el YAML de configuración, y el fallback es no escalar.
*Cómo evitarlo*: la lista de keywords de escalación inmediata tiene un conjunto mínimo no-eliminable definido en el harness (fraude, legal, denuncia, robo); el tenant solo puede añadir, nunca vaciar la lista completa.

**3. El borrador de respuesta se envía directamente al cliente sin revisión humana.**
*Síntoma*: el agente tiene un bug en el nodo `human_review` que no interrumpe el flujo; el borrador sale automáticamente.
*Causa raíz*: el flag `auto_send = True` fue activado en un experimento y no se revirtió.
*Cómo evitarlo*: el `interrupt_before: human_review` es un nodo no-removible del grafo LangGraph. Las pruebas de integración validan explícitamente que el flujo no puede llegar a `send_reply` sin pasar por el interrupt.

**4. Deriva silenciosa de la clasificación agéntica.**
*Síntoma*: al cabo de 3 meses, la categoría `billing_dispute` solo aparece en el 5% de los tickets cuando históricamente era el 22%; nadie lo nota.
*Causa raíz*: el modelo cambió de versión y su distribución de clasificaciones se desplazó; las métricas de SLA no detectan esto porque el SLA se cumple igual.
*Cómo evitarlo*: monitorear la distribución de categorías semana a semana en el dashboard de D04. Una desviación > 30% respecto al promedio histórico dispara alerta para recalibración del prompt.

**5. Ticket de canal WhatsApp perdido por cambio de plan en la API de Meta.**
*Síntoma*: durante 6 horas un domingo los tickets de WhatsApp no ingresan; el SLA se rompe sin que nadie lo sepa.
*Causa raíz*: el webhook de Twilio fue suspendido por falta de pago y el pipeline no tiene canal de fallback configurado.
*Cómo evitarlo*: el nodo `ingest` valida la salud del webhook cada hora; si falla, activa el canal de email de emergencia y notifica al administrador del tenant por SMS.

---

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame por qué la detección de lenguaje legal ('voy a demandar') es un tramo agéntico y no simplemente una lista de palabras clave determinística, con un ejemplo de caso donde la regla sola falla.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este pipeline de triage si mi operación recibe el 80% de los tickets como audios de WhatsApp y no como texto escrito.»
3. **Por qué falló**: «El ticket TB-29041 fue clasificado como `billing_inquiry` en lugar de `billing_dispute` y llegó tarde al área financiera. ¿En qué nodo del workflow ocurrió el error y qué cambiaría en el prompt o en las reglas determinísticas para prevenirlo?»

---

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline completo de triage desde la ingesta del webhook hasta el routing con SLA timer, separando claramente tramos determinísticos de agénticos.
- Identificar qué casos deben escalarse por regla dura (fraude, lenguaje legal) versus qué casos requieren juicio del modelo (riesgo contextual de un VIP).
- Implementar el fallback humano obligatorio antes de cualquier envío de respuesta al cliente, con el interrupt correcto en LangGraph.
- Evaluar el impacto de privacidad de cada nodo del pipeline y aplicar los controles de PII requeridos por Ley 1581 y LGPD.
- Decidir el tier de precio adecuado para un cliente dado su volumen de tickets y nivel de integración requerida.

---

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|---------------------------------|
| **E01** — Anthropic SDK + tools | El nodo `classify_agent` usa tool calling con respuesta estructurada (`category`, `urgency`, `confidence`); sin el patrón de tool loop, el estudiante no puede implementar la clasificación agéntica correctamente. |
| **E03** — Skills por tenant | El tono del borrador y las reglas de escalación varían por tenant; E03 enseña a inyectar estas diferencias sin duplicar el agente. |
| **E04** — Memoria y sesiones | El enriquecimiento del ticket con el historial del cliente (¿cuántos tickets abiertos? ¿es VIP?) es memoria de sesión por `customer_id`; sin E04, el estudiante trata cada ticket como si fuera el primero. |
| **D04** — Observabilidad y trazas auditables | El reporte diario de SLA y la detección de deriva de clasificación se construyen sobre las trazas de Phoenix; D04 enseña exactamente este patrón de métricas por span. |
| **C03** — Multitenancy | Las reglas de SLA, las colas de agentes y las keywords de escalación son por tenant; sin C03, el pipeline aplica las reglas de TiendaBox a Coop. Popular. |
