---
ext_id: F-PRD-04
slug: analisis-uso-features
track: F
dept: PRD
ord: 283
title: "Análisis de uso de features y diagnóstico de funnels"
summary: "Agente que procesa métricas de uso (funnel, retención, cohortes), identifica caídas anómalas, propone hipótesis explicativas, y entrega un diagnóstico accionable al PM sin que este necesite ser analista de datos."
estimated_minutes: 45
industries_instanced: [retail, servicios-fin]
tenants_in_examples: [tiendabox, cooppopular]
---

## 1. Problema operativo

La PM de TiendaBox Retail sabe que el **funnel** de activación cayó esta semana — el **funnel** es la secuencia de pasos que un usuario nuevo debe completar para llegar a su primer valor (en TiendaBox: registro → primera publicación → primera venta). El dato lo ve en GA4 o en Mixpanel. Lo que no sabe es *por qué* cayó: ¿fue el cambio de UI del martes? ¿fue una campaña que trajo usuarios de baja calidad? ¿fue un bug silencioso en el paso 3?

El gerente de producto de Coop. Popular de Crédito tiene un problema distinto: la **retención** de usuarios del módulo de crédito a 30 días cayó de 68% a 51% en dos meses. La **retención** mide qué porcentaje de usuarios que activaron una feature vuelven a usarla N días después. Sabe que algo cambió, pero entre los logs de Sentry, las métricas de Amplitude, y el historial de deploys, no tiene el tiempo ni las skills de datos para cruzarlo todo.

El agente no reemplaza al analista — la PYME no tiene analista. Reemplaza la reunión de 2 horas donde el PM mira datos sin contexto y concluye "hay que investigar más".

---

## 2. Hoy en big corps

Los equipos de producto con presupuesto dedican analistas de datos al análisis de uso, apoyados por plataformas de product analytics.

| Vendor | Capacidad | Precio orientativo |
|--------|-----------|-------------------|
| **Amplitude** (AI Feedback + Data Assistant, 2026) | Análisis de funnels, retención y cohortes con lenguaje natural; el Global Agent detecta anomalías y genera hipótesis | Desde ~1 200 USD/mes (Plus); Growth desde ~36 k USD/año |
| **Mixpanel** (AI Insights, 2026) | Funnel analysis, retención por cohorte, análisis de flujo; AI que responde preguntas en lenguaje natural sobre los datos | Desde ~25 USD/mes (Growth); Enterprise cotización |
| **Pendo Intelligence (Leo AI)** | Correlaciona uso de features con adoption, churn, NPS; guías in-app con IA | Desde ~2 000 USD/mes (Growth) |
| **PostHog** (self-hosted) | Funnels, retención, cohortes, session replay, feature flags; open source, self-hosteable | Gratis (self-hosted) o ~450 USD/mes (cloud) |

La PYME usa GA4 (gratis) o Mixpanel Growth. No tiene analista que interprete los datos automáticamente. El insight está en los datos; el tiempo de extraerlo no existe.

---

## 3. PYME LATAM realista

TiendaBox y Coop. Popular trabajan con:
- **Google Analytics 4** (GA4): eventos de comportamiento en web y app. Gratis, integrado en Google Tag Manager, pero no tiene funnel analysis avanzado sin exportar a BigQuery.
- **Mixpanel** (plan Growth, desde ~25 USD/mes): funnels, retención, cohortes básicas. La PYME lo usa para ver números, no para interpretar.
- **Firebase Analytics** (apps móviles): eventos automáticos de la app React Native o Flutter. Gratis, integrado con GA4.
- **Sentry** (free tier): logs de errores que a veces explican caídas en el funnel.
- **Notion / Google Sheets**: donde el PM intenta correlacionar datos a mano una vez al mes.

El ERP (Siigo, Alegra) no tiene datos de producto digital. El gap es que los datos de uso están en herramientas analíticas, los datos de errores están en Sentry, y el historial de deploys está en GitHub — nadie los cruza automáticamente.

---

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen |
|--------|---------|------------|---------|
| Mixpanel / GA4 export | JSON o CSV con eventos `{user_id, event_name, timestamp, properties}` | Diario o semanal | 10k–1M eventos/mes según usuario base |
| Funnel report (Mixpanel API) | JSON: `{step, users_entered, users_converted, conversion_rate}` | On demand | 1 report por funnel definido |
| Retention report (Mixpanel API) | JSON: `{cohort_date, day_N, retained_users, retention_rate}` | Semanal | 1 table de retención por evento de activación |
| Sentry issues (correlación) | JSON: errores del período analizado | Continuo | Variable |
| Deploy log (GitHub / Vercel) | JSON: `{deploy_id, timestamp, diff_summary}` | Por deploy | 5–30 deploys/mes |

Ejemplo de registro de funnel step:
```json
{
  "tenant_id": "tiendabox",
  "funnel_id": "onboarding_seller_v2",
  "step": 3,
  "step_name": "primera_publicacion",
  "week": "2026-W19",
  "users_entered": 420,
  "users_converted": 189,
  "conversion_rate": 0.45,
  "prev_week_rate": 0.61
}
```

---

## 5. Tramos determinísticos

1. **Ingesta de métricas via API**: pull de Mixpanel o GA4 para el período seleccionado. El agente extrae: funnel steps con tasa de conversión por paso, tabla de **retención** (retención: porcentaje de usuarios de una cohorte que vuelven a usar la app o feature N días después de la primera vez), tabla de **cohortes** (cohorte: grupo de usuarios que realizaron una acción común en el mismo período de tiempo — e.g., "usuarios que se registraron en la semana W19 de 2026").

2. **Cálculo de anomalías estadísticas**: comparar la métrica de la semana actual contra la media de las 4 semanas anteriores. Si la tasa de conversión de cualquier step de funnel cae > 15% o la retención a 7 días cae > 10 puntos porcentuales, se marca como anomalía. Este threshold es configurable por tenant.

3. **Correlación con eventos del sistema**: cruzar las fechas de caída de métricas contra: (a) deploys del período (GitHub API), (b) spikes de errores en Sentry (Sentry API), (c) campañas de marketing activas si el tenant integra su herramienta de email/ads. La correlación es temporal (mismo período), no causal — la causalidad es agéntica.

4. **Cálculo de **NPS** por cohorte** (cuando hay datos): el **NPS** (Net Promoter Score) es la diferencia entre el porcentaje de promotores (score 9–10) y detractores (score 0–6) en una encuesta de satisfacción. Si el tenant tiene encuestas NPS vinculadas a segmentos, se calcula el NPS de cada cohorte afectada y se incluye en el reporte.

5. **Generación de tabla comparativa**: funnel step × semana, retención por cohorte × semana. Formato tabular listo para el modelo y para el PM.

---

## 6. Tramos agénticos

1. **Diagnóstico de caída de funnel** — el modelo recibe la anomalía detectada (ej.: step 3 "primera_publicacion" cayó de 61% a 45% en la semana W19) y el contexto correlacionado (deploy del martes W19 que cambió el formulario de publicación, spike de errores en `/api/publicaciones` el mismo día). El modelo propone una hipótesis principal y 1–2 hipótesis alternativas con su razonamiento.

   *Por qué no es regla*: la relación entre un deploy, un spike de errores y una caída de conversión puede ser causal, coincidental, o consecuencia de un tercer factor (campaña que trajo usuarios de menor calidad). Determinar la hipótesis más probable requiere razonamiento sobre el contexto completo, no solo sobre los números.

2. **Explicación de caída de retención** — el modelo identifica qué cohorte de usuarios tiene retención anómala y propone explicaciones: ¿fue el canal de adquisición (users de campaña vs. orgánico)? ¿fue un cambio de producto que afectó a los usuarios heavy users más que a los nuevos? ¿fue la estacionalidad del negocio?

   *Por qué no es regla*: la retención puede caer por razones de producto, de mercado, o de mezcla de usuarios. Distinguir cuál es relevante requiere leer el contexto del tenant (su modelo de negocio, su calendario de marketing, sus deploys recientes).

3. **Priorización de hipótesis para investigar** — el modelo ordena las hipótesis por probabilidad estimada y facilidad de validación. "El deploy del martes cambió el formulario → fácil de validar con un A/B test retrospectivo" tiene prioridad sobre "la campaña trajo usuarios de menor calidad → requiere análisis de LTV por canal".

   *Por qué no es regla*: la prioridad de qué investigar primero depende del costo de validación, del impacto potencial si es verdad, y del contexto de qué el PM puede hacer esta semana con sus recursos. No hay regla cerrada que cubra esas dimensiones.

4. **Sugerencia de experimentos** — para cada hipótesis principal, el modelo propone cómo validarla: qué evento trackear, qué segmento comparar, si se necesita un A/B test o basta con análisis retrospectivo. La sugerencia es de diseño de investigación, no de ejecución.

   *Por qué no es regla*: el diseño del experimento correcto depende del stack de analytics del tenant, del volumen de usuarios (¿hay suficiente para un A/B?), y de los recursos disponibles.

5. **Fallback humano**: si la anomalía no tiene ningún evento correlacionado en el período (no hay deploys, no hay spikes de Sentry, no hay campañas), el modelo lo declara explícitamente: "No encontré eventos del sistema que correlacionen con esta caída. Necesito más contexto. Posibles fuentes: ¿hubo cambios en marketing? ¿hubo un incidente operativo no registrado? ¿cambió algo en la comunicación al usuario (emails, notificaciones)?". No inventa hipótesis sin evidencia.

---

## 7. Blueprint del workflow

```
[SCHEDULE: lunes 07:00 AM semanal | o trigger manual del PM]
      |
[FETCH_METRICS]              (determinístico — actividades Temporal)
  mixpanel_funnel_fetcher | ga4_export_fetcher | sentry_summary_fetcher
  → funnel_steps[], retention_table[], nps_cohort[]
      |
[DETECT_ANOMALIES]           (determinístico — umbral configurable)
  → anomalies[]: {metric, step, delta, severity}
  delta < umbral → reporte "sin anomalías", fin
      |
[CORRELATE_EVENTS]           (determinístico — cruce temporal)
  → correlated_events[]: {type, date, description, overlap_score}
      |
[DIAGNOSE_FUNNEL_DROP]       ← agéntico (solo si hay anomalía en funnel)
  LLM: (anomalies, correlated_events, tenant_context)
  → {hypothesis_main, hypothesis_alt[], confidence, evidence_used}
      |
[EXPLAIN_RETENTION_DROP]     ← agéntico (solo si hay anomalía en retención)
  LLM: (retention_table, cohort_metadata, deploy_history, nps_cohort)
  → {explanation, cohort_segments_affected, suggested_deep_dive}
      |
[PRIORITIZE_HYPOTHESES]      ← agéntico
  LLM: (hypotheses, validation_cost_estimate, tenant_resources)
  → ordered_hypotheses con próximos pasos
      |
[SUGGEST_EXPERIMENTS]        ← agéntico
  LLM: (top_hypothesis, tenant_analytics_stack)
  → experiments[]: {description, tracking_event, method, estimated_effort}
  si no hay contexto suficiente → NEEDS_HUMAN_CONTEXT flag
      |
[BUILD_DIAGNOSTIC_REPORT]    (determinístico — template Markdown)
  → Notion page | email | Slack thread
```

### Tools necesarias (referencia SHARED §3.6)

- `sql_query` (consultar eventos almacenados en warehouse del tenant)
- `fetch_csv` (exportar de Mixpanel / GA4 si no hay API directa)
- `write_report` (persistir diagnóstico como artefacto con `kind: md`)
- `post_slack_message` (resumen de anomalías en canal de producto)
- `send_email` (reporte completo al PM)

---

## 8. Salida y entrega

**Reporte semanal de uso** (Notion page o email):

```
ANÁLISIS DE USO — TiendaBox | Semana 20 de 2026
Generado: 2026-05-16 07:12

────────────────────────────────────────
FUNNEL: Onboarding Vendedor v2
────────────────────────────────────────
Paso                    | W18  | W19  | Δ
─────────────────────────|─────|──────|──────
1. Registro             | 100% | 100% |  —
2. Verificación email   |  83% |  81% | -2%
3. Primera publicación  |  61% |  45% | -16% ⚠
4. Primera venta        |  22% |  20% |  -2%

ANOMALÍA DETECTADA en paso 3 (umbral: -15%)

────────────────────────────────────────
DIAGNÓSTICO (hipótesis)
────────────────────────────────────────
HIPÓTESIS PRINCIPAL (confianza: 78%):
  El deploy del 2026-05-12 cambió el formulario de publicación:
  se añadió el campo obligatorio "categoría arancelaria" que los
  vendedores no saben cómo rellenar. Evidencia: spike de 23 errores
  en /api/publicaciones/validate entre el 12 y el 14 de mayo.

HIPÓTESIS ALTERNATIVA (confianza: 35%):
  La campaña de Facebook del 11 de mayo trajo usuarios nuevos
  sin experiencia en e-commerce (landing page dirigida a "emprendedores
  sin tienda online"). Perfil diferente del vendedor habitual.
  Sin datos de LTV por canal para confirmar.

────────────────────────────────────────
PRÓXIMOS PASOS SUGERIDOS
────────────────────────────────────────
1. [ALTA PRIORIDAD] Revisar si el campo "categoría arancelaria"
   puede hacerse opcional o agregar un tooltip explicativo.
   Validación: comparar conversión en paso 3 la semana siguiente.

2. [MEDIA PRIORIDAD] Segmentar funnel por canal de adquisición
   (orgánico vs. campaña) para la semana W19.
   Requiere: añadir propiedad "utm_source" al evento de publicación.

────────────────────────────────────────
RETENCIÓN: sin anomalías esta semana (retención D7: 64%)
NPS último mes: 42 (promotores 55%, detractores 13%) — sin cambio significativo
────────────────────────────────────────
```

---

## 9. Cómo se vende

**Gancho**: "¿Tu funnel cayó esta semana y no sabes por qué? Este agente cruza tus métricas, tus deploys y tus errores, y te dice la hipótesis más probable antes de que empiece la daily."

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Starter | 1 funnel, retención D7/D30, reporte semanal email | 150–300 USD/mes |
| Profesional | 3 funnels, retención + cohortes, diagnóstico con hipótesis, correlación deploy/Sentry | 400–700 USD/mes |
| SaaS B2B LATAM | Multi-tenant, funnels custom, integración Mixpanel + GA4 + Sentry + GitHub, NPS por cohorte | 600–1 200 USD/mes |

Setup (configurar funnels del tenant, definir eventos de activación para retención, umbral de anomalía): 800–2 000 USD una vez.

> [!nota]
> Este agente es el complemento de F-PRD-01 (análisis de feedback): F-PRD-01 dice *qué piden los usuarios*, F-PRD-04 dice *cómo los usan*. Juntos dan la visión de voz del cliente y comportamiento real. El bundle tiene precio preferencial.

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Correlación confundida con causalidad** (el modelo presenta una correlación como causa) | El PM hace un cambio equivocado y no resuelve el problema real | El reporte usa siempre el lenguaje "correlaciona con" o "hipótesis", nunca "fue causado por". El modelo incluye el nivel de confianza (%) en cada hipótesis. |
| **Datos de baja calidad en tracking** (eventos mal implementados, duplicados, propiedades faltantes) | El análisis es inválido desde la base | El agente incluye una sección `CALIDAD DE DATOS`: si detecta eventos con tasa de null > 20% en propiedades clave, lo reporta antes del diagnóstico. |
| **PII en eventos de analytics** | Datos de usuarios filtrados en el sistema de análisis | El pipeline de ingesta aplica hash a `user_id` y verifica que las propiedades de eventos no contengan email, nombre o CC. GA4 y Mixpanel tienen protección nativa; la capa extra protege los exports. |
| **Falsa alarma de anomalía** (caída explicada por estacionalidad conocida) | El PM pierde tiempo investigando algo que es normal | El tenant puede configurar "períodos de exclusión" (e.g., feriados locales, cierres de mes) donde el umbral de anomalía se sube automáticamente. |
| **El modelo no tiene contexto de negocio suficiente** | Hipótesis irrelevantes para el contexto del tenant | El tenant carga un documento de contexto en onboarding: modelo de negocio, segmentos de usuario, ciclo de compra típico. Este documento va como bloque cacheable del system prompt del agente. |

---

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: funnel de onboarding (registro → primera compra o primera venta), retención D1/D7/D30, cohortes por canal de adquisición (orgánico, paid social, referido), NPS post-compra.

**Delta determinístico**: el funnel se segmenta por rol (comprador vs. vendedor) antes del análisis. Un mismo evento de "registro" tiene funnels distintos según el rol. La segmentación es por propiedad `user_type` del evento — determinística.

**Delta agéntico**: el diagnóstico de caída de conversión en e-commerce requiere considerar factores externos (temporada, campañas de competidores, eventos de calendario como Hot Sale, Buen Fin, CyberMonday LATAM) que el modelo debe infererir desde el contexto del tenant y la fecha.

**Regulación**: ninguna específica. Protección de datos del consumidor (Ley 1581 Colombia, LGPD Brasil, LFPDPPP México) aplica a los datos de comportamiento si contienen PII.

**Precio tier profesional**: 500–700 USD/mes.

### Instancia 2 — Fintech / Servicios financieros (`cooppopular`)

**Datos típicos**: funnel de solicitud de crédito (registro → solicitud → aprobación → desembolso → primer pago), retención del módulo de pagos y crédito a 30/60/90 días, cohortes por producto (crédito de consumo vs. microcrédito), NPS post-desembolso.

**Delta determinístico**: el funnel de crédito tiene steps adicionales que son regulatorios (verificación de identidad, consulta de burós de crédito, firma digital). Cada step tiene tiempo máximo permitido por regulación. El agente mide y alerta si los tiempos promedio se acercan a los límites — esto es determinístico, con regla cerrada.

**Delta agéntico**: en fintech, una caída de retención en el módulo de pagos puede ser señal de fraude (usuarios que completan el onboarding pero no usan el servicio porque era una cuenta mula) o señal de UX pobre. Distinguir las dos hipótesis requiere cruzar con datos de comportamiento de riesgo — el modelo lo hace, pero con flag `REQUIRES_RISK_REVIEW` para el equipo de compliance.

**Regulación**: SFC (Colombia), CNBV (México), SBS (Perú). Retención de datos de comportamiento: mínimo 5 años. Anomalías en funnel de crédito pueden requerir reporte regulatorio si afectan a usuarios protegidos. El agente no decide si reportar — lo escala al equipo legal con el contexto.

**Precio tier profesional**: 700–1 200 USD/mes (compliance add-on + retención de datos extendida).

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica |
|--------|-----------|
| **E01** — Anthropic SDK tool loop | El loop de diagnóstico: el modelo llama a `sql_query(funnel_data, tenant)` para inspeccionar los datos de pasos específicos antes de proponer hipótesis. El tool result alimenta el razonamiento del siguiente turno. |
| **E02** — LangGraph StateGraph | El workflow de análisis se modela como grafo: `ingest → detect_anomaly → (si anomalía) → correlate → diagnose → suggest`. El nodo `detect_anomaly` es determinístico (Python); `diagnose` y `suggest` son agénticos (model). El grafo separa los dos tramos con claridad. |
| **D04** — Observabilidad Phoenix | Span por nodo del grafo de análisis; métrica de `hypothesis_acceptance_rate` (qué porcentaje de hipótesis del agente el PM marca como "válida" tras investigar). Si cae < 50%, el modelo necesita más contexto del tenant. |
| **E05** — Temporal workflows | El análisis semanal corre como schedule Temporal: `cron: "0 7 * * 1"` por tenant. `idempotency_key = "usage_analysis:{tenant_id}:{week}"` evita duplicados si el workflow se reintenta. Los steps de ingesta son activities con retry policy. |
| **C03** — Multitenancy | Los datos de analytics nunca se mezclan entre tenants. La query a la base de datos del agente siempre lleva `WHERE tenant_id = :tenant_id`. El módulo C03 enseña por qué olvidar ese filtro es el bug de seguridad #1 — aplica directamente aquí. |
| **A07** — Async con asyncio | Las tres llamadas de ingesta (Mixpanel + GA4 + Sentry) corren en paralelo con `asyncio.gather` para reducir la latencia del análisis de ~90s a ~30s. El módulo A07 enseña exactamente ese patrón. |

---

## 13. Errores típicos

**1. Correlación presentada como causalidad.**
*Síntoma*: el reporte dice «el deploy del martes causó la caída del funnel en el paso 3»; el PM revierte el deploy y la conversión no mejora porque la causa real era una campaña que trajo usuarios de baja calidad.
*Causa raíz*: el nodo `DIAGNOSE_FUNNEL_DROP` usó lenguaje causal en lugar de lenguaje de hipótesis.
*Cómo evitarlo*: el system prompt del nodo prohíbe expresamente las frases «causó», «provocó», «fue causado por». Solo se permiten «correlaciona con», «hipótesis principal», «coincide temporalmente con». El reporte incluye el nivel de confianza (%) de cada hipótesis. El PM decide si validar antes de actuar.

**2. Anomalía detectada durante período de exclusión conocido.**
*Síntoma*: el funnel cae un 25% la semana de Semana Santa; el agente manda alerta de anomalía y el PM pierde tiempo investigando algo que es estacionalidad normal.
*Causa raíz*: el tenant no configuró los períodos de exclusión en la configuración del agente.
*Cómo evitarlo*: el onboarding requiere definir `exclusion_periods` (feriados locales, cierres de mes, campañas estacionales conocidas). Durante esos períodos el umbral de anomalía se duplica automáticamente. Si no hay `exclusion_periods` configurados, el reporte advierte que el análisis no tiene en cuenta estacionalidad.

**3. Análisis basado en tracking con eventos mal implementados.**
*Síntoma*: el funnel paso 3 muestra una caída del 40%, pero el problema es que el evento `primera_publicacion` dejó de dispararse después de un deploy — el fallo es de tracking, no del producto.
*Causa raíz*: el nodo `DETECT_ANOMALIES` no tiene una validación de calidad de datos antes de generar hipótesis.
*Cómo evitarlo*: el nodo incluye una sección `CALIDAD DE DATOS` antes del diagnóstico: si la tasa de `null` en propiedades clave supera el 20%, o si el volumen de eventos de un paso cae > 50% de forma abrupta, se reporta como posible falla de tracking antes de proponer hipótesis de producto. El PM verifica el tracking antes de investigar el producto.

**4. Hipótesis propuesta sin contexto suficiente (alucinación de diagnóstico).**
*Síntoma*: el agente propone «posible impacto de estacionalidad por el Día de la Madre» para una caída que ocurrió en octubre; el diagnóstico no tiene sentido pero el PM confía en él porque parece plausible.
*Causa raíz*: el nodo `DIAGNOSE_FUNNEL_DROP` no tiene contexto de calendario del tenant y alucinó una causa estacional.
*Cómo evitarlo*: si el tenant no tiene un documento de contexto cargado (modelo de negocio, calendario, segmentos), el nodo declara explícitamente `contexto_insuficiente: true` y lista qué información necesita para producir hipótesis confiables. Sin ese contexto, entrega solo las correlaciones determinísticas sin diagnóstico agéntico.

**5. Datos de analytics con PII en propiedades de eventos.**
*Síntoma*: los eventos de Mixpanel tienen la propiedad `user_email` en el payload; el pipeline la ingesta y persiste en la tabla de eventos del agente.
*Causa raíz*: el nodo `FETCH_METRICS` no tiene scrubbing de PII sobre las propiedades de los eventos antes de almacenar.
*Cómo evitarlo*: el pipeline aplica hash a `user_id` y verifica que las propiedades de eventos no contengan email, nombre ni identificadores directos antes de persistir. La configuración del tenant en Mixpanel y GA4 debe tener activadas las opciones de anonimización nativas; la capa del agente añade una segunda verificación.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre la correlación determinística con eventos del sistema y el diagnóstico agéntico de hipótesis con el ejemplo de TiendaBox — ¿qué le da el modelo que no da la correlación?»
2. **Aplícalo a mi caso**: «Mi cliente tiene Mixpanel con tracking parcialmente implementado: algunos eventos tienen propiedades faltantes. ¿Cómo configuro la sección de calidad de datos para que el reporte sea honesto sobre las limitaciones?»
3. **Por qué falló**: «El agente propuso que la caída del funnel fue por la campaña de Facebook, pero el PM lo investigó y era un bug de tracking. ¿En qué nodo debería haber aparecido esa posibilidad como hipótesis y por qué no apareció?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Construir el pipeline de ingesta de métricas desde Mixpanel y GA4 con cálculo de anomalías estadísticas y validación de calidad de datos antes del diagnóstico.
- Diseñar la correlación determinística entre métricas de uso, deploys de GitHub y spikes de Sentry para alimentar el diagnóstico agéntico.
- Implementar los nodos agénticos de diagnóstico de funnel y retención con lenguaje de hipótesis (no causal) y niveles de confianza obligatorios.
- Configurar `exclusion_periods` y el documento de contexto del tenant para que el diagnóstico sea relevante para el modelo de negocio específico.
- Cotizar y dimensionar el servicio para retail y servicios financieros LATAM, incluyendo el add-on de compliance para fintech.

## 16. Módulos previos recomendados

| Módulo | Por qué leerlo antes |
|--------|---------------------|
| **D04** — Observabilidad | Phoenix traza cada nodo del grafo de análisis y mide `hypothesis_acceptance_rate`; sin D04 no hay forma de saber si las hipótesis del agente son útiles para el PM. Este módulo es el complemento directo de F-PRD-04. |
| **E01** — Anthropic SDK tool loop | El diagnóstico usa `sql_query(funnel_data, tenant)` para inspeccionar pasos específicos antes de concluir; E01 enseña el patrón de tool use con razonamiento multi-turno. |
| **E02** — LangGraph StateGraph | El grafo `ingest → detect_anomaly → correlate → diagnose → suggest` con nodos determinísticos y agénticos mezclados es el caso de uso canónico de E02. |
| **E05** — Temporal workflows | El schedule semanal `cron: "0 7 * * 1"` con `idempotency_key` por tenant y week es el patrón de E05 aplicado directamente; sin entender Temporal el workflow duplica análisis en retries. |
| **C03** — Multitenancy | Los datos de analytics nunca se mezclan entre tenants; el `WHERE tenant_id = :tenant_id` obligatorio en cada query es el patrón central de C03 y el bug de seguridad más frecuente si se omite. |
