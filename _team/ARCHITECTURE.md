# ARCHITECTURE.md — blueprint refinado del Opus arquitecto

> Este documento sustituye al BLUEPRINT.md en cualquier conflicto. Los Sonnets del
> agents team lo leen **antes** de escribir un módulo o una ficha. Si una decisión
> aquí choca con algo en BLUEPRINT.md, manda este archivo.
>
> Última revisión: 2026-05-16. Versión: 1.0.

---

## 1. Tesis pedagógica

El oficio de construir agentes IA para PYMES LATAM no se enseña con tutoriales de
Python ni con cursos de LangGraph. Se enseña construyendo **un servicio real,
multitenant, observable, durable**, y aprovechando ese servicio como espejo: cada
módulo apunta a una línea concreta de código que el lector puede leer, modificar
y romper. La app `bato-learning` se enseña a sí misma. El lector aprende
exactamente la arquitectura que va a vender, no una versión de juguete.

El segundo pilar es el corte determinístico-vs-agéntico. La mayoría de cursos de
agentes IA tratan al LLM como una caja mágica que "decide". En producción, el
LLM solo decide donde no hay regla. Todo lo demás es código aburrido y barato:
parseo, validación, agregación, plantilla. Este curso obliga a separar los dos
tramos en cada caso de uso (Track F), y a justificar por qué un fragmento es
agéntico (porque no hay regla cerrada, porque el costo de equivocarse es
asumible, porque el contexto cambia con el cliente). Esa disciplina es la
diferencia entre vender un demo y vender un servicio.

---

## 2. Decisiones de stack (con razones, no con preferencias)

### 2.1 Backend — FastAPI 0.136 + SQLAlchemy 2.x async + Alembic

- **FastAPI 0.136+** (verificado con WebSearch, 2026-04). Versión que el repo
  ya usa en `api/pyproject.toml`. Pin `>=0.115,<0.140` para tolerar parches sin
  romper minor.
- **Litestar** se descartó: documentación menor, ecosistema más pequeño, no
  aporta nada pedagógico sobre FastAPI excepto un router más limpio.
- **SQLAlchemy 2.x async** sobre `aiosqlite` en desarrollo, sobre `asyncpg` en
  el módulo de multitenancy (C03). El lector ve los dos drivers. Decisión
  honesta: **aiosqlite no es async real** (usa hilo de fondo). El curso lo
  dice, no lo esconde — y lo aprovecha para el primer "honestidad técnica" del
  curso.
- **Alembic** versionado en `migrations/versions/`. No "se autogenera todo"; el
  módulo C02 enseña cuándo el autogenerate adivina mal y qué editar a mano.

### 2.2 Base de datos — SQLite primero, Postgres como destino

- **SQLite** para la app de aprendizaje. Cero servidores, archivo en `data/`,
  backup con la API `.backup` (litestream se menciona, no se exige).
- **Postgres + RLS** se enseña en C03 como el destino de producción. El curso
  no pretende que SQLite escale; pretende que el lector vea el patrón de
  multitenancy en el dialect más simple y luego haga el salto.
- **Decisión revertida del BLUEPRINT**: usar SQLite tanto para contenido como
  para chat. El BLUEPRINT proponía compose extra para Postgres; aquí queda
  fuera de la app local. El módulo de Postgres existe pero corre contra una
  instancia descartable, no contra la app.

### 2.3 Frontend — Jinja2 + HTMX 2.0 + Tailwind CDN + CodeMirror 6 + Pyodide 0.29

- **Jinja2** server-rendered. Cero build pipeline. Inspeccionable con View
  Source. Esto es **pedagogía**: el lector entiende lo que ve.
- **HTMX 2.0.9** (verificado WebSearch). Las extensiones (SSE, ws) están fuera
  del core en 2.x. Para el chat usamos `htmx-ext-sse` cargado por separado.
  Anti-patrón explícito en módulo B03: HTMX no es para SPAs pesadas.
- **Alpine.js** se descartó: HTMX cubre todo lo que necesitamos en este sitio.
  Si una interacción exige estado local profundo (e.g., el editor), va en JS
  vanilla con `module` import.
- **Tailwind por CDN**. Aceptable para una app local. El módulo de despliegue
  (D03) menciona que producción exige build, pero **no** lo exige aquí.
- **CodeMirror 6** sobre Monaco: Monaco trae 4 MB de bundle, Lucio TS, y un
  IntelliSense que no aporta a Pyodide. CodeMirror 6 es modular y tipográfico.
- **Pyodide 0.29.4** (no 0.27 como pone el site actual). Built con Python 3.13,
  Emscripten 4.x. Pin a `0.29.4` explícito en el `<script src>` para reproducibilidad.

### 2.4 Chat — SSE en FastAPI + Anthropic SDK 0.40+ con `cache_control`

- **SSE** sobre WebSocket. El chat es unidireccional servidor→cliente con un
  POST inicial. WebSocket complica el manejo de reconexión sin aportar nada.
- **`sse-starlette`** como utilidad. `EventSourceResponse` directo si se
  prefiere; ambas opciones se documentan.
- **Anthropic SDK 0.40+** soporta `cache_control` con `ttl` explícito (`"5m"` o
  `"1h"`). Importante: **el default de TTL cambió a 5m en marzo 2026** (verificado
  WebSearch). Todo módulo y todo código del curso declara `ttl` explícito; no
  hay caching "por defecto".
- **Modelo**: `claude-sonnet-4-6` para el tutor de la app (cheap), `claude-opus-4-7`
  solo para escenarios donde se justifique en módulo (e.g., diff complejo en E02).
- **Prompt caching** del tutor: system prompt + body del módulo van marcados
  `cache_control: {"type": "ephemeral", "ttl": "1h"}`. El historial dinámico va sin
  cache. Esto cumple el mínimo de tokens (1024 para Sonnet 4.6) en la mayoría de
  módulos largos.

### 2.5 Workflows durables — Temporal Python SDK 1.7+

- **Temporal self-hosted** con `temporalio/auto-setup` en compose para módulos
  D04 y E05. El repo `api/` ya lo tiene; lo reusamos.
- **Reglas duras de determinismo** (E05) son intransigentes: ningún
  `datetime.now`, `random`, IO, LLM call en workflow code. Lo demás va en
  activities. El módulo incluye un ejercicio AST que detecta violaciones.
- **Schedules** para el patrón "audit-monthly-per-tenant" (verificado contra el
  workflow real `api/app/workflows/audit.py`).

### 2.6 Observabilidad — Phoenix self-hosted + logs JSON

- **Phoenix** (Arize) elegido en `DECISIONS.md §4`. Confirmado. Un solo
  container, OpenInference standard, gratis. Postgres y ClickHouse extra de
  Langfuse no se justifican para el alcance del curso.
- **OpenInference** para Anthropic SDK y LangChain (los dos paquetes ya están
  en `api/pyproject.toml`). El módulo D04 los enchufa al tracer.
- **Logfire** se menciona como SaaS alternativo. **Langfuse** se menciona como
  upgrade cuando se necesiten Annotation Queues.

### 2.7 Containerización — Docker + Compose, no Kubernetes

- Default: Hetzner CX22 (€4-5/mes), `docker compose up`, Traefik con TLS
  automático. Verificado: este patrón sigue siendo el right-sized para BATUTA.
- **k3s** queda en `infra/k3s/` como **referencia**, no en el default path.
  Módulo "cuándo migrar a K8s" lo cubre con reglas duras.

### 2.8 Gestión de paquetes — `uv` siempre

- `uv` (Astral) en lugar de pip/poetry/pdm. El repo ya lo usa. Lockfile
  determinista, instalación rápida, sin virtualenv hell. Cualquier ejemplo del
  curso que diga `pip install` está mal.

---

## 3. Modelo de aprendizaje progresivo

El curso son **5 tracks técnicos (A–E) + 1 track de playbook (F)**. Los tracks
técnicos se leen en orden lineal con dependencias mínimas hacia adelante; el
Track F se **referencia** desde los técnicos como aplicación.

### 3.1 Hilo conductor por track

- **Track A (Python pragmático, 7 módulos)**. El lector ya programa. Aquí se
  cubren las cosas que un programador no-Python suele ignorar: mutabilidad,
  módulos como ejecutables, type hints modernas, async honesto, clases mínimas.
  **No** se enseña qué es una variable. Sí se enseña qué es un objeto en CPython.

- **Track B (Web full-stack, 6 módulos)**. Cliente-servidor → FastAPI →
  Jinja+HTMX → 4 capas → editor+Pyodide → SSE+chat. El lector termina capaz de
  leer **cualquier feature de la app** y mapearla a sus archivos.

- **Track C (Datos y persistencia, 3 módulos)**. SQLAlchemy async → Alembic →
  multitenancy. El énfasis es entender por qué el schema vive en código, y por
  qué "olvidar `tenant_id` en una query" es el bug de seguridad #1.

- **Track D (Operación, 4 módulos)**. Docker → Compose → Hetzner+Traefik →
  Observabilidad. Reordenado: **viene antes de profundizar en E**, porque sin
  Docker funcionando localmente el lector no puede probar nada de E2+.

- **Track E (Agentes IA, 5 módulos)**. Anthropic SDK → LangGraph (equivalencia
  1:1) → Skills/AGENTS.md → Memoria/sesiones multitenant → Temporal. Aquí
  aterrizan **todos** los principios de los tracks anteriores.

- **Track F (Playbook por departamento × industria, 30+ fichas)**. No es un
  track lineal. Es un **catálogo** que se referencia desde los técnicos en
  cada "caso de uso real". Tres "rutas guiadas" sugeridas: finanzas,
  operaciones, ventas-CX.

### 3.2 Capstone — `E06 / Capstone`

Capstone único al final: portar un agente de Claude Code a LangGraph + Temporal
multitenant en Hetzner. Atraviesa todos los tracks. Criterios de "listo" duros
(ver MODULES.md).

### 3.3 Pre-requisitos y sucesores

Cada módulo declara `prerequisites: [id, id, ...]` y `next_hints: [id, ...]`.
El loader del site **bloquea** un módulo hasta que sus prerequisites estén
visitados, con un override "leer igual" persistente.

Reglas para los Sonnets:

- Si un módulo X depende de un concepto del Glosario que aún no se introdujo
  en sus prerequisites, **falta una dependencia**. Añádela en MODULES.md y
  notifica al integrador.
- Si dos módulos compiten por introducir el mismo concepto, el que esté **más
  temprano en orden global** lo introduce; el otro lo cita y profundiza si
  procede.

### 3.4 Por qué 26 módulos y no 30

El BLUEPRINT.md propuso ~30 técnicos. Tras revisión:

- Track A se reduce a **7** (no 11). El lector ya programa; module-paquete,
  errores, dataclasses se funden en módulos más densos. No se enseñan los
  módulos 00–01 del site actual (variables) — quien necesita eso no es el
  público objetivo.
- Track C se reduce a **3** (no 4): JSON/YAML se integra en A06 y B02; no es
  un módulo separado.
- Track F **no son módulos** secuenciales; son fichas referenciables. Por eso
  no entran en el conteo de "módulos".

Total: **26 módulos técnicos** + **39 fichas F base** + **~15 instancias-industria
explícitas** (las demás quedan como variaciones documentadas en cada ficha).

---

## 4. Forma canónica de módulo técnico

Trece secciones (refinamiento de BLUEPRINT §6) con **criterios de aceptación
medibles**. Si un módulo no pasa los criterios, no se publica.

### Secciones

| # | Nombre | Contenido | Criterio de aceptación |
|---|--------|-----------|------------------------|
| 1 | Hilo conductor | 1 párrafo: "viniendo de X, ahora Y, hacia Z" | Cita 1 módulo previo y 1 siguiente por slug. |
| 2 | Idea central | Definición precisa + imagen mental | ≤ 120 palabras. Usa el Glosario. |
| 3 | Por qué importa | Qué se rompe sin esto | Cita al menos 1 ficha F por id. |
| 4 | Cómo funciona por dentro | Mecanismos, sin magia | 250–500 palabras. ≥ 1 diagrama o tabla. |
| 5 | Ejemplo conducido | Código corto, paso a paso | ≤ 25 líneas. Ejecutable. |
| 6 | Ejercicios | 2–4 ejercicios | ≥ 1 no-trivial (ver §6 de este doc). Tests automáticos. |
| 7 | Quiz de comprensión | 2–4 preguntas | Cada distractor tiene `feedback_md` explicando por qué. |
| 8 | Caso de uso real | Apuntar a 1–2 fichas F | Link funcional. Resumen de 2 líneas. |
| 9 | Determinístico vs agéntico | Aplicado al tema del módulo | Tabla de 2 columnas, mínimo 3 filas. |
| 10 | Errores típicos | 2–5 errores con síntoma/causa/arreglo | Formato plantilla SHARED §5.1. |
| 11 | Para profundizar | Link a archivo real de la app | Path absoluto del repo. Dice **qué buscar dentro**. |
| 12 | Chat sugerido | 3 prompts pre-armados | Plantilla SHARED §5.5. Personalizados al módulo. |
| 13 | Salida esperada | Verbos accionables | Lista de 3–7 ítems. Cada uno empieza con verbo en infinitivo. |

### Criterios duros adicionales

- Frontmatter YAML completo (SHARED §5.6).
- Cabe en `estimated_minutes` declarado (15/30/60/90). Si excede, parte el módulo.
- Cero ejemplos `foo`/`bar`. Solo dominio canónico (SHARED §2).
- Cero meta-prosa ("en este módulo vamos a...").

---

## 5. Forma canónica de ficha de caso de uso (Track F)

Doce secciones, refinamiento de BLUEPRINT §6.1.

| # | Nombre | Contenido | Criterio de aceptación |
|---|--------|-----------|------------------------|
| 1 | Problema operativo | En lenguaje del cliente, no técnico | 1 párrafo. Cita ejecutivo arquetípico ("el CFO de ACME quiere..."). |
| 2 | Hoy en big corps | Stack/equipo/inversión | Nombra ≥ 2 vendors reales con costo orientativo. |
| 3 | PYME LATAM realista | Datos en Excel/ERP local, sin data engineer | Nombra ≥ 1 ERP LATAM (Siigo, Contpaq, Alegra, World Office). |
| 4 | Datos típicos | Formato, fuente, frecuencia, volumen | Tabla. Con ejemplo de fila si aplica. |
| 5 | Tramos determinísticos | ETL, validaciones, agregaciones, plantilla | Lista numerada. ≥ 3 ítems. |
| 6 | Tramos agénticos | Decisiones que exigen contexto | Lista numerada. ≥ 2 ítems. Cada uno justifica **por qué no es regla**. |
| 7 | Blueprint del workflow | LangGraph + Temporal cuando aplique | Diagrama ASCII de nodos. Lista de tools necesarias con schema breve. |
| 8 | Salida y entrega | Reporte/alerta/dashboard/mail | Mockup de output (texto o tabla). Canal de entrega. |
| 9 | Cómo se vende | Gancho, propuesta de valor, precio | Precio orientativo en USD/mes para PYME LATAM. Tier. |
| 10 | Riesgos | Alucinación, costos, PII, regulación | ≥ 3 riesgos con mitigación. |
| 11 | Variantes por industria | 2 instancias con deltas | Tabla comparativa. Deltas en datos, regulación, precio. |
| 12 | Módulos técnicos relacionados | Links a A/B/C/D/E | ≥ 3 módulos por id. Dice **qué del módulo aplica**. |

### Criterios duros

- Toda ficha referencia al menos 1 módulo de Track D (operación) y 1 de Track E
  (agente). Si no, no es desplegable.
- Toda ficha incluye al menos un caso donde "el LLM dice no sé" y se cae a
  excepción humana. Mostrar el camino fall-back es no-negociable.
- Precio orientativo siempre con rango (e.g., 200–600 USD/mes setup + 50–200/mes
  uso). Nunca un número único.

---

## 6. Tipos de ejercicios

Clasificación canónica. Cada módulo usa al menos **dos tipos distintos**.

| Tipo | Qué pide | Cuándo usarlo | Ejemplo |
|------|----------|---------------|---------|
| **code-fix** | Arregla código roto | Para enseñar errores comunes | Código con `default arg = []`, hay que detectar y corregir. |
| **code-from-scratch** | Escribe N líneas desde cero | Para introducir un patrón nuevo | Escribir una función `compute_total(invoices: list[Invoice]) -> Decimal`. |
| **debug** | Encuentra el bug | Para enseñar lectura crítica de código | Función pasa 4 tests y falla 1; el bug es de aliasing en `dict.copy()`. |
| **refactor** | Reorganiza | Para enseñar capas, composición sobre herencia | Router monolítico de 60 líneas → 4 archivos en B04. |
| **design** | Dibuja un workflow | Para enseñar arquitectura | "Dado este caso F-FIN-01, propón nodos LangGraph y activities Temporal." |
| **integration** | Atraviesa varios módulos | Para sintetizar | Capstone E06; también ejercicios "puente" cada 5 módulos. |
| **case-study** | Lee ficha F y diseña | Para conectar técnico con negocio | "Lee F-OPS-02. Identifica qué tramos son agénticos y por qué." |
| **trace-reading** | Lee una traza Phoenix | Para D04 y E04 | "Identifica el span de latencia más alta y propón una mitigación." |
| **ast-detection** | Detecta antipatrón con AST | E05 (determinismo Temporal) | Detector que falla si encuentra `datetime.now()` en workflow code. |

### Anti-ejercicios prohibidos

- "Rellena el blank" de una palabra.
- "Ejecuta este código y mira el output" sin pregunta.
- "¿Qué imprime?" sin que el lector tenga que razonar el path completo.

---

## 7. Sistema de evaluación

Tres capas, todas guardadas en DB (ver `BLUEPRINT §4`).

### 7.1 Quiz

- 2–4 por módulo. Multi-opción única correcta. `quiz_answers` guarda intentos.
- Cada distractor con feedback. **Feedback explicativo, no "Mal, prueba otra"**.

### 7.2 Ejercicios con tests automáticos

- 2–4 por módulo. Tests corren en Pyodide (Tracks A, parte de B) o en backend
  (módulos que requieren librerías no disponibles en Pyodide, e.g. SQLAlchemy
  async). El loader decide el runner según el `kind` del ejercicio.
- Cada intento se guarda en `exercise_attempts`. Métrica: tiempo al primer
  pass, número de intentos.

### 7.3 "Explícale al tutor"

- Al final de cada módulo, el chat tutor pide al lector que **explique el
  concepto con sus palabras** en 3-4 frases. El tutor evalúa con una rúbrica
  simple (cubre los key_concepts, ≤ 5 frases, sin copiar la lección).
- Esto no es un test "automatable" duro; es una conversación. Se guarda en
  `chat_messages` con tag `concept_check`.

### 7.4 Proyecto al final de cada track

- Track A: refactor de un script monolítico a paquete con tests.
- Track B: añadir una pantalla nueva a la app (router + service + repo +
  template + ejercicio Pyodide).
- Track C: añadir una migración Alembic + actualizar 2 repos para soportar
  un nuevo campo en `module_visits`.
- Track D: desplegar la app a Hetzner (o a localhost con Traefik) y configurar
  Phoenix.
- Track E: portar un skill propio a un nodo LangGraph **dentro** de la app
  (preview del Capstone).

### 7.5 Capstone E06

Criterios duros (ver MODULES.md E06). No es "ya estudié todo": es un entregable
ejecutable.

---

## 8. El chat tutor — rol pedagógico

### 8.1 Qué SÍ hace

- **Guía con preguntas**. Si el lector pregunta "cómo resuelvo este ejercicio",
  el tutor responde con otra pregunta que aísle el bloqueo (e.g., "qué error te
  da" / "qué crees que hace esta línea").
- **Pide código antes de opinar**. Si no tiene el código del editor en el
  contexto, lo pide explícito.
- **Conecta con módulos previos**. Si el lector confunde un concepto cubierto
  antes, el tutor cita el módulo por slug ("ver A05 §3").
- **Sugiere casos F**. Cuando el lector pregunta "para qué sirve esto en mi
  trabajo", apunta a fichas relevantes con id (e.g., "F-FIN-01 usa este
  patrón").
- **Reconoce limitaciones**. Si la pregunta excede el alcance del curso
  (e.g., "cómo configuro Kubernetes en GCP"), lo dice y orienta hacia material
  externo.

### 8.2 Qué NO hace

- **No resuelve ejercicios**. Aunque el lector lo pida tres veces. Da pistas.
- **No reescribe código del lector sin explicar el porqué**.
- **No inventa APIs**. Si no sabe una API exacta del SDK, pide consultar la
  doc oficial (y reconoce que no la tiene cargada).
- **No habla con tono motivacional**. Una sola persona técnica adulta del otro
  lado.
- **No genera mucho output sin estructura**. Responde corto por default;
  expande si el lector pide.

### 8.3 System prompt canónico (plantilla)

```text
Eres el tutor de bato-learning. Un solo lector técnico al otro lado.

Reglas:
- Respondes en español, ≤ 6 frases por defecto. Expandes si te lo piden.
- Antes de explicar, comprueba qué intentó el lector y dónde se atascó.
- Si el lector pide la solución de un ejercicio, **no la das**; sí das una
  pista que aísle el bloqueo concreto.
- Si el lector cita un concepto que se cubrió en un módulo previo, lo
  referencias por slug entre paréntesis: "(ver A05)".
- Si la pregunta toca un caso de negocio, sugieres una ficha F por id (formato
  F-DEPT-NN).
- Cuando no sabes una API, lo dices. No la inventas.
- Sin emojis, sin "¡vamos!", sin "excelente pregunta".

Contexto del módulo actual (cacheable, no se repite):
{module_body_md}

Ejercicios del módulo actual (cacheable):
{exercises_summary}

Intentos recientes del lector (dinámico, no cacheable):
{recent_attempts}

Código actual en el editor (dinámico):
{editor_code}
```

### 8.4 Inyección de contexto y caching

- Bloque `system` se parte en dos: estático (las reglas + body del módulo)
  marcado `cache_control: {"type": "ephemeral", "ttl": "1h"}`; dinámico (intentos,
  editor) sin cache.
- Mensajes de usuario y assistant no se cachean (historial dinámico).
- Si el módulo es < 1024 tokens, **no se cachea**. El SDK rechazaría el cache.
  Para esos módulos, se concatena con un footer de "convenciones del curso" del
  Glosario hasta llegar al mínimo. Documentado.

### 8.5 Reglas de costo

- **Hard limit por sesión-módulo**: 200K tokens entrada + 30K salida. Por
  encima, el tutor responde "esta conversación está pesada, recomiendo
  resumir y abrir una nueva sesión".
- **Cost ledger**: cada mensaje guarda `tokens_in`, `tokens_out`, `cost_usd`
  calculado en backend. Visible en `/progreso`.
- **Latencia visible**: el front muestra "Sonnet 4.6 · 3.2s · $0.018" en cada
  turno. Transparencia operativa, no esconde costo al lector.

---

## 9. La app como ejemplo vivo — matriz módulo → archivos

Cada módulo técnico cita archivos concretos del repo. La matriz es contrato:
si el archivo aún no existe (la app está en construcción), el Sonnet lo
**registra como dependencia** del scaffold y deja el path tentativo.

| Módulo | Archivos clave |
|--------|----------------|
| A01 | `pyproject.toml`, `app/main.py` |
| A02 | (ninguno, fundacional) |
| A03 | `app/services/progress.py` (una comprensión real) |
| A04 | `app/services/exercise_runner.py` |
| A05 | `app/__init__.py`, `app/routers/__init__.py`, `app/main.py` |
| A06 | `app/models/exercise.py`, `app/services/protocols.py` |
| A07 | `app/integrations/anthropic_chat.py` |
| B01 | `app/main.py` (curl real contra la app) |
| B02 | `app/routers/modules.py`, `app/deps.py` |
| B03 | `app/templates/module.html`, `app/templates/_exercise.html` |
| B04 | las 4 capas reales de `app/` |
| B05 | `app/static/js/runner.js`, `app/services/exercise_seed.py` |
| B06 | `app/routers/chat.py`, `app/integrations/anthropic_chat.py`, `app/static/js/chat.js` |
| C01 | `app/db.py`, `app/models/module.py`, `app/repos/progress.py` |
| C02 | `migrations/env.py`, `migrations/versions/*` |
| C03 | `app/repos/_base.py` (helper de filtro `tenant_id`) |
| D01 | `Dockerfile`, `.dockerignore` |
| D02 | `compose.yaml`, `compose.prod.yaml` |
| D03 | `infra/traefik/traefik.yml`, `infra/scripts/backup.sh` |
| D04 | `app/telemetry.py`, `app/middleware/cost.py` |
| E01 | `api/app/routers/anthropic_demo.py` (referencia ya existente) |
| E02 | `api/app/routers/langgraph_demo.py` |
| E03 | `app/integrations/skills/monthly_audit/SKILL.md` |
| E04 | `app/repos/chat.py`, `app/services/chat.py` |
| E05 | `api/app/workflows/audit.py`, `api/app/activities/agent.py` |
| E06 | todo lo anterior |

> Nota al scaffold: **fase A del plan de implementación** (BLUEPRINT §9) tiene
> que producir al menos los esqueletos vacíos con docstrings antes de soltar al
> Sonnet team. Sin eso, los módulos no pueden referenciar nada.

---

## 10. Determinístico vs agéntico — principio transversal

### 10.1 Cómo se enseña

- **Primera mención**: módulo A05 (cuando se introduce la arquitectura de la
  app), como decisión de diseño general.
- **Aplicación práctica**: cada módulo de Track D y E lo aplica al tema del
  módulo (e.g., en D01: "el Dockerfile es 100% determinístico; el agente que
  corre adentro, no").
- **Aplicación en negocio**: cada ficha F lo separa explícitamente en sus
  secciones 5 y 6.

### 10.2 Reglas para clasificar

Una operación es **determinística** si:

1. Tiene regla cerrada (e.g., "si monto = monto y fecha = fecha, match").
2. El costo de falso positivo y falso negativo es asimétrico y duro (e.g.,
   regulatorio).
3. Es barata de auditar (un humano puede revisar 1000 casos en 1 hora).

Una operación es **agéntica** si:

1. Requiere contexto que no cabe en regla (descripción ambigua, redacción
   variable, criterio que cambia con el cliente).
2. El costo de equivocarse es absorbible (se reintenta, hay validación humana
   downstream).
3. La salida es para humano (resumen, recomendación), no para sistema crítico.

### 10.3 Anti-patrones de clasificación

- "Lo agéntico porque es más cool". No. Si hay regla, va a código.
- "Lo determinístico porque el LLM cuesta". No. Si no hay regla cerrada, la
  alternativa no es determinística — es un humano caro.
- "Mezclar en un solo nodo LangGraph". El curso enseña a separar nodos
  determinísticos (Python puro) de nodos agénticos (model + tools).

---

## 11. Coordinación del agents team

### 11.1 Roles

- **Opus arquitecto** (yo). Mantiene este archivo y SHARED.md. Aprueba cambios
  estructurales (renombrar id, mover módulo entre tracks, añadir ficha F).
- **Sonnet de módulo técnico**. Escribe un módulo Track A–E. Lee
  ARCHITECTURE.md + SHARED.md + entrada propia en MODULES.md antes de empezar.
- **Sonnet de ficha F**. Escribe una ficha de caso de uso. Mismo ritual.
- **Sonnet integrador**. Pasa al final. Revisa coherencia global, glosario,
  hilo conductor, links rotos, duplicados. Escribe E06 (Capstone). Tiene
  permiso para **proponer** cambios pequeños al ARCHITECTURE.md (con PR
  separado al Opus).

### 11.2 Protocolo de lectura al empezar una tarea

Todo Sonnet, en cualquier rol, al recibir una tarea:

1. Lee `_team/ARCHITECTURE.md` entero. Sí, entero. Si excede contexto, lee al
   menos §1, §3 (track del módulo), §4 o §5 (forma canónica), §11 (este).
2. Lee `_team/SHARED.md` entero. Tiene la verdad del Glosario y los ejemplos.
3. Lee la entrada del módulo o ficha que le toca en `_team/MODULES.md`.
4. Si su entrada lista `prerequisites: [X, Y]`, lee los `.md` ya escritos de X
   e Y (en `app/content/{track}/{slug}.md`). Si no están escritos aún, **se
   bloquea y lo reporta**.
5. Lee el archivo de la matriz §9 que le toca referenciar. Si no existe el
   archivo, lo marca en `notes_for_subagent` y lo deja con path tentativo.

### 11.3 Protocolo de escritura al terminar

1. Produce el `.md` del módulo o ficha en `app/content/{track}/{slug}.md`
   (módulos) o `app/content/F/{dept}/{slug}.md` (fichas F).
2. Produce el YAML de ejercicios y quizzes en `app/content/{track}/{slug}.exercises.yaml`
   y `.quizzes.yaml` (módulos técnicos solo).
3. **Escribe una entrada** en `_team/MODULES_STATUS.md` con la forma:

   ```yaml
   - id: A05
     status: done
     assumed_from_prereqs: [A01: "uv corriendo; pyproject leído",
                            A04: "type hints conocidos"]
     prepared_for_successors:
       A06: "el lector ya entiende capas; el ejemplo de Vendor encaja directo"
       B01: "estructura src/ asumida"
     deviations_from_spec: |
       Cambio menor: añadí un ejercicio de detección de import circular que no
       estaba en el plan. Justifico: es el error #1 cuando se aprende esto.
     glossary_terms_introduced: [src layout, import absoluto]
     glossary_terms_added: []
     open_questions: []
   ```

4. Si introdujo un término nuevo, lo añadió a `SHARED.md §1` **antes** de
   usarlo. Si dudó, lo deja en `open_questions` y el integrador resuelve.

### 11.4 Cómo se evita inconsistencia

- **Una sola fuente de verdad para terminología**: SHARED §1 (Glosario).
- **Una sola fuente de verdad para ids**: MODULES.md. Renombrar un id requiere
  Opus.
- **Una sola fuente de verdad para personajes**: SHARED §2. ACME es
  manufactura, Globex es logística, no se intercambian.
- **Sonnet integrador final** corre 4 checks automáticos:
  1. Cada `prerequisites: [X]` apunta a un id que existe.
  2. Cada `references_app_code` apunta a un path que existe en el repo.
  3. Cada ficha F citada por un módulo existe y viceversa.
  4. Cada término del Glosario aparece en al menos 1 módulo (si no, se borra
     del glosario o se sospecha un hueco).

### 11.5 Versionado y cambios después del primer release

- Cada módulo `.md` empieza con `version: 1` en frontmatter. Cambios sin
  romper estructura → bump patch (`1.1`). Cambios que rompen ids o flujo →
  bump major (`2`), y requieren actualizar el campo `migrations:` del módulo
  (cómo migrar progreso del lector de la versión anterior).
- `MODULES.md` tiene una sección "changelog" al final que el integrador
  mantiene.

### 11.6 Paralelización

- Lotes de **4–5 módulos en paralelo** funcionan bien cuando los módulos del
  lote no se referencian entre sí.
- Lotes recomendados (compatibles, sin dependencias mutuas):
  - Lote 1: A01, A02, A03, A04 — fundacionales, sin cruces.
  - Lote 2: A05, A06, A07 — dependen de Lote 1, pero no entre sí (orden flex).
  - Lote 3: B01, B02, B03, C01 — frontend + DB; comparten dependencias hacia
    arriba pero no entre sí.
  - Lote 4: B04, B05, B06, C02, C03 — capa de arquitectura.
  - Lote 5: D01, D02, D03, D04 — operación.
  - Lote 6: E01, E02, E03, E04, E05 — agentes.
  - Lote 7: fichas Track F en lotes de 10, por departamento.
- E06 (Capstone) es individual e integrador. Va al final.

---

## Apéndice — Conflictos resueltos contra BLUEPRINT.md

| Tema | BLUEPRINT | ARCHITECTURE | Razón |
|------|-----------|--------------|-------|
| Conteo de módulos | ~30 técnicos | 26 técnicos + 39 fichas F | Funden A01/A02 del site; JSON/YAML deja de ser módulo solo; F deja de contar como track lineal. |
| Postgres en compose | Sí, opcional | No para la app local | Costo cognitivo. Postgres se enseña, no se exige. |
| Pyodide 0.27 | Implícito | Pyodide 0.29.4 | Verificación de versión 2026-05. |
| Anthropic SDK 0.x | "actual" | `>=0.40` con `ttl` explícito | Default de TTL cambió a 5m en 03/2026. |
| Chat con WebSocket o SSE | Ambos mencionados | SSE solo | Unidireccional. |
| Track F | "30 base + 60 instancias = 90" | 39 fichas, instancias dentro de la ficha | 90 piezas separadas es overhead de coordinación. |
| 13 secciones por módulo | 13 puntos | 13 secciones con criterios duros | El BLUEPRINT solo lista; aquí cada sección tiene "qué pasa" para aprobar. |
| Capstone "tipo lista" | Sí | E06 con criterios duros de "listo" | Lista no es entregable. |

Fin de ARCHITECTURE.md.
