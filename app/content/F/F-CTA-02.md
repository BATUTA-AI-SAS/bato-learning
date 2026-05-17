---
ext_id: F-CTA-02
slug: auditoria-interna-anomalias
track: F
dept: CTA
ord: 121
title: "Auditoría interna de transacciones (anomalías y duplicados)"
summary: "Agente ancla del curso: detecta duplicados estrictos y difusos, montos fuera de rango histórico, y gaps en numeración, luego redacta el reporte de findings ordenado por riesgo."
related_modules: [A06, C03, D04, E01, E05]
industries_instanced: [manufactura, salud]
tenants_in_examples: [acme, sanrafael]
big_corp_vendors: [AppZen, MindBridge, Trullion]
latam_tools: [siigo, contpaq]
key_concepts: [duplicado-estricto, duplicado-difuso, monto-fuera-de-rango, gaps-numeracion, riesgo-finding, monthly-audit]
estimated_minutes: 60
deterministic_share: 0.65
version: 1
---

## 1. Problema operativo

Esta es la ficha ancla del Capstone E06. El agente `monthly_audit` que construye el lector a lo largo del curso **es** este caso de uso.

El CFO de ACME Manufacturing recibe cada mes un reporte del revisor fiscal con observaciones sobre las transacciones del período. Pero ese reporte llega 15 días después del cierre, cuando ya es difícil actuar. Las observaciones típicas: «factura duplicada de proveedor Vargas (mayo y junio, mismo monto)», «pago a proveedor nuevo sin licitación previa», «gasto de viáticos 3× el promedio histórico».

La contadora de Clínica San Rafael enfrenta una variante: las facturas médicas (a EPS, ARL, particulares) tienen numeración regulada; un gap en la secuencia es un hallazgo que la Superintendencia de Salud puede objetar.

Ambos casos tienen la misma estructura: detectar lo que «no cuadra» antes de que el auditor externo lo encuentre, y hacerlo de forma sistemática sobre el 100 % de las transacciones del período.

## 2. Hoy en big corps

| Vendor | Producto | Capacidad clave | Inversión orientativa |
|--------|----------|-----------------|-----------------------|
| **MindBridge** | Autonomous Financial Oversight | Analiza el 100 % de transacciones; 8 000+ reglas GAAP embebidas; entrenado en 260 B+ transacciones; puntuación de riesgo por transacción | pricing por volumen de transacciones; impl. 15–50 k USD |
| **AppZen** | AP Audit + Expense AI | Audita el 100 % de facturas AP y reportes de gastos en tiempo real; ML para anomalías y policy violations | 500–3 000 USD/mes; impl. 15–40 k USD |
| **Trullion** | AI Accounting | Extracción de contratos + matching contra facturas; detección de discrepancias contrato-factura | pricing por módulo; impl. variable |

MindBridge es el referente más cercano al caso puro: analiza transacciones del GL y detecta riesgo sin necesidad de que el auditor defina reglas. Su diferenciador es la cobertura del 100 % de transacciones (vs el muestreo tradicional del auditor).

## 3. PYME LATAM realista

- **Fuente de transacciones**: export mensual del ERP (Siigo: CSV; Contpaq: XML o reporte en Excel) con todos los movimientos del período.
- **Catálogo de proveedores**: el ERP tiene el maestro de proveedores (NIT/RFC, nombre, tipo). El agente lo usa para detectar proveedores nuevos.
- **Historial**: transacciones de los últimos 12 meses del mismo tenant. El agente necesita este historial para calcular rangos históricos por proveedor.
- **Numeración de documentos**: Siigo asigna numeración secuencial por tipo de comprobante. El export incluye el número de comprobante; el agente verifica la secuencia.
- **Equipo**: el contador general o el revisor fiscal interno (si lo hay). La auditoría externa revisa el output del agente, no el raw data.

## 4. Datos típicos

| Atributo | Transacciones del período (Siigo CSV) | Catálogo de proveedores |
|----------|--------------------------------------|------------------------|
| Formato | `comprobante,tipo,fecha,proveedor_nit,descripcion,debito,credito,cuenta` | `nit,nombre,tipo,fecha_registro,activo` |
| Frecuencia | Export mensual al cierre | Estático; actualización ad-hoc |
| Volumen | 500–5 000 transacciones/mes | 50–500 proveedores activos |
| Ejemplo fila | `GR-00412,GR,2026-04-15,900123456,Pago proveedor Vargas insumos,4820000,,2205` | `900123456,Vargas Suministros SAS,PROVEEDOR,2023-01-10,true` |

**Tipos de comprobante Siigo/Contpaq**: GR (recibo de caja), GC (comprobante de contabilidad), NC (nota crédito), ND (nota débito), FC (factura de compra).

## 5. Tramos determinísticos

1. **Ingesta y normalización**: parseo del CSV/XML del ERP; normalización de fechas, montos, NIT (eliminar guiones y verificación de dígito de control). Validación de schema: si faltan columnas obligatorias, el proceso se detiene.
2. **Detección de duplicados estrictos**: hash `SHA-256(proveedor_nit + monto + fecha + tipo_comprobante)`. Si el hash existe en el período actual o en los 60 días anteriores, la transacción se marca como `DUPLICATE_STRICT`. Esta regla es cerrada; no hay ambigüedad.
3. **Detección de gaps en numeración**: para cada tipo de comprobante, verificar que la secuencia `[num_min, num_min+1, ..., num_max]` sea completa. Cualquier número faltante es un `GAP` finding. Aritmética pura.
4. **Cálculo de estadísticas históricas por proveedor**: `media` y `desviación estándar` de montos de transacciones de los últimos 12 meses por proveedor. Si < 5 transacciones históricas, usar estadísticas del sector (configurable).
5. **Detección de montos fuera de rango**: si `monto > media + 3σ` para ese proveedor, la transacción es `OUT_OF_RANGE`. Umbral configurable (2σ, 3σ, o percentil 95 según la política del tenant).
6. **Detección de proveedores nuevos con monto alto**: `proveedor_nit` registrado hace < 90 días AND `monto > umbral_proveedor_nuevo` (configurable; default: 5× el monto promedio del período). Finding `NEW_VENDOR_HIGH_AMOUNT`.
7. **Generación de tabla de findings**: estructura `{id, tipo, transaccion, descripcion_tecnica, nivel_riesgo_estimado}` donde el nivel de riesgo es determinístico para findings estrictos (duplicado = alto) y pendiente para los difusos.

## 6. Tramos agénticos

1. **Clasificación de duplicados difusos**: hay transacciones que no son duplicados exactos pero son sospechosas (mismo proveedor, mismo monto aproximado, distinta fecha dentro de 30 días, distinta descripción). El agente analiza si es un cargo legítimo repetido (e.g., cuota mensual de arrendamiento) o un posible duplicado de pago. **No es regla** porque la misma combinación puede ser legítima (arrendamiento mensual) o fraudulenta (pago duplicado disfrazado) dependiendo del contrato subyacente, que el agente no tiene acceso directo.
2. **Priorización y redacción de findings**: el agente toma la tabla de findings y los ordena por riesgo real (no solo por el tipo). Un `OUT_OF_RANGE` de 200 000 COP en un proveedor de papelería es menos relevante que uno de 45 M COP en un proveedor de construcción. La priorización requiere ponderar monto, proveedor, contexto del negocio, y tendencia histórica. **No hay fórmula cerrada** que pese todos esos factores correctamente en todos los casos.
3. **Redacción del hallazgo en lenguaje del auditor**: el agente redacta cada finding con la terminología que usa un revisor fiscal: «Se identificó una transacción con el proveedor Vargas Suministros SAS (NIT 900.123.456-1) por valor de $48.200.000 COP (comprobante GR-00412, 2026-04-15) que excede en 3,2 desviaciones estándar el promedio histórico de pagos a este proveedor ($14.820.000 COP). Se recomienda verificar el soporte contractual.» Esta redacción no es una plantilla que funcione para todos los casos; el agente adapta el texto al finding específico.
4. **Fallback humano**: si el agente encuentra un finding de tipo `DUPLICATE_STRICT` con monto > 10 M COP (configurable), genera un `interrupt_before` en el nodo `write_report` y escala al CFO y al revisor fiscal antes de emitir el reporte completo. El agente no determina si hubo fraude; solo informa. Si el agente dice «no tengo suficiente contexto para clasificar este finding», lo marca como `REQUIRES_HUMAN` con su análisis parcial.

## 7. Blueprint del workflow

### Nodos LangGraph (este es el grafo del `monthly_audit` skill de SHARED §2.2)

```
START
  ↓
[ingest_transactions] → erp_fetch_transactions(erp, period="2026-04", tenant)
  ↓                     → normalización + validación de schema
[detect_strict_dups] → hash SHA-256 (determinístico, Python puro)
  ↓                    → set DUPLICATE_STRICT findings
[detect_gaps] → secuencia de comprobantes (determinístico)
  ↓             → set GAP findings
[compute_stats] → sql_query(historial_12m_por_proveedor, tenant)
  ↓              → media + σ por proveedor
[detect_out_range] → montos > umbral (determinístico)
  ↓                  → set OUT_OF_RANGE findings
[detect_new_vendor] → sql_query(catalogo_proveedores, tenant) (determinístico)
  ↓                   → set NEW_VENDOR_HIGH_AMOUNT findings
[classify_fuzzy_dups] → LLM analiza candidatos a duplicado difuso (agéntico)
  ↓                     tool: sql_query(historial_proveedor, tenant)
  ↓                     → set DUPLICATE_FUZZY findings con confidence
[check_critical] → router: ¿DUPLICATE_STRICT > umbral_monto_critico?
  ├─ SÍ → [alert_critical] → interrupt_before → send_email(CFO + revisor, tenant)
  │           ↓ (sign-off)
  └─ NO ↓
[prioritize_findings] → LLM ordena findings por riesgo real (agéntico)
  ↓                     tool: sql_query(contexto_negocio, tenant)
[draft_report] → LLM redacta findings en lenguaje auditor (agéntico)
  ↓
[write_report] → write_report(kind=pdf, "Auditoría interna abril 2026", tenant)
  ↓
[send_report] → send_email(to=[CFO, revisor_fiscal], tenant)
  ↓
END
```

### Activities Temporal (Schedule: día 2 del mes siguiente)

- `ingest_erp_period(tenant, period)` — export del ERP; retry 3x.
- `load_historical_stats(tenant, period)` — carga estadísticas históricas desde la DB del agente.
- `run_audit_agent(tenant, period, dataset_id)` — ejecuta el grafo; timeout 20 min.
- `persist_audit_report(tenant, period, payload)` — `idempotency_key = "audit:{tenant}:{period}"`.

### Tools necesarias

| Tool | Uso |
|------|-----|
| `erp_fetch_transactions` | Transacciones del período desde Siigo/Contpaq |
| `sql_query` | Historial por proveedor, catálogo de proveedores, contexto del negocio |
| `write_report` | Reporte PDF de auditoría |
| `send_email` | Entrega al CFO y revisor fiscal |

## 8. Salida y entrega

**Reporte PDF de auditoría interna** con cuatro secciones:

1. **Resumen ejecutivo**: total de transacciones analizadas, total de findings por tipo, nivel de riesgo global (Bajo/Medio/Alto/Crítico), top 3 findings más relevantes en 3 párrafos.
2. **Findings por categoría**: tabla con cada finding, proveedor, monto, fecha, comprobante, tipo de finding, nivel de riesgo, nota del agente.
3. **Estadísticas del período**: comparativo con el período anterior, tendencias de proveedores, distribución de montos.
4. **Próximos pasos recomendados**: lista de acciones concretas (verificar soporte, contactar proveedor, revisar contrato).

**Nota**: el reporte es un borrador de auditoría interna, no un informe de revisor fiscal. El revisor fiscal firma su propio documento usando este reporte como insumo.

## 9. Cómo se vende

**Gancho**: «El auditor externo cobra 5 000–20 000 USD para revisar el 5 % de tus transacciones. Nosotros revisamos el 100 % cada mes, por menos de lo que cobran por hora.»

**Propuesta de valor**: cobertura del 100 % de transacciones vs el muestreo tradicional; hallazgos antes del cierre (no 15 días después); evidencia digital de que la empresa auditó internamente (reduce el riesgo en auditorías externas).

| Tier | Qué incluye | Precio USD/mes |
|------|-------------|----------------|
| Básico | 1 entidad, hasta 2 000 tx/mes, PDF básico | 200–400 |
| Estándar | 5 000 tx/mes, priorización de riesgo, Slack alert | 400–900 |
| Premium | tx ilimitadas, multi-entidad, integración ERP push | 900–2 000 |

Setup: 2 000–5 000 USD (calibración de umbrales con historial del cliente, golden set de 50 findings etiquetados por el revisor fiscal del cliente).

## 10. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **Falso positivo de duplicado**: el agente marca como duplicado un pago legítimo de cuota mensual | Alta | Medio | Los falsos positivos son inofensivos si el workflow requiere que un humano apruebe antes de cualquier acción. El reporte es informativo, no actúa automáticamente. Calibrar el umbral de días para duplicados según la frecuencia de pagos del cliente. |
| **Falso negativo de fraude**: el agente no detecta un esquema sofisticado de fraude | Media | Muy alto | El agente no es un sustituto de la auditoría forense. El reporte lo dice explícitamente. Complementa, no reemplaza, al revisor fiscal. |
| **Historial insuficiente en clientes nuevos**: sin 12 meses de historial, los rangos estadísticos son poco confiables | Alta | Medio | Para clientes < 6 meses, usar estadísticas sectoriales (configurable). Documentar la limitación en el reporte. |
| **Datos sensibles de proveedores y montos en prompts**: NIT, montos, nombres | Alta | Medio | Son datos de la empresa, no PII de personas naturales (excepto si el proveedor es persona natural). Separar el caso persona natural y manejar con mayor cuidado. Configurar en política de datos. |
| **Costo de LLM en auditorías grandes**: 5 000 transacciones con contexto histórico | Media | Bajo | Solo los findings candidatos a duplicado difuso y la redacción final van al LLM. El 65 % del trabajo es código determinístico. Costo estimado por corrida: < 3 USD para 5 000 tx. |

## 11. Variantes por industria

### Instancia 1 — Manufactura (`acme`)

**Datos típicos**: 1 000–3 000 transacciones/mes, 80–150 proveedores activos (insumos industriales, mantenimiento, energía), comprobantes tipo GR y FC dominantes. Los montos de insumos tienen alta variabilidad por precio de commodity.

**Delta determinístico**: los montos de insumos industriales fluctúan con el precio del mercado (acero, plástico, solventes). El umbral de `OUT_OF_RANGE` se ajusta mensualmente con un índice de precios del sector (e.g., IPP de manufactura del DANE). Sin este ajuste, el agente genera demasiados falsos positivos en meses de alta inflación.

**Delta agéntico**: ACME tiene proveedores de mantenimiento que facturan por proyecto, no por monto fijo. El agente distingue entre un pago de mantenimiento correctivo (variable, legítimo) y uno que coincide sospechosamente con otro pago reciente al mismo proveedor.

**Regulación**: en manufactura colombiana, las retenciones en la fuente (comprobantes ND de retención) deben corresponderse con las facturas de compra. El agente verifica que cada retención tenga su factura asociada.

**Precio orientativo**: 400–900 USD/mes; ACME tiene ~120 proveedores y ~2 000 transacciones/mes.

---

### Instancia 2 — Salud privada (`sanrafael`)

**Datos típicos**: 500–1 500 transacciones/mes, facturación médica con numeración regulada (resolución DIAN de facturación electrónica), tipos de documento específicos (FC médica, NC por glosa, ND por ajuste de EPS).

**Delta determinístico**: la numeración de facturas médicas electrónicas está regulada por la DIAN. Un gap en la secuencia es un finding crítico de cumplimiento, no solo contable. El agente verifica la secuencia completa de facturas electrónicas del período (distinto de los comprobantes internos del ERP).

**Delta agéntico**: las notas crédito (NC) de la clínica son, en su mayoría, glosas aceptadas de EPS. Pero algunas NC pueden ser ajustes incorrectos que reducen el ingreso sin soporte. El agente revisa cada NC > 500 000 COP para verificar si tiene un número de glosa asociado en el sistema de radicación de glosas. Si no lo tiene, es un finding de riesgo.

**Regulación**: la Resolución 2275 de 2023 (MSPS Colombia) exige trazabilidad completa de la facturación médica. El reporte del agente incluye la verificación de numeración DIAN como sección obligatoria.

**Precio orientativo**: 500–1 200 USD/mes; la complejidad regulatoria de salud justifica un precio mayor.

## 12. Módulos técnicos relacionados

| Módulo | Por qué aplica |
|--------|---------------|
| **E05** — Temporal | Este es el caso de uso que ancla E05: el Schedule `día 2 del mes` y las activities `ingest_erp_period` + `run_audit_agent` + `persist_audit_report` se implementan literalmente en E05. |
| **E01** — Anthropic SDK | Los nodos `classify_fuzzy_dups`, `prioritize_findings`, y `draft_report` son loops tool_use. E01 enseña exactamente ese patrón. El ejercicio 2 de E01 usa `monthly_audit` como caso. |
| **C03** — Multitenancy | Cada query de `sql_query` en este grafo lleva `tenant_id`. La regla «un tenant no puede ver los datos de otro» es crítica en un agente de auditoría. C03 enseña el filtro en el repo. |
| **D04** — Observabilidad | El trace de Phoenix del `run_audit_agent` es el ejemplo principal de D04: muestra spans de los nodos determinísticos (rápidos, sin costo LLM) y agénticos (lentos, con costo). El lector aprende a identificar el cuello de botella. |
| **A06** — Dataclasses | El tipo `Finding(id, type, transaction, risk_level, description, confidence)` es el ejercicio central de A06 en el dominio de auditoría. |
| **E03** — Skills | El `monthly_audit` skill (ver `app/integrations/skills/monthly_audit/SKILL.md`) es el caso de uso de E03. El lector porta ese skill a LangGraph en el Capstone. |

## 13. Errores típicos

**1. Umbral de duplicado estricto sin ventana de tiempo.**
*Síntoma*: el agente marca como duplicado el arrendamiento mensual de ACME porque el hash del pago de marzo coincide con el de abril (mismo proveedor, mismo monto exacto).
*Causa*: el hash no incluye el período contable; la ventana de 60 días captura pagos recurrentes legítimos.
*Cómo evitarlo*: incluir el mes del período en el hash o restringir la ventana de comparación al mismo mes. Alternativamente, añadir una lista blanca de proveedores con pagos recurrentes aprobados.

**2. Estadísticas históricas calculadas con datos de menos de 5 transacciones.**
*Síntoma*: un proveedor nuevo de Clínica San Rafael recibe un pago legítimo de $8 M COP; el agente lo marca `OUT_OF_RANGE` porque la media histórica se calculó con una sola transacción de $500 000 COP.
*Causa*: el pipeline no verifica el tamaño de la muestra antes de calcular σ; con N < 3 la desviación estándar no es representativa.
*Cómo evitarlo*: si `count_historico < 5`, usar estadísticas del sector configuradas en onboarding en lugar de estadísticas del proveedor específico. Documentarlo en el finding.

**3. Reporte enviado sin sign-off cuando hay findings críticos.**
*Síntoma*: el CFO recibe un reporte con un `DUPLICATE_STRICT` de $45 M COP sin haberse escalado previamente.
*Causa*: el nodo `check_critical` tiene un umbral configurado en COP pero el monto del finding está en miles de pesos por error de parseo.
*Cómo evitarlo*: normalizar siempre los montos a la unidad monetaria base (pesos enteros) en el nodo de ingesta, antes de cualquier comparación. Incluir tests de unidad para el parseo de montos con separadores de miles.

**4. El agente redacta findings en lenguaje técnico de base de datos, no de auditor.**
*Síntoma*: el finding dice «hash collision detected on field proveedor_nit=900123456» en lugar de usar terminología de revisión fiscal.
*Causa*: el prompt del nodo `draft_report` no especifica la audiencia ni el estilo esperado.
*Cómo evitarlo*: el system prompt de `draft_report` debe incluir explícitamente el rol («eres un revisor fiscal colombiano redactando hallazgos para el CFO») y un ejemplo del formato esperado.

## 14. Pregúntale al tutor

1. «Explícame cómo ajustaría el umbral de `OUT_OF_RANGE` para ACME si los precios de sus insumos industriales fluctúan con el IPP del DANE. ¿El umbral debería ser fijo o dinámico?»
2. «Audita mi prompt actual del nodo `classify_fuzzy_dups` para Clínica San Rafael y dime qué contexto adicional necesita para distinguir entre un duplicado de pago y una cuota mensual legítima de arrendamiento médico.»
3. «Genera el código mínimo del nodo `detect_gaps` en Python que verifica la secuencia completa de facturas electrónicas DIAN para un período dado y devuelve la lista de números faltantes.»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Implementar los cinco detectores determinísticos (duplicado estricto, gaps, rango, proveedor nuevo, estadísticas históricas) sin invocar un LLM en ninguno de ellos.
- Decidir cuándo un finding requiere escalamiento inmediato al CFO antes de completar el reporte.
- Diseñar el prompt del nodo `draft_report` para que los findings salgan en el formato y tono que espera un revisor fiscal colombiano o mexicano.
- Calibrar los umbrales de riesgo (σ, ventana de duplicados, monto crítico) con los datos históricos del tenant en el onboarding.
- Estimar el costo por corrida de auditoría para un tenant con 5 000 transacciones mensuales.

## 16. Módulos previos recomendados

| Módulo previo | Por qué te prepara |
|---------------|-------------------|
| **A06** — Dataclasses | El tipo `Finding(id, type, transaction, risk_level, description, confidence)` debe estar definido antes de construir cualquier nodo del grafo; A06 enseña exactamente ese patrón. |
| **C03** — Multitenancy | Cada `sql_query` de historial lleva `tenant_id`; sin entender el patrón de C03 es fácil cruzar datos de ACME con los de Clínica San Rafael. |
| **E01** — Anthropic SDK | Los nodos `classify_fuzzy_dups` y `draft_report` son loops `tool_use`; E01 enseña el ciclo completo antes de implementarlos. |
| **E05** — Temporal | El Schedule del día 2 del mes y la idempotencia de `persist_audit_report` son el núcleo de E05; esta ficha es el caso de uso que ancla ese módulo. |
| **D04** — Observabilidad | Distinguir en Phoenix qué nodos son determinísticos (rápidos, sin costo LLM) y cuáles son agénticos es la práctica central de D04 con este grafo. |
