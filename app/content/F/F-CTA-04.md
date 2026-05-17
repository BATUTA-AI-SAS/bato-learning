---
ext_id: F-CTA-04
slug: conciliacion-intercompania
track: F
dept: CTA
ord: 123
title: "Conciliación intercompañía (intercompany matching)"
summary: "Agente que empareja las transacciones AP de una entidad contra el AR de su contraparte dentro del mismo grupo, explica diferencias residuales de FX y cut-off, y propone los ajustes de eliminación."
related_modules: [A06, C01, C03, E01]
industries_instanced: [manufactura, energia]
tenants_in_examples: [acme, solenergy]
big_corp_vendors: [BlackLine Intercompany, SAP ICR, Trintech]
latam_tools: [excel-cross-company, siigo-grupos]
key_concepts: [AP-AR-matching, transfer-pricing, FX-diff, cut-off, eliminacion-intercompania, consolidacion]
estimated_minutes: 60
deterministic_share: 0.75
version: 1
---

## 1. Problema operativo

ACME Manufacturing tiene tres entidades: ACME Colombia (manufactura), ACME Distribución (ventas), y ACME Servicios (administración compartida). Cada mes, las tres entidades se facturan entre sí: Manufactura le vende a Distribución, Servicios le cobra honorarios de administración a las otras dos.

El problema: al cierre, los balances intercompañía no cuadran. La factura que Manufactura registra en su AR («ACME Distribución me debe $48 M COP») debería aparecer idéntica en el AP de Distribución («ACME Manufactura, $48 M COP»). Pero hay diferencias: diferente fecha de registro, diferente tasa de cambio si una entidad opera en USD, o simplemente una factura que una entidad registró y la otra aún no.

El contador grupo de SolEnergy Distribuidora tiene el mismo problema con sus dos filiales en Colombia y Ecuador: las transacciones cruzan en USD, el tipo de cambio varía entre el día de emisión y el día de registro, y al consolidar quedan diferencias que hay que explicar y eliminar.

Sin resolver la intercompañía, el balance consolidado tiene saldos que se cancelan entre sí pero que, si no se eliminan correctamente, distorsionan la imagen financiera del grupo.

## 2. Hoy en big corps

| Vendor | Producto | Capacidad clave | Inversión orientativa |
|--------|----------|-----------------|-----------------------|
| **BlackLine Intercompany** | Intercompany Hub | Match automático AP/AR entre entidades; workflow de aprobación bilateral; integración SAP/Oracle/Workday | 100–300 USD/usuario/mes; setup 30–100 k USD |
| **SAP ICR** | Intercompany Reconciliation | Nativo en SAP S/4HANA; matching en tiempo real; genera automáticamente los asientos de eliminación | incluido en SAP S/4HANA Finance; impl. 50–200 k USD |
| **Trintech Intercompany** | Cadency Intercompany | Workflow multilateral de aprobación; soporte multi-moneda; integración con ERPs heterogéneos | 100–300 USD/usuario/mes |

Estos productos asumen que todas las entidades del grupo usan el mismo ERP o tienen conectores certificados. Un grupo PYME LATAM con Siigo en Colombia y Alegra en Ecuador no tiene esa infraestructura.

## 3. PYME LATAM realista

- **Fuente por entidad**: cada entidad exporta su libro de transacciones intercompañía del ERP (Siigo en Colombia, Alegra/World Office en otras países, Contpaq en México). No hay un ERP único para el grupo.
- **Identificación de transacciones intercompañía**: el contador marca manualmente las transacciones intercompañía en el ERP con un código especial (e.g., cuenta contable «1405-IC» para cuentas por cobrar intercompañía). Esto es convención del cliente, no estándar.
- **Excel cross-company**: el método actual es exportar ambas entidades a Excel y cruzarlas a mano. Un contador de grupo puede pasar 2–3 días por mes en este proceso.
- **Multi-moneda**: si hay entidades en distintos países, la tasa de cambio es un factor. La DIAN en Colombia requiere usar la TRM (tasa de cambio oficial) del día de la transacción.

## 4. Datos típicos

| Atributo | AR entidad A (Siigo CSV) | AP entidad B (Siigo CSV) |
|----------|--------------------------|--------------------------|
| Formato | `comprobante,fecha,entidad_contraparte,factura_ref,monto_cop,monto_usd,cuenta_ic` | Idéntico formato, otra entidad |
| Frecuencia | Export mensual al cierre | Export mensual |
| Volumen | 20–200 transacciones IC por entidad/mes | Idem |
| Ejemplo fila A | `FC-2026-0812, 2026-04-15, ACME-DIST, FAC-0341, 48200000, 12050, 1405-IC` | — |
| Ejemplo fila B | `GR-2026-0293, 2026-04-16, ACME-MANU, FAC-0341, 48310000, 12050, 2205-IC` | — |

La diferencia entre las dos filas: la fecha de registro (15 vs 16 de abril) genera una diferencia de tasa de cambio COP/USD; el monto en COP difiere ($110 000 COP) pero el monto en USD coincide. Esto es un `FX_DIFF` legítimo, no un error.

## 5. Tramos determinísticos

1. **Ingesta multi-entidad**: lectura de los CSV de cada entidad del grupo. Identificación de las transacciones marcadas como intercompañía (por cuenta contable `*-IC` o por flag del ERP).
2. **Match exacto por referencia de factura**: el campo `factura_ref` es la referencia del documento original. Si `entidad_A.factura_ref == entidad_B.factura_ref` AND las entidades son contrapartes correctas, es un match exacto. Esto cubre el 60–70 % de los casos en grupos con buen discipline de referenciación.
3. **Cálculo de diferencias de monto**: para matches encontrados, `diff_monto = AR_monto - AP_monto`. Categorizar en `MATCH_EXACT` (diff = 0), `FX_DIFF` (diff explicado por tasa de cambio), `TIMING_DIFF` (una entidad no ha registrado aún), `UNEXPLAINED`.
4. **Verificación de cut-off**: transacciones registradas en los últimos 3 días del período en la entidad A pueden no estar en la entidad B (cruzaron el mes). Verificación determinística: si `fecha_A` está en los últimos 3 días del período y no hay match en B, categorizar como `TIMING_DIFF`.
5. **Cálculo de FX diff**: para transacciones multi-moneda, `FX_expected_diff = monto_usd × (TRM_fecha_A - TRM_fecha_B)`. Si `|diff_monto - FX_expected_diff| < tolerancia`, el residuo es explicado por FX. Las TRM históricas vienen de una tabla de referencia (Banco de la República Colombia).
6. **Generación de tabla de diferencias**: estructura `{par_entidades, factura_ref, AR_monto, AP_monto, diff_monto, categoria, explicacion_tecnica}`.
7. **Propuesta de asientos de eliminación**: para cada match exacto, generar el asiento de eliminación estándar (débito AP intercompañía, crédito AR intercompañía). Aritmética sobre los montos matcheados.

## 6. Tramos agénticos

1. **Explicación de diferencias residuales (`UNEXPLAINED`)**: el agente recibe las diferencias que no se explican por FX ni por cut-off, y las analiza. Puede ser un precio de transferencia aplicado diferente en las dos entidades, una comisión de intermediación que una entidad incluyó y la otra no, o un ajuste retroactivo que no tiene contrapartida. El agente describe la causa probable basándose en el contexto del grupo y propone la línea de investigación. **No es regla** porque las causas de diferencias residuales en intercompañía son altamente específicas al contexto de cada grupo empresarial.
2. **Propuesta de ajuste sugerido con justificación**: cuando la diferencia no es un error sino una diferencia legítima (e.g., la tasa de transfer pricing cambió a mitad del mes), el agente redacta el ajuste contable sugerido con la justificación en lenguaje técnico-contable. «Se recomienda registrar un asiento de ajuste en ACME Distribución por $110 000 COP (diferencia de TRM entre fecha de emisión y fecha de registro, acorde con la política de precios de transferencia del grupo).» La redacción del ajuste y su justificación no es una plantilla que funcione para todos los casos.
3. **Detección de diferencias sistemáticas**: si el agente detecta que el mismo par de entidades tiene diferencias del mismo tipo todos los meses (e.g., siempre hay un FX_DIFF de ~$100 000 COP), sugiere una política de ajuste automático para el futuro. Esta sugerencia requiere razonamiento sobre el patrón histórico y la política del grupo.
4. **Fallback humano**: cualquier `UNEXPLAINED` con monto > umbral_materialidad (configurable por grupo; default: 1 % del total intercompañía del período) requiere aprobación del controller del grupo antes de incluir el ajuste en el reporte. El agente no cierra diferencias sin evidencia ni sin aprobación humana.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_entity_A] → erp_fetch_transactions(erp=siigo, period, account="IC", tenant=acme_manu)
[ingest_entity_B] → erp_fetch_transactions(erp=siigo, period, account="IC", tenant=acme_dist)
  ↓ (paralelo)
[normalize_both] → normalización de fechas, montos, referencias (determinístico)
  ↓
[match_by_ref] → match exacto por factura_ref (determinístico)
  ↓               → sets: MATCHED, UNMATCHED_A, UNMATCHED_B
[classify_diffs] → FX diff + cut-off check (determinístico)
  ↓               → FX_DIFF, TIMING_DIFF, UNEXPLAINED
[load_trm] → sql_query(tabla_TRM_historica, tenant=grupo)
  ↓
[verify_fx] → cálculo de FX_expected_diff (determinístico)
  ↓
[explain_unexplained] → LLM analiza UNEXPLAINED (agéntico)
  ↓                     tool: sql_query(contexto_grupo + historial_IC, tenant=grupo)
[check_materiality] → router: ¿UNEXPLAINED > umbral_materialidad?
  ├─ SÍ → [request_controller] → interrupt_before → send_email(controller, tenant)
  │           ↓ (controller aprueba o corrige)
  └─ NO ↓
[generate_elimination_entries] → asientos de eliminación (determinístico)
  ↓
[propose_adjustments] → LLM redacta ajustes sugeridos (agéntico)
  ↓
[write_report] → write_report(kind=xlsx, "Conciliación IC abril 2026 grupo ACME", tenant=grupo)
  ↓
END
```

> [!nota]
> Los nodos `ingest_entity_A` e `ingest_entity_B` son **paralelos** (`asyncio.gather`). En un grupo con 5 entidades, se ejecutan los 5 en paralelo. Esto es el patrón de A07 (async) aplicado a un flujo real.

### Activities Temporal (Schedule: día 3 del mes siguiente)

- `ingest_ic_data(tenant_group, period, entities)` — lista de entidades del grupo; una activity por entidad.
- `run_intercompany_agent(tenant_group, period, dataset_id)` — ejecuta el grafo; timeout 15 min.
- `persist_ic_report(tenant_group, period, payload)` — `idempotency_key = "ic:{tenant_group}:{period}"`.

### Tools necesarias

| Tool | Uso |
|------|-----|
| `erp_fetch_transactions` | Transacciones IC de cada entidad |
| `sql_query` | TRM histórica, contexto del grupo, historial de diferencias IC |
| `write_report` | Reporte XLSX con matches, diferencias, y asientos de eliminación |
| `send_email` | Notificación al controller del grupo |

## 8. Salida y entrega

**Reporte XLSX** con cuatro pestañas:

1. `Resumen grupo`: total AR IC por entidad, total AP IC por entidad, total diferencias por categoría, estado (listo para consolidar / pendiente de aprobación).
2. `Matches`: pares matcheados con su monto, diferencia, categoría y asiento de eliminación propuesto.
3. `Diferencias`: transacciones sin match o con diferencias, categoría, explicación del agente, acción recomendada.
4. `Asientos`: tabla de asientos de eliminación listos para importar al ERP consolidador (si el grupo tiene uno) o para registrar manualmente.

**Email al controller del grupo** el día 3, con el XLSX adjunto y un resumen del estado de la conciliación intercompañía.

## 9. Cómo se vende

**Gancho**: «La conciliación intercompañía le toma al contador 3 días cada mes y el resultado siempre tiene diferencias que se explican en la auditoría. Nosotros la automatizamos y dejamos solo las diferencias reales en tu bandeja.»

**Propuesta de valor**: reducción del ciclo de conciliación IC de 3 días a 4 horas; trazabilidad completa de cada match y diferencia; asientos de eliminación listos para el ERP consolidador.

| Tier | Qué incluye | Precio USD/mes |
|------|-------------|----------------|
| Básico | 2 entidades, moneda única, reporte XLSX | 200–400 |
| Estándar | hasta 5 entidades, multi-moneda, FX diff automático | 400–900 |
| Premium | entidades ilimitadas, integración ERP consolidador, SLA | 900–2 000 |

Setup: 2 500–6 000 USD (mapeo de cuentas IC por entidad, configuración de parejas de entidades, calibración de tolerancias, golden set de 2 períodos de referencia).

## 10. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **Referencias de factura inconsistentes**: las dos entidades usan referenciación distinta y el match exacto falla | Alta | Alto | En el onboarding, el agente aprende los patrones de referenciación de cada par de entidades (e.g., entidad A pone «FAC-0341», entidad B pone «FACT0341»). Se crea una tabla de mapeo de prefijos. |
| **TRM desactualizada**: la tabla de TRM no incluye los días del período reciente | Alta | Medio | La tabla de TRM se actualiza automáticamente desde la API del Banco de la República (Colombia) o Banxico (México) al inicio de cada corrida. Alertar si falla la actualización. |
| **Diferencia `UNEXPLAINED` que el agente no puede explicar**: el agente dice «no sé» | Media | Medio | El agente siempre escala el `UNEXPLAINED` al controller sin inventar una explicación. El reporte incluye la evidencia disponible y la pregunta específica para el controller. |
| **Multi-ERP con formatos distintos**: una entidad usa Siigo, otra usa Alegra con formato de export diferente | Alta | Medio | El módulo de ingesta tiene adaptadores por ERP (ver §3.6 de SHARED.md `erp_fetch_transactions`). Añadir un adaptador nuevo requiere trabajo técnico one-time de onboarding. |
| **Precios de transferencia mal documentados**: la diferencia IC puede ser un incumplimiento de transfer pricing que el agente no puede detectar sin el estudio de precios de transferencia | Media | Muy alto | El agente no audita transfer pricing; solo concilia montos. Si el grupo tiene riesgos de transfer pricing, necesita un asesor fiscal especializado. El reporte lo indica explícitamente. |

## 11. Variantes por industria

### Instancia 1 — Manufactura (`acme`)

**Datos típicos**: 3 entidades (manufactura, distribución, servicios compartidos), 50–150 transacciones IC/mes por par de entidades, moneda COP con excepciones en USD para importaciones de maquinaria.

**Delta determinístico**: las transacciones de servicios compartidos (Administración → Manufactura + Distribución) siguen una clave de distribución fija por mes (e.g., 40 % Manufactura, 60 % Distribución por número de empleados). El agente aplica la clave y verifica que los asientos en cada entidad reflejen el split correcto. Es aritmética sobre una tabla de distribución.

**Delta agéntico**: cuando Manufactura le vende a Distribución a un precio que incluye margen, el agente verifica que ese margen esté dentro del rango del estudio de precios de transferencia del grupo (si lo hay). Si el margen está fuera del rango documentado, genera un finding de transfer pricing. Esta verificación requiere interpretar el rango del estudio TP, que es un documento en PDF.

**Precio orientativo**: 350–750 USD/mes; ACME tiene 3 entidades y ~120 transacciones IC/mes.

---

### Instancia 2 — Energía / Utilities (`solenergy`)

**Datos típicos**: 2 entidades en distintos países (Colombia y Ecuador), transacciones en COP y USD, regulación sectorial de la CREG (Colombia) y ARCONEL (Ecuador) sobre precios entre filiales de distribuidoras de energía.

**Delta determinístico**: las diferencias de FX entre COP/USD son la norma, no la excepción. El agente calcula el FX_DIFF usando la TRM del Banco de la República (Colombia) y el tipo de cambio oficial del Banco Central del Ecuador. El cálculo es determinístico; la tabla de tipos de cambio se actualiza diariamente.

**Delta agéntico**: la CREG regula los precios máximos de las transacciones entre filiales de distribución. El agente verifica que el precio de la transacción IC esté dentro del rango regulado. Si hay una transacción IC que supera el precio máximo regulado, el finding es crítico (riesgo regulatorio directo). La interpretación del rango regulado requiere leer la resolución de la CREG del año en curso, que cambia anualmente.

**Regulación**: la CREG exige que las transacciones IC entre distribuidoras estén documentadas y justificadas antes de la presentación del reporte de gestión a la CREG. El reporte del agente es el insumo para ese reporte regulatorio.

**Precio orientativo**: 600–1 500 USD/mes; la complejidad multi-país y regulación sectorial justifican un precio mayor. Setup 4 000–8 000 USD.

## 12. Módulos técnicos relacionados

| Módulo | Por qué aplica |
|--------|---------------|
| **C03** — Multitenancy | La conciliación IC involucra múltiples `tenant_id` (una por entidad del grupo) que se deben aislar entre sí pero cruzar para el matching. C03 enseña exactamente el patrón: cómo filtrar por tenant pero autorizar queries cross-tenant para el controller del grupo. |
| **A07** — Async | Los nodos de ingesta de las entidades corren en paralelo (`asyncio.gather`). El ejemplo de A07 puede usar exactamente este caso: «ingestar 5 entidades en paralelo reduce el tiempo de 25 a 5 segundos». |
| **C01** — SQLAlchemy async | La tabla de TRM histórica, el historial de diferencias IC, y los asientos de eliminación se almacenan en DB. C01 enseña el modelo ORM y la query de búsqueda cross-entidad con JOIN. |
| **E01** — Anthropic SDK | Los nodos `explain_unexplained` y `propose_adjustments` son loops tool_use. El modelo recibe el contexto del grupo y emite JSON estructurado con la explicación y el ajuste. |
| **A06** — Dataclasses | El tipo `ICTransaction(entity, counterparty, invoice_ref, amount_local, amount_usd, date, account_ic)` y el tipo `ICDiff(pair, invoice_ref, ar_amount, ap_amount, diff, category, explanation)` son los ejercicios naturales de A06. |

## 13. Errores típicos

**1. Ingestar las dos entidades secuencialmente en lugar de en paralelo.**
*Síntoma*: con cinco entidades del grupo, el tiempo de ingesta es 5× el de una sola entidad; el workflow supera el timeout de 15 minutos en grupos medianos.
*Causa*: el código usa `await ingest_entity(A)` seguido de `await ingest_entity(B)` en lugar de `asyncio.gather`.
*Cómo evitarlo*: usar `asyncio.gather(*[ingest_entity(e) for e in entities])`. El módulo A07 enseña exactamente este patrón; completarlo antes de implementar esta ficha es un prerequisito directo.

**2. Match por referencia de factura sensible a prefijos de ERP distintos.**
*Síntoma*: ACME Manufactura registra la referencia como «FC-2026-0812»; ACME Distribución la registra como «FACT-2026-0812». El match exacto falla y la transacción queda como `UNMATCHED` cuando en realidad sí existe la contraparte.
*Causa*: el onboarding no mapeó los prefijos de referencia entre las dos entidades; el match busca igualdad exacta de string.
*Cómo evitarlo*: durante el onboarding, construir una tabla `prefix_map(entity_a_prefix, entity_b_prefix)` para cada par. El match normaliza las referencias eliminando los prefijos antes de comparar.

**3. TRM aplicada a la fecha del registro contable, no a la fecha de la transacción.**
*Síntoma*: una transacción emitida el 30 de abril pero registrada en contabilidad el 2 de mayo usa la TRM del 2 de mayo; la contraparte usó la TRM del 30 de abril. La diferencia de FX calculada no cuadra con el `FX_expected_diff`.
*Causa*: el campo `fecha` del CSV de Siigo puede ser la fecha de registro, no la fecha de la transacción; el agente no distingue entre ambas.
*Cómo evitarlo*: el modelo `ICTransaction` debe tener dos campos separados: `fecha_transaccion` y `fecha_registro`. El cálculo de FX siempre usa `fecha_transaccion`. Validar en ingesta que ambos campos estén presentes.

**4. Diferencias `UNEXPLAINED` cerradas sin aprobación del controller porque el monto individual está por debajo del umbral, pero la suma del mes lo supera.**
*Síntoma*: hay 15 diferencias de $60 000 COP cada una; ninguna supera el umbral de materialidad de $500 000 COP por diferencia, pero suman $900 000 COP. Se cierran sin revisión humana.
*Causa*: el router `check_materiality` evalúa cada diferencia individualmente, no la suma del batch `UNEXPLAINED`.
*Cómo evitarlo*: el router evalúa dos condiciones: `any(diff > umbral_individual)` OR `sum(unexplained) > umbral_total`. Ambas disparan el escalamiento al controller.

## 14. Pregúntale al tutor

1. «Explícame cómo adaptaría el nodo `verify_fx` para SolEnergy si las transacciones cruzan entre COP y USD usando simultáneamente la TRM del Banco de la República y la tasa oficial del Banco Central del Ecuador. ¿Cómo gestiono las dos fuentes de tipos de cambio?»
2. «Audita mi diseño actual del módulo de ingesta para el grupo ACME y dime qué le falta para soportar una entidad adicional que usa Alegra en lugar de Siigo, sin modificar el resto del grafo.»
3. «Genera el código mínimo del nodo `match_by_ref` en Python que normaliza los prefijos de referencia usando la tabla `prefix_map` del tenant antes de hacer el join.»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar la ingesta paralela de múltiples entidades del grupo usando `asyncio.gather` con un adaptador por ERP.
- Implementar el match AP/AR con normalización de prefijos de referencia configurable por par de entidades.
- Calcular el `FX_expected_diff` usando TRM por fecha de transacción y clasificar correctamente las diferencias como `FX_DIFF`, `TIMING_DIFF` o `UNEXPLAINED`.
- Configurar el escalamiento al controller con umbral dual (por diferencia individual y por suma del batch).
- Dimensionar el servicio para un grupo con 2–5 entidades en distintos países con ERPs heterogéneos.

## 16. Módulos previos recomendados

| Módulo previo | Por qué te prepara |
|---------------|-------------------|
| **A07** — Async | La ingesta paralela de entidades es el caso de uso textual de A07; sin ese módulo el patrón `asyncio.gather` no está claro y el pipeline queda secuencial. |
| **C03** — Multitenancy | El matching cross-entidad requiere queries autorizadas entre `tenant_id` distintos del mismo grupo; C03 enseña cómo implementar esa excepción de forma segura. |
| **C01** — SQLAlchemy async | La tabla de TRM histórica y el historial de diferencias IC requieren el modelo ORM y la query de lookup por fecha que enseña C01. |
| **A06** — Dataclasses | Los tipos `ICTransaction` e `ICDiff` deben estar definidos con tipos precisos antes de implementar cualquier nodo; A06 enseña el patrón con validación Pydantic. |
| **E01** — Anthropic SDK | Los nodos `explain_unexplained` y `propose_adjustments` son loops `tool_use`; E01 enseña el ciclo completo con salida JSON estructurada. |
