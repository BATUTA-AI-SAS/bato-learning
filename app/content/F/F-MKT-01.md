---
ext_id: F-MKT-01
slug: postmortem-campanas-roas
track: F
dept: MKT
ord: 201
title: "Post-mortem de campañas digitales (atribución y ROAS)"
summary: "Agente que consolida datos de Meta Ads y Google Ads, calcula ROAS por canal con atribución configurable, e identifica hipótesis de causas y próximos tests."
related_modules: [A06, B02, C01, D04, E01]
industries_instanced: [retail, serv-prof]
tenants_in_examples: [tiendabox, consultorabc]
big_corp_vendors: [Adobe Analytics, GA4 360, Funnel.io]
latam_tools: [ga4, meta-ads-manager, looker-studio]
key_concepts: [ROAS, atribución-last-click, atribución-multi-touch, payback, incrementalidad, CAC]
estimated_minutes: 45
deterministic_share: 0.6
version: 1
---

## 1. Problema operativo

La directora de marketing de TiendaBox Retail invierte 40 000 USD al mes en Meta Ads y Google Ads combinados. Al final de cada campaña, el reporte que produce su equipo toma tres días de trabajo manual: descargar CSVs de tres plataformas, pegarlos en un Excel, calcular el ROAS en una tabla pivot, y escribir un párrafo de «conclusiones» que suele ser descriptivo sin ser diagnóstico. No hay tiempo para identificar qué causó la caída del ROAS en la semana 3, ni para proponer un test que valide la hipótesis.

En Consultora ABC el presupuesto es 5 000 USD al mes en LinkedIn Ads y Google Search, pero el problema es el mismo: nadie sabe si los leads generados por LinkedIn se cierran mejor o peor que los de Google, porque esa análisis cruzada tarda más de lo que vale hacerla manualmente.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|---|---|---|
| **Adobe Analytics + Attribution IQ** | Atribución multi-touch sobre todos los canales digitales, análisis de customer journey, integración con Adobe Experience Cloud. | 100–300 USD/user/mes; impl. 50k–200k USD |
| **GA4 360** | Versión enterprise de Google Analytics: data retention ilimitada, BigQuery export, integraciones con DV360 y Search Ads 360. | 150 000 USD/año (aproximado) |
| **Funnel.io** | Agregador de datos de marketing: conecta 500+ fuentes (Meta, Google, TikTok, LinkedIn...) y unifica en un data warehouse. | 1 200–8 000 USD/mes según fuentes y volumen |

La PYME usa la versión gratuita de GA4 (con 14 meses de retención de datos), Meta Ads Manager y Google Ads directo. No tiene Funnel.io ni un equipo de datos.

## 3. PYME LATAM realista

TiendaBox accede a sus datos así:
- **Meta Ads Manager**: exports CSV por campaña/adset/ad. En marzo 2026, Meta eliminó las ventanas de atribución de 7 días view y 28 días view; solo quedan 1-day click y 7-day click. Los datos de conversión bajan 40–60% respecto a pre-iOS17 sin Conversions API configurada.
- **Google Ads**: reporte de campañas exportado a Sheets o descargado manualmente. Datos de conversión dependientes de que Google Tag Manager esté bien configurado.
- **GA4 gratuito**: sesiones, fuente/medio, conversiones de objetivo. Sin exportación a BigQuery en versión free.
- **Herramienta BI**: Looker Studio gratuito, conectado manualmente a Sheets.

Sin un data pipeline. Sin un data warehouse. Los datos se pegan en Excel por un analista junior.

## 4. Datos típicos

| Campo | Fuente | Frecuencia | Ejemplo de fila |
|---|---|---|---|
| `campaign_id` | Meta Ads / Google Ads | por campaña | `"camp_meta_retargeting_mayo"` |
| `platform` | origen | por fila | `"meta"` / `"google_search"` |
| `period_start` | reporte | por campaña | `"2026-05-01"` |
| `period_end` | reporte | por campaña | `"2026-05-15"` |
| `spend_usd` | plataforma | diario | `8420.50` |
| `impressions` | plataforma | diario | `1240000` |
| `clicks` | plataforma | diario | `18300` |
| `conversions` | plataforma (atribución nativa) | diario | `142` |
| `revenue_usd` | plataforma (atribución nativa) | diario | `38900` |
| `revenue_crm_usd` | CRM (deals cerrados con fuente = campaña) | semanal | `28400` (diferencia con plataforma) |
| `ctr` | calculado | por fila | `0.0148` |
| `cpc_usd` | calculado | por fila | `0.46` |
| `cpa_usd` | calculado | por fila | `59.3` |
| `roas_platform` | calculado | por fila | `4.62` |
| `roas_crm` | calculado | por fila | `3.37` |

**ROAS (Return on Ad Spend)**: `revenue / spend`. Si gastas 8 420 USD y atribuyes 38 900 USD en ventas → ROAS = 4.62×. La diferencia entre ROAS de plataforma y ROAS de CRM es la brecha de atribución.

**CAC (Customer Acquisition Cost)**: `spend / new_customers_acquired`. Métrica complementaria: cuánto cuesta traer un cliente nuevo (no una venta recurrente).

**Payback**: tiempo en meses para recuperar el CAC con el MRR del cliente. Si CAC = 400 USD y MRR = 100 USD, payback = 4 meses.

## 5. Tramos determinísticos

1. **Ingestión y unificación de reportes**: leer CSVs de Meta Ads + Google Ads (vía `fetch_csv` o `fetch_excel`). Normalizar a schema común: `{campaign_id, platform, date, spend, impressions, clicks, conversions, revenue}`. Suma por período si los datos vienen diarios.

2. **Cálculo de métricas por campaña y canal**:
   - `ROAS = revenue_platform / spend`
   - `CTR = clicks / impressions`
   - `CPC = spend / clicks`
   - `CPA = spend / conversions`
   - `conversion_rate = conversions / clicks`
   Todo en Python/SQL. Sin LLM.

3. **Comparación ROAS plataforma vs ROAS CRM**: calcular la brecha de atribución por canal. Si Meta reporta 4.62× pero el CRM atribuye 3.37× al mismo canal en el mismo período, la diferencia (1.25×) es la sobreatribución de Meta (doble-conteo con Google). Esta discrepancia se calcula con regla cerrada.

4. **Análisis de variación semanal**: `delta_roas = roas_week_n - roas_week_n-1`. Si delta < -20%, flag `performance_drop`. Regla fija.

5. **Benchmark vs períodos anteriores**: comparar ROAS de esta campaña vs la campaña equivalente del período anterior (mismo producto, mismo canal). Delta porcentual.

6. **Segmentación por adset/ad**: el ROAS agregado de una campaña puede ocultar que un adset destruye valor mientras otro lo crea. La segmentación hasta el nivel de ad es determinística — es puro agregado.

## 6. Tramos agénticos

1. **Identificación de hipótesis de causa de la caída de ROAS.**
   *Por qué no es regla*: el sistema puede detectar que el ROAS cayó 30% en la semana 3. Pero no puede determinar si fue por saturación de audiencia, cambio en el algoritmo de Meta (el update de atribución de marzo 2026 afectó muchas cuentas), aumento de CPM por temporada, o un anuncio creativo que se agotó. El modelo lee los datos granulares (impresiones, frecuencia, CPM, CTR por creative) y propone la hipótesis más probable con evidencia.

2. **Atribución contextual cuando el cliente pasó por múltiples touchpoints.**
   *Por qué no es regla*: la atribución last-click es una mentira acordada: asigna todo el crédito al último canal antes de la conversión. Un cliente que vio el anuncio de TiendaBox en Meta 3 veces, hizo clic en Google Search y compró → Google se lleva el 100% del crédito. El modelo lee el journey completo del cliente (si GA4 tiene los datos de sesiones multi-fuente) y propone una distribución de crédito más razonable. No es exacta, pero es mejor que last-click.

3. **Propuesta de próximo test A/B o acción de optimización.**
   *Por qué no es regla*: la hipótesis determina el test, y las hipótesis son abiertas. Si la causa es saturación de audiencia → test: expandir audiencia lookalike al 3%. Si la causa es creative fatigue → test: rotar 3 nuevos creativos. Proponer el test correcto requiere razonamiento sobre el contexto, no una regla.

> [!cuidado]
> El agente distingue entre «ROAS plataforma» y «ROAS CRM» en todos sus outputs. Nunca consolida los dos sin declarar cuál usa. La brecha de atribución es un dato, no un error a esconder.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_ad_data] → fetch CSVs de Meta + Google + LinkedIn (determinístico)
  ↓
[normalize_schema] → mapear a schema común (determinístico)
  ↓
[compute_metrics] → ROAS, CTR, CPA, CPC por campaña/canal/semana (determinístico)
  ↓
[compute_attribution_gap] → ROAS plataforma vs ROAS CRM (determinístico)
  ↓
[flag_anomalies] → caídas > 20%, CPM spikes, CTR drops (determinístico)
  ↓
[read_creative_data] → nivel de ad: frecuencia, CTR por creative, CPM trend (determinístico: I/O)
  ↓
[hypothesize_causes] → LLM propone hipótesis de causa por anomalía (agéntico)
  ↓
[propose_tests] → LLM diseña próximo test A/B por hipótesis (agéntico)
  ↓
[draft_exec_summary] → LLM redacta resumen ejecutivo para el CEO (agéntico)
  ↓
[human_review?] → interrupt_before si presupuesto de test > threshold del tenant
  ↓
[write_report] → PDF con métricas + hipótesis + tests propuestos (determinístico)
  ↓
END
```

### Activities Temporal (job post-campaña o semanal)

- `pull_campaign_data(tenant, platform, period)` — con retry por límites de API.
- `run_postmortem_agent(tenant, campaign_ids, period)` — ejecuta el grafo.
- `deliver_postmortem_report(tenant, period, payload)` — email al equipo de marketing.
  `idempotency_key = "postmortem:{tenant}:{platform}:{period}"`

### Tools necesarias

- `fetch_csv` — reportes descargados de Meta/Google Ads.
- `fetch_excel` — si el equipo consolida en Sheets.
- `sql_query` — revenue CRM por fuente de lead (comparación con atribución de plataforma).
- `write_report` — PDF con tablas de métricas + hipótesis.
- `send_email` — entrega al equipo de marketing + CEO.

## 8. Salida y entrega

### Reporte post-campaña (PDF + email)

```
POST-MORTEM CAMPAÑA MAYO 2026 — TiendaBox Retail

RESUMEN EJECUTIVO:
El ROAS total de mayo fue 3.8× (plataforma) / 2.9× (CRM). La diferencia de 0.9×
refleja doble-conteo entre Meta y Google en el segmento de remarketing.
La caída del ROAS de Meta en la semana 3 (de 5.2× a 3.1×) se atribuye a saturación
de la audiencia de retargeting: frecuencia subió de 3.2 a 7.8 en 5 días.

MÉTRICAS POR CANAL:
| Canal | Spend | Revenue (plat) | ROAS (plat) | Revenue (CRM) | ROAS (CRM) |
|---|---|---|---|---|---|
| Meta Remarketing | 18 400 | 95 680 | 5.2× | 68 200 | 3.7× |
| Meta Prospecting | 12 200 | 28 060 | 2.3× | 19 520 | 1.6× |
| Google Search | 9 400 | 47 940 | 5.1× | 41 890 | 4.5× |
| Totales | 40 000 | 171 680 | 4.3× | 129 610 | 3.2× |

HIPÓTESIS DE CAUSA (caída semana 3, Meta):
Evidencia: frecuencia de 7.8×, CTR bajó de 2.1% a 0.8%, CPM subió 40%.
Hipótesis principal: SATURACIÓN DE AUDIENCIA. La audiencia de retargeting de
80 000 usuarios está demasiado pequeña para el presupuesto asignado.
Hipótesis secundaria: creative fatigue — el anuncio "banner verano" lleva 18 días.

PRÓXIMOS TESTS PROPUESTOS:
1. Ampliar audiencia de retargeting a LAL 1% (estimado: duplica el reach).
2. Rotar 3 creativos nuevos en Meta la primera semana de junio.
3. Reducir presupuesto Meta Prospecting (-30%) y mover a Google Performance Max.

⚠ Los tests 1 y 3 implican reasignación de presupuesto > 5 000 USD. Requieren
aprobación de la directora de marketing antes de ejecutar.
```

**Canal**: PDF adjunto en email a equipo de marketing. Resumen ejecutivo (1 página) separado para el CEO.

## 9. Cómo se vende

**Gancho**: «Tu equipo tarda 3 días en producir un reporte que describe lo que pasó. Este agente lo hace en 30 minutos y dice por qué pasó y qué hacer la próxima semana.»

**Propuesta de valor**: consolidación automática de datos de múltiples plataformas + ROAS honesto (plataforma vs CRM) + hipótesis accionables + propuesta de test.

| Tier | Qué incluye | Precio orientativo |
|---|---|---|
| Básico | Métricas determinísticas por canal + reporte visual | 150–300 USD/mes |
| Estándar | Métricas + brecha de atribución + hipótesis agénticas | 400–700 USD/mes |
| Premium | Todo + propuesta de tests + integración directa Meta/Google API + comparativa con períodos anteriores | 700–1 400 USD/mes + setup 2–5 k USD |

Setup: 2–4 semanas. Incluye: configuración de acceso API a Meta Ads y Google Ads, definición del schema de revenue en el CRM, golden set de 2 campañas históricas para validar hipótesis agénticas.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Atribución fundamentalmente rota**: iOS + privacy updates redujeron la señal de conversión de Meta 40–60%. Cualquier ROAS de plataforma está inflado. | El reporte declara explícitamente la brecha de atribución. Nunca presenta el ROAS de plataforma sin el comparativo CRM. |
| **Hipótesis incorrecta**: el modelo diagnostica saturación cuando la causa real fue un problema técnico de seguimiento (pixel roto). | Las hipótesis incluyen la evidencia que las sustenta. El equipo de marketing valida antes de ejecutar el test. |
| **Datos desactualizados**: si el equipo sube los CSVs con delay, el análisis llega tarde. | El agente reporta la fecha más reciente de los datos disponibles y avisa si los datos tienen > 5 días de antigüedad. |
| **Costos de API**: Meta Ads API y Google Ads API tienen límites. Un pull demasiado frecuente puede consumir el rate limit. | El job corre 1 vez por semana o post-campaña. Configurar retry con backoff. |
| **PII en datos de campaña**: los datos de audiencia de Meta pueden contener segmentaciones con datos sensibles (intereses, comportamientos). | El agente solo procesa métricas agregadas (spend, impressions, conversions), nunca datos a nivel de usuario individual. |

> [!cuidado]
> **Fallback humano**: si el agente no puede identificar una hipótesis de causa (datos insuficientes, falta de granularidad por creative, período < 7 días), entrega el reporte determinístico sin hipótesis y marca `análisis causal = requiere revisión manual del equipo de marketing`. No inventa causas.

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 3–5 canales activos (Meta, Google, TikTok Ads, email), presupuesto 15 000–80 000 USD/mes, campañas continuas con picos estacionales. Conversiones son transacciones directas (e-commerce), fácilmente medibles.

**Delta determinístico**: el ROAS se segmenta también por producto/categoría (no solo por canal). Un ROAS global de 3.5× puede esconder que la categoría «electrónica» tiene ROAS 1.8× (pierde dinero) y «ropa» tiene 6.2×.

**Delta agéntico**: el modelo detecta patrones estacionales en los datos históricos y advierte si el ROAS de esta semana es bajo para la temporada vs bajo en términos absolutos. Un ROAS de 2.5× en temporada baja puede ser bueno; en Black Friday es un desastre.

**Regulación**: datos de conversión deben cumplir las nuevas políticas de Meta (Conversions API obligatoria para atribución confiable desde 2025). El agente detecta si el tenant no tiene Conversions API configurada y lo advierte.

**Precio orientativo**: 500–1 000 USD/mes.

### Instancia 2 — Servicios profesionales (`consultorabc`)

**Datos típicos**: 1–2 canales (LinkedIn Ads, Google Search), presupuesto 3 000–10 000 USD/mes. Las conversiones son leads (formularios, calls), no transacciones directas. El revenue real se conoce semanas o meses después en el CRM.

**Delta determinístico**: el ROAS de plataforma es irreal (LinkedIn atribuye conversiones que el CRM no confirma). El análisis principal es CPL (Costo por Lead) y cCPL (Costo por Lead Calificado, definido por el vendedor). `ROAS real = revenue_crm_de_deals_cerrados / spend_del_período_de_captación`.

**Delta agéntico**: el modelo cruza el canal de adquisición del lead (LinkedIn vs Google) con la tasa de cierre en el CRM. Si los leads de LinkedIn cierran el 18% y los de Google cierran el 8%, pero el CPC de LinkedIn es el triple, el ROAS real puede ser similar. Esa comparativa requiere integrar datos de dos sistemas distintos.

**Regulación**: LinkedIn Ads tiene políticas estrictas sobre atribución de datos de audiencia profesional. No exportar datos de targeting de LinkedIn a sistemas externos.

**Precio orientativo**: 300–600 USD/mes.

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de ese módulo |
|---|---|
| **A06** — Clases, dataclasses | `CampaignMetrics`, `AttributionGap`, `PostmortemReport` como dataclasses. La jerarquía de métricas (campaign → adset → ad) se modela con composición. |
| **B02** — FastAPI a profundidad | Endpoint que recibe el upload de CSVs del equipo de marketing (multipart form) y dispara el análisis. Validación del formato de CSV antes de procesar. |
| **C01** — SQLAlchemy async | `campaign_metrics_repo` persiste las métricas por `(tenant, campaign_id, period)`. Permite comparar esta campaña vs la equivalente del trimestre anterior. |
| **D04** — Observabilidad | Phoenix traza `hypothesize_causes` y `draft_exec_summary`. Detectar si el modelo propone siempre la misma hipótesis (sesgo de calibración). |
| **E01** — Anthropic SDK | Prompt caching del system prompt con la definición de ROAS + benchmarks de industria del tenant + histórico de campañas. El dataset de la campaña actual va en el mensaje dinámico. |

## 13. Errores típicos

**1. Comparar ROAS de plataforma como si fuera ROAS real.**
*Síntoma*: el reporte final presenta un ROAS de 4.6× sin mencionar que el CRM atribuye 3.1×; el equipo de marketing toma decisiones de inversión sobre el número inflado.
*Causa raíz*: el nodo `draft_exec_summary` usó `roas_platform` en lugar de presentar ambos valores con la brecha.
*Cómo evitarlo*: el sistema prompt del agente prohíbe presentar un único ROAS sin declarar la fuente. La plantilla del reporte tiene dos columnas fijas: `ROAS (plataforma)` y `ROAS (CRM)`. Si `roas_crm` no está disponible, el campo se muestra como `N/D — requiere integración CRM` y no se suprime.

**2. Hipótesis de causa sin evidencia suficiente (alucinación de diagnóstico).**
*Síntoma*: el agente concluye «el ROAS cayó por saturación de audiencia» pero los datos de frecuencia no muestran ningún spike; la hipótesis es plausible pero no está respaldada en los datos disponibles.
*Causa raíz*: el nodo `hypothesize_causes` no recibió los datos granulares de creative y frecuencia, o el modelo generalizó un patrón de campañas previas sin verificar que aplica a esta.
*Cómo evitarlo*: el nodo exige que cada hipótesis cite la evidencia específica del dataset actual. Si la confianza del modelo es < 0.6, el reporte marca esa hipótesis como `[hipótesis especulativa — validar con el equipo]`. No se presentan hipótesis sin soporte empírico.

**3. Período de análisis demasiado corto para sacar conclusiones.**
*Síntoma*: el agente genera el post-mortem con 4 días de datos porque la campaña acaba de pausarse; las métricas son estadísticamente inestables y las hipótesis son ruido.
*Causa raíz*: no hay validación del período mínimo antes de correr el análisis agéntico.
*Cómo evitarlo*: el nodo `compute_metrics` verifica que el período tenga al menos 7 días y un mínimo de 300 conversiones antes de habilitar `hypothesize_causes`. Por debajo de esos umbrales, entrega solo las métricas determinísticas con aviso `análisis causal no disponible — datos insuficientes`.

**4. Riesgo legal por contenido auto-publicado sin revisión.**
*Síntoma*: el agente genera y publica automáticamente el resumen ejecutivo con los «próximos tests propuestos» que incluyen reasignación de presupuesto, y ese texto llega a un cliente externo sin que nadie lo haya aprobado.
*Causa raíz*: el nodo `[human_review?]` tiene el `interrupt_before` desactivado o el threshold de presupuesto está configurado demasiado alto.
*Cómo evitarlo*: cualquier output que mencione reasignación de presupuesto, cancelación de canales, o cambios de estrategia requiere aprobación del responsable de marketing antes de salir del sistema. El agente nunca toma acciones de gasto sin aprobación documentada. Registrar `approved_by` y timestamp en el log de cada reporte enviado.

**5. Datos de campaña con PII no scrubbeados.**
*Síntoma*: los CSVs de Meta Ads exportados manualmente contienen nombres o emails de custom audiences que el pipeline procesa y persiste en la base de datos del agente.
*Causa raíz*: el nodo `ingest_ad_data` no tiene un paso de scrubbing de PII antes de almacenar.
*Cómo evitarlo*: el pipeline solo persiste métricas agregadas (`spend`, `impressions`, `conversions`, `revenue`) y no almacena filas con identificadores de usuario. Verificar en el ingest que el CSV no tenga columnas `email`, `phone`, `name` antes de procesarlo.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre ROAS de plataforma y ROAS de CRM con el ejemplo de TiendaBox — ¿por qué siempre hay una brecha y cuál debo usar para tomar decisiones?»
2. **Aplícalo a mi caso**: «Mi cliente tiene Google Ads y Meta Ads pero no tiene CRM integrado. ¿Cómo configuro el agente para que el post-mortem sea útil sin el ROAS de CRM?»
3. **Por qué falló**: «El agente propuso saturación de audiencia como hipótesis principal, pero el equipo comprobó que el pixel de Meta estaba roto esa semana. ¿En qué nodo del workflow debería haberse detectado ese problema?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Construir el pipeline de ingestión y normalización de datos de Meta Ads y Google Ads a un schema unificado.
- Calcular ROAS, CTR, CPA y la brecha de atribución plataforma-CRM con código determinístico.
- Diseñar los nodos agénticos de hipótesis y propuesta de tests con guardrails que exigen evidencia antes de presentar una conclusión.
- Configurar el `interrupt_before` para que ninguna reasignación de presupuesto salga del sistema sin aprobación del responsable de marketing.
- Cotizar y dimensionar el servicio para retail y servicios profesionales LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué leerlo antes |
|--------|---------------------|
| **A06** — Clases y dataclasses | `CampaignMetrics` y `AttributionGap` se modelan como dataclasses; entender composición evita acoplar la lógica de cálculo al reporte. |
| **C01** — SQLAlchemy async | La persistencia de métricas por `(tenant, campaign_id, period)` y la consulta de benchmarks históricos usan los patrones del repositorio async de C01. |
| **D04** — Observabilidad | Phoenix traza `hypothesize_causes` y detecta si el modelo repite siempre la misma hipótesis; sin D04 no hay forma de auditar la calidad del diagnóstico. |
| **E01** — Anthropic SDK | El prompt caching del contexto del tenant (benchmarks de industria, histórico de campañas) es el patrón central de esta ficha. |
