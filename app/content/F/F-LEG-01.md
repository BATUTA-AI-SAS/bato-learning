---
ext_id: F-LEG-01
slug: revision-clausulas-contratos
track: F
dept: LEG
ord: 260
title: "Revisión de cláusulas en contratos contra plantilla aprobada"
summary: "Agente que compara un contrato recibido contra la plantilla legal aprobada, marca desviaciones, clasifica su materialidad y entrega un memo al abogado revisor."
estimated_minutes: 60
industries_instanced: [construccion, servicios-fin]
tenants_in_examples: [andina, cooppopular]
---

## 1. Problema operativo

El jefe de contratos de Constructora Andina recibe cada semana entre 5 y 15 contratos de subcontratistas: obra civil, alquiler de maquinaria, servicios de ingeniería. Todos llegan en Word o PDF, todos se desvían de la plantilla estándar de alguna manera. El abogado externo cobra por hora; revisar cada contrato completo es costoso e impredecible. El CFO quiere aprobar contratos en 24 h, no en 5 días. El abogado quiere saber exactamente dónde mirar, no leer el documento entero.

El agente no reemplaza al abogado. Prepara el material para que el abogado invierta su tiempo donde importa.

---

## 2. Hoy en big corps

Las empresas con equipos legales de más de 10 personas usan plataformas de CLM (Contract Lifecycle Management) con capas de IA sobre extracción de cláusulas.

| Vendor | Capacidad relevante | Precio orientativo |
|--------|--------------------|--------------------|
| **Ironclad** (OpenAI GPT-4o backend desde 2024) | Redline automático contra playbook aprobado; integración Salesforce | 30 k–80 k USD/año enterprise |
| **Kira Systems** (ahora Litera) | +1 000 campos de extracción pre-entrenados; due diligence pesado | 500–2 000 USD/usuario/mes |
| **LawGeex** | NDA y contratos estandarizados a alta escala; playbook personalizable | Enterprise, requiere cotización |
| **ContractPod Ai** (ahora Leah) | CLM + AI review; datos en entorno propio del cliente | Enterprise |

Una PYME con 50 contratos/mes no justifica ninguno de estos. El setup mínimo de Ironclad supera su presupuesto anual de herramientas legales.

---

## 3. PYME LATAM realista

Andina (construcción, 120 empleados, Bogotá) y Coop. Popular de Crédito (servicios financieros, 80 empleados, Medellín) tienen el mismo patrón:

- Los contratos llegan en Word. El abogado los abre, los compara mentalmente con la plantilla que tiene en Drive, tacha a mano, escribe comentarios en Track Changes.
- La plantilla aprobada vive en un PDF en Google Drive compartido, sin control de versiones.
- El ERP (World Office o Siigo) no tiene módulo legal. Las fechas de vencimiento se trackean en una hoja de cálculo.
- El abogado externo cobra entre 120 000 y 300 000 COP/hora. Revisar un contrato de 20 páginas le toma 2–4 h.

El agente entra aquí: extrae, compara, clasifica. El abogado solo revisa el memo de 1–2 páginas y valida la clasificación.

---

## 4. Datos típicos

| Atributo | Detalle |
|----------|---------|
| Formato | Word (.docx), PDF escaneado (requiere OCR), ocasionalmente Google Doc |
| Fuente | Email del proveedor, portal de licitaciones, notaría |
| Frecuencia | 5–15 contratos/semana por tenant |
| Volumen | 8–40 páginas por contrato |
| Plantilla | 1 archivo `.docx` por tipo de contrato (obra, servicio, alquiler) |
| Ejemplo de fila comparada | `{seccion: "Cláusula 7 – Responsabilidad", plantilla: "El contratista responde por daños hasta el valor del contrato", recibido: "El contratista responde por daños directos hasta COP 50.000.000"}` |

---

## 5. Tramos determinísticos

1. **Ingesta y normalización**: convertir DOCX/PDF a texto plano estructurado (secciones/headings extraídos por regex sobre estilos del documento).
2. **Carga de plantilla**: leer la plantilla aprobada del tenant (`templates/{tenant_id}/{contract_type}.docx`), misma extracción.
3. **Diff estructural por sección**: emparejar secciones por heading normalizado (Levenshtein ≤ 0.15 para cubrir variaciones de numeración); marcar secciones ausentes, añadidas o modificadas.
4. **Detección de campos críticos**: regex sobre campos contractuales de alto riesgo — monto máximo, plazo, penalidades, ley aplicable, jurisdicción. Si el campo no está presente en el contrato recibido: alerta automática `MISSING_CRITICAL_FIELD`.
5. **Índice de desviación cuantitativa**: `deviation_score = secciones_modificadas / secciones_totales`. Umbral > 0.4 → flag `HIGH_DEVIATION`.

---

## 6. Tramos agénticos

1. **Clasificación de materialidad de cada desviación** — el modelo recibe la cláusula de la plantilla, la cláusula recibida y el contexto del contrato (tipo, monto, partes). Decide: `equivalent` (redacción distinta, misma obligación), `minor` (cambio de forma sin impacto económico), `material` (cambia obligación, límite de responsabilidad o riesgo). Este juicio no es una regla cerrada porque depende de si un cambio de tope monetario es grande respecto al valor del contrato, de la industria, de la contraparte.

   *Por qué no es regla*: "COP 50 M de responsabilidad" es material en un contrato de COP 30 M pero trivial en uno de COP 2 000 M. El umbral relativo varía por tenant y por tipo de obra.

2. **Detección de cláusulas riesgosas ausentes** — algunas cláusulas no están en la plantilla pero deberían estar dadas las condiciones del contrato. El modelo identifica cláusulas estándar de la industria que el contrato omite (p. ej., cláusula anticorrupción FCPA/LSAP, protección de datos si hay PII, jurisdicción arbitral si es contrato internacional).

   *Por qué no es regla*: el catálogo de "cláusulas que deberían estar" cambia por industria, país de la contraparte y tipo de operación. No existe una lista cerrada aplicable a todos los contratos.

3. **Fallback humano**: si el modelo emite confianza < 0.7 en la clasificación de materialidad, la desviación se marca `NEEDS_LAWYER_REVIEW` sin clasificar. El memo incluye una sección "Pendiente de revisión humana" con esas cláusulas. El flujo **nunca bloquea**: siempre produce un memo, aunque sea parcial.

---

## 7. Blueprint del workflow

```
[INGEST]
  docx/pdf → text_extractor (determinístico)
      |
[PARSE_TEMPLATE]
  template store (por tenant) → section_parser (determinístico)
      |
[DIFF]
  structural_diff (determinístico)
  field_extractor → critical_fields_check (determinístico)
      |
[CLASSIFY_DEVIATIONS]           ← agéntico
  LLM: (plantilla_section, recibido_section, contract_context)
    → {materiality: "equivalent|minor|material", confidence: float, rationale: str}
      |
  confidence < 0.7? → mark NEEDS_LAWYER_REVIEW
      |
[DETECT_MISSING_CLAUSES]        ← agéntico
  LLM: (contract_type, parties, jurisdiction, full_text)
    → [missing_standard_clauses]
      |
[BUILD_MEMO]                    (determinístico — plantilla Jinja2)
  → memo.pdf (secciones: resumen, desviaciones críticas, desviaciones menores,
               cláusulas faltantes, pendiente revisión humana)
      |
[DELIVER]
  email al abogado revisor + link a expediente en Drive
```

**Tools necesarias**:
- `extract_text(file_path: str, tenant_id: str) -> dict[str, str]` — secciones normalizadas.
- `load_template(tenant_id: str, contract_type: str) -> dict[str, str]` — plantilla vigente.
- `structural_diff(template: dict, received: dict) -> list[DiffItem]` — diff por sección.
- `classify_deviation(template_clause: str, received_clause: str, context: ContractContext) -> ClassificationResult` — LLM call.
- `detect_missing_clauses(contract_text: str, context: ContractContext) -> list[str]` — LLM call.
- `render_memo(findings: MemoData, tenant_id: str) -> bytes` — PDF vía Jinja2 + WeasyPrint.

---

## 8. Salida y entrega

**Memo de revisión** (1–3 páginas, PDF):

```
MEMO DE REVISIÓN — Contrato de obra civil
Tenant: Constructora Andina | Fecha: 2026-05-16 | Contrato: OBR-2026-087

RESUMEN EJECUTIVO
  Desviación total: 34% (6 de 18 secciones modificadas) — NIVEL MEDIO
  Cláusulas con desviación MATERIAL: 2
  Cláusulas estándar ausentes: 1
  Pendiente revisión humana: 1

DESVIACIONES MATERIALES
  § 7 — Responsabilidad
    Plantilla:  "...hasta el valor total del contrato (COP 280.000.000)"
    Recibido:   "...hasta COP 50.000.000"
    Impacto:    Límite 82% inferior al valor del contrato. MATERIAL.
    Acción:     Negociar restitución del tope o ajuste de prima de seguro.

  § 12 — Ley aplicable
    Plantilla:  "Jurisdicción: Cámara de Comercio de Bogotá"
    Recibido:   "Jurisdicción: Tribunales ordinarios de Medellín"
    Impacto:    Cambio de foro arbitral. Costo potencial de litigio mayor. MATERIAL.

CLÁUSULAS ESTÁNDAR AUSENTES
  - Cláusula anticorrupción (LSAP Colombia). Recomendado añadir Adición 1.

PENDIENTE REVISIÓN HUMANA (confianza del modelo < 70%)
  § 9 — Garantías. Redacción ambigua. Revisar con abogado antes de aprobar.
```

**Canal**: email automático al abogado revisor con adjunto PDF + link al expediente en Drive del tenant.

---

## 9. Cómo se vende

**Gancho**: "Tu abogado externo revisa contratos por hora. Con este agente, revisa un memo de 2 páginas, no 20 páginas de contrato."

**Propuesta de valor**: reducir el tiempo de revisión legal de 2–4 h a 20–30 min por contrato; dar al CFO visibilidad de la pipeline de contratos pendientes.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Starter | Hasta 20 contratos/mes, 1 tipo de contrato, 1 plantilla | 200–400 USD/mes |
| Profesional | Hasta 80 contratos/mes, 3 tipos, integración Drive/email | 400–800 USD/mes |
| Multi-tenant | Tenant adicional | +150–300 USD/mes por tenant |

Setup inicial (ingesta de plantillas, calibración de umbral de materialidad, golden set): 800–2 000 USD una vez.

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **El modelo clasifica como `minor` una desviación material** | El abogado no la ve; el cliente firma un contrato desfavorable | (1) Golden set con 20 contratos reales del tenant para calibrar. (2) El memo siempre incluye las cláusulas clasificadas para que el abogado pueda contradecir. (3) Cláusulas de responsabilidad económica siempre en revisión humana obligatoria, sin excepción. |
| **OCR de mala calidad en contratos escaneados** | Secciones no detectadas; diff incorrecto | Marcar páginas con confianza OCR < 0.85 como `LOW_QUALITY`; incluir imagen de la página en el memo para revisión visual. |
| **El agente no reemplaza al abogado — riesgo regulatorio** | Si se usa como validación final, el cliente asume un riesgo legal que el agente no puede cubrir | Disclaimer visible en el memo: "Este análisis es un borrador de revisión para asistencia al abogado. No constituye opinión jurídica ni reemplaza la revisión de un profesional del derecho." |
| **Filtración de PII / datos confidenciales del contrato** | Breach legal y de confianza con el cliente | Contratos procesados on-premise o en VPC dedicada por tenant. Cero logs de contenido contractual en sistemas compartidos. Datos cifrados en reposo y en tránsito. |
| **Plantilla desactualizada** | El diff compara contra una plantilla obsoleta | Control de versiones de plantillas con fecha de vigencia. El agente rechaza plantillas sin `valid_from` o con `valid_until` expirado. |

---

## 11. Variantes por industria

| Delta | Construcción (Andina) | Servicios financieros (Coop. Popular) |
|-------|-----------------------|--------------------------------------|
| Tipos de contrato | Obra, alquiler maquinaria, subcontratación | Apertura de cuenta, crédito, fiducia, corresponsalía |
| Regulación aplicable | NSR-10 (sismo-resistente), RETIE, RETILAP | Circular Básica Jurídica SFC, SARLAFT, SAGRILAFT |
| Cláusulas críticas adicionales | Pólizas de responsabilidad civil, cumplimiento, estabilidad de obra | Cláusulas de habeas data (Ley 1581/2012), autorización SAGRILAFT, reportes UIAF |
| Autoridad que pide compliance | Camacol, Lonja, Contratista principal | Superintendencia Financiera de Colombia |
| Riesgo de multa si no se revisa bien | Veeduría de obra, pólizas que no pagan | Multas SFC hasta 200 000 SMMLV; sanciones UIAF |
| Precio del tier profesional | 400–600 USD/mes (volumen moderado) | 600–900 USD/mes (regulación más exigente, más tipos) |

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica |
|--------|-----------|
| **A06** — Type hints y protocolos | `ContractContext`, `ClassificationResult` como dataclasses tipados; `Protocol` para el extractor de texto (DOCX vs PDF comparten interfaz). |
| **B02** — FastAPI routers y deps | Endpoint `POST /contracts/review` que recibe el archivo y devuelve `task_id`; `GET /contracts/{task_id}/memo` para descargar el PDF. |
| **E01** — Anthropic SDK tool loop | El loop de clasificación de cláusulas: el modelo itera sobre cada `DiffItem` y llama a `classify_deviation`. |
| **E03** — Skills AGENTS.md | Skill `contract_review` con slots por tenant: `{template_path}`, `{risk_threshold}`, `{mandatory_clauses}`. |
| **D04** — Observabilidad Phoenix | Span por cláusula clasificada; métrica `cost_usd` por contrato; alerta si costo > 0.50 USD/contrato (modelo demasiado verboso). |
| **C03** — Multitenancy | `tenant_id` en cada query de template store; RLS en tabla `contract_reviews` para que cada tenant solo vea sus contratos. |

## 13. Errores típicos

**1. Usar la clasificación del agente como aprobación final sin revisión del abogado.**
*Síntoma*: el equipo jurídico del tenant configura el flujo para aprobar automáticamente contratos donde todas las desviaciones son `minor`; un contrato con una cláusula de arbitraje cambiada pasa sin revisión.
*Causa raíz*: el agente no reemplaza al abogado. La clasificación `minor` del modelo es una sugerencia para dirigir la atención del revisor, no una validación jurídica. El disclaimer del memo existe por una razón.
*Cómo evitarlo*: el workflow no expone ninguna acción de «aprobar contrato» automatizada. El único output es el memo; la aprobación es siempre un acto humano del abogado o del gerente jurídico. Esta restricción es no-negociable en el harness.

**2. Dependencia ciega del LLM en la clasificación de materialidad sin golden set.**
*Síntoma*: después de 3 meses, el modelo clasifica como `minor` el 70% de las desviaciones cuando el abogado del tenant, al revisar la muestra mensual, dice que el 40% deberían ser `material`.
*Causa raíz*: el golden set inicial se calibró con 5 contratos de ejemplo genéricos, no con contratos reales del tenant con sus umbrales específicos de cuantía y riesgo.
*Cómo evitarlo*: el onboarding incluye obligatoriamente la revisión de 20 contratos reales del tenant por el abogado, con su clasificación de materialidad como etiqueta de verdad. El modelo se evalúa mensualmente contra este golden set; si la precisión cae < 85%, se recalibra el prompt con nuevos ejemplos.

**3. OCR de baja calidad en contratos escaneados que produce un diff incorrecto.**
*Síntoma*: el memo dice «sin desviaciones en cláusula 7» porque el texto de esa sección llegó corrupto del OCR y el diff estructural no encontró contenido que comparar.
*Causa raíz*: el nodo `extract_text` no validó el confidence score del OCR antes de continuar con el diff.
*Cómo evitarlo*: cualquier página con confidence OCR < 0.85 se marca `LOW_QUALITY`; el memo incluye la imagen de la página y una advertencia explícita al abogado para que la revise visualmente.

**4. Plantilla desactualizada sin control de versiones.**
*Síntoma*: el agente compara el contrato recibido contra una plantilla de hace 8 meses que ya no refleja las condiciones actuales de la empresa; las «desviaciones» detectadas son comparaciones contra términos obsoletos.
*Causa raíz*: la plantilla se subió una vez al inicio y nadie la actualizó cuando cambió la política legal de la empresa.
*Cómo evitarlo*: las plantillas tienen campo obligatorio `valid_from` y `valid_until`. El agente rechaza plantillas con `valid_until` expirado y alerta al administrador del tenant para que las renueve. Sin plantilla vigente, el pipeline no corre.

**5. Filtración de contenido contractual sensible en logs compartidos.**
*Síntoma*: el texto de un contrato con condiciones de precio confidenciales aparece en las trazas de Phoenix de un tenant vecino por un error de `tenant_id` en la query de logs.
*Causa raíz*: el logging del nodo `classify_deviations` guarda el texto completo de las cláusulas sin aislar por tenant.
*Cómo evitarlo*: los contratos se procesan en VPC dedicada por tenant; los logs solo persisten metadatos (`contract_id`, `section_id`, `materiality`, `confidence`). El texto de las cláusulas no sale del entorno de procesamiento del tenant.

---

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame por qué la clasificación de materialidad de una cláusula de responsabilidad no puede ser una regla determinística con un threshold numérico, usando el ejemplo del contrato de COP 30M vs. COP 2.000M de la sección 6.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este pipeline si mis contratos están en inglés y español mezclado porque trabajo con proveedores internacionales, y si algunos contratos usan terminología del derecho anglosajón (common law) en lugar de civil law colombiano.»
3. **Por qué falló**: «El memo del contrato OBR-2026-087 clasificó la cláusula de responsabilidad como `minor` cuando debería ser `material`. ¿En qué parte del workflow pudo ocurrir el error y qué cambio en el golden set o en el prompt lo habría evitado?»

---

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de revisión de contratos con separación correcta de tramos determinísticos (diff estructural, campos críticos) y agénticos (clasificación de materialidad, cláusulas faltantes).
- Implementar el control de versiones de plantillas con `valid_from` / `valid_until` para que el agente rechace comparaciones contra plantillas obsoletas.
- Configurar el fallback humano para desviaciones con confianza < 0.7 y para cláusulas de responsabilidad económica, sin bloquear la generación del memo.
- Evaluar la calidad del agente con un golden set de contratos reales del tenant y recalibrar cuando la precisión cae bajo umbral.
- Decidir el tier de precio adecuado para un cliente dado su volumen y complejidad regulatoria (construcción vs. servicios financieros).

---

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|---------------------------------|
| **E01** — Anthropic SDK tool loop | El loop de clasificación de cláusulas (`classify_deviation` por cada `DiffItem`) es el primer ejemplo de tool calling con respuesta estructurada y múltiples iteraciones; sin E01, el estudiante no puede implementar el ciclo correctamente. |
| **E03** — Skills por tenant | El `risk_threshold`, las `mandatory_clauses` y el `template_path` se inyectan como skill por tenant; sin E03, el estudiante hardcodea estos parámetros y rompe la multitenancy. |
| **E05** — Temporal + idempotencia | Si el pipeline falla a mitad de la clasificación de un contrato largo, Temporal permite retomarlo desde la última cláusula clasificada sin re-procesar todo el documento; E05 enseña este patrón de checkpoint. |
| **D04** — Observabilidad y trazas auditables | El span por cláusula clasificada y la métrica `cost_usd` por contrato permiten detectar contratos anómalos y auditar decisiones del modelo; D04 es prerequisito para operar el agente en producción. |
