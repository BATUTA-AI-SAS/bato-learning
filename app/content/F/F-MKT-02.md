---
ext_id: F-MKT-02
slug: segmentacion-propuestas
track: F
dept: MKT
ord: 202
title: "Segmentación de clientes y propuesta de campañas"
summary: "Agente que calcula segmentos RFM sobre la base de clientes y genera briefs de campaña en lenguaje de marketing, listos para que el equipo los ejecute."
related_modules: [A06, B02, C01, D04, E01]
industries_instanced: [retail, hospitalidad]
tenants_in_examples: [tiendabox, mesonurbano]
big_corp_vendors: [Salesforce Marketing Cloud, Braze, Klaviyo]
latam_tools: [klaviyo, mailchimp, excel]
key_concepts: [RFM, recencia, frecuencia, monetización, segmento, brief-creativo, propensity]
estimated_minutes: 45
deterministic_share: 0.3
version: 1
---

## 1. Problema operativo

La gerente de marketing de TiendaBox Retail envía la misma campaña de email a todos sus 22 000 clientes. El open rate promedio es 18%. Sabe que hay clientes que compran cada semana y clientes que compraron una vez hace ocho meses. Enviarles lo mismo es desperdiciar presupuesto y quemar la base. Pero segmentar manualmente, definir mensajes por segmento, y escribir un brief creativo por segmento le tomaría una semana de trabajo.

En Mesón Urbano F&B el problema es parecido: 3 500 clientes en su base de emails y WhatsApp Business. El dueño sabe que algunos son habituales del almuerzo de lunes a viernes, otros vienen solo en cumpleaños y fechas especiales, y otros son turistas que vinieron una sola vez. Estrategias distintas para cada grupo, pero sin capacidad de análisis.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|---|---|---|
| **Salesforce Marketing Cloud** | Segmentación avanzada (Journey Builder + Audience Studio), análisis predictivo de propensión, personalización en tiempo real. | 400–3 200 USD/mes según módulos; impl. 30–150 k USD |
| **Braze** | Customer engagement platform: segmentación en tiempo real, mensajería multicanal (email, push, SMS, WhatsApp). Fuerte en apps móviles. | 30 000–200 000 USD/año según MAU |
| **Klaviyo** | Mid-market/SMB-friendly: segmentación por comportamiento, flujos automatizados, predicciones de CLV y propensión de compra. | 20–700 USD/mes hasta 25k contactos; escalable |

Klaviyo es el único vendor de esta lista accesible para PYME LATAM (plan gratuito hasta 500 contactos, plan básico desde 45 USD/mes). Las otras dos son enterprise.

## 3. PYME LATAM realista

TiendaBox tiene su base de clientes en Klaviyo (o Mailchimp), con historial de compras en su plataforma e-commerce (Shopify/WooCommerce) o en una planilla exportada del POS. El historial está, pero nadie lo analiza: se envían campañas a «todos» o a «los que compraron en los últimos 30 días» (segmento manual, sin refinamiento).

Mesón Urbano tiene la base en WhatsApp Business y una lista de emails en Mailchimp. No tiene un CRM. Los datos de compra están en el sistema de caja (Aleph o un POS básico), que exporta transacciones en CSV. No hay un ID de cliente unificado entre el sistema de caja y el email. La segmentación es artesanal.

> [!cuidado]
> **Regulación LATAM (obligatorio antes de enviar)**:
> - **Brasil (LGPD)**: el envío de mensajes de marketing por email o WhatsApp Business requiere opt-in explícito y documentado del destinatario. La multa por infracción puede llegar a 2% del ingreso anual del negocio, con tope de R$50 millones por infracción. El pipeline verifica `opt_in_marketing = true` con fecha de captura antes de incluir cualquier cliente en un segmento de envío.
> - **Argentina (Ley 25.326)**: las comunicaciones comerciales no solicitadas están prohibidas. La base legal es el consentimiento expreso del titular del dato. Los clientes sin consentimiento documentado se excluyen del segmento antes de pasar al LLM.

## 4. Datos típicos

| Campo | Fuente | Frecuencia | Ejemplo de fila |
|---|---|---|---|
| `customer_id` | POS / e-commerce | por transacción | `"CUS-8291"` |
| `email` | Klaviyo / Mailchimp / POS | por cliente | `"c.ramirez@gmail.com"` |
| `last_purchase_date` | POS / e-commerce | por transacción | `"2026-03-14"` |
| `days_since_last_purchase` | calculado | diario | `63` |
| `total_purchases_count` | POS | por cliente | `8` |
| `total_spend_usd` | POS | por cliente | `3240` |
| `avg_order_value_usd` | calculado | por cliente | `405` |
| `purchase_category_primary` | POS | por cliente | `"ropa-deportiva"` |
| `channel` | POS | por compra | `"online"` / `"tienda-física"` |
| `open_rate_email` | Klaviyo / Mailchimp | por cliente | `0.42` |
| `click_rate_email` | Klaviyo / Mailchimp | por cliente | `0.11` |

**RFM**: modelo de segmentación tridimensional de clientes.
- **R (Recencia)**: días desde la última compra. Menor = más reciente = mayor puntaje.
- **F (Frecuencia)**: número total de compras en el período de análisis.
- **M (Monetización)**: gasto total en el período de análisis.

Cada dimensión se quintiliza (1–5, donde 5 es mejor). Un cliente con R=5, F=5, M=5 es el segmento más valioso. Uno con R=1, F=1, M=1 es el más inactivo.

**CAC (Customer Acquisition Cost)**: gasto total en adquisición dividido por el número de clientes nuevos captados. `CAC = spend_periodo / new_customers`. Si el segmento «champions» tiene CAC de 80 USD, saber eso permite calibrar cuánto se puede invertir en retenerlos.

**LTV (Lifetime Value)**: ingreso total esperado de un cliente durante toda su relación con el negocio. Estimación conservadora: `LTV ≈ avg_order_value × compras_anuales × años_estimados`. Para retail LATAM, un horizonte de 2–3 años es razonable.

**CTR (Click-Through Rate)**: porcentaje de destinatarios de un email o anuncio que hacen clic sobre el total de los que lo recibieron. `CTR = clicks / impresiones`. Es la métrica de engagement más directa en campañas de email marketing.

## 5. Tramos determinísticos

1. **Cálculo de métricas RFM por cliente**: para cada `customer_id`, calcular `days_since_last_purchase` (R), `total_purchases_count` en período de análisis (F), y `total_spend_usd` en el período (M). Período de análisis: configurable por tenant (por defecto 12 meses).

2. **Quintilización de cada dimensión**: ordenar clientes por R, F, M por separado → asignar quintil 1–5. El quintil se calcula respecto a la distribución del tenant, no con umbrales fijos. Si la base tiene 500 clientes, cada quintil tiene ~100.

3. **Construcción del segmento RFM**: concatenar los tres quintiles → `rfm_score = "RFM-{r}{f}{m}"`. Ejemplo: `"RFM-554"` (alta recencia, alta frecuencia, monetización media-alta).

4. **Agrupación en segmentos de negocio**: mapear los 125 combinaciones posibles a segmentos interpretables. Agrupación estándar:
   - `champions`: R=5, F≥4, M≥4
   - `loyal_customers`: F≥4, M≥3 (independiente de R)
   - `potential_loyalists`: R≥4, F=1-2
   - `at_risk`: R≤2, F≥3 (compraban seguido, dejaron de comprar)
   - `cant_lose_them`: R=1, M=5 (compraban mucho, desaparecieron)
   - `hibernating`: R≤2, F≤2, M≤2
   - `lost`: R=1, F=1, M=1
   Esta agrupación es una regla cerrada — no interviene el LLM.

5. **Métricas del segmento**: por cada segmento, calcular `n_customers`, `total_revenue`, `avg_order_value`, `avg_days_since_purchase`. Permite al equipo de marketing cuantificar el impacto de cada segmento.

## 6. Tramos agénticos

1. **Naming y descripción del segmento en lenguaje de marketing.**
   *Por qué no es regla*: los nombres técnicos (`"RFM-554"` o incluso `"champions"`) no son útiles para el equipo de marketing que diseña la campaña. El modelo lee los datos del segmento (cuántos son, qué compran, cuándo, en qué canal) y genera una descripción usable: «Compradores frecuentes de ropa deportiva, compra mensual, ticket promedio USD 405, prefieren canal online. Son tu base más fiel — el 12% de tus clientes generan el 38% del revenue.» Eso sí lo puede usar el copywriter.

2. **Brief creativo por segmento.**
   *Por qué no es regla*: el brief tiene que proponer un ángulo de comunicación específico para el segmento, con tono, oferta y llamada a la acción apropiados. Para `champions`, el ángulo es exclusividad (acceso anticipado, producto nuevo antes que nadie), no un descuento. Para `at_risk`, el ángulo es recuperación (recordarles lo que amaban, ofrecer algo que les haga volver). Para `lost`, el ángulo es un descuento agresivo o simplemente no gastar presupuesto en ellos. Una regla no produce esos briefs — el modelo razona sobre el perfil del segmento y el estilo de la marca.

3. **Propuesta de canal y frecuencia por segmento.**
   *Por qué no es regla*: el canal óptimo depende del comportamiento del segmento. Si los `champions` tienen open rate de email de 55% y click rate de 18%, el email es el canal correcto. Si los `at_risk` tienen open rate < 10% pero abren WhatsApp, el brief propone un mensaje de WhatsApp. El modelo lee las métricas de engagement por canal por segmento.

> [!cuidado]
> El agente genera briefs, no copy final. El equipo de marketing siempre revisa y aprueba antes de lanzar. En particular, las ofertas económicas (descuentos, promociones) requieren aprobación del responsable comercial.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_customers] → histórico de transacciones + datos de email (determinístico)
  ↓
[compute_rfm] → métricas R, F, M por cliente (determinístico)
  ↓
[quintilize] → asignar quintil 1-5 por dimensión (determinístico)
  ↓
[assign_segments] → mapear rfm_score a segmento de negocio (determinístico)
  ↓
[compute_segment_metrics] → n, revenue, AOV, engagement por segmento (determinístico)
  ↓
[describe_segments] → LLM genera nombre y descripción usable por marketing (agéntico)
  ↓
[generate_briefs] → LLM redacta brief creativo + canal + frecuencia por segmento (agéntico)
  ↓
[human_review?] → interrupt_before si brief incluye descuento > threshold del tenant
  ↓
[write_report] → PDF con mapa de segmentos + briefs por segmento (determinístico)
  ↓
END
```

### Activities Temporal (job mensual o ad-hoc)

- `pull_transaction_history(tenant, period)` — histórico de compras del período.
- `run_segmentation_agent(tenant, snapshot_id)` — ejecuta el grafo.
- `deliver_segmentation_report(tenant, period, payload)` — reporte al equipo de marketing.
  `idempotency_key = "segmentation:{tenant}:{period}"`

### Tools necesarias

- `fetch_csv` — exportación de transacciones del POS o e-commerce.
- `fetch_excel` — si la base de clientes está en Google Sheets.
- `sql_query` — si las transacciones están en la DB del tenant.
- `write_report` — PDF con mapa de segmentos + briefs.
- `send_email` — reporte al gerente de marketing.

## 8. Salida y entrega

### Reporte mensual de segmentación (PDF)

```
SEGMENTACIÓN RFM — TiendaBox Retail — Mayo 2026

BASE: 22 400 clientes activos en los últimos 12 meses.

MAPA DE SEGMENTOS:

Champions (2 800 clientes — 12% de base — 38% del revenue)
"Compradores frecuentes de ropa deportiva y accesorios. Compra cada 3-4 semanas,
ticket USD 405 promedio, prefieren online. Los conocen bien: han comprado 9 veces
en promedio. Si los descuidas, se van a la competencia."
Brief: Lanza el catálogo de invierno a este segmento 48h antes del lanzamiento público.
Asunto: "Primero tú — el catálogo de invierno llegó." Sin descuento.
Canal: Email. Frecuencia: 1 vez. CTA: "Ver colección exclusiva".

En riesgo (3 100 clientes — 14% de base — 19% del revenue)
"Compraban mensual hace 4-6 meses. Llevan 75 días sin comprar. Ticket alto (USD 380).
No está claro si encontraron alternativa o simplemente olvidaron."
Brief: Campaña de recuperación. Recordarles su última compra + oferta de tiempo
limitado. Urgencia sin ser agresivo.
Asunto: "Hace tiempo que no te vemos — ¿qué tal esto?"
Descuento propuesto: 15% en categoría de su última compra.
⚠ Descuento requiere aprobación de gerencia antes de activar.
Canal: Email + WhatsApp si tienen opt-in. Frecuencia: 2 mensajes en 10 días.

[Continúan los otros 5 segmentos...]

PRIORIDAD DE ACTIVACIÓN SUGERIDA:
1. Champions (alto impacto, sin costo de descuento)
2. En riesgo (recuperación urgente antes de que se pierdan)
3. Potential loyalists (convertir compradores nuevos en recurrentes)
```

**Canal**: PDF + Sheets con la lista de clientes por segmento (para import a Klaviyo/Mailchimp). El equipo de marketing importa los segmentos y lanza las campañas.

## 9. Cómo se vende

**Gancho**: «Tienes 22 000 clientes y les mandas el mismo email a todos. Este agente los divide en 7 grupos con estrategias distintas, y te escribe el brief de cada campaña. Tu equipo solo ejecuta.»

**Propuesta de valor**: pasar de «campañas a todos» a «campañas de precisión» sin contratar un analista de datos. El brief agéntico es lo que le ahorra más tiempo al equipo.

| Tier | Qué incluye | Precio orientativo |
|---|---|---|
| Básico | Segmentación RFM + métricas por segmento (sin briefs) | 150–250 USD/mes |
| Estándar | Segmentación + descripción de segmentos + briefs por segmento | 400–700 USD/mes |
| Premium | Todo + actualización mensual automática + integración directa Klaviyo/Mailchimp API | 700–1 400 USD/mes + setup 2–5 k USD |

Setup: 2–4 semanas. Incluye: extracción del historial de transacciones (mínimo 12 meses), definición del mapping de segmentos con el equipo de marketing, golden set de 3 segmentos para validar los briefs agénticos.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Historial de transacciones incompleto**: si los clientes compran en físico y online pero no hay un ID unificado, los cálculos RFM están sesgados. | El agente detecta y reporta `% clientes con historial < 3 compras`. Si > 60%, advierte que la segmentación no es confiable para esos clientes. |
| **Brief inapropiado para el segmento**: el modelo propone un descuento agresivo a los champions (que no lo necesitan). | El brief incluye la justificación del ángulo propuesto. El equipo de marketing valida antes de activar. Descuentos > umbral siempre pasan por `interrupt_before`. |
| **PII en la base de clientes**: emails, nombres, historial de compras. | La base de clientes nunca sale del entorno del tenant. Los briefs se generan con datos agregados del segmento, no con datos individuales. |
| **Deriva del segmento**: los quintiles se recalculan con los datos disponibles. Si hay muchos clientes nuevos, la distribución cambia y un «champion» del mes pasado puede caer de segmento. | El reporte muestra la evolución del segmento respecto al período anterior. Movimientos > 15% se destacan como anomalía. |
| **Recomendación de canal inviable**: el modelo propone WhatsApp si los clientes no tienen opt-in de WhatsApp Business. | El agente verifica la disponibilidad de canal por segmento antes de proponerlo. Si no hay opt-in de WhatsApp, no lo incluye en el brief. |

> [!cuidado]
> **Fallback humano**: si la base de clientes tiene < 200 registros con historial suficiente para calcular RFM confiable, el agente entrega la segmentación básica (solo R: activos vs inactivos) y recomienda que el equipo de marketing valide manualmente los segmentos antes de activar campañas. No genera briefs con datos insuficientes.

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 5 000–100 000 clientes, historial de compras en e-commerce o POS, datos de email engagement en Klaviyo/Mailchimp. Compras recurrentes (moda, consumibles, electrónica).

**Delta determinístico**: además del RFM estándar, calcular `category_affinity` (qué categorías compra cada segmento) para personalizar el brief a nivel de producto. El `champions` de TiendaBox que compra ropa deportiva recibe un brief diferente al `champion` que compra electrónica.

**Delta agéntico**: el modelo incluye en el brief la propuesta de producto específica para el segmento, no solo el ángulo de comunicación. «Champions de ropa deportiva: lanzar la nueva colección de running» vs «Champions de electrónica: acceso anticipado al nuevo modelo de auriculares».

**Regulación**: GDPR/Ley de protección de datos local (Ley 1581 en Colombia, LFPDPPP en México). La base de emails debe tener opt-in explícito. El agente verifica que el segmento solo incluya clientes con opt-in válido antes de generar el brief.

**Precio orientativo**: 500–1 000 USD/mes.

### Instancia 2 — Hospitalidad (`mesonurbano`)

**Datos típicos**: 500–5 000 clientes en base de email/WhatsApp, historial de reservas o visitas (frecuencia, día de semana, tipo de ocasión si se registra). Compras no siempre trackeable si la caja no tiene CRM.

**Delta determinístico**: en hospitalidad, la dimensión más relevante del RFM es F (frecuencia). Un cliente que viene 3 veces por semana (habitual de almuerzo) es fundamentalmente diferente al que viene 3 veces al año (cumpleaños). Añadir dimensión `visit_pattern` (diurno regular, fin de semana, evento especial) como cuarta dimensión del segmento.

**Delta agéntico**: el brief para el segmento «habitual de almuerzo» propone un programa de fidelización o una oferta de happy hour entre semana — no un descuento genérico. Para el segmento «visita en fechas especiales», propone un recordatorio personalizado antes del cumpleaños con oferta de reserva para grupo.

**Regulación**: datos de comportamiento de consumo (qué piden, cuánto gastan) son sensibles. No compartir con terceros. Solo uso interno para personalización.

**Precio orientativo**: 200–400 USD/mes (base de clientes más pequeña, menor complejidad).

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de ese módulo |
|---|---|
| **A06** — Clases, dataclasses | `CustomerRFM`, `Segment`, `CampaignBrief` como dataclasses. El pipeline de segmentación es composicional: RFM → quintilización → mapping → brief. |
| **B02** — FastAPI a profundidad | Endpoint para upload del CSV de transacciones del POS. El equipo de marketing lo sube desde el navegador, Pydantic valida el formato antes de procesar. |
| **C01** — SQLAlchemy async | `customer_segment_repo` persiste el segmento asignado por `(tenant, customer_id, period)`. Evolución histórica del segmento = métrica de calidad de la base. |
| **D04** — Observabilidad | Phoenix traza `describe_segments` y `generate_briefs`. Medir latencia total del agente (la segmentación determinística debería ser < 5s; el LLM es donde va el tiempo). |
| **E01** — Anthropic SDK | Prompt caching del system prompt con la definición de segmentos del tenant + brand guidelines + historial de campañas pasadas. Los datos del segmento son dinámicos. |

## 13. Errores típicos

**1. Briefs generados con datos de clientes individuales en el prompt.**
*Síntoma*: el brief del segmento `champions` incluye frases como «como María Rodríguez, que compró 9 veces este año...»; hay PII de un cliente real en un documento de marketing.
*Causa raíz*: el nodo `generate_briefs` recibió el listado de clientes del segmento en lugar de las métricas agregadas.
*Cómo evitarlo*: el nodo solo recibe datos del segmento como grupo: `n_customers`, `avg_order_value`, `avg_days_since_purchase`, `top_category`. Nunca recibe `customer_id`, `email` ni `name` individuales.

**2. Quintilización con distribución sesgada que rompe los segmentos.**
*Síntoma*: el 70% de la base cae en el quintil R=1 porque hay un pico de clientes que no compran hace más de 180 días; el segmento `champions` queda casi vacío y el brief pierde relevancia.
*Causa raíz*: la quintilización asigna el 20% de clientes a cada quintil, pero si la distribución es bimodal (muchos activos + muchos inactivos), los quintiles intermedios capturan patrones mixtos.
*Cómo evitarlo*: antes de quintilizar, el agente reporta la distribución de cada dimensión. Si el coeficiente de variación de R es > 1.5, advierte que la segmentación puede estar sesgada y sugiere revisar el período de análisis.

**3. Brief enviado sin verificar opt-in del segmento.**
*Síntoma*: el equipo de marketing activa la campaña para el segmento `at_risk` de 3 100 clientes; 400 de ellos no tienen opt-in de email válido y la herramienta de envío los incluye de todas formas.
*Causa raíz*: el nodo `generate_briefs` no verifica la disponibilidad de canal por cliente antes de proponer el canal de envío.
*Cómo evitarlo*: el reporte de segmentación incluye `n_with_email_optin` y `n_with_whatsapp_optin` por segmento. El brief solo propone el canal para los clientes con opt-in válido. El Sheets de exportación de clientes excluye los sin opt-in por defecto.

**4. Riesgo legal por contenido auto-publicado sin review.**
*Síntoma*: el brief incluye un descuento del 20% para el segmento `at_risk`; el sistema lo convierte automáticamente en un email enviado sin que gerencia apruebe la oferta.
*Causa raíz*: el flujo no tiene `interrupt_before` configurado para briefs con descuentos, o el threshold está definido incorrectamente.
*Cómo evitarlo*: cualquier brief que proponga una oferta económica (descuento, cupón, regalo) requiere aprobación explícita del responsable comercial antes de activarse. El sistema registra `approved_by` y el monto de la oferta en el log de cada campaña ejecutada.

**5. Segmento `lost` recibiendo campañas de alto costo.**
*Síntoma*: el agente genera briefs para todos los segmentos incluyendo `lost` (R=1, F=1, M=1), y el equipo lanza una campaña de WhatsApp a 2 000 clientes perdidos con costo variable por mensaje.
*Causa raíz*: no hay lógica que filtre la conveniencia económica de activar ciertos segmentos.
*Cómo evitarlo*: el brief para el segmento `lost` incluye por defecto la recomendación `[evaluar ROI antes de activar — costo de campaña puede superar LTV esperado]`. El PM decide si activar con ese aviso visible.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la quintilización RFM con el ejemplo de TiendaBox — ¿por qué usamos quintiles relativos al tenant en lugar de umbrales fijos como "compró en los últimos 30 días"?»
2. **Aplícalo a mi caso**: «Mi cliente tiene una base de clientes donde el 60% compró una sola vez hace más de un año. ¿Cómo adapto la segmentación RFM para que los segmentos sean accionables con esa distribución?»
3. **Por qué falló**: «El agente generó un brief de WhatsApp para un segmento, pero la herramienta de envío rechazó la lista porque los clientes no tenían opt-in. ¿En qué nodo del workflow debería haberse detectado eso?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Implementar el cálculo de métricas RFM y la quintilización relativa al tenant en Python o SQL.
- Diseñar el mapping de 125 combinaciones RFM a segmentos de negocio como regla cerrada.
- Construir los nodos agénticos de descripción de segmento y brief creativo con datos solo agregados, sin PII individual.
- Configurar el `interrupt_before` para briefs con ofertas económicas y verificar opt-in antes de proponer canal de envío.
- Cotizar y dimensionar el servicio para retail y hospitalidad LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué leerlo antes |
|--------|---------------------|
| **A06** — Clases y dataclasses | `CustomerRFM`, `Segment` y `CampaignBrief` como dataclasses; la composición RFM → quintil → segmento → brief es el ejemplo central de pipelines tipados. |
| **C01** — SQLAlchemy async | El repositorio `customer_segment_repo` persiste el segmento por `(tenant, customer_id, period)`; entender la capa de acceso a datos evita mezclar datos de tenants. |
| **D04** — Observabilidad | Medir latencia de `describe_segments` y `generate_briefs` separado del pipeline determinístico; detectar si el modelo empieza a proponer los mismos ángulos de brief para todos los segmentos. |
| **E01** — Anthropic SDK | El prompt caching del system prompt con definición de segmentos y brand guidelines del tenant es el patrón que hace que el brief suene a la marca y no a cualquier marca. |
