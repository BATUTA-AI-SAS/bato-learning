# MODULES_STATUS.md — estado de producción de módulos

Este archivo lo actualizan los Sonnets de módulo al terminar su trabajo.
Formato: entrada YAML por lote. El integrador lo lee para saber qué está listo,
qué asume, y qué deja para el siguiente.

---

## Lote UX-FIX F1+F6+F7 — completado (2026-05-16)

Fixes de engagement identificados por el auditor Opus. Audiencia: Excel-only (Track 0).

```yaml
batch: UX-FIX F1+F6+F7
date: 2026-05-16
fixes:
  F1_inline_exercises:
    status: done
    files_modified:
      - app/templating.py          # sentinel strategy para marcadores INLINE_EXERCISE/QUIZ
      - app/templates/module.html  # data-module-id + hoist script
      - app/templates/partials/exercise.html  # data-slug añadido
      - app/templates/partials/quiz.html      # data-slug añadido
      - app/static/js/app.js       # hoistInlineExercises() llamada en DOMContentLoaded
    smoke_test: "00-05.md tiene <!-- INLINE_EXERCISE: repl-arithmetic --> tras §Idea central.
      El ejercicio aparece inline; si no hay anchor, cae a #exercises (legacy intacto)."

  F6_glossary_tooltips:
    status: done
    files_modified:
      - app/services/glossary.py   # nuevo; 35 términos canónicos + apply_glossary_tooltips()
      - app/templating.py          # llama apply_glossary_tooltips después de render
      - app/static/css/site.css    # abbr.term: border-bottom punteado + cursor help
    notes: "No toca <code>, <pre>, <a>, <abbr>. Solo primera aparición por render."

  F7_checkpoint_xp:
    status: done
    files_modified:
      - app/services/gamification.py   # XpRule('checkpoint_reached', 5, ...)
      - app/repos/gamification.py      # record_checkpoint_xp() idempotente
      - app/repos/modules.py           # get_by_id()
      - app/routers/progress.py        # POST /api/checkpoints/{module_id}/{checkpoint_id}
      - app/main.py                    # registra checkpoint_router
      - app/static/js/app.js           # wireCheckpoints() con IntersectionObserver + 5 s timer
      - app/templating.py              # _mark_checkpoints() añade class=checkpoint + data-checkpoint-id
      - app/static/css/site.css        # h2.checkpoint: border-left accent
    xp_math: "Track 0 módulo con 7 secciones: 7 × 5 × 2 (multiplicador T0) = 70 XP solo por leer.
      + 20 XP open + 50 XP por ejercicio (× 2 T0) = 190 XP sesión completa vs 70 antes."

tests_passing: 6/6
```

---

## Track G — Negocio LATAM — completado (2026-05-16)

**Archivos producidos** (3 archivos por módulo + _README.md):
- `app/content/G/_README.md` — convenciones del track
- `app/content/G/G01.md` + yaml × 2 — Discovery PYME LATAM (ord 200, 60 min)
- `app/content/G/G02.md` + yaml × 2 — Demo y POC (ord 201, 45 min)
- `app/content/G/G03.md` + yaml × 2 — Pricing models (ord 202, 60 min)
- `app/content/G/G04.md` + yaml × 2 — Contratos MSA/SOW/DPA/SLA (ord 203, 75 min)
- `app/content/G/G05.md` + yaml × 2 — Onboarding cliente (ord 204, 60 min)
- `app/content/G/G06.md` + yaml × 2 — Customer success (ord 205, 60 min)
- `app/content/G/G07.md` + yaml × 2 — Capstone comercial (ord 206, 90 min)

```yaml
- id: G01
  status: done
  assumed_from_prereqs:
    "E06": "lector puede construir un agente multitenant funcional"
    "F-FIN-01": "lector conoce el caso de conciliación bancaria como ejemplo vendible"
  prepared_for_successors:
    G02: "dolor del cliente cuantificado y champion identificados"
    G07: "discovery script template y BANT validado disponibles"
  glossary_terms_introduced:
    - "Discovery: sesión estructurada para mapear el problema operativo real"
    - "Champion: aliado interno sin poder de firma"
    - "BANT: Budget, Authority, Need, Timing"
  open_questions: []

- id: G02
  status: done
  assumed_from_prereqs:
    G01: "dolor cuantificado, champion y comprador económico identificados"
  prepared_for_successors:
    G03: "POC con success criteria da el baseline para el pricing"
    G07: "plantilla de demo (3 actos) y POC disponibles"
  glossary_terms_introduced:
    - "POC: agente mínimo sobre datos reales con success criteria y fecha de cierre"
    - "Time-to-first-value (TTFV): días hasta el primer valor demostrado"
  open_questions: []

- id: G03
  status: done
  assumed_from_prereqs:
    G02: "POC cerrado; success criteria validan el precio"
  prepared_for_successors:
    G04: "modelo de pricing y tiers definidos; el SOW recoge el precio"
    G07: "tabla de precios LATAM y calculadora de margen disponibles"
  deviations_from_spec: |
    Tabla de precios 2026 basada en costos reales Anthropic Sonnet 4.6 + Hetzner CX22.
    Rangos son síntesis de benchmarks SaaS SMB 2026 — no hay fuente pública específica
    de precios LATAM para agentes IA.
  glossary_terms_introduced:
    - "Anchoring: mostrar primero el precio más alto"
    - "Margen bruto: (precio - costo_variable) / precio × 100"
  open_questions:
    - "Precios de tokens Anthropic cambian. Revisar al actualizar el curso."

- id: G04
  status: done
  assumed_from_prereqs:
    G03: "precio y tiers acordados"
  prepared_for_successors:
    G05: "MSA/SOW/DPA firmados son requisito para iniciar el onboarding"
    G07: "esqueletos contractuales con campos de Andina completados"
  deviations_from_spec: |
    DPA cubre CO (Ley 1581), BR (LGPD) y MX (LFPDPPP reformada 2025).
    México: INAI reemplazado por Transparencia para el Pueblo en 2025.
  glossary_terms_introduced:
    - "MSA / SOW / DPA / SLA — todos definidos en _README.md del track"
  open_questions:
    - "Reforma LFPDPPP MX 2025 puede tener desarrollos reglamentarios adicionales. Verificar para clientes mexicanos."

- id: G05
  status: done
  assumed_from_prereqs:
    G04: "contratos firmados"
    "E06": "agente desplegado; onboarding lo configura para el tenant"
  prepared_for_successors:
    G06: "métricas de uso desde Día 1 post-go-live para el primer QBR"
    G07: "plan de onboarding 14 días con hitos"
  glossary_terms_introduced:
    - "Golden set: 5-20 ejemplos validados por el cliente con salida esperada"
    - "Hand-off operativo: transferencia de responsabilidad al cliente"
    - "Babysitting: soporte activo del primer mes"
  open_questions: []

- id: G06
  status: done
  assumed_from_prereqs:
    G05: "cliente en producción con métricas desde Día 1"
  prepared_for_successors:
    G07: "NDR/NRR, QBR template y protocolo de churn disponibles"
  deviations_from_spec: |
    Benchmarks NDR/NRR de Optifai 2026 (900+ empresas B2B SaaS).
    Churn anual PYME LATAM objetivo < 15 % — más conservador que benchmark US/EU.
  glossary_terms_introduced:
    - "QBR: Quarterly Business Review"
    - "Gross Retention / Expansion % / Escalation matrix"
  open_questions: []

- id: G07
  status: done
  assumed_from_prereqs:
    G01: "discovery + BANT"
    G02: "demo + POC"
    G03: "pricing + margen"
    G04: "contratos"
    G05: "onboarding"
    G06: "KPIs + QBR"
  prepared_for_successors:
    "H01": "plan de onboarding 14 días que H01 profundiza"
    "H02": "QBR template y KPIs acordados que H02 expande"
  deviations_from_spec: |
    5 entregables del Capstone son documentos reales usables con un cliente real.
    Ejercicio 1 (discovery) usa pyodide con tests sobre dict BANT.
    Ejercicio 2 (propuesta) valida longitud ≤ 300 palabras + campos obligatorios.
    Ejercicio 3 (KPIs) valida verificabilidad por el cliente.
  open_questions:
    - "El Capstone G07 asume E06 completado. Verificar prerequisito en el loader del site."
```

---

## Track J — Compliance LATAM — completado (2026-05-16)
### Lote J

**Archivos producidos** (3 archivos por módulo: `.md`, `.exercises.yaml`, `.quizzes.yaml`):
- `app/content/J/J01.md` + yaml × 2 — Habeas Data CO (Ley 1581) + LFPD Perú (Ley 29733) (ord 260, 60 min)
- `app/content/J/J02.md` + yaml × 2 — LGPD Brasil + ANPD resoluciones (ord 261, 60 min)
- `app/content/J/J03.md` + yaml × 2 — LFPDPPP México 2025 + CFDI 4.0 + Factura DIAN (ord 262, 75 min)
- `app/content/J/J04.md` + yaml × 2 — KYC/AML/SARLAFT 4.0 en flujos agénticos (ord 263, 60 min)
- `app/content/J/_README.md` — índice y referencias normativas del track

```yaml
- id: J01
  status: done
  assumed_from_prereqs:
    C03: "RLS y tenant_id como mecanismo técnico de aislamiento; el módulo J01 lo eleva a obligación legal"
    D02: "compose.yaml y elección de región de nube — J01 añade la restricción de transferencia internacional"
  prepared_for_successors:
    J02: "lector entiende responsable/encargado del tratamiento, principios de privacidad y DPA mínimo"
    E04: "retención de datos por tenant tiene plazo legal (no solo técnico) según jurisdicción"
  deviations_from_spec: |
    El plazo de notificación de brechas en Perú se actualizó a 48h (DS 16-2024-JUS,
    nov 2024) vs. el enunciado original que mencionaba 15 días. Se usa el dato vigente.
    Se añadió ejercicio breach_timeline_design que compara CO vs PE con fecha actual 2026-05-16.
  glossary_terms_introduced:
    - "habeas data: derecho constitucional a conocer, actualizar y rectificar datos propios"
    - "encargado del tratamiento: quien procesa datos por cuenta del responsable"
    - "responsable del tratamiento: quien decide sobre los datos"
    - "dato sensible: dato de salud, biometría, origen étnico, religión, opinión política"
    - "RNBD: Registro Nacional de Bases de Datos, portal SIC Colombia"
    - "DPA: acuerdo de tratamiento de datos entre responsable y encargado"
  open_questions: []

- id: J02
  status: done
  assumed_from_prereqs:
    J01: "lector conoce responsable/encargado, principios de privacidad, DPA mínimo"
  prepared_for_successors:
    J03: "lector tiene comparativa LGPD vs Ley 1581; entiende SCCs de transferencia"
    G04: "el DPA multi-jurisdiccional (CO + BR) requiere las SCCs ANPD como apéndice"
  deviations_from_spec: |
    Se incorporó la Resolução CD/ANPD Nº 19/2024 (transferencias internacionales)
    con fecha de gracia exacta: 22 agosto 2025. El enunciado solo mencionaba
    'transferencias internacionales' en genérico.
    La multa máxima en USD se aproximó a 10M USD (R$50M con tasa orientativa 2026).
  glossary_terms_introduced:
    - "LGPD: Lei Geral de Proteção de Dados, Brasil, Lei 13.709/2018"
    - "ANPD: Autoridade Nacional de Proteção de Dados, autoridad supervisora Brasil"
    - "encarregado: figura DPO obligatoria bajo Art. 41 LGPD"
    - "SCCs ANPD: cláusulas contractuales tipo de la ANPD para transferencia internacional"
    - "ROPA: Registro de Operações de Tratamento de Dados Pessoais"
    - "extraterritorialidade: alcance de la LGPD a operaciones fuera de Brasil (Art. 3)"
  open_questions: []

- id: J03
  status: done
  assumed_from_prereqs:
    J01: "lector conoce clasificación PII, DPA, principio de finalidad"
    J02: "lector entiende extraterritorialidad y SCCs de transferencia"
  prepared_for_successors:
    J04: "lector sabe que RFCs de personas físicas son PII bajo LFPDPPP 2025"
    F-CTA-03: "lector puede implementar el nodo ingest_efactura con parsing CFDI 4.0 correcto"
  deviations_from_spec: |
    Se incorporó la nueva LFPDPPP publicada el 20 marzo 2025 (no la ley de 2010)
    y la disolución del INAI → SABG (decreto dic 2024). El enunciado original
    referenciaba INAI que ya no existe como autoridad.
    CFDI: se añadió la tabla de 4 motivos de cancelación con decisión auto vs
    interrupt_before, que no estaba en el enunciado original pero es crítica para
    el diseño del agente de emisión.
  glossary_terms_introduced:
    - "CFDI 4.0: Comprobante Fiscal Digital por Internet v4.0, obligatorio México desde abr 2023"
    - "PAC: Proveedor Autorizado de Certificación, intermediario obligatorio para timbrar CFDIs"
    - "UUID CFDI: Folio Fiscal único del SAT, resultado del timbre PAC"
    - "CUFE: Código Único de Factura Electrónica, Colombia DIAN"
    - "rango numérico DIAN: autorización de secuencia de numeración de facturas CO"
    - "SABG: Secretaría de Anticorrupción y Buen Gobierno, nueva autoridad datos MX 2025"
  open_questions: []

- id: J04
  status: done
  assumed_from_prereqs:
    J01: "lector entiende que el agente es encargado del tratamiento; DPA requerido"
    F-LEG-02: "caso de uso KYC/AML concreto (Coop. Popular); el módulo J04 profundiza el marco regulatorio"
  prepared_for_successors:
    E04: "memoria multitenant incluye ahora retención de expedientes KYC con plazo legal"
    G04: "el contrato MSA/DPA debe incluir cláusulas de SARLAFT si el cliente es entidad vigilada SFC"
  deviations_from_spec: |
    Se añadió la tabla de listas de monitoreo con fuente y formato de acceso
    (OFAC CSV gratuito, ONU XML, RUES API, etc.) que el enunciado no especificaba.
    Se documentó el plazo AROS (10 días del mes siguiente al trimestre) con
    ejercicio de Temporal Schedule específico.
  glossary_terms_introduced:
    - "SARLAFT: Sistema de Administración del Riesgo de Lavado de Activos y FT, entidades Superfinanciera CO"
    - "SAGRILAFT: versión SARLAFT para sector real (Supersociedades CO)"
    - "PEP: Persona Expuesta Políticamente; definición ampliada en Circular 027/2020"
    - "ROS: Reporte de Operación Sospechosa, enviado a UIAF/COAF/UIF por oficial de cumplimiento"
    - "AROS: Ausencia de ROS, reporte trimestral cuando no hay operaciones sospechosas"
    - "UIAF: Unidad de Información y Análisis Financiero, Colombia"
    - "COAF: Conselho de Controle de Atividades Financeiras, Brasil"
    - "UIF: Unidad de Inteligencia Financiera, México y Argentina"
    - "UAF: Unidad de Análisis Financiero, Chile"
    - "UBO: Ultimate Beneficial Owner, beneficiario final real de una empresa"
  open_questions:
    - "J04 menciona SAGRILAFT pero no cubre su estructura completa (Supersociedades). Un módulo futuro o sección en G04 podría profundizar."
```

---

## Track S — Seguridad aplicada a agentes IA — completado (2026-05-16)
### Lote S

**Archivos producidos** (3 archivos por módulo: `.md`, `.exercises.yaml`, `.quizzes.yaml`):
- `app/content/S/S01.md` + yaml × 2 — OWASP API Security Top 10 aplicado a FastAPI (ord 220, 75 min)
- `app/content/S/S02.md` + yaml × 2 — Prompt injection, jailbreak, e indirect prompt injection (ord 221, 60 min)
- `app/content/S/S03.md` + yaml × 2 — Tool security: allowlist, sandbox, dry-run, human-in-the-loop (ord 222, 60 min)
- `app/content/S/S04.md` + yaml × 2 — Threat modeling para SaaS agéntico multitenant (ord 223, 75 min)
- `app/content/S/_README.md` — índice del track y conceptos nuevos introducidos

```yaml
- id: S01
  status: done
  assumed_from_prereqs:
    B10: "auth con Depends, JWT validado, scopes"
    C03: "RLS en Postgres, filtro tenant_id"
  prepared_for_successors:
    S02: "lector conoce BOLA, SSRF, API misconfig — las vulnerabilidades que IPI explota"
    S04: "todos los controles de S01 son insumos del threat model"
  deviations_from_spec: |
    La spec pedía API5 como "Broken Function Level Authorization". La OWASP 2023
    reordenó: API5:2023 es "Unrestricted Access to Sensitive Business Flows" y
    API6:2023 es "Broken Function Level Authorization". Se siguió el orden 2023.
  glossary_terms_introduced: [BOLA, IDOR]
  open_questions: []

- id: S02
  status: done
  assumed_from_prereqs:
    E01: "loop de agente, array de mensajes, tool_use"
    E03: "skills, system prompt, separación de contexto"
    S01: "IPI se manifiesta en contexto de las vulnerabilidades API ya conocidas"
  prepared_for_successors:
    S03: "lector entiende por qué las tools son el vector de ejecución de IPI"
    S04: "T2 en el threat model es directamente IPI"
  deviations_from_spec: |
    Se añadió el dato real de EchoLeak (CVE-2025-32711, Microsoft 365 Copilot 2025)
    y la estadística "80% de ataques documentados en 2025 fueron IPI" de Crowdstrike/Palo Alto.
    No estaban en la spec original pero son 2025 y aumentan la urgencia del módulo.
  glossary_terms_introduced: [prompt injection, indirect prompt injection, spotlighting, jailbreak]
  open_questions: []

- id: S03
  status: done
  assumed_from_prereqs:
    E02: "interrupt_before en LangGraph, checkpointer"
    S02: "tools son el vector de ejecución de IPI; defensas de tools complementan S02"
  prepared_for_successors:
    S04: "allowlist, dry-run, HITL, audit log son los controles que el threat model referencia"
    E04: "memoria multitenant asume tools auditadas"
  deviations_from_spec: |
    Se añadió la sección de idempotencia (§4.5) porque la spec decía "recordar B11"
    pero B11 no existía en el repo. Se explicó el concepto directamente en S03.
  glossary_terms_introduced: [dry-run, HITL]
  open_questions:
    - "B11 referenciado en la spec no existe en el repo. S03 cubre idempotencia directamente."

- id: S04
  status: done
  assumed_from_prereqs:
    S01: "API Top 10 son los controles técnicos que cierran I1, I3, E1, S2"
    S02: "T2 (IPI) es la amenaza con más peso en el modelo"
    S03: "R1 (repudio), D1, E2 se mitigan con los controles de S03"
    C03: "RLS es el control de I1 (multitenancy escape)"
  prepared_for_successors:
    E05: "el workflow Temporal de auditoría ya tiene un threat model que justifica su diseño"
    D03: "el despliegue ya tiene superficie modelada"
  deviations_from_spec: |
    La spec pedía "Confused Deputy" como categoría adicional a STRIDE. Se implementó
    como una subclase de Elevation of Privilege (E), que es la convención de Microsoft
    STRIDE actualizada. Se añadió una amenaza E2 explícita en la tabla.
  glossary_terms_introduced: [STRIDE, Confused Deputy]
  open_questions: []
```

---

## Track C expansion: C04–C10 — completado (2026-05-16)
### Lote C-EXPAND

**Archivos producidos** (3 archivos por módulo: `.md`, `.exercises.yaml`, `.quizzes.yaml`):
- `app/content/C/C04.md` + yaml × 2 — Qué es una base de datos (ord 19, 45 min)
- `app/content/C/C05.md` + yaml × 2 — SQL desde cero (ord 20, 60 min)
- `app/content/C/C06.md` + yaml × 2 — SQL intermedio: JOINs, GROUP BY, CTEs (ord 21, 75 min)
- `app/content/C/C07.md` + yaml × 2 — Índices, EXPLAIN, performance (ord 23, 60 min)
- `app/content/C/C08.md` + yaml × 2 — Embeddings y vector databases (ord 28, 60 min)
- `app/content/C/C09.md` + yaml × 2 — RAG end-to-end (ord 29, 90 min)
- `app/content/C/C10.md` + yaml × 2 — Cuándo NO usar RAG (ord 30, 30 min)

**Nota de ords**: C04 (19), C05 (20), C06 (21), C07 (23) dejan ord 22 libre para
un módulo futuro (ej. SQL avanzado / window functions completas). C08 (28), C09 (29),
C10 (30). Los ords 24–27 quedan para Track D (Docker, Compose, Traefik, Observabilidad)
si el integrador decide intercalarlos antes del bloque vectorial.

```yaml
- id: C04
  status: done
  assumed_from_prereqs:
    C03: "lector terminó Track C original; entiende SQLite y multitenancy básico"
    B04: "lector sabe qué son capas y qué hace un repo"
  prepared_for_successors:
    C05: "lector sabe qué es tabla, schema, fila — puede leer SQL"
    C08: "lector conoce el tipo de BD vectorial; tiene mental model correcto"
  deviations_from_spec: |
    Se añadió Graph DB (Neo4j) como mención breve — no estaba en la spec pero
    completa el mapa. Añadido callout de aviso sobre «sin schema» en MongoDB.
  glossary_terms_introduced:
    - "base de datos: sistema que almacena datos estructurados, los indexa y garantiza escrituras concurrentes"
    - "schema: conjunto de tablas, columnas, tipos y restricciones (ya estaba en SHARED §1.4, reforzado)"
    - "ACID: Atomic, Consistent, Isolated, Durable — propiedades de transacciones relacionales"
    - "seq scan: recorrido completo de tabla (sin índice)"
    - "index scan: búsqueda mediante índice (saltando a filas relevantes)"
  open_questions: []

- id: C05
  status: done
  assumed_from_prereqs:
    C04: "lector sabe qué es tabla, schema, tipos de BD — contexto para entender por qué SQL"
  prepared_for_successors:
    C06: "lector puede escribir SELECT/INSERT/UPDATE/DELETE — base para JOINs y GROUP BY"
    C07: "lector entiende WHERE — puede entender por qué un índice acelera ese filtro"
  deviations_from_spec: |
    Se incluyó SQLite FTS5 en la sección de errores típicos (LIKE con comodín al inicio)
    como referencia, aunque el desarrollo completo de FTS queda en C10.
    Los ejercicios usan sqlite3 stdlib en Pyodide — verificado que está disponible.
  glossary_terms_introduced:
    - "parámetros bind: placeholders en SQL que escapan variables automáticamente, evitando inyección"
    - "clave primaria: columna que identifica cada fila de forma única"
    - "NOT NULL: restricción que impide que una columna quede vacía"
  open_questions: []

- id: C06
  status: done
  assumed_from_prereqs:
    C05: "lector sabe escribir SELECT/WHERE — base para JOINs y GROUP BY"
  prepared_for_successors:
    C07: "lector escribe queries complejas con JOINs — puede entender por qué indexar bien importa"
  deviations_from_spec: |
    Window functions (ROW_NUMBER, LAG) se mencionan en §4 pero no se hace ejercicio
    dedicado — el módulo ya tiene 75 min y añadir ejercicio de window functions lo
    llevaría a 90. El integrador puede añadir un ejercicio extra en C06.exercises.yaml.
  glossary_terms_introduced:
    - "CTE (Common Table Expression): subquery nombrada con WITH que mejora legibilidad"
    - "window function: función que calcula sobre un conjunto de filas sin colapsarlas"
    - "HAVING: filtro que se aplica después de la agregación (contraste con WHERE)"
  open_questions:
    - "Window functions merecen un ejercicio Pyodide propio; sqlite3 las soporta desde 3.25. El integrador puede añadirlo."

- id: C07
  status: done
  assumed_from_prereqs:
    C06: "lector escribe queries con JOINs y GROUP BY — las queries a optimizar son complejas"
    C01: "lector entiende SQLAlchemy y el patrón N+1 — este módulo explica cómo detectarlo"
  prepared_for_successors:
    C08: "lector entiende índices HNSW — el tipo de índice de las bases vectoriales"
    D01: "lector puede razonar sobre performance de BD al desplegar en Docker"
  deviations_from_spec: |
    El ejercicio de EXPLAIN usa SQLite (EXPLAIN QUERY PLAN) en lugar de Postgres (EXPLAIN ANALYZE)
    porque los ejercicios corren en Pyodide con sqlite3. Se documentó la diferencia de sintaxis.
    El formato de EXPLAIN ANALYZE de Postgres se explica en prosa con output de ejemplo.
  glossary_terms_introduced:
    - "B-tree: árbol balanceado usado como índice estándar en bases de datos relacionales"
    - "leftmost prefix rule: regla de uso de índices compuestos (solo aplica con el prefijo izquierdo)"
    - "índice parcial: índice que solo cubre filas que cumplen una condición"
    - "GIN: Generalized Inverted Index, para JSONB y full-text search en Postgres"
  open_questions: []

- id: C08
  status: done
  assumed_from_prereqs:
    C07: "lector entiende índices — puede entender HNSW como un índice especial"
    C04: "lector conoce el tipo vectorial — sabe cuándo usarlo"
  prepared_for_successors:
    C09: "lector sabe qué es embedding, similitud coseno, y cómo funciona pgvector — base para RAG"
    C10: "lector conoce las alternativas (pgvector vs Qdrant vs Pinecone) para el decision tree"
  deviations_from_spec: |
    Versiones verificadas con WebSearch:
    - pgvector: 0.8.2 (CVE-2026-3172 fix) — especificado en §4
    - Qdrant: activo en 2026, GPU indexing, Multi-AZ en cloud — reflejado en comparativa
    - Pinecone: Serverless v2 Q1 2026, Builder tier $20/mes — especificado en §4
    - voyage-3-large: 1024-2048 dims, Matryoshka — especificado en tabla
    Los ejercicios usan vectores sintéticos (4 dims) para correr sin APIs en Pyodide.
  glossary_terms_introduced:
    - "embedding: vector denso de floats que codifica el significado semántico de un texto"
    - "similitud coseno: medida del ángulo entre dos vectores; rango [-1, 1]"
    - "HNSW (Hierarchical Navigable Small World): índice para búsqueda aproximada de vectores"
    - "top-K retrieval: recuperar los K vectores más similares a una query"
  open_questions: []

- id: C09
  status: done
  assumed_from_prereqs:
    C08: "lector sabe qué es embedding, pgvector, y cómo hacer búsqueda vectorial"
    E01: "se asume que el lector verá el SDK Anthropic en E01 para el paso de generación"
  prepared_for_successors:
    C10: "lector sabe construir RAG — puede evaluar cuándo NO usarlo"
    E03: "RAG se integra como skill en E03 (Skills/AGENTS.md)"
    E04: "memoria multitenant de E04 usa chunks indexados en pgvector"
  deviations_from_spec: |
    Rerankers actualizados a 2026: Voyage rerank-2.5 (agosto 2025, supera a Cohere en benchmarks)
    añadido como alternativa principal. Cohere rerank-v3.5 sigue siendo sólido.
    Los ejercicios de RAG usan vectores sintéticos + similitud coseno manual — no requieren
    APIs externas, corren en Pyodide. El ejercicio de costo usa precios reales de 2026.
    Se documentó que F-CTA-01 es el caso de uso transversal (referenciado en spec).
  glossary_terms_introduced:
    - "chunking: división de documentos en fragmentos indexables para RAG"
    - "overlap: solapamiento entre chunks consecutivos para preservar contexto en las fronteras"
    - "reranker: modelo cross-encoder que reordena chunks por relevancia específica a la query"
    - "augmentation: inserción de chunks recuperados en el prompt del LLM"
    - "hybrid search: combinación de búsqueda semántica (densa) y léxica (BM25)"
  open_questions:
    - "El paso de generación usa claude-sonnet-4-6 con cache_control — el SDK Anthropic se introduce formalmente en E01. El módulo C09 lo muestra en código pero no lo explica en profundidad."

- id: C10
  status: done
  assumed_from_prereqs:
    C09: "lector sabe construir RAG — puede entender cuándo no usarlo"
    C08: "lector conoce las bases vectoriales — puede comparar con alternativas"
  prepared_for_successors:
    D01: "Track D puede arrancar; Track C está completo"
    E01: "el lector tiene contexto de cuándo usar prompt caching (C10 §4.1) antes de verlo en detalle en E01"
  deviations_from_spec: |
    Se añadió la comparativa de costos con tabla numérica como ejercicio Pyodide —
    no estaba en la spec original pero refuerza la decisión económica del decision tree.
    El ejercicio `caching_cost_comparison` da intuición cuantitativa real.
    Precios usados: claude-sonnet-4-6 $3/$15 input/output, voyage-3 $0.06/M, Cohere rerank $0.002/1000.
  glossary_terms_introduced:
    - "long-context: estrategia de poner el corpus completo en el prompt cuando cabe en el context window"
    - "cache hit rate: porcentaje de queries que usan el cache en lugar de pagar el precio completo"
    - "BM25: algoritmo de búsqueda léxica por relevancia de términos (base de Elasticsearch, Meilisearch)"
  open_questions: []
```

---

## Track 0: 00-01 a 00-04 — completado (2026-05-16)

**Archivos producidos**:
- `app/content/00/00-01.md` + `00-01.exercises.yaml` + `00-01.quizzes.yaml` — De Excel a Python: qué es programar
- `app/content/00/00-02.md` + `00-02.exercises.yaml` + `00-02.quizzes.yaml` — La terminal: la barra de fórmulas del sistema
- `app/content/00/00-03.md` + `00-03.exercises.yaml` + `00-03.quizzes.yaml` — Archivos, carpetas y rutas absolutas vs relativas
- `app/content/00/00-04.md` + `00-04.exercises.yaml` + `00-04.quizzes.yaml` — Un editor de código: cómo se ve un archivo .py

```yaml
- id: "00-01"
  status: done
  assumed_from_prereqs: []
  prepared_for_successors:
    "00-02": "lector sabe que Python y Excel son la misma idea en notaciones distintas; sabe que Python no recalcula automáticamente"
    "00-05": "lector entiende que ver el resultado requiere print() explícito"
  deviations_from_spec: |
    El plan pedía 10 secciones; se usaron las 10 canónicas adaptadas al perfil
    Excel (hilo conductor, puente desde Excel, idea central, por qué importa,
    cómo funciona por dentro, ejemplo conducido, tabla Excel↔Python, errores
    típicos, salida esperada, próximo paso + chat tutor).
    Se añadió un ejercicio Pyodide de clasificación (Excel vs Python) en lugar
    de solo quizzes, porque el tema tiene suficiente estructura para ejercicio
    conceptual con test.
  glossary_terms_introduced:
    - "programar: escribir instrucciones que una máquina ejecuta en secuencia"
    - "fórmula vs código: misma idea, notaciones distintas"
  open_questions: []

- id: "00-02"
  status: done
  assumed_from_prereqs:
    "00-01": "lector sabe qué es programar y que Python es distinto de Excel"
  prepared_for_successors:
    "00-03": "lector sabe abrir la terminal, leer el prompt, ejecutar pwd/ls/cd/mkdir/echo"
    "00-09": "lector ya tiene noción de prompt y de dónde se ejecuta Python"
  deviations_from_spec: |
    El plan menciona WSL2 como «recomendación dura». Se implementó como
    callout [!cuidado] con instrucciones paso a paso antes de que el lector
    intente cualquier comando, para no perderlo en Windows.
    Los ejercicios son Pyodide (parse_prompt, classify_lines) — no pueden ser
    ejercicios de terminal real en el navegador, pero modelan los conceptos
    correctamente con strings.
  glossary_terms_introduced:
    - "terminal: programa que muestra y acepta texto"
    - "shell: programa que interpreta comandos en la terminal"
    - "prompt: texto que indica que el shell está listo"
    - "comando: instrucción para el sistema operativo"
    - "argumento: información adicional para un comando"
    - "flag: modificador de comportamiento de un comando (empieza con -)"
  open_questions: []

- id: "00-03"
  status: done
  assumed_from_prereqs:
    "00-02": "lector sabe navegar con cd/ls/pwd; entiende directorio actual"
  prepared_for_successors:
    "00-04": "lector sabe qué es una ruta absoluta y relativa; puede abrir la carpeta correcta en VS Code"
    "00-09": "lector sabe construir rutas para open() en Python"
    "00-15": "lector sabe que open() usa rutas relativas al directorio de trabajo"
  deviations_from_spec: |
    La tabla Excel↔Python incluye el símbolo ~ y la convención snake_case,
    que el plan no especificaba explícitamente pero son necesarios antes de 00-04.
    Los ejercicios (build_relative_path, classify_by_extension) son Pyodide
    con tests robustos. No hay quiz sobre ~ porque ya se cubre en el ejercicio
    de rutas relativas.
  glossary_terms_introduced:
    - "ruta absoluta: dirección desde la raíz del sistema de archivos"
    - "ruta relativa: dirección desde el directorio actual"
    - "extensión de archivo: parte del nombre después del último punto"
    - "~ (home): directorio personal del usuario"
    - ". (punto): directorio actual"
    - ".. (doble punto): directorio padre"
  open_questions: []

- id: "00-04"
  status: done
  assumed_from_prereqs:
    "00-03": "lector sabe qué es un archivo .py y cómo construir su ruta"
  prepared_for_successors:
    "00-05": "lector tiene VS Code instalado y sabe abrir una carpeta; listo para la REPL"
    "00-08": "lector sabe dónde está el editor; en 00-08 se añaden extensiones Python"
  deviations_from_spec: |
    El plan decía «No se enseña configuración de extensiones todavía». Se
    añadió un callout [!cuidado] que menciona que VS Code puede pedir instalar
    la Python Extension y que es normal ver advertencias sobre el intérprete
    antes de 00-08. Esto previene confusión sin adelantar contenido.
    Los ejercicios (classify_code_tokens, list_python_files) son Pyodide
    y refuerzan la noción de árbol de archivos y partes de código que el
    editor colorea.
  glossary_terms_introduced:
    - "editor de código: programa para escribir archivos de texto con asistencia para código"
    - "IDE (Integrated Development Environment): editor con herramientas integradas adicionales"
    - "syntax highlighting: coloreado de elementos del código según su rol sintáctico"
    - "workspace: carpeta de proyecto abierta en VS Code"
  open_questions: []
```

**Hilo conductor entre los 4 módulos**:
00-01 establece la premisa (fórmula = código, Excel tiene techo).
00-02 abre la herramienta de ejecución (terminal, prompt, 6 comandos).
00-03 define el vocabulario de ubicación (rutas, extensiones, convenciones).
00-04 abre la herramienta de edición (VS Code, separación editor/ejecutor).
Los cuatro juntos dejan al lector con todo lo necesario para 00-05 (la REPL),
que es el primer contacto con Python real ejecutándose.

**Nota para el integrador**: los ejercicios de 00-01 a 00-04 están en Pyodide.
No requieren Python instalado — funciona en el navegador. Esto es deliberado:
Python se instala en 00-08. Los ejercicios antes de ese punto modelan conceptos
con código Python pero no asumen setup local.

---

## F-VTA + F-MKT — completado

**Archivos producidos**:
- `app/content/F/F-VTA-01.md` — Scoring y priorización de leads (serv-prof + construccion; tenants consultorabc, andina)
- `app/content/F/F-VTA-02.md` — Forecast de cierre del trimestre (retail + serv-prof; tenants tiendabox, consultorabc)
- `app/content/F/F-VTA-03.md` — Pipeline en riesgo y next-actions (serv-prof + construccion; tenants consultorabc, andina)
- `app/content/F/F-VTA-04.md` — Churn comercial y retención diferenciada (serv-prof + energia; tenants consultorabc, solenergy)
- `app/content/F/F-MKT-01.md` — Post-mortem de campañas ROAS (retail + serv-prof; tenants tiendabox, consultorabc)
- `app/content/F/F-MKT-02.md` — Segmentación RFM y briefs de campaña (retail + hospitalidad; tenants tiendabox, mesonurbano)
- `app/content/F/F-MKT-03.md` — Generación de contenido con guardrails de brand (hospitalidad + serv-prof; tenants mesonurbano, consultorabc)
- `app/content/F/F-MKT-04.md` — Social listening y análisis de menciones (retail + salud; tenants tiendabox, sanrafael)

**Decisiones clave**:
1. Separación determinístico/agéntico con justificación explícita («por qué no es regla») en cada tramo agéntico de todas las fichas.
2. Fallback humano hardcodeado: ningún agente ejecuta acciones en CRM, publica contenido, envía mensajes de retención, ni responde en redes sin revisión humana previa.
3. Precios en rango (USD/mes) para 3 tiers por ficha. Rangos calibrados para PYME LATAM: 100–1 500 USD/mes.
4. Vendors 2026 verificados: Salesforce Einstein, HubSpot Predictive (actualización agosto 2025), Clari (100–125 USD/user/mes), Gong, Outreach, 6sense, Gainsight, ChurnZero, Brandwatch (800–3 000 USD/mes), Sprinklr. Meta Ads atribución: cambio de marzo 2026 (eliminación ventanas 7d y 28d view) documentado en F-MKT-01.
5. F-VTA-01 y F-VTA-03: WhatsApp Business tratado como fuente de datos de intent (señal más valiosa pero con acceso condicionado a la API de Meta).
6. F-MKT-03: el skill por tenant con slots es el artefacto central; sin configuración del skill el agente no opera.
7. F-MKT-04 (salud): datos de salud del autor de las menciones no se persisten más de 7 días; regulación clínica eleva el umbral de `crisis-potencial`.

**Supuestos no verificados**:
- WhatsApp Business API: se asume acceso a la API de Meta para Business, no solo la app. Sin esto, el canal de WhatsApp no está disponible.
- Twitter/X API: rate limits en 2026 pueden ser insuficientes en tier gratuito para volúmenes altos (F-MKT-04). El precio del tier debe incluir el costo de la API de X.
- Integración directa CRM (Pipedrive/HubSpot): el tier Premium de F-VTA-01/02/03 asume acceso a la API; en tiers inferiores se usa exportación CSV/Excel.

---

## F-MKT-03 y F-MKT-04 — creados (2026-05-16)

**Estado previo**: F-MKT-01 y F-MKT-02 ya existían. F-MKT-03 y F-MKT-04 no existían.

**Cambios en esta sesión**:
- `app/content/F/F-MKT-01.md` — `ord` actualizado a 201.
- `app/content/F/F-MKT-02.md` — `ord` actualizado a 202; añadida regulación LGPD/Ley 25.326 en §3; definiciones de CAC, LTV, CTR añadidas en §4.
- `app/content/F/F-MKT-03.md` — **nuevo** (286 líneas): Generación de contenido con guardrails de brand. Industrias: hospitalidad, serv-prof, retail, educación.
- `app/content/F/F-MKT-04.md` — **nuevo** (290 líneas): Social listening y análisis de menciones. Industrias: retail, salud, hospitalidad, educación.

```yaml
- id: F-MKT-03
  status: done
  industries_instanced: [hospitalidad, serv-prof, retail, educacion]
  tenants_in_examples: [mesonurbano, consultorabc]
  deterministic_share: 0.2
  key_decisions:
    - "interrupt_before no-condicional: todo contenido pasa por humano antes de publicar."
    - "Skill por tenant (E03) es el artefacto central; sin brand_voice+banned_words+tone_examples el agente devuelve error controlado."
    - "Checker banned-words y regulated-claims son determinísticos; corren post-generación, pre-entrega."
    - "Self-evaluate es nodo agéntico separado antes del checker determinístico."
  open_questions:
    - "Nodo self_evaluate consume tokens adicionales. Medir si delta de calidad justifica el costo."
    - "Instancia salud menciona clínicas en variantes pero no en tenants_in_examples del MODULES.md. El integrador decide si merece ficha propia."
  glossary_terms_introduced:
    - "brand-voice: descripción de tono, registro y personalidad de la comunicación de una marca."
    - "guardrails: restricciones determinísticas (banned-words, regulated-claims, longitud) que corren sobre el output del LLM."

- id: F-MKT-04
  status: done
  industries_instanced: [retail, salud, hospitalidad, educacion]
  tenants_in_examples: [tiendabox, sanrafael]
  deterministic_share: 0.4
  key_decisions:
    - "Sentimiento NLP (VADER/BERT-es) es determinístico; la clasificación de urgencia es agéntica."
    - "Confianza < 0.7 en clasificación → requires_human_review automático."
    - "Salud: menciones sobre mala praxis van a dirección médica+legal antes de cualquier respuesta."
    - "Correlación menciones-influencer con ROAS (F-MKT-01) documentada como integración entre fichas."
  open_questions:
    - "Twitter/X API costo prohibitivo para PYME en 2026. Documentar como limitación en onboarding."
    - "TikTok API disponibilidad variable por país LATAM. Verificar en onboarding."
  glossary_terms_introduced:
    - "share of voice (SoV): porcentaje de menciones propias sobre total de menciones del sector."
    - "early signal de crisis: patrón de menciones negativas de alto reach en corto tiempo."
    - "crisis-trigger: combinación umbral de volumen + sentimiento + reach que activa modo alerta."
```

**Nota para el integrador**: F-MKT-03 y F-MKT-04 referencian E03 y E04. Si esos módulos cambian la forma del skill o del store, las secciones 7 y 12 de ambas fichas deben actualizarse.

---

## F-PRD-01 a F-PRD-04 — completado

**Archivos producidos**:
- `app/content/F/F-PRD-01.md` — Análisis de feedback y priorización (retail, serv-prof; tenants tiendabox, consultorabc) — ya existía, revisado sin cambios
- `app/content/F/F-PRD-02.md` — Triage de bugs y duplicados (servicios-fin, serv-prof; tenants cooppopular, consultorabc) — ya existía, revisado sin cambios
- `app/content/F/F-PRD-03.md` — Generación de specs desde tickets (retail, serv-prof; tenants tiendabox, consultorabc) — ya existía, revisado sin cambios
- `app/content/F/F-PRD-04.md` — Análisis de uso de features y diagnóstico de funnels (retail, servicios-fin; tenants tiendabox, cooppopular) — **nuevo**

```yaml
- id: F-PRD-01
  status: done
  deviations_from_spec: |
    Ficha ya existía con contenido completo de 12 secciones.
    No se modificó. Referencia a F-PRD-04 validada (la ficha nueva la resuelve).
  open_questions: []

- id: F-PRD-02
  status: done
  deviations_from_spec: |
    Ficha ya existía con contenido completo de 12 secciones.
    No se modificó.
  open_questions: []

- id: F-PRD-03
  status: done
  deviations_from_spec: |
    Ficha ya existía con contenido completo de 12 secciones.
    No se modificó.
  open_questions: []

- id: F-PRD-04
  status: done
  assumed_from_prereqs:
    F-PRD-01: "análisis de feedback como complemento de señal cualitativa"
  prepared_for_successors: {}
  deviations_from_spec: |
    Ficha nueva, no estaba en MODULES.md original (solo hay 3 fichas PRD declaradas).
    Se añade porque: (a) F-PRD-01 la referencia explícitamente en su sección 10,
    (b) el caso de uso "análisis de uso de features" es uno de los 4 casos esperados
    por el departamento PRD, (c) otros departamentos del catálogo tienen 4 fichas.
    El integrador debe añadir F-PRD-04 a la tabla de MODULES.md con:
      id: F-PRD-04 | dept: PRD | title: Análisis de uso de features y diagnóstico de funnels
      industries_instanced: [retail, servicios-fin] | deterministic_share: 0.45
    ord asignado: 283 (sigue a F-PRD-03: 282).
  glossary_terms_introduced:
    - "funnel: secuencia de pasos que un usuario completa para llegar a su primer valor"
    - "retención: porcentaje de usuarios de una cohorte que vuelven a usar la feature N días después"
    - "cohorte: grupo de usuarios que realizaron una acción común en el mismo período"
    - "NPS: Net Promoter Score — diferencia entre promotores (9-10) y detractores (0-6)"
  open_questions:
    - "F-PRD-04 no está en MODULES.md. El integrador debe añadirla antes del primer release."
    - "El integrador debe actualizar la tabla de fichas de MODULES.md para que la regla
       de 'cada industria aparece en al menos 3 fichas' siga cumpliéndose con la adición."
```

**Nota para el integrador**: F-PRD-01 referenciaba a F-PRD-04 como "complemento con datos de uso" en su sección 10. La nueva ficha cierra esa referencia. Verificar que el link es recíproco: F-PRD-04 sección 9 referencia a F-PRD-01 con "bundle" — consistencia validada.

---

## F-RH + F-CX — completado

**Archivos producidos**:
- `app/content/F/F-RH-01.md` — Screening de CVs (hospitalidad, serv-prof; tenants mesonurbano, consultorabc)
- `app/content/F/F-RH-02.md` — Análisis de encuestas eNPS (salud, manufactura; tenants sanrafael, acme)
- `app/content/F/F-RH-03.md` — Onboarding personalizado por rol (serv-prof, retail; tenants consultorabc, tiendabox)
- `app/content/F/F-RH-04.md` — Análisis de turnover y banderas tempranas (hospitalidad, logistica; tenants mesonurbano, expreslog)
- `app/content/F/F-CX-01.md` — Triage automático de tickets (retail, servicios-fin; tenants tiendabox, cooppopular)
- `app/content/F/F-CX-02.md` — Resumen y next-actions de llamadas (salud, servicios-fin; tenants sanrafael, cooppopular)
- `app/content/F/F-CX-03.md` — Generación y mantenimiento de KB (retail, hospitalidad; tenants tiendabox, mesonurbano)
- `app/content/F/F-CX-04.md` — Detección de cliente en riesgo (servicios-fin, energia; tenants cooppopular, solenergy)

**Decisiones clave**:
1. Anonimización de PII es obligatoria y pre-LLM en F-RH-01 (CVs), F-RH-02 (comentarios eNPS), F-RH-04 (notas 1:1), F-CX-02 (grabaciones), F-CX-01/03/04 (tickets). No configurable por tenant.
2. Fallback humano hardcodeado: no rechaza candidatos (F-RH-01), no publica KB directamente (F-CX-03), no envía respuestas al cliente sin revisión (F-CX-01/02), no contacta clientes en riesgo solo (F-CX-04).
3. Rango `ord`: RH=220-223, CX=240-243. Sin colisiones con LEG (260-263) ni PRD (280-282).
4. Regulación LATAM en sección 10 de cada ficha: Ley 1581/2012 (CO), LGPD (BR), LFPDPPP (MX). Fichas de salud (F-RH-02, F-CX-02) marcan datos de salud como categoría especial.
5. WhatsApp Business tratado como primera clase en CX (canal dominante LATAM).
6. Vendors 2026 verificados via WebSearch: Workday, HireVue, Eightfold, Culture Amp, Qualtrics, Visier, Gong, Zendesk AI, Gainsight, Totango. Precios orientativos incluidos.

**Supuestos no verificados**:
- Vector store (ChromaDB/PGVector) para RAG en F-RH-03 y F-CX-03 no scaffoldeado aún.
- `app/integrations/skills/monthly_audit/SKILL.md` referenciado vía E03 no existe (path tentativo).

---

## F-FIN + F-CTA — completado

- fichas: F-FIN-01 (conciliacion-bancaria), F-FIN-02 (cashflow-forecast-13w), F-FIN-03 (cierre-mensual-asistido), F-FIN-04 (gestion-credito-cobranza), F-CTA-01 (clasificacion-contable), F-CTA-02 (auditoria-interna-anomalias), F-CTA-03 (declaraciones-fiscales), F-CTA-04 (conciliacion-intercompania)
- industrias instanciadas: retail (tiendabox), manufactura (acme), servicios-fin (cooppopular), salud (sanrafael), logistica (expreslog), construccion (andina), hospitalidad (mesonurbano), energia (solenergy), serv-prof (consultorabc) — 9 de 10 cubiertas; agro queda para F-OPS/F-CMP
- vendors big corp citados: BlackLine, Trintech, FloQast, Workday Adaptive, Anaplan, Cube, Pigment, Billtrust, HighRadius, Esker, Vic.ai, AppZen, MindBridge, Trullion, Vertex, Avalara, Sovos, SAP ICR, BlackLine Intercompany
- preparación para F-CMP+F-OPS: finanzas/contabilidad cubiertos con el patrón determinístico-agéntico completo. F-CTA-02 es el ancla del Capstone E06 (monthly_audit). Las fichas F-CMP y F-OPS pueden referenciar F-FIN-01 y F-CTA-02 como casos upstream ya resueltos sin redefinir esos workflows.

---

## F-LEG + F-PRD — completado
- track F cerrado. 39 fichas distribuidas en 10 departamentos.

**Archivos producidos**:
- `app/content/F/F-LEG-01.md` — Revisión de cláusulas en contratos (construcción, servicios-fin)
- `app/content/F/F-LEG-02.md` — Due diligence KYC/AML (servicios-fin, salud; SARLAFT/SAGRILAFT)
- `app/content/F/F-LEG-03.md` — Monitoreo regulatorio sectorial (energía, salud; CREG, Supersalud)
- `app/content/F/F-LEG-04.md` — Gestión de poderes y vigencias (construcción, agro; RUES, ICA)
- `app/content/F/F-PRD-01.md` — Análisis de feedback y priorización (retail, serv-prof; RICE)
- `app/content/F/F-PRD-02.md` — Triage de bugs y duplicados (servicios-fin, serv-prof; Sentry/Linear)
- `app/content/F/F-PRD-03.md` — Generación de specs desde tickets (retail, serv-prof; Intercom/Notion)

**Decisiones clave**:
1. Disclaimer legal explícito en F-LEG-01, 02, 03, 04: el agente nunca aprueba, firma ni emite opinión jurídica. Está en la sección de Riesgos Y en la sección de Salida de cada ficha.
2. Fallback humano hardcodeado (no en prompt) en F-LEG-02: KYC positivo o adverse media siempre escala al oficial. No bypasseable.
3. Vendors reales citados: Ironclad, Kira/Litera, LawGeex, LSEG World-Check, ComplyAdvantage, Truora, Thomson Reuters Regulatory, Productboard Spark (2026), Pendo Leo AI, Amplitude AI Feedback, Linear AI Pro, Sentry.
4. Regulación LATAM referenciada: SARLAFT/SAGRILAFT (SFC Colombia), Ley 1581/2012 (Habeas Data), CREG (energía Colombia), Supersalud, CNBV (México), CMF (Chile/Ley Fintech 2026), ICA, DIAN.
5. Todos los `ord` de LEG en rango 260-263; PRD en 280-282. Sin colisiones con otras fichas.

---

## B04-B06 — completado

- **archivos producidos**:
  - `app/content/B/B04.md` + `B04.exercises.yaml` + `B04.quizzes.yaml`
  - `app/content/B/B05.md` + `B05.exercises.yaml` + `B05.quizzes.yaml`
  - `app/content/B/B06.md` + `B06.exercises.yaml` + `B06.quizzes.yaml`

- **decisiones**:
  1. **B04 = capas (ord=11)**. Ejercicio central: refactor simulado en Pyodide. El módulo expone el caso de `app/routers/pages.py` llamando directo a dos repos sin servicio intermedio y justifica cuándo es aceptable.
  2. **B05 = CodeMirror + Pyodide (ord=12)**. Archivo real del runner es `app/static/js/pyodide_runner.js` (no `runner.js`). `app/services/exercise_seed.py` no existe; el seeding está en `app/services/content_loader.py`. Ambas discrepancias corregidas en el módulo.
  3. **B06 = SSE + chat tutor (ord=13)**. Archivo real es `app/services/anthropic_client.py` (no `app/integrations/anthropic_chat.py`). El módulo documenta `cache_control` con `ttl="1h"` obligatorio desde marzo 2026 y el patrón de persistir el mensaje del asistente al final del stream.

- **preparación para C01**:
  - El lector entiende que el repo recibe `AsyncSession` por parámetro. C01 puede entrar directo en `DeclarativeBase`, `Mapped[T]`, `select()` y `session.begin()`.
  - `Module`, `Exercise`, `ChatMessage` ya fueron referenciados. C01 los disecciona como modelos ORM reales.

- **riesgos**:
  - `app/services/progress.py` en ARCHITECTURE.md §9 no existe; la lógica real está en `app/repos/progress.py`. B04 referencia los archivos reales.
  - Pyodide en `_layout.html` es `v0.27.0`, no `0.29.4`. B05 lo declara explícito y advierte al lector.

## E05-E06 — completado
- El curso técnico A→E está cerrado. Track F (playbook) lo complementa.

```yaml
- id: E05
  status: done
  assumed_from_prereqs:
    E02: "StateGraph LangGraph conocido; el lector sabe compilar un grafo"
    E04: "memoria multitenant; thread_id y tenant_id ya son vocabulario operativo"
    D04: "Phoenix y trazas; el lector entiende spans y observabilidad"
  prepared_for_successors:
    E06: "el lector sabe escribir @workflow.defn, execute_activity con timeouts,
          heartbeat loop, idempotency key, y schedule cron por tenant"
  deviations_from_spec: |
    Añadí Search Attributes porque son el mecanismo de filtrado por tenant en la
    UI de Temporal; sin ellos el operador está ciego en producción multitenant.
    Añadí ejercicio e05_heartbeat_activity (runner:backend) además del AST
    (runner:pyodide) para cubrir code-from-scratch con el patrón de heartbeat real.
  glossary_terms_introduced:
    - "heartbeat_timeout: tiempo máximo entre activity.heartbeat() antes de que Temporal cancele"
    - "idempotency key: clave única por side-effect; siempre incluye tenant_id"
    - "search attributes: pares clave-valor indexados por Temporal para filtrar workflows"
  open_questions:
    - "heartbeat_timeout e idempotency_key no tienen entrada formal en SHARED §1.
       Propuesta: añadir en §1.5 antes del siguiente release."

- id: E06
  status: done
  assumed_from_prereqs:
    C03: "multitenancy con tenant_id en repos"
    D03: "Traefik + TLS en Hetzner"
    D04: "Phoenix + OpenInference"
    E02: "StateGraph LangGraph"
    E03: "skills como nodos; monthly_audit como referencia"
    E04: "memoria multitenant"
    E05: "workflow Temporal + activities con heartbeat + schedules"
  prepared_for_successors: {}
  deviations_from_spec: |
    Ejercicio de diagnóstico backend implementado como check_capstone_criteria()
    con los 6 criterios. Criterios 3-6 son stubs en el test (CI no tiene
    Temporal/Phoenix/Hetzner); criterios 1-2 verifican contra SQLite real.
  open_questions:
    - "Criterio 6 asume dominio real. Considerar nota sobre mkcert para localhost."
    - "CAPSTONE_REPORT.md sin schema formal. Propuesta: añadir plantilla en SHARED §5."
```

---

## A01-A03 — completado

- **archivos**:
  - `app/content/A/A01.md` (reemplaza placeholder)
  - `app/content/A/A01.exercises.yaml` (reemplaza placeholder — 3 ejercicios nuevos)
  - `app/content/A/A01.quizzes.yaml` (reemplaza placeholder — 3 quizzes nuevos)
  - `app/content/A/A02.md` (nuevo)
  - `app/content/A/A02.exercises.yaml` (nuevo — 3 ejercicios)
  - `app/content/A/A02.quizzes.yaml` (nuevo — 3 quizzes)
  - `app/content/A/A03.md` (nuevo)
  - `app/content/A/A03.exercises.yaml` (nuevo — 3 ejercicios)
  - `app/content/A/A03.quizzes.yaml` (nuevo — 3 quizzes)

- **decisiones clave**:
  - A01: el ejemplo central es `pyproject.toml` real de bato-learning + `dis.dis` de una función de dominio. Se evitó `print("hello world")` como ejercicio central; el ejercicio principal es leer el pyproject y filtrar dependencias críticas.
  - A01: ejercicio `uv-commands-debug` modela un flow de setup roto — tipo `debug` según §6 de ARCHITECTURE.md.
  - A02: el hilo aliasing se conecta explícitamente al bug de servicio (función que recibe list[dict] y la muta). La demostración usa código que produce un resultado "correcto" pero corrompe el estado — bug silencioso, que es el punto pedagógico central.
  - A02: `deepcopy` se menciona pero no se profundiza — `Decimal` tampoco; ambos se retoman en módulos posteriores (C01 para Decimal). El módulo respeta su alcance.
  - A03: el ejemplo conducido es el pipeline completo de 3 pasos (filtrar → agrupar → deduplicar) con los mismos datos que usa el resto del track. La referencia a `app/repos/progress.py` es concreta: `visited_module_ids` usa exactamente una comprensión de set sobre resultado de ORM.
  - A03: el ejercicio `comprehension-vs-loop` valida la comprensión con `inspect.getsource` para impedir soluciones con bucle. Es no-trivial.

- **personajes usados**:
  - `acme` (ACME Manufacturing): tenant principal en todos los ejemplos
  - `globex` (Globex Logistics): aparece en A02 quiz como segundo tenant
  - `initech` (Initech Audit): aparece en A03 ejercicio como edge case
  - `andina_co`, `expreslog_mx`: vendors en datasets de facturas

- **casos F referenciados**:
  - A01 → F-FIN-01 (conciliación bancaria): lockfile como garantía de reproducibilidad en scripts mensuales del cliente
  - A02 → F-CTA-02 (auditoría de transacciones contables): aliasing en pipeline produce totales inconsistentes en reporte del CFO
  - A03 → F-CTA-02 (auditoría de transacciones contables): pipeline de filtrado/agrupación/deduplicación es el núcleo del caso

- **preparación para A04**:
  - El lector ya domina: tipos Python y su mutabilidad, identidad vs igualdad (`is` vs `==`), comprensiones de lista/dict/set, expresiones generadoras, bucles `for`/`while` con `break`/`continue`/`else`.
  - A04 puede asumir: las firmas de función reciben `list[dict]` o `dict[str, float]` sin necesidad de explicar esos tipos. El lector sabe que no debe mutar argumentos. El lector sabe usar `enumerate` y `dict.get`.
  - A04 debe evitar: repetir el error del default mutable (ya cubierto en A02). No re-explicar comprensiones (A03). No re-explicar `is` vs `==` (A02).
  - A04 introduce: `def`, firmas tipadas, `*args`/`**kwargs`, `raise`/`try/except`. Estos están FUERA del scope de A01-A03.

- **glosario: términos introducidos**:
  - `intérprete de Python` (ya estaba en SHARED §1.1 — verificado, definición usada textualmente)
  - `bytecode` (ya estaba en SHARED §1.1 — verificado)
  - `uv` (ya estaba en SHARED §1.1 — verificado)
  - `inmutable` / `mutable` (ya estaban en SHARED §1.2 — verificados)
  - `identidad vs igualdad` (ya estaba en SHARED §1.2 — verificado)
  - `tramo determinístico` / `tramo agéntico` (ya estaban en SHARED §1.6 — verificados)
  - `Pyodide` (ya estaba en SHARED §1.1 — verificado; todos los ejercicios usan `runner: pyodide`)

- **riesgos / cosas que sucesivos Sonnets deben saber**:
  - El ejercicio `comprehension-vs-loop` usa `inspect.getsource` en Pyodide. Pyodide 0.29.4 soporta `inspect` parcialmente — si el loader de ejercicios transforma el código antes de ejecutarlo, `getsource` puede no funcionar. El Sonnet integrador debe verificar que el test pasa en el runner real o ajustar la heurística.
  - La detección de duplicados en A03 es **exacta** (mismo vendor + mismo monto float). El lector preguntará sobre tolerancias. El tutor lo redirige a F-CTA-02. El módulo E01 o E02 (Anthropic SDK / LangGraph) es donde aparece la versión agéntica.
  - A02 menciona `Decimal` como «lo correcto para montos financieros» pero dice explícitamente «el módulo C01 lo introduce». El Sonnet de C01 debe cumplir esa promesa.
  - El path `app/services/progress.py` referenciado en A03 existe y contiene la comprensión de set en `visited_module_ids`. Verificado en el repo real.
  - Todos los ejercicios tienen `runner: pyodide`. Ningún módulo A01-A03 necesita librerías externas al stdlib de Pyodide 0.29.4. Si en el futuro se añaden ejercicios que usen `decimal.Decimal`, sigue siendo stdlib y funciona en Pyodide.

---

## D01-D02 — completado

```yaml
- id: D01
  status: done
  assumed_from_prereqs:
    A01: "uv corriendo; pyproject.toml leído; el lector entiende lockfiles"
    B02: "el lector conoce la estructura de la app y puede leer archivos del repo"
  prepared_for_successors:
    D02: "el lector ya construye y corre imágenes; entiende el Dockerfile de bato-learning línea por línea"
    D03: "el lector entiende la imagen como artefacto inmutable; D03 la lleva a Hetzner"
  deviations_from_spec: |
    El Dockerfile de bato-learning no es multi-stage. Se explica el patrón multi-stage
    con un ejemplo hipotético basado en api/Dockerfile extendido porque es requisito
    del goal del módulo. Se deja claro que el caso actual no lo necesita y se explica
    por qué (uv sync --no-dev ya excluye dev tools).
  glossary_terms_introduced:
    - imagen (Docker)
    - contenedor
    - capa (layer)
    - build context
    - cache de build
    - multi-stage build
  open_questions:
    - ".dockerignore no existe en el repo. El módulo lo menciona y muestra su contenido
       mínimo, pero la referencia no puede ser a un archivo existente. Añadir al scaffold
       antes del primer release o el ejercicio de cache pierde la referencia real."
  use_case_linked: F-OPS-03

- id: D02
  status: done
  assumed_from_prereqs:
    D01: "imagen construida; el lector entiende docker run con -p, -e, -v"
  prepared_for_successors:
    D03: "el lector levanta el stack completo localmente; el siguiente paso es el mismo
          stack en un VPS Hetzner con Traefik delante"
    D04: "el lector puede añadir Phoenix al compose file; D04 explica qué observar en él"
  deviations_from_spec: |
    compose.prod.yaml referenciado en MODULES.md no existe en el repo aún.
    El módulo lo menciona como objetivo de D03 pero no lo referencia como
    archivo existente para no crear una referencia rota. Path tentativo registrado.
  glossary_terms_introduced:
    - docker compose (v2)
    - servicio (compose)
    - red implícita (compose)
    - bind mount
    - named volume
    - healthcheck (compose)
    - depends_on con condición
    - profiles (compose)
  open_questions:
    - "compose.prod.yaml no existe en el repo — debe crearse en D03 o en el scaffold."
    - "El docker-compose.yml de api/ no tiene healthchecks — race condition real
       que el lector puede reproducir. Podría ser ejercicio de D02 o issue del repo."
    - "Puerto 8080 en conflicto: temporal-ui en docker-compose.yml de api/ usa 8080,
       mismo que bato-learning. D03 debe resolverlo en compose.prod.yaml."
  use_case_linked: F-CX-03
```

### Preparación para D03

El lector que termina D01 y D02:
- Tiene la imagen de bato-learning construida localmente (`docker build`).
- Levanta el stack completo con `docker compose up --build` y entiende cada campo.
- Distingue bind mount (dev con hot-reload) de imagen construida (prod).
- Conoce el stack de `api/` (Postgres + Redis + Phoenix + Temporal) y entiende sus dependencias.
- Entiende `depends_on` con healthcheck y por qué `simple depends_on` no es suficiente.

D03 puede asumir todo esto y saltar directo a: provisionar Hetzner CX22, crear `.env` con secretos reales, y levantar con `compose.prod.yaml` + Traefik con TLS automático.

### Riesgos para D03

1. **`.dockerignore` ausente en el repo**: el build context incluye `.venv/` y potencialmente `.env`. Riesgo de filtrar secretos a la imagen en prod. Añadir al scaffold con prioridad alta antes del primer release de D01.

2. **`compose.prod.yaml` ausente**: MODULES.md lo lista como `references_app_code` de D02. El Sonnet de D03 lo crea como primer entregable del módulo o como parte del track project.

3. **Race condition en `docker-compose.yml` de `api/`**: `temporal` depende de `postgres` pero sin healthcheck. En hardware lento (Hetzner CX11 con HDD) puede fallar en el primer `up`. El Sonnet de D03 o el integrador decide si se corrige o se deja como ejercicio diagnóstico.

4. **Puerto 8080 duplicado**: `temporal-ui` y `bato-learning` ambos usan 8080. El `compose.prod.yaml` de D03 debe usar un puerto distinto para uno de ellos o poner bato-learning detrás de Traefik (que es el objetivo de D03).

---

## D03-D04 — completado

- preparación para E01: stack listo en prod, ahora a agentes.

```yaml
- id: D03
  status: done
  assumed_from_prereqs:
    D02: "el lector sabe levantar docker compose con override files y healthchecks"
  prepared_for_successors:
    D04: "el stack está en producción con dominio, TLS y logs disponibles; ahora se observa"
    E01: "el servidor CX22 está listo para alojar el worker Temporal y Phoenix"
  deviations_from_spec: |
    - MODULES.md mencionaba 'litestream' para backup; se incluyó 'sqlite3 .backup'
      como el método principal (más simple, sin dependencia extra) y se mencionó
      litestream como alternativa para WAL replication continua.
    - Se añadió sops+age para secrets (pedido explícito en la tarea).
      MODULES.md solo decía '.env y por qué no en repo'.
    - Traefik v3 verificado: imagen 'traefik:v3.2' ya está en
      infra/hetzner/compose.prod.yml del repo.
  glossary_terms_introduced: [sops, age, TLS-ALPN-01, hot-backup, smoke test]
  references_app_code_verified:
    - infra/traefik/traefik.yml: existe
    - infra/hetzner/compose.prod.yml: existe
    - infra/hetzner/README.md: existe
    - compose.yaml: existe
  open_questions:
    - "infra/scripts/backup.sh no existe aún (path tentativo). El scaffold debe crearlo."

- id: D04
  status: done
  assumed_from_prereqs:
    D02: "docker compose y servicios auxiliares conocidos"
    D03: "la app está en Hetzner; ahora se observa"
  prepared_for_successors:
    E04: "el lector sabe instrumentar spans con tenant; aplica directo a memoria"
    E05: "Temporal emite spans OTel; el lector ya sabe leerlos en Phoenix"
  deviations_from_spec: |
    - app/middleware/cost.py no existe en el repo. Se referenció
      app/services/anthropic_client.py (que sí existe con _estimate_cost y
      _PRICE_PER_M) y app/repos/chat.py (con tokens_cache_read/write).
      app/middleware/cost.py queda como scaffold pendiente.
    - Se añadió tabla comparativa Phoenix/Logfire/Langfuse/LangSmith y tabla
      de costo por sesión con caching (pedidos explícitos en la tarea).
  glossary_terms_introduced: [span, trace, exporter, OpenInference, BatchSpanProcessor]
  references_app_code_verified:
    - app/logging_setup.py: existe
    - api/app/telemetry.py: existe
    - app/services/anthropic_client.py: existe
    - app/repos/chat.py: existe
    - compose.yaml: existe
  open_questions:
    - "El prerequisito E02 listado en MODULES.md para D04 contradice ord:20 (D04)
       vs ord:22 (E02). El Sonnet integrador debe resolver si es prerequisito duro
       o soft (el módulo D04 funciona pedagógicamente sin haber leído E02)."
```

---

## E01-E03 — completado

```yaml
- id: E01
  status: done
  assumed_from_prereqs:
    A06: "el lector escribe dataclasses y funciones tipadas"
    A07: "el lector entiende async/await y asyncio.gather"
    B02: "el lector conoce FastAPI, Pydantic v2, y el ciclo request"
  prepared_for_successors:
    E02: "el lector domina el loop SDK con tool_use/tool_result y cache_control;
          E02 porta ese loop a StateGraph LangGraph"
    E03: "el lector entiende cómo el system prompt se construye por bloques;
          E03 explica cómo los skills se convierten en esos bloques"
  deviations_from_spec: |
    Ninguna desviación. Se añadió §4.7 (MCP en el SDK) como sección corta
    porque SHARED §1.5 lo menciona y E01 es el módulo donde el lector ve
    el SDK por primera vez.
  glossary_terms_introduced:
    - content blocks (text, tool_use, tool_result)
    - tool_choice
    - batches API
  references_app_code_verified:
    - app/services/anthropic_client.py: existe
    - app/services/context_builder.py: existe
    - api/app/routers/anthropic_demo.py: existe
  open_questions: []
  use_cases_linked: [F-FIN-01]

- id: E03
  status: done
  assumed_from_prereqs:
    E01: "el lector construye loops con tools y entiende el system prompt por bloques"
  prepared_for_successors:
    E04: "el lector sabe diseñar skills con slots por tenant; E04 persiste el
          estado del agente por (tenant_id, thread_id)"
    E05: "los skills son la unidad de receta que se porta a activities Temporal"
  deviations_from_spec: |
    El task original del Opus nombraba este módulo como 'E02 — Skills'. Según
    MODULES.md, E02 es LangGraph y E03 es Skills/AGENTS.md. Se respetó la
    numeración de MODULES.md para mantener consistencia con prerequisites y
    next_hints de los demás módulos. E02 (LangGraph) queda pendiente.
  glossary_terms_introduced:
    - gating (carga selectiva de skills)
    - AGENTS.md (estándar multi-agente, 2025)
    - agente mayordomo (anti-patrón)
  references_app_code_verified:
    - CLAUDE.md: existe
    - app/services/context_builder.py: existe (referencia indirecta como patrón)
  open_questions:
    - "app/integrations/skills/monthly_audit/SKILL.md referenciado en MODULES.md
       no existe aún. El scaffold debe crearlo antes del primer release de E03."
  use_cases_linked: [F-CTA-01]
```

### Preparación para E04

El lector que termina E01 y E03:
- Construye un loop SDK completo con tools, cache y verificación de hit rate.
- Diseña skills con frontmatter YAML, slots por tenant, y triggers específicos.
- Distingue qué va en CLAUDE.md (invariantes globales) vs skill (receta de tarea).
- Aplica gating selectivo: el harness carga solo el skill que el trigger indica.

E04 puede asumir todo esto y entrar en: `thread_id` como `(tenant_id, conversation_id)`,
checkpointer SQLite en LangGraph, y separación de sesión vs memoria larga por tenant.

**Nota de coordinación — preparación para E02 (LangGraph)**:
el lector domina SDK + skills. El siguiente paso natural es E02 (LangGraph),
que porta el loop de E01 a un StateGraph. E02 queda pendiente de escritura.

---

## E02 y E04 — completado

```yaml
- id: E02
  status: done
  assumed_from_prereqs:
    E01: "el lector construye loops SDK con tool_use/tool_result; ahora lo porta a StateGraph"
  prepared_for_successors:
    E03: "el lector sabe compilar un grafo con checkpointer y thread_id; E03 añade skills como system prompt"
    E04: "StateGraph + SqliteSaver + thread_id son vocabulario operativo; E04 añade la capa multitenant"
    E05: "el lector entiende interrupt_before como pause point; E05 envuelve el grafo en un workflow Temporal"
  deviations_from_spec: |
    El MODULES.md asigna la tabla de equivalencias SDK↔LangGraph a E02 (goal:
    "mapear cada primitiva del SDK a su equivalente LangGraph"). Se cumplió en
    la sección §4 de E02 con tabla explícita y en la prosa de cada mecanismo.
    La tabla ampliada (Claude Code→LangGraph) se distribuyó entre E02 y E03
    para no duplicar: E02 cubre las primitivas LangGraph puras; E03 cubre
    skills, hooks, gating y compaction como lo que el harness reconstruye.
  glossary_terms_introduced:
    - "reducer (add_messages): función que LangGraph aplica sobre un campo del estado en cada update"
    - "astream_events v2: API de streaming de LangGraph 0.2.50+ para consumir eventos por tipo"
  references_app_code_verified:
    - api/app/routers/langgraph_demo.py: existe (StateGraph + ToolNode + tools_condition real)
    - api/app/workflows/audit.py: existe (workflow Temporal que llama al agente)
  open_questions:
    - "AsyncSqliteSaver en producción multitenant: el ejercicio usa SqliteSaver sync.
       Para el caso de concurrencia real (E04+), el lector necesita AsyncSqliteSaver
       o AsyncPostgresSaver. Considerar nota en E04 o ejercicio adicional."
  use_cases_linked: [F-OPS-01]

- id: E04
  status: done
  assumed_from_prereqs:
    E02: "StateGraph, checkpointer, thread_id conocidos"
    E03: "skills con slots por tenant conocidos; el lector diseña agentes por caso de uso"
    C03: "aislamiento multitenant en repos; el lector aplica el mismo principio al thread_id"
  prepared_for_successors:
    E05: "el lector diseña thread_id como (tenant_id, conversation_id); Temporal usa el mismo
          principio con idempotency_key = f'{tenant_id}:{period}'"
    E06: "Capstone usa exactamente la estructura de thread_id y compaction_check de E04"
  deviations_from_spec: |
    El nodo compaction_check del ejercicio usa estimación de tokens por caracteres
    (4 chars ≈ 1 token) en lugar de anthropic.count_tokens — suficiente para el
    ejercicio; la nota en el módulo avisa del método exacto para producción.
    El store de largo plazo (InMemoryStore / AsyncPostgresStore) se documenta en
    tabla conceptual pero sin ejercicio dedicado — un ejercicio de store completo
    requeriría AsyncPostgresStore que no está disponible en el runner backend simple.
    El Sonnet integrador puede añadir ese ejercicio en E06 (Capstone) si procede.
  glossary_terms_introduced:
    - "memoria de turno: mensajes del turno actual, en RAM, no persiste"
    - "memoria de sesión: historial del thread_id actual, en el checkpointer"
    - "memoria de largo plazo: hechos entre sesiones, en el store o en DB"
    - "compactación: resumen del historial antiguo para evitar superar el context window"
  references_app_code_verified:
    - app/repos/chat.py: existe (filtro por tenant_id+user_id+module_id = equivalente de thread_id)
    - app/services/chat.py: existe (gestión de sesión del tutor)
    - app/integrations/anthropic_chat.py: existe (cache_control en system blocks)
  open_questions:
    - "AsyncPostgresSaver no se ejerce en el runner backend del curso (requiere asyncpg).
       La documentación lo menciona; si se añade un entorno Docker para ejercicios E04+,
       el Sonnet integrador puede añadir ejercicio de migración SqliteSaver→PostgresSaver."
  use_cases_linked: [F-CX-02]
```

---

## Track F — CX (Servicio al Cliente) — completado

```yaml
- dept: CX
  fichas_completadas: [F-CX-01, F-CX-02, F-CX-03, F-CX-04]
  status: done

  F-CX-01:
    archivo: app/content/F/F-CX-01.md
    estado: pre-existente (completo al inicio de esta tarea)
    secciones: 12/12
    industrias: [retail/tiendabox, servicios-fin/cooppopular]

  F-CX-02:
    archivo: app/content/F/F-CX-02.md
    estado: pre-existente (completo al inicio de esta tarea)
    secciones: 12/12
    industrias: [salud/sanrafael, servicios-fin/cooppopular]

  F-CX-03:
    archivo: app/content/F/F-CX-03.md
    estado: pre-existente (completo al inicio de esta tarea)
    secciones: 12/12
    industrias: [retail/tiendabox, hospitalidad/mesonurbano]

  F-CX-04:
    archivo: app/content/F/F-CX-04.md
    estado: creado en esta tarea
    secciones: 12/12
    industrias: [servicios-fin/cooppopular, energia/solenergy]

  decisiones_clave:
    - "F-CX-02: STT primario Deepgram Nova-3 (es-latam) 2026; gpt-4o-mini-transcribe
       como alternativa. Verificados con WebSearch 2026."
    - "WhatsApp Business 2026: Meta cobra por template enviado. Colombia ~0.02 USD/msg
       marketing, ~0.004 USD/msg utility. BSPs: 360dialog (49 USD base + 0.005/msg),
       Wati (49-99 USD/mes + 20% markup sobre Meta), GupShup (volumen LATAM)."
    - "F-CX-04 health score en Python puro, pesos configurables por tenant en YAML.
       Sin vendor lock. Referencia: ChurnZero CS Study 2025 — 73% de scores fallan
       por calidad de datos, no por herramienta."
    - "PII/privacidad cubierto en todas las fichas: Ley 1581 Colombia, LGPD Brasil,
       habeas data. Sección 10 de cada ficha detalla la regulación aplicable."
    - "Fallback humano explícito en cada ficha: F-CX-01 (agente revisa borrador antes
       de enviar), F-CX-02 (transcription_failed -> cola manual), F-CX-03 (owner
       humano revisa borrador de artículo), F-CX-04 (insufficient_signal -> tarea
       de contacto de cortesía)."

  terminologia_nueva_introducida:
    - "diarizacion: atribucion de turnos de habla a speakers en una transcripcion"
    - "health score: puntuacion compuesta que estima el estado de la relacion con un cliente"
    - "save play: intervencion de retencion especifica para un cliente en riesgo"
    - "PQR formal: peticion, queja o recurso formal ante regulador (Superfinanciera Colombia)"
    - "dark period: periodo sin interaccion registrada de un cliente; tratado como senal de riesgo"

  open_questions:
    - "F-CX-03 referencia pgvector y Qdrant para vector store KB. El repo actual usa SQLite.
       El integrador debe decidir si C01 ampliado o un modulo C04 futuro cubre pgvector."
    - "F-CX-02 menciona Whisper Large-v3 self-hosted en GPU T4 (Hetzner) como fallback.
       El repo no tiene ese perfil de compose. Scaffold o apuntar a instancia gestionada."
    - "ord de F-CX-04 asignado como 243. Verificar con el integrador que no hay colision
       con otras fichas del catalogo."
```

---

### Preparación para E05 — nota de coordinación

E02 y E04 completan la cadena técnica de LangGraph:
- **E02**: StateGraph + ToolNode + checkpointer + interrupt_before + astream_events.
- **E03**: Skills + gating + equivalencias Claude Code → LangGraph (harness).
- **E04**: Memoria multitenant + thread_id por tenant + compaction.

El agente LangGraph está listo. E05 añade la capa de durabilidad externa: el workflow Temporal envuelve el grafo, la activity `run_agent` lo ejecuta con heartbeat, el schedule lo dispara mensualmente por tenant.

---

## A04-A07 — completado

- **archivos**:
  - `app/content/A/A04.md` + `A04.exercises.yaml` (4 ejercicios) + `A04.quizzes.yaml` (3 quizzes)
  - `app/content/A/A05.md` + `A05.exercises.yaml` (4 ejercicios) + `A05.quizzes.yaml` (3 quizzes)
  - `app/content/A/A06.md` + `A06.exercises.yaml` (3 ejercicios) + `A06.quizzes.yaml` (3 quizzes)
  - `app/content/A/A07.md` + `A07.exercises.yaml` (4 ejercicios) + `A07.quizzes.yaml` (3 quizzes)

- **decisiones clave**:
  1. **A05 como bisagra real**: refleja la estructura física de `app/` con los `__init__.py` reales del repo verificados. El ejercicio cumbre `monolith-to-package` parte un script en dos módulos simulados con fachada, replicando el patrón de `app/models/__init__.py`.
  2. **A07 sigue MODULES.md** (async/await), no el título «Clases II» del prompt original. MODULES.md §A07 es autoritativo per ARCHITECTURE §11.1.
  3. **Composición sobre herencia en A06**: la única herencia en dominio es la de excepciones (A04). Los modelos SQLAlchemy heredan solo de `Base` — framework, no diseño propio. El lector llega a C01 sin hábito de herencia múltiple.

- **personajes usados**:
  - `acme` (ACME Manufacturing): tenant principal en todos los módulos
  - `globex` (Globex Logistics): A05 para ciclo de import
  - `initech` (Initech Audit): vendor bloqueado en A06 ejercicio de Protocol

- **casos F referenciados**:
  - A04 → F-CTA-01: dispatcher de reglas contables, una función por regla
  - A05 → F-FIN-01: estructura de paquete reconciliation/ con parser/matcher/reporter
  - A06 → F-CMP-01: clase Quote con Vendor para comparación de cotizaciones
  - A07 → F-OPS-01: asyncio.gather para fetch paralelo de inventario/órdenes/precios

- **preparación para B01**:
  El lector que termina A07 entiende módulos/paquetes, imports, clases con
  @dataclass y Protocol, coroutinas y gather. B01 asume que el lector navega
  app/ sin perderse y entiende por qué async def en los repos. B02 asume
  firmas tipadas y Protocol para DI.

- **riesgos**:
  - A07 usa time.monotonic() en tests de concurrencia. En Pyodide con delays muy
    pequeños puede no ser preciso. Tests usan 0.40s de tolerancia para 3 coroutinas
    de max 0.15s. Si el runner es lento, ajustar los delays.
  - Ejercicios con inspect.getsource en Pyodide (A05, A06): mismo riesgo que A03.
    El integrador verifica que el loader no transforma el código antes de exec.
  - El tema herencia/ABC/@classmethod/@staticmethod del prompt original para A07
    quedó sin cubrir. Si el Opus decide añadirlo: puede ir en A06 ampliado o en
    módulo A07b; debe actualizar MODULES.md y prerequisites en cascada.

```yaml
- id: A04
  status: done
  glossary_terms_introduced: []
  open_questions: []

- id: A05
  status: done
  glossary_terms_introduced:
    - módulo (archivo .py)
    - paquete (carpeta con __init__.py)
    - import absoluto / relativo
    - sys.path
    - ciclo de import
    - src-layout
  open_questions: []

- id: A06
  status: done
  glossary_terms_introduced:
    - atributo de instancia / atributo de clase
    - tipado estructural (Protocol)
    - composición sobre herencia
  open_questions: []

- id: A07
  status: done
  glossary_terms_introduced:
    - coroutina
    - event loop
    - asyncio.gather
    - blocking call
    - generador async (AsyncIterator)
  open_questions:
    - "Herencia/ABC/@classmethod/@staticmethod del prompt original no cubiertos.
       Opus debe decidir si va en A06 ampliado o en nuevo módulo."
```

---

## F-OPS-01 a F-OPS-04 — completado (Track F, departamento OPS)

```yaml
- id: F-OPS-01
  status: done
  notes: |
    Ficha preexistente y completa (ord=161). No se modificó.
    Manufactura (ACME plásticos) + Hospitalidad (Mesón Urbano).
    MRP determinístico + scheduling greedy; agéntico = priorización de conflictos y memo al jefe de planta.

- id: F-OPS-02
  status: done
  files_produced:
    - app/content/F/F-OPS-02.md
  assumed_from_prereqs:
    F-OPS-01: "patrón de workflow con ingest + tramos det. + agéntico + human_review + Temporal"
  deviations_from_spec: |
    La ficha preexistente era un placeholder de 253 líneas sin todas las secciones canónicas.
    Se reemplazó con ficha completa de 12 secciones.
    Se añadió énfasis en statsforecast (Nixtla) con CrostonSBA/AutoETS como stack real 2026,
    verificado via WebSearch. El placeholder mencionaba Prophet — se mantuvo como referencia
    secundaria pero se priorizó statsforecast por mejor rendimiento en series intermitentes PYME.
  industries_instanced: [retail, agro]
  tenants_used: [tiendabox, cafetera]
  big_corp_vendors_verified: [SAP IBP desde 29k USD/año, Blue Yonder Luminate Leader MQ 2026,
                               Kinaxis Maestro 250k-1M+ USD/año, o9 Solutions custom, Anaplan 100k-500k]
  key_additions:
    - Clasificación ABC-XYZ con umbral ADI/CV² para selección Croston vs. ETS
    - Workflow Temporal que separa actividad CPU-bound (statsforecast) de LLM-bound (agente)
    - Fallback humano explícito para eventos sin base histórica comparable
    - Instancia Cooperativa Cafetera con contratos forward y pronóstico agrometeorológico

- id: F-OPS-03
  status: done
  notes: |
    Ficha preexistente y completa (242 líneas, 12 secciones canónicas).
    No se modificó. Retail (TiendaBox) + Salud (Clínica San Rafael).
    Guardrail duro para medicamentos críticos documentado explícitamente.

- id: F-OPS-04
  status: done
  notes: |
    Ficha preexistente y completa (246 líneas, 12 secciones canónicas).
    No se modificó. Logística (Expreslog) + Hospitalidad (Mesón Urbano).
    Restricciones laborales LATAM (Colombia/México/Perú) configurables por tenant.
    requires_confirmation en send_email/post_slack_message documentado.
```

**Resumen del lote F-OPS:**
- F-OPS-01: scheduling greedy + MRP + memo de planta (manufactura / F&B).
- F-OPS-02: forecast estadístico Croston/ETS + ajuste de eventos extraordinarios (retail / agro).
- F-OPS-03: ROP/SS/EOQ + detección de anomalías + guardrail medicamentos críticos (retail / salud).
- F-OPS-04: FTE por franja + compliance laboral + comunicación al equipo (logística / hospitalidad).

Todas las fichas cumplen: ≥2 industrias instanciadas, sección determinístico/agéntico, fallback humano explícito, precio orientativo en rango USD/mes, referencia a ≥1 módulo Track D y ≥1 Track E.

---

## B01-B02 y C01 — completado

- **archivos producidos**:
  - `app/content/B/B01.md` + `B01.exercises.yaml` (2 ejercicios pyodide) + `B01.quizzes.yaml` (3 quizzes) — nuevos
  - `app/content/B/B02.md` + `B02.exercises.yaml` (2 ejercicios pyodide) + `B02.quizzes.yaml` (3 quizzes) — nuevos
  - `app/content/C/C01.md` + `C01.exercises.yaml` (2 ejercicios backend) + `C01.quizzes.yaml` (3 quizzes) — reemplazados

- **hilo**: HTTP ciclo completo → FastAPI internals → SQLAlchemy async

- **decisiones clave**:
  1. La tarea llamaba «B03» al módulo de SQLAlchemy pero MODULES.md asigna ese contenido a C01 (`sqlalchemy-async-sqlite`). Se usaron los ext_id correctos del MODULES.md. B03 (Jinja+HTMX) queda sin escribir.
  2. C01 tenía contenido previo sobre Postgres (`postgres-production`). Se reemplazó por el módulo correcto de SQLAlchemy. El contenido de Postgres desplazado (pooling, índices, EXPLAIN) es valioso; el integrador debe decidir si va en C03 ampliado o en un módulo nuevo.
  3. El ejercicio N+1 (C01, backend) usa `sa_event.listens_for` para contar queries reales — ejercicio ambicioso que requiere verificación en el runner de subprocess del backend.

- **preparación para B04**:
  El lector sabe: HTTP a mano (curl, status, headers), escribir router FastAPI con Pydantic v2 y Depends, definir modelo SQLAlchemy 2.x y ejecutar queries async con eager loading. B04 puede entrar directo en refactor de endpoint monolítico a 4 capas.

- **riesgos**:
  - El slug `postgres-production` del C01 anterior podría estar referenciado en algún módulo ya escrito (D01-D04, E*). El integrador debe buscar y corregir links rotos.
  - `app/deps.py` listado en MODULES.md como referencia de B02 no existe; la dependencia `SessionDep` está en `app/db.py`. El módulo apunta al archivo correcto; MODULES.md debe actualizarse.

---

## C01-C03 — completado

- **archivos producidos**:
  - `app/content/C/C01.md` — reemplazado (linter ajustó frontmatter a slug canónico `sqlalchemy-async-sqlite`, body reescrito con SQLAlchemy 2.x honesto + sección de frontera SQLite→Postgres)
  - `app/content/C/C01.exercises.yaml` — linter reemplazó con ejercicios de SQLAlchemy (model+query, selectinload N+1); son correctos y alineados con el slug
  - `app/content/C/C01.quizzes.yaml` — linter reemplazó con quizzes de flush/commit, N+1, expire_on_commit; alineados
  - `app/content/C/C02.md` — nuevo, slug `multitenancy-rls` (ext_id C02, ord 15); cubre tenant_id, RLS, SET LOCAL, test leak=0, tres patrones de multitenancy
  - `app/content/C/C02.exercises.yaml` — nuevo, 3 ejercicios: políticas RLS SQL, test de aislamiento Python, SET vs SET LOCAL
  - `app/content/C/C02.quizzes.yaml` — nuevo, 3 quizzes: superusuario bypass, SET LOCAL scope, elección de patrón
  - `app/content/C/C03.md` — nuevo, slug `datos-y-backups` (ext_id C03, ord 16); cubre pg_dump, retención, restore drill, pgBackRest, Hetzner Storage Box, cifrado, masking
  - `app/content/C/C03.exercises.yaml` — nuevo, 3 ejercicios: pg_dump command builder, retention_days(), restore_drill_steps()
  - `app/content/C/C03.quizzes.yaml` — nuevo, 3 quizzes: formato pg_dump, restore drill sin ejecutar, política de retención a 7 años

- **hilo C01→C02→C03**:
  1. C01: ORM y sesión async sobre SQLite (la app real). La sección "frontera con Postgres" prepara el terreno sin mentir: la app aún corre sobre SQLite.
  2. C02: el módulo bisagra. `tenant_id` en cada tabla + RLS en Postgres como red de seguridad. El aislamiento es determinístico; se testea con un caso que demuestra leak=0.
  3. C03: sin persistencia durable, el aislamiento de C02 no sirve. pg_dump + retención + restore drill como criterio de aceptación.

- **top 3 decisiones**:
  1. **C01 respeta el slug canónico** (`sqlalchemy-async-sqlite`). El linter forzó el frontmatter correcto; el body incluye honestamente la comparación SQLite→Postgres sin pretender que la app ya usa Postgres.
  2. **C02 es el módulo bisagra del curso completo** (no solo del Track C). RLS es determinístico: el motor lo aplica sin intervención del agente. La tabla "determinístico vs agéntico" lo dice explícitamente: el aislamiento nunca se delega al LLM.
  3. **C03 ancla el restore drill como criterio de aceptación**, no como recomendación. Un backup sin drill verificado no existe. Precio orientativo para PYME LATAM: Hetzner Storage Box desde 1 €/mes por 100 GB.

- **preparación para D01**:
  El lector domina la capa de persistencia completa: ORM async, schema versionado (C02 lo asume de Alembic, mencionado como prerequisito), aislamiento por tenant a nivel de motor, y estrategia de backup verificada. D01 puede entrar directo en containerización sin explicar nada de base de datos.

- **riesgos**:
  - C02 referencia `app/repos/_base.py` como helper de filtro por `tenant_id`. Ese archivo no existe aún en el repo. El integrador debe crearlo en el scaffold o cambiar la referencia a `app/repos/progress.py` donde el filtro está inline.
  - C03 ext_id C03 coincide con el C03 de MODULES.md (`multitenancy-rls`) — la instrucción del usuario reorganizó el Track C. El integrador debe actualizar MODULES.md si se acepta la nueva estructura (C01=SQLAlchemy, C02=RLS, C03=Backups).
  - Los ejercicios de C02 (`rls-policy-write`, `rls-isolation-test`) tienen `runner: backend` y `runner: pyodide` respectivamente. El test de aislamiento en Pyodide usa simulación de RLS con filtros Python — no conecta a Postgres real. El lector debe hacer el restore drill en un Postgres real en el Capstone.
  - C03 menciona `pg_anonymizer` para masking. No es una extensión instalada por defecto; requiere `EXTENSION pg_anonymize` o `pg_anonymizer`. El módulo lo menciona conceptualmente; el integrador debe verificar si se instala en el entorno del Capstone.

```yaml
- id: C01
  status: done
  assumed_from_prereqs:
    A07: "el lector entiende async/await; la honestidad sobre aiosqlite tiene sentido"
    B02: "el lector conoce el dependency injection; get_session ya es familiar"
  prepared_for_successors:
    C02: "el lector define modelos con Mapped[T] y ejecuta queries; C02 añade tenant_id y políticas RLS"
    C03: "la frontera SQLite→Postgres está trazada; C03 construye la estrategia de backup"
  deviations_from_spec: |
    El linter sobreescribió el frontmatter con el slug canónico `sqlalchemy-async-sqlite`.
    El body reescrito cubre SQLAlchemy 2.x + la sección "frontera con Postgres" explícita.
    La promesa de A02 ("C01 introduce Decimal") no se cumplió — Decimal es stdlib y no
    requiere módulo propio; se puede introducir en el ejercicio de totales de facturas.
  glossary_terms_introduced:
    - "DeclarativeBase / Mapped[T]"
    - "flush vs commit (unit of work)"
    - "expire_on_commit"
    - "N+1 queries"
    - "selectinload"

- id: C02
  status: done
  assumed_from_prereqs:
    C01: "modelos con tenant_id como columna; el lector puede añadir la columna a cualquier tabla"
  prepared_for_successors:
    C03: "el aislamiento está garantizado a nivel de motor; C03 asume que un restore no mezcla tenants"
    D01: "la capa de datos es correcta; D01 containeriza sin tocar la BD"
    E04: "thread_id como (tenant_id, conversation_id) es la extensión lógica de este principio"
    E05: "idempotency_key incluye tenant_id — el mismo principio de aislamiento"
  deviations_from_spec: |
    MODULES.md asigna `multitenancy-rls` a C03 (ord=16). Esta sesión lo escribe como
    C02 (ord=15), liberando C03 para `datos-y-backups`. El integrador debe actualizar
    MODULES.md o reordenar los archivos si prefiere mantener la numeración original.
  glossary_terms_introduced:
    - "RLS (Row Level Security) — ya estaba en SHARED §1.4, usada la definición textual"
    - "SET LOCAL (scope de transacción vs SET de scope de conexión)"
    - "schema-per-tenant / db-per-tenant (patrones alternativos)"
    - "BYPASSRLS (privilegio Postgres que ignora RLS)"

- id: C03
  status: done
  assumed_from_prereqs:
    C02: "el aislamiento está garantizado; C03 construye la capa de durabilidad sobre él"
  prepared_for_successors:
    D01: "el lector sabe que la BD tiene backup y el restore está verificado; D01 containeriza"
    D03: "D03 menciona SQLite backup (litestream / .backup API); C03 cubre el equivalente Postgres"
  deviations_from_spec: |
    MODULES.md no tenía un módulo dedicado a backups en el Track C original (era parte de D03).
    Esta sesión lo crea como C03 `datos-y-backups`. Si el integrador prefiere mantener la
    numeración original de MODULES.md (C03 = multitenancy-rls, backups en D03), debe mover
    el contenido de C03 a D03 ampliado y eliminar este archivo.
  glossary_terms_introduced:
    - "RPO (Recovery Point Objective)"
    - "RTO (Recovery Time Objective)"
    - "restore drill"
    - "WAL archiving / PITR"
    - "pgBackRest"
    - "Hetzner Storage Box (destino de backup económico para PYME LATAM)"
```

---

## F-CMP + F-OPS — completado

**Archivos producidos**:
- `app/content/F/F-CMP-01.md` — Comparación de cotizaciones RFQ (construccion, hospitalidad; tenants andina, mesonurbano)
- `app/content/F/F-CMP-02.md` — Evaluación trimestral de proveedores KPI scorecards (retail, logistica; tenants tiendabox, expreslog)
- `app/content/F/F-CMP-03.md` — OCR + validación de facturas 3-way match (salud, hospitalidad; tenants sanrafael, mesonurbano)
- `app/content/F/F-CMP-04.md` — Gestión de contratos marco vencimientos y cláusulas (servicios-fin, construccion; tenants cooppopular, andina)
- `app/content/F/F-OPS-01.md` — Planeación de producción semanal (manufactura, hospitalidad; tenants acme, mesonurbano)
- `app/content/F/F-OPS-02.md` — Forecast de demanda por SKU y canal (retail, agro; tenants tiendabox, cafetera)
- `app/content/F/F-OPS-03.md` — Optimización de inventario stock-out vs sobrestock (retail, salud; tenants tiendabox, sanrafael)
- `app/content/F/F-OPS-04.md` — Planeación de capacidad y staffing turnos y picos (logistica, hospitalidad; tenants expreslog, mesonurbano)

**Decisiones clave**:
1. `ord` asignados: CMP=141-144, OPS=161-164. Sin colisiones con fichas previas.
2. Separación determinístico/agéntico con ejemplos concretos por ficha:
   - CMP-01: normalización de unidades (determinístico) vs. emparejamiento «TUBO PVC 1/2 PULG x 6M» ↔ «TUBO 1/2" PVC 6 METROS» (agéntico).
   - CMP-03: parsing XML CFDI/DIAN + 3-way-match aritmético (determinístico, 70%) vs. resolución de discrepancias menores (agéntico).
   - OPS-01: explosión BOM + scheduling greedy (determinístico, 60%) vs. priorización de conflictos de capacidad (agéntico).
   - OPS-02: ETS/Prophet/Croston con statsforecast (determinístico, 50%) vs. incorporación de eventos que el modelo no ve (agéntico).
   - OPS-03: ROP/SS/EOQ fórmulas cerradas (determinístico, 70%) vs. detección de patrón anómalo que rompe supuestos (agéntico).
3. Guardrail duro en F-OPS-03 y F-CMP-03: SKU CRÍTICO en salud nunca se modifica sin sign-off humano con trazabilidad en DB (campo `approved_by` en `inventory_params`).
4. Industrias instanciadas: construccion (andina), hospitalidad (mesonurbano), retail (tiendabox), logistica (expreslog), manufactura (acme), agro (cafetera), salud (sanrafael), servicios-fin (cooppopular). Con esto, `agro` (cafetera) aparece en Track F por primera vez.
5. Vendors 2026 verificados via WebSearch: Coupa (50k-500k/año), SAP Ariba SLP, Jaggaer, Ivalua, Esker, Tradeshift, Vic.ai, Tipalti, SAP IBP, Anaplan, Kinaxis (~250k-1M/año), o9, Blue Yonder (100k+/año), ToolsGroup, RELEX, UKG/Kronos (6-22 USD/empleado/mes), Quinyx, Workday Scheduling.
6. OCR pricing 2026: Google Document AI $1.50/1k páginas básico; AWS Textract $0.0015/página.
7. Datup citado en F-OPS-01 y F-OPS-02 como alternativa LATAM (demand planning PYME desde ~200 USD/mes).
8. Validación fiscal DIAN/SAT en F-CMP-03: tramo determinístico, no bloqueante si la API está caída.
9. Temporal Activities documentadas en todos los workflows periódicos con `idempotency_key` explícito.

**Supuestos no verificados**:
- `statsforecast` (Nixtla) no está en `api/pyproject.toml`. El integrador debe añadir `nixtla-statsforecast>=1.7` si F-OPS-02 se implementa en backend.
- API DIAN/SAT: el integrador debe verificar endpoints de autenticación actuales antes de implementar F-CMP-03.
- `parse_contract_pdf` está en el catálogo de SHARED.md pero no tiene implementación; el integrador debe scaffoldearla para F-CMP-04.

---

## B03 — completado

- **archivos producidos**:
  - `app/content/B/B03.md` (slug `jinja-htmx-ui`, ord 10, ~90 min)
  - `app/content/B/B03.exercises.yaml` — 3 ejercicios pyodide
  - `app/content/B/B03.quizzes.yaml` — 3 quizzes

- **assumed_from_prereqs**:
  - B02: el lector entiende el ciclo request FastAPI, `TemplateResponse`, y `Depends`; sabe lo que es un `router`.

- **decisiones clave**:
  1. Los ejercicios usan Jinja2 en Pyodide para analizar HTML como texto. No hay browser real; los tests verifican presencia exacta de atributos en strings. Esto es suficiente para la didáctica (HTMX se enseña como texto de atributos; el comportamiento se describe en la lección).
  2. `hx-swap="outerHTML"` vs `"innerHTML"` es el error #1 que cometen los lectores y se trata con ejercicio dedicado (ejercicio 2) y quiz dedicado (quiz 1).
  3. El anti-patrón «HTMX para estado complejo» se trata con explicitación directa en §3 y §5 (errores típicos) y un quiz (quiz 3). Se referencia `app/static/js/chat.js` como el contra-ejemplo correcto en la app real.
  4. Determinístico vs agéntico: la tabla (§6) cubre 5 tramos del dashboard F-CX-03. El render del template es siempre determinístico; el ranking de sugerencias es agéntico. Esto es el ejemplo más limpio del curso de por qué los dos tramos están separados.
  5. Filtro `| md | safe` explicado con la razón del doble filtro (Jinja2 escapa por defecto; `safe` levanta esa protección solo después de que el servidor ya produjo el HTML).
  6. HTMX versión 2.0.4 (la que está en `_layout.html`); se menciona 2.0.9 como la verificada en ARCHITECTURE.md. No hay diferencia de API para los atributos del módulo; el lector puede ver la versión exacta en el `<script src>` del layout.

- **prepared_for_successors**:
  - B04: el lector entiende que el router devuelve `TemplateResponse`; B04 puede entrar directo en la refactorización de ese router hacia la capa de servicios sin explicar Jinja2.
  - B05: el lector sabe que `partials/exercise.html` es un partial incluido por `module.html`; B05 puede referenciarlo al explicar cómo el editor CodeMirror se monta en ese partial.

- **deviations_from_spec**:
  Las 13 secciones de ARCHITECTURE.md §4 se fusionaron en 11 secciones numeradas en el `.md` (secciones 6 «Determinístico vs agéntico» y 10 «Errores típicos» están presentes; se reorganizó el orden para que el flujo de lectura sea natural: ejemplo → det/agéntico → errores → caso de uso → profundizar → chat → salida). El contenido de todos los bloques obligatorios está cubierto.

- **open_questions**:
  - `app/routers/exercises.py` listado en MODULES.md como referencia de B03 no existe en el repo (según la matriz §9 de ARCHITECTURE.md). El módulo referencia `app/templates/module.html` y `app/templates/partials/exercise.html` que sí existen. El integrador debe crear el scaffold de `exercises.py` o actualizar la referencia en MODULES.md.
  - La versión de HTMX en `_layout.html` es 2.0.4 (CDN unpkg); ARCHITECTURE.md menciona 2.0.9. No hay impacto en el módulo, pero el integrador debería alinearlas.

---

## D-EXPAND — D05, D06, D07, D08 — completado (2026-05-16)

**Lote**: `D-EXPAND`
**Archivos producidos**:
- `app/content/D/D05.md` + `D05.exercises.yaml` + `D05.quizzes.yaml` — CI/CD desde 0: GitHub Actions
- `app/content/D/D06.md` + `D06.exercises.yaml` + `D06.quizzes.yaml` — Cómo se despliega cada pieza
- `app/content/D/D07.md` + `D07.exercises.yaml` + `D07.quizzes.yaml` — Estrategias de despliegue
- `app/content/D/D08.md` + `D08.exercises.yaml` + `D08.quizzes.yaml` — Secretos en producción

```yaml
- id: D05
  status: done
  assumed_from_prereqs:
    D03: "el lector desplegó en Hetzner con Traefik; sabe hacer SSH y docker compose manualmente"
    D04: "el lector entiende la app completa; sabe qué servicios existen en compose"
  prepared_for_successors:
    D06: "el pipeline CI/CD está operando; D06 explica qué se despliega en cada pieza"
    D07: "el deploy automático existe; D07 añade estrategias de rollout sobre él"
    E01: "el agente en E01 asume que hay CI/CD — cada push al repo testa y despliega"
  deviations_from_spec: |
    - Se cubrió `appleboy/ssh-action@v1` (confirmado en WebSearch 2026).
    - `docker/build-push-action@v6` verificado como versión 2026 estable.
    - Se añadió subsección explícita sobre costo del free tier (2000 min/mes)
      y criterios para migrar a self-hosted runner — pedido explícito en el briefing.
    - El énfasis determinístico vs agéntico en el pipeline se repite en múltiples
      secciones porque es el punto central del módulo según ARCHITECTURE.md §10.
  glossary_terms_introduced:
    - "workflow (GitHub Actions): archivo YAML en .github/workflows/ que define jobs y steps"
    - "runner: máquina virtual efímera donde corren los jobs de GitHub Actions"
    - "self-hosted runner: máquina propia que corre jobs de GitHub Actions"
  references_app_code_verified:
    - infra/hetzner/compose.prod.yml: existe
    - compose.yaml: existe
  open_questions:
    - ".github/workflows/ no existe en el repo (path tentativo). El scaffold debe crearlo
       con los dos YAMLs canónicos del módulo antes del primer release del track."

- id: D06
  status: done
  assumed_from_prereqs:
    D01: "el lector entiende imágenes y capas Docker"
    D02: "el lector sabe compose, healthchecks, redes implícitas"
    D05: "el pipeline CI/CD existe; D06 aplica el deploy a cada pieza"
  prepared_for_successors:
    D07: "el lector sabe qué piezas se despliegan; D07 añade estrategia de rollout por pieza"
    D08: "el lector sabe dónde van los secretos en cada pieza; D08 gestiona cómo se inyectan"
    E01: "el agente en E01 asume que hay worker, DB y observabilidad desplegados correctamente"
  deviations_from_spec: |
    - Se añadió Pieza 7 (LLM provider) porque el briefing la pedía explícitamente.
      No estaba en los 6 originales del título pero es parte natural del stack BATUTA.
    - Los precios de Cloudflare Pages, Neon, Supabase y Fly.io verificados con WebSearch 2026.
    - La tabla de costos PYME LATAM es orientativa (mayo 2026); se añadió advertencia explícita.
    - Tabla de decisión pgvector vs Qdrant Cloud cubre los criterios de volumen/latencia/costo.
  glossary_terms_introduced:
    - "worker (Docker Compose): servicio sin puerto que consume de una cola o workflow engine"
    - "perfil de despliegue: conjunto de propiedades (estado, escalabilidad, criticidad) que determina cómo se despliega un servicio"
  references_app_code_verified:
    - docker-compose.yml: existe (stack de referencia con Postgres + Phoenix + Temporal)
    - infra/hetzner/compose.prod.yml: existe
    - compose.yaml: existe
  open_questions: []

- id: D07
  status: done
  assumed_from_prereqs:
    D05: "el pipeline automático existe; el rolling/blue-green se implementa sobre él"
    D06: "el lector sabe qué piezas hay en el stack; la estrategia aplica a la API principalmente"
    C02: "el lector entiende migraciones Alembic; expand-contract las usa"
  prepared_for_successors:
    D08: "el lector sabe cuándo es seguro hacer rollback; D08 gestiona los secretos durante ese proceso"
    E05: "Temporal tiene su propia estrategia de deploy de workflows — el lector la entiende en contexto"
  deviations_from_spec: |
    - La implementación de blue-green con Traefik usa variables de entorno y labels condicionados.
      Es una simplificación vs un swap DNS completo, pero es la implementación factible
      en el stack Hetzner+Compose+Traefik que el lector ya tiene.
    - Feature flags: se implementó la versión más simple (tabla en DB) antes de mencionar
      LaunchDarkly/Unleash/PostHog, para anclar con el stack mínimo.
    - Canary con Traefik weighted services se menciona pero no se implementa en detalle:
      la complejidad no se justifica para la audiencia PYME del módulo.
  glossary_terms_introduced:
    - "expand-contract: patrón de migración de schema en tres fases sin downtime"
    - "blue-green deploy: estrategia con dos entornos idénticos y swap instantáneo de routing"
    - "canary deploy: estrategia que envía % del tráfico a la nueva versión antes del rollout completo"
    - "feature flag: interruptor en código que activa una funcionalidad para un subconjunto de usuarios"
  references_app_code_verified:
    - infra/hetzner/compose.prod.yml: existe
    - migrations/versions/: directorio existe
  open_questions:
    - "El ejercicio de feature_flag usa Pyodide (runner: pyodide). Verifica que
       el test no require imports de SQLAlchemy — el ejercicio usa solo dicts puros."

- id: D08
  status: done
  assumed_from_prereqs:
    D03: "el lector ya encontró sops+age mencionado en D03; D08 lo profundiza"
    D05: "los secretos de GitHub Actions (SSH_PRIVATE_KEY, HETZNER_HOST) son el contexto"
    D06: "el lector sabe qué secretos necesita cada pieza del stack"
  prepared_for_successors:
    E01: "el agente en E01 asume ANTHROPIC_API_KEY gestionada correctamente; D08 la establece"
    E05: "Temporal necesita su propio secret para conectar al servidor; D08 lo cubre"
  deviations_from_spec: |
    - sops v3.9.0 verificado como versión 2026 estable (WebSearch confirma artículos 2026).
    - Se añadió el patrón de rotación de API key con doble key porque el briefing
      lo pedía explícitamente como "rotación sin downtime".
    - Vault se cubre en nivel 2, no como default: la audiencia PYME raramente tiene
      equipo de plataforma para operarlo. Se pone el énfasis en sops+age.
    - El ejercicio de detección de secretos en logs (find_leaked_secrets) usa Pyodide
      con regex — es ejecutable en el navegador sin dependencias externas.
  glossary_terms_introduced:
    - "sops (Secrets OPerationS): herramienta que cifra archivos YAML/JSON/ENV manteniendo estructura"
    - "age: algoritmo de cifrado moderno con claves X25519; reemplaza GPG en casos simples"
    - "dynamic secrets (Vault): credenciales temporales generadas por Vault que expiran automáticamente"
    - "bus factor (secretos): número mínimo de personas cuya salida dejaría sin acceso a los secretos"
  references_app_code_verified:
    - compose.yaml: existe (usa ${ANTHROPIC_API_KEY:-} como referencia canónica)
    - infra/hetzner/compose.prod.yml: existe
  open_questions:
    - "D03 ya introdujo sops+age brevemente (ver su entrada en MODULES_STATUS). D08 profundiza
       sin contradecirlo. El integrador debe verificar que D03 no da instrucciones que D08 corrija."
```

**Decisiones transversales del lote D-EXPAND:**

1. **Orden de `ord`**: D05=32, D06=34, D07=35, D08=37. Se dejaron huecos intencionales (33, 36) para que Track F pueda intercalar fichas operativas si el integrador lo decide.

2. **Énfasis determinístico vs agéntico**: todos los módulos tienen la tabla canónica con mínimo 5 filas. En D05 y D07 el énfasis es especialmente fuerte porque el deploy es el tramo donde un agente jamás debe tener permisos de ejecución.

3. **Ejercicios de tipo `design`**: D05, D06, D07 tienen ejercicios de diseño (pipeline, compose, estrategia) además de code y code-fix. Esto sigue el tipo `design` de ARCHITECTURE.md §6.

4. **Tabla de costos PYME LATAM en D06**: precios verificados con WebSearch 2026. Incluye columna de notas para contexto. Se añadió advertencia de volatilidad de precios.

5. **Gestión de secretos cross-cutting**: D08 complementa pero no contradice a D03 (que los menciona brevemente) y a D05 (que usa GitHub Secrets). El integrador debe verificar la coherencia entre los tres módulos.

**Preparado para Track E:**
- El lector que termina D01-D08 tiene el stack completo en producción con CI/CD, observabilidad, secretos gestionados y estrategia de rollout. Puede recibir Track E (agentes) con la infraestructura lista para deployar agentes reales con monitoring de costo y métricas de calidad.

---

## Lote B-EXPAND — Track B ampliado (2026-05-16)

**Lote**: 7 módulos nuevos de Track B intercalados con B01-B06 existentes.

### Archivos creados

```
app/content/B/B07.md + B07.exercises.yaml + B07.quizzes.yaml
app/content/B/B08.md + B08.exercises.yaml + B08.quizzes.yaml
app/content/B/B09.md + B09.exercises.yaml + B09.quizzes.yaml
app/content/B/B10.md + B10.exercises.yaml + B10.quizzes.yaml
app/content/B/B11.md + B11.exercises.yaml + B11.quizzes.yaml
app/content/B/B12.md + B12.exercises.yaml + B12.quizzes.yaml
app/content/B/B13.md + B13.exercises.yaml + B13.quizzes.yaml
```

### Ords reasignados (frontmatter editado)

Los módulos B02-B06 y todos los C/D/E se corrieron para hacer espacio a los 7 nuevos.

| módulo | ord anterior | ord nuevo |
|--------|-------------|-----------|
| B07 (nuevo) | — | 7 |
| B01 | 8 | 8 (sin cambio) |
| B08 (nuevo) | — | 9 |
| B02 | 9 | 10 |
| B03 | 10 | 11 |
| B04 | 11 | 12 |
| B10 (nuevo) | — | 13 |
| B05 | 12 | 14 |
| B09 (nuevo) | — | 15 |
| B11 (nuevo) | — | 16 |
| B06 | 13 | 17 |
| B12 (nuevo) | — | 18 |
| B13 (nuevo) | — | 19 |
| C01 | 14 | 20 |
| C02 | 15 | 21 |
| C03 | 16 | 22 |
| D01 | 17 | 23 |
| D02 | 18 | 24 |
| D03 | 19 | 25 |
| D04 | 20 | 26 |
| E01 | 21 | 27 |
| E02 | 22 | 28 |
| E03 | 23 | 29 |
| E04 | 24 | 30 |
| E05 | 25 | 31 |
| E06 | 26 | 32 |

**Nota**: B10 (auth) fue puesto en ord=13 (antes de B09 agente) porque B09 declara B10 como prerequisite. El orden de prerequisite prevalece sobre el orden del enunciado.

### Decisiones clave por módulo

```yaml
- id: B07
  status: done
  assumed_from_prereqs:
    A05: "lector entiende imports y capas; la app como ejemplo ya es conocida"
  prepared_for_successors:
    B01: "modelo mental de UI fijado; HTTP es el protocolo que la alimenta"
    B03: "el lector ya sabe qué es DOM y render cycle antes de ver Jinja+HTMX"
  deviations_from_spec: |
    ord=7 en lugar del 7 solicitado — sin cambio. Puesto antes de B01 porque
    entender UI antes de HTTP tiene sentido pedagógico.
  glossary_terms_introduced:
    - "UI: capa que transforma datos en representación perceptible y acepta acciones"
    - "DOM: árbol de nodos en memoria que el navegador construye del HTML"
    - "render cycle: estado → render → evento → update"
    - "server-rendered: el render ocurre en el servidor"
    - "SPA: Single-Page Application, el render ocurre en el navegador"
  open_questions: []

- id: B08
  status: done
  assumed_from_prereqs:
    B01: "lector sabe HTTP request/response, status codes, headers"
    B07: "lector entiende qué es una API como UI para desarrolladores"
  prepared_for_successors:
    B02: "lector llega a FastAPI sabiendo qué es el contrato REST que va a implementar"
    B09: "lector conoce los 4 estilos de API antes de ver cómo conectar el agente"
  deviations_from_spec: |
    Se añadió un decision tree explícito como tabla ASCII para elegir entre REST/
    GraphQL/gRPC/webhook/SSE/WebSocket — el enunciado no lo pedía explícitamente
    pero es el ejercicio mental más valioso del módulo.
  glossary_terms_introduced:
    - "REST: convenciones sobre HTTP para exponer recursos como sustantivos"
    - "OpenAPI: estándar de descripción de APIs REST"
    - "webhook: API invertida — el sistema externo notifica al cliente"
    - "GraphQL: lenguaje de query para APIs con un solo endpoint"
    - "gRPC: RPC binario con Protocol Buffers sobre HTTP/2"
  open_questions: []

- id: B09
  status: done
  assumed_from_prereqs:
    B06: "lector sabe SSE desde el servidor y StreamingResponse"
    B08: "lector conoce los patrones de API"
    B10: "lector sabe auth (prerequisite declarado en frontmatter)"
  prepared_for_successors:
    B11: "lector ve que webhook puede llegar dos veces — idempotency key es la solución"
    E01: "los tres patrones de integración se aplican directamente al Anthropic SDK"
    E02: "LangGraph necesita un entry point — pull es el más común"
  deviations_from_spec: |
    B09 declara B10 como prerequisite (auth antes de agente). El ord de B10 fue
    ajustado a 13 (antes de B09 en ord=15) para mantener coherencia.
  glossary_terms_introduced:
    - "pull síncrono: el cliente llama y espera respuesta inmediata"
    - "pull asíncrono: el cliente llama y recibe job_id; consulta el estado"
    - "streaming SSE: el agente emite tokens o resultados parciales en tiempo real"
  open_questions: []

- id: B10
  status: done
  assumed_from_prereqs:
    B02: "lector sabe Depends para inyección de dependencias en FastAPI"
    B08: "lector sabe que las APIs tienen headers Authorization"
  prepared_for_successors:
    B09: "agente necesita auth antes de conectarse a nada"
    B11: "idempotency keys incluyen tenant — la noción de tenant viene de aquí"
    C03: "RLS Postgres es la extensión de auth al nivel de rows en DB"
  deviations_from_spec: |
    OAuth2 se cubre a nivel conceptual con los dos flows más relevantes
    (Authorization Code y Client Credentials). No se implementa un servidor OAuth2
    completo — eso requeriría una librería externa no justificada en este punto.
  glossary_terms_introduced:
    - "autenticación (AuthN): verificar la identidad del caller"
    - "autorización (AuthZ): verificar si la identidad tiene permiso"
    - "JWT: JSON Web Token — token firmado con claims"
    - "OAuth2: framework de delegación de autorización"
    - "scope: permiso específico dentro de una API key o token"
  open_questions: []

- id: B11
  status: done
  assumed_from_prereqs:
    B09: "lector sabe que un webhook puede llegar dos veces"
    B10: "idempotency keys incluyen tenant_id — la noción viene de auth"
  prepared_for_successors:
    B12: "versionar una API es otro mecanismo de no-romper contratos, como la idempotency"
    E05: "Temporal retry_policy asume actividades idempotentes — el módulo lo conecta explícitamente"
  deviations_from_spec: |
    El ejercicio de IdempotencyStore usa una clase en lugar de función pura — justificado
    porque el store necesita estado entre llamadas. Es el primer ejercicio del Track B
    que introduce clase como contenedor de estado (sin ORM).
  glossary_terms_introduced:
    - "idempotencia: propiedad de una operación que ejecutada N veces da el mismo resultado que 1"
    - "idempotency key: identificador único por intento de negocio, para deduplicación"
    - "backoff exponencial: estrategia de retry con espera creciente entre intentos"
    - "jitter: aleatoriedad añadida al backoff para evitar thundering herd"
    - "thundering herd: múltiples clientes reintentando al mismo tiempo y saturando el servidor"
  open_questions: []

- id: B12
  status: done
  assumed_from_prereqs:
    B08: "lector sabe qué es el contrato de una API REST"
    B11: "la idea de «no romper clientes» viene de idempotencia y contratos"
  prepared_for_successors:
    B13: "los tests de regresión de versiones son el tema central de testing"
    C01: "el schema de DB también se versiona (Alembic) — el mismo principio"
  deviations_from_spec: |
    Módulo de 30 minutos con dos ejercicios sustantivos: clasificador de breaking/
    non-breaking changes (Pyodide) y constructor de deprecation headers (Pyodide).
    No requiere runner: backend.
  glossary_terms_introduced:
    - "breaking change: cambio que rompe a los clientes existentes sin que actualicen"
    - "non-breaking change: cambio retrocompatible"
    - "expand-contract: estrategia de migración — añadir primero, eliminar después"
    - "Sunset header: RFC 8594 — anuncia la fecha de eliminación de un endpoint"
  open_questions: []

- id: B13
  status: done
  assumed_from_prereqs:
    B02: "lector sabe FastAPI y Depends"
    B04: "lector sabe las cuatro capas — los tests las atraviesan juntas"
    B12: "lector entiende contratos — los tests verifican contratos"
  prepared_for_successors:
    C01: "SQLAlchemy async requiere fixtures de DB en memoria — este módulo las establece"
    E01: "Anthropic SDK requiere mocks en tests — este módulo introduce el patrón"
  deviations_from_spec: |
    Los ejercicios son Pyodide (no backend) porque httpx no está disponible en Pyodide.
    Se simuló la lógica de validación de respuestas y el diseño de test cases como
    ejercicios de concepto puro. El ejercicio de backend real (AsyncClient con TestClient)
    queda documentado en el módulo como referencia para cuando el lector tenga el
    entorno local corriendo.
  glossary_terms_introduced:
    - "integration test: test que atraviesa varias capas juntas con DB en memoria"
    - "ASGITransport: adapter de httpx para testear apps ASGI sin servidor real"
    - "dependency_overrides: mecanismo de FastAPI para sustituir Depends en tests"
    - "coverage: porcentaje de líneas ejecutadas durante los tests — métrica, no objetivo"
  open_questions: []
```

### Glosario — términos añadidos en este lote

Los siguientes términos fueron introducidos y deben verificarse contra SHARED.md §1 en el próximo ciclo del integrador:
- UI, DOM, render cycle, server-rendered, SPA
- REST, OpenAPI, webhook, GraphQL, gRPC
- pull síncrono, pull asíncrono, streaming SSE (patrones de integración)
- AuthN, AuthZ, JWT, OAuth2, scope
- idempotencia, idempotency key, backoff exponencial, jitter, thundering herd
- breaking change, non-breaking change, expand-contract, Sunset header
- integration test, ASGITransport, dependency_overrides, coverage

### Preparado para Track C

El lector que completa B07-B13 llega a C01 con:
- Modelo mental de UI y ciclo de render (B07) — sabe por qué Jinja2 produce HTML
- Anatomía de API REST completa (B08) — puede leer el /docs de FastAPI
- Los tres patrones de integración del agente (B09) — base para E01/E02/E03
- Auth con API keys, JWT, OAuth2 (B10) — prerequisite para C03 (RLS + tenant_id)
- Idempotencia y retry seguro (B11) — prerequisite para E05 (Temporal)
- Versionado de API (B12) — conecta con Alembic (C01/C02) como versionado de DB schema

---

## INSERCIONES P0 — completado (2026-05-16)

**Archivos producidos**:
- `app/content/00/00-18.md` + `00-18.exercises.yaml` + `00-18.quizzes.yaml` — Git desde cero
- `app/content/D/D00.md` + `D00.exercises.yaml` + `D00.quizzes.yaml` — Linux operativo
- `app/content/E/E07.md` + `E07.exercises.yaml` + `E07.quizzes.yaml` — LLM evals y golden sets
- `app/content/D/D09.md` + `D09.exercises.yaml` + `D09.quizzes.yaml` — Git + CI flow

```yaml
- id: "00-18"
  lote: INSERCIONES P0
  status: done
  assumed_from_prereqs:
    "00-17": "lector tiene terminal, Python instalado, uv configurado, VS Code"
  prepared_for_successors:
    A01: "lector entiende qué es un repositorio y puede hacer git clone; A01 asume git básico funcionando"
    D00: "clave SSH ed25519 generada en 00-18 es la misma que se configura en D00 para SSH al servidor"
    D05: "lector conoce push, branch, PR — D05 los automatiza en CI/CD"
    D09: "lector conoce el flujo git básico que D09 conecta con CI"
  deviations_from_spec: |
    Se incluyeron 10 secciones canónicas (estilo Track 0) en lugar de 13:
    no aplica sección de "caso de uso real F" a este nivel — el lector de Track 0
    no tiene el vocabulario de fichas F todavía. La sección "determinístico vs agéntico"
    sí se incluyó porque es transversal y el concepto es visible en Git.
    El ejercicio Pyodide de simulación repo/staging/commit cubre el concepto
    de las tres zonas de Git de forma concreta y testeable sin necesitar Git real
    en el browser.
  glossary_terms_introduced:
    - "repositorio: carpeta con su historia completa de cambios"
    - "commit: foto del estado del repositorio en un momento dado"
    - "branch: línea paralela de commits"
    - "staging area: zona intermedia entre working directory y repository"
    - "Conventional Commits: estándar de formato para mensajes de commit"
    - "conflict: dos ramas modificaron la misma línea; requiere resolución manual"
  open_questions: []

- id: D00
  lote: INSERCIONES P0
  status: done
  assumed_from_prereqs:
    "00-18": "lector tiene clave SSH ed25519 generada; sabe qué es un repositorio"
    C03: "lector terminó la app multitenant; está listo para desplegarla"
  prepared_for_successors:
    D01: "lector puede conectarse al servidor por SSH; sabe qué es systemd; puede diagnosticar un proceso caído"
    D03: "lector sabe configurar ufw antes de exponer la app a internet; sabe manejar journalctl para post-deploy"
    D05: "lector entiende el servidor donde va a hacer deploy; puede leer los logs del pipeline"
  deviations_from_spec: |
    El módulo cubre las 13 secciones canónicas de Track D.
    Se añadió una sección sobre filesystem básico (FHS, df, du) que no estaba
    explícita en el plan pero que el Capstone E06 asume — el criterio «backup se
    restaura limpio» de E06 requiere saber dónde viven los datos (/srv).
    Los tres ejercicios Pyodide modelan conceptos reales (SSH config parser,
    diagnóstico de outage, crontab) sin necesitar acceso a un servidor real.
    La sección systemd incluye un unit file completo con Restart=on-failure
    porque ese era el bug más común identificado en el ROADMAP_GAPS.
  glossary_terms_introduced:
    - "SSH (Secure Shell): protocolo de conexión remota cifrada"
    - "systemd: init system de Ubuntu/Debian; gestiona el ciclo de vida de servicios"
    - "unit file: archivo de configuración de un servicio systemd"
    - "journald: daemon de logging de systemd; journalctl es su lector"
    - "ufw (Uncomplicated Firewall): interfaz de alto nivel para iptables en Ubuntu"
    - "socket activation: patrón donde systemd escucha en el puerto y activa el servicio al primer connection"
  open_questions:
    - "Ubuntu 24.04 usa ssh.socket en lugar de sshd.service para socket activation. Verificar en los ejercicios de D03 que el módulo apunta al servicio correcto."

- id: E07
  lote: INSERCIONES P0
  status: done
  assumed_from_prereqs:
    E06: "lector completó el Capstone; tiene un agente multitenant funcionando con golden set mínimo"
    D05: "lector tiene CI/CD configurado en GitHub Actions; sabe añadir jobs al workflow"
  prepared_for_successors:
    H06: "E07 introduce el golden set y las métricas; H06 extiende esto a drift detection en producción viva con alertas automáticas"
    D09: "E07 define el job de evals que D09 integra como required check en branch protection"
  deviations_from_spec: |
    Se coordinó con H06 (drift detection) para no duplicar: E07 cubre
    construcción del golden set, métricas (exact match, LLM-judge, schema validation,
    latencia/costo), frameworks (Promptfoo, DeepEval, Phoenix evals) y CI gate.
    H06 cubrirá drift detection en producción viva (alertas automáticas, comparación
    de distribuciones, dashboards). No hay solapamiento.
    El ejercicio de LLM-judge es simulado (determinístico) porque no podemos
    llamar a un modelo real en Pyodide. El comentario en el ejercicio explica que
    en producción el judge usa Anthropic SDK con temperature=0.
    Se incluyó tabla de cuántos casos según fase (5/20/50/100+) que no estaba
    en el spec pero responde la pregunta más frecuente del lector.
  glossary_terms_introduced:
    - "golden set: colección versionada de pares (input, output_esperado) del cliente"
    - "LLM-as-judge: evaluación donde un segundo modelo puntúa la salida del agente según rúbrica"
    - "exact match accuracy: proporción de predicciones idénticas al output esperado"
    - "eval threshold: nivel mínimo de calidad que un PR debe superar para mergear"
  open_questions:
    - "Promptfoo requiere Node.js. Verificar en D05 si el runner de GitHub Actions tiene Node disponible o si hay que añadir un setup-node step."

- id: D09
  lote: INSERCIONES P0
  status: done
  assumed_from_prereqs:
    "00-18": "lector sabe git básico: commit, branch, push, pull, conflict"
    D05: "lector tiene el pipeline CI/CD con GitHub Actions; sabe la anatomía de workflow/job/step"
  prepared_for_successors:
    E07: "D09 establece el flujo de CI donde E07 añade el job de evals como required check"
  deviations_from_spec: |
    El módulo es 45 min (el más corto de las inserciones P0) porque es
    esencialmente integración de 00-18 y D05 — no introduce conceptos nuevos,
    introduce el flujo completo.
    Se añadió la sección de «predecir si un PR bloquea» porque el spec lo pedía
    como ejercicio pero también hace sentido como prosa pedagógica.
    El ejercicio de can_merge() es el más útil: el lector entiende exactamente
    por qué el CI bloquea o no un PR, sin necesitar GitHub real.
    Se cubrió revert vs rollback con énfasis en por qué force push a main
    es destructivo — el ROADMAP_GAPS identificaba este como anti-patrón frecuente.
  glossary_terms_introduced:
    - "branch protection rule: configuración de GitHub que impide merge sin CI verde o sin review"
    - "squash merge: estrategia que combina todos los commits del branch en uno al llegar a main"
    - "hotfix flow: variante del flujo normal para bugs críticos en producción"
    - "git revert: operación que crea un nuevo commit que deshace un commit anterior sin reescribir historial"
  open_questions: []
```

**Resumen de riesgos cerrados**:

1. **00-18**: cierra el riesgo de que A01 asuma git sin haberlo enseñado. Sin este módulo, D03 (git clone en Hetzner) y D05 (push dispara CI) son incomprensibles para el lector de Excel.

2. **D00**: cierra el riesgo de «demo falla en producción». El lector que llega a Hetzner sin SSH/systemd/journalctl no puede diagnosticar nada. Identificado en ROADMAP_GAPS como el gap más bloqueante del track D.

3. **E07**: cierra el riesgo de «demo eterna». Sin golden set y CI de evals, el agente «funciona» es una opinión. Este módulo lo convierte en un número con umbral. Prerequisito para que E06 sea vendible con SLA.

4. **D09**: cierra el hueco de integración entre 00-18 y D05. El lector sabía git y sabía CI por separado; ahora ve el flujo completo como una unidad operativa diaria.

**Nota para el integrador**: los 4 módulos son 100% determinísticos en su contenido (Git, Linux, evals, CI). La tabla determinístico/agéntico en cada uno lo declara explícito. Ningún módulo requiere llamadas a LLM real — todos los ejercicios corren en Pyodide.
- Testing con fixtures async (B13) — los tests de C01 usan exactamente este patrón

---

## Track H — Operación de Producto — completado (2026-05-16)
### Lote H — 7 módulos (H01–H07)

```yaml
- id: H01
  status: done
  slug: runbooks-and-oncall
  ord: 240
  assumed_from_prereqs:
    D03: "el lector desplegó en Hetzner con Traefik; sabe dónde están los logs"
    D04: "el lector tiene Phoenix y ledger de costo funcionando"
  prepared_for_successors:
    H02: "el runbook es el artefacto que el postmortem mejora"
    H07: "RB-001 menciona hipótesis de Anthropic 529 → runbook H07-fallback"
  deviations_from_spec: |
    - Opsgenie declarado obsoleto (Atlassian detuvo ventas junio 2025, cierre abril 2027).
    - Grafana OnCall OSS archivado marzo 2026; se usa versión Cloud.
    - BetterStack elegido como default para PYME (plan gratuito verificado).
    - PagerDuty a 21 USD/usuario/mes (verificado WebSearch 2026).
  glossary_terms_introduced:
    - "runbook: documento ejecutable que convierte síntoma en acción sin razonamiento bajo presión"
    - "SEV1/SEV2/SEV3: niveles de severidad de incidente con criterios de respuesta medibles"
    - "MTTR: Mean Time To Resolve, métrica central de eficiencia del on-call"
  open_questions: []

- id: H02
  status: done
  slug: blameless-postmortems
  ord: 241
  assumed_from_prereqs:
    H01: "el lector sabe qué es SEV1/2/3 y tiene runbooks"
    D04: "el ledger de costo es fuente de verdad para el timeline"
  prepared_for_successors:
    H03: "el postmortem de un incidente de calidad del agente lleva a evals"
  deviations_from_spec: |
    - Plantilla de 7 secciones (vs 5 whys mencionado en brief): se añadieron "Qué funcionó"
      y "Qué no funcionó" como secciones explícitas para capturar aprendizaje positivo.
  glossary_terms_introduced:
    - "postmortem blameless: análisis de incidente que asigna causas al sistema, no a personas"
    - "5 whys: técnica de análisis causal que itera hasta llegar a una falla sistémica"
    - "action item (postmortem): compromiso con dueño, fecha y métrica verificable"
  open_questions: []

- id: H03
  status: done
  slug: agent-drift-and-evals
  ord: 242
  assumed_from_prereqs:
    E01: "el lector construyó el agente de auditoría con Anthropic SDK"
    D04: "Phoenix registra spans que se usan para extraer golden set histórico"
    E05: "Temporal se menciona para evals CI; el lector lo conoce"
  prepared_for_successors:
    H04: "el golden set tiene un costo de ejecución que H04 calcula"
  deviations_from_spec: |
    - Phoenix client API para `extract_golden_candidates` es pseudocódigo ilustrativo;
      la API real de Arize Phoenix puede diferir. El integrador debe verificar.
    - El bias de LLM-as-judge se cubre con nota [!cuidado] y mitigaciones concretas.
  glossary_terms_introduced:
    - "golden set: colección versionada de pares (input, expected_output) para evaluar calidad del agente"
    - "LLM-as-judge: uso de un LLM para evaluar la calidad del output de otro LLM"
    - "drift (agente): degradación del comportamiento útil sin cambio aparente en el código"
    - "regression_rate: proporción de casos que antes pasaban y ahora fallan en el golden set"
  open_questions:
    - "API exacta de Phoenix client para consultar spans — verificar con Arize docs actuales"

- id: H04
  status: done
  slug: finops-cost-monitoring
  ord: 243
  assumed_from_prereqs:
    D04: "app/middleware/cost.py y app/services/anthropic_client.py ya calculan cost_usd"
    H03: "los evals del golden set tienen un costo de tokens calculado con esta lógica"
  prepared_for_successors:
    H05: "los números de costo por tenant alimentan el plan de escalado"
  deviations_from_spec: |
    - Precios de claude-sonnet-4-6 tomados del anthropic_client.py de la app (fuente canónica).
    - Vantage y CloudZero mencionados como herramientas para Etapa 4+ en AWS/GCP; no recomendados
      para Hetzner PYME (overhead de 10-25% del cloud bill no se justifica hasta 100+ tenants en cloud).
    - Hard stop implementado como degradación graceful (Haiku), no como 503.
  glossary_terms_introduced:
    - "FinOps (aplicado a agentes IA): sistema de monitoreo de costo por tenant con alertas y optimización"
    - "hard stop (presupuesto): límite de costo que activa degradación graceful al 100% del presupuesto"
  open_questions: []

- id: H05
  status: done
  slug: scale-small-to-big
  ord: 244
  assumed_from_prereqs:
    D03: "Hetzner + Traefik es la base de Etapa 1"
    D07: "expand-contract para migrar de SQLite a Postgres en Etapa 2"
    H04: "el ledger de costo alimenta el ratio infra/revenue"
  prepared_for_successors:
    H06: "el plan de escalado determina qué estrategia de backup es apropiada"
    H07: "a partir de Etapa 2, el gateway multi-modelo tiene sentido económico"
  deviations_from_spec: |
    - Precios Hetzner verificados con WebSearch 2026: CX22=€4.49, CX32=€6.80, LB11=€5.39.
    - Neon paid a ~$19/mes verificado con contexto de mercado 2026.
    - KEDA se posiciona claramente como herramienta de Etapa 4 (requiere k3s/k8s).
    - Fly.io mencionado para staging/apps secundarias; no para agente de producción (cold start).
    - Las 6 reglas "no quemar dinero" son el núcleo pedagógico del módulo.
  glossary_terms_introduced:
    - "escalado vertical: aumentar los recursos del mismo servidor (más vCPU, más RAM)"
    - "escalado horizontal: añadir más servidores del mismo tipo con balanceador de carga"
    - "ratio infra/revenue: proporción del costo de infraestructura sobre el revenue mensual"
    - "KEDA: Kubernetes Event-Driven Autoscaling, escala workloads basado en profundidad de queue"
  open_questions: []

- id: H06
  status: done
  slug: restore-drills
  ord: 245
  assumed_from_prereqs:
    D03: "infra/scripts/backup.sh genera el backup que el drill restaura"
    E05: "el workflow Temporal del drill sigue el patrón de RestoreDrillWorkflow"
  prepared_for_successors:
    H07: "el drill mensual incluye verificar que el failover de modelo también funciona"
  deviations_from_spec: |
    - RTO=4h y RPO=1h declarados como valores razonables para PYME LATAM; justificados
      en la sección de mecanismos.
    - Se añadió el workflow Temporal como automatización del drill (pedido implícito en brief
      por conexión con E05).
    - Litestream mencionado como opción de RPO~5min sin costo adicional relevante.
  glossary_terms_introduced:
    - "RTO (Recovery Time Objective): tiempo máximo desde el incidente hasta restaurar el servicio"
    - "RPO (Recovery Point Objective): máximo de datos que se puede perder en un incidente"
    - "restore drill: ejercicio programado de restauración de backup en infraestructura paralela"
  open_questions: []

---

## UX-FIX F2+F3+F5 — Track 0 engagement dynamics (2026-05-16)

**Agente**: Sonnet 4.6 (fix-batch F2+F3+F5)

**Archivos modificados**:
- `app/content/00/00-01.md` … `app/content/00/00-18.md` — marcadores inline insertados
- `app/content/00/00-03.quizzes.yaml` — bytecode eliminado del feedback
- `app/content/00/00-06.quizzes.yaml` — PEP 8 (×2) reemplazado por "convención estándar de Python"
- `app/content/00/00-09.md` — bytecode eliminado de "Cómo funciona por dentro"
- `app/content/00/00-09.quizzes.yaml` — AST + bytecode eliminados del feedback
- `app/content/00/00-16.md` — lockfile reemplazado por "versiones exactas de cada paquete"
- `scripts/lint_track0_terms.py` — creado (nuevo)

```yaml
- id: UX-FIX-F2
  status: done
  scope: app/content/00/ — los 18 módulos del Track 0
  description: |
    Marcador INLINE_EXERCISE insertado después de la sección "Idea central"
    (antes de "Por qué importa") en los 18 módulos. Marcador INLINE_QUIZ
    insertado después de "Ejemplo conducido" en los 18 módulos.
    Total: 18 INLINE_EXERCISE + 18 INLINE_QUIZ = 36 marcadores Fix2.
  assumed_from_prereqs:
    F1: "templating.py + module.html + app.js procesan los marcadores INLINE_EXERCISE e INLINE_QUIZ"
  open_questions:
    - "F1 debe estar activo para que los marcadores sean renderizados"

- id: UX-FIX-F3
  status: done
  scope: app/content/00/ — 8 módulos críticos (00-01, 00-02, 00-05, 00-06, 00-10, 00-11, 00-12, 00-13)
  description: |
    Quiz de comprensión (INLINE_QUIZ) insertado inmediatamente después de
    "Idea central" (antes de "Por qué importa") en los 8 módulos críticos.
    Se usan quizzes conceptuales existentes: formula-vs-code, prompt-symbol,
    repl-cycle, variable-is-label, equals-vs-assign, list-index-zero,
    accumulator-init, return-vs-print. No hubo necesidad de crear quizzes nuevos.
    Total: 8 INLINE_QUIZ adicionales (Fix3).
  open_questions: []

- id: UX-FIX-F5
  status: done
  scope: scripts/lint_track0_terms.py + app/content/00/
  description: |
    Script lint_track0_terms.py creado. Escanea .md y .yaml bajo app/content/00/
    detectando 19 términos prohibidos con exclusiones por archivo y por bloque
    <details>. Primera ejecución: 10 violaciones → reducidas a 7 tras ajustar
    lint para ignorar <details> → 0 violaciones tras corregir los 7 restantes.
    Correcciones: bytecode (×3), PEP 8 (×2), AST (×1), lockfile (×1).
    Resultado final: lint_track0_terms: 0 violations — Track 0 is clean.
  open_questions: []
```

**Totales de marcadores inline**:
- Fix2: 18 INLINE_EXERCISE + 18 INLINE_QUIZ = 36
- Fix3: 8 INLINE_QUIZ adicionales (check de comprensión tras Idea central)
- **Total global: 44 marcadores** (18 ejercicios + 26 quizzes)

**Lint**: 10 hallazgos iniciales → 0 tras correciones (7 en texto + 3 ya en `<details>`)

**Validación**: 54 archivos MD+YAML parsean OK; seed requiere PostgreSQL (Docker); HTTP 200 en `/m/excel-to-python-bridge` tras `docker compose restart app`.

- id: H07
  status: done
  slug: multi-model-failover
  ord: 246
  assumed_from_prereqs:
    E01: "app/services/anthropic_client.py es el punto de extensión para añadir fallback"
    H04: "el costo de tokens justifica el routing cost-optimal por tipo de tarea"
    H05: "LiteLLM se introduce en Etapa 2+ con Docker Compose"
  prepared_for_successors:
    "G07 (capstone comercial)": "el gateway multi-modelo es un diferenciador en la propuesta al cliente"
  deviations_from_spec: |
    - Helicone mencionado como capa de observabilidad complementaria a Phoenix.
    - Bedrock cubierto como solución para data residency LATAM (LGPD Brasil, sa-east-1).
    - LiteLLM versión main-stable usada en el ejemplo de compose; verificar tag exacto.
    - OpenRouter posicionado para Etapa 1 (sin contenedor adicional); LiteLLM para Etapa 2+.
  glossary_terms_introduced:
    - "gateway de modelos: capa de abstracción entre el agente y múltiples proveedores LLM"
    - "data residency: requisito de que los datos se procesen en una región geográfica específica"
    - "LiteLLM: proxy open source OpenAI-compatible para 100+ proveedores LLM"
  open_questions:
    - "Verificar tag estable de LiteLLM al publicar (main-stable puede cambiar)"
    - "Verificar disponibilidad de claude-sonnet-4-6 en Bedrock sa-east-1 a la fecha de publicación"
```

**Decisiones transversales del lote H:**

1. **Todos los precios en USD/mes y EUR/mes con rangos verificados**: Hetzner (WebSearch 2026),
   Anthropic (anthropic_client.py del repo), PagerDuty/BetterStack (WebSearch 2026).

2. **H05 es el módulo central**: 90 min, 4 etapas con números, 6 reglas, tabla de upgrade path,
   3 ejercicios ejecutables en Pyodide (stage classifier, cost calculator, plan mensual).

3. **Ejercicios de tipo `design` con validación en código**: todos los módulos tienen ≥1 ejercicio
   de diseño que produce código verificable (validate_runbook, validate_golden_set, build_scaling_plan).

4. **Determinístico vs agéntico en cada módulo**: tabla canónica con ≥5 filas. El énfasis es que
   la operación de producción es mayoritariamente determinística (monitoreo, alertas, backup),
   pero las decisiones estratégicas (cuándo escalar, qué optimizar, cuándo hacer fallback) son agénticas.

5. **Continuidad con Track D**: H01 apunta a D03 (backup.sh) y D04 (Phoenix). H06 apunta a
   infra/scripts/backup.sh. H07 apunta a app/services/anthropic_client.py. Todos los paths son reales.

**Preparado para Track G (Negocio):**
- El lector que termina H01-H07 puede operar el servicio en producción y responder incidentes.
- H04 y H05 dan los números de costo e infraestructura que G03 (pricing) usa para calcular márgenes.
- H07 (multi-modelo) y H03 (evals) son diferenciadores técnicos en la propuesta comercial de G02.

---

## UX-FIX F4 — Excel bridge en A01/B01/B07 (2026-05-16)

**Archivos editados** (solo inserción de sección, sin tocar el resto del contenido):
- `app/content/A/A01.md` — sección "Puente desde Excel" insertada después de "## Idea central"
- `app/content/B/B01.md` — sección "Puente desde Excel" insertada después de "## 2. Idea central" (sin número para no romper numeración 1-13)
- `app/content/B/B07.md` — sección "Puente desde Excel" insertada después de "## 2. Idea central" (sin número para no romper numeración 1-13)

```yaml
- id: UX-FIX-F8
  status: done
  type: ux-fix
  date: 2026-05-16
  rationale: |
    Los 4 módulos más densos del primer tercio del curso superaban 6+ min de lectura.
    Audiencia Track 0 (Excel-only) no está preparada para contenido técnico profundo en el flujo principal.
    Se movió contenido "para profundizar" a bloques <details> colapsables. Nada se eliminó.
  modules_patched:
    - app/content/00/00-06.md (variables-and-types)
    - app/content/00/00-13.md (your-own-functions)
    - app/content/A/A01.md (interpreter-and-uv)
    - app/content/B/B07.md (what-is-a-ui)
  word_counts:
    before:  { 00-06: 1371, 00-13: 1763, A01: 1874, B07: 2006 }
    visible_after: { 00-06: 1161, 00-13: 1219, A01: 1185, B07: 1239 }
    details_blocks_added: { 00-06: 4, 00-13: 7, A01: 6, B07: 7 }
  content_moved_to_details:
    00-06:
      - IEEE 754 / precisión flotante
      - Truthy/falsy y conversión implícita de bool
      - Inmutabilidad, id() e identidad de objetos
      - Tabla Excel↔Python completa
    00-13:
      - Type hints (para VS Code)
      - "*args/**kwargs"
      - Convenciones de naming para funciones
      - Función pura vs función con efectos
      - Funciones que reciben listas/dicts
      - Ejemplo conducido completo (pipeline de 3 funciones)
      - Errores típicos extendidos (2 de 4)
    A01:
      - Pipeline completo CPython (AST, bytecode, __pycache__)
      - Inspección con dis
      - Detalles de uv.lock y resolución SAT
      - Determinístico vs agéntico tabla
      - Error __pycache__ con versión antigua
    B07:
      - Tipos de nodo del DOM (Element, HTMLElement, NodeType)
      - Bundle sizes / SPA justification / Web Components
      - Tipos de UI tabla completa
      - Render cycle detallado bato-learning paso a paso
      - Determinístico vs agéntico tabla
      - Ejemplo conducido completo (lista de facturas)
      - Puente desde Excel tabla
  open_questions: []

- id: UX-FIX-F4
  status: done
  type: ux-fix
  rationale: |
    Track 0 cumple el contrato Excel↔código con secciones "Puente desde Excel" en sus 18 módulos.
    Los primeros módulos de Track A y B rompían ese contrato implícito. El lector Excel-user
    se sentía abandonado en A01 (bytecode/dis/AST sin ancla Excel) y en B07 (DOM/SPA/useState
    sin ancla Excel). Se insertan tres secciones de puente sin alterar el contenido existente.
  modules_patched:
    - A01 (interpreter-and-uv): tabla Excel↔Python, analogía del intérprete como "abrir .xlsx"
    - B01 (http-and-the-browser): tabla Excel↔HTTP, analogía libro-como-servidor y fórmula-como-cliente
    - B07 (what-is-a-ui): tabla Excel↔UI-web, analogía DOM=celdas, server-rendered=Excel-Online vs SPA=Excel-desktop
  renumbering: |
    A01 no tiene secciones numeradas — sin renumeración necesaria.
    B01 y B07 tienen secciones numeradas 1-13; la sección "Puente desde Excel" se insertó
    sin número (heading plano) entre la sección 2 y la 3, preservando la numeración original.
  open_questions: []
```
