---
ext_id: F-CX-04
slug: cliente-en-riesgo
track: F
dept: CX
ord: 243
title: "Detección de cliente en riesgo (CSAT decaying)"
summary: "Pipeline que combina un health score determinístico con análisis agéntico de señales cualitativas para identificar clientes en riesgo de churn y proponer el save play correcto antes de que sea tarde."
related_modules: [B02, C01, D04, E01]
industries_instanced: [servicios-fin, energia]
tenants_in_examples: [cooppopular, solenergy]
big_corp_vendors: [Gainsight, Totango, ChurnZero]
latam_tools: [hubspot, salesforce-essentials, siigo]
key_concepts: [health-score, leading-indicators, save-play, fallback-humano, churn]
estimated_minutes: 45
deterministic_share: 0.5
version: 1
---

## 1. Problema operativo

La gerente de retención de **SolEnergy Distribuidora** lleva 1.200 clientes B2B (empresas, comercios y conjuntos residenciales con contrato de suministro de energía). Sabe por experiencia que 3 semanas antes de que un cliente envíe la carta de terminación del contrato, había señales visibles: subió tickets de facturación, bajó el consumo declarado, y su último correo tenía un tono diferente. Pero nadie leyó esas señales a tiempo porque la cartera es demasiado grande para revisarla manualmente.

El mismo problema existe en **Coop. Popular de Crédito**: de 4.000 socios activos, los 80 que retiraron aportes y cancelaron el crédito en el último trimestre habían reducido sus transacciones mensuales 60% en los 90 días previos. El dato estaba en el sistema; nadie lo procesó.

El costo del churn no detectado no es solo el ingreso perdido: es el costo de adquisición del reemplazo (5x–7x más caro que retener), y la reputación si el cliente se va molesto.

---

## 2. Hoy en big corps

| Vendor | Qué hace | Precio orientativo |
|--------|----------|--------------------|
| **Gainsight** | Customer success platform; health score compuesto (uso, tickets, NPS, CSM inputs); playbooks automatizados; CTAs para el CSM | 2.500–6.000 USD/mes para 500–2.000 clientes; impl. 30–80 k USD |
| **Totango** | Health score modular por SuccessBLOC; integra producto, soporte y CRM; alertas de riesgo con segmentación de cuenta | 1.500–4.000 USD/mes; onboarding 10–30 k USD |
| **ChurnZero** | Orientado a SaaS; score en tiempo real; playbook de retención; integra con HubSpot/Salesforce | 1.000–3.500 USD/mes; mínimo anual |

Nota 2026: según el estudio CS Leadership de ChurnZero (2025), el 73% de los líderes de Customer Success admiten que su health score actual no predice churn con confiabilidad. El problema casi siempre es calidad de datos, no la herramienta. Para la PYME LATAM, el problema es más fundamental: los datos ni siquiera están centralizados.

---

## 3. PYME LATAM realista

**SolEnergy Distribuidora** (utilities/energía, 200 empleados, 1.200 clientes B2B) y **Coop. Popular de Crédito** (servicios financieros, 90 empleados, 4.000 socios) trabajan con:

- **HubSpot Essentials** (45–90 USD/mes) o **Salesforce Essentials** (25–75 USD/usuario/mes): CRM con datos de contacto y notas manuales del ejecutivo de cuenta, sin campos estructurados de health.
- **Siigo** o sistema de facturación propio: historial de pagos, sin API REST usable out-of-the-box.
- Encuestas CSAT por email (tasa de respuesta: 15–25%); los datos quedan en SurveyMonkey o Google Forms, no en el CRM.
- Los tickets de soporte están en Freshdesk o en el WhatsApp del ejecutivo de cuenta, sin relación estructurada con el cliente en el CRM.
- El ejecutivo de cuenta «siente» que un cliente está en riesgo pero no tiene forma sistemática de demostrarlo ni de priorizarlo contra 100 otros clientes en su cartera.

---

## 4. Datos típicos

| Campo | Formato | Fuente | Frecuencia | Volumen |
|-------|---------|--------|------------|---------|
| Consumo / uso del producto | Numérico (kWh/mes o transacciones/mes) | Sistema de facturación / core bancario | Mensual | 1 fila/cliente/mes |
| Tickets de soporte | JSON array (ticket_id, categoría, fecha, estado) | Helpdesk API | Continuo | 0–20 tickets/cliente/mes |
| Estado de pagos | Enum (puntual, tardío, en_mora, saldado) + días_mora | Siigo / ERP | Mensual | 1 fila/cliente/mes |
| Notas del ejecutivo de cuenta | Texto libre | CRM (HubSpot) | Ad hoc | 0–5 notas/cliente/mes |
| Correos del cliente | Texto libre (subject + body) | Email del ejecutivo (con permiso) | Continuo | 0–10 emails/cliente/mes |
| CSAT / NPS | Numérico (1–10) + comentario libre | SurveyMonkey / email | Trimestral | 0–1 respuesta/cliente/trim. |

**Ejemplo de fila de health score calculado**:

```json
{
  "client_id": "SE-0441",
  "period": "2026-03",
  "usage_delta_pct": -28,
  "open_tickets": 3,
  "days_overdue": 12,
  "csat_last": 5,
  "csat_prev": 8,
  "csm_note_count_last_30d": 0,
  "health_score": 31,
  "risk_band": "red"
}
```

---

## 5. Tramos determinísticos

1. **Cálculo del health score base** — fórmula ponderada configurable por tenant en un YAML de configuración:
   ```
   health_score = (
     uso_relativo_vs_periodo_anterior × 0.35 +
     inverso_tickets_abiertos        × 0.25 +
     puntualidad_pagos               × 0.25 +
     csat_normalizado                × 0.15
   ) × 100
   ```
   Todos los inputs son numéricos; la fórmula es Python, no LLM.

2. **Clasificación en bandas de riesgo** — regla cerrada: `score < 40 → red`, `40–65 → yellow`, `> 65 → green`. Los umbrales los define el tenant en onboarding y están en la config; no hay razonamiento.

3. **Alertas duras independientes del score** — siempre activan alerta: 3 tickets de facturación en 30 días, pago con más de 20 días de mora, caída de uso > 50% en 60 días, CSAT < 4 tras llevar > 6 en el trimestre anterior. Son reglas cerradas, no agénticas.

4. **Segmentación por valor de cartera** — join con la tabla de ingresos del tenant: clientes `tier = enterprise` (> X USD/mes) tienen umbrales de alerta más estrictos y escalación obligatoria si caen a `yellow`.

5. **Reporte agregado de la cartera** — distribución de bandas, evolución semanal, clientes que cambiaron de banda. SQL + Python, sin LLM.

---

## 6. Tramos agénticos

1. **Lectura de señales cualitativas del último mes** — el modelo lee notas del CSM y correos del cliente (con permiso y scrubbing de PII) para detectar señales de churn que no aparecen en los números: tono más frío, menciones de «estamos evaluando opciones», quejas acumuladas sin resolución formal, comparaciones con competidores. _Por qué no es regla_: «estamos evaluando opciones» puede ser una negociación de precio o el primer paso hacia la salida; la diferencia está en el contexto completo de la relación, que ningún regex puede evaluar.

2. **Propuesta del save play adecuado** — para clientes en `red`, el modelo propone la intervención específica, no una plantilla genérica: «llamada del gerente de cuenta esta semana» vs. «revisión de tarifa de renovación» vs. «visita presencial para revisar el servicio». _Por qué no es regla_: el save play correcto depende de la razón del riesgo (precio, calidad de servicio, cambio de interlocutor en el cliente, problema técnico recurrente) — razón que solo se infiere del contexto cualitativo.

3. **Priorización de la cartera en riesgo** — cuando hay 20+ clientes en `red` simultáneamente, el modelo ordena quiénes atender primero según: valor en riesgo, probabilidad de retención estimada, señales de urgencia, y capacidad del equipo CSM disponible. _Por qué no es regla_: la urgencia relativa de «cliente A que bajó uso pero no dijo nada» vs. «cliente B que mencionó un competidor» no es calculable con un ranking numérico simple.

> [!cuidado]
> El modelo dice «no tengo suficiente información» cuando el cliente tiene menos de 3 meses de relación (histórico insuficiente), cuando no hay notas ni correos del CSM en 90 días (sin señal cualitativa), o cuando el cliente no respondió ninguna encuesta CSAT. En esos casos, el pipeline marca `insufficient_signal` y el ejecutivo de cuenta recibe una tarea genérica de «contacto de cortesía». El fallback es siempre acción humana, no ausencia de acción.

---

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[collect_signals] → agrega uso, tickets, pagos, CSAT del período (determinístico, tool: sql_query)
  ↓
[compute_health_score] → fórmula ponderada + bandas de riesgo (determinístico)
  ↓
[apply_hard_alerts] → 3 tickets/30d? mora > 20d? caída > 50%? (determinístico)
  ↓
[qualify_signals?] → ¿suficiente señal cualitativa (notas + correos)?
    no → marca insufficient_signal → [assign_courtesy_task] → END
  ↓
[pii_scrub_text] → enmascara PII en notas y correos (determinístico)
  ↓
[read_qualitative_signals] → LLM lee notas + correos del último mes (agéntico)
  ↓
[propose_save_play] → LLM propone intervención por cliente en red (agéntico)
  ↓
[prioritize_portfolio] → LLM ordena cola si > 10 clientes en red (agéntico)
  ↓
[human_review?] → clientes enterprise en red → interrupt obligatorio
  ↓
[assign_tasks] → crea tareas en CRM para los CSMs asignados (determinístico, tool: sql_query)
  ↓
[generate_report] → reporte semanal retención (determinístico, tool: write_report)
  ↓
END
```

### Activities Temporal (para ejecución semanal por tenant)

- `collect_client_signals(tenant, period)` — agrega todas las fuentes; retryable con backoff.
- `run_retention_analysis(tenant, period)` — corre el grafo LangGraph; idempotente por `"retention:{tenant}:{period}"`.
- `push_tasks_to_crm(tenant, period, tasks)` — crea tareas en HubSpot/SF Essentials; idempotente por `task_id`.

### Tools necesarias (ver SHARED §3.6)

- `sql_query` — histórico de uso, tickets, pagos por cliente y período.
- `send_email` — alerta al gerente de retención cuando hay clientes enterprise en riesgo crítico.
- `write_report` — reporte semanal con distribución de bandas y tareas asignadas.

---

## 8. Salida y entrega

**Cola de atención semanal para el equipo CSM** (entregada cada lunes):

```
## Retención — SolEnergy · semana 2026-04-14 → 2026-04-20

Cartera en riesgo
  Red (score < 40):   12 clientes · $48.200 USD en riesgo mensual
  Yellow (40–65):     38 clientes · $94.000 USD en riesgo mensual
  Green (> 65):    1.150 clientes

Prioritarios esta semana (acción antes del viernes):

1. Comercializadora Andina Norte  (score: 23) · $4.200/mes
   Health: uso -41%, 4 tickets abiertos, pago 18 días de mora, CSAT: 4→2
   Señal cualitativa: correo del 11-abr mencionó "estamos revisando nuestra
   infraestructura energética para 2027" — lenguaje de re-evaluación de proveedor.
   Save play: llamada del gerente regional + revisión de tarifa de renovación
   antes de jun-26. Dueño: Valentina R. · Límite: miércoles

2. Conjuntos Las Palmas  (score: 31) · $1.800/mes
   Health: uso -18%, 3 tickets de facturación, pago puntual
   Señal cualitativa: administradora preguntó por "otras opciones de proveedor"
   en nota del CSM del 9-abr.
   Save play: visita presencial + demo de portal de monitoreo de consumo.
   Dueño: Marco T. · Límite: jueves
```

---

## 9. Cómo se vende

**Gancho**: «El 73% de los clientes que se fueron dieron señales visibles 30–60 días antes. El problema no es que las señales no existieran — es que nadie tuvo tiempo de leerlas».

**Propuesta de valor**: el ejecutivo de cuenta llega el lunes con 5 clientes a atender esta semana, en orden de urgencia, con contexto completo y el guión de la conversación. No tiene que revisar 100 cuentas para encontrarlos.

| Tier | Condiciones | Precio |
|------|-------------|--------|
| Starter | ≤ 200 clientes en cartera, 1 CSM | 300–600 USD/mes |
| Growth | ≤ 1.000 clientes, hasta 5 CSMs | 700–1.500 USD/mes |
| Enterprise | > 1.000 clientes + integración ERP profunda | 1.800–4.000 USD/mes |
| Setup | Calibración del health score + golden set 50 clientes históricos | 2.500–7.000 USD |

---

## 10. Riesgos

**1. PII en notas del CSM y correos del cliente.**
*Síntoma*: las notas contienen datos personales de interlocutores («habló con la Dra. García, quien dijo que...») y el modelo los procesa sin enmascarar.
*Mitigación*: el nodo `pii_scrub_text` enmascara nombres propios (NER), cargos identificadores y datos de contacto antes del LLM. Colombia — Ley 1581 / Habeas Data: los contactos de empresas son personas naturales; sus datos requieren tratamiento conforme. Brasil — LGPD art. 5: el interlocutor del cliente es titular de sus datos aún en contexto B2B. Contratos B2B no eximen del habeas data del contacto individual.

**2. Health score que no predice churn real (falsos negativos).**
*Síntoma*: un cliente con score `green` termina el contrato de sorpresa porque cambió el interlocutor y el nuevo no conoce el servicio.
*Mitigación*: `csm_note_count_last_30d == 0` en cliente con > 6 meses de relación genera automáticamente tarea de «contacto de cortesía» sin importar el score. El 73% de los scores que fallan lo hacen por falta de señal (ChurnZero 2025), no por mala fórmula. El golden set de churn histórico se revisa trimestralmente para recalibrar pesos.

**3. Save play incorrecto que acelera el churn.**
*Síntoma*: el modelo propone un descuento de precio para un cliente que se va por calidad de servicio; el descuento se percibe como desesperación y confirma la decisión de salida.
*Mitigación*: el nodo `propose_save_play` siempre incluye la razón inferida del riesgo junto con la propuesta; el CSM revisa y puede rechazar antes de ejecutar. Sin aprobación humana, no hay acción sobre el cliente. Criterio de fallback: si la razón del riesgo es ambigua, el save play siempre es «llamada de descubrimiento» — bajo riesgo, alta información.

**4. Clientes sin señal digital son invisibles (sesgo de cobertura).**
*Síntoma*: el pipeline solo ve señales de clientes que usan email y responden CSAT; clientes en riesgo que no interactúan digitalmente tienen score artificialmente alto.
*Mitigación*: cualquier cliente sin interacción registrada en 60 días recibe flag `dark_period` y tarea manual de contacto para el CSM, independientemente del score. La ausencia de señal es tratada como señal de riesgo, no como señal positiva.

---

## 11. Variantes por industria

### Instancia 1 — Servicios financieros (`cooppopular`)

**Datos típicos**: 4.000 socios activos; churn en cooperativa = retiro de aportes + cierre de productos; señales cuantitativas: frecuencia de transacciones, saldo promedio, uso de crédito, puntualidad de aportes mensuales.

**Delta determinístico**: el health score pondera `reduccion_saldo_aportes_pct` (retiro del 50% de aportes es señal dura de salida) y `meses_sin_credito_activo` (más de 12 meses sin crédito nuevo en un socio con historial de 1–2 créditos/año). Ambos campos son calculables sin LLM.

**Delta agéntico**: el modelo distingue si los retiros de aportes corresponden a una necesidad de liquidez temporal (oportunidad para ofrecer crédito de emergencia) vs. una decisión de salida (retención urgente). La distinción requiere leer las notas del asesor y el historial de la relación.

**Regulación**: Superfinanciera Colombia — las cooperativas financieras están sujetas al mismo régimen de habeas data que los bancos (Ley 1266). Los datos de transacciones de los socios son datos semisensibles; el pipeline no puede usarlos para fine-tuning externo del modelo sin autorización expresa en los estatutos.

**Precio orientativo**: 400–900 USD/mes para 4.000 socios; setup con integración al core cooperativo: 3.000–8.000 USD.

### Instancia 2 — Energía / Utilities (`solenergy`)

**Datos típicos**: 1.200 clientes B2B; churn = no renovar contrato al vencimiento o solicitar terminación anticipada (con penalidad); señales: consumo declarado vs. real, tickets de medición, pagos con mora, consultas sobre «cambio de proveedor» o «auditoría energética».

**Delta determinístico**: el contrato tiene fecha de vencimiento conocida. El nodo `contract_expiry_check` emite alerta `renewal_risk` cuando el contrato vence en < 90 días y el score < 60, con escalación obligatoria al gerente de cuenta — sin necesidad de análisis agéntico.

**Delta agéntico**: el modelo detecta si el cliente menciona en correos o notas del CSM que está «haciendo una auditoría energética» o «evaluando eficiencia» — señales de un proceso de decisión de cambio de proveedor que no se expresan como queja directa. En utilities, este lenguaje corporativo es el equivalente de «estamos revisando opciones».

**Regulación**: Colombia — CREG regula los contratos de suministro de energía; las penalidades por terminación anticipada son contractuales y el pipeline no puede instruir evasiones. El agente puede sugerir renegociar condiciones; la firma final es siempre humana. Los datos de consumo de empresas son datos comerciales (no personales stricto sensu), pero los datos de los contactos sí están sujetos al habeas data.

**Precio orientativo**: 800–2.000 USD/mes para 1.200 clientes B2B con alta rotación de contratos; setup con integración al sistema de facturación: 4.000–10.000 USD.

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de él |
|--------|-----------------|
| **B02** — FastAPI routing | El endpoint `GET /retention/report` sirve el reporte semanal al gerente de CX; el `Depends(get_tenant)` garantiza que cada empresa ve solo su cartera con su fórmula de health score. |
| **C01** — SQLAlchemy async | La tabla `client_signals` acumula señales por período; las queries de agregación usan `select()` con `group_by(client_id, period)` — el módulo enseña exactamente este patrón de agregación async sobre SQLite/Postgres. |
| **D04** — Observabilidad | Cada ejecución del pipeline produce un span en Phoenix con: `tenant_id`, clientes analizados, distribución de bandas, tokens consumidos en el análisis cualitativo. El equipo puede auditar por qué un cliente se clasificó en `red`. |
| **E01** — Anthropic SDK | Los nodos `read_qualitative_signals` y `propose_save_play` usan `cache_control: ttl:"1h"` sobre el system prompt con la fórmula del health score y las instrucciones de save plays del tenant (estáticos); los datos del cliente van sin cache (dinámicos, cambian por cliente). |
| **E05** — Temporal | El schedule `weekly_retention_analysis` corre cada lunes a las 6 AM por tenant con idempotency key `"retention:{tenant_id}:{iso_week}"`; si el pipeline falla (API del CRM caída), Temporal lo reintenta con backoff sin duplicar el análisis ni las tareas en el CRM. |

## 13. Errores típicos

**1. PII de los interlocutores del cliente en las notas del CSM enviadas al LLM sin scrubbing.**
*Síntoma*: las notas del CSM contienen «habló con la Dra. García, directora de compras, quien mencionó que...» y esa información aparece en los logs del nodo `read_qualitative_signals`.
*Causa raíz*: el nodo `pii_scrub_text` no fue aplicado a las notas del CRM antes de enviarlas al modelo porque el desarrollador asumió que las notas no contenían PII.
*Cómo evitarlo*: las notas del CSM siempre pasan por el scrubber de NER (nombres propios, cargos identificadores, datos de contacto) antes del LLM. Bajo Ley 1581 (Colombia) y LGPD (Brasil), los contactos B2B son personas naturales cuyos datos requieren protección aunque el contrato sea corporativo.

**2. Save play incorrecto ejecutado sin revisión humana porque se desactivó el interrupt.**
*Síntoma*: el pipeline propone un descuento del 15% a un cliente que se va por calidad de servicio; como el interrupt de revisión estaba desactivado en el tier Growth, el descuento se crea automáticamente en el CRM.
*Causa raíz*: se configuró `human_review = optional` para clientes que no son enterprise, pensando en reducir carga operativa.
*Cómo evitarlo*: el interrupt antes de `assign_tasks` es obligatorio para cualquier save play que involucre una acción sobre el cliente (llamada, descuento, visita). Solo el reporte de bandas (sin acciones) puede generarse sin interrupt.

**3. Health score artificialmente alto para clientes sin señal digital (sesgo de cobertura).**
*Síntoma*: tres clientes de SolEnergy con score `green` no renuevan contrato; al revisar, ninguno había interactuado digitalmente en 90 días.
*Causa raíz*: la ausencia de señal se interpreta como señal neutra en la fórmula del health score.
*Cómo evitarlo*: cualquier cliente sin interacción registrada en > 60 días recibe flag `dark_period` y el campo `dark_period_flag` baja el score en 15 puntos independientemente de los demás indicadores.

**4. Recalibración de pesos del health score sin golden set actualizado.**
*Síntoma*: el equipo ajusta los pesos del health score trimestralmente pero lo hace en base a intuición, no a comparación con churn real histórico.
*Causa raíz*: el golden set de churn histórico no se actualiza con los clientes que abandonaron en el último trimestre.
*Cómo evitarlo*: el golden set se amplía mensualmente con los nuevos casos de churn confirmado. Cada recalibración de pesos se valida contra el golden set antes de aplicarse en producción.

---

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame por qué el health score determinístico no es suficiente por sí solo y qué aporta el análisis cualitativo agéntico con un ejemplo concreto de un cliente que el score no habría detectado.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este pipeline si mi cartera de retención son personas naturales (B2C) en lugar de empresas B2B, donde no hay notas del CSM ni correos corporativos para analizar.»
3. **Por qué falló**: «SolEnergy tenía al cliente SE-0441 con score 31 (red) pero el CSM no actuó a tiempo. ¿En qué parte del pipeline se rompió el flujo y qué cambio en el nodo `assign_tasks` lo habría prevenido?»

---

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el health score multi-señal con la fórmula ponderada configurable por tenant, incluyendo las alertas duras independientes del score.
- Implementar el scrubbing de PII en notas del CSM y correos antes del análisis cualitativo agéntico, cumpliendo Ley 1581 y LGPD.
- Identificar los casos de `insufficient_signal` y `dark_period` y asignarles el fallback humano correcto.
- Evaluar la calidad del save play propuesto por el modelo comparándolo con el golden set de churn histórico del tenant.
- Decidir cuándo el interrupt de revisión humana es obligatorio versus optativo en función del tipo de acción sobre el cliente.

---

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|---------------------------------|
| **E01** — Anthropic SDK + tools | Los nodos `read_qualitative_signals` y `propose_save_play` usan `cache_control` sobre el system prompt con la fórmula del health score y los save plays del tenant; sin E01, el estudiante no sabe cuándo cachear y cuándo no. |
| **E04** — Memoria y sesiones | El historial de interacciones del cliente (notas del CSM, tickets anteriores, CSAT histórico) se inyecta como contexto de sesión por `client_id`; E04 enseña a gestionar este estado entre ejecuciones semanales del pipeline. |
| **C01** — SQLAlchemy async | La tabla `client_signals` y las queries de agregación por `client_id` y `period` son el corazón del tramo determinístico; sin C01, el estudiante no puede implementar el `collect_signals` correctamente. |
| **D04** — Observabilidad y trazas auditables | Cada ejecución del pipeline produce un span con la distribución de bandas y los tokens del análisis cualitativo; D04 enseña a auditar por qué un cliente específico fue clasificado en `red`. |
| **E05** — Temporal + idempotencia | El schedule semanal con idempotency key es el patrón central para evitar duplicar tareas en el CRM; E05 es prerequisito directo. |
