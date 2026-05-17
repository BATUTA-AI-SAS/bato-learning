---
ext_id: F-FIN-03
slug: cierre-mensual-asistido
track: F
dept: FIN
ord: 102
title: "Cierre mensual asistido (checklist agéntico)"
summary: "Agente que valida el checklist de cierre contable, clasifica hallazgos como bloqueantes o informativos, y genera el reporte de estado para el equipo de finanzas."
related_modules: [A06, A07, C02, D04, E03, E05]
industries_instanced: [manufactura, salud]
tenants_in_examples: [acme, sanrafael]
big_corp_vendors: [BlackLine, FloQast, Trintech]
latam_tools: [siigo, contpaq, world_office]
key_concepts: [close-checklist, journal-entries, validaciones, holds, sign-off, accruals, depreciacion]
estimated_minutes: 60
deterministic_share: 0.6
version: 1
---

## 1. Problema operativo

El equipo de finanzas de ACME Manufacturing cierra cada mes en un proceso que dura 5–7 días laborales. El primero de esos días lo pasa verificando manualmente que todos los pasos estén completos: ¿conciliaciones bancarias listas?, ¿depreciaciones corridas?, ¿accruals registrados?, ¿balances cuadran? Cuando algo falta, hay que rastrear quién lo olvidó y enviar correos de seguimiento.

El segundo problema: cuando el CFO pregunta «¿por qué el gasto de personal subió 12 % este mes respecto al anterior?», nadie tiene la respuesta preparada. Se investiga sobre la marcha, atrasando el cierre.

La contadora general de Clínica San Rafael enfrenta la misma situación multiplicada: los centros de costo (urgencias, cirugía, hospitalización) cierran en momentos distintos, y una sola cuenta sin cerrar bloquea el cierre consolidado.

## 2. Hoy en big corps

| Vendor | Producto | Capacidad clave | Inversión orientativa |
|--------|----------|-----------------|-----------------------|
| **BlackLine** | Financial Close Management | Checklist por tarea con responsable, fecha límite, status; integración con SAP/Oracle para auto-completar tareas | 80–250 USD/usuario/mes; setup 25–80 k USD |
| **FloQast** | Close Management + AutoRec | Checklist accountant-friendly; AI-powered matching; integración Excel nativa; menos infraestructura que BlackLine | 60–150 USD/usuario/mes; setup 10–30 k USD |
| **Trintech Cadency** | Financial Close | Predicción de excepciones; tareas automáticas; certificaciones de cuentas | 100–300 USD/usuario/mes; setup 40–150 k USD |

FloQast es el más cercano a una PYME grande (50–500 empleados) pero su precio y el requisito de integración con ERP occidental lo dejan fuera del alcance de la PYME LATAM promedio.

## 3. PYME LATAM realista

- **Checklist actual**: documento Word o pestaña Excel con las tareas del cierre. El responsable lo actualiza a mano.
- **ERP**: Siigo (Colombia), Contpaq (México), World Office (Colombia). Todos exportan reportes de saldos de cuentas en CSV o PDF.
- **Depreciaciones y accruals**: se calculan en Excel aparte y se importan manualmente al ERP como asientos de diario.
- **Validación de balances**: el contador verifica que Activo = Pasivo + Patrimonio en una hoja de balance que exporta del ERP.
- **Equipo de cierre**: 1–3 personas (contador general, auxiliar, revisor fiscal externo que firma). El cierre se basa en que el contador recuerda qué falta.

## 4. Datos típicos

| Ítem del checklist | Fuente de verificación | Verificable automáticamente |
|--------------------|------------------------|----------------------------|
| Conciliaciones bancarias completas | Reporte de conciliación (F-FIN-01) | Sí, si F-FIN-01 ya corrió |
| Depreciaciones del período corridas | Export saldos cuenta «depreciación» del ERP | Sí, si el saldo cambió vs mes anterior |
| Accruals registrados | Lista de accruals esperados vs asientos reales | Parcialmente (requiere lista de fuente) |
| Balance cuadra (A = P + PAT) | Export balance general ERP | Sí, aritmética |
| Novedades de nómina reflejadas | Saldo cuentas de personal vs nómina aprobada | Sí, comparación numérica |
| Documentación soporte subida | Carpeta de soporte en drive/bucket | Parcialmente (verificar existencia de archivos) |
| Variaciones > 10 % entre meses explicadas | Comparativo meses | Detección automática; explicación agéntica |

**Ejemplo de fila de balance**: `4105,Ingresos operacionales,COP,2026-04-30,124 820 000`

## 5. Tramos determinísticos

1. **Descarga de saldos del ERP**: lectura del CSV de cuentas con saldos al cierre (`erp_fetch_transactions` con `account="balances"` y `period="2026-04"`).
2. **Verificación de ecuación contable**: `assert abs(total_activo - (total_pasivo + total_patrimonio)) < tolerancia`. Si falla, el checklist se bloquea aquí.
3. **Verificación de conciliaciones**: consulta si F-FIN-01 corrió para el período y tiene estado `CONCILIADO` o `PENDIENTE_REVISIÓN_APROBADA`.
4. **Verificación de depreciaciones**: comparación del saldo de la cuenta de depreciación acumulada con el saldo del mes anterior. Si la diferencia es cero y hay activos fijos activos, hay una alerta.
5. **Detección de variaciones materiales**: para cada cuenta del P&L, calcular `delta_pct = (saldo_actual - saldo_anterior) / abs(saldo_anterior)`. Marcar como `VARIACIÓN_MATERIAL` si `|delta_pct| > umbral_material` (configurable por tenant; default: 10 %).
6. **Estado del checklist**: clasificar cada tarea en `OK` / `PENDIENTE` / `BLOQUEANTE`. Agregación del estado global del cierre.

## 6. Tramos agénticos

1. **Clasificar hallazgo: informativo vs bloqueante**: el agente recibe la lista de tareas en estado `PENDIENTE` o `VARIACIÓN_MATERIAL` y decide cuáles bloquean el cierre y cuáles son informativos. Esta decisión no tiene regla cerrada: una variación del 15 % en gastos de personal puede ser bloqueante si es por un error de nómina, o informativa si fue un bono aprobado por el directorio. El agente cruza la variación con las notas del período (texto libre) y con el historial para decidir.
2. **Redactar explicación de variaciones**: para cada `VARIACIÓN_MATERIAL`, el agente produce un párrafo explicativo que el CFO puede incluir en el reporte al directorio. «El gasto de personal aumentó 12 % vs marzo por el bono semestral pagado el 28 de abril (aprobado por acta de directorio 2026-04-20).» El agente sintetiza las notas del período y los datos numéricos; no tiene una plantilla que capture todos los casos.
3. **Priorización del orden de cierre en multi-cost-center (Clínica San Rafael)**: cuando múltiples centros de costo están en cierre simultáneo, el agente sugiere el orden de cierre basándose en cuál bloquea a cuál (dependencias). No hay una regla fija; depende del mapa de cuentas compartidas entre centros.
4. **Fallback humano**: cualquier `VARIACIÓN_MATERIAL` > 20 % sin nota explicativa genera un `interrupt_before` antes de emitir el reporte de cierre. El agente redacta la pregunta para el contador («El gasto de servicios externos subió 23 %. ¿Hay un contrato nuevo que debería estar documentado?») y espera respuesta antes de continuar.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_balances] → erp_fetch_transactions(erp, period="2026-04", account="all", tenant)
  ↓
[verify_equation] → A = P + PAT (determinístico, Python puro)
  ├─ FAIL → [block_close] → send_email(CFO, "Balance no cuadra") → END
  └─ OK ↓
[run_checklist] → verificación paralela de 6 ítems (determinístico)
  ↓
[flag_variances] → delta_pct por cuenta P&L (determinístico)
  ↓
[classify_findings] → LLM clasifica hallazgos: bloqueante/informativo (agéntico)
                       tool: sql_query(notas_periodo, tenant)
  ↓
[check_blockers] → router: ¿hay hallazgos bloqueantes?
  ├─ SÍ → [request_resolution] → interrupt_before → send_email(contador, preguntas)
  │           ↓ (contador responde, hallazgos resueltos)
  └─ NO ↓
[draft_variance_notes] → LLM redacta explicaciones por variación (agéntico)
  ↓
[write_report] → write_report(kind=pdf, "Reporte de cierre abril 2026", tenant)
  ↓
[notify] → send_email(to=[CFO, revisor_fiscal], tenant)
  ↓
END
```

### Activities Temporal (Schedule: día 1 y día 3 de cada mes)

- `ingest_close_data(tenant, period)` — descarga balances y notas del ERP.
- `run_close_agent(tenant, period)` — ejecuta el grafo; timeout 15 min.
- `persist_close_report(tenant, period, payload)` — `idempotency_key = "close:{tenant}:{period}"`.

### Tools necesarias

| Tool | Uso |
|------|-----|
| `erp_fetch_transactions` | Saldos de todas las cuentas del ERP |
| `sql_query` | Notas del período, historial de variaciones, estado de F-FIN-01 |
| `write_report` | Reporte de cierre PDF |
| `send_email` | Notificación al CFO, contador y revisor fiscal |

## 8. Salida y entrega

**Reporte de cierre PDF** con cuatro secciones:

1. **Estado del checklist**: tabla con cada ítem, responsable, estado (`OK` / `PENDIENTE` / `BLOQUEANTE`), fecha de verificación.
2. **Balance general resumido**: activos, pasivos, patrimonio, con delta vs mes anterior.
3. **Variaciones materiales**: tabla con cuenta, saldo actual, saldo anterior, delta %, categoría (bloqueante/informativa), nota explicativa del agente.
4. **Firmas**: espacio para firma digital del contador y del revisor fiscal (el agente no firma; solo prepara el documento).

**Email** al CFO el día 3 del mes siguiente con el PDF adjunto y un resumen de 3 líneas del estado del cierre.

## 9. Cómo se vende

**Gancho**: «El cierre mensual les toma 7 días. Con el agente, el día 1 ya saben qué falta; el día 3 tienen el reporte listo para el directorio.»

**Propuesta de valor**: reducción del ciclo de cierre de 7 a 3 días; trazabilidad de cada decisión del cierre; narrativa de variaciones lista para el directorio sin trabajo manual.

| Tier | Qué incluye | Precio USD/mes |
|------|-------------|----------------|
| Básico | 1 entidad, checklist automático, reporte PDF | 200–400 |
| Estándar | multi-cost-center, notas de variación, integración F-FIN-01 | 400–800 |
| Premium | multi-entidad, firma digital, SLA día 2 | 800–1 500 |

Setup: 2 000–5 000 USD (mapeo del chart of accounts, definición del checklist por tenant, golden set de 3 meses de referencia).

## 10. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **Clasificación errónea bloqueante/informativo**: el agente marca como informativo algo que debería bloquear | Baja | Muy alto | Umbral duro: cualquier variación > 20 % sin nota siempre es bloqueante independientemente de la clasificación del LLM. Regla determinística primero. |
| **Accruals no detectados**: el agente no sabe qué accruals deberían registrarse | Alta | Alto | El onboarding captura la lista de accruals recurrentes del cliente (arrendamientos, seguros, honorarios). El agente verifica contra esa lista; sin la lista, no puede verificar. Documentar la limitación. |
| **Datos del ERP incompletos**: el export de cierre se corre antes de que todos los asientos estén ingresados | Alta | Alto | El agente registra el timestamp del export y lo incluye en el reporte. El contador debe confirmar que el ERP está cerrado antes de correr el agente. |
| **PII de empleados en variaciones de nómina**: los datos de nómina pueden contener nombres | Media | Alto | No enviar datos individuales de nómina al LLM. Solo totales por categoría. |
| **Regulación de firma del revisor fiscal**: en Colombia, el revisor fiscal debe firmar el cierre. El agente no puede firmar ni sustituir esa firma | — | Legal | El reporte es siempre un borrador hasta que el revisor firma. El agente deja explícito el estado `BORRADOR` en el PDF. |

## 11. Variantes por industria

### Instancia 1 — Manufactura (`acme`)

**Datos típicos**: 150–300 cuentas activas, 3–5 centros de costo (producción, ventas, administración), depreciación de maquinaria como ítem fijo del checklist, inventario valorado a FIFO o promedio ponderado.

**Delta determinístico**: verificación del ajuste de inventario (costo de ventas vs variación de inventario) como ítem adicional del checklist. Es aritmética pura sobre los saldos de cuentas de inventario y COGS.

**Delta agéntico**: si la variación de materias primas supera el 15 %, el agente correlaciona con el índice de precios de insumos industriales (si el tenant lo configura) para decidir si la variación es de precio o de volumen. Esa distinción cambia el comentario del reporte.

**Precio orientativo**: 350–750 USD/mes; ACME tiene ~200 cuentas y 4 centros de costo.

---

### Instancia 2 — Salud privada (`sanrafael`)

**Datos típicos**: 4–8 centros de costo (urgencias, cirugía, laboratorio, hospitalización, administración), facturación por eventos médicos (EPS, particulares, ARL), cartera de difícil cobro como cuenta de ajuste importante.

**Delta determinístico**: verificación adicional de la provisión de cartera incobrable (porcentaje regulado por la Superintendencia de Salud en Colombia sobre la cartera > 180 días). El cálculo es una fórmula fija; el agente solo verifica que se aplicó.

**Delta agéntico**: en salud, las glosas (rechazos de factura por EPS) generan ajustes que llegan fuera del período de cierre. El agente identifica las glosas pendientes de respuesta y evalúa si su monto potencial justifica retrasar el cierre o se puede provisionar. Esa decisión mezcla política del cliente, riesgo de glosa, y contexto histórico de cada EPS.

**Regulación**: las clínicas colombianas reportan a la Superintendencia de Salud con plazos estrictos (día 10 del mes siguiente). El cierre agéntico debe respetar esa fecha límite como constraint duro.

**Precio orientativo**: 500–1 000 USD/mes; la complejidad de multi-cost-center y glosas justifica un precio mayor.

## 12. Módulos técnicos relacionados

| Módulo | Por qué aplica |
|--------|---------------|
| **E03** — Skills | El checklist de cierre es un skill por tenant: cada cliente tiene su propia lista de ítems, umbrales y responsables. E03 enseña cómo construir ese skill con slots variables. |
| **E05** — Temporal | El Schedule «día 1 del mes» y la actividad `run_close_agent` son ejemplos directos de E05. El ejercicio de diseño de E05 puede usar este caso. |
| **C02** — Alembic | Si el cliente añade un nuevo centro de costo, hay que migrar el schema. C02 enseña exactamente ese delta incremental. |
| **D04** — Observabilidad | El nodo `classify_findings` es el más caro en LLM (múltiples hallazgos). D04 enseña cómo leer el span de latencia en Phoenix y optimizar el batch. |
| **A06** — Dataclasses | El modelo `CloseChecklistItem(task, owner, status, note)` es el ejercicio natural de A06 en el dominio de cierre contable. |
| **A07** — Async | La verificación paralela de los 6 ítems del checklist es un `asyncio.gather` sobre funciones de validación independientes. A07 explica exactamente ese patrón. |

## 13. Errores típicos

**1. Checklist corrido antes de que el ERP esté efectivamente cerrado.**
*Síntoma*: la verificación de la ecuación contable pasa (A = P + PAT), pero a las 2 horas el auxiliar de Clínica San Rafael ingresa los últimos asientos del período y el balance cambia; el reporte de cierre ya fue enviado al CFO con datos incorrectos.
*Causa*: el agente corre el Schedule del día 1 a las 00:01 sin verificar que el contador haya marcado el ERP como «cerrado para el período».
*Cómo evitarlo*: añadir una tarea previa al checklist: el contador debe marcar en la app `erp_period_locked = true` para el período antes de que el agente empiece. Si no está marcado a las 08:00 del día 1, el agente envía un recordatorio y no corre el checklist.

**2. Variación material de nómina clasificada como «informativa» porque el agente no tiene acceso a las notas del período.**
*Síntoma*: el gasto de personal de ACME subió 18 % por un bono aprobado en junta; el agente lo clasifica como `informativo` porque en su contexto no hay nota que lo explique. El CFO lo ve en el reporte sin explicación y bloquea el cierre.
*Causa*: el nodo `classify_findings` recibe la variación pero el `sql_query(notas_periodo)` devuelve vacío porque las notas del período se guardan en un Excel de gestión, no en la DB del agente.
*Cómo evitarlo*: durante el onboarding, definir la fuente de notas del período (puede ser un campo de texto en la app o un Google Doc compartido). El nodo `classify_findings` no puede funcionar sin esa fuente configurada.

**3. Verificación de depreciaciones con saldo cero considerada como «OK» en el primer mes de un activo nuevo.**
*Síntoma*: ACME adquirió una máquina nueva en marzo; la depreciación de marzo debería ser $2 M COP, pero el saldo de la cuenta de depreciación acumulada es cero porque el activo se ingresó sin configurar la vida útil. El checklist marca el ítem como «OK» porque el saldo del mes anterior también era cero.
*Causa*: la validación solo compara el saldo actual vs el saldo del mes anterior; si ambos son cero, pasa.
*Cómo evitarlo*: cruzar la lista de activos fijos activos (con vida útil configurada) contra la cuenta de depreciación. Si hay activos activos y el movimiento de depreciación del período es cero, el ítem es `BLOQUEANTE`.

**4. Reporte de cierre emitido en estado `BORRADOR` sin marca de agua visible.**
*Síntoma*: el revisor fiscal externo recibe el PDF, lo firma pensando que es la versión final, y luego el contador descubre que hay variaciones bloqueantes sin resolver.
*Causa*: la marca de agua «BORRADOR» está en el pie de página con fuente pequeña; el revisor no la ve.
*Cómo evitarlo*: la marca de agua debe aparecer en diagonal en cada página con opacidad suficiente para ser visible en impresión. El campo `status` del documento debe estar en el encabezado de la primera página, no solo en el pie.

## 14. Pregúntale al tutor

1. «Explícame cómo adaptaría el nodo `run_checklist` para Clínica San Rafael, donde los 8 centros de costo tienen ítems de checklist distintos y algunos centros dependen de que otros estén cerrados primero. ¿Cómo modelo esas dependencias?»
2. «Audita mi configuración del umbral de variación material para ACME y dime si el 10 % predeterminado es apropiado para la cuenta de materias primas dado que sus precios fluctúan con commodities. ¿Qué umbral sugeriría?»
3. «Genera el código mínimo del nodo `verify_equation` en Python que lee el CSV de saldos del ERP y lanza una excepción con el detalle del desequilibrio si `|activo - pasivo - patrimonio| > tolerancia`.»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el checklist de cierre como un skill configurable por tenant con ítems, umbrales y responsables distintos por cliente.
- Implementar la verificación paralela de los ítems del checklist con `asyncio.gather` y agregar el estado global del cierre.
- Configurar la detección de variaciones materiales con umbrales por tipo de cuenta, no con un único umbral global.
- Decidir cuándo una variación es bloqueante vs informativa cruzando el delta numérico con las notas del período.
- Integrar el resultado de F-FIN-01 como ítem del checklist verificable automáticamente.

## 16. Módulos previos recomendados

| Módulo previo | Por qué te prepara |
|---------------|-------------------|
| **E03** — Skills | El checklist de cierre es un skill por tenant con slots variables; E03 enseña cómo construir esa abstracción antes de implementarla aquí. |
| **E05** — Temporal | El Schedule «día 1 del mes» con la actividad `run_close_agent` es el caso de uso directo de E05; completar ese módulo antes de implementar esta ficha evita errores de idempotencia. |
| **A07** — Async | La verificación paralela de los 6 ítems del checklist es `asyncio.gather`; sin A07 el código queda secuencial y 6× más lento. |
| **C02** — Alembic | Cuando el cliente añade un centro de costo nuevo, hay que migrar el schema; C02 enseña exactamente ese delta incremental que esta ficha necesita en producción. |
| **D04** — Observabilidad | El nodo `classify_findings` es el más caro en LLM; D04 enseña cómo identificar ese bottleneck en Phoenix y optimizar el batch de hallazgos. |
