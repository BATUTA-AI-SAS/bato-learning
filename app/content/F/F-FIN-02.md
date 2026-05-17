---
ext_id: F-FIN-02
slug: cashflow-forecast-13w
track: F
dept: FIN
ord: 101
title: "Forecast de cash flow rolling a 13 semanas"
summary: "Agente que actualiza cada lunes el forecast de tesorería a 13 semanas, detecta semanas críticas y redacta el ejecutivo para el CFO."
related_modules: [A06, B02, C01, E01, E05]
industries_instanced: [manufactura, serv-prof]
tenants_in_examples: [acme, consultorabc]
big_corp_vendors: [Workday Adaptive, Anaplan, Cube, Pigment]
latam_tools: [siigo, alegra, excel]
key_concepts: [receivables, payables, payroll-cycle, runway, escenarios, what-if, rolling-forecast]
estimated_minutes: 60
deterministic_share: 0.5
version: 1
---

## 1. Problema operativo

El CFO de ACME Manufacturing actualiza el forecast de caja cada lunes por la mañana. El proceso toma 3–4 horas: descarga las cuentas por cobrar y por pagar de Siigo, las pega en un Excel de 12 pestañas que construyó hace dos años, ajusta a mano las semanas donde sabe que un cliente grande suele pagar tarde, y escribe un email de media página para el comité directivo. Si se va de viaje, no hay nadie más que sepa usar ese Excel.

El riesgo real: en dos ocasiones han llegado a la semana 8 sin saberlo con anticipación. Un forecast actualizado automáticamente, que muestre las semanas de riesgo con 4–6 semanas de antelación, cambia las decisiones de inversión y de crédito.

## 2. Hoy en big corps

| Vendor | Producto | Capacidad clave | Inversión orientativa |
|--------|----------|-----------------|-----------------------|
| **Workday Adaptive** | Adaptive Planning (Cash Forecasting) | Modelos estadísticos sobre GL histórico; integración nativa con Workday HCM/FIN | 30–200 USD/usuario/mes; impl. 30–200 k USD |
| **Anaplan** | Treasury Planning model | Escenarios multidimensionales; recalcula en segundos; requiere Anaplan architect | desde 1 000 USD/usuario/mes; impl. 100 k+ USD |
| **Cube** | FP&A + cash | Spreadsheet-native; menos infraestructura que Anaplan | 1 500–5 000 USD/mes flat; impl. 10–30 k USD |
| **Billtrust Cash Forecasting** | 13-week AR forecast | Self-updating; ingiere open AR diario + historial de pagos; agentic alert layer | pricing negociado por volumen de AR |

Ninguno de estos se justifica para una PYME: los precios de implementación superan el presupuesto anual de software de un cliente LATAM de 50 empleados.

## 3. PYME LATAM realista

- **Fuente AR**: reporte de cuentas por cobrar de Siigo (CSV export, columnas `cliente,factura,fecha_vencimiento,monto_pendiente`) o Alegra (API REST disponible). Frecuencia: export manual semanal o pull automatizado.
- **Fuente AP**: reporte de cuentas por pagar del mismo ERP. Incluye proveedores con fecha de vencimiento acordada.
- **Fuente nómina**: archivo de nómina (fechas fijas de pago: 15 y último de mes en Colombia; 15 y 30 en México). Se ingresa una vez en onboarding; el agente lo toma como calendario fijo.
- **Flujos fijos**: cuotas de crédito, arrendamientos, servicios públicos. Se configuran en onboarding como tabla de compromisos.
- **Historial de cobro**: cuántos días tarda cada cliente en pagar desde el vencimiento. Existe implícito en el AR histórico de Siigo; hay que calcularlo.

## 4. Datos típicos

| Fuente | Columnas clave | Frecuencia | Volumen |
|--------|---------------|------------|---------|
| AR pendiente (Siigo CSV) | `cliente, factura, fecha_emision, fecha_vencimiento, monto_cop` | Semanal | 50–500 facturas abiertas |
| AP pendiente (Siigo CSV) | `proveedor, orden, fecha_vencimiento, monto_cop` | Semanal | 30–200 órdenes abiertas |
| Historial de pagos de clientes | `cliente, factura, dias_para_pago` | Mensual | 12–24 meses atrás |
| Nómina (configuración fija) | `fecha_pago, monto_nomina, frecuencia` | Onboarding | 2 filas (quincena/mes) |
| Flujos fijos | `concepto, dia_del_mes, monto` | Onboarding | 5–15 líneas |

Ejemplo de fila AR: `DISTRIBUIDORA NORTE, FAC-2026-0341, 2026-04-01, 2026-04-30, 4 820 000`

## 5. Tramos determinísticos

1. **Ingesta y validación**: lectura de los CSV/API de AR y AP; verificación de integridad (fechas válidas, montos positivos, sin duplicados de factura).
2. **Cálculo de DSO por cliente**: `DSO_cliente = media(dias_para_pago últimos 6 meses)`. Para clientes nuevos sin historial: DSO promedio del sector (configurable por tenant).
3. **Proyección de cobros**: para cada factura abierta, `fecha_cobro_estimada = fecha_vencimiento + DSO_cliente`. Agrupación por semana.
4. **Proyección de pagos**: AP ordenado por `fecha_vencimiento`; nómina por calendario fijo; flujos fijos por tabla de configuración.
5. **Construcción del rolling 13W**: tabla semanal con columnas `semana, inflows_esperados, outflows_comprometidos, saldo_proyectado, saldo_acumulado`. Actualización cada lunes con semana+1 rolling.
6. **Detección de semanas críticas (regla dura)**: `saldo_acumulado < umbral_minimo` (configurable; default: reserva de 2 semanas de nómina). Las semanas críticas se marcan automáticamente en rojo.

## 6. Tramos agénticos

1. **Ajuste de DSO por señales cualitativas**: el agente lee las notas de la semana anterior (e.g., «Distribuidora Norte comunicó dificultades de liquidez») y ajusta su DSO estimado hacia arriba. Un humano puede escribir esas notas en lenguaje natural en la interfaz; el agente las interpreta y las convierte en parámetros numéricos. **No es regla** porque la relación entre una nota de texto libre y un cambio de DSO no tiene una fórmula cerrada; depende del contexto y la gravedad.
2. **Estimación de timing de cobros irregulares**: clientes que no siguen un patrón estable —pagan en 20 días un mes y en 45 el siguiente— requieren que el agente razone sobre el contexto más reciente (último contacto, historial de litigios, estacionalidad del sector del cliente). No hay regla que cubra todos los casos.
3. **Redacción del ejecutivo summary**: el agente produce el correo semanal al CFO. Describe las 2–3 semanas más críticas, la causa probable (e.g., «Factura de 48 M COP de GLOBEX con 22 días de vencida y sin confirmación de pago»), y sugiere acciones concretas (llamar al cliente, negociar extensión con proveedor). La narrativa adapta el tono y el nivel de detalle al perfil configurado del receptor. **No es regla** porque la síntesis y priorización de múltiples factores simultáneos excede lo que una plantilla puede hacer.
4. **Escenarios what-if bajo petición**: el CFO puede preguntar «¿qué pasa con el saldo si ACME tarda 15 días más de lo esperado en pagar?». El agente recalcula el 13W con ese supuesto y muestra el delta. La interpretación del lenguaje natural de la pregunta y la traducción al modelo cuantitativo es agéntica.
5. **Fallback humano**: si la proyección muestra un saldo negativo en las próximas 3 semanas, el agente genera una alerta de prioridad alta y espera confirmación del CFO antes de enviar el reporte al comité. El modelo no decide por el CFO qué hacer; solo informa y escala.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_ar] → erp_fetch_transactions(erp=siigo, period, account="AR", tenant)
  ↓
[ingest_ap] → erp_fetch_transactions(erp=siigo, period, account="AP", tenant)
  ↓
[load_fixed] → sql_query(historial_nomina + flujos_fijos, tenant)
  ↓
[compute_dso] → cálculo determinístico de DSO por cliente (Python puro)
  ↓
[adjust_dso]  → LLM revisa notas de gestión + señales cualitativas (agéntico)
                 tool: sql_query(notas_cliente, tenant)
  ↓
[build_13w]   → proyección determinística semana a semana
  ↓
[flag_critical] → router determinístico: ¿saldo < umbral?
  ├─ NO → [draft_summary]
  └─ SÍ → [alert_human] interrupt_before + post_slack_message
              ↓ (CFO confirma continuar)
[draft_summary] → LLM redacta ejecutivo (agéntico)
  ↓
[write_report] → write_report(kind=xlsx, tenant) + send_email(to=[CFO], tenant)
  ↓
END
```

### Activities Temporal (Schedule lunes 06:00 por tenant)

- `ingest_ar(tenant, period)` — retry 3x; idempotente por `(tenant, week_iso)`.
- `ingest_ap(tenant, period)` — idem.
- `run_forecast_agent(tenant, dataset_id)` — ejecuta el grafo; timeout 8 min.
- `persist_forecast(tenant, week_iso, payload)` — `idempotency_key = "forecast13w:{tenant}:{week_iso}"`.

### Tools necesarias

| Tool | Uso |
|------|-----|
| `erp_fetch_transactions` | AR y AP desde Siigo/Alegra |
| `sql_query` | Historial de pagos, notas de gestión, flujos fijos |
| `write_report` | Reporte XLSX con el 13W |
| `send_email` | Ejecutivo semanal al CFO |
| `post_slack_message` | Alerta inmediata si saldo < umbral |

## 8. Salida y entrega

**Reporte XLSX** con dos pestañas:

1. `13W Rolling`: tabla semana por semana con `inflows`, `outflows`, `saldo_semana`, `saldo_acumulado`. Celdas rojas en semanas críticas. Columna `confidence` (alta/media/baja) basada en el DSO estimado.
2. `Detalle AR`: lista de facturas con cliente, monto, vencimiento, `fecha_cobro_estimada`, DSO aplicado.

**Email automático** cada lunes a las 07:00 (después del Schedule de Temporal). Asunto: `[ACME] Forecast 13W — semana del 2026-05-18 — 2 semanas en alerta`. Cuerpo: 3 párrafos con resumen ejecutivo + tabla de semanas críticas + acciones sugeridas.

**Alerta Slack** inmediata si alguna semana tiene saldo proyectado negativo.

## 9. Cómo se vende

**Gancho**: «El CFO dedica 3 horas cada lunes a actualizar un Excel. Nosotros lo actualizamos solo, con un correo que le llega antes del desayuno.»

**Propuesta de valor**: visibilidad de tesorería 13 semanas adelante, sin trabajo manual; alertas tempranas antes de que el problema sea urgente; narrativa lista para el comité directivo.

| Tier | Qué incluye | Precio USD/mes |
|------|-------------|----------------|
| Starter | 1 ERP (Siigo/Alegra), hasta 500 facturas AR | 200–400 |
| Estándar | 2 ERPs, 2 000 facturas AR, Slack alert | 400–800 |
| Premium | multi-ERP, escenarios what-if, SLA respuesta | 800–1 800 |

Setup: 1 500–4 000 USD (mapeo de cuentas, calibración de DSO, golden set de 4 semanas de referencia).

## 10. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **DSO estimado incorrecto**: cliente que históricamente paga en 30 días cambia su comportamiento | Alta | Alto | Recalibrar DSO mensualmente con el historial real. Mostrar el intervalo de confianza del forecast, no solo el valor puntual. |
| **Datos AR desactualizados**: el export de Siigo se olvidó de correr | Media | Alto | El agente verifica que el timestamp del CSV sea de las últimas 48 h antes de procesar. Si no, alerta al usuario antes de correr. |
| **Alucinación en la narrativa**: el agente describe una semana de riesgo que en realidad no lo es | Baja | Medio | La narrativa siempre cita las facturas concretas que generan la alerta (con número y cliente). El CFO puede verificar. |
| **Costo LLM en escenarios what-if interactivos**: múltiples preguntas del CFO en una sesión | Baja | Bajo | Cachear el 13W calculado en la sesión (determinístico, no recalcula); solo la interpretación de la pregunta usa el LLM. |
| **Privacidad**: montos y nombre de clientes en el prompt | Alta | Medio | Los nombres de clientes individuales se envían al LLM; no hay números de documento ni datos personales de personas naturales. Registrar en política de datos. |

## 11. Variantes por industria

### Instancia 1 — Manufactura (`acme`)

**Datos típicos**: AR de 50–200 clientes (distribuidores), facturas de 50 000–500 000 COP promedio, ciclos de pago 30–60 días. AP dominado por materias primas con proveedores fijos (10–30). Nómina quincena + prima semestral.

**Delta determinístico**: inclusión de los ciclos de producción (ingesta de órdenes de producción activas) como proxy de futuros pagos a proveedores de insumos. Si hay una orden de producción programada para la semana 4, se proyecta el AP asociado.

**Delta agéntico**: el agente detecta si hay una factura grande de un distribuidor clave vencida hace más de 15 días y la resalta como riesgo crítico, porque el historial de ese cliente muestra que después de 15 días la recuperación tarda 30 días más.

**Regulación**: sin particularidades adicionales a la tributaria local.

**Precio orientativo**: 300–700 USD/mes; ACME tiene ~150 facturas AR activas en un mes normal.

---

### Instancia 2 — Servicios profesionales (`consultorabc`)

**Datos típicos**: AR de 10–30 clientes (proyectos), facturas grandes por hitos (500 USD–20 000 USD), ciclos de pago muy irregulares (dependen de aprobación interna del cliente). AP mínimo (freelancers, software). Nómina mensual pequeña (3–8 personas).

**Delta determinístico**: el forecast se basa en el calendario de hitos de proyecto, no en fechas de vencimiento de factura. Hay que leer una hoja «hitos» del Excel del proyecto para proyectar cuándo se emite la factura y cuándo se cobra.

**Delta agéntico**: la principal fuente de incertidumbre es el tiempo de aprobación interna del cliente (puede tardar 2 semanas o 2 meses). El agente calibra ese factor por cliente basándose en el historial de aprobaciones pasadas y las notas del gestor del proyecto.

**Regulación**: en servicios profesionales, el IVA sobre honorarios puede ser retenido por el cliente (retención en la fuente en Colombia). El agente descuenta la retención del cobro esperado para evitar sobreestimar el inflow.

**Precio orientativo**: 200–500 USD/mes; volumen bajo de facturas pero alta variabilidad en el timing.

## 12. Módulos técnicos relacionados

| Módulo | Por qué aplica |
|--------|---------------|
| **E05** — Temporal | El Schedule `lunes 06:00 por tenant` es el caso de uso textual de E05. El ejercicio `design` de E05 pide diseñar exactamente este workflow. |
| **A06** — Dataclasses y tipos | El modelo de datos `CashFlowRow(week_iso, inflows, outflows, balance, confidence)` es el ejercicio de A06. |
| **C01** — SQLAlchemy async | El historial de pagos de clientes y las proyecciones se persisten en DB. C01 enseña el modelo ORM que los almacena. |
| **E01** — Anthropic SDK | El nodo `adjust_dso` es un loop tool_use simple: el modelo lee notas y emite un JSON con los ajustes. Ejemplo directo de E01. |
| **D04** — Observabilidad | El span de `run_forecast_agent` en Phoenix muestra qué parte del tiempo va a LLM y qué parte a cálculo determinístico. Útil para optimizar costos. |
| **B02** — FastAPI + Pydantic | El endpoint `/forecast/what-if` que recibe la pregunta del CFO en lenguaje natural y devuelve el 13W recalculado. Ejemplo de B02. |

## 13. Errores típicos

**1. DSO calculado con todas las facturas cobradas, incluyendo las pagadas en el mismo día de emisión.**
*Síntoma*: el DSO de ACME resulta en 2 días para un cliente que normalmente tarda 35 días; hay facturas de anticipo que el cliente paga al recibir y que distorsionan el promedio.
*Causa*: el cálculo incluye pagos anticipados sin filtrar por tipo de factura.
*Cómo evitarlo*: excluir del cálculo de DSO las facturas con `dias_reales_pago < 3` (anticipos) y las facturas de tipo «anticipo» o «enganche» marcadas en el ERP. Documentar qué criterio de exclusión se usó.

**2. CSV de AR con timestamp del archivo de la semana anterior porque el proceso de exportación falló silenciosamente.**
*Síntoma*: el forecast del lunes muestra datos de la semana pasada; el CFO toma decisiones con información desactualizada sin saberlo.
*Causa*: el agente no verifica el timestamp del archivo antes de procesarlo; el Export de Siigo falló y el archivo viejo quedó en el bucket sin sobrescribirse.
*Cómo evitarlo*: el nodo `ingest_ar` verifica que `file_timestamp >= monday_00:00_local`. Si no, detener la corrida y alertar por Slack antes de procesar. No continuar con datos viejos.

**3. Escenario what-if recalcula el 13W completo invocando el LLM para los cálculos determinísticos.**
*Síntoma*: cada pregunta del CFO en una sesión de what-if cuesta $0.40 USD en LLM cuando debería costar $0.02 USD (solo la interpretación de la pregunta).
*Causa*: el endpoint `/forecast/what-if` recorre el grafo completo en lugar de usar el 13W ya calculado como punto de partida y solo recomputar la proyección determinística con el nuevo supuesto.
*Cómo evitarlo*: persistir el 13W calculado con su `dataset_id` al inicio del Schedule. Las preguntas what-if usan el LLM solo para interpretar la pregunta y extraer el parámetro a modificar; el recálculo de la proyección es código Python puro sobre el dataset cacheado.

**4. Notas del CFO en español informal truncadas por el LLM al ajustar el DSO.**
*Síntoma*: el CFO escribe «creo que norte no va a pagar este mes, está complicado» refiriéndose a Distribuidora Norte; el agente ajusta el DSO de un proveedor llamado «Norte Construcciones» porque el nombre coincide parcialmente.
*Causa*: el nodo `adjust_dso` no tiene acceso al catálogo de clientes para resolver el nombre ambiguo antes de aplicar el ajuste.
*Cómo evitarlo*: el prompt del nodo `adjust_dso` incluye la lista de clientes activos del tenant. Si el nombre en la nota no resuelve de forma unívoca, el agente pide confirmación al CFO antes de aplicar el ajuste.

## 14. Pregúntale al tutor

1. «Explícame cómo calcularía el DSO para ConsultorABC donde los cobros dependen de hitos de proyecto y no de fechas de vencimiento de factura. El historial de hitos está en un Excel de gestión de proyectos, no en el ERP.»
2. «Audita mi prompt del nodo `draft_summary` para ACME y dime qué información de contexto le falta para que el ejecutivo semanal mencione específicamente qué acción concreta debe tomar el CFO con las 2 semanas críticas.»
3. «Genera el código mínimo del nodo `flag_critical` en LangGraph que detecta semanas con `saldo_acumulado < umbral` y dispara el `interrupt_before` con un mensaje que indica exactamente qué facturas explican el déficit.»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Implementar el cálculo de DSO por cliente excluyendo anticipos y calculando el intervalo de confianza del forecast.
- Diseñar la validación de frescura del CSV de AR antes de iniciar la corrida semanal.
- Separar el recálculo determinístico del what-if del costo LLM de interpretar la pregunta, reduciendo el costo por interacción del CFO.
- Configurar el ajuste de DSO por notas de texto libre con resolución unívoca de nombre de cliente antes de aplicar el cambio.
- Dimensionar el Schedule de Temporal para ejecución semanal con idempotencia y retry ante fallos de exportación del ERP.

## 16. Módulos previos recomendados

| Módulo previo | Por qué te prepara |
|---------------|-------------------|
| **E05** — Temporal | El Schedule `lunes 06:00` con idempotencia `"forecast13w:{tenant}:{week_iso}"` es el caso de uso textual de E05; el ejercicio de diseño de ese módulo pide implementar exactamente este workflow. |
| **A06** — Dataclasses | El modelo `CashFlowRow(week_iso, inflows, outflows, balance, confidence)` es el ejercicio natural de A06 para este dominio. |
| **C01** — SQLAlchemy async | El historial de pagos de clientes y las proyecciones persisten en DB; C01 enseña el modelo ORM que los almacena y la query de historial por cliente. |
| **E01** — Anthropic SDK | El nodo `adjust_dso` es un loop `tool_use` simple; E01 enseña el patrón de salida JSON estructurada antes de implementarlo. |
| **B02** — FastAPI + Pydantic | El endpoint `/forecast/what-if` con validación del body de la pregunta del CFO es el ejercicio de B02 para este dominio. |
