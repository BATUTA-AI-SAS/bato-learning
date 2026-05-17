---
ext_id: F-VTA-03
slug: pipeline-en-riesgo
track: F
dept: VTA
ord: 3
title: "Análisis de pipeline en riesgo y próximas acciones"
summary: "Agente que detecta deals estancados, clasifica la señal real (pausa temporal vs deal muerto) y genera una próxima acción accionable."
related_modules: [B02, C01, D04, E01, E03]
industries_instanced: [serv-prof, construccion]
tenants_in_examples: [consultorabc, andina]
big_corp_vendors: [Clari, Gong, Outreach]
latam_tools: [hubspot, pipedrive]
key_concepts: [deal-velocity, last-touch, multithreading, escalation, riesgo-pipeline, fallback-humano]
estimated_minutes: 45
deterministic_share: 0.3
version: 1
---

## 1. Problema operativo

La directora comercial de Consultora ABC tiene un problema que no es falta de leads: es que no sabe cuáles de sus deals activos están realmente vivos. Hay doce deals en etapa «propuesta enviada» que llevan más de 30 días sin actividad. Algunos son clientes que dijeron «nos llamamos en dos semanas» y nunca llamaron. Otros son clientes que firmaron NDA y están en proceso de aprobación interna. Son situaciones completamente distintas que exigen respuestas distintas, pero en el CRM se ven idénticos.

En Andina Constructora el problema escala: algunos deals representan 200 k USD en licitaciones con fechas duras. Perder la ventana de seguimiento en un deal así no es una oportunidad perdida — es un trimestre perdido.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|---|---|---|
| **Clari** | Analiza señales de CRM + emails + calls para identificar deals en riesgo. Dashboards de «pipeline health» en tiempo real. | 100–125 USD/user/mes |
| **Gong** | Conversational intelligence: transcribe y analiza calls de ventas; detecta señales de riesgo en el lenguaje del cliente (objeciones de precio, mención de competidores, falta de urgencia). | 1 200–1 600 USD/user/año + platform fee 5k–50k USD |
| **Outreach** | Sales engagement + Kaia (AI): graba calls, genera transcripts, detecta buying signals y flags de riesgo. Pipeline analytics con forecasting integrado. | Precios no públicos; estimado 100–150 USD/user/mes |

Estas plataformas necesitan que los vendedores tengan sus emails y calendarios conectados, que todas las calls se graben y procesen, y que el CRM esté limpio. Meses de implementación. Un equipo de RevOps para mantenerlo.

## 3. PYME LATAM realista

En Consultora ABC, Gong no existe. Las llamadas de ventas suceden en Zoom o en Google Meet, sin grabar. Los emails van por Gmail sin integración completa al CRM. WhatsApp es el canal donde realmente pasan las negociaciones críticas. El CRM (Pipedrive o HubSpot Starter) tiene notas cuando el vendedor se acuerda de escribirlas, que es el 40% de las veces.

Lo que sí existe: el historial de etapas, las fechas de última actividad, y —si el equipo tiene algún hábito— notas cortas después de cada llamada. Con eso trabaja este agente.

## 4. Datos típicos

| Campo | Fuente | Frecuencia | Ejemplo de fila |
|---|---|---|---|
| `deal_id` | CRM | por deal | `"DEAL-5102"` |
| `company_name` | CRM | por deal | `"Constructora Andina S.A."` |
| `stage` | CRM | tiempo real | `"propuesta enviada"` |
| `days_in_current_stage` | calculado | diario | `31` |
| `last_activity_date` | CRM | tiempo real | `"2026-04-14"` |
| `days_since_last_activity` | calculado | diario | `32` |
| `num_contacts_in_account` | CRM | por deal | `2` (threading coverage) |
| `deal_value_usd` | CRM | por deal | `180000` |
| `close_date_expected` | CRM | por deal | `"2026-06-15"` |
| `days_to_close` | calculado | diario | `30` |
| `notes_history` | CRM | batch diario | Array de notas con fecha |
| `email_last_sent` | CRM / Gmail | batch diario | `"2026-04-12: Adjuntamos propuesta técnica..."` |
| `email_last_received` | CRM / Gmail | batch diario | `"2026-04-09: Gracias, lo revisamos y les confirmamos"` |

**Threading**: número de personas distintas con las que el equipo ha tenido contacto en la cuenta. Un deal donde solo se habla con una persona es de mayor riesgo — si esa persona sale, el deal muere.

## 5. Tramos determinísticos

1. **Umbral de inactividad por etapa**: cada etapa tiene un umbral de «días sin actividad» configurado por el tenant. Ejemplos: `discovery: 7 días`, `demo: 10 días`, `proposal: 21 días`, `negotiation: 14 días`. Si `days_since_last_activity > threshold[stage]`, el deal se marca `at_risk_inactivity`.

2. **Ratio de velocidad vs benchmark**: calcular `days_in_current_stage / median_days_in_stage_historical`. Si este ratio > 1.5, el deal va más lento que la media histórica del tenant. Flag `velocity_anomaly`.

3. **Threading score**: `num_contacts_in_account`. Si < 2 y `deal_value > 50 000 USD`, flag `single_threaded_risk`.

4. **Proximity to close date**: si `days_to_close < 30` y stage es `proposal` o anterior → flag `close_date_pressure`. El deal necesita avanzar rápido para cerrar a tiempo.

5. **Clasificación inicial de riesgo**: combinación de flags anteriores → `risk_level: low / medium / high`. Regla: high si tiene 2+ flags o 1 flag con `deal_value > umbral_del_tenant`.

6. **Ordenamiento del reporte**: deals ordenados por `risk_level DESC, days_to_close ASC`. Los más urgentes primero.

## 6. Tramos agénticos

1. **Clasificación de la señal real de estancamiento.**
   *Por qué no es regla*: hay múltiples causas de inactividad con respuestas radicalmente distintas. «El cliente pidió 30 días por proceso de aprobación interna con fecha comprometida» → deal vivo, acción: esperar y confirmar en la fecha acordada. «El cliente no responde desde hace 3 semanas, última nota: precio es alto» → deal probablemente muerto, acción: intento final de rescate o cierre como lost. «Vendedor en vacaciones» → deal pausado, no en riesgo real. Una regla no puede distinguir estos casos leyendo solo campos del CRM.

2. **Generación de próxima acción específica por deal.**
   *Por qué no es regla*: la acción óptima depende del contexto: quién habló último, qué se dijo, cuál es el perfil del contacto, qué otros deals similares cerraron o se perdieron con ese tipo de empresa. El modelo propone una acción concreta («Envía un caso de éxito de una firma del mismo sector — no toques el tema de precio todavía») en lugar de «hacer follow-up».

3. **Detección de cambio de contexto en la cuenta.**
   *Por qué no es regla*: a veces el estancamiento se explica por algo que no está en el CRM: «mencionó en la última llamada que están en proceso de fusión», «el CFO que era nuestro sponsor acaba de renunciar». El modelo extrae esos fragmentos de las notas y los marca como factores de riesgo explicativo.

> [!cuidado]
> Si el agente detecta un deal de alto valor (> umbral configurable) con señal de riesgo alta, el output incluye `requires_escalation: true`. El gerente comercial recibe una alerta separada antes de que el vendedor actúe.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_pipeline] → deals activos del CRM con campos + historial (determinístico)
  ↓
[compute_risk_flags] → umbrales, velocity, threading, close date (determinístico)
  ↓
[filter_at_risk] → deals con risk_level medium o high (determinístico)
  ↓
[read_deal_context] → notas + email history por deal at risk (determinístico: I/O)
  ↓
[classify_stagnation] → LLM clasifica causa real del estancamiento (agéntico)
  ↓
[generate_next_action] → LLM propone acción específica por deal (agéntico)
  ↓
[escalation_check] → si deal_value > threshold AND risk = high → interrupt_before
  ↓
[write_report] → reporte de pipeline at risk con acciones (determinístico)
  ↓
END
```

### Activities Temporal (job diario)

- `pull_at_risk_deals(tenant, date)` — snapshot de deals at_risk.
- `run_pipeline_risk_agent(tenant, snapshot_id)` — ejecuta el grafo.
- `deliver_risk_alert(tenant, date, payload)` — email + Slack al vendedor asignado.
  `idempotency_key = "pipeline-risk:{tenant}:{date}"`

### Tools necesarias

- `sql_query` — deals + actividades desde DB del tenant.
- `fetch_excel` — si el pipeline está en Sheets.
- `send_email` — alerta a vendedor asignado + copia al gerente si escalación.
- `write_report` — PDF semanal de «estado del pipeline».

## 8. Salida y entrega

### Alerta diaria por vendedor (email)

```
PIPELINE EN RIESGO — Consultora ABC — 2026-05-16
Para: Carlos (vendedor)

RIESGO ALTO (actúa hoy):

· DEAL-5102 · Constructora Andina · USD 180 000 · Propuesta enviada · 31 días sin actividad
  Clasificación: Deal vivo pero en pausa por proceso interno.
  Señal: "nos escriben la semana del 20 para confirmar" (nota del 14 de abril).
  Próxima acción: Escríbele hoy a Juan Pedraza: "Hola Juan, queríamos confirmar si
  esta semana podemos avanzar con la propuesta. ¿Tienen novedades del comité?"
  Fecha límite para actuar: antes del 20 de mayo.

· DEAL-5088 · Importadora Norte · USD 45 000 · Demo realizada · 22 días sin actividad
  Clasificación: Señales mixtas. Posible pérdida de interés.
  Señal: última email del cliente fue "gracias, lo revisamos", sin fecha comprometida.
  Próxima acción: Intenta una última llamada. Si no responde en 48h, cierra como lost
  y libera el tiempo del pipeline.
  ⚠ Si el deal se pierde, notifica al gerente para activar pipeline de reserva.

RIESGO MEDIO (monitorea esta semana):
· DEAL-5071 · Grupo Sur · USD 28 000 · Negotiation · 10 días sin actividad
  [ver detalle en reporte completo]
```

**Canal**: email individual a cada vendedor + resumen ejecutivo semanal al gerente comercial en Slack.

## 9. Cómo se vende

**Gancho**: «Tu equipo no sabe cuáles deals están vivos y cuáles son muertos ambulantes. Este agente los distingue leyendo las notas, no solo los campos del CRM, y dice exactamente qué hacer con cada uno.»

**Propuesta de valor**: elimina el tiempo que el vendedor pasa revisando su pipeline manualmente. Cada mañana tiene una lista priorizada con acciones concretas.

| Tier | Qué incluye | Precio orientativo |
|---|---|---|
| Básico | Flags determinísticos + ranking de riesgo | 100–200 USD/mes |
| Estándar | Clasificación de señal + próxima acción agéntica + alerta diaria | 350–600 USD/mes |
| Premium | Todo + detección de contexto de cuenta + escalación automática a gerente | 600–1 200 USD/mes + setup 2–5 k USD |

Setup: 2–4 semanas. Incluye: definición de umbrales de inactividad por etapa, calibración con historial de deals perdidos, conexión al CRM (API o exportación), golden set de 15 deals para validar clasificación de señal.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Clasificación errónea**: el modelo dice «deal muerto» en un deal que estaba en pausa real. | El vendedor siempre valida antes de marcar como lost. El agente recomienda, no ejecuta. |
| **Fatiga de alertas**: si todos los días llegan 15 deals «en riesgo», el vendedor ignora el email. | Umbral configurable: solo enviar alerta si `deals_at_high_risk >= 1` o cambio respecto al día anterior. |
| **Notas vacías**: sin notas, el agente no puede clasificar la señal y solo entrega los flags determinísticos. | Cuando no hay notas, el agente lo dice explícito: `clasificación = desconocida — requiere input del vendedor`. No inventa. |
| **PII**: nombres de contactos y contenido de notas son datos de negocio sensibles. | Procesamiento solo en el entorno del tenant. Las notas no se logean fuera del sistema. |
| **Dependencia del CRM**: si el vendedor no actualiza el CRM, el agente trabaja con datos viejos. | El agente reporta `% deals sin nota en los últimos 7 días`. Umbral: > 40% → aviso al gerente. |

> [!cuidado]
> **Fallback humano**: si el agente no puede clasificar la señal de un deal (notas vacías, error de API, contexto ambiguo), marca el deal como `clasificación = requiere revisión manual` y lo pone primero en la lista del vendedor. Nunca asigna una clasificación ficticia.

## 11. Variantes por industria

### Instancia 1 — Servicios profesionales (`consultorabc`)

**Datos típicos**: 40–100 deals activos, ticket USD 15 000–150 000. Las notas son relativamente ricas (consultores documentan reuniones). Las negociaciones son largas porque involucran aprobación de múltiples stakeholders.

**Delta determinístico**: el threading score es crítico aquí. Deals single-threaded (solo hablan con el CFO) tienen alto riesgo si el CFO cambia de rol. Umbral de alerta: `num_contacts < 2` y `deal_value > 30 000 USD`.

**Delta agéntico**: el modelo detecta en las notas si el interlocutor principal es el decisor o un intermediario. La acción varía: si es intermediario, next-action es «solicitar reunión con el decisor final».

**Regulación**: contratos de confidencialidad. Las notas pueden contener información sujeta a NDA. Solo tráfico interno.

**Precio orientativo**: 400–700 USD/mes.

### Instancia 2 — Real estate / Construcción (`andina`)

**Datos típicos**: 20–60 deals activos (licitaciones + proyectos directos), ticket USD 80 000–500 000. Las licitaciones tienen fechas duras (plazo de presentación de propuesta). Los proyectos directos tienen ciclos largos (6–18 meses).

**Delta determinístico**: para licitaciones, el flag `close_date_pressure` tiene un umbral más agresivo: si `days_to_close < 15` y el deal está en etapa `propuesta`, se genera una alerta crítica (no solo medium). El costo de perder la ventana es irrecuperable.

**Delta agéntico**: el modelo diferencia entre inactividad en un proyecto directo (normal en ciclos largos) e inactividad en una licitación (señal de alarma). El mismo dato (`days_since_last_activity = 30`) tiene significados distintos en cada contexto.

**Regulación**: en licitaciones públicas (SECOP/CompraNet), el contacto con funcionarios durante el proceso puede estar restringido. El agente flagea deals de licitación pública en período de evaluación para no generar acciones de contacto inapropiadas.

**Precio orientativo**: 500–1 000 USD/mes + setup 3–6 k USD.

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de ese módulo |
|---|---|
| **B02** — FastAPI a profundidad | Webhook del CRM que dispara el job de risk analysis al crear/actualizar un deal. Validación del payload con Pydantic. |
| **C01** — SQLAlchemy async | `pipeline_risk_repo` persiste el snapshot de deals at_risk por `(tenant, date)`. Historial de clasificaciones para medir accuracy del agente. |
| **D04** — Observabilidad | Phoenix traza las llamadas a `classify_stagnation` y `generate_next_action`. Detectar si el modelo clasifica siempre «vivo» o siempre «muerto» (sesgo de calibración). |
| **E01** — Anthropic SDK | Prompt caching: el system prompt con las reglas del tenant (umbrales, lista de industrias objetivo, perfil del equipo) es cacheable. El contexto del deal es dinámico. |
| **E03** — Skills y AGENTS.md | El skill `pipeline_risk_analyst` tiene slots: `inactivity_thresholds_by_stage`, `escalation_threshold_usd`, `vendor_profile_notes` (descripción del estilo de cada vendedor). |

## 13. Errores típicos

**1. Sobre-confianza en la clasificación de señal sin notas del CRM.**
*Síntoma*: el agente clasifica como «deal vivo en pausa» un deal que en realidad está muerto, basándose en el nombre de la empresa y en el valor del ticket, no en evidencia textual.
*Causa raíz*: el nodo `classify_stagnation` recibió campos del CRM pero no notas; el modelo llenó el vacío con inferencias plausibles.
*Cómo evitarlo*: cuando no hay notas, el agente devuelve `clasificación = desconocida — requiere input del vendedor` y lo pone primero en la lista. El nodo nunca clasifica sin evidencia textual explícita.

**2. Scoring fugado al futuro en la calibración de umbrales de inactividad.**
*Síntoma*: los umbrales de `days_since_last_activity` por etapa se calcularon usando el historial completo de deals, incluidos los que ya cerraron o se perdieron. El modelo aprendió que deals que cerraron en `proposal` tardaban 15 días; en producción, los deals en curso tienen patrones distintos.
*Causa raíz*: al calibrar los umbrales con el historial, se usó la fecha de cierre como punto de corte en lugar de la fecha de la última actividad real antes del cierre.
*Cómo evitarlo*: calibrar los umbrales con el `p75 de days_in_stage` calculado exclusivamente desde deals completamente cerrados, usando solo la actividad registrada antes del evento de cierre o pérdida. Nunca usar datos post-evento para calibrar señales pre-evento.

**3. Fatiga de alertas por umbral demasiado sensible.**
*Síntoma*: el vendedor recibe 20 deals «en riesgo alto» cada mañana; los ignora todos porque no puede procesar tanta información.
*Causa raíz*: los umbrales de inactividad por etapa son demasiado bajos y el pipeline no filtra cambios respecto al día anterior.
*Cómo evitarlo*: el digest solo envía alerta si `deals_at_high_risk >= 1` y hubo un cambio respecto al día anterior; incluir un contador semanal («esta semana subieron 3 deals a riesgo alto») para dar contexto sin generar ruido diario.

**4. Escalación de un deal de alto valor al gerente sin contexto suficiente.**
*Síntoma*: el gerente recibe una alerta de escalación sobre un deal de 200 k USD, pero el mensaje no incluye el contexto del deal ni la acción recomendada; el gerente no sabe qué hacer.
*Causa raíz*: el nodo de escalación envía el flag sin el output completo del agente.
*Cómo evitarlo*: la alerta de escalación incluye siempre: clasificación de la señal, evidencia textual, próxima acción específica, y plazo sugerido.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «¿Por qué el mismo dato `days_since_last_activity = 30` puede indicar riesgo alto en un deal de servicios profesionales y ser normal en un deal de construcción? ¿Cómo lo modela el agente?»
2. **Aplícalo a mi caso**: «¿Cómo adaptaría el pipeline si el equipo de ventas tiene el hábito de escribir notas en WhatsApp en lugar de en el CRM? ¿Qué cambia en el flujo de ingesta?»
3. **Por qué falló**: «El agente clasificó como 'deal muerto' un deal que el vendedor sabía que estaba en pausa por proceso interno. ¿Cómo mejoro la calibración del golden set para evitar este error?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de análisis de pipeline en riesgo con flags determinísticos (inactividad, velocity, threading) y clasificación agéntica de la señal real.
- Calibrar los umbrales de inactividad por etapa usando datos históricos sin data leakage (solo actividad pre-evento de cierre).
- Implementar el fallback `clasificación = desconocida` cuando no hay notas, sin inventar una clasificación.
- Configurar la escalación automática para deals de alto valor con contexto completo en el mensaje al gerente.
- Dimensionar y cotizar este servicio para servicios profesionales y para construcción con licitaciones de fechas duras.

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|--------------------------------|
| **E04** — Memoria de sesión por SDR/cuenta | El historial de notas y actividades por cuenta es la base de la clasificación de señal; sin entender cómo se persiste la sesión por `deal_id`, el agente no puede diferenciar el patrón actual del patrón histórico de esa cuenta. |
| **C01** — SQLAlchemy async | El `pipeline_risk_repo` persiste el snapshot de deals at_risk por `(tenant, date)` para medir accuracy histórica del agente; entender el repositorio async es prerequisito. |
| **E03** — Skills por tenant | El skill `pipeline_risk_analyst` tiene slots de umbrales por etapa y perfil de vendedor; sin este módulo no se entiende cómo los umbrales varían entre Consultora ABC y Andina sin cambiar código. |
| **D04** — Observabilidad | Detectar si el modelo clasifica siempre «vivo» o siempre «muerto» (sesgo de calibración) requiere monitoreo en Phoenix de la distribución de clasificaciones a lo largo del tiempo. |
