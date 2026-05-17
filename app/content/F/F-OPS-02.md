---
ext_id: F-OPS-02
slug: forecast-demanda-sku
track: F
dept: OPS
ord: 162
title: "Forecast de demanda por SKU y canal (mensual rolling)"
summary: "Modelos baseline estadísticos (Croston/SBA para intermitentes, ETS para regulares) producen el forecast base; el agente incorpora eventos extraordinarios que el modelo no puede ver y explica las variaciones al planificador."
related_modules: [A06, C01, D04, E01, E05]
industries_instanced: [retail, agro]
tenants_in_examples: [tiendabox, cafetera]
big_corp_vendors: [SAP IBP, Anaplan, o9 Solutions, Kinaxis Maestro, Blue Yonder Luminate]
latam_tools: [excel, datup, world_office, siigo]
key_concepts: [Croston-SBA, ETS, AutoARIMA, statsforecast, MAPE, wMAPE, intermittent-demand, slow-moving, seasonality, rolling-forecast]
estimated_minutes: 60
deterministic_share: 0.5
version: 1
---

## 1. Problema operativo

La planificadora de TiendaBox revisa cada mes el forecast de sus 1.200 SKUs activos. El 60% de esos SKUs tienen demanda esporádica: semanas sin ventas intercaladas con picos. El modelo de Excel que heredó —una media móvil de 3 meses— subestima los picos y sobreestima los períodos muertos. El resultado: rotura de stock en los SKUs de temporada alta y sobrestock en los de rotación lenta. Además, el lanzamiento de una línea nueva el mes próximo y una promoción 3×2 regional no caben en ningún modelo estadístico porque ocurren una vez. La planificadora pasa 2 días al mes ajustando el Excel a mano; necesita el forecast base listo en 30 minutos y que el sistema le señale exactamente qué SKUs requieren su criterio.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|--------|----------|-------------------|
| **SAP IBP** Demand | Forecast estadístico + ML, integración directa con S/4HANA, gestión de lifecycle de SKU, consensus demand | Desde 29k USD/año en starter; enterprise 100k–500k USD/año |
| **Blue Yonder Luminate Planning** | AI-driven demand planning, probabilistic forecast, gestión de promociones y eventos | Custom, 200k–1M+ USD/año; nombrado Leader Gartner Magic Quadrant 2026 |
| **Kinaxis Maestro** (ex-RapidResponse) | Concurrent planning: el forecast se actualiza cuando cambia cualquier señal upstream | 250k–1M+ USD/año |
| **o9 Solutions** | Digital Brain: integra señales externas (clima, macro, tendencias redes) con el forecast estadístico | Custom pricing, 300k–1M+ USD/año |
| **Anaplan** | Planificación conectada, Polaris engine, simulación de escenarios de demanda | 100k–500k USD/año; impl. 100k–300k |

El modelo big corp: datos históricos desde el ERP + señales externas + consenso humano en una plataforma conectada al plan de producción y compras. La PYME: Excel con una media móvil que nadie entiende cómo se calculó.

## 3. PYME LATAM realista

TiendaBox exporta ventas desde Siigo o World Office a un Excel mensual. Datup (plataforma colombiana de demand planning) ofrece modelos estadísticos sobre ese Excel a partir de 200 USD/mes, pero la integración con el plan de compras sigue siendo manual. La Cooperativa Cafetera del Valle gestiona su forecast por variedad y calidad de café con Excel pivotante sobre datos del acopio semanal, sin separar canal exportación de canal nacional.

El agente no necesita sustituir Datup ni el ERP: se asienta **sobre** la exportación de datos que el cliente ya hace y devuelve un forecast accionable con contexto narrativo.

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Histórico de ventas por SKU + canal | CSV/Excel desde ERP o POS | Mensual (pull) | 12–36 meses, 100–5000 SKUs |
| Catálogo de SKUs (activo/descontinuado/nuevo) | Excel maestro o tabla ERP | Mensual | 100–5000 filas |
| Calendario de eventos (promociones, lanzamientos, feriados, cosechas) | Excel manual del planificador | Manual / irregular | 5–30 eventos/año |
| Stock disponible y en tránsito | Tabla ERP | Semanal | 100–5000 SKUs |
| Precios históricos y descuentos | Tabla ERP o Excel | Mensual | Alineado a histórico de ventas |

**Ejemplo de fila de histórico:**

| sku | canal | periodo | unidades_vendidas | precio_unitario |
|-----|-------|---------|-------------------|----------------|
| SKU-0314 | tienda-bogota | 2026-02 | 0 | 18500 |
| SKU-0314 | tienda-bogota | 2026-03 | 47 | 18500 |
| SKU-0314 | ecommerce | 2026-03 | 12 | 17990 |

## 5. Tramos determinísticos

1. **Clasificación ABC-XYZ de SKUs**: clasificar por volumen (A/B/C) y variabilidad de demanda (X=regular, Y=variable, Z=esporádico/intermitente). La clasificación determina qué modelo se aplica. Regla cerrada sobre el histórico.

2. **Selección del modelo por clase**: AX/BX → ETS (Holt-Winters) o AutoARIMA con detección de estacionalidad; CZ/BZ → Croston SBA (Syntetos-Boylan Approximation) para intermitentes. La asignación es una tabla de decisión, no una heurística blanda.

3. **Entrenamiento y proyección con `statsforecast` (Nixtla)**: dado el histórico por SKU-canal, ajustar el modelo seleccionado y proyectar N períodos forward. `statsforecast` implementa `CrostonSBA`, `AutoETS` y `AutoARIMA` y procesa millones de series en paralelo — ejecutable en un servidor de 4 vCPU en minutos para carteras PYME.

4. **Cálculo de error histórico**: calcular MAPE y wMAPE sobre el período de hold-out (últimos 3 meses). Identificar SKUs con MAPE > 40% como candidatos a revisión manual. Regla aritmética.

5. **Agregación por canal y categoría**: sumar el forecast SKU-nivel a nivel de categoría, línea, canal. Generar la vista jerárquica que el planificador necesita para el plan de compras. Aritmética pura.

> [!nota]
> Croston SBA reduce el sesgo del Croston clásico al corregir el factor de división por demanda inter-llegada. Es el modelo recomendado para SKUs con `ADI > 1.32` (Advance Demand Interval) y `CV² < 0.49`. `statsforecast` lo implementa en `CrostonSBA` con ajuste automático de parámetros via `AutoCroston`.

## 6. Tramos agénticos

1. **Incorporar eventos extraordinarios**: el modelo estadístico no ve el lanzamiento de una nueva línea de snacks ni la campaña 3×2 del próximo mes ni la huelga de transporte que afectó ventas en febrero. El planificador declara el evento; el agente evalúa qué SKUs afecta, en qué magnitud y dirección, y ajusta el forecast base con un factor multiplicativo explicado. Justificación: el impacto de cada evento depende del contexto del canal y del cliente — no hay fórmula que lo capture sin conocer la historia del negocio.

2. **Detección de SKUs con patrón anómalo**: el MAPE alto es una señal, no un diagnóstico. El agente analiza la serie de un SKU de alto error y distingue: ¿es intermitencia reciente (cambio de patrón)?, ¿fin de vida (últimas ventas decrecientes)?, ¿error de registro (un pico aislado en el histórico que no es demanda real)?, ¿nuevo canal sin historia suficiente? Justificación: las causas tienen distintas respuestas operativas y no hay regla cerrada para distinguirlas.

3. **Narrativa mensual para el planificador**: síntesis de qué cambió respecto al mes anterior, por qué, qué SKUs requieren decisión humana y cuál es la incertidumbre del forecast. Escrita en lenguaje de negocio, no de estadística. Justificación: comunicación contextual para humano.

> [!cuidado]
> Fallback humano obligatorio: si el agente no puede justificar el ajuste de un evento con datos históricos comparables (es la primera vez que ocurre para ese tenant), debe declarar «no tengo base histórica para estimar el impacto de este evento — propongo dejarlo en cero y revisarlo manualmente» y marcar el SKU para revisión explícita. El planificador confirma o edita antes de publicar el forecast.

## 7. Blueprint del workflow

```
START
  ↓
[ingest_sales_history] → pull CSV/Excel de ventas históricas por SKU-canal
                          (determinístico, tools: fetch_excel / erp_fetch_transactions)
  ↓
[ingest_sku_catalog] → activos, descontinuados, nuevos; filtrar series < 6 meses
                        (determinístico)
  ↓
[classify_abc_xyz] → tabla ABC-XYZ por SKU-canal (determinístico)
  ↓
[select_model] → asignar ETS/AutoARIMA o CrostonSBA por clase (determinístico)
  ↓
[run_statsforecast] → entrenar y proyectar N meses rolling
                       (determinístico, CPU-bound en backend)
  ↓
[compute_error_metrics] → MAPE, wMAPE por SKU; identificar outliers > umbral
                           (determinístico)
  ↓
[detect_anomalous_skus] → analizar SKUs de alto error; clasificar causa
                           (agéntico, tool: sql_query historial)
  ↓
[incorporate_events] → ajustar forecast base con eventos del calendario
                        (agéntico, tool: fetch_excel eventos)
  ↓
[human_review?] → interrupt_before si hay SKUs nuevos, eventos de alto impacto
                   o error agregado > 30%
  ↓
[aggregate_forecast] → sumar a nivel canal / categoría / total (determinístico)
  ↓
[draft_narrative] → resumen mensual para el planificador (agéntico)
  ↓
[write_report] → forecast en XLSX + narrativa en PDF
                  (determinístico, tool: write_report)
  ↓
END
```

**Activities Temporal:**

- `ingest_sales_history(tenant, period)` — pull de datos, retry con backoff.
- `run_forecast_models(tenant, period)` — CPU-bound; timeout 10 minutos. Heartbeat cada 60 segundos.
- `run_forecast_agent(tenant, period, dataset_id)` — corre el grafo LangGraph (tramos agénticos).
- `persist_forecast(tenant, period, payload)` — idempotente con `idempotency_key = "forecast:{tenant}:{period}"`.

**Tools necesarias (referencia SHARED §3.6):**

- `fetch_excel` — histórico de ventas, catálogo de SKUs, calendario de eventos
- `erp_fetch_transactions` — ventas desde Siigo / World Office
- `sql_query` — historial de anomalías, eventos pasados, margen por SKU
- `write_report` — forecast XLSX + narrativa PDF

## 8. Salida y entrega

1. **Archivo de forecast** (XLSX): columnas `sku | canal | periodo | forecast_unidades | IC_bajo | IC_alto | modelo_usado | ajuste_evento`.
2. **Narrativa mensual** (1–2 páginas): qué cambió vs. mes anterior, top 10 SKUs con mayor variación, SKUs que requieren decisión manual.
3. **Dashboard de error** (tabla o gráfica): MAPE/wMAPE por categoría, evolución en los últimos 6 meses.

Canal: XLSX descargable + PDF por email al planificador + Slack con resumen ejecutivo.

**Mockup de fila de forecast:**

| sku | canal | periodo | forecast | IC_bajo | IC_alto | modelo | ajuste_evento |
|-----|-------|---------|----------|---------|---------|--------|--------------|
| SKU-0314 | tienda-bogota | 2026-06 | 41 | 28 | 58 | CrostonSBA | — |
| SKU-0921 | ecommerce | 2026-06 | 310 | 260 | 370 | ETS | +25% promo 3×2 semana 3 |
| SKU-1102 | tienda-bogota | 2026-06 | 0 | 0 | 4 | CrostonSBA | ⚠ fin de vida probable |

## 9. Cómo se vende

**Gancho**: «El forecast del mes te toma 2 días en Excel. Con el agente tienes el baseline listo en 30 minutos y el sistema ya te señala los 20 SKUs que necesitan tu criterio, no los 1.200.»

**Diferencial**: la narrativa que explica qué cambió y por qué — ningún modelo estadístico la genera, y es lo que el planificador necesita para justificar el plan de compras al CFO.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Básico | Forecast baseline ETS/Croston, MAPE por SKU, XLSX | 200–400 USD/mes |
| Estándar | Clasificación ABC-XYZ, ajuste de eventos manual, narrativa mensual, integración Siigo/World Office | 400–800 USD/mes |
| Avanzado | AutoARIMA multi-estacional, ajuste automático de eventos, dashboard de error, workflow Temporal mensual | 800–1500 USD/mes + setup 3–8k USD |

## 10. Riesgos

**1. Histórico con huecos o registros erróneos.**
*Síntoma*: el modelo produce forecast de 0 para un SKU porque diciembre no tiene ventas registradas (estaban en otra tabla del ERP).
*Causa*: los ceros en el histórico no distinguen «sin demanda» de «sin registro».
*Arreglo*: en el ingest, detectar meses con ventas = 0 y diferenciar cero real de cero por error de registro. Si la proporción de ceros sospechosos supera el 10% del histórico del SKU, alertar antes de entrenar.

**2. El agente sobre-ajusta el evento (amplificación).**
*Síntoma*: la planificadora declaró +15% para una promoción; el agente aplicó +40% porque en el año anterior hubo una promoción similar con ese resultado (pero ese año era temporada de fin de año — contexto distinto).
*Causa*: el agente usa el evento histórico más cercano sin considerar si el contexto es comparable.
*Arreglo*: el ajuste de evento debe mostrar la base histórica que lo sustenta. Si la base es < 2 eventos similares, el agente declara incertidumbre alta y propone un rango, no un punto.

**3. SKUs nuevos sin historia (cold start).**
*Síntoma*: el agente asigna CrostonSBA a un SKU con 2 meses de historia; el intervalo de confianza es demasiado amplio para planificar.
*Causa*: no hay umbral mínimo de historia para seleccionar modelo estadístico.
*Arreglo*: SKUs con < 6 meses de historia van a un modelo especial: promedio de la categoría + ajuste del planificador. El agente los marca explícitamente como «cold start — requiere criterio humano».

**4. Forecast correcto en promedio, inútil en la práctica.**
*Síntoma*: el MAPE agregado es 8%, pero hay un SKU clase A con error de 200% que causa un stockout crítico.
*Causa*: se reporta solo el error agregado, no por SKU individual.
*Arreglo*: reportar MAPE tanto agregado como por SKU. Alertar si algún SKU clase A tiene MAPE > 30%.

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce multicanal (`tiendabox`)

**Datos típicos**: 1.000–5.000 SKUs activos, 3–5 canales (tienda física, ecommerce, marketplace, B2B), histórico de 24–36 meses, patrones de alta estacionalidad (temporada escolar, navidad, cyber).

**Delta determinístico**: antes de entrenar, normalizar las ventas por canal eliminando el efecto de descuentos (precio efectivo vs. precio lista). La elasticidad-precio es un ajuste aritmético sobre el histórico de precio efectivo.

**Delta agéntico**: TiendaBox vende en Mercado Libre y en tienda propia; los descuentos y la visibilidad del marketplace generan picos que el modelo interpreta como señal de demanda real cuando son artefactos de la plataforma. El agente detecta si un pico coincide con una campaña del marketplace y lo trata como evento, no como tendencia.

**Regulación**: si TiendaBox maneja productos con fechas de vencimiento (alimentos, cosméticos), el forecast debe considerar la rotación mínima para evitar merma por vencimiento.

**Precio orientativo**: 400–900 USD/mes para 1.000–5.000 SKUs.

### Instancia 2 — Agro / Cooperativa exportadora (`cafetera`)

**Datos típicos**: 20–80 SKUs (variedades y calidades de café), 2 canales (exportación spot/forward, mercado nacional), demanda altamente estacional (cosecha principal oct–dic, traviesa abr–jun), precio de referencia indexado a mercado de futuros (ICE).

**Delta determinístico**: la «demanda» en la Cooperativa cruza contratos forward firmados (demanda comprometida) con estimado de acopio (oferta proyectada), no solo ventas históricas. El MRP de la Cooperativa es oferta vs. demanda comprometida.

**Delta agéntico**: la cosecha de 2026 viene con 15% menos volumen por El Niño. El modelo estadístico no lo sabe; el agente incorpora el pronóstico agrometeorológico (dato externo que el planificador aporta) y ajusta el forecast de oferta, priorizando los contratos de exportación sobre el canal nacional. El razonamiento de priorización requiere conocer las penalidades contractuales de cada contrato forward.

**Regulación**: contratos de exportación de café en Colombia están sujetos a cuotas de reintegro de divisas. El forecast de ingresos en USD debe separarse del flujo en COP para el área financiera.

**Precio orientativo**: 300–600 USD/mes; volumen de datos bajo pero complejidad del contexto agronómico alta.

## 12. Módulos técnicos relacionados

- **A06** (dataclasses y Pydantic): `ForecastResult`, `SKUClassification`, `EventAdjustment` son dataclasses validadas. El catálogo de SKUs se modela como `list[SKURecord]` con validación de campos obligatorios antes de pasar al pipeline.
- **C01** (SQLAlchemy async): tabla `forecast_runs` con `tenant_id`, `period`, `model_used`, `mape`; tabla `sku_classifications` para persistir la clasificación ABC-XYZ y reutilizarla entre ciclos.
- **D04** (observabilidad): el costo del tramo agéntico (detección de anomalías + ajuste de eventos) se traza en Phoenix. Si el costo por ciclo de forecast supera el umbral configurado, se reduce el número de SKUs enviados al agente y se amplía el umbral de MAPE para alertar.
- **E01** (Anthropic SDK + tools): el agente de detección de anomalías usa `sql_query` para recuperar el historial del SKU y `fetch_excel` para el calendario de eventos; ilustra el loop multi-herramienta con contexto acumulado entre iteraciones.
- **E05** (Temporal): `MonthlyForecastWorkflow` separa la actividad CPU-bound (entrenamiento de modelos, hasta 10 minutos) de la actividad LLM-bound (agente de anomalías y eventos). La separación es obligatoria: una actividad CPU larga no puede contener una llamada LLM que puede fallar por timeout independiente o rate limit.

## Determinístico vs agéntico

| Tramo | Tipo | Por qué |
|-------|------|---------|
| Clasificación ABC-XYZ de SKUs | determinístico | Regla cerrada sobre percentiles de volumen y CV de demanda. |
| Selección de modelo (ETS vs. CrostonSBA) | determinístico | Tabla de decisión sobre ADI y CV² calculados. |
| Entrenamiento y proyección con statsforecast | determinístico | Algoritmo determinista dado el histórico. Mismo input → mismo output. |
| Cálculo de MAPE/wMAPE | determinístico | Aritmética pura. |
| Diagnóstico de causa de error alto (intermitencia vs. fin de vida vs. error de registro) | agéntico | Requiere razonamiento sobre el contexto del SKU; las causas no se distinguen con reglas cerradas. |
| Ajuste del forecast por evento extraordinario (lanzamiento, promo, fuerza mayor) | agéntico | El impacto depende del contexto del canal y del historial del evento; no hay fórmula general. |
| Narrativa mensual para el planificador | agéntico | Comunicación contextual para humano; no formulable como plantilla fija. |

## 13. Errores típicos

**1. CrostonSBA aplicado a SKU con demanda regular.**
*Síntoma*: el forecast de un SKU con ventas estables de 100 unidades/mes sale en 40 unidades.
*Causa*: la clasificación ABC-XYZ no se ejecutó antes de seleccionar el modelo, o el umbral de ADI está mal calibrado.
*Arreglo*: verificar que ADI se calcula correctamente (períodos totales / períodos con demanda > 0). Si ADI < 1.32, usar ETS, no Croston.

**2. El agente aplica el mismo ajuste de evento en meses sucesivos.**
*Síntoma*: la planificadora declaró la promoción de marzo una vez; el agente la sigue aplicando en abril y mayo.
*Causa*: los eventos del calendario no tienen campo `fecha_fin` o el agente no valida que el evento sea vigente para el período en curso.
*Arreglo*: el calendario de eventos requiere `fecha_inicio` y `fecha_fin` obligatorios. El ingest filtra solo los eventos cuyo rango solapa con el período de forecast.

**3. Forecast correcto en punto medio, inútil para planificación de stock.**
*Síntoma*: el planificador sigue ordenando de más porque el forecast no le da la distribución de incertidumbre.
*Causa*: se reporta solo el valor central del forecast, no el intervalo de confianza.
*Arreglo*: incluir siempre `IC_bajo` e `IC_alto`. El plan de compras usa `IC_alto` para SKUs críticos (no stockout) e `IC_bajo` para SKUs con alto costo de sobrestock.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre Croston SBA y ETS con un ejemplo de un SKU de TiendaBox que tiene semanas sin ventas.»
2. **Aplícalo a mi caso**: «Mi negocio vende café de especialidad con una cosecha al año. ¿Qué modelo elegiría para forecastear la demanda mensual y cómo incorporo el pronóstico de cosecha?»
3. **Por qué falló**: «El MAPE de mi pipeline salió en 60% para los SKUs clase C. ¿En qué paso del pipeline es más probable que esté el error?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Clasificar una cartera de SKUs en ABC-XYZ y asignar el modelo estadístico correcto a cada clase.
- Implementar el pipeline de forecast con `statsforecast` (Nixtla) usando `CrostonSBA` para intermitentes y `AutoETS` para regulares.
- Identificar qué tramos son determinísticos (modelado, métricas de error) y cuáles son agénticos (diagnóstico de anomalías, ajuste de eventos, narrativa).
- Diseñar el workflow Temporal mensual separando la actividad CPU-bound (entrenamiento) de la actividad LLM-bound (agente), con idempotencia por `tenant + period`.
- Cotizar y dimensionar el servicio para retail multicanal o cooperativa agro con estacionalidad compleja.

## 16. Módulos previos recomendados

| Módulo | Por qué te prepara para implementar esta ficha |
|--------|------------------------------------------------|
| A06   | `ForecastResult`, `SKUClassification` y `EventAdjustment` son dataclasses Pydantic; los campos `modelo_usado` y `ajuste_evento` con `Literal` y `Optional` son los tipos que A06 enseña a modelar. |
| C01   | Las tablas `forecast_runs` y `sku_classifications` con `tenant_id` y la query de historial de anomalías entre ciclos siguen el patrón de SQLAlchemy async con multitenancy que C01 establece. |
| D04   | El costo del tramo agéntico (detección de anomalías + ajuste de eventos) se traza span a span en Phoenix; si el costo por ciclo supera el umbral, se reduce el número de SKUs enviados al agente — lógica que D04 enseña a implementar. |
| E01   | El agente de detección de anomalías que llama `sql_query` y `fetch_excel` en un loop acumulando contexto entre iteraciones es el ejemplo de tool-use multi-herramienta con estado que E01 introduce. |
| E05   | `MonthlyForecastWorkflow` que separa `run_forecast_models` (CPU-bound, hasta 10 min) de `run_forecast_agent` (LLM-bound) en actividades distintas es el patrón de separación de cargas que E05 justifica y enseña. |
