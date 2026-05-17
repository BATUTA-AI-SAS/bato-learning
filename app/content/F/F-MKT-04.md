---
ext_id: F-MKT-04
slug: social-listening
track: F
dept: MKT
ord: 204
title: "Social listening y análisis de menciones"
summary: "Agente que ingesta menciones de redes sociales y reseñas, calcula sentimiento y share of voice, y clasifica cada mención como oportunidad comercial, riesgo reputacional o alerta de crisis."
related_modules: [B02, B06, C01, D04, E01]
industries_instanced: [retail, salud, hospitalidad, servicios-edu]
tenants_in_examples: [tiendabox, sanrafael]
big_corp_vendors: [Brandwatch, Sprinklr, Talkwalker]
latam_tools: [mention, hootsuite, meta-business-suite, google-alerts]
key_concepts: [sentiment, share-of-voice, crisis-trigger, alerting, CAC, CTR, ROAS]
estimated_minutes: 45
deterministic_share: 0.4
version: 1
---

## 1. Problema operativo

La directora de marketing de TiendaBox Retail se entera de que hay una queja viral sobre un envío demorado tres días después de que el post tiene 400 comentarios negativos. Para entonces, el daño reputacional ya está hecho. No hay un sistema que la avise cuando una mención supera un umbral de negatividad o cuando una influencer menciona la marca — positiva o negativamente.

En Clínica San Rafael el problema es inverso: los pacientes publican reseñas en Google Maps y Doctoralia continuamente, pero nadie las lee de manera sistemática. El gerente de marketing no sabe si las reseñas de la semana pasada mencionan un médico específico, si hay un patrón de queja sobre los tiempos de espera, o si hay una oportunidad de responder públicamente a un paciente satisfecho y amplificar esa señal positiva.

El problema no es la falta de datos — las menciones existen. El problema es que leerlas manualmente, categorizarlas y decidir qué requiere acción urgente es imposible a escala humana.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|---|---|---|
| **Brandwatch** | Escucha de 100M+ fuentes, análisis de sentimiento con NLP avanzado, share of voice, alerts, integración con plataformas de publicación. Estándar de facto enterprise. | 800–15 000 USD/mes; enterprise 60 000–150 000 USD/año |
| **Sprinklr** | Suite unificada de CXM (social listening + publishing + CRM). Discontinúa self-serve desde abril 2026; es puro enterprise. | Custom; estimado 100 000+ USD/año para grandes cuentas |
| **Talkwalker** | Análisis de conversación en tiempo real, tendencias, detección de crisis, cobertura en medios digitales y TV/radio. | 10 000–50 000 USD/mes; plan básico ~1 000 USD/mes |

La PYME no puede pagar ninguno de estos. Usa Google Alerts (gratuito, muy limitado), menciones manuales en Meta Business Suite, o no hace nada sistemático.

## 3. PYME LATAM realista

TiendaBox tiene acceso a:
- **Meta Business Suite**: menciones en Facebook e Instagram que etiquetan la cuenta.
- **Google Alerts**: alertas de mencion del nombre de la marca en texto indexado.
- **Google Maps / Reseñas de Google**: reseñas de la tienda física si la tiene.
- **Manual**: un community manager que revisa menciones cuando tiene tiempo.

Clínica San Rafael tiene acceso a:
- **Doctoralia / Doctify**: plataformas de reseñas de salud específicas para LATAM.
- **Google Maps**: reseñas generales.
- **Instagram**: menciones de pacientes que publican sobre sus experiencias.

No tiene acceso a APIs de Twitter/X (cuyo costo API subió 42 000 USD/mes para acceso enterprise en 2023 y siguió subiendo), ni a Reddit, ni a foros. La cobertura es parcial pero suficiente para el 80% de los casos.

## 4. Datos típicos

| Campo | Fuente | Frecuencia | Ejemplo de fila |
|---|---|---|---|
| `mention_id` | API / scraper | por mención | `"mention_ig_20260514_082341"` |
| `platform` | fuente | por mención | `"instagram"` / `"google_maps"` / `"doctoralia"` |
| `author_handle` | fuente | por mención | `"@usuario_123"` |
| `author_followers` | API (si disponible) | por mención | `14800` |
| `content_text` | fuente | por mención | `"Esperé 45 min y al final me dijeron que no tenían el medicamento"` |
| `publication_date` | fuente | por mención | `"2026-05-14T09:23:00"` |
| `brand_mentioned` | detectado | por mención | `"Clínica San Rafael"` |
| `keyword_matched` | detectado | por mención | `["espera", "medicamento", "atención"]` |
| `sentiment_score` | calculado | por mención | `-0.72` (escala -1 a +1) |
| `sentiment_label` | calculado | por mención | `"negativo"` |
| `reach_estimate` | calculado | por mención | `14800` (followers del autor) |
| `engagement` | API | por mención | `{likes: 142, comments: 38, shares: 12}` |

**Share of Voice (SoV)**: porcentaje de menciones de la marca dentro del total de menciones del sector o de los competidores. `SoV = menciones_marca / (menciones_marca + menciones_competidores)`. Si la marca tiene 340 menciones y los competidores suman 860, `SoV = 28%`. Métrica de posicionamiento relativo, no absoluto.

Volumen típico para PYME retail: 50–500 menciones por semana. Para clínica: 10–80 reseñas por semana. Para e-commerce durante campaña: 200–2 000 menciones en 48h.

## 5. Tramos determinísticos

1. **Ingesta de menciones vía APIs y exportaciones**: pull desde la API de Meta (Graph API para menciones de la página), Google My Business API (reseñas), Doctoralia/Doctify si tienen API disponible, o scraping programático de reseñas con las credenciales del tenant. Normalizar a schema común `{mention_id, platform, author, content_text, date, reach}`. Frecuencia: cada 6 horas en modo normal; cada 15 minutos en modo alerta activa.

2. **Análisis de sentimiento básico**: aplicar un modelo de sentimiento (VADER para español o un fine-tuned BERT-es disponible en HuggingFace) sobre `content_text`. Produce `sentiment_score` (-1 a +1) y `sentiment_label` (positivo/neutro/negativo). Este análisis es determinístico dado el modelo y el texto: mismo texto → mismo score. El modelo no cambia en cada ejecución.

3. **Detección de keywords de alerta**: verificar si `content_text` contiene alguna keyword de la lista `alert_keywords` del tenant (e.g., `["devolución", "estafa", "timo", "muy malo", "nunca más"]`). Si hay match, marcar la mención como `alert_keyword_detected: true`. Regla cerrada.

4. **Cálculo de métricas agregadas**: por período (diario/semanal):
   - `total_mentions`: recuento total.
   - `sentiment_breakdown`: % positivo / neutro / negativo.
   - `share_of_voice`: menciones propias / (propias + competidores) si hay datos de competidores.
   - `avg_sentiment_score`: promedio ponderado por reach.
   - `top_keywords_by_sentiment`: las 10 palabras más frecuentes en menciones negativas y positivas.

5. **Alertas por umbral**: si el porcentaje de menciones negativas en las últimas 2 horas supera el umbral del tenant (por defecto: > 40% negativo + volumen > 20 menciones/hora), generar alerta inmediata. Regla fija.

## 6. Tramos agénticos

1. **Clasificación de urgencia y tipo de cada mención.**
   *Por qué no es regla*: el sentimiento negativo no siempre implica urgencia. «Ojalá abrieran más temprano» es negativo pero no urgente. «Me engañaron y voy a denunciar» es negativo y urgente. La clasificación en `{oportunidad_comercial, queja_menor, queja_urgente, riesgo_reputacional, crisis_potencial, neutro_informativo}` requiere leer el contexto, el tono y el contenido de la mención — no hay regla que lo cubra.

2. **Detección de señal temprana de crisis.**
   *Por qué no es regla*: una crisis en redes no empieza con un post viral — empieza con 5 posts similares de autores distintos en 30 minutos, o con una mención de un autor de alta influencia (> 10 000 followers) con tono agresivo, o con una palabra específica en el contexto de un evento reciente (un retiro de producto, una noticia de salud). El modelo lee el cluster de menciones, el reach agregado, y el contexto temporal para detectar el early signal. Una regla puede detectar el umbral de volumen, pero no el patrón de early signal.

3. **Identificación de oportunidad comercial.**
   *Por qué no es regla*: una mención positiva de un influencer que tiene 50 000 seguidores es una oportunidad de partnership. Un comentario de alguien preguntando «¿dónde consigo X?» es una oportunidad de venta directa. Un post de un competidor que recibe quejas es una oportunidad de posicionamiento. Identificar cuál es cuál requiere razonamiento contextual.

4. **Redacción de respuesta sugerida para menciones que requieren respuesta pública.**
   *Por qué no es regla*: la respuesta a una queja en Google Maps tiene que sonar humana, empática y específica — no puede ser un template genérico de «lamentamos tu experiencia». El modelo lee el contenido de la queja y propone una respuesta en el tono de marca del tenant, con las instrucciones concretas para el community manager.

> [!cuidado]
> **Fallback humano**: si el modelo no puede determinar si una mención es `crisis_potencial` o `queja_urgente` (contenido ambiguo, idioma regional o jerga no reconocida), la clasifica como `requires_human_review` y la pone en la cola de revisión manual con prioridad alta. No asigna una categoría incorrecta para completar el flujo — la incertidumbre es un dato válido.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_mentions] → pull vía APIs + scraping con normalización (determinístico)
  ↓
[compute_sentiment] → modelo NLP sobre content_text (determinístico)
  ↓
[detect_alert_keywords] → match contra alert_keywords del tenant (determinístico, GUARD)
  ↓
[compute_aggregates] → SoV, sentiment breakdown, top keywords por período (determinístico)
  ↓
[check_alert_threshold] → si %negativo + volumen supera umbral → alerta inmediata (determinístico)
  ↓
[classify_mentions] → LLM clasifica urgencia y tipo de cada mención (agéntico)
  ↓
[detect_crisis_signal] → LLM detecta early signal de crisis en el cluster (agéntico)
  ↓
[identify_opportunities] → LLM identifica menciones con potencial comercial (agéntico)
  ↓
[draft_responses] → LLM redacta respuesta sugerida para menciones que la requieren (agéntico)
  ↓
[human_escalation?] → interrupt_before para crisis_potencial o riesgo_reputacional
  ↓
[write_report] → reporte diario/semanal + cola de acciones para el community manager (determinístico)
  ↓
END
```

### Activities Temporal (job recurrente + on-demand de alerta)

- `pull_mentions(tenant, platforms, since)` — ingesta de las últimas N horas. Retry con backoff para límites de API.
- `run_listening_agent(tenant, batch_id)` — ejecuta el grafo sobre el batch.
- `send_crisis_alert(tenant, mention_ids, summary)` — alerta inmediata al responsable si crisis_potencial.
  `idempotency_key = "listening:{tenant}:{batch_id}"`

### Frecuencia recomendada

- **Modo normal**: cada 6 horas (4 ejecuciones diarias).
- **Modo campaña activa**: cada hora durante el período de campaña.
- **Modo alerta**: pull cada 15 minutos cuando hay alerta activa, hasta que el responsable confirme que está gestionando.

### Tools necesarias (referencia SHARED.md §3.6)

- `fetch_csv` — si las menciones se exportan manualmente (Meta Business Suite, Google Alerts).
- `sql_query` — menciones ya almacenadas + histórico de sentimiento para comparativa.
- `post_slack_message` — alerta de crisis al canal de marketing o CX del tenant.
- `send_email` — reporte diario/semanal al equipo.
- `write_report` — PDF con dashboard de sentimiento + cola de acciones.

## 8. Salida y entrega

### Reporte diario (email matutino)

```
SOCIAL LISTENING — Clínica San Rafael — 15 Mayo 2026

RESUMEN DEL DÍA (últimas 24h):
Total menciones: 47
  Positivas: 28 (59.6%) | Neutras: 12 (25.5%) | Negativas: 7 (14.9%)
Share of Voice vs Clínica del Norte y Centro Médico Los Andes: 38% (vs 34% semana pasada ↑)

⚡ ALERTA ACTIVA: 0 activas en este período.

🔴 REQUIEREN RESPUESTA URGENTE (hoy):

1. Google Maps — @marian.rodz (12 likes, 3 respuestas)
   «Fui a urgencias y tuve que esperar 2.5 horas con un dolor agudo. El personal
   fue grosero. No regreso.»
   Clasificación: queja_urgente / posible riesgo_reputacional
   Respuesta sugerida:
   «Mariana, sentimos profundamente tu experiencia. Los tiempos de espera en
   urgencias son una prioridad que estamos trabajando activamente. Por favor,
   escríbenos a atencion@sanrafael.com.co para que un coordinador se comunique
   contigo hoy. Tu opinión es importante para mejorar.»
   ⚠ REQUIERE APROBACIÓN del Gerente Médico antes de publicar.

🟡 OPORTUNIDADES COMERCIALES (esta semana):

1. Instagram — @drpedro_nutricion (8 400 seguidores)
   «Si buscan una clínica con excelente nutricionista, Clínica San Rafael. Tuve
   una consulta espectacular con el Dr. García.»
   Clasificación: oportunidad_de_partnership
   Acción sugerida: Contactar @drpedro_nutricion para colaboración — tiene
   audiencia alineada con los servicios de nutrición de la clínica.

🟢 POSITIVAS DESTACADAS:

[Lista de 5 menciones positivas con propuesta de respuesta pública]

TENDENCIAS DE LA SEMANA:
Top palabras en menciones negativas: "espera" (12×), "tiempo" (9×), "farmacia" (6×)
Top palabras en menciones positivas: "amable" (18×), "profesional" (14×), "rápido" (8×)
Insight: El patrón de quejas sobre tiempo de espera es consistente (3 semanas seguidas).
Requiere atención operativa, no solo de comunicación.
```

**Canal**: email matutino al equipo de marketing + Slack para alertas de crisis. El community manager tiene la cola de respuestas con las sugerencias listas para aprobar/editar.

## 9. Cómo se vende

**Gancho**: «Tu competidor está leyendo lo que dicen de ti en Google Maps. Tú no. Este agente lo hace en tiempo real y te avisa cuando hay que actuar — antes de que sea tarde.»

**Propuesta de valor**: de «enterarse del problema 3 días después» a «actuar en menos de 2 horas». El valor está en la clasificación de urgencia (el agente distingue una queja menor de un early signal de crisis) y en las respuestas sugeridas (el community manager no tiene que redactar desde cero).

| Tier | Qué incluye | Precio orientativo |
|---|---|---|
| Básico | Ingesta + sentimiento básico + reporte semanal + alertas por umbral | 150–300 USD/mes |
| Estándar | Todo Básico + clasificación de urgencia agéntica + oportunidades comerciales + respuestas sugeridas | 400–700 USD/mes |
| Premium | Todo Estándar + cobertura de plataformas adicionales (TikTok, Twitter/X si el cliente paga la API, foros) + análisis de competidores + integración Slack en tiempo real | 700–1 500 USD/mes + setup 2–5 k USD |

Setup: 1–3 semanas. Incluye: configuración de acceso a APIs (Meta Graph, Google My Business), definición de `alert_keywords` y umbrales con el equipo, definición de competidores para SoV, y golden set de 20 menciones históricas para calibrar la clasificación agéntica.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Cobertura parcial**: la API de Twitter/X es inaccessible para PYMES (costo prohibitivo desde 2023). Reddit, TikTok y foros tienen APIs limitadas. | Documentar explícitamente qué plataformas cubre el sistema para ese tenant. El reporte declara `plataformas_monitoreadas` en el encabezado. Sin declararlo, el cliente asume cobertura total. |
| **Falsos positivos de crisis**: el agente marca como crisis_potencial una mención que es un meme o sarcasmo sin intención real de daño. | El modelo incluye su nivel de confianza en la clasificación. Si confianza < 0.7, pasa a `requires_human_review` automáticamente. La clasificación de crisis requiere confianza ≥ 0.85. |
| **Latencia en alerta de crisis**: si el job corre cada 6 horas, una crisis puede escalar antes de la siguiente ejecución. | En modo normal, job cada 6 horas. Si en cualquier ejecución se detecta `alert_keyword_detected` con volumen elevado, el job pasa automáticamente a modo alerta (cada 15 minutos) hasta confirmación manual del responsable. |
| **Datos de salud en reseñas**: pacientes mencionan diagnósticos, medicamentos, nombres de médicos. Esos datos son sensibles. | El agente procesa el texto de las reseñas para clasificarlas, pero **no almacena datos de pacientes individuales** en la DB del sistema. Las reseñas se procesan en tránsito; lo que persiste es la clasificación + métricas agregadas, no el texto completo de reseñas con PII. |
| **Respuesta pública incorrecta**: el agente sugiere una respuesta que el community manager publica sin revisar, y la respuesta es inapropiada o agrava la situación. | Las respuestas sugeridas siempre se entregan como «BORRADOR — REQUIERE APROBACIÓN». El flujo de entrega incluye checkbox de aprobación. Se registra quién aprobó y cuándo. |
| **Alucinación en detección de oportunidades**: el agente clasifica una mención neutra como oportunidad_comercial. | Las oportunidades identificadas siempre se entregan al community manager con el razonamiento del modelo. El manager decide si actuar. No hay acción automática sobre menciones clasificadas como oportunidad. |

> [!cuidado]
> **Regulación datos de salud (Clínica San Rafael)**: el procesamiento de reseñas de pacientes que mencionan experiencias clínicas requiere base legal bajo la legislación de salud local (Ley 1581 en Colombia, LGPD en Brasil para datos de salud). Las reseñas son texto público, pero el hecho de procesarlas con IA para análisis interno puede requerir comunicarlo en la política de privacidad de la clínica. El agente solo procesa texto publicado públicamente por el propio autor; no accede a historiales clínicos.

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 100–2 000 menciones semanales en campaña, principalmente Instagram y Google Maps (si tiene tienda física). Picos de volumen en Black Friday, CyberMonday, liquidaciones. Menciones sobre productos, envíos, atención al cliente.

**Delta determinístico**: durante campañas activas, el sistema activa automáticamente modo alerta (pull cada hora). El umbral de alerta se ajusta al volumen esperado de la campaña — en Black Friday, el umbral base se multiplica por 3 para no saturar al equipo con falsos positivos de alto volumen normal.

**Delta agéntico**: el modelo detecta si una mención negativa sobre envío está correlacionada con un proveedor logístico específico (e.g., «Coordinadora tardó 10 días» aparece 15 veces en una semana). Eso es una señal operativa que el equipo de logística debe recibir, no solo marketing. El agente clasifica la mención como `operational_signal` y la enruta al canal correcto.

**ROAS relevante**: las menciones positivas de influencers durante campañas pagadas son datos de atribución. Si una influencer con 80 000 seguidores menciona la marca el mismo día que el CTR del anuncio de Instagram sube 40%, esa correlación es información. El sistema registra las menciones de influencers con reach > 10 000 como `influencer_signal` para cruzar con los datos de ROAS de F-MKT-01.

**Precio orientativo**: 500–1 000 USD/mes.

### Instancia 2 — Salud / Clínicas (`sanrafael`)

**Datos típicos**: 10–100 reseñas semanales en Doctoralia, Google Maps, Instagram. Menor volumen que retail, pero mayor sensibilidad por el contenido (menciones de diagnósticos, experiencias clínicas).

**Delta determinístico**: el sistema categoriza las reseñas por servicio o especialidad (nutrición, urgencias, consulta general) si la mención lo indica. Las quejas por área se agregan para identificar si es un problema sistémico de un área específica vs una experiencia aislada.

**Delta agéntico**: en salud, el modelo tiene que ser especialmente cuidadoso al clasificar urgencia. Una mención sobre un error médico potencial tiene urgencia extrema — no porque vaya a ser viral, sino por las implicaciones legales y de reputación clínica. El modelo aprende a priorizar la gravedad clínica percibida sobre el reach del autor.

**Regulación**: el agente no puede responder automáticamente a quejas que mencionen mala praxis, diagnósticos incorrectos o daño al paciente. Esas menciones van directamente a la dirección médica + legal antes de cualquier respuesta pública. Esto es non-negociable y está hard-coded en el flujo.

**Precio orientativo**: 300–600 USD/mes.

### Instancia 3 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: 20–200 reseñas semanales en Google Maps, TripAdvisor, Instagram. Alta correlación entre reseñas y temporada turística.

**Delta agéntico**: el modelo detecta menciones que son «señal de oportunidad de viralización» — un post con fotos del plato que tiene 500 likes orgánicos en las primeras 2 horas es una oportunidad de repostear o amplificar. La detección de ese patrón (alto engagement temprano en contenido orgánico) no es una regla fija porque depende del baseline del tenant.

**Precio orientativo**: 200–400 USD/mes.

### Instancia 4 — Educación

**Datos típicos**: instituciones educativas monitorizan menciones de su marca, de sus programas, de sus directivos y de sus competidores en LinkedIn, Instagram y foros estudiantiles.

**Delta agéntico**: el modelo detecta cuando la mención es de un exalumno con alto perfil profesional (señal de alumni success) — oportunidad de relaciones públicas. O cuando es una queja de un estudiante actual sobre la calidad del programa — señal que puede llegar a la dirección académica antes de que escale.

**CAC relevante**: el costo de adquisición de un estudiante es alto (campañas de captación en redes, eventos, ferias). Una mención negativa de un estudiante potencial durante el período de inscripción puede afectar directamente el **CAC** de ese período. El sistema prioriza las menciones negativas durante ventanas de inscripción.

**Precio orientativo**: 250–500 USD/mes.

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de ese módulo |
|---|---|
| **B02** — FastAPI a profundidad | Endpoint que recibe webhooks de menciones en tiempo real (cuando la plataforma los soporta, como Meta Graph API con webhooks configurados). Valida el payload del webhook antes de encolar. |
| **B06** — SSE + chat tutor | El dashboard de menciones puede usar SSE para actualizar en tiempo real la cola de menciones pendientes de clasificación, sin que el community manager tenga que recargar la página. |
| **C01** — SQLAlchemy async | `mentions_repo` persiste menciones clasificadas por `(tenant, mention_id, platform, classification, date)`. El histórico de sentimiento por semana permite comparar la salud reputacional mes a mes. |
| **D04** — Observabilidad | Phoenix traza `classify_mentions`, `detect_crisis_signal`, `identify_opportunities`, `draft_responses`. Medir: ¿cuántas clasificaciones son confirmadas por el community manager sin edición? Esa métrica es el proxy de calidad del agente. |
| **E01** — Anthropic SDK | Las definiciones de `alert_keywords`, `competitor_names`, y `brand_context` del tenant se cachean con `cache_control: {"type": "ephemeral", "ttl": "1h"}`. Las menciones del batch actual van en el mensaje dinámico. Dado el volumen (50–500 menciones/día), el caching del contexto del tenant es crítico para el costo. |

## 13. Errores típicos

**1. Clasificación de crisis con falso positivo que interrumpe operaciones.**
*Síntoma*: el agente clasifica un meme sarcástico como `crisis_potencial` y manda una alerta de crisis al CEO a las 2AM; el equipo activa el protocolo de crisis para un post sin impacto real.
*Causa raíz*: el nodo `detect_crisis_signal` no tiene umbral mínimo de confianza activo, o el modelo no está calibrado para detectar sarcasmo e ironía en español informal.
*Cómo evitarlo*: la clasificación `crisis_potencial` requiere confianza ≥ 0.85. Por debajo de ese umbral, la mención pasa a `requires_human_review`. El golden set de calibración incluye ejemplos de sarcasmo, humor negro y crítica indirecta en el lenguaje regional del tenant.

**2. Alucinación de oportunidad comercial en menciones neutras.**
*Síntoma*: el agente clasifica como `oportunidad_de_partnership` una mención que dice «fui a San Rafael de camino al trabajo» (referencia geográfica, no a la clínica); el community manager pierde tiempo contactando a un usuario que no habló de la marca.
*Causa raíz*: el nodo `identify_opportunities` no verifica que la mención sea inequívocamente sobre la marca del tenant antes de clasificarla como oportunidad.
*Cómo evitarlo*: el nodo requiere que `brand_mentioned` esté confirmado (match exacto del nombre de la marca o alias configurados) antes de clasificar como oportunidad comercial. Menciones ambiguas van a `requires_human_review`.

**3. Respuesta sugerida publicada sin aprobación en caso de queja médica.**
*Síntoma*: el community manager publica la respuesta sugerida a una reseña que menciona una mala praxis sin pasar por la dirección médica; la respuesta pública puede ser usada como evidencia en un proceso legal.
*Causa raíz*: el flujo de aprobación no distingue entre quejas generales y quejas con implicación clínica o legal.
*Cómo evitarlo*: el nodo `draft_responses` para tenants del sector salud tiene una regla adicional: si la mención contiene keywords de `medical_risk_keywords` (`["mala praxis", "error médico", "daño", "demanda", "denunciar"]`), la respuesta sugerida va directamente a la dirección médica + legal y no al community manager hasta recibir aprobación de ambos.

**4. Riesgo legal por contenido auto-publicado sin review.**
*Síntoma*: el sistema tiene habilitada la publicación automática de respuestas positivas en Google Maps; el agente publica una respuesta que menciona un descuento o una promesa («próxima visita gratis») que el negocio no autorizó.
*Causa raíz*: el `interrupt_before` está desactivado para las respuestas clasificadas como «positivas» bajo la asunción de que son de bajo riesgo.
*Cómo evitarlo*: ninguna respuesta pública se publica automáticamente sin aprobación humana. El checklist de aprobación registra quién aprobó y cuándo. Si el sistema ofrece integración de publicación directa, esta requiere una acción explícita del community manager, no una confirmación pasiva por timeout.

**5. Cobertura de plataformas no declarada al cliente.**
*Síntoma*: el cliente asume que el sistema monitorea Twitter/X y TikTok; una crisis empieza en TikTok y el sistema no la detecta porque esas plataformas no están integradas.
*Causa raíz*: el alcance de plataformas monitoreadas no está documentado de forma visible en el reporte ni en el onboarding.
*Cómo evitarlo*: el encabezado de cada reporte declara explícitamente `plataformas_monitoreadas: [instagram, google_maps, doctoralia]` y `plataformas_no_cubiertas: [twitter_x, tiktok, reddit]`. El contrato de servicio incluye esta declaración de alcance.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre `alert_keyword_detected` (determinístico) y `detect_crisis_signal` (agéntico) con el ejemplo de TiendaBox — ¿cuándo necesito cada uno y por qué no basta con el keyword?»
2. **Aplícalo a mi caso**: «Mi cliente es una clínica dental en Colombia. ¿Cómo configuro el flujo para que las quejas que mencionan daño al paciente vayan obligatoriamente al director médico antes de cualquier respuesta pública?»
3. **Por qué falló**: «El agente marcó como crisis una mención que era un meme; el threshold de confianza estaba configurado en 0.6. ¿A qué valor lo subo y cómo calibro el modelo con ejemplos regionales de sarcasmo?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Construir el pipeline de ingesta de menciones desde Meta Graph API, Google My Business API y exportaciones manuales con schema normalizado.
- Implementar el análisis de sentimiento determinístico con VADER o BERT-es y los alertas por umbral de volumen/negatividad.
- Diseñar los nodos agénticos de clasificación de urgencia, detección de early signal de crisis, e identificación de oportunidades con umbrales de confianza y fallback a `requires_human_review`.
- Configurar el flujo de aprobación para respuestas públicas con trail de auditabilidad para sectores sensibles (salud, educación).
- Cotizar y dimensionar el servicio para retail, salud, hospitalidad y servicios educativos LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué leerlo antes |
|--------|---------------------|
| **B02** — FastAPI a profundidad | El endpoint de webhooks de Meta Graph API usa los patrones de validación de payload y encola en background; B02 enseña exactamente ese patrón. |
| **B06** — SSE + chat tutor | El dashboard de menciones en tiempo real usa SSE para actualizar la cola sin recargar; B06 explica cuándo SSE es mejor que WebSockets para este caso. |
| **C01** — SQLAlchemy async | El repositorio de menciones `(tenant, mention_id, platform, classification, date)` y el histórico de sentimiento semanal requieren los patrones async de C01. |
| **D04** — Observabilidad | Phoenix traza cada clasificación de mención; la métrica `classification_confirmed_rate` (cuántas clasificaciones confirma el community manager sin editar) es el proxy de calidad del agente. |
| **E01** — Anthropic SDK | El caching del contexto del tenant (`alert_keywords`, `competitor_names`, `brand_context`) es crítico cuando el agente procesa 50–500 menciones por día — sin caché el costo es prohibitivo. |
