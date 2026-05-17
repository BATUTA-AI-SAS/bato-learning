---
ext_id: F-OPS-01
slug: planeacion-produccion-semanal
track: F
dept: OPS
ord: 161
title: "Planeación de producción semanal (capacidad + demanda + materiales)"
summary: "Genera el plan de producción semanal con MILP/heurística simple desde BOM + inventario + demanda; el agente prioriza conflictos de capacidad y explica los cambios al jefe de planta en lenguaje operativo."
related_modules: [A06, C01, E01, E05]
industries_instanced: [manufactura, hospitalidad]
tenants_in_examples: [acme, mesonurbano]
big_corp_vendors: [SAP IBP, Anaplan, Kinaxis, o9 Solutions]
latam_tools: [excel, world_office, datup]
key_concepts: [MPS, MRP, BOM, capacidad-restricción, bottleneck, what-if, MILP, ordenes-de-fabricacion]
estimated_minutes: 60
deterministic_share: 0.6
version: 1
---

## 1. Problema operativo

El jefe de producción de ACME Manufacturing pasa los viernes por la tarde armando el plan de la semana siguiente en un Excel con 6 pestañas: demanda comprometida, inventario de materias primas, capacidad de cada línea de producción, BOM de cada producto, órdenes de fabricación pendientes, y una pestaña de «ajustes manuales». Cada semana hay al menos un conflicto: la línea 2 no alcanza para producir tanto pedido urgente como producto de inventario preventivo, o falta un insumo para el SKU más pedido. Resolver el conflicto le toma 2 horas de negociación verbal con el supervisor y la persona de compras. Necesita que el plan tentativo llegue listo el viernes a las 2pm para dedicar la tarde a los conflictos reales, no a la mecánica del Excel.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|--------|----------|-------------------|
| **SAP IBP** (Integrated Business Planning) | Planificación S&OP integrada con S/4HANA, MILP para production scheduling, simulación de escenarios, alertas de constraint en tiempo real | Dentro del bundle SAP, 100k–500k USD/año; impl. 200k–1M USD |
| **Kinaxis RapidResponse** | Concurrent planning: cualquier cambio en demanda/oferta se propaga inmediatamente a todos los planes; análisis de what-if en segundos | 250k–1M+ USD/año |
| **Anaplan** | Plataforma de planificación conectada; supply chain modules configurables, Polaris forecasting engine | 100k–500k USD/año; impl. 100k–300k USD |
| **o9 Solutions** | IA nativa para S&OP, integración de señales externas (clima, macro), simulación de escenarios enterprise | Custom pricing, 300k–1M+ USD/año |

El modelo big corp: planificación continua y conectada. La PYME tiene planificación semanal en Excel desconectada del ERP.

## 3. PYME LATAM realista

ACME usa World Office para registrar las órdenes de fabricación resultantes, pero el plan se hace fuera del ERP. Datup (plataforma colombiana de demand planning para PYME) puede proveer el forecast de demanda, pero no tiene módulo de production scheduling. La integración manual entre el forecast y el plan de producción sigue siendo un Excel.

El agente no reemplaza al jefe de producción: le da el 80% del trabajo hecho para que él dedique su experiencia al 20% de decisiones reales.

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Demanda comprometida (órdenes de cliente) | Excel exportado de ERP / tabla ERP | Semanal | 20–200 órdenes abiertas |
| Forecast de demanda no comprometida | Excel (puede venir de Datup/F-OPS-02) | Semanal | 10–50 SKUs |
| BOM (bill of materials) | Excel maestro o tabla ERP | Estático (actualización mensual) | 10–80 SKUs con 3–15 componentes c/u |
| Inventario de materias primas | Excel o tabla ERP actualizada diariamente | Diaria | 50–300 materiales |
| Capacidad de líneas (horas disponibles) | Excel de RRHH/producción con turnos | Semanal | 2–8 líneas con 40–120 h/semana c/u |
| Órdenes de fabricación en curso | Tabla ERP | Tiempo real | 5–30 OFs abiertas |

**Ejemplo de fila de BOM:**

| sku_producto | componente | cantidad_por_unidad | unidad |
|-------------|------------|---------------------|--------|
| PROD-045 | MAT-012 (Polietileno HD) | 2.5 | kg |
| PROD-045 | MAT-031 (Colorante azul) | 0.08 | kg |
| PROD-045 | MAT-007 (Tapa rosca 28mm) | 1 | unidad |

## 5. Tramos determinísticos

1. **Explosión de materiales (MRP)**: dado el plan tentativo de producción (qué producir, cuánto, cuándo), calcular los requerimientos brutos de cada componente via BOM. Restar inventario disponible. Resultado: `requerimientos_netos` por material. Algoritmo: tabla × BOM, resta inventario. Sin modelo.
2. **Validación de capacidad**: para cada línea y cada turno de la semana, calcular las horas necesarias según `tiempo_ciclo_sku × cantidad_planificada`. Si `horas_necesarias > horas_disponibles`, hay conflicto de capacidad en ese turno. Regla cerrada.
3. **Generación de plan tentativo (heurística FIFO + prioridad)**: ordenar los ítems a producir por `{prioridad_cliente DESC, fecha_entrega ASC}`, asignar a líneas respetando restricciones de capacidad. Si no cabe todo, identificar qué queda fuera. Este es un scheduling greedy, no un MILP completo — suficiente para PYME con ≤ 8 líneas.
4. **Detección de faltantes de material**: compara `requerimientos_netos` con inventario disponible. Genera lista de `{material, faltante, fecha_requerida}`. Regla aritmética.
5. **Cálculo de carga por línea**: sumarizar `horas_cargadas / horas_disponibles` por línea para el período. Identificar líneas > 90% de carga (bottleneck) y < 50% (capacidad ociosa).

> [!nota]
> El MILP completo (solver tipo PuLP o OR-Tools) es la versión avanzada. Para una PYME con ≤ 8 líneas y ≤ 50 SKUs, la heurística greedy produce resultados ≥ 90% del óptimo en < 1 segundo. No sobreingenierar.

## 6. Tramos agénticos

1. **Priorización de conflictos de capacidad**: cuando hay más demanda que capacidad en la línea 2, el modelo decide qué producir primero considerando: penalidad por entrega tardía de cada cliente, probabilidad de que el cliente posponga vs. cancele, costo de hora extra vs. costo de stockout. Justificación: la decisión óptima depende de contexto de negocio que no está en los datos (relación con el cliente, margen del pedido, historia de pagos).
2. **Explicación del plan al jefe de planta**: el modelo genera el «memo de producción semanal» comparando el plan propuesto contra el plan de la semana anterior: qué cambió, por qué, qué riesgos tiene. Escrito en lenguaje de planta, no de analytics. Justificación: la comunicación con el equipo operativo requiere contexto y tono que no es formulable como plantilla.
3. **Evaluación de what-if**: el jefe de producción puede pedir «¿qué pasa si agrego un turno extra el sábado en la línea 3?». El modelo orquesta recalcular el plan con esa hipótesis y explica el impacto en términos de pedidos cubiertos y costo adicional estimado.

## 7. Blueprint del workflow

```
START
  ↓
[ingest_inputs] → cargar demanda, BOM, inventario, capacidad del tenant (determinístico, tools: fetch_excel, erp_fetch_transactions)
  ↓
[explode_bom] → MRP: requerimientos brutos → netos (determinístico)
  ↓
[detect_material_shortages] → comparar netos vs. inventario disponible (determinístico)
  ↓
[build_tentative_plan] → scheduling greedy FIFO + prioridad (determinístico)
  ↓
[validate_capacity] → detectar conflictos por línea y turno (determinístico)
  ↓
[resolve_conflicts] → priorizar qué producir cuando no cabe todo (agéntico, tool: sql_query historial clientes)
  ↓
[draft_production_memo] → explicar el plan vs. semana anterior al jefe de planta (agéntico)
  ↓
[human_review] → jefe de producción revisa y aprueba (siempre — el plan no se ejecuta sin aprobación)
  ↓
[emit_work_orders] → registrar OFs aprobadas en ERP / World Office (determinístico)
  ↓
END
```

**Activities Temporal:**

- `ingest_weekly_inputs(tenant, week)` — pull de datos del ERP y Excel. Retry con backoff.
- `run_planning_agent(tenant, week)` — corre el grafo LangGraph. Timeout 5 minutos.
- `emit_work_orders(tenant, plan_id)` — escritura idempotente en ERP. `idempotency_key = "plan:{tenant}:{week}"`.

**Tools necesarias:**

- `fetch_excel` — BOM, capacidad, inventario desde Excel
- `erp_fetch_transactions` — órdenes de cliente desde World Office/Siigo
- `sql_query` — historial de clientes, márgenes, historial de producción
- `write_report` — plan de producción semanal en PDF/XLSX

## 8. Salida y entrega

1. **Plan de producción semanal** (tabla con: SKU | cantidad | línea asignada | turno | horas requeridas | estado).
2. **Reporte de faltantes de material** con fecha de requerimiento y proveedor sugerido.
3. **Carga por línea** (gráfica o tabla con % utilización y alertas de bottleneck).
4. **Memo de producción** para el jefe de planta (1 página, lenguaje operativo).

Canal: PDF/XLSX descargable desde la app + Slack al jefe de producción.

**Mockup de plan:**

| SKU | Descripción | Cantidad | Línea | Turno | Horas | Estado |
|-----|-------------|----------|-------|-------|-------|--------|
| PROD-045 | Contenedor PE-HD 5L | 800 | L2 | Lun-Mié | 24h | ✓ |
| PROD-032 | Tapa rosca 28mm | 2000 | L1 | Lun-Mar | 16h | ✓ |
| PROD-067 | Bidón 20L naranja | 300 | L2 | Jue-Vie | 18h | ⚠ Falta MAT-031 (colorante) |
| PROD-012 | Caja plástica apilable | 150 | — | — | — | 🔴 Sin capacidad disponible |

## 9. Cómo se vende

**Gancho**: «El plan de producción del viernes que hoy te toma 3 horas lo tienes listo en 20 minutos. Con los conflictos ya identificados para que tú los resuelvas, no para que los descubras.»

**Diferencial**: el memo que explica el plan al jefe de planta — comunicación operativa que ningún sistema de scheduling genera.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Básico | Scheduling greedy, detección de faltantes, plan XLSX | 200–400 USD/mes |
| Estándar | MRP completo, carga por línea, memo de planta, integración World Office | 400–800 USD/mes |
| Avanzado | What-if interactivo, optimización con OR-Tools, integración ERP bidireccional | 800–1600 USD/mes + setup 5–10k USD |

## 10. Riesgos

**1. BOM desactualizada.**
*Síntoma*: el plan usa el BOM del año pasado; el producto cambió de formulación y el cálculo de materiales es incorrecto.
*Mitigación*: el tenant debe marcar la fecha de última actualización del BOM en la configuración. Si `bom_last_updated > 30 días`, alerta al inicio de cada ciclo de planificación.

**2. Inventario incorrecto por falta de actualización del ERP.**
*Síntoma*: el sistema dice que hay 500 kg de polietileno; en realidad hay 200 porque el ingreso de almacén se registró tarde.
*Mitigación*: el sistema no puede resolver esto solo. Declarar en el UI: «El inventario proviene de [fuente] actualizado a [hora]. Verificar antes de confirmar el plan.»

**3. El modelo prioriza al cliente más grande ignorando penalidades del más pequeño.**
*Síntoma*: el agente siempre favorece a ACME-cliente-A (mayor volumen) aunque B tiene penalidad por demora 2x más alta.
*Mitigación*: el prompt de priorización incluye explícitamente la penalidad por SKU y cliente. Si no hay penalidad en el sistema, el tenant la declara en la configuración. El modelo debe justificar su priorización con los datos.

**4. Plan aprobado sin revisar los faltantes de material.**
*Síntoma*: el jefe de producción aprueba el plan sin notar que el material faltante tiene 5 días de lead time; la OF queda bloqueada.
*Mitigación*: el plan no se puede aprobar sin confirmar qué hacer con cada faltante de material: «ordenar urgente», «reprogramar», «sustituir».

## 11. Variantes por industria

### Instancia 1 — Manufactura PYME plásticos (`acme`)

**Datos típicos**: 5–8 líneas de inyección/soplado, 20–60 SKUs de producto terminado, BOM de 3–8 componentes, turnos de 8h (lunes–sábado), lead time de materias primas 2–7 días.

**Delta determinístico**: tiempo de preparación (`setup_time`) entre cambios de molde es significativo (1–4 horas). El scheduling debe incluir `setup_time` al calcular la capacidad real disponible por cambio de producto. Regla: minimizar cambios de molde en la misma línea agrupando lotes similares.

**Delta agéntico**: el proveedor de polietileno avisó que el lote llegará con 2 días de retraso. El modelo re-evalúa qué SKUs pueden producirse de todas formas (los que no usan ese material) y cuáles se reprograman, y propone el mensaje al cliente afectado.

**Regulación**: si ACME produce envases para alimentos, los materiales deben ser grado alimentario (FDA/INVIMA). El sistema verifica que el BOM solo use materiales con certificación activa.

**Precio orientativo**: 400–800 USD/mes.

### Instancia 2 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: «producción» es la mise en place diaria y semanal para 3–5 eventos o servicios de restaurante. BOM = recetas. «Líneas» = estaciones de cocina (fría, caliente, pastelería). Inventario: insumos perecederos con fecha de vencimiento.

**Delta determinístico**: insumos perecederos → no se puede planificar con más de 3 días de anticipación para muchos ítems. El planificador filtra los ítems por `vida_util > dias_planificacion` antes de calcular requerimientos.

**Delta agéntico**: el chef quiere sustituir un ingrediente que no llegó por algo equivalente. El modelo propone la sustitución (ej: merluza → corvina para una preparación específica) evaluando compatibilidad culinaria y costo. Sin regla cerrada: la compatibilidad culinaria es contextual.

**Regulación**: INVIMA / SECRETA en México: control de temperatura en cadena de frío. El plan de producción debe respetar que los insumos refrigerados se usen dentro de los rangos declarados.

**Precio orientativo**: 150–300 USD/mes.

## 12. Módulos técnicos relacionados

- **A06** (dataclasses y Pydantic): `BOMLine`, `ProductionOrder`, `CapacityConstraint` son dataclasses; el plan resultante es una `list[ProductionOrder]` validada con Pydantic.
- **C01** (SQLAlchemy async): tabla `production_plans` con `tenant_id`, `week_start`, `status`; tabla `work_orders` con FK al plan. La query de historial de clientes para priorización usa un join con `customer_orders`.
- **E01** (Anthropic SDK + tools): el what-if interactivo es el ejemplo de agente con loop: el modelo pide datos via `sql_query`, recibe el resultado, elabora el análisis, puede pedir más datos antes de concluir.
- **E05** (Temporal): el workflow `WeeklyPlanningWorkflow` es el caso canónico de workflow periódico. La actividad `run_planning_agent` encapsula el LLM call — el workflow code no lo llama directamente.

## Determinístico vs agéntico

| Tramo | Tipo | Por qué |
|-------|------|---------|
| Explosión de BOM (MRP) | determinístico | Aritmética matricial sobre datos estructurados. Mismo resultado siempre. |
| Validación de capacidad por línea y turno | determinístico | Suma de horas contra disponible. Regla cerrada. |
| Scheduling greedy FIFO + prioridad | determinístico | Algoritmo determinista sobre la lista ordenada. |
| Priorización cuando hay más demanda que capacidad | agéntico | Requiere contexto de negocio: penalidades, margen, relación con cliente. |
| Explicación del plan al jefe de planta | agéntico | Comunicación operativa contextual; salida para humano no formulable como plantilla. |
| Análisis de what-if (turno extra, material alternativo) | agéntico | Multi-paso con herramientas; el contexto cambia el razonamiento. |

## 13. Errores típicos

**1. BOM con unidades inconsistentes.**
*Síntoma*: el colorante aparece en la BOM en «kg» pero el inventario lo registra en «gramos»; el cálculo de faltantes es incorrecto por un factor de 1000.
*Causa*: la BOM y el inventario se gestionan por equipos distintos con nomenclaturas propias.
*Arreglo*: validar en ingest que cada `(material_id, unidad)` aparece consistente en ambas fuentes. Si hay discrepancia de unidad para el mismo `material_id`, detener y alertar antes de calcular.

**2. Plan generado con datos de la semana anterior por error de fecha.**
*Síntoma*: el agente usó el archivo de demanda de la semana pasada porque el nombre del archivo no cambió.
*Causa*: el proceso de actualización del Excel no tiene convención de nombre con fecha.
*Arreglo*: en el ingest, verificar que `fecha_datos ≥ lunes_de_semana_actual`. Si no, rechazar e indicar qué archivo espera.

**3. La priorización del agente no es explicable para el cliente afectado.**
*Síntoma*: el agente pospone al cliente B; el jefe de producción no puede justificar la decisión en la llamada.
*Causa*: el memo de planta no incluye el razonamiento de priorización con datos.
*Arreglo*: el memo debe incluir por cada reprogramación: qué cliente, qué pedido, por qué se pospone (capacidad / material), y cuál es la nueva fecha propuesta.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre MPS (Master Production Schedule) y MRP (Material Requirements Planning) con el ejemplo de ACME.»
2. **Aplícalo a mi caso**: «Mi empresa tiene una línea de producción compartida entre tres tipos de producto con tiempos de setup distintos. ¿Cómo ajusto el scheduling greedy?»
3. **Por qué falló**: «El agente generó un plan que requiere más horas de las que tiene la semana. ¿En qué paso de validación de capacidad falló?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Implementar el pipeline MRP desde BOM + inventario + demanda hasta requerimientos netos de materiales.
- Diseñar el scheduling greedy con restricciones de capacidad por línea y turno.
- Identificar exactamente qué tramos son determinísticos (MRP, validación) y cuáles son agénticos (priorización de conflictos, comunicación al equipo).
- Configurar el workflow Temporal semanal con idempotencia y retry para la generación automática del plan.
- Cotizar y dimensionar el servicio para manufactura PYME o F&B.

## 16. Módulos previos recomendados

| Módulo | Por qué te prepara para implementar esta ficha |
|--------|------------------------------------------------|
| A07   | La explosión de BOM (MRP) sobre 50 SKUs × 8 líneas × 5 turnos es un cálculo matricial que se beneficia de `asyncio.gather` para paralelizar las queries de inventario por material; A07 establece el patrón de I/O concurrente que aquí se aplica. |
| C01   | Las tablas `production_plans` y `work_orders` con `tenant_id` y el join con `customer_orders` para priorizar por penalidad siguen el patrón de SQLAlchemy async con multitenancy que C01 enseña. |
| E01   | El what-if interactivo es el ejemplo de agente con loop multi-herramienta: el modelo consulta `sql_query` varias veces, acumula contexto entre iteraciones y produce el análisis — patrón que E01 introduce. |
| E02   | El grafo LangGraph que encadena `resolve_conflicts` → `draft_production_memo` → `human_review` es el caso concreto de grafo con nodo de interrupción humana que E02 enseña a diseñar. |
| E05   | `WeeklyPlanningWorkflow` con `ingest_weekly_inputs` y `run_planning_agent` como actividades separadas, con `idempotency_key = "plan:{tenant}:{week}"`, es el patrón de workflow periódico que E05 establece. |
