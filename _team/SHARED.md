# SHARED.md — contrato compartido del agents team

> Cualquier Sonnet que escriba un módulo lee este archivo **antes** de empezar a
> redactar. Si un módulo introduce un término que ya está en el Glosario, usa la
> definición de aquí palabra por palabra. Si necesita inventar un término nuevo,
> primero lo añade aquí en un PR y luego lo usa.
>
> Idioma: prosa y comentarios en **español**, identificadores y código en
> **inglés**. Convención fija de todo el repo.

---

## 1. Glosario canónico

Estas definiciones son **autoritativas**. Reemplaza cualquier formulación previa
del CURRICULUM.md o del site actual que diga algo distinto.

### 1.1 Lenguaje y proceso

- **Intérprete de Python**: programa (`python3` ejecutable, normalmente CPython)
  que lee un archivo `.py` token por token, lo compila a *bytecode* en memoria,
  y lo ejecuta en una *máquina virtual* propia. No hay paso de "compilación"
  visible para el usuario, pero existe y se cachea en `__pycache__/`.
- **Bytecode**: representación intermedia, binaria, del código Python. El usuario
  casi nunca lo manipula directo.
- **Pyodide**: CPython compilado a WebAssembly. Corre dentro del navegador. **No
  es** una reimplementación: es el mismo intérprete con un puente JS↔Python.
- **uv**: gestor de proyectos Python (Astral). Reemplaza a pip + virtualenv +
  pip-tools. Lockfile determinista. Es el comando que el repo usa siempre;
  cualquier ejemplo que diga `pip install x` es incorrecto en este curso.

### 1.2 Tipos y mutabilidad

- **Inmutable**: el objeto no se puede modificar después de creado. Reasignar la
  variable cambia a qué objeto apunta, no el objeto. Aplica a `int`, `float`,
  `str`, `tuple`, `frozenset`, `bytes`.
- **Mutable**: el objeto se puede modificar en su lugar. `list`, `dict`, `set`,
  instancias de clases por defecto.
- **Identidad vs igualdad**: `is` compara identidad (mismo objeto en memoria),
  `==` compara valor. Esto se usa para explicar por qué `a = [1]; b = a;
  b.append(2)` cambia `a`.

### 1.3 Web y arquitectura

- **HTTP request/response**: ciclo síncrono entre cliente y servidor. Verbo
  (`GET`, `POST`, ...), URL, headers, body. La respuesta tiene status, headers,
  body. Sin estado entre requests; el estado lo aporta DB o cookie/sesión.
- **API**: contrato de endpoints que un servidor expone. En este curso "API" =
  "API HTTP", normalmente JSON. Si hablamos de otro tipo de API lo nombramos
  explícito (CLI API, SDK API).
- **Capa (layer)**: agrupación de funciones/clases con una sola responsabilidad
  y una dirección de dependencia. En bato-learning las capas son, de fuera hacia
  dentro: `routers` → `services` → `repos` → `models`. **Una capa nunca importa
  desde una capa más externa.** Esa es la regla operativa.
- **Router**: archivo en `app/routers/` que define endpoints HTTP. Valida
  entrada (Pydantic), llama al servicio, formatea la respuesta. No toca DB
  directo.
- **Servicio**: función o clase en `app/services/` que implementa lógica de
  negocio. Es la única capa que orquesta varios repos. No conoce HTTP.
- **Repo (repository)**: función en `app/repos/` que ejecuta una query
  concreta. Recibe `AsyncSession` por parámetro, devuelve modelos o filas. No
  conoce reglas de negocio.
- **Modelo (ORM model)**: clase en `app/models/` que mapea a una tabla. Define
  columnas y relaciones. No define queries.
- **Migración**: archivo versionado en `migrations/versions/` generado por
  Alembic. Describe el delta entre dos estados del schema. Es el único lugar
  donde el schema cambia.

### 1.4 Datos

- **Schema**: el conjunto de tablas, columnas, tipos y restricciones de una BD.
  Vive en código (modelos + migraciones), no en la BD "a mano".
- **Transacción**: bloque de queries que se commitea o se aborta como un todo.
  En SQLAlchemy async se abre con `async with session.begin():`.
- **RLS (Row-Level Security)**: política Postgres que filtra filas según una
  variable de sesión (`current_setting('app.tenant_id')`). El curso lo enseña
  pero **el código que se construye corre sobre SQLite**: el módulo de RLS
  explica el patrón y lo replica con un filtro explícito por `tenant_id` en
  cada repo.

### 1.5 Agentes y LLMs

- **Agente**: un loop `(prompt → modelo → tool_use → tool_result → modelo →
  ...)` que termina cuando el modelo dice `stop_reason: end_turn` o cuando
  alguien lo corta. Lo que lo distingue de un simple "llamar al LLM" es ese
  bucle con herramientas.
- **Harness**: el código alrededor del SDK que gestiona el loop, los hooks, las
  skills, la memoria, los permisos. Claude Code **es** un harness. Cuando
  migras a SDK propio o LangGraph, lo reconstruyes.
- **Skill**: archivo Markdown con frontmatter (`name`, `description`,
  `trigger`, ...) que describe una receta o procedimiento. La carga
  selectiva la decide el harness, no el modelo.
- **Tool (herramienta)**: función externa que el modelo puede invocar con
  argumentos estructurados (JSON schema). La declara el harness, la ejecuta el
  harness, el modelo solo emite `tool_use`.
- **Prompt caching**: marca `cache_control` en bloques del prompt para que
  Anthropic los almacene 5 min o 1 h y cobre menos en cada hit. El curso lo
  enseña como decisión arquitectónica, no como tweak.
- **Determinismo (Temporal)**: el código de workflow no puede llamar a
  `datetime.now`, `random`, IO, ni LLMs. Solo `execute_activity`. Las
  actividades son donde vive todo lo no-determinista. Si rompes esto, Temporal
  hard-falla en el replay.
- **Tenant**: cliente/organización en una app multitenant. Es una dimensión
  obligatoria en todo: en cada fila, en cada `idempotency_key`, en cada
  `thread_id`, en cada log, en cada métrica.
- **Loop de agente**: el ciclo
  `prompt → modelo → tool_use → tool_result → modelo → ...`. Termina cuando
  el modelo emite `stop_reason: end_turn` o cuando el harness lo corta por
  límite de iteraciones, tiempo o coste.
- **MCP (Model Context Protocol)**: estándar que estandariza cómo un harness
  expone tools y recursos a un modelo. El curso lo menciona y lo consume con
  `langchain-mcp-adapters` cuando un caso F lo justifica; no se enseña a
  escribir un servidor MCP propio.

### 1.6 Determinístico vs agéntico — vocabulario operativo

- **Tramo determinístico**: parte de un flujo donde la salida es función
  cerrada de la entrada. Se programa con código tradicional. Auditable,
  testeable, barato. Ejemplos: parseo de CSV, agregaciones SQL, validación
  contra un schema Pydantic.
- **Tramo agéntico**: parte de un flujo donde la salida exige razonamiento
  contextual o redacción para humano. Se programa con modelo + tools en un
  loop. Caro, no determinístico, exige observabilidad. Ejemplos: emparejar
  una transacción con descripción ambigua, redactar un hallazgo, decidir si
  un duplicado es timing o error.
- **Fallback humano**: el camino que toma el flujo cuando el modelo dice "no
  sé" o cuando la confianza es baja. Toda ficha F lo declara explícito.

### 1.7 Track F — vocabulario de negocio

> Nota industrias canónicas: las 10 industrias para `industries_instanced` son
> `retail`, `manufactura`, `servicios-fin`, `salud`, `logistica`,
> `construccion`, `hospitalidad`, `serv-prof`, `agro`, `energia`. Si una ficha
> necesita educación, social, gov u otra, registrarla aquí primero o
> reasignarla a la industria canónica más cercana.


- **Caso de uso**: una ficha F. Identifica un problema operativo concreto y
  su solución agéntica. Tiene id `F-DEPT-NN`.
- **Big corp**: empresa con presupuesto > 1 M USD/año en software empresarial.
  Compra Anaplan, SAP IBP, Workday, Salesforce Einstein, BlackLine, Trintech.
- **PYME LATAM**: empresa de 10–500 empleados en LATAM. Vive en Excel + un
  ERP local (Siigo, Contpaq, World Office, Alegra, Aspel). Presupuesto típico
  para automatización: 200–2000 USD/mes.
- **Instancia industria**: dentro de una ficha, las variantes que muestran
  cómo cambia el caso entre dos industrias (retail vs manufactura, salud vs
  agro). No es una ficha aparte; es una sección.
- **Workflow de negocio**: el conjunto de pasos que **una operación
  empresarial real** sigue (recibir factura → validar → contabilizar →
  pagar). Distinto del workflow Temporal (que es código).
- **Skill por tenant**: skill con slots variables (tono, glosario, KPIs,
  fuentes) que se rellenan en onboarding.
- **Golden set**: 5–20 ejemplos del cliente con salida esperada. Cualquier
  cambio al agente se evalúa contra el golden set antes de promover a prod.

### 1.7.1 Términos operativos (sufijo Track F)

- **3-way match**: comparación tripartita orden de compra ↔ recepción ↔ factura
  del proveedor antes de aprobar el pago (F-CMP-03).
- **OTD (on-time delivery)**: porcentaje de entregas a tiempo de un proveedor
  o canal (F-CMP-02, F-OPS-04).
- **DSO (days sales outstanding)**: días promedio que tarda el cliente en
  pagar una factura. KPI core de F-FIN-04.
- **EOQ (economic order quantity)**: cantidad de pedido que minimiza el costo
  total (holding + ordering) bajo demanda determinística (F-OPS-03).
- **ROP (reorder point)**: nivel de inventario que dispara una nueva orden;
  función de lead time y safety stock (F-OPS-03).
- **eNPS (employee NPS)**: encuesta de 1 pregunta a empleados (0–10) con
  segmentación promotor/pasivo/detractor (F-RH-02).
- **BANT**: Budget, Authority, Need, Timing — criterios clásicos de
  calificación de lead (F-VTA-01).
- **ICP (ideal customer profile)**: descripción del cliente ideal en variables
  observables (industria, tamaño, geografía, stack). Anclaje del scoring (F-VTA-01).
- **CAC / LTV**: costo de adquisición / valor de vida del cliente. Definidos
  en F-MKT-02.
- **MRR / ARR / churn**: monthly/annual recurring revenue / tasa de baja.
  Vocabulario SaaS (F-CX-04).
- **SoV (share of voice)**: proporción de menciones de la marca vs
  competidores en un canal (F-MKT-04).
- **Idempotency key**: clave única por side-effect agéntico; siempre incluye
  `tenant_id` (D04, E05, fichas F con escritura).
- **Fallback humano**: ruta del workflow donde, ante baja confianza, el agente
  delega a un humano. Hard-coded, no configurable.

### 1.8 Pyodide y el editor

- **Editor del módulo**: instancia de CodeMirror 6 con autocompletado mínimo,
  syntax highlighting Python, y tema acordado.
- **Namespace del ejercicio (`__ns`)**: dict aislado por ejercicio donde corre
  el código del usuario. Los tests del ejercicio corren en el mismo namespace
  para poder inspeccionar variables.
- **`__cap`**: `StringIO` que captura `stdout` del ejercicio. Los tests lo leen
  con `__cap.getvalue()`. Si un módulo introduce captura distinta lo declara
  explícito.

---

## 2. Personajes y ejemplos canónicos

**Regla**: cuando un módulo necesita un ejemplo de dominio, usa **estos**. No
inventes "compañía X" o "FooCorp". Mantener los mismos personajes a través de
los módulos es lo que crea hilo conductor.

### 2.1 Tenants

Los **tres primeros** son los principales de Tracks A–E (módulos técnicos). Los
demás existen para que las fichas Track F puedan instanciar industrias sin
inventar nombres ad-hoc.

| slug              | nombre                          | industria          | tamaño     | uso principal |
|-------------------|---------------------------------|--------------------|------------|----------------|
| `acme`            | ACME Manufacturing              | manufactura        | mediana    | tenant principal, ejemplos por defecto |
| `globex`          | Globex Logistics                | logística / 3PL    | mediana    | segundo tenant para multitenancy |
| `initech`         | Initech Audit                   | servicios fin.     | pequeña    | edge cases, casos límite |
| `andina`          | Constructora Andina             | construcción       | mediana    | fichas F-CMP, F-LEG, F-FIN, obra LATAM |
| `sanrafael`       | Clínica San Rafael              | salud privada      | mediana    | fichas F-CX, F-RH, F-LEG, manejo PII |
| `cafetera`        | Cooperativa Cafetera del Valle  | agro / exportación | grande     | fichas F-OPS, F-CMP, F-FIN multi-moneda |
| `expreslog`       | Logística Express               | logística / 3PL    | mediana    | fichas F-OPS, F-VTA, last mile |
| `tiendabox`       | TiendaBox Retail                | retail / e-comm    | mediana    | fichas F-VTA, F-MKT, F-OPS, multi-canal |
| `cooppopular`     | Coop. Popular de Crédito        | servicios fin.     | mediana    | fichas F-FIN, F-LEG, KYC/AML |
| `mesonurbano`     | Mesón Urbano F&B                | hospitalidad       | pequeña    | fichas F-OPS, F-CX, F-RH, alta rotación |
| `solenergy`       | SolEnergy Distribuidora         | utilities / energía | grande    | fichas F-OPS, F-CTA, regulación sectorial |
| `consultorabc`    | Consultora ABC                  | servicios prof.    | pequeña    | fichas F-VTA, F-MKT, F-RH, billable hours |

**Reglas de uso**:

- Módulo técnico (Tracks A–E) que necesita 1 tenant: **ACME**.
- Módulo técnico que muestra aislamiento: **ACME + Globex**.
- Módulo técnico con edge case: **Initech**.
- Ficha F: usa **los dos tenants que mejor encajen** con la industria
  declarada en `industries_instanced` (ver `_team/MODULES.md`).
- **No inventes** un tenant nuevo sin proponerlo aquí primero.

### 2.1.1 Vendors big corp (para sección 2 de fichas F)

Cuando una ficha F describe "cómo lo hacen las big corps hoy", usa nombres
reales del catálogo siguiente. Si necesitas uno no listado, lo añades aquí
primero. Precios orientativos para anclar al lector — no son cotizaciones.

| Categoría | Vendors típicos | Precio orientativo |
|-----------|-----------------|--------------------|
| Conciliación contable | BlackLine, Trintech, FloQast | 50–250 USD/usuario/mes; setup 20–80 k USD |
| ERP enterprise | SAP S/4HANA, Oracle Fusion, NetSuite | 1500–10000 USD/mes; impl. 100k–1M USD |
| Demand / supply planning | SAP IBP, Anaplan, o9, Kinaxis | Anaplan desde 1000 USD/usuario/mes; impl. 100k+ |
| FP&A | Workday Adaptive, Anaplan, Pigment, Cube | 30–200 USD/usuario/mes; impl. 30k–200k |
| CRM | Salesforce Einstein, HubSpot, Dynamics 365 | 80–300 USD/usuario/mes |
| Procurement | Coupa, SAP Ariba, Jaggaer | 20k–500k USD/año |
| Contract / CLM | Ironclad, DocuSign CLM, Icertis | 50–200 USD/usuario/mes |
| HRIS | Workday, SuccessFactors, BambooHR | 6–50 USD/empleado/mes |
| Ticketing / CX | Zendesk, ServiceNow, Salesforce SC | 50–200 USD/agente/mes |

### 2.1.2 ERPs y herramientas LATAM (para sección 3 de fichas F)

Cuando una ficha describe "cómo vive una PYME LATAM", apunta a herramientas
reales del mercado regional. **No usar Quickbooks ni Xero** como representante
de PYME LATAM por defecto: la mayoría usa local.

| Categoría | Herramientas LATAM | Países típicos |
|-----------|--------------------|----------------|
| Contabilidad / facturación | Siigo, World Office, Alegra, Aspel SAE/COI, Contpaq i | CO, MX, PE, CL |
| Nube hispana SMB | ContaAzul, Bsale, Defontana | BR, CL, AR |
| Punto de venta | Aleph, Sirvap, Loyverse | MX, CO |
| Banca / pagos | Plaid LatAm (Belvo), Conekta, Mercado Pago, Wompi | regional |
| Logística / WMS | Slamcodes, Drivin, Beetrack | regional |
| BI ligero | Power BI, Looker Studio, Excel/Google Sheets | universal |

> [!nota]
> El lector típico **ya** trabaja con uno o dos de estos. Ese conocimiento es
> activo, no carga; el curso lo aprovecha en fichas F.

### 2.1.3 Industrias canónicas

Las ≥10 industrias que el catálogo Track F instancia. Cada ficha F declara
`industries_instanced: [...]` con al menos 2 de esta lista. Distribuir entre
fichas para que cada industria aparezca al menos en 3 fichas distintas.

| id              | industria                       | tenants asociados                       |
|-----------------|---------------------------------|-----------------------------------------|
| `retail`        | Retail / E-commerce             | `tiendabox`                              |
| `manufactura`   | Manufactura PYME-mediana        | `acme`                                   |
| `servicios-fin` | Servicios financieros           | `initech`, `cooppopular`                 |
| `salud`         | Salud privada / laboratorios    | `sanrafael`                              |
| `logistica`     | Logística / 3PL / last mile     | `globex`, `expreslog`                    |
| `construccion`  | Construcción / Real estate      | `andina`                                 |
| `hospitalidad`  | Hospitalidad / F&B              | `mesonurbano`                            |
| `serv-prof`     | Servicios profesionales         | `consultorabc`                           |
| `agro`          | Agro / Agroindustria            | `cafetera`                               |
| `energia`       | Energía / Utilities             | `solenergy`                              |

### 2.2 Dominio: auditoría financiera mensual

El dominio recurrente del curso es **auditoría financiera mensual** (lo que
BATUTA hace en producción). El curso construye una versión simplificada:

- **Entidades**: `invoice` (factura), `vendor` (proveedor), `audit_run`
  (ejecución de auditoría), `finding` (hallazgo).
- **Caso de uso transversal**: el agente `monthly_audit` ingiere las facturas
  del período, busca anomalías (proveedor nuevo, monto fuera de rango,
  duplicados), produce un `audit_report` con findings.
- **Período**: siempre `"2026-04"` en ejemplos por defecto. No usar fechas
  móviles ("este mes") para mantener tests reproducibles.
- **Montos**: en EUR, sin separador de miles en código, formateados en prosa.

### 2.3 La app misma (`bato-learning`)

Cuando un módulo necesita un ejemplo full-stack real, usa la propia app:

- `app/models/exercise.py` cuando enseña ORM.
- `app/routers/modules.py` cuando enseña routing.
- `app/services/progress.py` cuando enseña capa de servicio.
- `app/integrations/anthropic_chat.py` cuando enseña SDK Anthropic.
- `app/main.py` cuando enseña lifespan / wiring.

Los paths exactos están en `_team/MODULES.md` columna `references_app_code`.

### 2.4 Ejemplos prohibidos

- ❌ `foo`, `bar`, `baz` — usar siempre dominio real.
- ❌ "una tienda de mascotas" — Petstore es FastAPI tutorial, no este curso.
- ❌ "tu empresa" en abstracto — usa ACME.
- ❌ Fechas relativas tipo `datetime.now()` en ejemplos de prosa — los hace
  irreproducibles.

---

## 3. Convenciones de código en ejemplos

### 3.1 Identificadores

- Inglés siempre: `def compute_total(invoices)`, no `def calcular_total`.
- `snake_case` para funciones, variables, módulos.
- `PascalCase` para clases.
- `SCREAMING_SNAKE_CASE` para constantes.
- Prefijo `_` para privado por convención.

### 3.2 Type hints

- **Obligatorios** en toda firma de función pública (la que aparece en un
  ejemplo del módulo). Excepción: el primer módulo de funciones puede mostrar
  funciones sin hints como contraste, pero **acaba** con la versión tipada.
- Estilo Python 3.12+: `list[int]`, `dict[str, Any]`, `str | None`. **No** uses
  `List`, `Dict`, `Optional` (eso es Python ≤3.8).
- Imports de tipos solo cuando es necesario: `from typing import Annotated,
  Any, TypedDict`. Nada de `from typing import *`.

### 3.3 Estilo

- Comentarios en español ("# calcula el total"), código en inglés.
- Líneas ≤ 88 columnas (Black/Ruff default).
- f-strings siempre que se interpola.
- No usar `print()` salvo en ejemplos del módulo de I/O o cuando es el output
  del ejercicio.
- En código async, los nombres de funciones async terminan en verbo normal
  (`get_user`, no `aget_user`). El que sean async se ve por la firma.

### 3.4 Longitud de ejemplo

- Snippet inline (dentro de prosa): ≤ 8 líneas.
- Ejemplo conducido (sección "ejemplo"): ≤ 25 líneas. Si necesitas más, parte
  en dos snippets con prosa entre medias.
- Código del ejercicio (starter): ≤ 15 líneas; idealmente 3–10.
- Código de solución: misma longitud que starter ± 5 líneas.

### 3.5 Imports

- En ejemplos, todos los imports al principio del bloque. Nada de "import en
  medio de función" salvo cuando el módulo explícitamente enseña lazy imports.
- Orden: stdlib, terceros, locales. Línea en blanco entre grupos.

### 3.6 Catálogo de tools canónicas (reusable por módulos y fichas)

Cuando un ejemplo o ficha F necesita "una tool que…", usa **estas firmas**. No
inventes una versión paralela. Si necesitas una tool nueva, propónla aquí
primero. Todas siguen el shape Anthropic `{name, description, input_schema}`,
también consumible por `@tool` de LangChain.

#### 3.6.1 Acceso a datos estructurados

```yaml
- name: sql_query
  description: Ejecuta una query SQL de solo-lectura sobre el warehouse del tenant.
  input_schema:
    type: object
    properties:
      query:   { type: string, description: "SELECT válido. Sin DDL/DML." }
      tenant:  { type: string, description: "Slug del tenant (multitenant guard)." }
    required: [query, tenant]

- name: fetch_excel
  description: Lee una hoja de Excel del bucket del tenant y devuelve filas como JSON.
  input_schema:
    type: object
    properties:
      path:       { type: string }
      sheet_name: { type: string }
      tenant:     { type: string }
    required: [path, sheet_name, tenant]

- name: fetch_csv
  description: Lee un CSV del bucket del tenant.
  input_schema:
    type: object
    properties:
      path:      { type: string }
      delimiter: { type: string, default: "," }
      tenant:    { type: string }
    required: [path, tenant]
```

#### 3.6.2 Ingesta de documentos

```yaml
- name: parse_invoice_pdf
  description: OCR + extracción estructurada de una factura PDF.
  input_schema:
    type: object
    properties:
      path:   { type: string }
      tenant: { type: string }
    required: [path, tenant]

- name: parse_bank_statement
  description: Parsea extracto bancario en PDF o CSV a transacciones normalizadas.
  input_schema:
    type: object
    properties:
      path:    { type: string }
      account: { type: string }
      tenant:  { type: string }
    required: [path, account, tenant]

- name: parse_contract_pdf
  description: Extrae cláusulas y partes de un contrato en PDF.
  input_schema:
    type: object
    properties:
      path:   { type: string }
      tenant: { type: string }
    required: [path, tenant]
```

#### 3.6.3 Comunicación de salida

```yaml
- name: send_email
  description: Envía email transaccional. La plantilla y destinatarios los decide el harness.
  input_schema:
    type: object
    properties:
      to:        { type: array, items: { type: string } }
      subject:   { type: string }
      body_md:   { type: string }
      tenant:    { type: string }
    required: [to, subject, body_md, tenant]

- name: post_slack_message
  description: Publica un mensaje en el canal Slack del tenant.
  input_schema:
    type: object
    properties:
      channel: { type: string }
      text:    { type: string }
      tenant:  { type: string }
    required: [channel, text, tenant]

- name: write_report
  description: Persiste un reporte como artefacto del tenant, listo para descarga.
  input_schema:
    type: object
    properties:
      kind:    { type: string, enum: [pdf, md, xlsx] }
      title:   { type: string }
      payload: { type: object }
      tenant:  { type: string }
    required: [kind, title, payload, tenant]
```

#### 3.6.4 Integraciones LATAM

```yaml
- name: erp_fetch_transactions
  description: Trae transacciones contables del ERP local (Siigo/Contpaq/Alegra/World Office).
  input_schema:
    type: object
    properties:
      erp:       { type: string, enum: [siigo, contpaq, alegra, world_office, aspel] }
      period:    { type: string, description: "YYYY-MM" }
      account:   { type: string }
      tenant:    { type: string }
    required: [erp, period, tenant]

- name: bank_open_api
  description: Trae transacciones bancarias vía agregador (Belvo, Plaid LatAm).
  input_schema:
    type: object
    properties:
      provider: { type: string, enum: [belvo, plaid] }
      account:  { type: string }
      from:     { type: string, description: "YYYY-MM-DD" }
      to:       { type: string }
      tenant:   { type: string }
    required: [provider, account, from, to, tenant]
```

#### 3.6.5 Reglas duras para tools

- **Todo input lleva `tenant`** salvo que el harness lo inyecte fuera de la
  llamada del modelo. Hacerlo explícito en el schema es defensa en profundidad.
- **Solo lectura por default**. Tools que escriben (e.g., `send_email`,
  `write_report`) marcan `requires_confirmation: true` en el harness; el
  modelo no decide solo.
- **No usar nombres en español** para tools. Siempre inglés snake_case.
- **No crear tools "genéricas"** tipo `run_code` o `do_anything`. Cada tool
  es un verbo concreto con propósito acotado.

---

## 4. Convenciones de prosa

### 4.1 Voz

- **Tú** (no "ustedes", no "usted", no "vosotros"). Una sola persona lee.
- **Indicativo directo**: "FastAPI valida el body con Pydantic." No: "Vamos a
  ver cómo FastAPI valida...".
- Sin frases motivacionales ("¡Genial!", "¡Vamos!", "¡Ahora sí!"). El lector
  sabe lo que está haciendo.
- Sin disculpas ("perdón por la simplificación", "siento que sea técnico").
- Sin meta-comentarios ("en este módulo vamos a aprender..."). El título y el
  hilo conductor ya lo dicen.

### 4.2 Densidad

- Una idea por párrafo. Párrafos de 2–5 líneas.
- Sección 2 ("idea central") ≤ 120 palabras.
- Sección 4 ("cómo funciona por dentro") es la más larga: 250–500 palabras.
- Sección 6 (ejercicios) no se cuenta en prosa.

### 4.3 Callouts (formato Markdown)

Tres tipos, marcados con sintaxis explícita en el `.md`:

```markdown
> [!nota]
> Información útil que no rompe el flujo. Optional reading.

> [!cuidado]
> Algo que el lector va a equivocar si no lo señalamos.

> [!profundizar]
> Link al código real de la app que usa el patrón.
```

El renderer del site mapea estos prefijos a clases CSS. No inventes nuevos
tipos.

### 4.4 Listas

- Listas con bullet cuando el orden no importa.
- Listas numeradas cuando el orden importa (pasos, secuencia).
- Tablas cuando se compara ≥3 cosas en ≥2 dimensiones. No abuses; una tabla
  larga es ilegible.

### 4.5 Código inline

- `` `nombre_variable` `` para identificadores.
- `` `python -m http.server` `` para comandos.
- `**negrita**` para términos clave la primera vez que aparecen en el módulo.
- Cursiva (`*x*`) para énfasis suave, no para términos.

---

## 5. Plantillas reusables (fragmentos Markdown listos para pegar)

### 5.1 Bloque "errores típicos"

```markdown
## Errores típicos

**1. {nombre del error}.**
*Síntoma*: {qué ve el lector}.
*Causa*: {por qué pasa}.
*Arreglo*: {qué cambia}.

**2. {siguiente}.**
...
```

Mínimo 2 errores típicos por módulo. Máximo 5. Si tienes menos de 2, el módulo
no está terminado.

### 5.2 Formato de ejercicio (YAML, va en `exercises.yaml` del módulo)

```yaml
- slug: factura_basica
  kind: code              # code | quiz
  title: Diccionario de factura
  ord: 1
  prompt_md: |
    Crea `factura` como dict con claves `cliente`, `monto`, `pagada`.
    Cliente es `"ACME"`, monto `4820`, `pagada` empieza en `False`. Luego
    márcala como pagada.
  starter_code: |
    factura = {
        # completa
    }

    # marcar como pagada
  test_code: |
    assert isinstance(factura, dict), "factura debe ser dict"
    assert factura["cliente"] == "ACME"
    assert factura["monto"] == 4820
    assert factura["pagada"] is True, "márcala como pagada después de crearla"
    print("ok")
  solution_code: |
    factura = {"cliente": "ACME", "monto": 4820, "pagada": False}
    factura["pagada"] = True
  hints:
    - "Un dict literal en Python es {clave: valor, ...}."
    - "Modificas un valor reasignándolo: dict[clave] = nuevo_valor."
```

### 5.3 Formato de quiz

```yaml
- slug: identidad_vs_igualdad
  kind: quiz
  ord: 1
  question_md: |
    ¿Cuál de estas comparaciones devuelve `True` *siempre*, sin importar la
    versión de Python?
  options:
    - text_md: "`[1, 2] == [1, 2]`"
      is_correct: true
      feedback_md: "Igualdad por valor — `list.__eq__` compara elemento a elemento."
    - text_md: "`[1, 2] is [1, 2]`"
      is_correct: false
      feedback_md: "Identidad: comparan objetos en memoria. Dos literales `[1, 2]` son objetos distintos."
    - text_md: "`1.0 is 1`"
      is_correct: false
      feedback_md: "Distinto tipo, distinto objeto."
```

Mínimo 2 quizzes por módulo, máximo 4. Cada opción incorrecta debe tener un
`feedback_md` que explica **por qué**, no solo "incorrecto".

### 5.4 Bloque "para profundizar"

```markdown
> [!profundizar]
> El patrón de {concepto} lo usa el archivo
> [`app/routers/modules.py`](../../app/routers/modules.py) en la función
> `list_modules`. Ahí ves cómo {qué ver concretamente}.
```

El path siempre relativo desde `content/{track}/{slug}.md`. El texto siempre
**dice qué buscar dentro del archivo**, no solo "léelo".

### 5.5 Bloque "chat sugerido"

```markdown
## Pregúntale al tutor

Tres prompts que puedes pegar en el panel lateral:

1. **Explícame de otra forma**: "Explícame {concepto} con un ejemplo distinto
   al de las facturas."
2. **Aplícalo a BATUTA**: "Cómo aplicaría {concepto} a una auditoría
   multitenant real."
3. **Por qué falló mi intento**: "Mira mi último intento del ejercicio 2 y
   dime por qué no pasa el test."
```

El tutor recibe el contexto del módulo, así que el lector no tiene que
re-pegar nada.

### 5.6 Cabecera de módulo

Todo `.md` de módulo empieza con frontmatter YAML:

```yaml
---
id: A05
slug: modulos-y-paquetes
track: A
ord: 5
title: "Módulos, paquetes, imports"
goal: "Organizar código Python en módulos y paquetes, y entender qué pasa cuando se hace `import`."
prerequisites: [A01, A04]
next_hints: [A06, B01]
estimated_minutes: 60
version: 1
---
```

El loader del site lee esto. Los campos coinciden con `_team/MODULES.md`.

### 5.7 Bloque "determinístico vs agéntico" (módulos y fichas)

Cada módulo Track D, E y toda ficha F lleva una tabla con este shape:

```markdown
## Determinístico vs agéntico

| Tramo                                         | Tipo            | Por qué |
|-----------------------------------------------|-----------------|---------|
| Parseo de extracto bancario PDF→tabla         | determinístico  | Layout estable; biblioteca cubre el caso. |
| Match exacto por monto + fecha + referencia   | determinístico  | Regla cerrada. |
| Match difuso por descripción ("PAGO ACME" ↔ "ACME INC FACT 4820") | agéntico | Variabilidad de redacción; sin regla. |
| Decidir si una diferencia es timing o error   | agéntico        | Requiere contexto del cliente. |
| Generación del email de reporte               | agéntico        | Salida es para humano. |
```

Mínimo 3 filas. Mínimo 1 fila por tipo. Si todo es agéntico, se pierde el
punto del curso; si todo es determinístico, no hay agente.

### 5.8 Cabecera de ficha F

```yaml
---
id: F-FIN-01
slug: conciliacion-bancaria
track: F
dept: FIN
ord: 1
title: "Conciliación bancaria multi-cuenta"
related_modules: [A05, B03, C03, D04, E01, E05]
industries_instanced: [retail, servicios-fin]
tenants_in_examples: [acme, cooppopular]
big_corp_vendors: [BlackLine, Trintech]
latam_tools: [siigo, world_office, belvo]
key_concepts: [matching, tolerancias, fuzzy-match, reglas-duras, agente-de-excepciones]
estimated_minutes: 60
deterministic_share: 0.7   # estimación: 70% del flujo es código tradicional
version: 1
---
```

### 5.9 Bloque "instancia industria" (sección 11 de ficha F)

```markdown
## Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 3–8 cuentas bancarias (multi-país si vende cross-border),
volumen 2k–10k transacciones/mes, descriptores cortos y ruidosos
(`"PAGO MERCH PAGO 4820"`).

**Delta determinístico**: agregación por gateway de pago (MP, Wompi, Conekta)
antes del match.

**Delta agéntico**: identificar contracargos disfrazados de reembolso.

**Regulación**: tributaria local sobre IVA cobrado. Mantener evidencia 5 años.

**Precio orientativo**: 250–700 USD/mes según volumen.

### Instancia 2 — Servicios financieros (`cooppopular`)

**Datos típicos**: 1–3 cuentas, volumen alto en transferencias inter-asociados,
descripción rica (`"TRANSF SOCIO 0214 APORTE MARZO"`).

**Delta determinístico**: clasificación por código de transacción del core
bancario (provee tabla SBA/COSAC).

**Delta agéntico**: detectar layering (varios depósitos pequeños del mismo
asociado en distintos días).

**Regulación**: AML/KYC. SOX-equivalente local. **No** dejar que el agente
borre transacciones marcadas; solo `human_in_the_loop`.

**Precio orientativo**: 600–1500 USD/mes; setup 5–15 k USD.
```

Mínimo 2 instancias por ficha. Cada una debe declarar **al menos un delta**
en alguna de las dimensiones: datos, determinístico, agéntico, regulación,
precio.

### 5.10 Bloque "blueprint del workflow" (sección 7 de ficha F)

```markdown
## Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest] → carga del extracto y del libro contable (determinístico)
  ↓
[match_strict] → match exacto monto + fecha + ref (determinístico)
  ↓
[match_fuzzy] → emparejamiento por descripción (agéntico, tool: sql_query, fetch_excel)
  ↓
[classify_diffs] → clasifica diferencias en timing/error/desconocido (agéntico)
  ↓
[draft_report] → redacta el reporte y findings (agéntico)
  ↓
[human_review?] → interrupt_before si findings sin clasificar > N
  ↓
[write_report] → persiste artefacto (determinístico, tool: write_report)
  ↓
END
```

### Activities Temporal (cuando aplique)

- `ingest_bank_statement(tenant, period)` — IO real, con retry policy.
- `run_recon_agent(tenant, dataset_id)` — corre el grafo LangGraph dentro.
- `persist_report(tenant, period, payload)` — escritura idempotente con
  `idempotency_key = "recon:{tenant}:{period}"`.

### Tools necesarias (referencia §3.6 de SHARED.md)

- `fetch_excel` (libro contable)
- `parse_bank_statement` (extracto)
- `sql_query` (catálogo de cuentas)
- `write_report` (output)
- `bank_open_api` (opcional, si el cliente tiene Belvo/Plaid)
```

---

## 6. Anti-patrones explícitos (no hacer)

1. **Definiciones circulares**. "Una función es un bloque de código que ejecuta
   una función." Si necesitas usar el término dentro de su definición, ya
   tienes un problema; recurre al Glosario.

2. **"Completar el blank" de 1 línea**. Si el ejercicio se resuelve cambiando
   `...` por una palabra, no es un ejercicio: es trivia. Mínimo: 3 cambios en
   sitios distintos del código, o reescribir 5+ líneas.

3. **Ejemplos foo/bar**. Usa el dominio canónico (sección 2). Si necesitas un
   ejemplo *neutro* (raro), usa cosas concretas: "una lista de ciudades", no
   "una lista de foos".

4. **Prosa motivacional**. "¡Excelente, ya casi!". El lector es adulto y
   técnico. Esto le insulta la inteligencia.

5. **Esconder mecanismos**. "FastAPI mágicamente convierte tu función en una
   API." Mal. La forma correcta: "FastAPI ejecuta tu función dentro de un
   contexto async, valida el body con Pydantic antes de llamarla, captura el
   return y lo serializa a JSON. El decorador `@router.post(...)` registra la
   función en el router; el router luego se monta en `app` con
   `app.include_router`. Sin magia."

6. **Saltar la primera vez que aparece un término**. La primera mención de un
   término del Glosario se enlaza al Glosario y se define en una línea.

7. **Ejemplos en otro lenguaje que el módulo**. Un módulo Python solo enseña
   Python. Si necesita SQL, lo dice. Si necesita YAML, lo dice. Pero no hay
   ejemplos "en pseudocódigo".

8. **Cambiar terminología entre módulos**. Si dos módulos hablan del mismo
   concepto, lo nombran igual. Si crees que el término del Glosario es malo,
   propones el cambio aquí; no lo cambias en silencio en tu módulo.

9. **Resumen al final que repite la sección 2**. La sección "salida esperada"
   no es un TL;DR, es **una lista de verbos accionables**: "Al terminar, puedes:
   declarar una clase con `__init__`; añadirle un `@property`; ...". No
   "aprendiste sobre clases".

10. **Asumir que el lector resolverá el ejercicio para entender el concepto**.
    El concepto se entiende leyendo la lección. El ejercicio **comprueba** que
    se entendió. Si el ejercicio es indispensable para entender, falta prosa.

11. **Ficha F sin precio orientativo**. Una ficha sin rango de precio (USD/mes)
    no es vendible y, por tanto, no está completa.

12. **Ficha F sin fallback humano**. Toda ficha declara explícitamente qué
    pasa cuando el modelo dice "no sé". Si no lo declara, está incompleta.

13. **Mezclar pesos y medidas**. Montos siempre en EUR para ACME (auditoría
    canónica) y en USD para fichas F (precios y mercado). No alternar dentro
    del mismo módulo.

---

## 7. Decisiones de tono y registro

El lector es **una persona técnica con criterio**. Construye agentes a diario
en Claude Code y tiene huecos puntuales (Python formal, full-stack moderno,
operación). Tres reglas operativas que se siguen del perfil:

### 7.1 No infantilices

- Cero **frases puente vacías** ("Ahora que entendiste X, veamos Y").
- Cero **disclaimers innecesarios** ("simplificando mucho", "como verás más
  adelante", "es un poco más complejo en producción").
- Cero **encomios** ("¡buena pregunta!", "¡excelente!", "casi lo tenías").
- Cero **emojis** salvo dentro de prompts de chat (cuando se reproduce un
  ejemplo de UI). Nunca en prosa explicativa.

### 7.2 No asumas

- La **primera vez** que aparece un término del Glosario, se define en una
  línea entre paréntesis o se enlaza explícito al Glosario.
- Las **versiones** siempre se anclan: "FastAPI 0.136+", "Pyodide 0.29.4", no
  "FastAPI moderno".
- Las **decisiones** llevan razón. "Usamos SQLite porque…" no "Usamos SQLite".

### 7.3 Densidad por tipo de bloque

| Bloque | Largo objetivo | Tolerancia |
|--------|----------------|------------|
| Hilo conductor | 1 párrafo (60–120 palabras) | ±20% |
| Idea central | 1 párrafo + 1 imagen mental (≤120 palabras) | -, no más |
| Por qué importa | 2 párrafos (≤180 palabras) | ±20% |
| Cómo funciona por dentro | 3–6 párrafos (250–500 palabras) | duro |
| Ejemplo conducido | Código ≤25 líneas + prosa entre snippets | duro |
| Errores típicos | 2–5 bloques con plantilla | mínimo 2 |
| Salida esperada | Lista 3–7 verbos | duro |

### 7.4 Convenciones lingüísticas

- "Tú", nunca "usted" o "ustedes".
- Voz activa, presente indicativo. "FastAPI valida", no "es validado por
  FastAPI" ni "vamos a validar".
- Tecnicismos en inglés cuando son nombres propios (`StateGraph`, `cache_control`).
  El verbo se conjuga en español ("compilas el grafo").
- Comillas tipográficas en prosa: «así». En código: rectas: `"así"`.
- Decimales con coma en prosa ("48 210,50 EUR"). Con punto en código
  (`48210.50`).

### 7.5 Cuándo escribir en imperativo vs declarativo

- **Imperativo** para instrucciones que el lector va a ejecutar
  ("Ejecuta `uv sync`", "Edita `app/main.py`").
- **Declarativo** para descripciones de mecanismo ("El loader lee el
  frontmatter y lo guarda en `modules.body_md`").
- Nunca mezclar en la misma frase.
