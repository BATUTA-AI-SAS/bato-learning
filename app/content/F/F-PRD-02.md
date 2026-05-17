---
ext_id: F-PRD-02
slug: triage-bugs-duplicados
track: F
dept: PRD
ord: 281
title: "Triage de bugs y detección de duplicados"
summary: "Agente que clasifica bugs por severidad y componente, detecta duplicados semánticos (mismo fallo reportado con distintas palabras), sugiere el dueño del issue, y escala los críticos antes de que lleguen a la daily del equipo."
estimated_minutes: 45
industries_instanced: [servicios-fin, serv-prof]
tenants_in_examples: [cooppopular, consultorabc]
---

## 1. Problema operativo

El equipo de ingeniería de Coop. Popular de Crédito (5 devs, app de crédito digital) recibe entre 30 y 60 bugs por mes. Llegan de tres fuentes: errores automáticos de Sentry, tickets de soporte del equipo de atención al cliente, y reportes directos de usuarios. El mismo bug suele llegar por los tres canales en distintas palabras. El dev lead dedica los primeros 20 minutos de cada mañana a leer el tracker, deduplicar a mano y asignar. Es tiempo de desarrollo que se consume en burocracia.

Consultora ABC tiene 2 devs y un tracker en Linear con 80 issues abiertos. No saben cuáles son críticos hoy. La última vez que se les pasó un bug de producción crítico fue porque estaba enterrado en los 80 issues sin prioridad.

---

## 2. Hoy en big corps

Los equipos de ingeniería con 20+ devs y presupuesto tienen herramientas de bug intelligence integradas al tracker.

| Vendor | Capacidad | Precio orientativo |
|--------|-----------|-------------------|
| **Linear AI** (2026) | Triage automático, sugerencia de severity, dedup por similitud, integración con Sentry | Linear Pro: 8 USD/usuario/mes; AI features incluidas |
| **GitHub Copilot for PRs** | Análisis de issues relacionados, sugerencia de fix approach, dedup dentro de GitHub Issues | 19–39 USD/usuario/mes |
| **Jira AI** (Atlassian Intelligence) | Clasificación automática de severity, sugerencia de componente, dedup | Jira Premium: 14–16 USD/usuario/mes |
| **Sentry** (error monitoring, plan Business) | Agrupación de errores por stack trace, alertas de regresión | 26–89 USD/mes según volumen |

La PYME puede pagar Linear Pro o Sentry free tier. Lo que no tiene es la integración entre el error automático de Sentry y el issue humano de Linear — ese gap es donde los duplicados se acumulan.

---

## 3. PYME LATAM realista

Coop. Popular y Consultora ABC trabajan con:
- **Sentry** (free tier: 5 000 errores/mes) para errores automáticos de backend.
- **Linear** (Starter: gratis hasta 250 MB) para el tracker de issues.
- **Intercom** o email directo para tickets de soporte que mencionan bugs.
- Comunicación por **WhatsApp** entre el equipo cuando algo se rompe en producción.

El flujo actual: Sentry manda un email → alguien lo lee → crea un issue en Linear → alguien ya había creado otro issue similar el día anterior. El tracker tiene 40% de duplicados. La deuda de limpieza nadie la paga.

---

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen |
|--------|---------|------------|---------|
| Sentry events | JSON vía webhook + API | Tiempo real | 50–500 eventos/mes (agrupa por fingerprint) |
| Linear issues (tag `bug`) | JSON vía API | Continuo | 20–50/mes |
| Intercom tickets con keyword "error/falla/no funciona" | JSON vía API | Continuo | 10–30/mes |
| Reportes directos (email, WhatsApp) | Texto libre | Esporádico | 5–15/mes |

Ejemplo de registro:
```json
{
  "source": "sentry",
  "tenant_id": "cooppopular",
  "event_id": "abc-123",
  "title": "TypeError: Cannot read property 'monto' of null",
  "stack_trace_hash": "sha256:d4e5f6...",
  "component": "api.creditos.solicitud",
  "occurrences": 47,
  "affected_users": 12,
  "first_seen": "2026-05-13",
  "last_seen": "2026-05-16",
  "severity_sentry": "error"
}
```

---

## 5. Tramos determinísticos

1. **Ingesta y normalización**: pull de cada fuente vía API. Esquema unificado: `{source, raw_text, component_hint, stack_trace_hash, occurrences, affected_users, date, tenant_id}`.
2. **Deduplicación por hash de stack trace**: si dos issues tienen el mismo `stack_trace_hash` (Sentry fingerprint o hash propio), son el mismo bug. Vincular y no crear duplicado. Este paso es exacto y barato.
3. **Clasificación por componente via reglas**: el `component_hint` de Sentry (path del módulo que falla) mapea a componentes del sistema via tabla de reglas del tenant: `api.creditos.*` → `Créditos`, `api.pagos.*` → `Pagos`, `app.ui.login` → `Autenticación`. Asignación de componente sin LLM.
4. **Scoring de severidad base**: regla cuantitativa: `severity_score = affected_users * 3 + occurrences * 0.5`. Thresholds: `CRITICAL (>= 50)`, `HIGH (20–49)`, `MEDIUM (5–19)`, `LOW (< 5)`. Esto es la severidad técnica antes de contexto.
5. **Alerta automática CRITICAL**: si `severity_score >= 50` → notificación inmediata por Slack al dev lead + CTO, independientemente del proceso de triage. No espera al agente agéntico.

---

## 6. Tramos agénticos

1. **Detección de duplicados semánticos** — el mismo bug reportado en palabras distintas por distintas fuentes: "no puedo ver el saldo de mi crédito" (ticket de soporte) es el mismo issue que "NullPointerException en CreditoSaldoView" (Sentry) que "el módulo de créditos falla al cargar" (issue de Linear creado por el dev). El modelo recibe los candidatos (agrupados por componente y período de tiempo) y decide cuáles son el mismo problema subyacente.

   *Por qué no es regla*: la equivalencia semántica entre un error técnico (stack trace) y un reporte de usuario en lenguaje natural no tiene regla cerrada. "No puedo pagar" puede ser el mismo bug que "timeout en /api/pagos/procesar" o puede ser un problema de configuración de PSP distinto.

2. **Clasificación de severidad desde reporte humano** — un ticket de soporte dice "mi cliente no puede hacer el desembolso de su crédito". No hay stack trace. El modelo infiere: ¿es esto `CRITICAL` (bloquea una operación de negocio para un usuario activo) o `HIGH` (bug real pero tiene workaround)? La clasificación depende del contexto de la operación (desembolso es el core del negocio de una cooperativa de crédito).

   *Por qué no es regla*: la criticidad de una funcionalidad depende del modelo de negocio del tenant. "No puedo ver el historial de pagos" es `MEDIUM` para un e-commerce pero puede ser `HIGH` para una cooperativa que necesita reportarlo a la SFC mensualmente.

3. **Sugerencia de dueño** — el modelo sugiere el dev más apropiado para el bug basándose en: el componente afectado, el historial de commits recientes en ese módulo (si se integra con GitHub), y el conocimiento previo del equipo (capturado en el perfil del tenant como "María es dueña del módulo de pagos").

   *Por qué no es regla*: el ownership de componentes cambia, los devs rotan, y a veces un bug de frontend tiene causa raíz en backend. La sugerencia es una orientación, no una asignación.

4. **Fallback humano**: el modelo marca con `TRIAGE_NEEDED` cualquier bug donde la severidad no puede determinarse sin más contexto (ej.: reporte ambiguo sin reproducción, sistema afectado desconocido). El dev lead recibe esos bugs con la pregunta explícita que necesita respuesta para clasificarlos.

---

## 7. Blueprint del workflow

```
[INGEST]
  sentry_fetcher | linear_fetcher | intercom_fetcher
  → unified_bug_list
      |
[DEDUP_EXACT]                (determinístico — hash de stack trace)
  → grupos de duplicados exactos
      |
[CLASSIFY_COMPONENT]         (determinístico — tabla de reglas del tenant)
  → component_tag por issue
      |
[SEVERITY_SCORE]             (determinístico — fórmula cuantitativa)
  → severity_level: CRITICAL | HIGH | MEDIUM | LOW
      |
  severity = CRITICAL → alerta inmediata Slack (sin esperar agente)
      |
[DEDUP_SEMANTIC]             ← agéntico
  LLM: (candidatos agrupados por componente + período)
  → clusters de duplicados semánticos
      |
[CLASSIFY_SEVERITY_HUMAN]    ← agéntico (solo para reportes sin stack trace)
  LLM: (reporte_texto, tenant_context)
  → {severity, rationale, confidence}
  confidence < 0.7 → TRIAGE_NEEDED
      |
[SUGGEST_OWNER]              ← agéntico
  LLM: (component, recent_commits_summary, tenant_team_profile)
  → suggested_owner: dev_id
      |
[BUILD_TRIAGE_REPORT]        (determinístico)
  → Linear: crear/actualizar issues con severity, component, owner sugerido
  → Slack: digest diario con top 10 bugs
```

---

## 8. Salida y entrega

**Digest diario en Slack** (06:30 AM):

```
TRIAGE DIARIO — Coop. Popular de Crédito | 2026-05-16

CRÍTICOS (acción inmediata)
  🔴 [BUG-341] Falla en desembolso de crédito — 12 usuarios afectados
     Duplicado de: Sentry abc-123 + ticket IC-4521 + Linear BUG-338
     Componente: Créditos | Sugerido: María López | Occurrences: 47

ALTOS (resolver esta semana)
  🟠 [BUG-340] Saldo no actualiza tras pago anticipado — 5 usuarios
  🟠 [BUG-339] PDF de extracto no genera en Firefox — 18 occurrences

TRIAGE NECESARIO (el equipo debe decidir)
  ❓ [BUG-342] "La app tarda mucho" — no reproducible sin más info
     Pregunta para el equipo: ¿a qué pantalla se refiere?

CERRADOS COMO DUPLICADO HOY: 4 issues
```

---

## 9. Cómo se vende

**Gancho**: "Tu equipo empieza cada mañana limpiando el tracker. Este agente lo hace mientras duermen. Entran a la daily sabiendo exactamente qué está en llamas."

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Starter | 2 fuentes (Sentry + Linear), digest diario Slack | 150–250 USD/mes |
| Profesional | 4 fuentes, dedup semántico, sugerencia de dueño, integración GitHub | 300–600 USD/mes |
| Fintech | Multi-tenant, SLA-tracking, reportes de incidentes para auditoría | 500–1 000 USD/mes |

Setup (configuración de fuentes, tabla de componentes del tenant, perfil del equipo): 500–1 200 USD una vez.

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Dedup incorrecto** (cerrar como duplicado un bug que es distinto) | Se pierde un bug real en producción | El agente no cierra issues automáticamente — solo los vincula y sugiere cierre. El dev confirma. Logs de cada decisión de dedup con el rationale del modelo. |
| **Severidad subestimada** (clasificar como LOW algo CRITICAL) | Un bug crítico queda sin atención hasta el día siguiente | La alerta CRITICAL es determinística (score numérico) y no pasa por el LLM. El LLM solo sube la clasificación, nunca la baja de lo que el score indica. |
| **Falsa alerta CRITICAL** (score alto por un spike de errores transitorios) | Equipo interrumpido innecesariamente | Ventana de 15 min: si el error cae solo en < 15 min, la alerta se cancela y se registra como "transient spike". |
| **Sugerencia de dueño incorrecta** | El dev asignado no sabe nada del componente | La sugerencia es solo eso — sugerencia. El dev lead hace la asignación final. El sistema aprende de las correcciones históricas. |
| **PII en stack traces o logs** | Datos de usuarios en el sistema de triage | Scrubber de PII en el pipeline de ingesta (Sentry tiene scrubber nativo; para otras fuentes, regex sobre CC, email, teléfono antes de almacenar). |

---

## 11. Variantes por industria

| Delta | Servicios financieros (Coop. Popular) | Servicios profesionales (Consultora ABC) |
|-------|---------------------------------------|-----------------------------------------|
| Stack tecnológico típico | Python backend, React Native app móvil, Postgres | Python / Node.js, web app, PostgreSQL o Airtable |
| Fuentes de bugs | Sentry + Linear + tickets de soporte interno | Linear + GitHub Issues + email de clientes |
| Criticidad más frecuente | CRITICAL: fallas en pagos/créditos (impacto regulatorio SFC) | HIGH: features que no funcionan para el cliente que las solicitó |
| Regulación afectada | SFC exige incidentes mayores reportados en < 72 h | Ninguna regulación específica de software |
| Dueño típico de bugs | Dev especializado por dominio (créditos, pagos, reportes) | 1–2 devs full-stack que cubren todo |
| Latencia tolerable | 0 para CRITICAL (alert en tiempo real), < 4 h para HIGH | 24 h para HIGH; semanal para MEDIUM/LOW |
| Precio tier profesional | 500–700 USD/mes (SLA + reportes incidentes) | 250–400 USD/mes |

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica |
|--------|-----------|
| **A06** — Type hints y protocolos | `BugReport`, `TriageResult`, `DuplicateCluster` como dataclasses; `Protocol` para fetchers de distintas fuentes (Sentry, Linear, Intercom). |
| **B02** — FastAPI routers y deps | Endpoint `POST /bugs/ingest` para webhooks de Sentry; `GET /bugs/triage?tenant_id=X&date=today` para el reporte del día. |
| **C01** — SQLAlchemy y modelos ORM | Modelo `BugReport` con `source`, `severity`, `component`, `duplicate_of`, `tenant_id`; índice compuesto `(tenant_id, stack_trace_hash)` para dedup exacto O(1). |
| **E01** — Anthropic SDK tool loop | El loop de dedup semántico: el modelo llama a `get_bug_details(bug_id)` para leer el texto completo de cada candidato antes de decidir si son duplicados. |
| **D04** — Observabilidad Phoenix | Span por decisión de dedup semántico; alerta si la tasa de falsos positivos en dedup supera 10% (medido contra correcciones del dev lead). |

---

## 13. Errores típicos

**1. Clustering de bugs distintos como duplicados.**
*Síntoma*: el agente marca «no puedo ver el saldo de mi crédito» (bug de UI en la app) y «timeout en /api/creditos/saldo» (error de red en backend) como duplicados; el equipo cierra el issue de UI creyendo que el backend los resuelve a ambos.
*Causa raíz*: el nodo `DEDUP_SEMANTIC` agrupó por componente y síntoma superficial sin verificar que la causa raíz es distinta.
*Cómo evitarlo*: el agente incluye en su rationale de dedup la pregunta explícita «¿la misma causa raíz o causas independientes que producen el mismo síntoma?». Si el modelo no puede determinar la causa raíz con los datos disponibles, marca el par como `TRIAGE_NEEDED` en lugar de confirmarlo como duplicado. El dev confirma antes de vincular.

**2. Severidad subestimada por ausencia de stack trace.**
*Síntoma*: un ticket de soporte dice «mi cliente no puede hacer el desembolso»; el agente lo clasifica como `MEDIUM` porque no hay stack trace y `affected_users` aparece como 1.
*Causa raíz*: el scoring determinístico usa `affected_users * 3 + occurrences * 0.5`; sin datos numéricos, la fórmula produce un score bajo aunque la operación afectada sea el core del negocio.
*Cómo evitarlo*: el nodo `CLASSIFY_SEVERITY_HUMAN` tiene instrucción explícita de elevar la severidad cuando la operación afectada es core del modelo de negocio del tenant (configurado en el perfil del tenant: `critical_operations: ["desembolso", "pago", "solicitud_credito"]`). Si la descripción toca una `critical_operation`, la severidad mínima es `HIGH` independientemente del score numérico.

**3. Dedup automático sin trail de auditoría.**
*Síntoma*: el agente vincula issues como duplicados y la semana siguiente nadie sabe por qué BUG-338 quedó vinculado a BUG-341; si la decisión fue incorrecta, no hay forma de revertirla con contexto.
*Causa raíz*: el sistema solo registra el resultado del dedup, no el rationale del modelo.
*Cómo evitarlo*: cada decisión de dedup persiste con `{issue_a, issue_b, decision, rationale_text, confidence, decided_by: "agent", reviewed_by: null}`. El dev lead puede marcar `reviewed_by` y `override: true` si la decisión fue incorrecta. Las correcciones históricas alimentan el golden set de calibración.

**4. Alerta CRITICAL por spike transitorio de errores.**
*Síntoma*: un deploy fallido genera 200 errores en 3 minutos antes de ser revertido; el agente manda alerta CRITICAL al CTO a las 11PM para un problema que ya no existe.
*Causa raíz*: la alerta CRITICAL se dispara por score instantáneo sin ventana de estabilización.
*Cómo evitarlo*: la alerta CRITICAL requiere que el score se mantenga sobre el umbral durante una ventana de 15 minutos. Si los errores caen solos antes de los 15 minutos, la alerta se cancela y se registra como `transient_spike` con el contexto del deploy asociado.

**5. PII en stack traces almacenado en la base de datos del agente.**
*Síntoma*: los stack traces de Sentry incluyen valores de variables locales que contienen email o número de documento de un usuario; esos datos quedan en la tabla `BugReport`.
*Causa raíz*: el pipeline de ingesta no tiene scrubber de PII antes de persistir.
*Cómo evitarlo*: el nodo `INGEST` aplica regex sobre el texto de cada issue antes de persistir: sustituye patrones de email, teléfono y número de identificación por `[REDACTED]`. Sentry tiene scrubber nativo; para otras fuentes la capa extra es obligatoria.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre deduplicación por hash de stack trace (determinístico) y deduplicación semántica (agéntico) con el ejemplo de Coop. Popular — ¿cuándo cada una falla y por qué necesito las dos?»
2. **Aplícalo a mi caso**: «Mi cliente tiene bugs que llegan por WhatsApp de sus propios clientes, sin stack trace ni información técnica. ¿Cómo configuro el scoring de severidad para esos reportes?»
3. **Por qué falló**: «El agente marcó como duplicados dos bugs que el dev lead confirmó que son distintos. ¿Cómo reviso el rationale de la decisión y qué configuro para que no vuelva a pasar?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Construir el pipeline de ingesta desde Sentry, Linear e Intercom con deduplicación exacta por hash y scoring determinístico de severidad.
- Diseñar el nodo agéntico de deduplicación semántica con rationale persistido y confirmación del dev lead.
- Configurar la alerta CRITICAL con ventana de estabilización de 15 minutos para evitar falsas alarmas por spikes transitorios.
- Implementar el scrubber de PII en el pipeline de ingesta antes de persistir cualquier texto de issue.
- Cotizar y dimensionar el servicio para servicios financieros y servicios profesionales LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué leerlo antes |
|--------|---------------------|
| **A06** — Type hints y protocolos | `BugReport`, `TriageResult` y `DuplicateCluster` como dataclasses; el `Protocol` para fetchers permite añadir Sentry, Linear e Intercom con la misma interfaz. |
| **C01** — SQLAlchemy async | El índice compuesto `(tenant_id, stack_trace_hash)` para dedup O(1) y el modelo `BugReport` con FK a `duplicate_of` son patrones directos de C01. |
| **D04** — Observabilidad | Span por decisión de dedup semántico; sin trazabilidad en Phoenix no hay forma de auditar qué porcentaje de dedup agéntico el dev lead corrige. |
| **E01** — Anthropic SDK tool loop | El loop de dedup semántico: el modelo llama a `get_bug_details(bug_id)` para leer el texto completo de cada candidato antes de decidir; E01 enseña ese patrón con tool use iterativo. |
