---
ext_id: F-VTA-02
slug: forecast-cierre-q
track: F
dept: VTA
ord: 2
title: "Forecast de cierre del trimestre por vendedor y segmento"
summary: "Agente que combina probabilidades por etapa con calibración del historial del vendedor para producir un forecast ajustado y accionable."
related_modules: [A06, C01, D04, E01, E05]
industries_instanced: [retail, serv-prof]
tenants_in_examples: [tiendabox, consultorabc]
big_corp_vendors: [Clari, Salesforce Einstein, BoostUp]
latam_tools: [hubspot, pipedrive, excel]
key_concepts: [pipeline-coverage, win-rate, sandbagging, calibración, forecast-agéntico, ARR]
estimated_minutes: 45
deterministic_share: 0.45
version: 1
---

## 1. Problema operativo

El gerente general de TiendaBox Retail necesita saber, cada lunes, cuánto va a cerrar el equipo comercial este trimestre. Sus tres vendedores usan Pipedrive. Uno es sistemáticamente optimista (dice que va a cerrar todo y cierra el 40%). Otro es conservador (dice que cierra tres deals y cierra los tres más uno extra). El tercero es impredecible. El CEO hace sus propias correcciones mentales, pero sin base de datos. Cuando el forecast falla en 30%, la empresa sobre-compra inventario o deja de contratar.

En Consultora ABC el problema es el mismo pero con un giro: el forecast afecta la capacidad de entrega. Si el equipo de ventas promete 8 proyectos y operaciones solo puede absorber 5, hay un problema de staffing que se descubre dos semanas tarde.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|---|---|---|
| **Clari** | Agrega señales de CRM, email y actividad del rep; genera forecast por rep, segmento y empresa. Afirma 98% de precisión en la segunda semana del trimestre. | 100–125 USD/user/mes; mínimo ~10 seats |
| **Salesforce Einstein Opportunity Scoring** | Score de probabilidad de cierre por deal basado en historial y actividad. Forecast roll-up en Salesforce Forecasting | Incluido en Sales Cloud Einstein; paquete desde 40 000 USD/año |
| **BoostUp** | Revenue intelligence más ligero que Clari; foco en forecast accuracy y deal risk | Precios no públicos; estimado 60–100 USD/user/mes |

Estas plataformas requieren que el CRM tenga al menos 12–24 meses de historial de deals cerrados con stage history limpio. Sin esa data, el modelo no tiene con qué calibrarse.

## 3. PYME LATAM realista

TiendaBox usa HubSpot Starter. El historial de deals cerrados está, pero la limpieza es cuestionable: deals arrastrados de Q a Q sin actualizar la fecha de cierre esperada, etapas saltadas, valores modificados el día que se cierra. Consultora ABC usa Pipedrive con exportación semanal a Google Sheets donde el dueño hace el forecast a mano, con una columna «factor de corrección» por vendedor.

La PYME no tiene un equipo de RevOps. El «modelo» actual son dos celdas de Excel.

## 4. Datos típicos

| Campo | Fuente | Frecuencia | Ejemplo de fila |
|---|---|---|---|
| `deal_id` | CRM | por deal | `"DEAL-4820"` |
| `owner_id` | CRM | por deal | `"rep_marta"` |
| `stage` | CRM | tiempo real | `"propuesta enviada"` |
| `close_date_expected` | CRM | por deal | `"2026-06-30"` |
| `deal_value_usd` | CRM | por deal | `45000` |
| `stage_history` | CRM / export | batch semanal | `[{stage: discovery, date: 2026-03-10}, {stage: demo, date: 2026-03-24}, ...]` |
| `days_in_current_stage` | calculado | diario | `18` |
| `rep_historical_win_rate_by_stage` | calculado desde historial | semanal | `{discovery: 0.3, demo: 0.5, proposal: 0.62}` |
| `rep_forecast_vs_actual_bias` | calculado | por trimestre cerrado | `+0.25` (sobre-estima en 25% de media) |
| `notes_last_activity` | CRM | por actividad | `"Cliente pidió 30 días adicionales por proceso de aprobación interna"` |

Stage history se puede extraer de HubSpot con la API de deals properties history, o de Pipedrive con activities log.

## 5. Tramos determinísticos

1. **Cálculo de probabilidad base por etapa**: tabla de win-rate histórico del tenant por etapa (`discovery → 25%, demo → 45%, proposal → 60%, negotiation → 80%`). Multiplica `deal_value × prob_etapa` para cada deal activo.
2. **Filtro por fecha de cierre esperada dentro del trimestre**: excluye deals con `close_date_expected > fin_de_Q`. Deals sin fecha se marcan como `out_of_scope`.
3. **Pipeline coverage**: `sum(deal_value × prob_etapa) / target_Q`. Si coverage < 2×, el pipeline es insuficiente para cumplir el target. Alerta determinística.
4. **Segmentación por rep**: subtotales por `owner_id`. Permite ver qué parte del forecast viene de quién.
5. **Detección de deals estancados**: deals cuyo `days_in_current_stage` supera el p75 histórico de ese stage → flag `velocity_risk`.
6. **Cálculo de sesgo histórico por rep**: `rep_forecast_vs_actual_bias = mean(rep_commit - actual_closed)` sobre los últimos 4 trimestres. Si un rep tiene bias > +0.2, su pipeline se descuenta en ese porcentaje. Regla cerrada, auditable.

## 6. Tramos agénticos

1. **Detección de sandbagging y wishful thinking deal a deal.**
   *Por qué no es regla*: el sesgo histórico del rep es útil en aggregate, pero un deal individual puede ser diferente. El modelo lee las notas del deal y el stage history: si un rep conservador dice «50% de probabilidad» en un deal donde el cliente preguntó por condiciones de pago y firmó NDA, el modelo puede subir ese estimado. Inversamente, si un rep optimista pone «90%» pero las últimas 3 notas son «el cliente no responde», el modelo lo baja. Ninguna regla captura esas combinaciones.

2. **Ajuste por contexto del cliente (no solo del vendedor).**
   *Por qué no es regla*: la nota «el cliente pidió 30 días adicionales por aprobación interna» puede significar deal real pero con delay, o deal muerto con excusa educada. El modelo lee el historial completo de esa cuenta y propone su hipótesis. Un cliente que siempre paga y siempre pide extensiones vs un lead nuevo que pide extensión en la primera propuesta — la probabilidad real es diferente.

3. **Generación del resumen ejecutivo del forecast.**
   *Por qué no es regla*: el CEO necesita 5 líneas de contexto, no una tabla. «El forecast de Q2 es 380 k USD ajustado. El 60% depende de dos deals de TiendaBox que están en etapa de negociación. Si alguno se cae, necesitamos activar el pipeline de reserva de Marta antes del 15 de junio.» Eso no sale de una suma.

> [!cuidado]
> El agente nunca modifica la probabilidad registrada en el CRM. Trabaja sobre una copia del dataset y produce el forecast ajustado como artifact. El vendedor y el gerente son libres de ignorarlo.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_pipeline] → pull de deals + stage_history del CRM (determinístico)
  ↓
[compute_base_forecast] → prob_etapa × valor × filtro de fecha (determinístico)
  ↓
[compute_rep_bias] → sesgo histórico por rep (determinístico)
  ↓
[read_deal_notes] → últimas notas por deal (determinístico: I/O)
  ↓
[adjust_per_deal] → LLM ajusta prob por deal leyendo notas + context rep (agéntico)
  ↓
[flag_risks] → deals con velocity_risk + deals con probabilidad ajustada < base (agéntico)
  ↓
[draft_exec_summary] → LLM redacta resumen ejecutivo del forecast (agéntico)
  ↓
[human_review?] → interrupt_before siempre (forecast es decisión gerencial)
  ↓
[write_report] → persiste forecast ajustado como artefacto (determinístico)
  ↓
END
```

### Activities Temporal (job semanal, lunes 7am)

- `pull_pipeline_snapshot(tenant, quarter)` — snapshot inmutable del pipeline.
- `run_forecast_agent(tenant, snapshot_id)` — ejecuta el grafo.
- `deliver_forecast_report(tenant, quarter, week_n, payload)` — email al CEO + gerente.
  `idempotency_key = "forecast:{tenant}:{quarter}:w{week_n}"`

### Tools necesarias

- `sql_query` — deals + stage_history desde DB del tenant.
- `fetch_excel` — si el pipeline vive en Google Sheets.
- `write_report` — forecast como PDF con tabla + resumen.
- `send_email` — entrega al CEO y gerente comercial.

## 8. Salida y entrega

### Reporte semanal (PDF + email)

```
FORECAST Q2 2026 — TiendaBox Retail — Semana 7 del trimestre

Target Q2: USD 500 000
Forecast base (prob. por etapa): USD 412 000
Forecast ajustado (calibración rep + notas): USD 348 000
Ajuste neto: -15.5% (2 deals sobre-estimados por sesgo optimista de rep Diego)

TOP DEALS EN RIESGO:
· DEAL-4820 · Andina Distribución · USD 90 000 · Negotiation
  Base: 80% · Ajustado: 55%
  Motivo: 3 notas seguidas de "cliente no responde". Último contacto hace 19 días.
  Acción sugerida: escalar a gerente de cuenta esta semana o marcarlo como lost.

· DEAL-4751 · Importadora Sur · USD 45 000 · Proposal
  Base: 60% · Ajustado: 75%
  Motivo: rep conservador (bias histórico -0.22); cliente firmó NDA y preguntó por
  condiciones de pago. Señal positiva no reflejada en el stage.

PIPELINE COVERAGE: 1.8× (por debajo del mínimo de 2×).
Recomendación: activar 2–3 oportunidades del pipeline de reserva antes del 30 de mayo.

⚠ Este forecast requiere validación del gerente comercial antes de comunicar al directorio.
```

**Canal**: PDF adjunto en email + tabla en Slack `#forecast-q2`. Siempre marcado como «requiere validación».

## 9. Cómo se vende

**Gancho**: «Tu CEO hace el forecast corriendo columnas en Excel. Este agente lo hace en 3 minutos con calibración por vendedor y lectura de deals individuales — y explica por qué ajustó cada número.»

**Propuesta de valor**: forecast semanal auditado, con las razones detrás de cada ajuste, y sin depender de que el CRM esté perfectamente actualizado.

| Tier | Qué incluye | Precio orientativo |
|---|---|---|
| Básico | Forecast determinístico (prob × valor) + pipeline coverage | 100–200 USD/mes |
| Estándar | Forecast ajustado por sesgo del rep + resumen ejecutivo agéntico | 350–600 USD/mes |
| Premium | Todo + ajuste deal a deal agéntico + alerta de riesgo Temporal | 700–1 400 USD/mes + setup 3–6 k USD |

Setup: 3–5 semanas. Incluye: extracción de historial de deals cerrados (mínimo 2 trimestres), calibración de tabla de win-rate por etapa, definición del target trimestral por rep, golden set de 10 deals para validar ajustes agénticos.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Datos históricos insuficientes**: menos de 2 trimestres de deals cerrados imposibilita la calibración. | El agente detecta tamaño de historial. Si `n_closed_deals < 20`, usa benchmarks de industria como prior y lo declara explícito en el reporte. |
| **Alucinación en ajuste de probabilidad**: el modelo sube un deal muerto porque las notas son ambiguas. | Cada ajuste incluye la frase textual que lo motivó. El gerente valida antes de usar el número. |
| **Sesgo del forecast agéntico**: si el modelo siempre ajusta hacia abajo, desmotiva al equipo. | Se reporta el `mean_adjustment_pct` del trimestre. Si el agente ajusta > ±20% de media, se revisa el prompt y el golden set. |
| **Dependencia del CRM actualizado**: deals sin stage_history no se pueden ajustar. | El agente reporta `% deals sin historia de etapas`. Umbral: si > 30%, avisa al administrador. |
| **PII**: los nombres de empresas y contactos en las notas son datos de negocio sensibles. | Todo el procesamiento ocurre dentro del entorno del tenant. Sin logs de notas en sistemas externos. |

> [!cuidado]
> **Fallback humano**: si el agente no puede generar el resumen ejecutivo (error del modelo, tokens insuficientes para el contexto, pipeline vacío), entrega la tabla determinística sin comentario narrativo y notifica al gerente que el resumen requiere revisión manual.

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 30–120 deals activos (cuentas B2B que compran al por mayor), ticket USD 10 000–200 000, ciclo 15–60 días. Stage history razonablemente limpio si usan HubSpot con pipeline automatizado.

**Delta determinístico**: el forecast se segmenta por canal (tienda física vs e-commerce vs marketplace). El win-rate varía mucho entre canales. La cobertura se mide por canal, no solo en aggregate.

**Delta agéntico**: el modelo detecta deals atados a «temporada alta» (Navidad, Día de la Madre) donde el cierre tiene una ventana dura. Si el deal no cierra antes de la ventana, se cae. Esa señal temporal no está en el stage.

**Regulación**: ninguna específica. Datos de pricing de clientes son confidenciales.

**Precio orientativo**: 350–700 USD/mes.

### Instancia 2 — Servicios profesionales (`consultorabc`)

**Datos típicos**: 40–100 deals activos, ticket USD 15 000–150 000, ciclo 30–120 días. El forecast también implica planificación de capacidad: un deal ganado consume X horas de consultor por mes.

**Delta determinístico**: además del forecast en USD, el agente calcula el forecast en horas-consultor comprometidas. Si `total_hours_forecast > capacity_available`, flag de sobre-compromiso.

**Delta agéntico**: el modelo detecta deals donde el interlocutor en la empresa cliente cambió (nuevo CFO, restructuración interna) — señal de riesgo que no aparece en el CRM.

**Regulación**: contratos con cláusulas de confidencialidad. Las notas del deal pueden contener información de NDA. No se almacenan en sistemas externos del tenant.

**Precio orientativo**: 400–800 USD/mes + setup 2–5 k USD (incluye integración de capacidad de entrega).

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de ese módulo |
|---|---|
| **A06** — Clases, dataclasses | `DealSnapshot`, `RepBias`, `ForecastResult` como dataclasses tipadas. Composición sobre herencia para los distintos modelos de forecast. |
| **C01** — SQLAlchemy async | `forecast_repo` guarda el snapshot semanal por tenant. Cada reporte es inmutable — no se sobrescribe, se versiona por `(tenant, quarter, week_n)`. |
| **D04** — Observabilidad | Phoenix traza las llamadas a `adjust_per_deal` y `draft_exec_summary`. La latencia de esas dos actividades es el costo principal del agente. |
| **E01** — Anthropic SDK | Prompt caching del system prompt con las reglas de calibración + historial del rep (cacheable, cambia semanalmente). El contexto del deal va en el mensaje dinámico. |
| **E05** — Temporal | El job semanal de forecast corre como Temporal Schedule. `idempotency_key` garantiza que si el job falla a mitad, no produce dos reportes del mismo lunes. |

## 13. Errores típicos

**1. Sobre-confianza en el forecast agéntico sin baseline determinístico documentado.**
*Síntoma*: el CEO recibe el forecast ajustado de 348 k USD, no tiene el forecast base de 412 k USD a mano, y no puede entender el ajuste ni cuestionar si tiene sentido.
*Causa raíz*: el reporte muestra solo el número final; el vendedor y el gerente no pueden auditar el razonamiento.
*Cómo evitarlo*: el reporte siempre incluye ambos números (base y ajustado) con el delta porcentual y la lista de los deals que contribuyen al ajuste; el forecast agéntico nunca se presenta solo.

**2. Scoring fugado al futuro en la calibración del sesgo del rep.**
*Síntoma*: al calcular `rep_forecast_vs_actual_bias` para el trimestre en curso, el pipeline usa deals que ya cerraron este trimestre para calibrar el sesgo; el modelo «sabe» qué pasó y ajusta en la dirección correcta sin esfuerzo real.
*Causa raíz*: el cálculo de sesgo incluye el trimestre actual en lugar de usar solo los trimestres completamente cerrados.
*Cómo evitarlo*: `rep_forecast_vs_actual_bias` se calcula exclusivamente con los `N` trimestres previos completamente cerrados (`close_date_actual < inicio_del_trimestre_actual`). Nunca mezclar datos del trimestre en curso en la calibración del modelo. Este error es silencioso: produce métricas de evaluación excelentes en backtesting pero colapsa en producción.

**3. Ajuste agéntico que desmotiva al equipo por sesgo sistemático hacia abajo.**
*Síntoma*: durante 3 semanas seguidas el agente ajusta el forecast a la baja; el equipo de ventas percibe que el sistema «siempre desconfía» de sus estimates.
*Causa raíz*: el prompt tiene un sesgo implícito hacia la prudencia («sé conservador») que se activa independientemente de las señales del deal.
*Cómo evitarlo*: monitorear `mean_adjustment_pct` semanalmente en Phoenix; si el ajuste promedio supera -20% durante más de 3 semanas consecutivas, revisar el prompt y el golden set. El agente debe ajustar hacia arriba y hacia abajo con la misma frecuencia según las señales.

**4. Deals sin stage_history ajustados con probabilidades del estado actual.**
*Síntoma*: un deal que saltó de `discovery` a `negotiation` en un día (arrastrado manualmente) recibe una probabilidad del 80% basada en la etapa actual, sin que el agente detecte la velocidad anormal.
*Causa raíz*: el nodo `adjust_per_deal` no verifica la coherencia del stage_history antes de aceptar la etapa actual como válida.
*Cómo evitarlo*: el pipeline valida que la velocidad de progreso entre etapas sea plausible (dentro de ± 2σ del histórico del tenant); deals con saltos de etapa sospechosos se marcan como `stage_history_anomaly` y van a revisión humana antes del ajuste.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «¿Cuál es la diferencia entre el forecast base determinístico y el forecast ajustado agéntico? Dame un ejemplo donde ambos diverjan en más de 30 k USD.»
2. **Aplícalo a mi caso**: «¿Cómo adaptaría el pipeline si el CRM del cliente tiene solo 1 trimestre de historial de deals cerrados, que es menos del mínimo recomendado?»
3. **Por qué falló**: «El agente subió la probabilidad de un deal que estaba muerto y el CEO tomó decisiones de contratación basado en ese forecast. ¿Qué validación faltaba y dónde la añado?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de forecast con la separación entre cálculo determinístico (prob × valor, sesgo del rep) y ajuste agéntico (lectura de notas, contexto del cliente).
- Construir el cálculo de `rep_forecast_vs_actual_bias` usando exclusivamente trimestres completamente cerrados, sin data leakage del trimestre actual.
- Implementar el snapshot inmutable del pipeline por semana para garantizar que el forecast es auditable y reproducible.
- Configurar el `human_review` como nodo obligatorio antes de comunicar el forecast al directorio.
- Dimensionar y cotizar este servicio para retail B2B y para una consultora donde el forecast también implica planificación de capacidad.

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|--------------------------------|
| **E04** — Memoria de sesión por SDR/cuenta | El historial de deals por rep y por cuenta es la base de la calibración de sesgo; sin entender cómo se persiste ese historial por `owner_id`, el cálculo de bias se recalcula desde cero en cada run. |
| **C01** — SQLAlchemy async | El `forecast_repo` guarda el snapshot semanal inmutable por `(tenant, quarter, week_n)`; entender el patrón de repositorio async es prerequisito para garantizar que los reportes son versionados, no sobrescritos. |
| **A06** — Dataclasses y Pydantic | `DealSnapshot`, `RepBias` y `ForecastResult` como dataclasses tipadas; la composición correcta de estos tipos es lo que permite el pipeline determinístico + agéntico sin mezclar capas. |
| **E05** — Temporal | El job semanal corre como Temporal Schedule con `idempotency_key`; sin este módulo, un retry puede producir dos reportes del mismo lunes con números distintos. |
