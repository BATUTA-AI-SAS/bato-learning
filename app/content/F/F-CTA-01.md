---
ext_id: F-CTA-01
slug: clasificacion-contable
track: F
dept: CTA
ord: 120
title: "Clasificación contable de transacciones bancarias"
summary: "Agente que aplica el plan de cuentas del cliente para clasificar transacciones bancarias, propone creación de reglas nuevas cuando detecta patrones repetidos, y marca con baja confianza lo que no puede clasificar."
related_modules: [A06, B02, C01, E01]
industries_instanced: [servicios-fin, hospitalidad]
tenants_in_examples: [cooppopular, mesonurbano]
big_corp_vendors: [Vic.ai, BlackLine, AppZen]
latam_tools: [siigo, contpaq, alegra, world_office]
key_concepts: [PUC, centros-de-costo, reglas-previas, confianza-low, propuesta-de-regla, chart-of-accounts]
estimated_minutes: 45
deterministic_share: 0.6
version: 1
---

## 1. Problema operativo

El auxiliar contable de la Cooperativa Popular de Crédito recibe cada semana el extracto bancario con 300–800 transacciones. Su trabajo es clasificar cada una contra el Plan Único de Cuentas (PUC) que exige la Superintendencia Financiera: el pago de un proveedor va a la cuenta 2205, un depósito de asociado va a la 2101, un gasto administrativo va a la 5105.

El problema: el 60 % de las transacciones son variaciones del mismo patrón («TRANSF PAGO NÓMINA», «PAGO SERVICIO», «ABONO SOCIO»), pero el 40 % tiene descripciones que el auxiliar debe interpretar. Sin asistencia, el proceso toma 2–3 días por semana. Los errores de clasificación se descubren en la auditoría externa, no antes.

El dueño de Mesón Urbano F&B tiene el mismo problema: cada transacción del POS, proveedor de alimentos, o servicio de delivery debe clasificarse entre una docena de centros de costo (cocina, salón, bar, administración) antes de que el contador pueda hacer el P&L semanal.

## 2. Hoy en big corps

| Vendor | Producto | Capacidad clave | Inversión orientativa |
|--------|----------|-----------------|-----------------------|
| **Vic.ai** | Autonomous AP + GL Coding | ML entrenado sobre el historial de clasificaciones del cliente; auto-codificación de facturas y transacciones; confianza por línea | 1 000–5 000 USD/mes; impl. 20–60 k USD |
| **BlackLine** | Transaction Matching + GL Coding | Reglas determinísticas + excepción agéntica; integrado con su plataforma de conciliación | 80–250 USD/usuario/mes |
| **AppZen** | AP Audit + Coding | Audita el 100 % de gastos y facturas en tiempo real; ML para detectar anomalías de clasificación | 500–3 000 USD/mes; impl. variable |

Vic.ai es el más cercano al caso puro de clasificación contable automatizada. En 2025 su modelo cubre GAAP y IFRS; para PUC colombiano o PCGA mexicano requiere fine-tuning con el historial del cliente.

## 3. PYME LATAM realista

- **PUC del cliente**: en Colombia, el PUC es obligatorio por ley para entidades vigiladas por Supersociedades o Superfinanciera. La PYME lo tiene en un Excel o en la configuración de su ERP (Siigo/World Office lo trae preconfigurado).
- **Reglas previas**: el cliente ha entrenado empíricamente qué descripción va a qué cuenta. Pueden estar en el ERP como «keywords» o solo en la cabeza del contador.
- **Volumen**: 200–1 500 transacciones/semana para una PYME mediana.
- **Formato de entrada**: extracto bancario CSV (ver F-FIN-01 §4) más la lista de transacciones de tarjetas de crédito corporativas (otro CSV, formato distinto).
- **ERP de destino**: el auxiliar importa las clasificaciones de vuelta al ERP vía asiento de diario (Siigo permite importación de asientos en Excel; World Office tiene endpoint REST).

## 4. Datos típicos

| Atributo | Transacción bancaria | Regla previa (configuración del tenant) |
|----------|---------------------|----------------------------------------|
| Formato | CSV: `fecha,descripcion,monto,tipo` | YAML: `{keyword: "PAGO NÓMINA", account: "5105", cost_center: "ADM", confidence: 1.0}` |
| Volumen | 200–1 500 filas/semana | 20–200 reglas activas |
| Ejemplo fila | `2026-04-15, TRANSF PAGO PROV VARGAS, -4820000, DEBITO` | `{keyword: "PROV VARGAS", account: "2205", cost_center: "PROD"}` |
| Nuevas transacciones sin regla | ~30–40 % del total | — |

**PUC típico**: 5 dígitos en Colombia (clase 1=activos, 2=pasivos, 3=patrimonio, 4=ingresos, 5=gastos, 6=costos de producción, 7=costos de ventas).

## 5. Tramos determinísticos

1. **Normalización de transacciones**: parseo del CSV del extracto bancario; normalización de fecha, monto (eliminar separadores de miles), tipo (`DEBITO`/`CREDITO`).
2. **Match por regla previa (keyword exact)**: para cada transacción, buscar en la tabla de reglas del tenant si alguna `keyword` aparece en la descripción. Si hay match con `confidence = 1.0`, clasificar directamente. Si hay múltiples matches, tomar el de mayor especificidad (regla más larga).
3. **Match por regla previa (regex)**: para los tenants que definen reglas con patrones (e.g., `^TRANSF\s+SOCIO\s+\d{4}$`), aplicar el regex. Este paso cubre el 60–70 % del volumen en tenants maduros.
4. **Enriquecimiento del contexto**: para transacciones sin match, consultar historial de clasificaciones anteriores de la misma descripción (`sql_query` sobre la tabla de transacciones clasificadas del tenant). Si la misma descripción fue clasificada 3+ veces en el mismo account, eso es evidencia fuerte.
5. **Generación del asiento preliminar**: para transacciones clasificadas con confianza alta, generar el asiento de diario listo para importar al ERP (`fecha, cuenta_debito, cuenta_credito, monto, descripcion`).
6. **Agrupación de baja confianza**: transacciones sin match o con historial inconsistente se agrupan en el batch `PENDING_REVIEW` para enviar al LLM.

## 6. Tramos agénticos

1. **Clasificación de transacciones sin regla previa**: el agente recibe el batch `PENDING_REVIEW` y clasifica cada transacción usando el PUC del tenant como contexto, el historial de clasificaciones similares, y el tipo de operación inferido de la descripción. «SERV TECH SOPORTE AGOSTO» probablemente es gastos de servicios tecnológicos (cuenta 5155 o similar), pero necesita contexto del cliente para elegir entre varios candidatos. **No es regla** porque las descripciones en LATAM son libres, ambiguas, y cambian constantemente.
2. **Propuesta de regla nueva**: cuando el agente clasifica la misma descripción (o variaciones de ella) con alta confianza 3+ veces en un período, propone una regla nueva al operador: «He clasificado 5 transacciones de "PAGO PLATAFORMA RAPPI" como cuenta 4135 (ingresos por ventas plataformas). ¿Quieres crear una regla fija?» Esta propuesta no se activa automáticamente; requiere aprobación humana. **Es agéntico** porque detectar el patrón y decidir el umbral de propuesta requiere razonamiento sobre el contexto del negocio.
3. **Asignación de centro de costo en ambigüedad**: en Mesón Urbano, una transacción de «COMPRA INSUMOS PROVIFOOD» puede corresponder a cocina, bar, o eventos. El agente revisa el monto, el día de la semana, y el historial del proveedor para decidir. No hay regla que cubra todos los proveedores.
4. **Fallback humano**: cualquier transacción donde la confianza del agente es < 0.75 se marca como `REQUIRES_HUMAN` y va al inbox del auxiliar contable con la propuesta del agente como sugerencia (no como clasificación definitiva). El auxiliar aprueba o corrige. Las correcciones alimentan el historial para futuras corridas.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_txns] → fetch_csv(extracto_bancario, tenant)
  ↓               + fetch_csv(tarjetas_corp, tenant) si aplica
[normalize] → normalización determinística (Python puro)
  ↓
[match_rules] → match exact keyword + regex sobre reglas del tenant (determinístico)
  ↓               → sets: HIGH_CONF, PENDING_REVIEW
[enrich_history] → sql_query(historial_clasificaciones, tenant)
  ↓               → evidencia histórica para PENDING_REVIEW
[classify_pending] → LLM clasifica batch PENDING_REVIEW (agéntico)
  ↓                  tool: sql_query(PUC_tenant, tenant)
  ↓                  confidence score por transacción
[split_confidence] → router determinístico: confidence >= 0.75?
  ├─ SÍ → [generate_journal] → asientos listos para importar
  └─ NO → [queue_review]    → inbox del auxiliar contable
              ↓ (auxiliar aprueba/corrige)
[propose_rules] → LLM detecta patrones recurrentes → propone reglas nuevas (agéntico)
  ↓               → notificación al operador para aprobación
[write_report] → write_report(kind=xlsx, "Clasificación semana 2026-W16", tenant)
  ↓
END
```

### Tools necesarias

| Tool | Uso |
|------|-----|
| `fetch_csv` | Extracto bancario y tarjetas corporativas |
| `sql_query` | PUC del tenant, historial de clasificaciones, reglas previas |
| `write_report` | Archivo XLSX con asientos para importar al ERP |
| `send_email` | Resumen semanal al contador y al auxiliar |

## 8. Salida y entrega

**Archivo XLSX importable al ERP** con columnas: `fecha, cuenta_debito, cuenta_credito, monto, descripcion, centro_costo, metodo` (regla/LLM/historial), `confianza`.

**Resumen semanal** al contador: total de transacciones, breakdown por método de clasificación, lista de `REQUIRES_HUMAN` con propuesta del agente, y propuestas de nuevas reglas pendientes de aprobación.

**Inbox del auxiliar** (en la UI de la app): lista de transacciones de baja confianza con la clasificación propuesta por el agente, botones de «Aprobar» / «Corregir», y el campo de corrección (cuenta correcta).

## 9. Cómo se vende

**Gancho**: «Tu auxiliar pasa 3 días clasificando transacciones en el ERP. Nosotros clasificamos el 70 % automáticamente; él solo revisa el 30 % restante y en una hora.»

**Propuesta de valor**: reducción del 70–80 % del tiempo de clasificación manual; trazabilidad de cada clasificación; aprendizaje continuo del plan de cuentas del cliente; cero errores de clasificación que lleguen a la auditoría.

| Tier | Qué incluye | Precio USD/mes |
|------|-------------|----------------|
| Básico | 1 ERP, hasta 500 tx/semana, email only | 100–250 |
| Estándar | 2 000 tx/semana, propuesta de reglas, inbox UI | 250–600 |
| Premium | volumen ilimitado, multi-ERP, SLA respuesta | 600–1 200 |

Setup: 1 000–2 500 USD (carga del PUC, configuración de reglas previas iniciales, golden set de 100 transacciones etiquetadas).

## 10. Riesgos

| Riesgo | Probabilidad | Impacidad | Mitigación |
|--------|-------------|---------|-----------|
| **Clasificación incorrecta en cuenta fiscal**: el agente pone un gasto deducible en una cuenta no deducible o viceversa | Media | Muy alto | El agente no tiene confianza > 0.9 a menos que la regla sea exacta o el historial sea consistente. Las cuentas de impacto fiscal (e.g., 2404 retención en la fuente) siempre tienen umbral de confianza mínimo 0.95; por debajo, van a revisión humana obligatoria. |
| **PUC desactualizado**: el cliente modifica su catálogo de cuentas y el agente sigue usando el anterior | Alta | Alto | Versionado del PUC en DB; el agente usa siempre la versión activa. Alerta cuando el PUC tiene > 6 meses sin actualizar. |
| **Regla propuesta incorrecta aprobada sin revisión**: el operador aprueba una regla propuesta sin verificarla | Media | Alto | Las reglas propuestas siempre requieren aprobación explícita (no hay «aprobar todo»). Las primeras 10 transacciones que aplican a una regla nueva se muestran en el inbox para validación. |
| **Volumen de LLM en tenants grandes**: clasificar 1 500 transacciones semanales con LLM es caro si no se hace batch eficiente | Alta | Medio | Solo las transacciones `PENDING_REVIEW` van al LLM (30–40 % del total). Las demás se clasifican con reglas. Batch de 50 transacciones por llamada para aprovechar el context window. |

## 11. Variantes por industria

### Instancia 1 — Servicios financieros (`cooppopular`)

**Datos típicos**: 300–800 transacciones/semana, PUC del sector cooperativo supervisado por Supersolidaria (Colombia), cuentas altamente específicas por tipo de operación (aportes sociales, préstamos, ahorros a la vista).

**Delta determinístico**: los códigos de transacción del core bancario de la cooperativa (sistema COSAC o similar) mapean directamente a cuentas del PUC. El 80 % se clasifica por este código; el agente solo interviene en el 20 % sin código o con código ambiguo.

**Delta agéntico**: distinguir entre una transferencia que es un abono de cuota de préstamo (cuenta 1402) y una que es un depósito de ahorro a la vista (cuenta 2101). A veces la descripción no lo dice; el agente debe consultar el registro de obligaciones del asociado.

**Regulación**: Supersolidaria exige reportes mensuales con el catálogo de cuentas exacto. Una clasificación errónea genera una observación formal en la inspección.

**Precio orientativo**: 300–700 USD/mes; la complejidad regulatoria justifica un precio mayor.

---

### Instancia 2 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: 150–400 transacciones/semana (POS, proveedores de alimentos, plataformas de delivery Rappi/iFood, nómina diaria de meseros), 8–12 centros de costo (cocina caliente, cocina fría, bar, salón, delivery, eventos).

**Delta determinístico**: las transacciones del POS tienen el número de turno y el punto de venta, lo que permite clasificar el centro de costo directamente (POS-salón → centro de costo «Salón»). El agente no interviene en esas.

**Delta agéntico**: un proveedor de alimentos puede surtir tanto a cocina como a bar; el agente decide basándose en el tipo de producto (si la descripción menciona «bebidas» → bar; «carnes» → cocina). Pero muchos proveedores tienen descripciones genéricas («DIST ALIMENTOS GEN»), y el agente debe usar el historial para inferir.

**Regulación**: en Colombia, las facturas de consumo en restaurante tienen IVA del 8 % para consumo en el local. La clasificación debe separar el IVA del valor base. El agente verifica que la descomposición sea correcta.

**Precio orientativo**: 150–350 USD/mes; volumen y complejidad menores que el sector financiero.

## 12. Módulos técnicos relacionados

| Módulo | Por qué aplica |
|--------|---------------|
| **E01** — Anthropic SDK | El nodo `classify_pending` es un loop tool_use donde el modelo recibe el batch de transacciones y el PUC, y emite clasificaciones estructuradas en JSON. Ejemplo directo de E01. |
| **C01** — SQLAlchemy async | La tabla de reglas previas y el historial de clasificaciones se almacenan en DB. C01 enseña el modelo ORM `ClassificationRule` y la query de historial. |
| **A06** — Dataclasses | El tipo `Transaction(date, description, amount, type, account, cost_center, confidence, method)` es el ejercicio natural de A06. |
| **B02** — FastAPI + Pydantic | El endpoint `/classify/approve-rule` que recibe la aprobación de una regla nueva propuesta por el agente. Ejemplo de validación de body con Pydantic. |
| **D04** — Observabilidad | El span de `classify_pending` en Phoenix muestra el costo por transacción y la distribución de confidence scores. Referencia para optimizar el umbral de 0.75. |

## 13. Errores típicos

**1. PUC cargado al inicio del onboarding y nunca actualizado.**
*Síntoma*: el agente clasifica transacciones en cuentas que ya no existen en el plan de cuentas activo del cliente; el auxiliar rechaza el import al ERP con error de cuenta inexistente.
*Causa*: el PUC se subió una vez y no hay proceso de sincronización cuando el contador añade o elimina cuentas en Siigo.
*Cómo evitarlo*: al inicio de cada corrida, comparar el hash del PUC activo en Siigo vs el almacenado en DB. Si difieren, detener y notificar al operador para actualizar antes de clasificar.

**2. Regla propuesta activada en bloque sin revisar las primeras aplicaciones.**
*Síntoma*: el contador aprueba la nueva regla «RAPPI → cuenta 4135» sin verificar; resulta que algunas transacciones de RAPPI son devoluciones (nota crédito) que deberían ir a la cuenta 4375.
*Causa*: el operador usó «Aprobar todo» en el panel de reglas propuestas.
*Cómo evitarlo*: las primeras 10 transacciones que aplican a una regla nueva entran automáticamente al inbox de validación; solo después de confirmarlas se activa la regla de forma general.

**3. Batch al LLM con transacciones mezcladas de distintos períodos.**
*Síntoma*: el agente clasifica una transacción de marzo con el contexto del cierre de abril; la cuenta elegida es correcta para abril pero incorrecta para el período fiscal de marzo.
*Causa*: el pipeline no filtra por `period` antes de armar el batch `PENDING_REVIEW`.
*Cómo evitarlo*: el batch de clasificación siempre lleva el atributo `period` en el system prompt y las transacciones se segmentan por período antes de enviarse al LLM.

**4. Umbral de confianza 0.75 aplicado igual a cuentas fiscales y no fiscales.**
*Síntoma*: una retención en la fuente (cuenta 2404) se clasifica automáticamente con confianza 0.76; el error llega a la declaración sin detección.
*Causa*: el umbral único no distingue el impacto fiscal de la cuenta destino.
*Cómo evitarlo*: definir un `confidence_threshold` por clase de cuenta en la configuración del tenant; las cuentas de impacto fiscal (clase 2 pasivos fiscales, clase 5 gastos deducibles) usan un umbral mínimo de 0.95.

## 14. Pregúntale al tutor

1. «Explícame cómo adaptaría el nodo `classify_pending` si la Cooperativa Popular tuviera un PUC del sector cooperativo con 800 cuentas activas en lugar de 200. ¿Cómo gestiono el tamaño del contexto?»
2. «Audita mi diseño actual de la tabla de reglas previas para Mesón Urbano y dime qué le falta para que el agente proponga reglas por centro de costo y no solo por cuenta contable.»
3. «Genera el código mínimo en LangGraph para el nodo `propose_rules` que detecta que la misma descripción fue clasificada con alta confianza 3 veces y dispara la propuesta al operador.»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de clasificación con tres capas ordenadas: regla exacta → historial → LLM, sin saltarte el orden.
- Identificar qué transacciones van al LLM (solo `PENDING_REVIEW`) y justificar por qué las demás no deben hacerlo.
- Implementar el umbral de confianza diferenciado por clase de cuenta para proteger las cuentas de impacto fiscal.
- Configurar el flujo de propuesta y aprobación de reglas nuevas con validación de las primeras aplicaciones.
- Dimensionar el costo de LLM por tenant según el volumen semanal y el porcentaje de transacciones sin regla previa.

## 16. Módulos previos recomendados

| Módulo previo | Por qué te prepara |
|---------------|-------------------|
| **A06** — Dataclasses y Pydantic | El tipo `Transaction` con campo `confidence: float` y `method: Literal["rule","llm","history"]` es el ejercicio central antes de construir el pipeline. |
| **C01** — SQLAlchemy async | La tabla de reglas previas y el historial de clasificaciones usan exactamente los patrones ORM de C01; sin ese módulo el `sql_query` del nodo `enrich_history` no tiene base. |
| **E01** — Anthropic SDK + tools | El nodo `classify_pending` es un loop `tool_use`; E01 enseña el patrón de llamada estructurada con `response_format` JSON que este nodo necesita. |
| **B02** — FastAPI + Pydantic | El endpoint `/classify/approve-rule` requiere validación de body y autorización; B02 enseña ambos patrones antes de implementarlo. |
| **D04** — Observabilidad | Antes de ajustar el umbral de 0.75, necesitas leer la distribución de confidence scores en Phoenix; D04 enseña cómo instrumentar ese span. |
