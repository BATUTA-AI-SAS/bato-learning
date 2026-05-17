---
ext_id: F-FIN-04
slug: gestion-credito-cobranza
track: F
dept: FIN
ord: 103
title: "Gestión de crédito y cobranza temprana"
summary: "Agente que monitorea el aging de cartera, calibra el tono de comunicación por historial de cliente, y escala automáticamente antes de que la deuda entre en mora."
related_modules: [B02, B06, C03, E01, E04]
industries_instanced: [retail, logistica]
tenants_in_examples: [tiendabox, expreslog]
big_corp_vendors: [HighRadius, Billtrust, Esker]
latam_tools: [siigo, alegra, kushki, mercadopago]
key_concepts: [aging, scoring-riesgo, tono-comunicacion, escalamiento, DSO, human-in-the-loop-VIP]
estimated_minutes: 60
deterministic_share: 0.5
version: 1
---

## 1. Problema operativo

El equipo de cobranza de TiendaBox tiene 400 clientes B2B activos. Cada mes, un porcentaje de facturas vence sin pagar. La persona de cobranza manda el mismo correo genérico de «recuérdele que tiene una factura pendiente» a todos, sin importar si el cliente es un distribuidor que lleva 3 años pagando con 5 días de retraso típico o si es uno nuevo que lleva 45 días sin señales de vida.

El resultado: los clientes buenos se molestan por el tono, los clientes malos siguen sin pagar porque el correo genérico no genera urgencia, y el equipo de ventas se queja porque el equipo de cobranza «arruina relaciones».

Logística Express tiene el mismo problema pero con un matiz: sus clientes son transportistas y almacenes que operan con márgenes ajustados; un correo agresivo a tiempo puede reemplazar semanas de espera.

## 2. Hoy en big corps

| Vendor | Producto | Capacidad clave | Inversión orientativa |
|--------|----------|-----------------|-----------------------|
| **HighRadius** | Autonomous Receivables (Collections) | Scoring de riesgo por cliente, workflow de cobranza multicanal (email/llamada/portal), predicción de días de pago | 500–3 000 USD/mes (flat) + impl. 20–80 k USD |
| **Billtrust** | Collections Management + AI Buyer Portal | Agentic alert layer sobre días-a-pago, variaciones de comportamiento, señales de autopago; 13W AR forecast integrado | pricing por volumen de AR |
| **Esker** | Accounts Receivable | Workflow de escalamiento automático, portal de pago self-service, AI para priorizar llamadas | 20–100 USD/usuario/mes; impl. 15–50 k USD |

HighRadius y Billtrust tienen casos documentados de reducción de DSO del 20–50 %. El problema para PYME LATAM: el mínimo de implementación de HighRadius supera el presupuesto anual de automatización.

## 3. PYME LATAM realista

- **Cartera**: reporte de aging de Siigo o Alegra (CSV con columnas `cliente,factura,fecha_vencimiento,dias_vencida,monto`). Sin API push; hay que hacer pull periódico.
- **Historial de pagos**: en el mismo ERP; hay que calcularlo. No hay scoring preconfigurado.
- **Canal de comunicación**: email (SMTP transaccional con Mailgun/SES) como primera línea. WhatsApp Business API como segunda línea para clientes en Colombia/México donde el canal tiene alta tasa de apertura.
- **CRM**: muchas PYMEs no tienen CRM formal. Los comentarios de cobranza viven en un Excel de seguimiento o en emails.
- **Equipo**: 1 persona de cobranza para 200–500 clientes. El agente es el «primer contacto»; el humano interviene en escalamientos.

## 4. Datos típicos

| Atributo | Aging de cartera (Siigo) | Historial de pagos (calculado) |
|----------|--------------------------|-------------------------------|
| Formato | CSV: `cliente,factura,emision,vencimiento,monto,dias_vencida` | Tabla calculada: `cliente,factura,dias_reales_pago,bucket` |
| Frecuencia | Pull diario (automatizable con Siigo API o CSV programado) | Mensual (batch) |
| Volumen | 100–600 facturas abiertas | 12–24 meses de historial |
| Ejemplo de fila | `DIST NORTE SAS,FAC-2026-0341,2026-04-01,2026-04-30,4820000,15` | `DIST NORTE SAS,FAC-2026-0299,32,31-60` |

**Buckets de aging estándar**: 0–30 días, 31–60, 61–90, 91–120, >120 días.

## 5. Tramos determinísticos

1. **Cálculo del aging por bucket**: para cada factura abierta, `dias_vencida = today - fecha_vencimiento`. Clasificación en buckets. Suma por cliente y por bucket.
2. **Cálculo del DSO actual**: `DSO = (cartera_total / ventas_30d) × 30`. Comparación con DSO objetivo (configurable por tenant).
3. **Scoring de riesgo basado en historial**: para clientes con historial, `risk_score = media_dias_reales_pago / dias_credito_acordados`. Score > 1.5 = riesgo alto; 1.0–1.5 = medio; < 1.0 = bajo. Esto es aritmética pura sobre datos históricos.
4. **Generación de listas de gestión**: lista priorizada por `(bucket, risk_score, monto)` para la persona de cobranza. Fórmula determinística; el agente no decide el orden, la fórmula sí.
5. **Regla dura VIP**: si el cliente tiene flag `is_vip = true` en la configuración del tenant, **ninguna comunicación automatizada** se envía sin sign-off del gerente comercial. Esta regla es no-negociable y vive en código, no en el LLM.
6. **Trigger de comunicación**: si `dias_vencida >= umbral_primer_contacto` (configurable, default: 5) y el cliente no tiene `is_vip`, se activa el flujo de comunicación.

## 6. Tramos agénticos

1. **Calibración de tono por perfil de cliente**: el agente determina el tono del correo de cobranza basándose en el `risk_score`, el valor del cliente (facturación histórica), el contexto de la relación comercial (notas del CRM si existen), y el bucket de aging. Un cliente de bajo riesgo que suele pagar en 32 días recibe un recordatorio amable; uno de alto riesgo en bucket 61–90 recibe un correo con fecha límite y mención a consecuencias. **No es regla** porque la combinación de factores y sus pesos varía por cliente, industria y política interna del tenant.
2. **Decidir momento de escalamiento**: el agente evalúa si una factura debe escalar de correo automático a llamada telefónica (humano) o a carta de cobro jurídico. La decisión combina `dias_vencida`, respuesta a comunicaciones anteriores, valor del cliente, y señales de comportamiento reciente (¿pagó otras facturas en el mismo período?). No hay una fórmula que capture todos los casos.
3. **Detectar cambio de comportamiento**: Billtrust llama a esto «agentic alert layer». El agente monitorea si un cliente que históricamente pagaba en 30 días empieza a pagar en 45, o si cancela la suscripción de autopago. Esos cambios son señales tempranas de dificultad de liquidez del cliente. **No hay regla** que defina cuándo un cambio es significativo vs ruido; el agente razona sobre la tendencia.
4. **Redacción de la comunicación**: el agente redacta el correo/WhatsApp adaptado al tono decidido, con el detalle de las facturas pendientes, la fecha límite, y el enlace de pago. La redacción adapta el español al contexto regional del cliente (Colombia vs México tienen convenciones distintas de formalidad en comunicación comercial).
5. **Fallback humano**: (a) clientes VIP: siempre pasa por sign-off del gerente comercial antes de enviar. (b) Si el agente detecta que el cliente ha respondido indicando una disputa sobre el monto, detiene el flujo automatizado y escala a la persona de cobranza con un resumen de la disputa. El agente no resuelve disputas.

## 7. Blueprint del workflow

### Nodos LangGraph (corrida diaria por tenant)

```
START
  ↓
[ingest_aging] → erp_fetch_transactions(erp, period, account="AR", tenant)
  ↓               → tabla de aging actualizada
[compute_buckets] → cálculo determinístico de aging + DSO (Python puro)
  ↓
[load_history] → sql_query(historial_pagos_cliente, tenant)
  ↓
[score_risk] → cálculo determinístico de risk_score por cliente
  ↓
[filter_actionable] → filtrar: dias_vencida >= umbral AND NOT is_vip (determinístico)
  ↓
[for each cliente_actionable]:
  ├─ [check_vip] → router: ¿is_vip?
  │   └─ SÍ → [queue_vip_review] → interrupt_before → notificar gerente comercial
  │
  └─ NO ↓
[detect_behavior_change] → LLM analiza tendencia días-a-pago (agéntico)
  ↓
[decide_action] → LLM decide: recordatorio / escalamiento / alerta disputa (agéntico)
  ↓
[draft_comms] → LLM redacta comunicación con tono calibrado (agéntico)
  ↓
[send_comms] → send_email(to=[cliente], tenant) [requires_confirmation si bucket>61]
  ↓
[log_action] → sql_query(insert accion_cobranza, tenant)
  ↓
END
```

### Activities Temporal (Schedule: diario 08:00 por tenant)

- `ingest_ar(tenant, date)` — pull del aging actualizado.
- `run_collections_agent(tenant, date)` — ejecuta el grafo; timeout 20 min (puede haber muchos clientes).
- `persist_actions(tenant, date, payload)` — registro de acciones enviadas.

### Tools necesarias

| Tool | Uso |
|------|-----|
| `erp_fetch_transactions` | Aging de AR desde Siigo/Alegra |
| `sql_query` | Historial de pagos, notas de CRM, configuración VIP |
| `send_email` | Comunicación de cobranza |
| `post_slack_message` | Alerta al gerente comercial para clientes VIP |

## 8. Salida y entrega

**Dashboard diario** (reporte XLSX o vista en la app) con:

1. `KPIs`: DSO actual vs objetivo, cartera total por bucket, clientes en escalamiento, acciones enviadas hoy.
2. `Clientes en acción`: tabla con cliente, factura(s), días vencida, bucket, acción tomada, próximo paso.
3. `Alerta de cambio de comportamiento`: lista de clientes donde el agente detectó cambio de tendencia.

**Email diario resumen** a la persona de cobranza (no al CFO): lista de acciones tomadas y escalamientos pendientes.

**Alerta VIP** vía Slack al gerente comercial con el borrador de la comunicación para aprobación.

## 9. Cómo se vende

**Gancho**: «Tu equipo de cobranza manda el mismo correo a todos. Nosotros ajustamos el tono para cada cliente basándonos en su historial, y escalamos antes de que la deuda entre en mora legal.»

**Propuesta de valor**: reducción de DSO 10–25 % en 3 meses; cero comunicaciones a clientes VIP sin aprobación; equipo de cobranza enfocado en escalamientos reales, no en recordatorios.

| Tier | Qué incluye | Precio USD/mes |
|------|-------------|----------------|
| Básico | 1 ERP, hasta 200 clientes activos, email only | 150–300 |
| Estándar | 500 clientes, WhatsApp Business, scoring automático | 300–700 |
| Premium | clientes ilimitados, multi-canal, CRM integration, SLA | 700–1 500 |

Setup: 1 500–3 500 USD (calibración del scoring, golden set de 30 clientes, configuración de reglas VIP).

## 10. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **Tono inapropiado daña relación comercial**: el agente usa tono formal con un cliente que espera trato amigable | Media | Alto | Golden set de 20 comunicaciones aprobadas por el tenant antes de producción. Revisión humana durante las primeras 4 semanas de operación. |
| **Comunicación a cliente en disputa activa**: el agente no sabe que hay una disputa abierta | Alta | Alto | La persona de cobranza marca en el sistema (campo `disputa_activa`) antes de que corra el agente. El agente verifica ese campo como primer paso. |
| **Exposición legal (Colombia/México)**: la comunicación de cobranza tiene restricciones legales (horarios, canales, contenido) | Alta | Alto | Template de comunicación revisado por abogado del tenant. El agente no modifica las cláusulas legales. |
| **WhatsApp API cost spike**: en temporada alta con muchos clientes, el costo de mensajes puede escalar | Media | Bajo | Límite configurable de mensajes WhatsApp por día por tenant. Por encima del límite, cae a email. |
| **Datos de deuda en prompts**: montos de deuda y nombres de clientes en los prompts del LLM | Alta | Medio | Los nombres de empresas y montos son datos de negocio, no PII de personas naturales. Registrar en política de datos. Evitar incluir datos de clientes persona natural. |

## 11. Variantes por industria

### Instancia 1 — Retail B2B (`tiendabox`)

**Datos típicos**: 200–500 clientes (distribuidores y tiendas), facturas de 500 000–5 000 000 COP, ciclos de pago 30 días acordados. Alta estacionalidad: cartera se dispara en diciembre y enero.

**Delta determinístico**: agrupación de facturas por campaña estacional (navidad, temporada escolar) para ajustar el umbral de escalamiento en esos períodos. La regla es simple: en diciembre, el umbral de primer contacto sube de 5 a 10 días.

**Delta agéntico**: identificar clientes que en años anteriores tuvieron problemas de cartera en Q1 (post-temporada navidad) y anticipar la comunicación preventiva en noviembre. El agente cruza el historial de aging de los últimos 2 años con el calendario estacional.

**Precio orientativo**: 250–600 USD/mes; TiendaBox tiene ~300 clientes B2B activos.

---

### Instancia 2 — Logística / 3PL (`expreslog`)

**Datos típicos**: 50–150 clientes (empresas medianas con contratos de servicio), facturas de 2 M–50 M COP por despacho consolidado, contratos con términos de pago 45–60 días. La cartera vive en ciclos largos.

**Delta determinístico**: las facturas de logística tienen una lógica de disputa muy común: el cliente objeta un cargo por daño o entrega tardía. El sistema marca automáticamente como `pending_dispute` cualquier factura con una nota de objeción en el tracking del despacho asociado.

**Delta agéntico**: en logística, el cliente más valioso puede ser también el que paga más tarde porque negocia mejores condiciones. El agente pondera el `Lifetime Value` del cliente (calculado determinísticamente) para decidir si el tono duro se aplica o no, incluso estando en bucket 61–90. Un cliente que genera el 30 % de la facturación de Logística Express recibe un trato diferente aunque esté vencido.

**Regulación**: en Colombia, la Ley 1231 de 2008 regula la factura como título valor. Una factura protestada no puede enviarse a cobro ejecutivo sin proceso previo. El agente incluye en el escalamiento jurídico una verificación de si la factura fue «aceptada» formalmente por el cliente (dato del ERP).

**Precio orientativo**: 350–800 USD/mes; volumen más bajo de clientes pero mayor complejidad por disputas.

## 12. Módulos técnicos relacionados

| Módulo | Por qué aplica |
|--------|---------------|
| **E04** — Memoria y sesiones | El historial de comunicaciones con cada cliente es la «memoria» del agente. E04 enseña cómo gestionar el `thread_id` por cliente y persistir el contexto entre corridas diarias. |
| **E01** — Anthropic SDK | El nodo `decide_action` es un loop tool_use: el modelo lee el perfil del cliente y emite la acción estructurada (`{action: "escalate", channel: "whatsapp", tone: "firm"}`). Ejemplo directo de E01. |
| **B06** — SSE y chat | Si el gerente comercial quiere preguntar «¿cómo va la cartera de este cliente?», la respuesta puede venir por el chat SSE del panel de administración. B06 enseña ese patrón. |
| **C03** — Multitenancy | La regla VIP es por tenant; los umbrales de aging son por tenant. C03 enseña cómo el repo filtra siempre por `tenant_id` y cómo la configuración por tenant se almacena en DB. |
| **B02** — FastAPI + Pydantic | El endpoint `/collections/approve-vip` que recibe el sign-off del gerente comercial es un ejemplo de B02: validación de body, respuesta JSON, llamada al servicio. |
| **D04** — Observabilidad | El span de `run_collections_agent` en Phoenix muestra cuántos clientes procesó, cuántos correos envió, y el costo total de LLM por corrida. Referencia directa para D04. |

## 13. Errores típicos

**1. `is_vip` verificado después del nodo de comunicación en lugar de antes.**
*Síntoma*: el agente redacta y envía un correo de cobranza a un cliente VIP de TiendaBox antes de que el gerente comercial apruebe; el cliente llama molesto a las 9 de la mañana.
*Causa*: el router `check_vip` está ubicado después del nodo `draft_comms` en el grafo; el correo se envía antes de llegar al checkpoint de aprobación.
*Cómo evitarlo*: el nodo `check_vip` debe ser el primer nodo del loop por cliente, antes de cualquier acción. El grafo no puede continuar hacia `detect_behavior_change` si `is_vip = true`; va directamente a `queue_vip_review`.

**2. Scoring de riesgo calculado con historial de menos de 3 pagos para clientes nuevos de Logística Express.**
*Síntoma*: un cliente nuevo de Expreslog con 2 facturas pagadas, ambas a tiempo, recibe un `risk_score` de 1.0 (neutro), pero la segunda factura está a 75 días vencida; el agente usa tono amable porque el score histórico no refleja el comportamiento reciente.
*Causa*: el cálculo de `risk_score` usa el promedio histórico sin ponderar los pagos más recientes.
*Cómo evitarlo*: para clientes con `count_historico < 5`, el score se calcula con el promedio del sector más un ajuste por el comportamiento del bucket actual. Si la factura está en bucket 61–90, el score mínimo es 1.3 independientemente del historial.

**3. Campo `disputa_activa` no verificado porque la persona de cobranza anotó la disputa en el Excel de seguimiento pero no en la app.**
*Síntoma*: el agente envía un correo de cobro urgente a un cliente que presentó una disputa formal ayer; el cliente responde con una queja y el equipo legal de TiendaBox debe intervenir.
*Causa*: el sistema tiene dos fuentes de verdad para las notas de cobranza: la app y un Excel paralelo que el equipo mantiene por costumbre.
*Cómo evitarlo*: eliminar el Excel paralelo en el onboarding. La app debe ser la única fuente de verdad para `disputa_activa`. Si el equipo resiste, añadir una integración de importación desde el Excel que sincroniza el campo antes de cada corrida.

**4. Comunicación enviada al mismo cliente desde dos corridas concurrentes del Schedule.**
*Síntoma*: Distribuidora Norte recibe dos correos de cobro el mismo día con distinto tono porque el Schedule del lunes y una corrida manual disparada por el gerente corren en paralelo.
*Causa*: no hay lock por cliente que impida dos corridas simultáneas.
*Cómo evitarlo*: al iniciar la corrida, insertar un registro `lock(tenant, cliente, date)` en DB. Si el lock existe, saltar ese cliente. El `idempotency_key` de Temporal previene corridas duplicadas del Schedule, pero no bloquea corridas manuales.

## 14. Pregúntale al tutor

1. «Explícame cómo calibraría el nodo `decide_action` para Logística Express, donde el cliente más valioso (30 % de la facturación) está en bucket 61–90 con una disputa parcial. ¿Qué información mínima necesita el prompt para tomar la decisión correcta?»
2. «Audita mi implementación del nodo `detect_behavior_change` para TiendaBox y dime si detectaría a tiempo un cliente que pasó de pagar en 28 días a pagar en 50 días durante los últimos 3 meses de forma gradual.»
3. «Genera el código mínimo del nodo `score_risk` en Python que calcula el `risk_score` por cliente usando el historial de 6 meses y aplica el ajuste por bucket actual para clientes con menos de 5 pagos en el historial.»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el grafo de cobranza con el router `check_vip` como primer nodo del loop por cliente, antes de cualquier acción.
- Implementar el scoring de riesgo con ajuste por bucket para clientes nuevos sin historial suficiente.
- Configurar la verificación de `disputa_activa` como prerequisito bloqueante antes de cualquier comunicación automatizada.
- Decidir cuándo el agente escala de correo a llamada o a cobro jurídico combinando `dias_vencida`, `risk_score` y respuesta histórica.
- Dimensionar el costo diario de LLM para un tenant con 400 clientes activos y estimar cuántos clientes llegan al nodo `draft_comms` en un día típico.

## 16. Módulos previos recomendados

| Módulo previo | Por qué te prepara |
|---------------|-------------------|
| **E04** — Memoria y sesiones | El historial de comunicaciones con cada cliente es la memoria del agente; E04 enseña cómo persistir el `thread_id` por cliente entre corridas diarias antes de implementar este workflow. |
| **E01** — Anthropic SDK | El nodo `decide_action` es un loop `tool_use` con salida estructurada `{action, channel, tone}`; E01 enseña ese patrón antes de implementarlo. |
| **C03** — Multitenancy | Las reglas VIP y los umbrales de aging son por tenant; C03 enseña cómo el repo filtra por `tenant_id` y cómo la configuración por tenant se almacena en DB. |
| **B06** — SSE y chat | La consulta del gerente comercial «¿cómo va la cartera de este cliente?» en el panel responde por SSE; B06 enseña ese patrón de respuesta en streaming. |
| **D04** — Observabilidad | El span `run_collections_agent` en Phoenix muestra el costo total de LLM por corrida y cuántos clientes llegaron a `draft_comms`; D04 enseña cómo leer esa métrica para optimizar el umbral de activación. |
