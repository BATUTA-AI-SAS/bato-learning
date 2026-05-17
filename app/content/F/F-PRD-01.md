---
ext_id: F-PRD-01
slug: feedback-priorizacion
track: F
dept: PRD
ord: 280
title: "Análisis de feedback (tickets, reseñas, NPS) y priorización"
summary: "Agente que consolida feedback de múltiples canales, agrupa por tema, calcula señales de valor y frecuencia, y produce un backlog priorizado con justificación para el PM."
estimated_minutes: 45
industries_instanced: [retail, serv-prof]
tenants_in_examples: [tiendabox, consultorabc]
---

## 1. Problema operativo

La PM de TiendaBox Retail recibe feedback disperso en cuatro lugares: tickets de Intercom, reseñas en Google Play y App Store, respuestas a NPS trimestrales, y mensajes directos en WhatsApp Business. Suma 300–800 piezas de feedback al mes. No tiene tiempo de leerlas todas, pero tampoco puede ignorarlas: el competidor lanzó el mes pasado una feature que sus usuarios llevan 6 meses pidiendo.

Consultora ABC tiene un problema parecido pero más pequeño: 40–80 tickets/mes en Linear, comentarios en Notion de sus 15 clientes, y una encuesta mensual de satisfacción. El problema no es el volumen — es que no saben qué pesa más cuando priorizan el sprint.

El agente no toma decisiones de producto. Estructura la conversación para que el PM pueda tomarlas.

---

## 2. Hoy en big corps

Los equipos de producto con > 5 PMs y presupuesto propio usan plataformas de product intelligence.

| Vendor | Capacidad | Precio orientativo |
|--------|-----------|-------------------|
| **Productboard Spark** (enero 2026) | Agente IA que genera PRDs, sintetiza feedback, conecta con Amplitude y Linear vía MCP | ~25 USD/usuario/mes (Maker), hasta 100/usuario/mes (Enterprise) |
| **Pendo (Leo AI)** | Feedback in-app + usage analytics + AI para insights; ganó 2026 Fast Company Most Innovative | Desde ~2 000 USD/mes (Growth); Enterprise cotización |
| **Amplitude AI Feedback** (febrero 2026) | Conecta feedback cualitativo con comportamiento cuantitativo; identifica oportunidades desde analytics | Desde ~1 200 USD/mes (Plus) |
| **Aha! AI** | Roadmap + ideas + feedback con scoring automático de RICE | 59–149 USD/usuario/mes |

Una PYME con 2 PMs no justifica Pendo Enterprise. Productboard starter está en el límite (25 USD/usuario/mes) pero no tiene el agente de IA en ese tier.

---

## 3. PYME LATAM realista

TiendaBox y Consultora ABC trabajan con:
- **Linear Starter** (gratuito hasta 250 MB) para issues y feedback técnico.
- **Notion** para backlogs y roadmaps curados manualmente.
- **Google Play Console / App Store Connect**: reseñas leídas manualmente por la PM.
- **Intercom** (plan Starter, ~39 USD/mes): tickets de soporte y conversaciones.
- **SurveyMonkey / Typeform** para NPS ocasionales.
- **WhatsApp Business**: canal informal pero de alto volumen.

El ERP (Siigo, World Office, Alegra) no tiene modulo de feedback de producto. El PM vive entre tabs.

---

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Intercom tickets | JSON vía API | Continuo | 50–300/mes |
| App Store / Play Store | JSON vía API pública | Diario | 20–200 reseñas/mes |
| NPS survey (Typeform) | CSV / webhook | Mensual o trimestral | 10–100 respuestas |
| Linear issues con tag `feedback` | JSON vía API | Continuo | 20–80/mes |
| WhatsApp (si se integra) | Texto libre, export manual | Semanal | Variable |

Ejemplo de registro unificado:
```json
{
  "source": "intercom",
  "tenant_id": "tiendabox",
  "raw_text": "No puedo ver el historial de pedidos de más de 30 días. Necesito ver los de enero.",
  "user_segment": "vendedor_marketplace",
  "date": "2026-05-10",
  "sentiment_score": -0.6,
  "channel": "support_ticket"
}
```

---

## 5. Tramos determinísticos

1. **Ingesta y normalización**: pull de cada fuente vía API o webhook. Normalizar a esquema unificado: `{source, raw_text, date, user_id, user_segment, tenant_id}`.
2. **Deduplicación**: hash de texto normalizado. Si el mismo usuario reportó lo mismo en dos canales, contar como 1 instancia del problema.
3. **Clasificación por tipo**: regex + reglas simples para separar `bug_report`, `feature_request`, `complaint`, `praise`. Si el texto menciona "error" o "no funciona" → `bug_report` candidato; si menciona "quisiera" o "sería útil" → `feature_request`. Clasificación inicial, no final.
4. **Agregación por semana/mes**: contar instancias por tipo, tendencia semana a semana, distribución por segmento de usuario.
5. **Scoring RICE parcial** (Reach, Impact, Confidence, Effort): Reach = número de instancias del tema en el período. El resto del RICE es agéntico.

---

## 6. Tramos agénticos

1. **Clustering temático** — el modelo agrupa las piezas de feedback por tema subyacente, independiente del canal o las palabras exactas. "No veo mis pedidos viejos", "quiero el historial completo", "los pedidos de enero no aparecen" → mismo cluster: `historial_pedidos_limitado`. El modelo nombra el cluster con lenguaje de producto, no de usuario.

   *Por qué no es regla*: el mismo problema se describe de formas muy distintas. Un clustering por keyword ("historial") perdería "mis pedidos de enero no aparecen". La equivalencia semántica requiere comprensión, no matching.

2. **Priorización RICE completa** — para cada cluster identificado, el modelo estima: Impact (1–3: bajo/medio/alto, según el tono y urgencia de los comentarios), Confidence (% de certeza de que el problema es real vs. malentendido del usuario), Effort (T-shirt: S/M/L, basado en la descripción técnica del problema si se infiere). Con Reach del paso determinístico, calcula el RICE score orientativo.

   *Por qué no es regla*: Impact y Confidence requieren leer el contexto. Un solo usuario muy enojado que reporta que no puede pagar puede tener más impacto que 50 usuarios que "quisieran" una feature cosmética.

3. **Detección de señal de churn** — el modelo identifica feedback que, aunque sea bajo en volumen, sugiere riesgo de abandono: usuarios que mencionan "voy a cancelar", "me fui a otro sistema", "ya no lo recomiendo". Estos se sacan del análisis normal y se escalan como alerta de retención.

   *Por qué no es regla*: "me fui" puede ser un error de escritura o una metáfora. La distinción requiere leer el contexto completo del mensaje.

4. **Fallback humano**: el modelo marca con `NEEDS_PM_REVIEW` los clusters cuya interpretación es ambigua (feedback contradictorio dentro del mismo cluster, o un problema que podría ser bug o diseño intencional). El PM recibe esos clusters con el feedback original, no solo el resumen.

---

## 7. Blueprint del workflow

```
[SCHEDULE: semanal lunes 08:00 AM]
      |
[FETCH_FEEDBACK]             (determinístico — actividades Temporal por fuente)
  intercom_fetcher | appstore_fetcher | nps_fetcher | linear_fetcher
  → unified_feedback_list
      |
[NORMALIZE + DEDUP]          (determinístico)
  → deduped_feedback_list con reach_count por instancia
      |
[TYPE_CLASSIFY]              (determinístico — regex + rules)
  → bug_report | feature_request | complaint | praise
      |
[CLUSTER_THEMES]             ← agéntico
  LLM: (batch de 50–100 items) → clusters con nombre + miembros
      |
[SCORE_RICE]                 ← agéntico
  LLM: (cluster, reach, feedback_samples) → {impact, confidence, effort, rice_score}
      |
[DETECT_CHURN_SIGNALS]       ← agéntico
  LLM: (full_text per item) → churn_flag: bool
  churn_flag = True → crear alerta de retención separada
      |
[BUILD_BACKLOG_REPORT]       (determinístico — template Jinja2)
  → Notion page OR Linear Epic OR email resumen
```

---

## 8. Salida y entrega

**Reporte semanal de feedback** (Notion page o email):

```
ANÁLISIS DE FEEDBACK — TiendaBox | Semana 20 de 2026

TOP 5 CLUSTERS POR RICE SCORE
┌────────────────────────────────────┬───────┬───────┬───────┬───────┬───────────┐
│ Tema                               │ Reach │Impact │ Conf. │Effort │ RICE Score│
├────────────────────────────────────┼───────┼───────┼───────┼───────┼───────────┤
│ Historial de pedidos > 30 días     │  47   │  3    │  90%  │  M    │   127     │
│ Filtro por estado en búsqueda      │  31   │  2    │  80%  │  S    │    99     │
│ Notificación de envío duplicada    │  28   │  2    │  95%  │  S    │    90     │
│ Exportar reportes a Excel          │  22   │  2    │  70%  │  L    │    21     │
│ Login con Google                   │  18   │  1    │  60%  │  M    │    11     │
└────────────────────────────────────┴───────┴───────┴───────┴───────┴───────────┘

SEÑALES DE CHURN DETECTADAS (2 usuarios esta semana)
  → Escalar a CX para save play

REQUIERE REVISIÓN DEL PM (ambigüedad)
  - "Problema con pagos" — 8 reportes; puede ser bug o configuración del tenant.
```

---

## 9. Cómo se vende

**Gancho**: "¿Cuánto feedback tienes sin leer en Intercom y en Play Store? Este agente te lo procesa el lunes y te dice qué construir esta semana."

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Starter | 2 fuentes, hasta 200 piezas/mes, reporte semanal email | 150–300 USD/mes |
| Profesional | 5 fuentes, hasta 800 piezas/mes, integración Notion/Linear | 400–700 USD/mes |
| SaaS LATAM | Multi-tenant, custom RICE weights por cliente, Slack alerts | 600–1 200 USD/mes |

Setup (configuración de fuentes, calibración de clusters iniciales con el PM, golden set): 800–2 000 USD una vez.

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Clustering incorrecto** (feedback sobre distintos problemas en el mismo cluster) | El PM prioriza una feature mal definida | El reporte siempre incluye 3–5 ejemplos del feedback original por cluster. El PM puede reclasificar. |
| **RICE score sesgado por usuarios vocales** | Un usuario muy activo distorsiona el Reach | Deduplicar por usuario antes de contar Reach. Máximo 3 instancias por usuario en el mismo cluster. |
| **Ignorar feedback de usuario silencioso** (no escribe, pero sí abandona) | Churners no detectados | Complementar con datos de uso (funnel de retención, DAU/WAU) en la ficha F-PRD-04. El feedback textual es solo una señal. |
| **Costo de LLM si el volumen es alto** | Procesar 800 piezas/semana con LLM puede ser caro | Batch clustering: agrupar en lotes de 50; el modelo no lee cada pieza individualmente — lee el batch con few-shot para clustering. Costo estimado < 2 USD/semana para 800 piezas con Sonnet 4.6. |

---

## 11. Variantes por industria

| Delta | Retail / E-commerce (TiendaBox) | Servicios profesionales (Consultora ABC) |
|-------|--------------------------------|------------------------------------------|
| Fuentes principales | App Store, Google Play, Intercom, WhatsApp | Linear, Notion, encuesta mensual de satisfacción |
| Volumen | 300–800 piezas/mes (escala con usuarios) | 40–100 piezas/mes (base de clientes pequeña, feedback más denso) |
| Segmento de usuario | Vendedores marketplace, compradores finales | Directores de proyecto, usuarios del sistema interno |
| Tipo de feedback dominante | Feature requests de UX, bugs de app móvil | Solicitudes de personalización, bugs de integración, pedidos de reporte |
| Señal de churn | "Me voy a Mercado Libre" | "No están entregando lo que prometieron" |
| Peso del RICE | Reach pesa más (muchos usuarios finales) | Impact pesa más (cada cliente vale mucho más en ARR) |
| Precio tier profesional | 500–700 USD/mes | 300–500 USD/mes |

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica |
|--------|-----------|
| **A06** — Type hints y protocolos | `FeedbackItem`, `ClusterResult`, `RICEScore` como dataclasses tipados; `Protocol` para fetchers de distintas fuentes (Intercom, App Store comparten interfaz). |
| **B02** — FastAPI routers y deps | Endpoint `POST /feedback/ingest` para webhooks de Intercom/Typeform; `GET /feedback/report?tenant_id=X&week=20` para el reporte. |
| **C01** — SQLAlchemy y modelos ORM | Modelo `FeedbackItem` con `source`, `raw_text`, `cluster_id`, `tenant_id`; modelo `FeedbackCluster` con `rice_score`. |
| **E01** — Anthropic SDK tool loop | El modelo llama a `get_cluster_samples(cluster_id, n=5)` para leer ejemplos antes de estimar RICE. |

---

## 13. Errores típicos

**1. Clustering que junta bugs distintos como duplicados.**
*Síntoma*: el agente agrupa «no puedo exportar a Excel» y «el PDF de la factura está en blanco» en el mismo cluster `exportacion_documentos`; el PM prioriza una feature que en realidad son dos problemas independientes con soluciones distintas.
*Causa raíz*: el nodo `CLUSTER_THEMES` recibió un batch demasiado grande sin segmentar por tipo previo; el modelo agrupó por categoría superficial en lugar de necesidad subyacente.
*Cómo evitarlo*: el clustering corre por separado para `bug_report` y `feature_request` (salida del nodo `TYPE_CLASSIFY`). No se mezclan tipos en el mismo batch de clustering. Si el cluster resultante tiene ítems de más de un tipo, el modelo lo divide antes de nombrar el cluster.

**2. RICE score sesgado por un usuario muy vocal.**
*Síntoma*: un único usuario reportó el mismo problema 12 veces desde distintos ángulos; el Reach del cluster sube a 15, pero en realidad solo 4 usuarios distintos reportaron el problema.
*Causa raíz*: la deduplicación por hash cubre el texto idéntico, pero no las variaciones del mismo usuario.
*Cómo evitarlo*: la deduplicación aplica un máximo de 3 instancias por `user_id` en el mismo cluster antes de calcular Reach. El reporte muestra `reach_unique_users` separado de `reach_total_reports`.

**3. Señal de churn ignorada porque el volumen es bajo.**
*Síntoma*: 2 usuarios escribieron «me voy a Mercado Libre» en el período; el agente los procesa como feedback normal de baja prioridad por su Reach = 2.
*Causa raíz*: el nodo `DETECT_CHURN_SIGNALS` no está separado del ranking RICE; la señal de churn compite con features de alta frecuencia.
*Cómo evitarlo*: los ítems marcados con `churn_flag: true` salen del análisis RICE normal y van directamente a una sección separada del reporte `SEÑALES DE CHURN` sin importar su Reach. El PM los ve siempre, con el texto original.

**4. Reporte entregado con clusters sin ejemplos de feedback original.**
*Síntoma*: el reporte muestra el cluster `historial_pedidos_limitado` con RICE score 127, pero el PM no puede ver qué dijo la gente exactamente; toma decisiones sobre el nombre del cluster, no sobre la voz del usuario.
*Causa raíz*: el template Jinja2 no incluye los ejemplos de feedback en el output.
*Cómo evitarlo*: cada cluster en el reporte incluye obligatoriamente 3–5 fragmentos de feedback original con `source` y `date`. Sin esos fragmentos, el cluster no se considera finalizado.

**5. Período de análisis incorrecto por error de fecha.**
*Síntoma*: el job del lunes procesa el feedback de las últimas 2 semanas en lugar de la última semana porque el parámetro de fecha no se actualizó correctamente.
*Causa raíz*: el activity `pull_feedback` usa una fecha hardcodeada en lugar de `current_week_start`.
*Cómo evitarlo*: el reporte incluye en el encabezado el período exacto de los datos: `datos_del: 2026-05-10 al 2026-05-16`. Si el período no es 7 días, el reporte muestra una advertencia antes del análisis.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre el clustering agéntico de F-PRD-01 y la deduplicación por hash de F-PRD-02 — ¿cuándo uso cada uno y pueden coexistir en el mismo pipeline?»
2. **Aplícalo a mi caso**: «Mi cliente tiene 80% de su feedback en WhatsApp como texto libre sin estructura. ¿Cómo adapto el pipeline para que el clustering sea útil con esa fuente?»
3. **Por qué falló**: «El agente agrupó un bug crítico de pagos con feature requests de UX en el mismo cluster por su RICE score bajo; el bug quedó sin atención. ¿En qué nodo debería haberse separado?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Construir el pipeline de ingesta y normalización de feedback desde múltiples fuentes (Intercom, App Store, NPS, Linear) con deduplicación por hash y por usuario.
- Implementar el clustering agéntico con batches de 50 ítems y separación por tipo antes de agrupar.
- Diseñar el nodo de scoring RICE con Reach determinístico y estimación agéntica de Impact, Confidence y Effort.
- Separar la señal de churn del ranking RICE para que siempre sea visible en el reporte independientemente del volumen.
- Cotizar y dimensionar el servicio para retail y servicios profesionales LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué leerlo antes |
|--------|---------------------|
| **A06** — Type hints y protocolos | `FeedbackItem`, `ClusterResult` y `RICEScore` como dataclasses; el `Protocol` para fetchers de distintas fuentes es el patrón central para añadir nuevas fuentes sin romper el pipeline. |
| **C01** — SQLAlchemy async | El modelo `FeedbackCluster` con `rice_score` y el índice por `(tenant_id, cluster_id)` usan los patrones de C01; sin la capa de repositorio el pipeline mezcla datos de tenants. |
| **E01** — Anthropic SDK tool loop | El loop de clustering: el modelo llama a `get_cluster_samples(cluster_id, n=5)` para leer ejemplos antes de estimar RICE; E01 enseña ese patrón de tool use con contexto progresivo. |
