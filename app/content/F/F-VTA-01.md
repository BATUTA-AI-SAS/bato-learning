---
ext_id: F-VTA-01
slug: scoring-leads
track: F
dept: VTA
ord: 1
title: "Scoring y priorización de leads desde CRM"
summary: "Agente que combina features estructurados del CRM con lectura de conversaciones para separar leads calientes de ruido."
related_modules: [B02, C01, D04, E01, E03]
industries_instanced: [serv-prof, construccion]
tenants_in_examples: [consultorabc, andina]
big_corp_vendors: [Salesforce Einstein, HubSpot AI, 6sense]
latam_tools: [hubspot-starter, pipedrive, excel]
key_concepts: [BANT, fit-vs-intent, intent-signals, próxima-acción, lead-score, sandbagging]
estimated_minutes: 45
deterministic_share: 0.3
version: 1
---

## 1. Problema operativo

La directora comercial de Consultora ABC tiene 120 leads activos en Pipedrive. Tres vendedores. Nadie sabe a cuál llamar primero. El criterio actual es «el que llegó más reciente» — que es lo mismo que no tener criterio. Cada semana se pierden dos o tres oportunidades calientes porque el vendedor estaba empujando una empresa que nunca iba a comprar.

El CFO de Andina Constructora tiene el mismo problema con un matiz distinto: los leads son obras o licitaciones con ticket de 80–400 k USD. Un solo lead mal priorizado desperdicia diez horas de un gerente técnico.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|---|---|---|
| **Salesforce Einstein Lead Scoring** | Modelo ML sobre campos CRM + historial de actividad; actualiza score automáticamente | 40 000–80 000 USD/año (paquete Sales Cloud Einstein; mínimo 10 seats) |
| **HubSpot Predictive Scoring** | Disponible en Sales Hub Enterprise; en agosto 2025 rediseñó su infraestructura con multi-model support y explicabilidad de señales | 43 200 USD/año (10 seats Enterprise); predictive scoring no disponible en tiers inferiores |
| **6sense** | Intent data de terceros (web, review sites, firmographics) + scoring predictivo; especialidad B2B | 60 000–150 000 USD/año |

La infraestructura de estas plataformas exige: un CRM enterprise limpio, un equipo de RevOps que mantenga el modelo, y meses de datos históricos de conversión para calibrar. Una PYME LATAM no tiene ninguno de los tres.

## 3. PYME LATAM realista

Consultora ABC vive en **Pipedrive** (plan Essential, 14 USD/seat) o en **HubSpot Starter** (18 USD/seat), a veces con un Excel paralelo que el dueño lleva en Google Sheets. Los datos disponibles son:

- Campos del deal: nombre empresa, industria, tamaño estimado (muchas veces vacío), fuente (LinkedIn, referido, web, cold outreach), etapa actual.
- Notas del vendedor: texto libre, actualizado cuando el vendedor se acuerda. Calidad variable.
- Historial de emails: si el cliente usa Gmail + integración HubSpot o Pipedrive, hay threads parciales. Si usa Outlook sin integración, no hay nada.
- WhatsApp: la mayor parte de la conversación real ocurre aquí. Nunca está en el CRM.

Sin data engineer. Sin modelo de propensión entrenado. Sin datos históricos limpios de cierre por segmento.

## 4. Datos típicos

| Campo | Fuente | Frecuencia | Ejemplo de fila |
|---|---|---|---|
| `deal_id` | Pipedrive / HubSpot | por deal | `"DEAL-4820"` |
| `company_name` | CRM | por deal | `"Andina Constructora S.A."` |
| `industry` | CRM (manual) | por deal | `"construcción"` |
| `company_size` | CRM (manual, libre) | por deal | `"mediana"` / `""` (frecuentemente vacío) |
| `deal_value_usd` | CRM | por deal | `95000` |
| `lead_source` | CRM | por deal | `"LinkedIn outreach"` |
| `stage` | CRM | en tiempo real | `"propuesta enviada"` |
| `days_in_stage` | calculado | diario | `12` |
| `last_activity_date` | CRM | en tiempo real | `"2026-05-10"` |
| `notes_raw` | CRM, texto libre | por actividad | `"preguntaron por comparativo vs competidor X, precio parecía ok"` |
| `email_threads` | Gmail / Outlook integration | batch diario | texto de últimos 3 hilos |
| `whatsapp_last_msg` | exportación manual o API Business | batch diario | `"Necesitamos esto antes de fin de mes para presentar al directorio"` |

Volumen típico: 50–300 deals activos. Actualizaciones diarias vía webhook del CRM o pull nocturno con `fetch_excel` / `sql_query`.

## 5. Tramos determinísticos

1. **Ingestión y normalización de campos CRM**: extraer deal fields vía API de Pipedrive/HubSpot o desde un CSV exportado. Mapear a schema interno (`deal_id`, `stage`, `value`, `source`, `days_in_stage`, `last_activity_date`).
2. **Cálculo de fit score (0–100)**: regla explícita por columna — industria en lista objetivo (+20), tamaño empresa conocido (+10), ticket > umbral del tenant (+15), fuente = referido (+15), fuente = cold-outreach (-5). Suma ponderada. Sin LLM.
3. **Señales de actividad fría**: si `days_in_stage > threshold_por_etapa[stage]` → flag `stale`. Si `last_activity_date > 14 días` → flag `no_touch`. Reglas fijas, auditables.
4. **Deduplicación**: si dos deals tienen `company_name` con distancia de Levenshtein < 3 y mismo `deal_value_usd`, se marcan como posibles duplicados para revisión humana.
5. **Ordenamiento inicial**: lista de deals ordenada por `fit_score DESC, days_in_stage ASC`. Esta es la lista que ve el vendedor si no hay análisis agéntico.

## 6. Tramos agénticos

1. **Lectura de notas + emails + WhatsApp para detectar intent real.**
   *Por qué no es regla*: la señal de intent está en el lenguaje natural. «Preguntaron por precio» puede ser curiosidad o urgencia; «necesitamos para el directorio del viernes» es urgencia real. No hay regla que capture eso con regex. El modelo lee el contexto, detecta señales como «comparativo con competidor», «fecha límite mencionada», «aprobación interna pendiente», y ajusta el `intent_score`.

2. **Generación de next-action personalizada por deal.**
   *Por qué no es regla*: la acción óptima depende del historial de la cuenta, la persona que habló, el tono del último intercambio, y el perfil del vendedor. Una regla genérica («envía follow-up a los 3 días») produce mensajes que suenan a template. El modelo redacta una acción específica: «Llama a María en Andina y menciona que el caso de Globex Logistics (construcción de bodega) está cerrado — es el tipo de obra que les interesa».

3. **Clasificación del motivo de bajo score a pesar de fit alto.**
   *Por qué no es regla*: un deal con fit alto y score de intent bajo puede estar en varias situaciones: el interlocutor no es el decisor, hay bloqueo presupuestal temporal, la empresa está evaluando 3 opciones. El modelo lee las notas y propone la hipótesis más probable, que el vendedor confirma o descarta.

> [!cuidado]
> El agente **nunca mueve un deal de etapa** ni registra una actividad en el CRM sin confirmación del vendedor. Su output es siempre una recomendación, no una acción ejecutada.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_crm] → pull de deals via API CRM o fetch_excel (determinístico)
  ↓
[compute_fit_score] → suma ponderada por reglas del tenant (determinístico)
  ↓
[flag_stale_deals] → deals sin actividad > threshold (determinístico)
  ↓
[read_conversations] → lee notas + emails + WhatsApp por deal (determinístico: I/O)
  ↓
[score_intent] → LLM clasifica intent 0-10 + extrae señales clave (agéntico)
  ↓
[generate_next_actions] → LLM redacta acción siguiente por deal top-N (agéntico)
  ↓
[human_review?] → interrupt_before si deal_value > threshold_alto del tenant
  ↓
[write_report] → persiste ranking + next-actions (determinístico, tool: write_report)
  ↓
END
```

### Activities Temporal (cuando se programa como job diario)

- `pull_crm_deals(tenant, date)` — con retry; falla si CRM API está caída.
- `run_scoring_agent(tenant, dataset_id)` — ejecuta el grafo LangGraph.
- `deliver_digest(tenant, date, payload)` — envía email/Slack con ranking.
  `idempotency_key = "lead-score:{tenant}:{date}"`

### Tools necesarias (ver SHARED.md §3.6)

- `fetch_excel` — si el CRM exporta a Google Sheets o CSV.
- `sql_query` — si los deals están en la DB del tenant.
- `send_email` — digest diario al equipo comercial.
- `write_report` — artefacto en PDF/MD para revisión.

### Schema del tool `score_intent` (tool interna del agente)

```yaml
name: score_intent
description: |
  Analiza el texto de conversaciones de un deal y devuelve
  un intent_score (0-10) y señales detectadas.
input_schema:
  type: object
  properties:
    deal_id:   { type: string }
    notes:     { type: string, description: "Texto libre de notas CRM" }
    emails:    { type: string, description: "Threads de email concatenados" }
    whatsapp:  { type: string, description: "Últimos mensajes WhatsApp" }
    tenant:    { type: string }
  required: [deal_id, notes, tenant]
```

## 8. Salida y entrega

### Digest diario (email + Slack)

```
=== TOP LEADS — Consultora ABC — 2026-05-16 ===

1. Andina Constructora · fit 85/100 · intent 9/10
   Deal: Auditoría de procesos obra Bogotá · USD 95 000
   Señales: "necesitamos presentar al directorio el viernes", precio no fue objeción
   Next action: Llama a Juan Pedraza hoy antes de las 3pm. Menciona el caso Globex Logistics.

2. Inmobiliaria Valle Verde · fit 70/100 · intent 6/10
   Deal: Consultoría procesos internos · USD 40 000
   Señales: comparando con otra consultora, preguntaron por metodología
   Next action: Envía el caso de estudio de retail que cerraron en Q1. No price-push aún.

3. [STALE — 18 días sin actividad] Grupo Altamira · fit 60/100 · intent desconocido
   Deal: Due diligence para adquisición · USD 120 000
   Señales: no hay notas ni emails recientes
   Next action: Decide si está muerto o pide al vendedor que lo archive.
   ⚠ Requiere confirmación humana antes de cualquier acción.
```

**Canal**: email matutino + mensaje en canal Slack `#ventas`. Si `deal_value > 100 000 USD`, el item se marca como `⚠ Requiere confirmación humana antes de cualquier acción`.

## 9. Cómo se vende

**Gancho**: «Tu equipo comercial pasa 2 horas al día decidiendo a quién llamar. Este agente lo hace en 90 segundos con toda la información disponible.»

**Propuesta de valor**: ranking diario de leads con intent real (no solo campos CRM), + acción siguiente específica por deal, + alerta de deals en riesgo de enfriarse.

**Diferencia con un Excel de scoring manual**: el agente lee el WhatsApp, los emails y las notas. El Excel no.

| Tier | Qué incluye | Precio orientativo |
|---|---|---|
| Básico | Scoring fit (determinístico) + digest semanal | 150–300 USD/mes |
| Estándar | Fit + intent (agéntico) + digest diario + Slack | 400–700 USD/mes |
| Premium | Todo + next-actions personalizadas + integración directa CRM vía API | 800–1 500 USD/mes + setup 2–5 k USD |

Setup: 2–4 semanas. Incluye: definición de reglas de fit con el cliente, calibración de umbrales por etapa, conexión al CRM (API o exportación CSV), 20 deals de golden set para evaluar intent.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Alucinación de intent**: el modelo interpreta una pregunta casual como señal de urgencia. | El intent score va acompañado de las frases textuales que lo sostienen. El vendedor valida en 10 segundos. |
| **Datos de WhatsApp sucios o ausentes**: la mayoría de PYMES no tienen WhatsApp Business API. | El agente es explícito cuando no tiene conversaciones: `intent_score = null, fuente = solo CRM`. No inventa. |
| **Sesgo hacia deals grandes**: el vendedor puede ignorar el ranking y siempre ir al mayor ticket. | El digest muestra el score, no el ticket. El cliente puede configurar un peso para `deal_value`. |
| **PII en notas**: nombres de personas, montos confidenciales. | Las notas solo se procesan dentro del tenant. No salen del entorno del cliente. `send_email` solo al equipo interno. |
| **CRM desactualizado**: el scoring es tan bueno como los datos. | El agente reporta la tasa de campos vacíos. Si `industry` está vacío en > 40% de deals, avisa al administrador. |

> [!cuidado]
> **Fallback humano**: si el agente no puede determinar intent (conversación vacía, deal sin notas, error de API), el deal queda marcado `intent = desconocido` y el vendedor decide. El agente nunca asigna un score ficticio para completar la lista.

## 11. Variantes por industria

### Instancia 1 — Servicios profesionales (`consultorabc`)

**Datos típicos**: 50–150 deals activos, ticket USD 15 000–150 000, ciclo 30–120 días. Notas ricas (el consultor documenta reuniones). WhatsApp frecuente con el contacto directo.

**Delta determinístico**: el fit score pesa más `industry` (lista de sectores objetivo que la consultora define) y `company_size`. El campo `referral_source` vale doble porque los referidos cierran 3× más.

**Delta agéntico**: el modelo busca en las notas señales de «decision-maker identificado» vs «hablo con el asistente». Ese dato cambia el next-action dramáticamente.

**Regulación**: ninguna específica. PII en notas: nombres y montos. Solo tráfico interno.

**Precio orientativo**: 400–800 USD/mes (tier estándar + integración Pipedrive API).

### Instancia 2 — Real estate / Construcción (`andina`)

**Datos típicos**: 20–60 deals activos, ticket USD 80 000–500 000, ciclo 60–365 días. Fuentes principales: licitaciones públicas (SECOP en Colombia, CompraNet en México), referidos de arquitectos, contacto directo.

**Delta determinístico**: el fit score incluye `licitacion_publica` (flag boolean) y `fecha_cierre_licitacion`. Deals de licitación con fecha < 30 días se priorizan automáticamente independientemente del intent score.

**Delta agéntico**: el modelo lee las bases técnicas de licitación (PDF) para determinar si la empresa cumple los requisitos (experiencia acreditada, capacidad financiera). Tool adicional: `parse_contract_pdf` sobre el pliego de condiciones.

**Regulación**: en licitaciones públicas, el agente no puede «recomendar no participar» sin que un humano revise. Toda recomendación negativa pasa por un revisor senior.

**Precio orientativo**: 600–1 200 USD/mes + setup 3–8 k USD (incluye integración con SECOP/CompraNet API o scraping).

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de ese módulo |
|---|---|
| **B02** — FastAPI a profundidad | El endpoint que recibe el webhook del CRM (deal created/updated) y dispara el job de scoring. Validación Pydantic del payload de Pipedrive/HubSpot. |
| **C01** — SQLAlchemy async | Persistir el `lead_score` por deal+tenant en la DB. El repo `score_repo` filtra siempre por `tenant_id`. |
| **D04** — Observabilidad | Trazar cada llamada al LLM en Phoenix. Ver latencia de `score_intent` vs `generate_next_actions`. Detectar si el modelo está sobreconfiado (todos los scores > 8). |
| **E01** — Anthropic SDK | Loop de scoring: prompt con conversaciones del deal → tool `score_intent` → resultado. Prompt caching del system prompt (reglas de fit + glosario del tenant). |
| **E03** — Skills y AGENTS.md | El skill `lead_scorer` tiene slots: `target_industries`, `fit_weights`, `intent_signals_list`. Se configura en onboarding por tenant. |

## 13. Errores típicos

**1. Sobre-confianza en el intent_score sin baseline de conversiones históricas.**
*Síntoma*: el agente asigna intent 9/10 a tres deals cada semana; el vendedor los prioriza todos y descubre que solo uno de cada tres cierra. El equipo pierde confianza en el ranking.
*Causa raíz*: el intent score no está calibrado contra el win-rate histórico del tenant; sin baseline, el modelo no tiene referencia para distinguir «señal fuerte» de «señal moderada».
*Cómo evitarlo*: en el setup, construir un golden set de al menos 20 deals cerrados (ganados y perdidos) con sus notas, y calibrar el umbral de «intent alto» contra los que efectivamente cerraron. Revisar el `mean_intent_score` mensualmente.

**2. Scoring fugado al futuro (data leakage en features).**
*Síntoma*: durante la evaluación del agente en el golden set, el modelo parece predecir cierres con alta precisión; en producción, la precisión cae drásticamente.
*Causa raíz*: al construir el golden set de evaluación, se usaron features que solo existen después del cierre (p. ej., `stage_final`, `close_date_real`, o notas escritas después de la firma). El modelo aprendió a reconocer esas señales futuras, no las señales disponibles en el momento de scoring.
*Cómo evitarlo*: al construir el golden set, usar exclusivamente los datos disponibles en `t = fecha_de_evaluación`, no en `t = fecha_de_cierre`. Aplicar un corte temporal estricto: si la nota tiene fecha posterior a la evaluación, excluirla. Este error es especialmente frecuente cuando las notas del CRM se actualizan retroactivamente tras el cierre.

**3. Deals grandes ignorados por el vendedor a favor de deals con score visible.**
*Síntoma*: el vendedor invierte la semana en deals con intent 8/10 y descuida uno de 200 k USD que aparece más abajo porque tiene intent 6/10 (notas vacías).
*Causa raíz*: el digest solo muestra el top-N por score y el vendedor no ve más allá.
*Cómo evitarlo*: añadir una sección separada en el digest para «deals de alto valor con intent desconocido» — estos requieren acción de recolección de información, no scoring.

**4. Notas del CRM actualizadas post-facto contaminando el intent.**
*Síntoma*: el agente asigna intent alto a un deal que ya cerró hace dos semanas porque las notas reflejan la conversación de cierre, no las señales previas.
*Causa raíz*: el pipeline usa el estado actual de las notas, no un snapshot con corte temporal.
*Cómo evitarlo*: el nodo `read_conversations` filtra notas con fecha posterior a `snapshot_date`; el ingress del CRM genera un snapshot inmutable por `date`.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «¿Cuál es la diferencia entre el fit score (determinístico) y el intent score (agéntico)? ¿Puede un deal tener fit alto e intent bajo, y qué significa eso para el vendedor?»
2. **Aplícalo a mi caso**: «¿Cómo adaptaría el pipeline si el 80% de las conversaciones de ventas ocurren por WhatsApp y no están en el CRM?»
3. **Por qué falló**: «El agente calificó con intent 9 un deal que llevaba 18 días sin respuesta del cliente. ¿En qué nodo falló y cómo lo detecto en Phoenix?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de scoring con la separación entre fit score determinístico e intent score agéntico.
- Construir un golden set de calibración sin data leakage, usando exclusivamente los datos disponibles en el momento de scoring.
- Configurar las reglas de fit por tenant (industrias objetivo, pesos por fuente, umbrales de valor) sin hardcodear ningún valor.
- Implementar el fallback `intent = desconocido` cuando no hay conversaciones disponibles, sin asignar scores ficticios.
- Dimensionar y cotizar este servicio para una consultora de servicios profesionales y para una constructora con licitaciones públicas.

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|--------------------------------|
| **E04** — Memoria de sesión por SDR/cuenta | El historial de interacciones con cada cuenta es la base del intent scoring; sin entender cómo se persiste la sesión por `account_id`, el agente no puede diferenciar señales nuevas de señales repetidas. |
| **C01** — SQLAlchemy async | El repo `score_repo` filtra siempre por `tenant_id`; entender el patrón de repositorio async es prerequisito para no contaminar el scoring entre tenants. |
| **E01** — Anthropic SDK + tools | El loop de scoring usa `cache_control` sobre el system prompt (reglas de fit + glosario del tenant); sin este módulo, el costo por deal procesado crece sin control. |
| **D04** — Observabilidad | Detectar sobreconfianza del modelo (todos los scores > 8) requiere monitoreo en Phoenix; sin trazas, el agente puede estar en modo «siempre optimista» sin que nadie lo note. |
