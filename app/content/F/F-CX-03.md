---
ext_id: F-CX-03
slug: kb-mantenimiento
track: F
dept: CX
ord: 242
title: "Generación y mantenimiento de base de conocimiento"
summary: "Pipeline que detecta brechas en la KB analizando tickets sin respuesta en la base existente, redacta borradores de artículo a partir de tickets resueltos, y detecta artículos desactualizados."
related_modules: [B02, C01, E01, E03]
industries_instanced: [retail, hospitalidad]
tenants_in_examples: [tiendabox, mesonurbano]
big_corp_vendors: [Zendesk Guide, Confluence, Notion AI]
latam_tools: [notion, confluence-cloud, freshdesk-kb]
key_concepts: [gap-detection, deflection-rate, versionado, ownership, fallback-humano]
estimated_minutes: 45
deterministic_share: 0.4
version: 1
---

## 1. Problema operativo

El equipo de CX de **TiendaBox** responde la misma pregunta 30 veces al mes: «¿Cómo devuelvo un producto?». Tienen 3 artículos en la KB sobre devoluciones, pero están desactualizados (la política cambió en enero y nadie actualizó la KB) y están escritos en lenguaje técnico que el cliente no entiende. El 35% de los tickets entrantes podrían resolverse con la KB si estuviera completa y actualizada. Hoy, el jefe de CX sabe que la KB está mal pero no tiene tiempo de revisarla — y el equipo tampoco sabe cuáles artículos son los más urgentes de actualizar.

---

## 2. Hoy en big corps

| Vendor | Qué hace | Precio orientativo |
|--------|----------|--------------------|
| **Zendesk Guide** | KB integrada con el helpdesk; análisis de búsquedas fallidas; sugerencia de artículo al agente | Incluido en Suite; análisis avanzado en Suite Professional (115 USD/agente/mes) |
| **Confluence (Atlassian)** | Wiki corporativo con Atlassian Intelligence para sugerir y mejorar contenido | 5–10 USD/usuario/mes; impl. y mantenimiento significativos |
| **Notion AI** | KB flexible con IA para redactar y mejorar artículos | 8–10 USD/usuario/mes + AI add-on 8–10 USD/usuario/mes |

Las grandes empresas tienen equipos de «knowledge management» dedicados a mantener la KB actualizada. Una PYME no tiene ese rol.

---

## 3. PYME LATAM realista

**TiendaBox** (e-commerce) y **Mesón Urbano** (hospitalidad) operan con:

- **Freshdesk** con el módulo de KB básico, o una carpeta en Google Drive, o una sección de Notion sin estructura.
- La KB la «mantiene» alguien de CX cuando tiene tiempo, que es casi nunca.
- No hay métricas de deflection (cuántos tickets se evitaron por la KB).
- Los artículos nuevos se crean cuando hay una crisis, no de forma proactiva.
- Cero proceso de revisión: un artículo publicado en 2023 sigue activo aunque el proceso cambió.

---

## 4. Datos típicos

| Campo | Formato | Fuente | Frecuencia | Volumen |
|-------|---------|--------|------------|---------|
| Tickets resueltos | JSON (texto del ticket, respuesta del agente, categoría, resolución) | Helpdesk API | Continuo | 50–500/día |
| Artículos KB existentes | Markdown / HTML | Freshdesk/Notion API | Actualización continua | 10–200 artículos |
| Búsquedas fallidas en KB | JSON (query, fecha, resultado vacío) | Helpdesk search logs | Diario | 20–200/día |
| Métricas de artículo | JSON (views, thumbs_up, thumbs_down, tickets_deflected) | Helpdesk API | Diario | 1 fila/artículo |

**Ejemplo de ticket resuelto**:

```json
{
  "ticket_id": "TB-29850",
  "text": "Compré unas zapatillas talla 40 pero me quedaron grandes. ¿Las puedo cambiar por la 39?",
  "agent_response": "Claro, puedes solicitar el cambio dentro de los 30 días de recibido. Ve a tu pedido en la app, selecciona 'Solicitar cambio' y elige la talla. Llega en 5-7 días hábiles.",
  "category": "returns_exchange",
  "resolution": "resolved",
  "kb_article_used": null,
  "created_at": "2026-04-15T14:23:00Z"
}
```

---

## 5. Tramos determinísticos

1. **Detección de tickets sin KB match** — para cada ticket entrante, el sistema busca en la KB usando similitud coseno (vector search). Si ningún artículo supera el umbral de similitud (configurable, default: 0.75), el ticket se marca como «sin cobertura KB». Determinístico dado el umbral y el modelo de embedding.
2. **Agrupación de tickets sin cobertura por tema** — tickets marcados como «sin cobertura» se agrupan por similaridad semántica (clustering: HDBSCAN o K-means sobre embeddings). Determinístico con semilla fija.
3. **Detección de artículos desactualizados** — artículos cuyo `last_updated` es > N días (configurable por tenant) Y cuyo `thumbs_down_rate > umbral` O cuyo `related_ticket_rate` (tickets sobre ese tema que llegaron igual después de leer el artículo) aumentó en los últimos 30 días. Determinístico.
4. **Métricas de deflection** — `tickets_deflected = tickets donde el cliente leyó el artículo KB y no abrió ticket en las siguientes 24h`. Cálculo determinístico con los logs del helpdesk.
5. **Reindexado del vector store** — cuando se publica o actualiza un artículo, el pipeline lo re-embeda e inserta en el vector store. Determinístico.

---

## 6. Tramos agénticos

1. **Decisión: crear artículo nuevo vs. ampliar uno existente** — para un grupo de tickets sin cobertura, el modelo analiza si existe un artículo relacionado que podría ampliarse o si se necesita uno nuevo. _Por qué no es regla_: la decisión depende del grado de solapamiento semántico y del alcance del artículo existente — no es un threshold numérico; dos artículos sobre «devoluciones» pueden ser tan distintos que fusionarlos empeora ambos.

2. **Redacción del borrador de artículo** — el modelo redacta un artículo a partir de 3–8 tickets resueltos sobre el mismo tema, usando las respuestas del agente como base pero reescribiéndolas en lenguaje del cliente (no de agente). _Por qué no es regla_: el tono, la estructura, y qué incluir o excluir del borrador dependen del contexto del cliente objetivo y del estilo del tenant; no hay plantilla que capture eso sin juicio contextual.

3. **Identificación de por qué un artículo está desactualizado** — para artículos marcados como desactualizados, el modelo lee los tickets recientes relacionados y explica qué ha cambiado (nueva política, nuevo producto, cambio de proceso). _Por qué no es regla_: un artículo puede estar desactualizado porque cambió el proceso, porque el producto se descontinuó, o porque la redacción era confusa desde el inicio — la razón no es detectable sin leer los tickets y el artículo.

4. **Priorización del backlog de artículos pendientes** — el modelo ordena los grupos de tickets sin cobertura por urgencia: volumen × severidad del impacto al cliente × facilidad de resolución. _Por qué no es regla_: «facilidad de resolución» y «severidad del impacto» son juicios cualitativos que el modelo estima del contenido de los tickets.

> [!cuidado]
> El modelo nunca publica artículos directamente a la KB. Todo borrador pasa por revisión humana antes de ser publicado. El flujo es siempre: borrador → editor humano → publicación manual.

---

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[load_tickets] → tickets resueltos del período (determinístico, tool: sql_query)
  ↓
[search_kb] → vector search por ticket (determinístico)
  ↓
[group_uncovered] → cluster tickets sin cobertura (determinístico)
  ↓
[detect_outdated] → artículos desactualizados por métricas (determinístico)
  ↓
[prioritize] → ordena backlog por urgencia (agéntico)
  ↓
[decide_create_or_update] → nuevo artículo vs ampliar existente (agéntico)
  ↓
[draft_articles] → borradores por grupo (agéntico, loop)
  ↓
[explain_outdated] → por qué está desactualizado + qué cambiar (agéntico)
  ↓
[human_review] → interrupt: editor KB revisa y publica (siempre)
  ↓
[reindex] → actualiza vector store con artículos publicados (determinístico)
  ↓
[write_report] → reporte semanal de KB health (tool: write_report)
  ↓
END
```

Schedule recomendado: análisis semanal (lunes AM); reindexado continuo (webhook al publicar).

### Activities Temporal

- `load_ticket_batch(tenant, period)` — carga batch de tickets; idempotente por período.
- `run_kb_agent(tenant, period)` — corre el grafo; puede tardar 5–15 min según volumen.
- `reindex_kb(tenant, article_ids)` — re-embeda artículos nuevos/modificados.

### Tools necesarias

- `sql_query` — tickets del período + métricas de artículos del tenant.
- `write_report` — reporte de KB health semanal.
- `send_email` — borrador de artículo a editor KB.

---

## 8. Salida y entrega

**Reporte semanal de KB health**:

```
## KB Health Report — TiendaBox · Semana 2026-W16

**Deflection rate**: 28% (+3% vs semana anterior).
**Tickets sin cobertura KB esta semana**: 89 (21% del total).

### Artículos pendientes de crear (ordenados por urgencia)
1. «¿Cómo cambio la talla de un producto?» — 34 tickets esta semana (ningún artículo cubre cambios específicamente).
   → Borrador adjunto. Revisor asignado: [editor_cx@tiendabox.com]
2. «¿Qué pasa si me llega el producto dañado?» — 22 tickets.
   → Borrador adjunto.

### Artículos desactualizados
| Artículo | Problema detectado | Acción sugerida |
|----------|--------------------|-----------------|
| «Política de devoluciones» | 18 tickets dicen «30 días» pero el artículo dice «15 días» (cambio enero 2026) | Actualizar plazo en sección 2 |
| «¿Cómo contacto soporte?» | 12 tickets preguntan por WhatsApp; el artículo no menciona WhatsApp | Añadir canal WhatsApp |

⚠ Ningún borrador está publicado. Requieren revisión y aprobación antes de subir a la KB.
```

---

## 9. Cómo se vende

**Gancho**: «El 30% de tus tickets se podrían evitar con una KB actualizada. Nosotros te decimos qué artículos faltan, te damos el borrador, y tu equipo solo revisa y publica».

**Propuesta de valor**: reducción de volumen de tickets entrantes (deflection rate), reducción del tiempo de respuesta del agente (tiene el artículo listo para compartir), y KB que se mantiene sola con ciclo semanal.

| Tier | Condiciones | Precio |
|------|-------------|--------|
| Starter | ≤ 500 tickets/mes, KB ≤ 50 artículos | 150–300 USD/mes |
| Growth | ≤ 3000 tickets/mes, KB sin límite | 350–700 USD/mes |
| Setup | Indexado inicial de KB + integración helpdesk | 800–2000 USD |

---

## 10. Riesgos

**1. Borradores con información incorrecta publicados sin revisión.**
*Síntoma*: el modelo redacta un artículo diciendo que el plazo de devolución es 30 días cuando la política cambió a 15.
*Mitigación*: el pipeline es diseño de solo-lectura hacia la KB — nunca escribe directamente. El borrador se envía por email al editor con instrucciones explícitas de revisión. El harness incluye un check: si el borrador menciona fechas o plazos específicos, se resalta en rojo en el email de revisión.

**2. Vector store con embeddings desactualizados.**
*Síntoma*: el sistema sigue diciendo que el ticket tiene cobertura KB aunque el artículo relacionado fue archivado.
*Mitigación*: el reindexado es parte del pipeline al publicar o archivar artículos (webhook del helpdesk). El pipeline incluye un check de «artículos en vector store que no existen en KB» como parte del análisis semanal.

**3. Agrupación de tickets incorrecta.**
*Síntoma*: el cluster agrupa «problema con el pago» y «problema con la aplicación» como un solo grupo, generando un borrador confuso.
*Mitigación*: el reporte incluye los tickets de muestra de cada cluster para que el editor valide antes de usar el borrador. Si el editor rechaza el borrador, el sistema registra la razón y ajusta los parámetros de clustering en el siguiente ciclo.

**4. PII de clientes en los tickets usados para generar borradores.**
*Síntoma*: el borrador del artículo incluye detalles de un ticket específico de un cliente («Juan Pérez de Bogotá tuvo este problema cuando…»).
*Mitigación*: los tickets se anonimiza antes de usarlos como input del LLM (mismos patrones de F-CX-02: nombres, emails, teléfonos → `[CLIENTE]`). El modelo recibe el contenido del problema, no el contexto del cliente.

---

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: KB de 50–200 artículos; temas dominantes: devoluciones, tracking, pagos, cuenta, productos; alta velocidad de cambio (política de devoluciones puede cambiar en temporadas); clientes con bajo nivel de tolerancia a respuestas vagas.

**Delta determinístico**: los artículos se etiquetan con `valid_from` y `valid_until` según la política vigente; el sistema retira automáticamente artículos con `valid_until` pasado y los pone en estado `outdated` para revisión.

**Delta agéntico**: el modelo detecta inconsistencias entre artículos («el artículo de devoluciones dice 30 días; el artículo de garantías dice 15 días para el mismo producto»). Genera un alerta de inconsistencia, no resuelve solo.

**Regulación**: si la KB incluye precios, descuentos, o términos de garantía, su publicación puede tener implicaciones contractuales. El editor debe ser alguien con autorización para publicar información oficial de la empresa.

**Precio orientativo**: 250–600 USD/mes.

### Instancia 2 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: KB más pequeña (10–30 artículos); temas: reservaciones, menú, eventos, políticas de cancelación; alta estacionalidad (menú cambia); el canal principal de consulta es WhatsApp, no un portal de KB.

**Delta determinístico**: en hospitilidad, la KB se entrega al cliente vía WhatsApp Business (respuestas automáticas) en lugar de un portal. El pipeline genera los mensajes de respuesta automática de WhatsApp desde el mismo contenido que la KB; son dos outputs del mismo artículo.

**Delta agéntico**: el modelo detecta preguntas frecuentes en WhatsApp que no tienen respuesta automática configurada y genera tanto el artículo de KB como el mensaje de respuesta automática de WhatsApp en un solo borrador. El editor revisa y activa la automatización en WhatsApp Business.

**Regulación**: en hospitilidad, la información de alérgenos en el menú es regulatoria (Decreto 60/2002 Colombia, NOM-251 México). Si el artículo toca alérgenos, el editor debe ser el responsable de calidad de alimentos, no solo CX.

**Precio orientativo**: 150–300 USD/mes (KB pequeña, menor volumen de tickets).

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de él |
|--------|-----------------|
| **B02** — FastAPI routing | El endpoint `POST /kb/reindex` recibe el webhook del helpdesk cuando se publica un artículo y dispara el reindexado; el `Depends(get_tenant)` asegura que solo se reindexan artículos del tenant correcto. |
| **C01** — SQLAlchemy async | La tabla `kb_articles` persiste id, título, vector embedding, métricas y versión por tenant; las queries de similitud coseno se ejecutan sobre pgvector o sobre ChromaDB según el deploy. |
| **E01** — Anthropic SDK | El nodo `draft_articles` usa `cache_control: ttl:"1h"` sobre el system prompt con el estilo y guías de la KB del tenant (estático); los tickets de input van sin cache (dinámicos por análisis). |
| **E03** — Skills por tenant | El estilo de escritura de la KB, el tono, y el nivel de detalle esperado se inyectan como skill por tenant; TiendaBox quiere un tono cercano y paso a paso; Mesón Urbano quiere respuestas cortas y directas para WhatsApp. |
| **D04** — Observabilidad | Cada ciclo semanal se traza en Phoenix: cuántos artículos analizados, cuántos borradores generados, tasa de aceptación vs. rechazo por el editor. La tasa de rechazo es el KPI principal de calidad del agente. |

## 13. Errores típicos

**1. Borrador de artículo publicado directamente a la KB sin revisión humana.**
*Síntoma*: el pipeline tiene un bug en el nodo `human_review` que lo salta cuando el score de confianza del borrador es alto; el artículo con información incorrecta (plazo de devolución equivocado) queda publicado y visible para los clientes.
*Causa raíz*: se añadió un flag `auto_publish_if_confidence > 0.9` para acelerar el ciclo, ignorando que la confianza del modelo mide cohesión textual, no corrección factual.
*Cómo evitarlo*: el nodo `human_review` es no-removible en el workflow. La confianza del modelo nunca es criterio suficiente para publicar sin revisión; los datos factuales (plazos, precios, políticas) solo los puede validar un humano con acceso al documento de política vigente.

**2. PII de clientes filtrada en los borradores de artículo.**
*Síntoma*: el borrador incluye la frase «como ocurrió con un cliente que compró en octubre desde Barranquilla» porque el modelo copió detalles del ticket real.
*Causa raíz*: los tickets usados como input del nodo `draft_articles` no fueron anonimizados antes de enviarse al LLM.
*Cómo evitarlo*: todos los tickets que entran al nodo `draft_articles` pasan por el mismo PII scrubber de F-CX-02 (nombres, emails, teléfonos, direcciones → `[CLIENTE]`). El modelo solo recibe el contenido del problema, nunca el contexto identificable del cliente.

**3. Vector store con artículos obsoletos que siguen marcando «cobertura OK».**
*Síntoma*: el sistema indica que el ticket sobre «plazo de devolución» tiene cobertura KB, pero el artículo relacionado fue archivado hace 2 semanas y el vector store no se actualizó.
*Causa raíz*: el webhook de reindexado del helpdesk no disparó al archivar el artículo porque el evento `article_archived` no estaba en la lista de eventos suscritos.
*Cómo evitarlo*: el pipeline incluye un check semanal de «artículos en el vector store cuyo `kb_article_id` ya no existe en el helpdesk». Estos artículos se eliminan del índice automáticamente.

**4. Agrupación de tickets que combina problemas distintos en un solo borrador.**
*Síntoma*: el cluster agrupa «producto llegó roto» con «producto llegó tarde» porque tienen similitud semántica alta; el borrador generado es confuso y cubre mal ambos casos.
*Causa raíz*: el umbral de similitud del clustering (HDBSCAN `min_cluster_size`) es demasiado permisivo.
*Cómo evitarlo*: el reporte semanal muestra los 5 tickets de muestra de cada cluster para que el editor valide la coherencia antes de usar el borrador. Si el editor rechaza el borrador, el sistema registra la razón y ajusta `min_cluster_size` en el siguiente ciclo.

---

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre el deflection rate y la tasa de aceptación de borradores, y cuál de los dos me indica primero que el agente de KB está fallando.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este pipeline si mi 'KB' no es un portal de artículos sino respuestas automáticas de WhatsApp Business, y cómo se integra el ciclo de generación con la plataforma de WhatsApp.»
3. **Por qué falló**: «El sistema dijo que el ticket TB-29850 sobre cambio de talla tenía cobertura KB pero el agente tuvo que responder manualmente igual. ¿Qué puede haber ocurrido en el nodo `search_kb` y cómo lo diagnostico con las trazas de D04?»

---

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de detección de brechas en la KB usando vector search, clustering y métricas de deflection como señales complementarias.
- Implementar el ciclo de generación de borradores con anonimización de PII en los tickets de entrada, cumpliendo Ley 1581 y LGPD.
- Configurar el reindexado automático del vector store cuando se publican o archivan artículos.
- Evaluar la calidad del agente de KB mediante la tasa de aceptación de borradores y la tendencia del deflection rate semanal.
- Decidir cuándo un grupo de tickets justifica un artículo nuevo versus una actualización del artículo existente, y documentar el criterio en el golden set del tenant.

---

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|---------------------------------|
| **E01** — Anthropic SDK + tools | El nodo `draft_articles` usa `cache_control` sobre el system prompt con el estilo de KB del tenant; sin E01, el estudiante no configura el caching de prompts estáticos correctamente. |
| **E04** — Memoria y sesiones | Los artículos publicados anteriormente y el historial de rechazos del editor se inyectan como contexto en el ciclo semanal para no proponer el mismo borrador rechazado dos veces. |
| **C01** — SQLAlchemy async | La tabla `kb_articles` con embeddings en pgvector y las queries de similitud coseno son el patrón central del módulo C01; sin él, el estudiante no puede implementar el `search_kb`. |
| **D04** — Observabilidad y trazas auditables | La tasa de aceptación de borradores y el deflection rate son las métricas clave de este pipeline; D04 enseña a construirlas sobre las trazas de Phoenix sin instrumentación manual. |
