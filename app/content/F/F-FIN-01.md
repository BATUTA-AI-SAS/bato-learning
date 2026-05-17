---
ext_id: F-FIN-01
slug: conciliacion-bancaria
track: F
dept: FIN
ord: 100
title: "Conciliación bancaria multi-cuenta"
summary: "Agente que empareja extractos bancarios con el libro contable, clasifica diferencias y produce un reporte listo para el contador."
related_modules: [A05, B03, C03, D04, E01, E05]
industries_instanced: [retail, servicios-fin]
tenants_in_examples: [tiendabox, cooppopular]
big_corp_vendors: [BlackLine, Trintech, FloQast]
latam_tools: [siigo, world_office, belvo]
key_concepts: [matching, tolerancias, fuzzy-match, reglas-duras, agente-de-excepciones, fallback-humano]
estimated_minutes: 60
deterministic_share: 0.7
version: 1
---

## 1. Problema operativo

La contadora de TiendaBox dedica dos días cada fin de mes a cruzar el estado de cuenta del banco con el libro mayor de Siigo. El banco tiene 3 000 movimientos en temporada alta; Siigo tiene 2 800 asientos. El 90 % cuadra solo, pero el 10 % restante —transacciones con descripciones tipo «TRANSF VARGAS 04/15», notas de crédito sin referencia, o pagos de plataforma MP que agrupan 40 ventas en un solo abono— le cuesta un día entero de trabajo manual, búsqueda en correos y llamadas al banco. Los errores que pasan sin detectar se arrastran al siguiente mes y complican el cierre.

El CFO de TiendaBox quiere que ese proceso tarde menos de una hora y que el sistema le muestre exactamente qué diferencias existen, por qué, y cuáles necesitan su ojo.

## 2. Hoy en big corps

| Vendor | Producto | Stack / capacidad | Inversión orientativa |
|--------|----------|-------------------|-----------------------|
| **BlackLine** | Transaction Matching + Verity AI | Match por reglas + ML para descripción; conectores certificados SAP, Oracle, Workday | 80–250 USD/usuario/mes; setup 20–80 k USD |
| **Trintech Cadency** | Reconciliation Hub | Predicción de excepciones antes de que ocurran; conector SAP/Oracle nativo | 100–300 USD/usuario/mes; impl. 40–150 k USD |
| **FloQast AutoRec** | AutoRec | Matching automático + checklist de cierre integrado; más accesible que BlackLine | 60–150 USD/usuario/mes; setup 15–40 k USD |

Estas plataformas requieren un equipo de implementación (2–6 semanas), conectores con el ERP corporativo, y un mínimo de usuarios que hace el ROI negativo para una PYME.

## 3. PYME LATAM realista

La PYME típica trabaja con:

- **Extracto bancario**: PDF descargado del portal del banco (Bancolombia, BBVA MX, Davivienda) o CSV si el banco lo permite. Formato propietario por banco; no hay estandarización.
- **Libro contable**: export CSV/Excel de Siigo (Colombia) o World Office (Colombia), o reporte de movimientos de Contpaq (México). No hay API REST en tiempo real para los ERPs locales de gama baja; sí hay exportación a CSV/XLSX programable.
- **Integración bancaria**: Belvo (open banking, cubre 60+ instituciones en MX/CO/BR) permite traer transacciones vía API sin descargar PDF. Alternativa con Plaid si el banco está en su catálogo.
- **Equipo**: 1 contador general, sin data engineer. El agente es el «data engineer».

## 4. Datos típicos

| Atributo | Extracto bancario | Libro contable (Siigo CSV) |
|----------|-------------------|---------------------------|
| Formato | PDF (layout variable) o CSV propietario | CSV con columnas fijas: `fecha,comprobante,descripcion,debito,credito,saldo` |
| Frecuencia | Mensual (descarga manual) o diario vía Belvo API | Exportación ad-hoc o por periodo |
| Volumen | 500–5 000 filas/mes (PYME mediana) | 400–4 500 asientos/mes |
| Ejemplo de fila | `15/04/2026, TRANSF VARGAS, -4820.00, 18 230 401.50` | `2026-04-15, GR-00412, Pago proveedor Vargas Suministros, 4820.00, , 210 400.00` |
| Moneda | COP o MXN (raramente multi-moneda en PYME) | Misma moneda, misma cuenta |
| Volumen de excepciones | ~5–15 % del total | — |

## 5. Tramos determinísticos

1. **Parseo del extracto bancario**: PDF → tabla estructurada con `pdfplumber` o `camelot`; CSV → `pandas`. Normalización de fecha (dd/mm/yyyy → ISO), monto (separadores de miles), cuenta.
2. **Parseo del libro contable**: lectura del CSV de Siigo/World Office con schema fijo. Validación de integridad: que los saldos cuadren, que no haya filas con monto cero.
3. **Match exacto por monto + fecha + referencia**: si `|extracto.monto - libro.monto| < tolerancia` AND `extracto.fecha == libro.fecha` AND `extracto.referencia == libro.comprobante` → match automático. Tolerancia configurable por tenant (típico: 0.01 USD o 1 COP).
4. **Agregación de pagos de plataforma**: agrupar transacciones del libro por gateway (Mercado Pago, Wompi, Conekta) para comparar contra el abono consolidado del extracto.
5. **Clasificación por estado**: `MATCHED` / `UNMATCHED_BANK` / `UNMATCHED_BOOK` / `PENDING_FUZZY`. Generación de tabla de diferencias con monto total por estado.
6. **Generación de reporte estructurado**: plantilla Markdown/XLSX con resumen, tabla de matches, tabla de diferencias, saldo conciliado vs saldo contable.

## 6. Tramos agénticos

1. **Match difuso por descripción** (`PENDING_FUZZY`): transacciones donde el monto coincide pero la descripción del banco no tiene correspondencia directa en el libro (e.g., «TRANSF MARIA 04/15» vs «Nómina parcial María López, comisión abril»). El agente razona sobre el contexto —historial de esa descripción en meses anteriores, proveedor probable, importe— y propone el asiento correspondiente con nivel de confianza. **No es regla** porque la variabilidad de las descripciones bancarias en LATAM es ilimitada: el mismo proveedor puede aparecer como «VARGAS S», «VARG SUMI», «TRANS 0491 VARG», dependiendo del banco y del momento.
2. **Clasificar diferencias residuales**: después del fuzzy match quedan diferencias. El agente las categoriza en `timing` (pago cruzó de mes), `error_libro` (falta un asiento en Siigo), `error_banco` (cargo duplicado del banco), `desconocido`. La categorización requiere leer el contexto del cliente —¿hubo un pago el último día del mes anterior?— y no tiene regla cerrada para todos los casos.
3. **Redacción del hallazgo**: si la diferencia supera el umbral de materialidad (configurable por tenant), el agente redacta un párrafo explicativo para el correo al CFO. La narrativa adapta el tono y el nivel de detalle al perfil del receptor —sin regla cerrada.
4. **Fallback humano**: cualquier diferencia cuyo importe supera el 5 % del saldo conciliado, o cuya categoría es `desconocido`, genera una tarea en la cola de revisión humana. El agente pone `interrupt_before` en el nodo `write_report` y espera sign-off. El modelo **no borra ni ajusta** asientos; solo propone.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_bank] → parse_bank_statement(path, account, tenant)
  ↓               → tabla normalizada de transacciones bancarias
[ingest_book] → fetch_csv(path, tenant) + fetch_excel(path, sheet, tenant)
  ↓               → tabla de asientos del ERP
[match_strict] → match exacto monto+fecha+ref (código Python puro)
  ↓               → sets: MATCHED, UNMATCHED_BANK, UNMATCHED_BOOK
[match_fuzzy]  → LLM loop sobre UNMATCHED con tool sql_query (historial)
  ↓               → propuestas de match + confidence score
[classify_diffs] → LLM clasifica residuos: timing/error/desconocido
  ↓
[check_threshold] → router determinístico: ¿diferencia > 5% saldo?
  ├─ NO → [draft_report]
  └─ SÍ → [human_review] interrupt_before + notificación al contador
              ↓ (sign-off recibido)
[draft_report] → LLM redacta narrativa + tabla de findings
  ↓
[write_report] → write_report(kind=xlsx, tenant) + send_email(to=[CFO], tenant)
  ↓
END
```

### Activities Temporal (ejecución mensual programada)

- `ingest_bank_statement(tenant, period, account)` — IO real, retry 3x con backoff.
- `ingest_erp_ledger(tenant, period, erp)` — descarga CSV del ERP; idempotente por `(tenant, period)`.
- `run_recon_agent(tenant, dataset_id)` — ejecuta el grafo LangGraph; timeout 10 min.
- `persist_report(tenant, period, payload)` — escritura con `idempotency_key = "recon:{tenant}:{period}"`.

### Tools necesarias

| Tool | Uso |
|------|-----|
| `parse_bank_statement` | Parsea el PDF/CSV del extracto |
| `fetch_csv` | Lee el libro contable de Siigo/WO |
| `fetch_excel` | Alternativa si el libro viene en XLSX |
| `sql_query` | Consulta historial de descripciones pasadas |
| `bank_open_api` | Opcional: trae transacciones en tiempo real vía Belvo |
| `write_report` | Persiste el reporte XLSX |
| `send_email` | Envía el reporte al CFO |

## 8. Salida y entrega

**Reporte XLSX** con tres pestañas:

1. `Resumen`: saldo banco, saldo libro, diferencia neta, total matched, total unmatched, estado (`CONCILIADO` / `PENDIENTE_REVISIÓN`).
2. `Matches`: tabla de pares (transacción banco ↔ asiento libro) con método de match (`exact` / `fuzzy`) y confianza.
3. `Diferencias`: filas sin match con categoría (`timing`, `error_libro`, `error_banco`, `desconocido`), monto, y nota del agente.

**Email automático** al CFO y al contador cada fin de mes (trigger: Temporal Schedule). Asunto: `[TiendaBox] Conciliación abril 2026 — 12 diferencias pendientes`. Cuerpo: resumen de 3 párrafos + link al XLSX.

**Alerta inmediata** vía Slack si el agente detecta una diferencia de categoría `error_banco` mayor a 50 000 COP (configurable): `post_slack_message(channel="#finanzas", ...)`.

## 9. Cómo se vende

**Gancho**: «Tu contadora dedica dos días a cruzar el banco. Nosotros lo hacemos en 20 minutos, con un reporte que le muestra exactamente qué revisar.»

**Propuesta de valor**: reducción de 85–90 % del tiempo de conciliación manual; cero diferencias que pasan sin detectar; auditoría completa de cada decisión del agente.

| Tier | Qué incluye | Precio USD/mes |
|------|-------------|----------------|
| Básico | 1 cuenta, hasta 2 000 tx/mes, reporte XLSX | 150–300 |
| Estándar | hasta 5 cuentas, 10 000 tx/mes, Slack + email | 300–700 |
| Premium | cuentas ilimitadas, Belvo en tiempo real, SLA | 700–1 500 |

Setup inicial (mapeo de cuentas, golden set de 50 transacciones): 1 000–3 000 USD una vez.

## 10. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **Alucinación en fuzzy match**: el agente propone un match incorrecto entre transacción y asiento | Media | Alto (error contable) | Confianza mínima 0.85 para match automático; por debajo, va a revisión humana. El reporte muestra la confianza en cada fila. |
| **Costo de LLM en volúmenes altos**: 5 000 transacciones en fuzzy match con contexto largo | Media | Medio | Truncar contexto a 200 transacciones por batch; usar `claude-sonnet-4-6` (barato); prompt caching del system. Costo estimado: < 2 USD/corrida para 5 000 tx. |
| **PII en descripciones**: nombres de personas en descripciones bancarias (nómina, transferencias entre socios) | Alta | Alto | Anonimización de nombres antes de enviar al LLM (regex sobre patrones NOMBRE APELLIDO). Log de las descripciones sin PII. |
| **Regulación fiscal**: en Colombia, la conciliación bancaria es parte del soporte del libro fiscal. El reporte del agente debe ser trazable | Media | Alto | Cada decisión del agente se guarda con `trace_id` de Phoenix. El reporte XLSX es el artefacto auditable. El agente no modifica asientos en Siigo. |
| **Parseo de PDFs bancarios cambia**: el banco actualiza el layout del extracto | Alta | Medio | Detectar automáticamente cambio de layout (número de columnas inesperado) y alertar al equipo técnico antes de procesar. |

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 3–8 cuentas bancarias (COP + USD si vende cross-border), 2 000–10 000 transacciones/mes en temporada alta (noviembre–enero). Descriptores cortos y ruidosos: «PAGO MERCH MP 4820», «WOMPI-TRX-8820142».

**Delta determinístico**: paso adicional de agregación por gateway de pago antes del match. Mercado Pago y Wompi envían un único abono diario que agrupa N ventas; hay que desagregar usando el reporte de liquidación de la plataforma (CSV descargable).

**Delta agéntico**: identificar contracargos disfrazados de reembolso ordinario. El agente compara el descriptor con el historial de contracargos del cliente y marca los sospechosos.

**Regulación**: IVA sobre ventas online; mantener evidencia de cada transacción 5 años (DIAN Colombia). El reporte incluye columna `tipo_operacion` para clasificación tributaria.

**Precio orientativo**: 300–700 USD/mes según volumen de transacciones.

---

### Instancia 2 — Servicios financieros (`cooppopular`)

**Datos típicos**: 1–3 cuentas, volumen alto en transferencias entre asociados (500–2 000/mes), descripción más rica: «TRANSF SOCIO 0214 APORTE MARZO», «RETIRO PARCIAL AHORRO 0099».

**Delta determinístico**: clasificación previa por código de transacción del core bancario de la cooperativa (tabla SBA/COSAC provista por el sistema central). El 80 % se clasifica por código antes de llegar al agente.

**Delta agéntico**: detectar patrones de layering —varios depósitos pequeños del mismo asociado en días distintos que suman un monto redondo— y marcarlos para revisión de cumplimiento. El modelo razona sobre el patrón histórico, no sobre una regla fija.

**Regulación**: AML/KYC (SARLAFT en Colombia). El agente **nunca** borra ni reclasifica transacciones marcadas; solo genera una alerta en la cola de cumplimiento. `human_in_the_loop` es no-negociable antes de cualquier acción sobre esas transacciones.

**Precio orientativo**: 600–1 500 USD/mes; setup 5 000–15 000 USD (incluye revisión de política AML con el compliance officer del cliente).

## 12. Módulos técnicos relacionados

| Módulo | Por qué aplica |
|--------|---------------|
| **E01** — Anthropic SDK básico | El loop `tool_use → tool_result` es el core del nodo `match_fuzzy`. El ejemplo de E01 usa conciliación como caso conducido. |
| **E02** — LangGraph | El grafo de nodos de esta ficha es el ejercicio `design` de E02. La bifurcación `check_threshold → human_review` enseña el `interrupt_before`. |
| **E05** — Temporal | El `Schedule` mensual por tenant es el caso de uso concreto de E05. Las activities `ingest_*` y `persist_report` aterrizan aquí. |
| **D04** — Observabilidad | Cada span del grafo (ingest, match_strict, match_fuzzy) se traza en Phoenix. El módulo D04 enseña cómo leer esa traza para diagnosticar latencia. |
| **C03** — Multitenancy | Cada query de `sql_query` lleva `tenant` explícito. C03 enseña el patrón de filtro que impide que los datos de TiendaBox se mezclen con los de CoopPopular. |
| **A05** — Módulos y paquetes | La estructura del agente de conciliación (`ingest/`, `match/`, `report/`) es un ejemplo directo de cómo organizar un paquete Python. |

## 13. Errores típicos

**1. Parseo del PDF bancario sin detección de cambio de layout.**
*Síntoma*: Bancolombia actualiza el diseño de su extracto en marzo; el agente de TiendaBox extrae montos erróneos o vacíos sin avisar; el reporte muestra 3 000 filas `UNMATCHED_BANK` cuando en realidad casi todo coincide.
*Causa*: el parser asume columnas fijas por posición y no verifica que el número de columnas detectadas sea el esperado.
*Cómo evitarlo*: al parsear, validar que el número de columnas y los encabezados detectados coincidan con el schema esperado. Si difieren, detener el proceso y notificar al equipo técnico con el extracto adjunto antes de producir ningún resultado.

**2. Agregación de pagos de plataforma omitida antes del match estricto.**
*Síntoma*: el extracto de TiendaBox muestra un único abono de Wompi por $4 820 000 COP que representa 40 ventas; el libro tiene 40 asientos individuales. El match estricto no encuentra par para el abono; aparece como `UNMATCHED_BANK`.
*Causa*: el nodo `match_strict` corre antes del nodo de agregación por gateway; el abono consolidado no tiene contraparte individual en el libro.
*Cómo evitarlo*: el nodo de agregación por gateway debe ejecutarse siempre antes del match estricto, no después. Verificar con un test de integración que el orden de nodos es correcto.

**3. PII anonimizada en el log pero enviada al LLM sin filtro.**
*Síntoma*: el log de Phoenix muestra los prompts completos con nombres de empleados de la nómina de la Cooperativa Popular; viola la política de datos del cliente.
*Causa*: el regex de anonimización solo se aplica al archivo de log, no al texto que se envía como mensaje al LLM.
*Cómo evitarlo*: la anonimización debe aplicarse en el nodo `match_fuzzy` antes de construir el payload del LLM, no después de recibir la respuesta.

**4. Sign-off del contador bloqueado infinitamente por falta de timeout.**
*Síntoma*: el workflow lleva 72 horas esperando el `interrupt_before` del contador, que está de vacaciones; el proceso de cierre mensual queda bloqueado.
*Causa*: el nodo `human_review` no tiene deadline configurado.
*Cómo evitarlo*: definir un `timeout_human_review` (default: 48 h) en la configuración del tenant. Si expira, escalar automáticamente al supervisor del contador con un recordatorio y prolongar el timeout otras 24 h.

## 14. Pregúntale al tutor

1. «Explícame cómo adaptaría el nodo `match_fuzzy` para la Cooperativa Popular, donde las descripciones de transacciones incluyen números de asociado y el historial tiene 24 meses de datos. ¿Cómo gestiono el tamaño del contexto sin perder precisión?»
2. «Audita mi implementación del parseo de extracto bancario de Davivienda y dime qué validaciones de schema le faltan para detectar un cambio de layout sin romper el pipeline.»
3. «Genera el código mínimo en LangGraph del nodo `classify_diffs` que recibe la lista de transacciones `UNMATCHED` y devuelve una clasificación `{timing, error_libro, error_banco, desconocido}` para cada una usando un único batch al LLM.»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de conciliación en tres capas: match exacto → agregación por gateway → match difuso, en el orden correcto.
- Implementar la anonimización de PII en el nodo de preparación del prompt, antes de enviar al LLM.
- Configurar el `interrupt_before` con timeout y escalamiento automático para evitar bloqueos indefinidos.
- Identificar qué diferencias residuales pueden cerrarse automáticamente y cuáles requieren sign-off del contador.
- Estimar el costo por corrida según el porcentaje de transacciones que llegan al nodo `match_fuzzy`.

## 16. Módulos previos recomendados

| Módulo previo | Por qué te prepara |
|---------------|-------------------|
| **E01** — Anthropic SDK | El nodo `match_fuzzy` es el primer ejemplo de loop `tool_use` con historial; E01 enseña exactamente ese patrón antes de implementarlo. |
| **E02** — LangGraph | La bifurcación `check_threshold → human_review` con `interrupt_before` es el ejercicio de diseño de E02 usando esta ficha como caso. |
| **E05** — Temporal | El Schedule mensual por tenant con idempotencia `"recon:{tenant}:{period}"` es el caso de uso textual de E05. |
| **C03** — Multitenancy | Cada `sql_query` de historial lleva `tenant_id`; el patrón de filtro de C03 evita que los datos de TiendaBox se mezclen con los de CoopPopular. |
| **D04** — Observabilidad | Leer en Phoenix el span `match_fuzzy` para ver la latencia y el costo LLM por transacción es la práctica central de D04 con este grafo. |
