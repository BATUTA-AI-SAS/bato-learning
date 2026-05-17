---
ext_id: F-LEG-03
slug: monitoreo-regulatorio
track: F
dept: LEG
ord: 262
title: "Monitoreo regulatorio sectorial (alertas + impacto)"
summary: "Agente que rastrea diarios oficiales, superintendencias y circulares sectoriales, clasifica el impacto de cada norma nueva en el negocio del tenant y genera alertas accionables con deadline para el área responsable."
estimated_minutes: 45
industries_instanced: [energia, salud]
tenants_in_examples: [solenergy, sanrafael]
---

## 1. Problema operativo

La directora jurídica de SolEnergy Distribuidora recibe entre 3 y 8 notificaciones semanales de cambios regulatorios: resoluciones de la CREG (Comisión de Regulación de Energía y Gas), circulares de la Superintendencia de Servicios Públicos, decretos del Minminas. No tiene tiempo de leerlos todos en profundidad. Tampoco puede ignorarlos: el incumplimiento de una resolución CREG puede implicar multas que calculan sobre la facturación anual del distribuidor.

Clínica San Rafael enfrenta el mismo problema: resoluciones del Ministerio de Salud, circulares de la Superintendencia Nacional de Salud (Supersalud), actualizaciones del manual tarifario SOAT.

El agente no interpreta la norma en sentido jurídico. Clasifica impacto operativo, extrae deadlines, y dirige el aviso a quien debe actuar.

---

## 2. Hoy en big corps

Los equipos de Regulatory Affairs de grandes corporaciones usan plataformas de regulatory intelligence con curación manual más automatización.

| Vendor | Capacidad | Precio orientativo |
|--------|-----------|-------------------|
| **Thomson Reuters Regulatory Intelligence** | Cobertura global de regulaciones financieras y sectoriales; alertas configurables por jurisdicción y sector | 10 000–40 000 USD/año; enterprise |
| **Wolters Kluwer EHS / Compliance** | Regulatory tracking + workflow de acciones de compliance | 15 000–50 000 USD/año |
| **Vera AI (regulatory)** | Startup; NLP sobre texto regulatorio; integrable vía API | Pricing emergente, ~500–2 000 USD/mes |
| **Cuatrecasas / Baker McKenzie alertas** (LATAM) | Alertas curadas por abogados de firma; HTML/email | Incluido en retainer de 3 000–10 000 USD/mes |

La PYME no tiene retainer con una firma grande. Tampoco puede pagar Thomson Reuters. Tiene un RSS del Diario Oficial y una Google Alert mal configurada.

---

## 3. PYME LATAM realista

SolEnergy tiene suscripción al boletín PDF del Diario Oficial (Colombia) y recibe los correos de la CREG. El problema: llegan 30–50 documentos/mes. La directora jurídica abre los que tienen títulos obvios ("tarifas" o "distribución") y pospone los demás. Los demás a veces tienen deadlines.

Fuentes típicas en LATAM que tienen RSS o descarga programable:

| País | Fuente | Formato |
|------|--------|---------|
| Colombia | Diario Oficial (imprenta.gov.co), circulares SFC, resoluciones CREG, resoluciones Supersalud | PDF + índice HTML |
| México | DOF (dof.gob.mx), circulares CNBV, CONDUSEF | HTML + PDF |
| Chile | Diario Oficial (diarioficial.interior.gob.cl), circulares CMF | RSS + PDF |
| Perú | El Peruano (elperuano.pe), SBS circulares | HTML + PDF |

---

## 4. Datos típicos

| Atributo | Detalle |
|----------|---------|
| Fuente | RSS/scraping de portales oficiales; email parsing de listas de distribución |
| Frecuencia de ingesta | Diaria (diarios oficiales); semanal (circulares regulatorias) |
| Volumen | 10–60 documentos/semana por sector monitoreado |
| Formato | PDF (mayoría), HTML (algunos portales modernos) |
| Output | Alerta JSON + email/Slack al área responsable con resumen + deadline |
| Ejemplo de registro | `{source: "CREG", doc_id: "Resolución 101 de 2026", published: "2026-05-12", topic: "Actualización fórmula tarifaria distribución nivel 3", impact: "HIGH", deadline: "2026-07-01", responsible_area: "Tarifas y Regulación", summary: "..."}` |

---

## 5. Tramos determinísticos

1. **Ingesta de fuentes**: scraper (BeautifulSoup + requests) o parser RSS por fuente configurada por tenant. Descarga el documento (PDF/HTML) si es nuevo (hash de contenido para deduplicar).
2. **Extracción de metadatos estructurados**: número de resolución/circular, fecha de publicación, entidad emisora, número de páginas. Regex sobre el encabezado estándar del Diario Oficial.
3. **Filtro de relevancia por palabras clave del sector**: cada tenant tiene un `keyword_profile` (p. ej., para SolEnergy: `["tarifas", "distribución", "generación", "CREG", "UPME", "comercialización"]`). Si ninguna palabra clave aparece en el título + primer párrafo → descartado sin procesar.
4. **Deduplicación**: no procesar el mismo documento dos veces (hash SHA-256 del contenido).
5. **Almacenamiento en `regulatory_docs` con `tenant_id`**: cada documento ingestado queda trazado con su fuente, timestamp y estado (`pending_classification`, `classified`, `archived`).

---

## 6. Tramos agénticos

1. **Clasificación de impacto en el negocio** — el modelo recibe el texto del documento (o un extracto de las primeras 3 000 palabras) más el perfil del tenant (sector, país, actividades reguladas). Clasifica: `no_aplica`, `informativo` (leer pero no actuar), `acción_requerida` (hay que hacer algo), `urgente` (deadline < 30 días o multa inminente).

   *Por qué no es regla*: la misma resolución puede ser `informativo` para un distribuidor de nivel 2 y `urgente` para uno de nivel 3. El impacto depende del modelo de negocio específico del tenant, no solo del texto normativo.

2. **Extracción de deadlines y obligaciones** — cuando el impacto es `acción_requerida` o `urgente`, el modelo extrae: (a) la fecha límite de cumplimiento, (b) la obligación concreta (qué debe hacer el tenant), (c) el área responsable sugerida (Tarifas, Operaciones, Jurídica, Contabilidad).

   *Por qué no es regla*: los deadlines en textos normativos no siguen un formato estándar. A veces dicen "dentro de los 60 días hábiles siguientes a la publicación"; a veces "antes del 31 de julio del año en curso"; a veces el deadline está en un artículo de remisión cruzada. Extraerlos correctamente exige leer con comprensión.

3. **Redacción del resumen ejecutivo** — máximo 150 palabras, en lenguaje no técnico-jurídico, dirigido al responsable del área (no al abogado). "Esta resolución cambia la fórmula con la que la CREG calcula lo que SolEnergy puede cobrar por distribuir energía. El cambio entra en vigor el 1 de julio de 2026. El equipo de Tarifas debe actualizar el modelo de ingresos antes de esa fecha."

   *Por qué no es regla*: transformar lenguaje normativo en lenguaje operativo para distintas audiencias (tarifas, operaciones, contabilidad) no tiene una plantilla universal.

4. **Fallback humano**: documentos con `impact = urgente` y `deadline < 15 días` crean automáticamente una tarea de revisión humana urgente en el sistema, con notificación directa al gerente del área responsable. El agente no puede ignorar un deadline inminente aunque no esté seguro de su clasificación.

---

## 7. Blueprint del workflow

```
[SCHEDULE: diaria 06:00 AM por tenant]
      |
[FETCH_SOURCES]              (determinístico — Temporal activity)
  RSS parsers + scrapers por fuente configurada
  → lista de doc_ids nuevos
      |
[FILTER_RELEVANCE]           (determinístico)
  keyword_profile del tenant
  → docs relevantes / descartados
      |
[CLASSIFY_IMPACT]            ← agéntico
  LLM: (doc_excerpt, tenant_profile)
  → {impact, confidence}
      |
  confidence < 0.6 → impact = "revisar_humano"
      |
[EXTRACT_OBLIGATIONS]        ← agéntico (solo si impact >= "acción_requerida")
  LLM: (full_text, tenant_profile)
  → {deadline, obligation, responsible_area}
      |
[DRAFT_SUMMARY]              ← agéntico
  LLM: (findings, audience = responsible_area)
  → summary (≤ 150 palabras)
      |
[ALERT_GATE]                 (determinístico)
  impact == urgente AND deadline < 15 días
  → tarea urgente al gerente del área
      |
[DELIVER]
  email/Slack al responsable con: resumen + deadline + link al documento original
  archivar en regulatory_tracker del tenant
```

---

## 8. Salida y entrega

**Alerta regulatoria** (email + registro en dashboard):

```
ALERTA REGULATORIA — SolEnergy Distribuidora
Fuente: CREG | Documento: Resolución 101 de 2026 | Publicado: 2026-05-12
Impacto: ACCIÓN REQUERIDA | Deadline: 2026-07-01 | Área: Tarifas y Regulación

RESUMEN (para el equipo de Tarifas)
La CREG actualizó la fórmula con la que se calcula el cargo por uso de la red de
distribución de nivel 3. El cambio implica recalcular las tarifas vigentes de
SolEnergy antes del 1 de julio de 2026. Si no se actualiza la fórmula en el sistema
de facturación, hay riesgo de cobro incorrecto a usuarios y posible multa de la SSPD.

OBLIGACIÓN CONCRETA
  Actualizar el modelo tarifario (carga en sistema de facturación) antes del 01-07-2026.

ACCIÓN RECOMENDADA
  1. Compartir este documento con el consultor tarifario.
  2. Actualizar parámetros en el sistema (ERP de facturación).
  3. Notificar al asesor jurídico para confirmar interpretación.

[Ver documento original]  [Marcar como atendido]  [Escalar a gerencia]
```

---

## 9. Cómo se vende

**Gancho**: "¿Cuántas veces te enteraste tarde de un cambio regulatorio que implicaba acción? Este agente monitorea todo, filtra lo que te importa, y te dice qué hacer y para cuándo."

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Starter | 2 fuentes, 1 sector, alertas email | 150–300 USD/mes |
| Profesional | 6 fuentes, 2 sectores, Slack + email, dashboard de tracking | 400–800 USD/mes |
| Multi-sector | Fuentes ilimitadas, múltiples países, API de integración | 800–2 000 USD/mes |

Setup (configuración de fuentes, keyword profile del tenant, onboarding de áreas responsables): 600–1 500 USD una vez.

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Clasificación errónea de impacto** (urgente marcado como informativo) | El tenant no actúa a tiempo; multa o incumplimiento | (1) Umbral conservador: en caso de duda entre `informativo` y `acción_requerida`, el agente clasifica `acción_requerida`. (2) Revisar mensualmente el golden set con el equipo jurídico del tenant. |
| **Fuente caída o con estructura HTML cambiada** | Dejar de ingestar documentos sin saberlo | Monitoreo de health de cada scraper: si una fuente lleva 48 h sin nuevos documentos, alerta al administrador del tenant. |
| **El agente no interpreta la norma — riesgo jurídico** | Si el tenant actúa solo basado en el resumen del agente sin leer la norma, puede malinterpretar | Disclaimer en cada alerta: "Este resumen es orientativo. La decisión de cumplimiento debe basarse en la lectura de la norma completa y, si es material, en asesoría jurídica." Link al documento original siempre presente. |
| **Volumen de alertas excesivo** | Alert fatigue; el tenant ignora las alertas | Máximo 3 alertas de acción requerida por semana. Si hay más, se consolidan en un digest diario priorizado. Las `informativas` solo salen en un resumen semanal. |

---

## 11. Variantes por industria

| Delta | Energía (SolEnergy) | Salud (Clínica San Rafael) |
|-------|---------------------|---------------------------|
| Fuentes clave | CREG, SSPD, Minminas, UPME (Colombia) | Minsalud, Supersalud, INVIMA, ADRES |
| Tipo de norma más frecuente | Resoluciones tarifarias, fórmulas de cargos, manuales técnicos | Resoluciones de habilitación, actualizaciones manuales tarifarios, alertas INVIMA (farmacovigilancia) |
| Área responsable típica | Tarifas y Regulación, Ingeniería, Jurídica | Calidad y Acreditación, Facturación (SOAT/SGSSS), Jurídica |
| Consecuencia de incumplimiento | Multas SSPD (hasta 2000 SMMLV), suspensión de operación | Cierre de servicios, multas Supersalud, sanciones INVIMA |
| Frecuencia de cambios relevantes | 4–8 resoluciones relevantes/mes | 8–15 resoluciones relevantes/mes (INVIMA alta frecuencia) |
| Precio tier profesional | 500–700 USD/mes | 600–900 USD/mes |

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica |
|--------|-----------|
| **B02** — FastAPI routers y deps | Endpoint `GET /regulatory/alerts?tenant_id=X` para el dashboard de alertas; endpoint `POST /regulatory/sources` para que el admin del tenant configure fuentes. |
| **E01** — Anthropic SDK tool loop | El loop de clasificación e impacto: el modelo puede llamar a `fetch_document_section(doc_id, section)` para leer partes específicas del documento largo sin pasarlo todo al contexto. |
| **E05** — Temporal | Schedule diario por tenant: `regulatory_monitor_workflow` corre a las 06:00 AM por cada tenant activo. Si el scraper falla, Temporal lo reintenta con backoff sin duplicar alertas. |

## 13. Errores típicos

**1. El equipo actúa basándose solo en el resumen del agente sin leer la norma completa.**
*Síntoma*: el equipo de Tarifas de SolEnergy actualiza el modelo de ingresos siguiendo el resumen del agente, pero el resumen omitió un artículo transitorio que cambiaba la fecha de vigencia; el cumplimiento se implementa mal.
*Causa raíz*: el agente no interpreta la norma en sentido jurídico. El resumen ejecutivo de 150 palabras es una orientación para dirigir la atención del área responsable, no una opinión jurídica.
*Cómo evitarlo*: el disclaimer en cada alerta es obligatorio y no editable por el tenant: «Este resumen es orientativo. La decisión de cumplimiento debe basarse en la lectura de la norma completa y, si es material, en asesoría jurídica.» El link al documento original siempre está presente y es el primer elemento de la alerta.

**2. Dependencia ciega del LLM para fijar deadlines regulatorios sin verificación humana.**
*Síntoma*: el modelo extrae «antes del 31 de julio» de un decreto pero ese artículo fue modificado 10 días después por una resolución aclaratoria; el tenant usa la fecha original sin saberlo.
*Causa raíz*: el pipeline no tiene mecanismo para detectar resoluciones aclaratorias que modifiquen documentos ya clasificados.
*Cómo evitarlo*: los documentos con `impact >= acción_requerida` se marcan para re-revisión si, en los 30 días siguientes, se ingesta un nuevo documento del mismo ente emisor que referencie el mismo número de resolución. El área responsable recibe una alerta de «posible modificación» para que consulte al asesor jurídico.

**3. Alert fatigue por exceso de alertas `acción_requerida`.**
*Síntoma*: en la primera semana, SolEnergy recibe 12 alertas de acción requerida porque el `keyword_profile` es demasiado amplio; el equipo empieza a ignorarlas todas.
*Causa raíz*: el `keyword_profile` inicial fue configurado con términos genéricos («energía», «tarifas», «distribución») que capturan documentos irrelevantes para el modelo de negocio específico del tenant.
*Cómo evitarlo*: el onboarding incluye una sesión de calibración del `keyword_profile` con el equipo del tenant, usando 20 documentos reales de los últimos 6 meses para ajustar los términos. El cap de 3 alertas de acción requerida por semana actúa como guardarrail mientras el perfil se afina.

**4. Fuente de ingesta caída sin alerta al administrador del tenant.**
*Síntoma*: el scraper del Diario Oficial lleva 4 días sin ingestar documentos porque cambió la estructura del HTML; el tenant cree que no hubo novedades regulatorias cuando en realidad hay 3 resoluciones pendientes de clasificar.
*Causa raíz*: el health check de la fuente no está configurado; el silencio del scraper se interpreta como ausencia de novedades.
*Cómo evitarlo*: cada fuente tiene un `max_silence_hours` configurable (default: 48h para el Diario Oficial). Si una fuente no produce documentos nuevos en ese período, el sistema alerta al administrador con el mensaje «fuente sin documentos nuevos en las últimas 48h — verificar manualmente».

---

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame por qué la extracción de deadlines de un texto normativo es un tramo agéntico y no determinístico, con tres ejemplos de formas diferentes en que los decretos colombianos expresan una fecha límite.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este pipeline si necesito monitorear regulación de tres países simultáneamente (Colombia, México, Perú) para el mismo tenant, con fuentes en diferentes idiomas y formatos.»
3. **Por qué falló**: «La Resolución 101 de 2026 fue clasificada como `informativo` en lugar de `acción_requerida`, y SolEnergy se enteró del deadline cuando ya era tarde. ¿Qué pudo fallar en el nodo `CLASSIFY_IMPACT` y cómo lo diagnostico con las trazas de D04?»

---

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de monitoreo regulatorio con ingesta multi-fuente, filtro por `keyword_profile` del tenant, y clasificación de impacto agéntica.
- Implementar el health check de fuentes de ingesta para detectar silencios anómalos antes de que el tenant pierda un deadline regulatorio.
- Configurar el `ALERT_GATE` determinístico para deadlines urgentes con escalación automática al gerente del área responsable.
- Evaluar la calidad del clasificador de impacto con un golden set de documentos reales del tenant y recalibrar el `keyword_profile` cuando hay alert fatigue.
- Identificar los límites del agente como herramienta de orientación versus el rol del asesor jurídico en decisiones de cumplimiento material.

---

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|---------------------------------|
| **E01** — Anthropic SDK tool loop | El loop de clasificación e impacto: el modelo puede llamar a `fetch_document_section` para leer partes específicas de documentos largos sin saturar el contexto; sin E01, el estudiante pasa el documento completo al modelo en cada llamada. |
| **E05** — Temporal + idempotencia | El schedule diario por tenant con deduplicación por hash de documento es el patrón central; E05 enseña a garantizar que la misma resolución no genere dos alertas aunque el workflow se ejecute dos veces. |
| **D04** — Observabilidad y trazas auditables | El dashboard de alertas clasificadas y la detección de fuentes caídas se construyen sobre los spans de Phoenix; D04 enseña a instrumentar el scraper y el clasificador para que los fallos sean visibles. |
| **B02** — FastAPI routers y deps | El endpoint `POST /regulatory/sources` para que el administrador del tenant configure fuentes, y `GET /regulatory/alerts` para el dashboard, usan el patrón de `Depends(get_tenant)` que enseña B02. |
