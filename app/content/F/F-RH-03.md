---
ext_id: F-RH-03
slug: onboarding-personalizado
track: F
dept: RH
ord: 222
title: "Onboarding personalizado por rol y área"
summary: "Chat de onboarding que responde preguntas del nuevo empleado usando la documentación interna del tenant, adaptando el nivel de detalle al perfil (senior vs junior)."
related_modules: [B02, B03, E01, E03]
industries_instanced: [serv-prof, retail]
tenants_in_examples: [consultorabc, tiendabox]
big_corp_vendors: [Workday Onboarding, Enboarder, Sapling]
latam_tools: [notion, confluence-cloud, sharepoint]
key_concepts: [checklist-por-rol, glosario-empresa, mentor-asignado, dia-30-60-90, fallback-humano]
estimated_minutes: 30
deterministic_share: 0.3
version: 1
---

## 1. Problema operativo

El director de **Consultora ABC** tiene tres nuevos consultores empezando en la misma semana: uno con 8 años de experiencia en proyectos de transformación digital, uno recién graduado, y uno de una consultora competidora que conoce metodologías pero no los procesos internos. Los tres reciben el mismo pack de bienvenida de 40 páginas en PDF, el mismo tour de 2 horas, y el mismo «pregúntale a quien tengas al lado». El senior se aburre con explicaciones de conceptos que ya domina. El junior se pierde en jerga interna. El transferido de competencia tiene las preguntas en los primeros 3 días pero no sabe a quién preguntarle sin parecer incompetente. El resultado: 3–6 semanas hasta productividad real, cuando podría ser 1–2.

---

## 2. Hoy en big corps

| Vendor | Qué hace | Precio orientativo |
|--------|----------|--------------------|
| **Workday Onboarding** | Flujos de tareas pre-start + día 1 integrados con HRIS; asignación automática de equipos/sistemas | Incluido en Workday HCM; 6–15 USD/empleado/mes |
| **Enboarder** | Workflows de onboarding personalizados con triggers por rol/fecha; nudges automáticos a mentor y manager | 4–10 USD/empleado/mes; mínimo 10 k USD/año |
| **Sapling (ahora Kallidus)** | HRIS ligero + onboarding checklist + portal del nuevo empleado | 6–9 USD/empleado/mes |

En 2026, Enboarder y los módulos de IA de estas plataformas permiten adaptar el contenido según el rol y nivel, pero la personalización real (responder preguntas sobre procesos internos específicos) sigue requiriendo un humano o una base de conocimiento bien mantenida.

---

## 3. PYME LATAM realista

**Consultora ABC** (35 personas, servicios profesionales) y **TiendaBox Retail** (80 empleados, e-commerce + tienda física) operan con:

- Un **folder en Google Drive o Notion** con manuales de procedimientos, plantillas, y el organigrama.
- Un **checklist en Excel o Notion** que HR imprime y le da al nuevo empleado el día 1.
- El **mentor informal** = el compañero de al lado, que responde cuando puede.
- Las preguntas repetidas («¿cómo registro las horas?», «¿cuál es el proceso para pedir vacaciones?») las responde RRHH por WhatsApp, una y otra vez, para cada nuevo empleado.

---

## 4. Datos típicos

| Campo | Formato | Fuente | Frecuencia | Volumen |
|-------|---------|--------|------------|---------|
| Documentación interna | Markdown, PDF, DOCX | Notion / Drive del tenant | Actualización continua | 50–500 documentos, 1–50 KB/doc |
| Perfil del nuevo empleado | JSON (rol, área, nivel, fecha inicio) | HRIS o formulario HR | Por contratación | 1 fila |
| Checklist de onboarding por rol | YAML / Notion template | HR | Actualización trimestral | 10–30 ítems por rol |
| Historial de preguntas frecuentes | Chat logs anonimizados | Sistema de onboarding | Continuo | Crece con el uso |

**Ejemplo de perfil**:

```json
{
  "employee_id": "EMP-2026-041",
  "role": "consultant_senior",
  "area": "digital_transformation",
  "level": "senior",
  "start_date": "2026-05-20",
  "previous_industry": "banca",
  "tenant": "consultorabc"
}
```

---

## 5. Tramos determinísticos

1. **Generación del checklist personalizado** — por `role` + `area`, lookup en tabla de checklists del tenant; asignación de ítems con fechas relativas al `start_date`. Sin LLM: es un join entre el perfil y la tabla de tareas.
2. **Asignación de recursos obligatorios** — credenciales de sistemas, accesos a repositorios, equipo de hardware: se generan tickets en el sistema del tenant (Jira, GitHub Org invite, etc.) por regla determinística.
3. **Indexado de la documentación del tenant** — documentos de Drive/Notion se convierten a texto plano, se chunkan y se indexan en un vector store (ChromaDB o PGVector). Este proceso es determinístico y se re-ejecuta cuando hay actualización de docs.
4. **Filtro de acceso por rol** — antes de recuperar fragmentos de la documentación, el sistema verifica que el documento esté marcado como accesible para el `role` del nuevo empleado. Sin LLM.
5. **Tracking de progreso del checklist** — cada ítem tiene estado `pending / done / skipped`; el progreso se calcula aritméticamente y se reporta al manager.

---

## 6. Tramos agénticos

1. **Respuesta a preguntas del nuevo empleado usando la doc interna** — el nuevo empleado pregunta en el chat del onboarding; el agente recupera fragmentos relevantes (RAG sobre la doc del tenant) y responde con lenguaje adaptado al `level` del perfil. _Por qué no es regla_: la pregunta puede estar formulada en términos que no matchean el título del documento; la adaptación de nivel (senior recibe la razón detrás del proceso; junior recibe el paso a paso) exige juicio contextual.

2. **Detección de gaps en la documentación** — cuando el agente no encuentra respuesta satisfactoria (baja similitud coseno en el RAG, o el modelo expresa baja confianza), registra la pregunta como «sin cobertura documental» y la envía a RRHH para que cree o actualice el artículo. _Por qué no es regla_: si el agente simplemente responde «no encontré», no hay aprendizaje. El modelo evalúa si la pregunta es recurrente (comparando con historial) para priorizar la actualización de docs.

3. **Adaptación del contenido al perfil** — el mismo bloque de documentación se presenta de forma diferente para un senior vs un junior. _Por qué no es regla_: qué simplificar, qué expandir, y qué asumir ya conocido depende del contexto del perfil y de la pregunta puntual.

> [!nota]
> El agente de onboarding es el único caso F de esta sección donde el «usuario final» no es RRHH sino el nuevo empleado. Eso implica que el tono y las respuestas deben ser más orientados a guía que a análisis. El system prompt del tenant lo declara explícito.

---

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[setup_employee] → crea checklist + asigna recursos (determinístico)
  ↓
[index_docs] → (re-)indexa docs del tenant si hay cambios (determinístico)
  ↓
[onboarding_chat] ← loop: pregunta del empleado
    [retrieve] → RAG sobre doc del tenant (determinístico: vector search)
    [answer]   → responde con nivel adaptado (agéntico)
    [gap_check] → ¿la respuesta fue satisfactoria? (agéntico)
        si gap → [flag_gap] → HR notificada (tool: send_email)
  ↓
[track_progress] → actualiza checklist (determinístico)
  ↓
[day30_check?] → interrupt_before a los 30 días: reporte al manager
  ↓
[write_report] → resumen 30/60/90 días (tool: write_report)
  ↓
END
```

### Activities Temporal

- `setup_onboarding(tenant, employee_id)` — crea checklist y accesos; idempotente.
- `reindex_docs(tenant)` — re-indexa la doc cada vez que hay commit a Notion/Drive; scheduled diario.
- `generate_progress_report(tenant, employee_id, day)` — genera reporte en días 30, 60, 90.

### Tools necesarias

- `sql_query` — checklist de tareas del tenant, historial de preguntas frecuentes.
- `fetch_excel` — si el tenant mantiene la doc en Sheets.
- `send_email` — notificación de gap al equipo de RRHH; reporte al manager.
- `write_report` — reporte de progreso 30/60/90.

---

## 8. Salida y entrega

**Experiencia del nuevo empleado**: un panel de chat en la intranet o en Slack con el agente de onboarding. El empleado pregunta en lenguaje natural; el agente responde con la documentación relevante y el tono apropiado al nivel.

**Reporte de progreso (día 30)** para el manager:

```
## Onboarding — [EMP-2026-041] · Consultora ABC · Día 30

Checklist: 24/30 ítems completados (80%).
Ítems pendientes: acceso a repositorio de propuestas (bloqueado TI), formación GDPR.

Temas más preguntados:
1. Proceso de timesheet (8 preguntas) → doc actualizada el 2026-05-22.
2. Protocolo de propuesta comercial (6 preguntas) → gap detectado, HR notificada el 2026-05-24.
3. Estructura de fees por proyecto (5 preguntas) → respondido con doc "fee_structure_v3.md".

Recomendación: agendar reunión con mentor para cubrir protocolo de propuesta (gap en doc).

⚠ Este reporte lo genera el sistema. La evaluación de desempeño la hace el manager.
```

---

## 9. Cómo se vende

**Gancho**: «El nuevo empleado pregunta lo mismo que preguntó el anterior. En vez de que RRHH responda por WhatsApp, el agente responde en 3 segundos y aprende qué documentación falta».

**Propuesta de valor**: reducción del tiempo hasta productividad (de 4–6 semanas a 1–2), liberación de 3–5 horas/semana de RRHH en preguntas repetidas, mejora de la experiencia del nuevo empleado.

| Tier | Condiciones | Precio |
|------|-------------|--------|
| Starter | ≤ 10 incorporaciones/año, doc en Notion/Drive | 200–400 USD/mes |
| Growth | ≤ 50 incorporaciones/año + integración HRIS | 500–1000 USD/mes |
| Setup | Indexado inicial de doc + calibración de roles | 1000–3000 USD |

---

## 10. Riesgos

**1. Doc interna desactualizada.**
*Síntoma*: el agente responde con el proceso anterior a una actualización que RRHH no subió al índice.
*Mitigación*: el reindex corre automáticamente al detectar cambios en el Drive/Notion del tenant (webhook). Cada respuesta incluye la fecha del documento fuente («según el manual actualizado el 2026-03-15»). Si la fecha es > 90 días, el agente advierte.

**2. Filtración de información confidencial.**
*Síntoma*: un empleado de nivel junior pregunta sobre la estructura de fees de un cliente y el agente responde con datos de un documento que solo debería ver un senior.
*Mitigación*: cada documento se etiqueta con `access_level: [junior | senior | manager | confidential]` al indexar; el retriever filtra por el nivel del perfil antes de devolver fragmentos.

**3. Alucinación sobre procesos internos.**
*Síntoma*: el agente inventa un proceso de aprobación que no existe en la documentación del tenant.
*Mitigación*: el prompt exige que el agente cite el documento fuente (nombre + sección); si no encuentra fuente, responde «no tengo documentación sobre esto; contacta a RRHH». El harness verifica que la respuesta contenga al menos 1 citación antes de enviarla.

**4. PII del nuevo empleado en logs.**
*Síntoma*: los logs del chat contienen el nombre, cargo y preguntas del empleado sin cifrar.
*Mitigación*: los logs del chat se guardan con `employee_id` (no nombre); solo RRHH con permisos explícitos puede resolver el ID al nombre real. Ley 1581 (Colombia) y LGPD (Brasil) exigen propósito declarado para el procesamiento.

---

## 11. Variantes por industria

### Instancia 1 — Servicios profesionales (`consultorabc`)

**Datos típicos**: 5–20 incorporaciones/año; docs en Notion o Confluence; el gap de conocimiento más crítico es metodológico (cómo se estructura un proyecto, cómo se comunica con el cliente).

**Delta determinístico**: checklist diferenciado por nivel (junior: tools + procesos; senior: clientes actuales, estructura de fees, red de contactos internos).

**Delta agéntico**: para un senior que viene de otra industria, el agente detecta las preguntas que revelan desconocimiento del contexto del cliente objetivo y sugiere proactivamente documentos de contexto («parece que no tienes acceso al deck de industria bancaria; ¿quieres que te lo busque?»).

**Regulación**: si el tenant maneja información de clientes en los docs (propuestas, contratos), el indexado debe excluir documentos marcados como confidenciales del cliente. NDA del empleado cubre esto, pero el sistema añade una capa técnica.

**Precio orientativo**: 200–400 USD/mes.

### Instancia 2 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 20–60 incorporaciones/año (alta rotación en temporadas); roles operativos (bodega, atención al cliente, cajero); docs simples (1–2 páginas por proceso); la mayoría de preguntas son operativas («¿cómo proceso una devolución?»).

**Delta determinístico**: checklist simplificado con video + imagen por tarea (el nuevo empleado de bodega prefiere ver el proceso, no leerlo). El sistema dispara el primer mensaje del agente vía WhatsApp Business, no por un portal interno.

**Delta agéntico**: al día 7, si el empleado no ha completado los ítems de seguridad del checklist, el agente manda un recordatorio personalizado («Hola, aún tienes pendiente el módulo de manejo de efectivo; ¿quieres que te lo explique ahora?»). Si responde con duda real, el agente la resuelve; si está bloqueado por un jefe que no ha dado acceso, lo escala a RRHH.

**Regulación**: en retail con empleados de jornada parcial y contratos por temporada, el onboarding debe documentar que el empleado recibió la información de seguridad (OSHA/HSE local). El sistema genera un log firmado digitalmente.

**Precio orientativo**: 300–600 USD/mes (volumen mayor, integración WhatsApp).

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de él |
|--------|-----------------|
| **B02** — FastAPI routing | El endpoint `POST /onboarding/{employee_id}/chat` recibe el mensaje del empleado y dispara el nodo `answer`; el `Depends(get_tenant)` asegura que el RAG solo accede a docs del tenant correcto. |
| **B03** — Jinja2 + HTMX | El panel de chat del nuevo empleado usa HTMX SSE para streaming de la respuesta; el template `onboarding_chat.html` muestra el checklist al lado del chat. |
| **E01** — Anthropic SDK | El nodo `answer` usa `cache_control: ttl:"1h"` sobre el system prompt con el perfil del empleado (estático por sesión); los fragmentos RAG van sin cache (dinámicos por pregunta). |
| **E03** — Skills por tenant | El tono, el glosario interno (siglas, nombres de proyectos) y los roles permitidos se inyectan como skill por tenant; el mismo agente funciona para Consultora ABC y TiendaBox sin cambiar código. |
| **E04** — Memoria de sesión | El historial del chat de onboarding se persiste por `employee_id`; el agente recuerda qué preguntas hizo ayer para no re-explicar lo mismo. |
| **D04** — Observabilidad | Cada sesión de chat de onboarding genera spans en Phoenix: latencia de respuesta, tokens consumidos, y tasa de gaps detectados (preguntas sin cobertura documental). Si el gap rate supera el 20%, el pipeline alerta a RRHH para actualizar la documentación. El cost ledger por tenant acumula el costo de las sesiones de onboarding. |

## 13. Errores típicos

**1. Documentación desactualizada indexada sin advertencia.**
*Síntoma*: el nuevo empleado recibe el proceso de aprobación de gastos que cambió hace 4 meses; hace el proceso incorrecto y genera un problema operativo.
*Causa raíz*: el reindex automático no detectó que el documento había cambiado porque el webhook de Drive/Notion no estaba configurado correctamente.
*Cómo evitarlo*: cada respuesta del agente incluye la fecha del documento fuente; si la fecha es > 90 días, el agente advierte explícitamente. Validar el webhook en el setup y monitorear que el reindex diario corra sin errores.

**2. Filtración de documentación confidencial a un nivel sin acceso.**
*Síntoma*: un empleado junior pregunta sobre la estructura de fees de un cliente y el agente responde con datos de un documento marcado `access_level: manager`.
*Causa raíz*: el filtro de `access_level` en el retriever RAG no estaba aplicado correctamente al hacer el vector search.
*Cómo evitarlo*: el filtro de nivel de acceso debe aplicarse antes de devolver fragmentos, no después; test en CI que verifica que un perfil junior no puede recuperar documentos confidenciales aunque estén en el mismo índice.

**3. Alucinación de procesos internos sin fuente documental.**
*Síntoma*: el agente describe un proceso de aprobación de proyectos que no existe en ningún documento del tenant; el nuevo empleado lo aplica y genera confusión.
*Causa raíz*: el prompt no exige citación de fuente; cuando el RAG no encuentra fragmentos relevantes, el modelo genera una respuesta plausible en lugar de admitir que no tiene información.
*Cómo evitarlo*: el prompt exige citar el documento fuente (nombre + sección) en cada respuesta; si no hay fuente, la respuesta obligatoria es «No tengo documentación sobre esto; contacta a RRHH». El harness valida que la respuesta contenga al menos una citación antes de enviarla.

**4. Inferencia de atributos del empleado a partir de preguntas.**
*Síntoma*: el historial del chat revela, por el tipo de preguntas, que el empleado tiene dificultades con ciertos procesos, y ese dato llega al manager sin el consentimiento del empleado.
*Causa raíz*: el reporte de progreso incluye el detalle de preguntas individuales sin proceso de anonimización.
*Cómo evitarlo*: el reporte al manager muestra solo los temas más preguntados (agregados), no las preguntas individuales; los logs del chat se guardan con `employee_id` y solo RRHH con permisos puede resolver el ID al nombre real.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «¿Cuál es la diferencia entre el nodo `retrieve` (determinístico) y el nodo `answer` (agéntico) en el flujo del chat de onboarding? ¿Por qué la búsqueda vectorial es determinística si también usa un modelo?»
2. **Aplícalo a mi caso**: «¿Cómo adaptaría el sistema si el tenant tiene documentación en tres idiomas distintos (español, inglés y portugués) y los nuevos empleados pueden preguntar en cualquiera de los tres?»
3. **Por qué falló**: «El agente respondió con información de un proceso que fue actualizado hace dos semanas, aunque el reindex debería haber corrido. ¿Cómo lo diagnostico en la traza?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de onboarding con generación de checklist personalizado por rol, indexado de documentación y chat con RAG adaptado al nivel del perfil.
- Separar los tramos determinísticos (generación de checklist, indexado, filtro de acceso) de los agénticos (respuesta adaptada, detección de gaps en doc).
- Implementar el filtro de `access_level` en el retriever antes de devolver fragmentos al modelo.
- Configurar el sistema para que los logs del chat usen `employee_id` y nunca incluyan PII en sistemas externos.
- Dimensionar y cotizar este servicio para una consultora de servicios profesionales y para retail con alta rotación.

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|--------------------------------|
| **C02** — Multitenancy y RLS | La documentación interna de cada empresa es confidencial y no debe ser accesible desde otro tenant; el RAG debe filtrar por `tenant_id` antes del vector search. |
| **E04** — Memoria de sesión | El historial del chat de onboarding se persiste por `employee_id`; sin entender la gestión de sesión del SDK, el agente re-explica lo mismo en cada conversación. |
| **B03** — Jinja2 + HTMX | El panel de chat usa HTMX SSE para streaming; entender el template de frontend es necesario para el contexto completo de la experiencia del nuevo empleado. |
| **E03** — Skills por tenant | El tono, el glosario interno y los roles permitidos se inyectan como skill por tenant; sin este módulo no se entiende por qué el mismo agente funciona para Consultora ABC y TiendaBox. |
