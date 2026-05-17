---
ext_id: F-PRD-03
slug: specs-desde-tickets
track: F
dept: PRD
ord: 282
title: "Generación de specs desde tickets de soporte"
summary: "Agente que agrupa tickets de soporte relacionados, sintetiza la necesidad subyacente, y produce un borrador de spec con user story, acceptance criteria y edge cases que el equipo de ingeniería puede ejecutar."
estimated_minutes: 30
industries_instanced: [retail, serv-prof]
tenants_in_examples: [tiendabox, consultorabc]
---

## 1. Problema operativo

La PM de TiendaBox Retail recibe cada semana una lista de tickets de soporte que, técnicamente, no son bugs: son solicitudes de feature o limitaciones del producto que los usuarios fueron a soporte porque no encontraron cómo hacerlo. El problema: esos tickets viven en Intercom, no en Linear. Nadie los convierte en issues ejecutables. Nadie sabe qué necesita ingeniería para construirlo.

Consultora ABC tiene el problema inverso: tiene los tickets en Linear, pero los escribió el cliente en lenguaje de usuario ("necesito que el sistema me deje exportar más cosas"). Ingeniería no sabe qué construir. El PM pasa 2–3 horas por sprint escribiendo specs que, a veces, todavía están incompletas cuando llegan al dev.

El agente produce el primer borrador. El PM lo cierra. Ingeniería lo ejecuta.

---

## 2. Hoy en big corps

Los equipos de producto con más de 5 PMs usan herramientas de AI product management que generan specs directamente desde señales de usuario.

| Vendor | Capacidad | Precio orientativo |
|--------|-----------|-------------------|
| **Productboard Spark** (2026) | Agente que genera PRDs completos, conecta con Amplitude y Linear vía MCP; también agrupa ideas de feedback para generar specs | 25–100 USD/usuario/mes |
| **Aha! AI** | Generación de user stories desde ideas de feedback; integración directa con Jira | 59–149 USD/usuario/mes |
| **Linear AI** | Sugerencia de issues relacionados, borrador de descripción de feature, sub-issues automáticos | Linear Pro: 8 USD/usuario/mes |
| **GitHub Copilot Workspace** | Genera issue → plan → código; pensado para devs, no para PMs | 19 USD/usuario/mes |

Ninguna de estas herramientas habla "ticket de soporte de Intercom" de forma nativa. Las integraciones existen pero requieren configuración y un PM que sepa usarlas. La PYME no tiene ese PM.

---

## 3. PYME LATAM realista

TiendaBox y Consultora ABC trabajan con:
- **Intercom** (Starter): soporte al cliente, conversaciones por chat.
- **Linear** (Starter / Pro): tracker de issues de ingeniería.
- **Notion**: espacio donde a veces existen specs de features, a veces no.
- **Google Docs / Drive**: donde van a parar los documentos de producto que nadie encuentra después.
- El proceso de convertir ticket → spec es un proceso artesanal, inconsistente, y dependiente de que la PM tenga tiempo.

El ERP no juega aquí. El gap es entre el canal de soporte y el tracker de ingeniería.

---

## 4. Datos típicos

| Atributo | Detalle |
|----------|---------|
| Input | Tickets de Intercom (o Linear) agrupados por tema (output de F-PRD-01) o seleccionados manualmente por el PM |
| Formato | JSON con `raw_text`, `user_segment`, `date`, `channel`, `tenant_id` |
| Volumen por spec | 3–20 tickets por feature (pocos tickets → spec pequeña; muchos → feature compleja) |
| Output | Documento Markdown con frontmatter: `user_story`, `acceptance_criteria`, `edge_cases`, `dependencies`, `open_questions` |
| Destino | Linear issue (descripción), Notion page, o Google Doc |

Ejemplo de tickets de entrada:
```
T-1201: "No puedo descargar mi historial de pedidos como Excel"
T-1187: "¿Hay forma de exportar los pedidos del mes pasado?"
T-1203: "Necesito enviar el reporte de ventas a mi contador pero no puedo"
T-1199: "El PDF de pedidos no tiene los datos del cliente, solo el número"
```

---

## 5. Tramos determinísticos

1. **Agrupación de tickets relacionados**: los tickets de input ya vienen agrupados por cluster temático (salida de F-PRD-01) o se agrupan por keyword/tema en este paso. Resultado: un conjunto de tickets que todos hablan del mismo problema subyacente.
2. **Extracción de metadatos del grupo**: cuántos tickets, qué segmentos de usuario están representados, rango de fechas, canal de origen. Estos metadatos van al frontmatter de la spec.
3. **Plantilla de spec**: estructura fija con secciones: `user_story`, `acceptance_criteria` (lista numerada), `edge_cases` (lista), `dependencies` (lista de módulos/servicios afectados), `open_questions` (lo que el PM necesita decidir antes de que ingeniería arranque).
4. **Renderizado de la spec final**: una vez el LLM genera el contenido, el template Jinja2 produce el Markdown final con formato consistente para Linear o Notion.

---

## 6. Tramos agénticos

1. **Síntesis de la necesidad subyacente** — los tickets dicen cosas distintas pero tienen una necesidad común: poder exportar datos de pedidos en formatos útiles (Excel, PDF con campos completos) para uso externo (contador, cliente). El modelo identifica esa necesidad subyacente, que no es igual a ninguno de los tickets individuales.

   *Por qué no es regla*: la necesidad subyacente requiere abstracción. "No puedo descargar en Excel" + "el PDF no tiene datos del cliente" no suman a "exportar en Excel" — suman a "capacidades de exportación de pedidos para uso externo", que es una feature más amplia. La abstracción correcta depende de leer el conjunto, no de reglas sobre palabras.

2. **Redacción de user story y acceptance criteria** — "Como vendedor del marketplace, quiero exportar mi historial de pedidos en Excel con los datos del cliente incluidos, para poder enviarlos a mi contador mensualmente. Criteria: (1) El botón 'Exportar' está disponible en la sección Pedidos. (2) El Excel incluye: número de pedido, fecha, cliente nombre+email, monto, estado. (3) Se puede filtrar por rango de fechas antes de exportar. (4) El archivo descarga en < 3 segundos para hasta 1000 pedidos."

   *Por qué no es regla*: la user story requiere inferir el contexto del usuario (vendedor del marketplace, no comprador) y el caso de uso real (enviar al contador) desde los tickets, que no lo dicen explícitamente. Los acceptance criteria requieren decidir qué campos incluir, qué rendimiento es aceptable, qué filtros son necesarios — decisiones que no están en los tickets.

3. **Identificación de edge cases** — el modelo piensa activamente en los bordes del problema: ¿qué pasa si hay 50 000 pedidos en el rango seleccionado? ¿qué pasa con pedidos cancelados — ¿se incluyen o no? ¿qué pasa si el tenant tiene múltiples catálogos y quiere exportar solo uno?

   *Por qué no es regla*: los edge cases son los casos que los usuarios no reportaron porque no llegaron a ellos. Anticiparlos requiere razonamiento sobre el sistema, no sobre los tickets.

4. **Open questions para el PM** — el modelo identifica explícitamente qué decisiones no puede tomar y las lista: "¿Se incluyen pedidos cancelados en el export? ¿Cuál es el límite de filas aceptable antes de ofrecer paginación? ¿Necesita formato específico para el SAT (México) o DIAN (Colombia)?".

4. **Fallback humano**: el output siempre es un borrador marcado como `status: draft — requires PM review`. El PM lo aprueba, edita, y convierte en el issue final. El agente nunca crea un issue en estado `ready for dev` sin aprobación humana.

---

## 7. Blueprint del workflow

```
[INPUT: ticket cluster OR manual selection]
  lista de tickets relacionados (3–20 items)
      |
[GROUP_METADATA]             (determinístico)
  contar, segmentar, fechar
      |
[SYNTHESIZE_NEED]            ← agéntico
  LLM: (tickets_texts, tenant_context)
  → need_statement: "Los vendedores necesitan exportar pedidos para uso externo"
      |
[DRAFT_USER_STORY]           ← agéntico
  LLM: (need_statement, user_segment, tenant_context)
  → user_story: "Como X, quiero Y, para Z"
      |
[DRAFT_ACCEPTANCE_CRITERIA]  ← agéntico
  LLM: (user_story, ticket_samples, tenant_tech_context)
  → acceptance_criteria: lista numerada, testeable
      |
[IDENTIFY_EDGE_CASES]        ← agéntico
  LLM: (user_story, acceptance_criteria, system_context)
  → edge_cases: lista de scenarios límite
      |
[LIST_OPEN_QUESTIONS]        ← agéntico
  LLM: (full spec draft)
  → open_questions: decisiones que el PM debe cerrar
      |
[RENDER_SPEC]                (determinístico — template Jinja2)
  → spec.md con frontmatter
      |
[DELIVER: draft]
  → Linear issue (status: draft) OR Notion page OR Google Doc
  → notificación al PM: "Spec lista para revisión"
```

---

## 8. Salida y entrega

**Spec generada** (Linear issue o Notion page):

```markdown
---
status: draft
ticket_cluster: exportar-pedidos
source_tickets: [T-1187, T-1199, T-1201, T-1203]
user_segments: [vendedor_marketplace]
created_by: agent-prd-specs
requires_pm_review: true
---

# Exportación de historial de pedidos (Excel + PDF mejorado)

## User Story
Como vendedor del marketplace en TiendaBox, quiero exportar mi historial de pedidos
en formato Excel con los datos completos del cliente, para poder compartirlo con mi
contador y llevar control de mis ventas fuera de la plataforma.

## Acceptance Criteria
1. El botón "Exportar" está visible en la sección Pedidos (desktop y web móvil).
2. El usuario puede filtrar por rango de fechas antes de exportar (mínimo: mes actual, mes anterior, rango personalizado).
3. El archivo Excel (.xlsx) incluye las columnas: Número de pedido, Fecha, Cliente (nombre + email), Producto(s), Monto total, Estado del pedido.
4. El PDF de pedido individual incluye todos los campos del Excel más la dirección de envío.
5. La descarga inicia en < 3 segundos para rangos de hasta 1 000 pedidos.
6. Para rangos con > 1 000 pedidos, el sistema envía el archivo por email al completarse.

## Edge Cases
- [ ] Pedidos cancelados: ¿se incluyen en el export? (decisión PM)
- [ ] Pedidos con múltiples ítems: cada ítem en fila separada o columnas dinámicas
- [ ] Tenant con múltiples catálogos: ¿filtrar por catálogo antes de exportar?
- [ ] Usuario sin pedidos en el rango seleccionado: mensaje vacío o error graceful

## Dependencies
- Módulo de Pedidos (backend): añadir endpoint `GET /orders/export`
- Servicio de generación de XLSX (nueva librería: openpyxl o xlsxwriter)
- Cola de jobs para exports grandes (si > 1 000 pedidos)

## Open Questions (PM debe responder antes de dev)
1. ¿Se incluyen pedidos cancelados?
2. ¿El email de notificación para exports grandes usa el correo del tenant o el del usuario?
3. ¿Se necesita formato fiscal específico (DIAN para Colombia, SAT para México)?

## Source Tickets
T-1187, T-1199, T-1201, T-1203 (ver Intercom)
```

---

## 9. Cómo se vende

**Gancho**: "Tu PM gasta 2–3 horas por sprint escribiendo specs desde tickets. Este agente genera el borrador en 2 minutos. El PM edita y aprueba en 20 minutos."

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Starter | 5 specs/mes, 2 fuentes, entrega por email | 100–200 USD/mes |
| Profesional | 20 specs/mes, integración Linear/Notion, sugerencia de dependencias | 300–600 USD/mes |
| SaaS LATAM | Ilimitado, multi-tenant, personalización de template por tenant | 500–1 000 USD/mes |

Setup (configuración de contexto del sistema del tenant, template de spec, calibración con 3 specs del PM como golden set): 500–1 000 USD una vez.

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Acceptance criteria no testeables** (el modelo escribe criterios ambiguos) | Ingeniería no sabe cuándo la feature está lista | El PM revisa y reformula los criteria antes de aprobar. El agente sugiere; no es el entregable final. Golden set de specs aprobadas para calibrar. |
| **El modelo infiere necesidades que no están en los tickets** (alucinación de feature) | Se construye algo que los usuarios no pidieron | Cada claim del modelo en la spec referencia el(los) ticket(s) de origen. Si una acceptance criteria no tiene fuente en los tickets, el modelo la marca como `[inferido — confirmar con usuario]`. |
| **Contexto técnico insuficiente** (el modelo no sabe qué es posible en el stack del tenant) | Dependencies y effort estimados incorrectamente | El tenant puede cargar un documento de "arquitectura del sistema" como contexto del agente. Sin ese contexto, la spec omite la sección de Dependencies y la marca como `[pendiente de análisis técnico]`. |
| **El borrador se entrega a ingeniería sin revisión del PM** | Ingeniería construye algo mal especificado | El issue siempre nace en estado `draft`; el sistema bloquea moverlo a `ready for dev` sin al menos una edición del PM (campo `pm_reviewed: true` que solo el PM puede setear). |

---

## 11. Variantes por industria

| Delta | Retail / E-commerce (TiendaBox) | Servicios profesionales (Consultora ABC) |
|-------|--------------------------------|------------------------------------------|
| Tipo de feature pedida | UX de la app móvil, exportaciones, notificaciones | Reportes personalizados, integraciones con herramientas del cliente, flows de aprobación |
| Usuario que pide | Vendedor del marketplace, comprador | Director de proyecto del cliente, usuario del sistema interno |
| Contexto técnico relevante | App React Native + API REST + base multi-tenant | Web app + integraciones con ERP del cliente (Siigo, World Office) |
| Edge cases más frecuentes | Multi-idioma, multi-moneda, regulación fiscal DIAN/SAT | Multi-cliente (cada cliente tiene config diferente), SLA de disponibilidad |
| Acceptance criteria típicos | UX (tiempo de carga, estados vacíos, mensajes de error) | Funcionales (qué cálculo, qué datos, qué formato) + non-functional (tiempo de generación del reporte) |
| Tiempo de calibración inicial | 3–4 specs del PM como golden set | 3–4 specs del PM como golden set; más contexto técnico de integraciones |
| Precio tier profesional | 400–600 USD/mes | 300–500 USD/mes |

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica |
|--------|-----------|
| **E01** — Anthropic SDK tool loop | El modelo llama a `get_ticket_details(ticket_id)` para leer el texto completo de tickets individuales antes de draftar la spec, en lugar de recibir todos en el contexto de una vez. |
| **E03** — Skills AGENTS.md | Skill `spec_writer` con slots por tenant: `{system_context_doc}` (arquitectura del sistema), `{spec_template}` (formato preferido del PM), `{output_destination}` (Linear o Notion). |
| **B02** — FastAPI routers y deps | Endpoint `POST /specs/generate` que recibe `{ticket_ids, tenant_id}` y retorna `task_id`; `GET /specs/{task_id}` para el resultado. |
| **D04** — Observabilidad Phoenix | Span por sección de spec generada; métricas de `pm_acceptance_rate` (qué porcentaje de specs se aprueba sin edición mayor) para detectar drift del modelo. |

---

## 13. Errores típicos

**1. Acceptance criteria no testeables por lenguaje ambiguo.**
*Síntoma*: el criterio dice «el sistema debe ser rápido al exportar» — ingeniería no sabe qué medir para considerar la feature lista.
*Causa raíz*: el nodo `DRAFT_ACCEPTANCE_CRITERIA` generó criterios en lenguaje natural sin anclas numéricas.
*Cómo evitarlo*: el system prompt del nodo exige que cada criterio de performance incluya una métrica concreta: tiempo, volumen de filas, tamaño de archivo. Si el modelo no puede inferirlo de los tickets, marca el criterio como `[NÚMERO PENDIENTE — PM debe definir antes de dev]`. Un criterio ambiguo en el borrador es mejor que uno falso.

**2. Spec creada con acceptance criteria que no tienen fuente en los tickets.**
*Síntoma*: la spec incluye «el sistema debe integrarse con el SAT de México» pero ningún ticket lo mencionó; el PM lo aprueba asumiendo que alguien lo pidió.
*Causa raíz*: el nodo `DRAFT_ACCEPTANCE_CRITERIA` infirió requisitos regulatorios que no estaban en los tickets de entrada.
*Cómo evitarlo*: cada criterio en el borrador referencia el ticket de origen entre paréntesis. Si un criterio es `[inferido]`, se marca explícitamente y el PM debe confirmarlo antes de moverlo a `ready for dev`. El agente no puede aprobar sus propias inferencias.

**3. Spec enviada a ingeniería en estado `draft` sin revisión del PM.**
*Síntoma*: el dev recibe una spec en Linear con status `draft` y empieza a trabajar en ella porque el título parece claro; la spec tiene open questions sin resolver que afectan el diseño.
*Causa raíz*: el proceso de entrega no bloquea a ingeniería de ver las specs en estado `draft`.
*Cómo evitarlo*: el issue en Linear nace con label `blocked: awaiting-pm-review` y no puede moverse a `ready for dev` sin que el campo `pm_reviewed: true` esté seteado. Ingeniería ve el issue pero no puede arrastrarlo al sprint hasta que el PM lo apruebe.

**4. Contexto técnico ausente produce dependencias incorrectas.**
*Síntoma*: la spec propone «usar una nueva librería de generación de PDF» cuando el tenant ya tiene una implementada; ingeniería pierde tiempo evaluando una opción innecesaria.
*Causa raíz*: el nodo no tiene acceso al documento de arquitectura del tenant.
*Cómo evitarlo*: si el slot `system_context_doc` del skill no está cargado, la sección `Dependencies` de la spec se omite y se marca `[pendiente de análisis técnico — cargar arquitectura del sistema en el skill]`. Una spec sin sección de dependencias es preferible a una con dependencias inventadas.

**5. Open questions sin resolver bloquean el sprint.**
*Síntoma*: la spec llega a ingeniería con 4 open questions; el PM no las resolvió porque no las vio; el dev tiene que interrumpir al PM durante el sprint para obtener respuesta.
*Causa raíz*: el flujo de entrega no obliga al PM a responder las open questions antes de aprobar la spec.
*Cómo evitarlo*: el issue no puede cambiar de `draft` a `ready for dev` con open questions sin responder. El sistema lista las open questions pendientes como checklist en el issue de Linear. El PM debe marcar cada una como resuelta (con la respuesta en el comentario) antes de aprobar.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre la síntesis de necesidad subyacente (agéntico) y la agrupación de tickets relacionados (determinístico) con el ejemplo de TiendaBox — ¿por qué no basta con juntar los tickets sin sintetizar?»
2. **Aplícalo a mi caso**: «Mi cliente tiene tickets que mezclan requests de múltiples clientes distintos en el mismo tracker. ¿Cómo configuro el agente para que la spec refleje solo los tickets del cliente para el que es relevante?»
3. **Por qué falló**: «El agente generó una spec con un acceptance criteria que menciona integración con el SAT de México, pero ningún ticket lo pedía. ¿Cómo configuro el nodo para que marque esos criterios inferidos de forma visible?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Construir el pipeline de síntesis de necesidad subyacente desde un cluster de tickets con el nodo agéntico `SYNTHESIZE_NEED`.
- Generar user stories, acceptance criteria testeables, edge cases y open questions como secciones estructuradas en Markdown con Jinja2.
- Configurar el flujo de aprobación que bloquea a ingeniería hasta que el PM resuelva las open questions y apruebe la spec.
- Integrar el skill `spec_writer` con `system_context_doc` del tenant para que las dependencias propuestas sean coherentes con el stack real.
- Cotizar y dimensionar el servicio para retail y servicios profesionales LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué leerlo antes |
|--------|---------------------|
| **E01** — Anthropic SDK tool loop | El modelo llama a `get_ticket_details(ticket_id)` para leer cada ticket individualmente antes de sintetizar; E01 enseña ese patrón de tool use con acumulación de contexto progresivo. |
| **E03** — Skills por tenant | El skill `spec_writer` con slots `system_context_doc`, `spec_template` y `output_destination` es el patrón directo de E03; sin entender skills por tenant el agente produce specs genéricas. |
| **B02** — FastAPI routers | El endpoint `POST /specs/generate` con `task_id` y el polling `GET /specs/{task_id}` son patrones de B02 para jobs asíncronos de duración variable. |
| **D04** — Observabilidad | La métrica `pm_acceptance_rate` (porcentaje de specs aprobadas sin edición mayor) es el indicador de calidad del skill; sin D04 el drift del modelo es invisible. |
