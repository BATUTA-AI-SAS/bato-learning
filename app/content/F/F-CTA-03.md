---
ext_id: F-CTA-03
slug: declaraciones-fiscales
track: F
dept: CTA
ord: 122
title: "Preparación de declaraciones fiscales mensuales"
summary: "Agente que agrega los datos contables del período, verifica consistencia contra los libros, redacta las notas explicativas, y prepara el borrador listo para firma del contador antes del plazo regulatorio."
related_modules: [B02, C01, E01, E05]
industries_instanced: [retail, construccion]
tenants_in_examples: [tiendabox, andina]
big_corp_vendors: [Vertex, Avalara, Sovos]
latam_tools: [siigo, dian-muisca, sat-mexico, contpaq]
key_concepts: [IVA, retencion-fuente, ICA, conciliacion-fiscal-contable, human-in-the-loop-obligatorio, plazo-regulatorio]
estimated_minutes: 45
deterministic_share: 0.8
version: 1
---

## 1. Problema operativo

El contador de TiendaBox prepara cada mes cuatro declaraciones: IVA (bimestral), retenciones en la fuente (mensual), ICA (industria y comercio, bimestral en Bogotá), y renta (anual). La preparación del IVA mensual le toma 1.5–2 días: descargar los libros de compras y ventas del ERP, cruzarlos con los XML de facturación electrónica de la DIAN, calcular los saldos, llenar el formulario 300 en MUISCA, y revisar que los números coincidan.

El riesgo operativo: si hay una inconsistencia entre el libro y la facturación electrónica y no se detecta antes de la firma, la DIAN puede iniciar un proceso de fiscalización. El plazo de presentación en Colombia es el último día hábil del mes siguiente al período; si el contador está de vacaciones ese día, nadie tiene la información preparada.

Constructora Andina tiene el mismo problema multiplicado: los proyectos en varias ciudades tienen diferentes tasas de ICA, y el cálculo de retenciones en contratos de obra es un nido de reglas específicas (el porcentaje de retención depende del tipo de ingreso: materiales vs mano de obra).

## 2. Hoy en big corps

| Vendor | Producto | Capacidad clave | Inversión orientativa |
|--------|----------|-----------------|-----------------------|
| **Vertex** | Indirect Tax O Series | Cálculo de impuestos en tiempo real integrado con ERP; cubre 19 000+ jurisdicciones globales | 50 000–500 000 USD/año; impl. 100 k+ USD |
| **Avalara** | AvaTax + Returns | Cumplimiento de IVA/VAT en 100+ países; e-invoicing para México y Colombia; auto-presentación de declaraciones | 5 000–50 000 USD/año según volumen |
| **Sovos** | Tax Compliance Suite | Especializado en países con facturación electrónica obligatoria y controles transaccionales continuos (CTC); fuerte en LATAM | 10 000–100 000 USD/año |

Sovos es el más fuerte en LATAM por su conocimiento de los CTCs de DIAN (Colombia), SAT (México), y AFIP (Argentina). Avalara tiene presencia pero es más fuerte en Norteamérica. Para una PYME LATAM, el costo mínimo de implementación de cualquiera de estos supera el valor de 12 meses de un agente.

## 3. PYME LATAM realista

- **Colombia**: el contador trabaja directamente en el portal MUISCA de la DIAN para presentar el formulario 300 (IVA) y el 350 (retenciones). La información viene del ERP (Siigo tiene un reporte de «libro de ventas» y «libro de compras» que cuadra con la declaración).
- **México**: el contador usa el portal del SAT para la declaración de IVA mensual (formato DIOT para operaciones con terceros) y el CFDI para facturas. Contpaq tiene exportación directa al formato DIOT.
- **Flujo habitual**: ERP → reporte exportado (CSV/Excel) → revisión manual → MUISCA/SAT → firma.
- **La DIAN y el SAT ya tienen los datos del contribuyente** vía facturación electrónica. El riesgo es la inconsistencia entre lo que el contribuyente declara y lo que el fisco ya sabe.

## 4. Datos típicos

| Fuente | Contenido | Formato | Frecuencia |
|--------|-----------|---------|------------|
| Libro de ventas (Siigo) | `fecha, cliente_nit, factura, base_iva, iva_facturado, base_exenta` | CSV | Mensual |
| Libro de compras (Siigo) | `fecha, proveedor_nit, factura, base_iva, iva_descontable` | CSV | Mensual |
| Retenciones practicadas | `fecha, beneficiario_nit, pago, base_retencion, porcentaje, valor_retencion, concepto` | CSV | Mensual |
| ICA municipal | `municipio, base_gravable, tarifa_ica, iva_a_descontar` | Calculado | Bimestral |
| XML DIAN (Colombia) | CUFE, fecha, monto, NIT receptor/emisor, estado (aceptada/rechazada) | XML | Continuo |

**Ejemplo de inconsistencia típica**: el libro de ventas de Siigo muestra $120 M COP de base IVA, pero la suma de los XML aceptados por la DIAN arroja $118.5 M COP. La diferencia de $1.5 M puede ser facturas en papel (si el cliente aún las tiene), facturas rechazadas por la DIAN, o un error de registro.

## 5. Tramos determinísticos

1. **Ingesta y normalización**: lectura de los CSV del ERP + XML de la DIAN (en Colombia) o CFDI del SAT (en México). Normalización de NIT/RFC (formato estándar sin guiones).
2. **Cálculo del IVA a pagar/descontar**: `IVA_neto = suma(IVA_facturado) - suma(IVA_descontable)`. Si es negativo, hay saldo a favor. Aritmética pura.
3. **Cálculo de retenciones practicadas por concepto**: agrupación de retenciones por código DIAN (concepto de retención) y suma. Formula cerrada que la DIAN define en la resolución anual de tarifas.
4. **Cálculo del ICA**: `ICA = base_gravable_municipio × tarifa_municipal`. Las tarifas son tablas fijas por municipio (en Colombia, Bogotá tiene tarifa diferencial por actividad económica CIIU). Código que consume una tabla de tarifas.
5. **Conciliación libro vs facturación electrónica**: comparar `suma_ventas_libro` vs `suma_XML_aceptados_DIAN` por período. Calcular la diferencia. Si la diferencia > tolerancia (configurable; default: 0.5 % del total), marcar como `INCONSISTENCIA`.
6. **Generación del borrador de formulario**: plantilla del formulario 300 (IVA Colombia) o DIOT (México) con los valores calculados, lista para que el contador revise y firme. Nunca se presenta automáticamente; siempre hay un `interrupt_before`.
7. **Verificación de plazo**: calcular días hábiles hasta el vencimiento de la declaración (tabla de días hábiles por año fiscal configurable). Si quedan < 3 días hábiles, escalar urgencia.

## 6. Tramos agénticos

1. **Explicación de inconsistencias**: cuando la conciliación libro-DIAN muestra una diferencia, el agente investiga las causas posibles basándose en el detalle de transacciones. «La diferencia de $1.5 M COP parece provenir de 3 facturas emitidas el 30 de abril que la DIAN registra como aceptadas el 2 de mayo (cruce de período). Recomendamos verificar si se incluyeron en el libro del período correcto.» Esta explicación requiere razonamiento sobre el contexto del calendario y las reglas de cut-off. **No es regla** porque las causas posibles son múltiples y la misma diferencia puede tener distintas explicaciones.
2. **Redacción de notas al formulario**: algunos formularios (especialmente declaración de renta anual) requieren notas explicativas de variaciones > X %. El agente redacta esas notas con el contexto del período. No hay plantilla que cubra todos los casos.
3. **Detección de gastos no deducibles en la declaración de renta**: el agente revisa la lista de gastos del período y marca los que probablemente no son deducibles (e.g., multas, sanciones, gastos personales registrados como empresariales). La clasificación de deducibilidad tiene reglas generales en el Estatuto Tributario, pero la aplicación a casos específicos requiere razonamiento. **Siempre va a revisión del contador**; el agente solo señala.
4. **Fallback humano obligatorio**: esta es la ficha con el `human_in_the_loop` más estricto del catálogo. El agente **nunca presenta la declaración**. El flujo siempre termina con el borrador en manos del contador, quien firma y presenta. El nodo `submit_declaration` no existe en este grafo; está bloqueado por diseño. Si el agente detecta una inconsistencia grave (diferencia > 5 % del total de IVA), el flujo se detiene y escala antes de completar el borrador.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_books] → erp_fetch_transactions(erp=siigo, period, account="ventas+compras+retenciones", tenant)
  ↓
[ingest_efactura] → fetch_csv(xmls_dian_aceptados, tenant) [Colombia]
  │                  O fetch_csv(cfdi_sat, tenant) [México]
  ↓
[compute_iva] → cálculo determinístico de IVA neto (Python puro)
  ↓
[compute_retenciones] → agrupación por concepto (determinístico)
  ↓
[compute_ica] → tarifa municipal × base (determinístico)
  ↓
[reconcile_books_efactura] → diferencia libro vs DIAN/SAT (determinístico)
  ↓
[check_inconsistency] → router: ¿diferencia > tolerancia?
  ├─ SÍ → [explain_diff] → LLM explica causas posibles (agéntico)
  │         ↓              tool: sql_query(detalle_transacciones, tenant)
  │         [interrupt_before] → enviar al contador para resolución
  │         ↓ (contador resuelve o acepta la diferencia)
  └─ NO ↓
[flag_non_deductibles] → LLM revisa gastos del período (agéntico)
  ↓                      tool: sql_query(gastos_periodo, tenant)
[draft_form] → genera borrador formulario 300/DIOT (determinístico, plantilla)
  ↓
[check_deadline] → ¿días hábiles restantes < 3? → alerta urgente (determinístico)
  ↓
[interrupt_before_always] → SIEMPRE pausa para revisión del contador
  ↓ (contador aprueba el borrador)
[write_report] → write_report(kind=pdf, "Borrador IVA abril 2026", tenant)
  ↓
[notify] → send_email(to=[contador, CFO], tenant)
  ↓
END
```

> [!cuidado]
> El nodo `submit_declaration` no existe en este grafo por diseño arquitectónico. El agente prepara, el contador presenta. Esta regla es no-negociable independientemente de lo que el cliente pida.

### Activities Temporal (Schedule: día 20 del mes, plazo estimado)

- `ingest_fiscal_data(tenant, period, jurisdiction)` — libros + e-factura.
- `run_fiscal_agent(tenant, period)` — ejecuta el grafo; timeout 10 min.
- `persist_fiscal_draft(tenant, period, payload)` — `idempotency_key = "fiscal:{tenant}:{period}"`.

### Tools necesarias

| Tool | Uso |
|------|-----|
| `erp_fetch_transactions` | Libros de ventas, compras, retenciones |
| `fetch_csv` | XMLs de DIAN / CFDIs del SAT |
| `sql_query` | Detalle de transacciones para análisis de inconsistencias |
| `write_report` | Borrador de formulario en PDF |
| `send_email` | Envío al contador con plazo explícito |

## 8. Salida y entrega

**Borrador de formulario** (PDF con marca de agua «BORRADOR — REQUIERE REVISIÓN DEL CONTADOR»):

- Formulario 300 Colombia / DIOT México con valores calculados.
- Sección de conciliación: libro vs e-factura, diferencias, explicación.
- Sección de notas: gastos potencialmente no deducibles identificados por el agente.
- Checklist de verificación para el contador antes de presentar.

**Email al contador** con:
- Adjunto: borrador PDF.
- Resumen: total IVA a pagar/favor, total retenciones, ICA (si aplica).
- Alerta de plazo: «Quedan N días hábiles para presentar».
- Lista de inconsistencias y preguntas pendientes de resolver.

## 9. Cómo se vende

**Gancho**: «El contador dedica 2 días a preparar la declaración de IVA. Nosotros preparamos el borrador en 30 minutos; él solo lo revisa y lo presenta.»

**Propuesta de valor**: reducción del 80 % del tiempo de preparación; cero inconsistencias que lleguen al fisco sin detectar; plazo siempre monitorizado; trazabilidad completa del borrador.

| Tier | Qué incluye | Precio USD/mes |
|------|-------------|----------------|
| Básico | IVA mensual + retenciones, 1 jurisdicción | 150–300 |
| Estándar | + ICA multi-municipio, conciliación e-factura | 300–600 |
| Premium | multi-jurisdicción, renta anual, SLA contador | 600–1 200 |

Setup: 1 500–3 500 USD (configuración de tarifas municipales, mapeo del PUC a conceptos fiscales, golden set de 3 períodos de referencia).

## 10. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| **Error de cálculo en tarifa**: el agente usa una tarifa de retención desactualizada | Alta | Muy alto | Las tarifas se actualizan anualmente (resolución DIAN/SAT). El agente usa una tabla versionada por año fiscal. Alertar si la tabla tiene > 13 meses de antigüedad. |
| **Presentación sin supervisión**: un operador configura el agente para presentar automáticamente | Muy baja | Crítico | El `interrupt_before` antes de la presentación es hardcoded en el nodo; no es configurable por el operador. Documentar este constraint en el contrato de servicio. |
| **Inconsistencia libro-DIAN no explicable**: la diferencia es real y el agente no puede explicarla | Media | Alto | El agente escala al contador con toda la evidencia disponible. No inventa una explicación. Documenta «no tengo suficiente contexto para determinar la causa». |
| **ICA tarifa incorrecta por municipio**: Bogotá tiene 22 actividades con tarifas distintas | Media | Alto | La tabla de tarifas ICA se actualiza manualmente por el equipo de soporte anualmente. El agente indica de qué fuente toma la tarifa y cuándo fue actualizada. |
| **Datos del NIT de clientes y proveedores en prompts**: son datos fiscales sensibles | Alta | Medio | Los NITs y montos son datos de la empresa, no PII de personas naturales. Los NIT de personas naturales (que coinciden con la cédula) sí son PII; se envían hasheados al LLM. |

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: ventas B2C de alta frecuencia (5 000–50 000 facturas/mes), múltiples plataformas (e-commerce propio + Mercado Libre + Falabella Marketplace), todas generando facturas electrónicas DIAN.

**Delta determinístico**: el volumen de facturas electrónicas requiere una agregación previa (no se puede cruzar 50 000 XMLs uno a uno con el libro). La conciliación se hace a nivel de totales diarios: suma de XMLs aceptados por fecha vs suma del libro por fecha. Si una fecha no cuadra, se profundiza en ese día.

**Delta agéntico**: las devoluciones y contracargos de marketplace generan notas crédito que el agente debe emparejar con las facturas originales para calcular el IVA neto correcto. Un contracargo de Mercado Libre no siempre tiene la misma referencia que la factura original; el agente infiere el emparejamiento.

**Regulación**: el régimen común de IVA en Colombia aplica tarifa general del 19 %. Pero algunos productos de TiendaBox pueden estar en tarifa diferencial (5 %) o exentos. El agente verifica la tarifa aplicada en cada factura contra el catálogo de productos del cliente.

**Precio orientativo**: 300–700 USD/mes; el volumen alto de facturas justifica un tier mayor.

---

### Instancia 2 — Construcción (`andina`)

**Datos típicos**: 30–100 facturas/mes (contratos de obra grandes), retenciones en la fuente complejas (materiales al 3.5 %, mano de obra al 2 %, honorarios al 11 %), ICA diferencial por municipio de la obra.

**Delta determinístico**: el cálculo de retenciones en contratos de construcción sigue una tabla fija de la DIAN (Resolución 000015 de 2024). El agente aplica la tabla al desglose del contrato (materiales vs mano de obra vs AIU). Es aritmética sobre una tabla normativa.

**Delta agéntico**: en algunos contratos de Andina, el desglose materiales/mano de obra no está explícito en la factura; está en el contrato original (PDF). El agente lee el contrato para extraer ese desglose. La extracción de información estructurada desde contratos PDF es agéntica (ver F-CMP referencia).

**Regulación**: en construcción colombiana, las facturas de avance de obra deben correlacionarse con las actas de entrega parcial (documentos que el interventor firma). Una factura sin acta de soporte puede ser glosada por la entidad contratante. El agente verifica que cada factura del período tenga un acta asociada en el sistema de gestión de proyectos del cliente.

**Precio orientativo**: 350–750 USD/mes; menor volumen que retail pero mayor complejidad por tipo de retención.

## 12. Módulos técnicos relacionados

| Módulo | Por qué aplica |
|--------|---------------|
| **E05** — Temporal | El Schedule `día 20 del mes` con alertas de plazo es el caso de uso de E05. El constraint de `idempotency_key = "fiscal:{tenant}:{period}"` garantiza que la corrida no se duplica si el Schedule se reintenta. |
| **E01** — Anthropic SDK | El nodo `explain_diff` es un loop tool_use donde el modelo recibe el detalle de transacciones del período y razona sobre la causa de la inconsistencia. Ejemplo directo de E01. |
| **C01** — SQLAlchemy async | La tabla de tarifas fiscales (IVA, retenciones, ICA) vive en DB y se consulta con `sql_query`. C01 enseña el modelo ORM y la query de lectura. |
| **B02** — FastAPI + Pydantic | El endpoint `/fiscal/approve-draft` que registra el sign-off del contador (con timestamp y usuario) antes de generar el PDF final. Ejemplo de validación y autorización. |
| **D04** — Observabilidad | El trace de Phoenix muestra el costo de los nodos agénticos (`explain_diff`, `flag_non_deductibles`) vs el tiempo total del flujo. El 80 % del flujo es determinístico y gratuito en LLM. |

## 13. Errores típicos

**1. Tabla de tarifas de retención no versionada por año fiscal.**
*Síntoma*: en enero, el agente calcula las retenciones de diciembre usando las tarifas del año nuevo, que la DIAN actualizó con la resolución de enero. Los montos del formulario no coinciden con el ERP.
*Causa*: la tabla de tarifas no tiene campo `vigencia_desde` / `vigencia_hasta`; el agente siempre toma la tarifa más reciente.
*Cómo evitarlo*: la tabla de tarifas en DB debe incluir el rango de fechas de vigencia. El agente consulta la tarifa cuya vigencia cubre la fecha de cada transacción, no la tarifa activa al momento de correr.

**2. Conciliación libro-DIAN con tolerancia absoluta en lugar de porcentual.**
*Síntoma*: para TiendaBox con $800 M COP de base IVA, una tolerancia absoluta de $100 000 COP equivale al 0.01 %; cualquier diferencia real se oculta porque el umbral en monto parece pequeño pero en porcentaje es irrelevante. Para una PYME de $5 M COP de base, $100 000 COP equivale al 2 %, que sí debería alertar.
*Causa*: la tolerancia se configuró como monto fijo en onboarding sin ajustarla al volumen del tenant.
*Cómo evitarlo*: definir la tolerancia como porcentaje del total de la base (default: 0.5 %); traducirla a monto en cada corrida según el volumen real del período.

**3. El borrador se genera aunque haya una inconsistencia sin resolver.**
*Síntoma*: el contador recibe el PDF del borrador del formulario 300 con una diferencia de $3 M COP sin explicar, pero la sección de inconsistencias está al final del PDF y no la ve antes de presentar.
*Causa*: el flujo no bloquea la generación del borrador cuando hay inconsistencias pendientes de resolución.
*Cómo evitarlo*: el nodo `draft_form` solo se ejecuta si el nodo `check_inconsistency` terminó con estado `RESOLVED` o `ACCEPTED_BY_CONTADOR`. Si hay inconsistencias abiertas, el borrador lleva marca de agua «INCOMPLETO — inconsistencias pendientes» y la sección de inconsistencias aparece en la primera página.

**4. Período fiscal de Colombia y México manejado con la misma lógica de plazo.**
*Síntoma*: el Schedule de Temporal corre el día 20 para todos los tenants; los tenants mexicanos (SAT) tienen un plazo diferente y reciben el borrador demasiado tarde.
*Causa*: la variable `deadline_day` estaba hardcodeada a 20 en lugar de ser configurable por `jurisdiction`.
*Cómo evitarlo*: la tabla de configuración del tenant incluye `jurisdiction` (CO / MX / AR) y la tabla de plazos fiscales por jurisdicción. El nodo `check_deadline` consulta la tabla correcta.

## 14. Pregúntale al tutor

1. «Explícame cómo extendería el nodo `compute_retenciones` para manejar un contrato de Constructora Andina donde la factura no desglosa materiales y mano de obra; el desglose está en el contrato PDF adjunto.»
2. «Audita mi diseño del nodo `explain_diff` para TiendaBox con 50 000 facturas mensuales y dime cómo reducir el costo de LLM sin perder calidad en la explicación de inconsistencias.»
3. «Genera el código mínimo del `interrupt_before_always` en LangGraph que bloquea el flujo hasta que el contador haga sign-off y registra el timestamp de aprobación en DB.»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Implementar el cálculo determinístico de IVA, retenciones e ICA usando tablas de tarifas versionadas por año fiscal y jurisdicción.
- Diseñar la conciliación libro–e-factura con tolerancia porcentual configurable por tenant.
- Configurar el `interrupt_before` obligatorio antes de la generación del borrador y justificar por qué no puede ser opcional.
- Decidir qué diferencias escalan al contador de inmediato vs cuáles se incluyen como nota informativa en el borrador.
- Dimensionar el Schedule de Temporal para múltiples tenants con plazos fiscales distintos por jurisdicción.

## 16. Módulos previos recomendados

| Módulo previo | Por qué te prepara |
|---------------|-------------------|
| **E05** — Temporal | El Schedule `día 20 del mes` con idempotencia por `(tenant, period)` es el núcleo de E05; esta ficha es uno de los casos de uso directos de ese módulo. |
| **C01** — SQLAlchemy async | La tabla de tarifas fiscales versionadas y la query de lookup por `(jurisdiction, year, concept)` requieren el modelo ORM que enseña C01. |
| **E01** — Anthropic SDK | El nodo `explain_diff` es un loop `tool_use` donde el modelo razona sobre el detalle de transacciones; E01 enseña ese patrón antes de implementarlo. |
| **B02** — FastAPI + Pydantic | El endpoint `/fiscal/approve-draft` con registro de timestamp de sign-off es el ejercicio de validación y autorización de B02. |
| **D04** — Observabilidad | Verificar en Phoenix que el 80 % del costo está en los nodos agénticos y que el cálculo determinístico no genera llamadas al LLM requiere la instrumentación que enseña D04. |
