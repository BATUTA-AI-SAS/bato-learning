# MODULES.md — lista canónica de módulos

> Este es el plan maestro. Cada Sonnet de módulo lo lee para saber:
> - qué módulo le toca,
> - qué se asume ya cubierto,
> - qué prepara para el siguiente,
> - qué archivo de la app referenciar en "Para profundizar".
>
> Cualquier reorganización (renombrar, mover, partir un módulo) requiere
> regenerar también `_team/ARCHITECTURE.md` §3 (modelo progresivo).

---

## Decisión sobre cuántos módulos

El BLUEPRINT.md propuso ~30. El CURRICULUM.md previo tenía 13. El site actual
tiene 19. Los números que **funcionan** para el objetivo "diseño → despliegue de
agente multitenant + catálogo vendible" son:

- **Track A — Python pragmático**: 7 módulos (no 11). Se eliminan/funden los
  que ya domina alguien que construye agentes en Claude Code.
- **Track B — Web full-stack**: 6 módulos.
- **Track C — Datos y persistencia**: 3 módulos.
- **Track D — Operación**: 4 módulos.
- **Track E — Agentes IA**: 5 módulos + 1 Capstone (E06).
- **Track F — Playbook**: **39 fichas base** distribuidas en 10 departamentos
  (mínimo 3 por dept., algunos llegan a 4). Cada ficha instancia ≥ 2 industrias.

Total: **26 módulos técnicos** (Tracks A–E con Capstone) + **39 fichas Track F**.

Justificación en `_team/ARCHITECTURE.md` §3. Los `id` siguen los patrones:
- Módulos técnicos: `{track}{ord:02}` → `A01..E06`.
- Fichas F: `F-{DEPT}-{ord:02}` → `F-FIN-01..F-PRD-03`.

---

## Convenciones de esta tabla

- `id`: identificador estable. **No se renombra** una vez asignado.
- `slug`: kebab-case, en inglés. Se usa en URLs (`/m/{slug}`) y en paths
  (`app/content/{track}/{slug}.md`).
- `ord`: orden global de aparición. No reinicia por track.
- `prerequisites`: lista de `id` que **deben** estar leídos. El loader del site
  bloquea el módulo si no se han visitado todos (con un override "leer igual").
- `next_hints`: lista de `id` que continúan naturalmente. El módulo cierra
  apuntando a estos.
- `goal`: una sola oración, verbo accionable en infinitivo o imperativo. No
  "entender", no "conocer". Sí: "implementar", "depurar", "decidir cuándo
  usar".
- `key_concepts`: 3–7 términos del Glosario (SHARED §1). Si introduces un
  concepto no listado, lo añades primero a SHARED.
- `recurring_examples_used`: qué subset de SHARED §2 emplea.
- `references_app_code`: archivos concretos. Si el archivo aún no existe (la
  app está en construcción), se nombra con su path futuro y el módulo se
  marca con `notes_for_subagent: "depende de scaffold {fase}"`.
- `estimated_minutes`: 15 / 30 / 60 / 90. No otros valores.

---

## Track A — Python pragmático

Pre-condición global del track: el lector ya programa, ya usa Python en algún
nivel. **No** se enseña qué es una variable; se enseña qué es una variable
**en Python concretamente** (objetos, referencias, mutabilidad).

### A01 — Modelo mental del intérprete y `uv`

- **id**: `A01`
- **slug**: `interpreter-and-uv`
- **track**: A
- **ord**: 1
- **title**: "Cómo Python ejecuta tu archivo, y por qué usamos `uv`"
- **prerequisites**: []
- **next_hints**: [A02, B01]
- **goal**: "Explicar paso a paso qué pasa entre `uv run python foo.py` y la
  primera línea ejecutada; crear un proyecto nuevo con `uv init`."
- **key_concepts**: intérprete, bytecode, `__pycache__`, uv, lockfile,
  pyproject.toml
- **recurring_examples_used**: ACME (un script `audit.py` mínimo)
- **references_app_code**: `pyproject.toml`, `app/main.py`
- **estimated_minutes**: 30
- **notes_for_subagent**:
  - Énfasis: el lector probablemente nunca leyó `pyproject.toml` con
    atención. Despiezarlo es el ejercicio central.
  - Error típico a destacar: confundir `python -m foo` con `python foo.py`
    (uno trata `foo` como módulo, otro como path).
  - **No** enseñes `pip install`. Si aparece es para criticarlo.

### A02 — Tipos, mutabilidad e identidad

- **id**: `A02`
- **slug**: `types-mutability-identity`
- **track**: A
- **ord**: 2
- **title**: "Tipos, mutabilidad e identidad de objetos"
- **prerequisites**: [A01]
- **next_hints**: [A03]
- **goal**: "Predecir el comportamiento de aliasing en `list`/`dict`; usar
  `is` vs `==` correctamente."
- **key_concepts**: int, float, str, bool, None, list, dict, tuple, set,
  inmutable, mutable, identidad, igualdad
- **recurring_examples_used**: ACME (lista de facturas, dict de cliente)
- **references_app_code**: ninguno (módulo fundacional)
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Funde los módulos 01–02 del site actual.
  - Demuestra aliasing con un ejemplo donde `clientes2 = clientes;
    clientes2.append(...)` modifica los dos. Esto el lector lo va a sufrir
    luego en código de servicios.
  - Errores típicos: mutar default args (`def f(xs=[])`), comparar floats
    con `==`.

### A03 — Control de flujo y comprensiones

- **id**: `A03`
- **slug**: `flow-and-comprehensions`
- **track**: A
- **ord**: 3
- **title**: "if, for, while y comprensiones"
- **prerequisites**: [A02]
- **next_hints**: [A04]
- **goal**: "Escribir comprensiones de lista/dict/set con filtro y
  transformación, y decidir cuándo usar bucle explícito."
- **key_concepts**: if/elif/else, for, while, break/continue, list
  comprehension, dict comprehension, generator expression
- **recurring_examples_used**: ACME (filtrar facturas pagadas, sumar por
  mes)
- **references_app_code**: una comprensión real en `app/services/progress.py`
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Anti-patrón a marcar: comprensiones de 4 líneas con condicional anidado.
    Si tienes que pensar más de 2 segundos para leerla, usa un bucle.

### A04 — Funciones, type hints y errores

- **id**: `A04`
- **slug**: `functions-types-errors`
- **track**: A
- **ord**: 4
- **title**: "Funciones tipadas y manejo de errores"
- **prerequisites**: [A03]
- **next_hints**: [A05, B02]
- **goal**: "Diseñar la firma tipada de una función pura; lanzar y capturar
  excepciones específicas en lugar de `except Exception`."
- **key_concepts**: def, parámetros posicionales/keyword, `*args`/`**kwargs`,
  type hints (3.12+), `raise`, `try/except/else/finally`, jerarquía de
  excepciones, excepciones propias
- **recurring_examples_used**: ACME (validar factura, lanzar
  `InvoiceMissingVendorError`)
- **references_app_code**: `app/services/exercise_runner.py` (manejo de
  errores del usuario)
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Funde los módulos 03 y 07 del site actual.
  - Énfasis en diseñar errores como parte del API público de la función. No
    `except: pass`.

### A05 — Módulos, paquetes e imports

- **id**: `A05`
- **slug**: `modules-packages-imports`
- **track**: A
- **ord**: 5
- **title**: "Módulos, paquetes, imports y cómo se conecta el código"
- **prerequisites**: [A04]
- **next_hints**: [A06, B01, B04]
- **goal**: "Estructurar un paquete Python con `__init__.py`, importar entre
  capas sin ciclos, y entender qué hace `python -m`."
- **key_concepts**: módulo, paquete, `__init__.py`, import absoluto vs
  relativo, `sys.path`, `python -m`, src/ layout
- **recurring_examples_used**: el árbol `app/` real
- **references_app_code**: `app/__init__.py`, `app/routers/__init__.py`,
  `app/main.py` (cómo `include_router` cierra el círculo)
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Este es **el** módulo bisagra de todo el curso. Si el lector no entiende
    imports, no va a entender capas.
  - Error típico: import circular (`router` importa `service`, `service`
    importa `router`). Muéstralo y rómpelo con dependency injection.

### A06 — Clases, dataclasses y protocolos

- **id**: `A06`
- **slug**: `classes-dataclasses-protocols`
- **track**: A
- **ord**: 6
- **title**: "Clases, dataclasses y diseño por protocolos"
- **prerequisites**: [A05]
- **next_hints**: [A07, C01]
- **goal**: "Decidir cuándo usar `@dataclass` vs Pydantic `BaseModel` vs una
  clase normal, y definir un `Protocol` para inyección de dependencias."
- **key_concepts**: clase, `__init__`, `self`, métodos, `@property`,
  `@dataclass`, `typing.Protocol`, herencia (uso mínimo), composición
- **recurring_examples_used**: ACME (modelar `Invoice`, `Vendor` como
  dataclass)
- **references_app_code**: `app/models/exercise.py`,
  `app/services/protocols.py` (si se introducen)
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Funde los módulos 05 y 06 del site actual.
  - **Empuja** composición sobre herencia. Solo se enseña una jerarquía con
    herencia: la de excepciones (vista en A04).
  - Pydantic se nombra pero **no se profundiza aquí** — eso es B02.

### A07 — Async/await y el event loop

- **id**: `A07`
- **slug**: `async-await-eventloop`
- **track**: A
- **ord**: 7
- **title**: "async/await, el event loop, y cuándo no usarlo"
- **prerequisites**: [A06]
- **next_hints**: [B01, B02, E02]
- **goal**: "Identificar funciones I/O-bound vs CPU-bound; escribir una
  función `async` que use `asyncio.gather` para paralelizar llamadas."
- **key_concepts**: coroutina, `async def`, `await`, event loop,
  `asyncio.gather`, blocking call, `run_in_threadpool`
- **recurring_examples_used**: ACME (fetch en paralelo facturas de 3
  fuentes mock)
- **references_app_code**: `app/integrations/anthropic_chat.py` (uso real
  de `AsyncAnthropic`)
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Errores típicos:
    - Llamar `requests.get` (sync) dentro de `async def`. Bloquea el loop.
    - Olvidar `await`. La coroutina queda colgada sin ejecutarse y
      Python lanza un warning.
  - Aclarar que **SQLite + aiosqlite no es async real**: usa un hilo por
    conexión. Lo explicamos honesto, no como "magia". Esto prepara C01.

---

## Track B — Web full-stack

### B01 — Cliente-servidor, HTTP, qué hace un navegador

- **id**: `B01`
- **slug**: `http-and-the-browser`
- **track**: B
- **ord**: 8
- **title**: "Qué pasa entre Enter en el navegador y el primer byte"
- **prerequisites**: [A01]
- **next_hints**: [B02]
- **goal**: "Leer y producir requests HTTP a mano con `curl` y `httpie`;
  explicar status codes, headers relevantes, cookies y sesiones."
- **key_concepts**: HTTP request/response, métodos (GET/POST/PUT/PATCH/
  DELETE), status codes, headers (Content-Type, Authorization, Cookie),
  CORS (mención), TLS (mención)
- **recurring_examples_used**: la propia app (`curl http://localhost:8080/`
  contra ella)
- **references_app_code**: `app/main.py`
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Este módulo **se ejecuta contra la app que estamos construyendo**. El
    lector hace `curl` real a su instancia local.
  - No te metas en HTTP/2 o WebSockets aquí; mencionas SSE como teaser de
    D04.

### B02 — FastAPI a profundidad

- **id**: `B02`
- **slug**: `fastapi-deep`
- **track**: B
- **ord**: 9
- **title**: "FastAPI: routing, Pydantic, dependency injection"
- **prerequisites**: [A04, A06, A07, B01]
- **next_hints**: [B03, C01]
- **goal**: "Escribir un router con validación Pydantic v2 y una dependency
  inyectada; explicar el ciclo de un request en FastAPI."
- **key_concepts**: router, path operation, Pydantic v2 BaseModel, validación,
  `Depends`, dependency override (para tests), `Response`,
  `StreamingResponse`, lifespan
- **recurring_examples_used**: `app/routers/modules.py` real
- **references_app_code**: `app/routers/modules.py`, `app/main.py`,
  `app/deps.py`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - Pydantic v2 es **distinto** de v1. Field validators usan `@field_validator`;
    `Config` se reemplaza por `model_config`. Marca esto explícito.
  - Dependency injection: el ejemplo canónico es `get_session` que da una
    `AsyncSession`. Lo construyes aquí y lo reutiliza C01.

### B03 — Jinja2, HTMX y server-rendered UI

- **id**: `B03`
- **slug**: `jinja-htmx-ui`
- **track**: B
- **ord**: 10
- **title**: "UI server-rendered con Jinja2 + HTMX 2"
- **prerequisites**: [B02]
- **next_hints**: [B04, B05]
- **goal**: "Renderizar un fragmento HTML desde FastAPI y refrescarlo con
  `hx-post` + `hx-target`; explicar cuándo HTMX no es la opción correcta."
- **key_concepts**: template, herencia de templates (`extends`/`block`),
  partials, `hx-get`/`hx-post`/`hx-target`/`hx-swap`, `HX-Request` header,
  out-of-band swaps
- **recurring_examples_used**: la pantalla `/m/{slug}` real
- **references_app_code**: `app/templates/module.html`,
  `app/templates/_exercise.html`, `app/routers/exercises.py`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - HTMX 2.x: `hx-on:` reemplaza `hx-on=` viejo. Comprueba con Context7 si
    dudas.
  - Anti-patrón a marcar: usar HTMX para reemplazar React en una SPA pesada.
    HTMX premia páginas multi-screen con interacciones puntuales.
  - El lector debe terminar el módulo habiendo modificado **una plantilla
    real del repo** y viendo el cambio en su navegador.

### B04 — Capas: routers, services, repos, models

- **id**: `B04`
- **slug**: `layers-routers-services-repos`
- **track**: B
- **ord**: 11
- **title**: "Las cuatro capas: routers, services, repos, models"
- **prerequisites**: [A05, A06, B02]
- **next_hints**: [B05, C01, C02]
- **goal**: "Tomar un endpoint que mezcla todo y refactorizarlo en cuatro
  capas con dependency injection."
- **key_concepts**: separation of concerns, capa router/service/repo/model,
  regla de dirección de import, dependency injection como vehículo de
  desacoplamiento
- **recurring_examples_used**: la propia app
- **references_app_code**: `app/routers/progress.py`,
  `app/services/progress.py`, `app/repos/progress.py`,
  `app/models/progress.py`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - Este módulo es **el otro bisagra** del curso (junto con A05). El lector
    debe terminar capaz de mirar cualquier feature de la app y mapearla a
    sus 4 archivos.
  - El ejercicio central es **refactor**: damos un router monolítico de 60
    líneas y el lector lo parte en 4 archivos con tests verdes al final.

### B05 — Editor en navegador: CodeMirror + Pyodide

- **id**: `B05`
- **slug**: `codemirror-and-pyodide`
- **track**: B
- **ord**: 12
- **title**: "Cómo corre Python en el navegador: CodeMirror 6 + Pyodide"
- **prerequisites**: [B03]
- **next_hints**: [E01]
- **goal**: "Explicar el flujo `editor → Pyodide → captura de stdout →
  tests`; añadir un nuevo ejercicio al módulo desde un YAML."
- **key_concepts**: CodeMirror 6 (vista mínima, no plugin internals), Pyodide
  runtime, namespace de ejercicio (`__ns`), captura de stdout (`__cap`),
  test runner del repo
- **recurring_examples_used**: el propio sistema de ejercicios de la app
- **references_app_code**: `app/static/js/runner.js`,
  `app/services/exercise_seed.py`
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - El lector debería terminar habiendo añadido un ejercicio real al
    contenido del módulo en el que esté trabajando (meta-ejercicio).

### B06 — SSE y el chat tutor por dentro

- **id**: `B06`
- **slug**: `sse-and-tutor-chat`
- **track**: B
- **ord**: 13
- **title**: "Streaming con SSE y arquitectura del chat tutor"
- **prerequisites**: [A07, B02]
- **next_hints**: [E02]
- **goal**: "Implementar un endpoint SSE en FastAPI que streamee la respuesta
  de `AsyncAnthropic`; consumirlo desde el frontend con `EventSource`."
- **key_concepts**: Server-Sent Events, `EventSourceResponse` de FastAPI,
  `AsyncAnthropic.messages.stream`, `text_stream`, persistencia de sesión y
  mensajes
- **recurring_examples_used**: el chat real
- **references_app_code**: `app/routers/chat.py`,
  `app/integrations/anthropic_chat.py`, `app/static/js/chat.js`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - Énfasis: SSE es unidireccional servidor→cliente. WebSocket sería
    bidireccional pero overkill para chat.
  - Inyección de contexto: muestra el system prompt real del tutor y por qué
    está marcado con `cache_control`. Hace referencia directa a E03.

---

## Track C — Datos y persistencia

### C01 — SQLAlchemy 2.0 async + SQLite

- **id**: `C01`
- **slug**: `sqlalchemy-async-sqlite`
- **track**: C
- **ord**: 14
- **title**: "SQLAlchemy 2.0 async sobre SQLite"
- **prerequisites**: [A06, A07, B02]
- **next_hints**: [C02, C03]
- **goal**: "Definir un modelo declarativo, abrir una sesión async, ejecutar
  una query con `select()` y un join; entender qué es `flush` vs `commit`."
- **key_concepts**: `DeclarativeBase`, `Mapped[T]`, `mapped_column`,
  `AsyncEngine`, `AsyncSession`, `select()`, joins, `session.begin()`,
  unit of work, "aiosqlite no es realmente async"
- **recurring_examples_used**: `app/models/*` real
- **references_app_code**: `app/db.py`, `app/models/module.py`,
  `app/repos/progress.py`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - **Honestidad técnica**: aiosqlite usa un hilo de fondo por conexión, no
    es no-blocking real. Lo decimos explícito y citamos el doc oficial.
  - El loader del site corre sobre esta capa: el lector ya está usando lo
    que el módulo le enseña.

### C02 — Migraciones con Alembic

- **id**: `C02`
- **slug**: `alembic-migrations`
- **track**: C
- **ord**: 15
- **title**: "Migraciones versionadas con Alembic"
- **prerequisites**: [C01]
- **next_hints**: [C03, D01]
- **goal**: "Generar y revisar una migración autogenerada; reordenar pasos
  cuando autogenerate adivina mal; hacer downgrade."
- **key_concepts**: revisión, `upgrade`/`downgrade`, autogenerate y sus
  limitaciones, migraciones a mano, branches y merges (mención), `env.py`
- **recurring_examples_used**: una migración real del repo
- **references_app_code**: `migrations/env.py`,
  `migrations/versions/{algun_archivo}.py`
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Ejercicio: añadir una columna `notes_md` a `exercise_attempts` y
    generar la migración correctamente.
  - Anti-patrón: editar el archivo de migración después de haberlo aplicado.

### C03 — Multitenancy: del `tenant_id` filter al RLS Postgres

- **id**: `C03`
- **slug**: `multitenancy-rls`
- **track**: C
- **ord**: 16
- **title**: "Multitenancy: tenant_id, RLS, y por qué SQLite no basta en prod"
- **prerequisites**: [C01, C02]
- **next_hints**: [D01, E04, E05]
- **goal**: "Implementar aislamiento por `tenant_id` en cada repo de SQLite;
  describir el equivalente en Postgres con RLS y `current_setting`."
- **key_concepts**: tenant, filtro por `tenant_id`, RLS, policies, `SET LOCAL
  app.tenant_id`, riesgos de olvido en queries ad-hoc, schema-per-tenant,
  db-per-tenant (cuándo)
- **recurring_examples_used**: ACME + Globex (mostrar aislamiento real),
  Initech (caso límite)
- **references_app_code**: `app/repos/_base.py` (helper de filtro),
  `app/services/audit.py` (uso)
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - Esta es la primera vez que el curso decide que SQLite **se queda corto**
    y se compara con Postgres. Tono: "para esta app local, SQLite. Para
    BATUTA producción, Postgres + RLS. Aquí está el mapeo 1:1".
  - El ejercicio: detectar en un repo dado dónde **falta** el filtro de
    `tenant_id`. Tipo: bug-hunting.

---

## Track D — Operación

### D01 — Docker, imágenes y contenedores

- **id**: `D01`
- **slug**: `docker-images-containers`
- **track**: D
- **ord**: 17
- **title**: "Docker: imágenes, contenedores, capas, multi-stage"
- **prerequisites**: [A01, B02]
- **next_hints**: [D02, D03]
- **goal**: "Escribir un Dockerfile multi-stage para la app, entender el orden
  de capas y por qué afecta el cache, y diferenciar imagen vs contenedor."
- **key_concepts**: imagen, contenedor, capa, `Dockerfile`, multi-stage,
  cache de build, `.dockerignore`, `ENTRYPOINT` vs `CMD`
- **recurring_examples_used**: el `Dockerfile` real del repo
- **references_app_code**: `Dockerfile`, `.dockerignore`
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - El Dockerfile de bato-learning **es** el ejemplo. El lector lee el del
    repo línea por línea.
  - Errores típicos: `COPY . .` antes de `pip install` (rompe cache);
    instalar `uv` con curl y luego no fijar versión.

### D02 — Docker Compose y orquestación local

- **id**: `D02`
- **slug**: `docker-compose-local`
- **track**: D
- **ord**: 18
- **title**: "docker compose: servicios, volúmenes, healthchecks"
- **prerequisites**: [D01]
- **next_hints**: [D03, D04]
- **goal**: "Leer y modificar el `compose.yaml` del repo; añadir un servicio
  auxiliar (e.g., un mailcatcher) y conectarlo por la red de compose."
- **key_concepts**: servicio, red, volumen, healthcheck, `depends_on` con
  condición, override files
- **recurring_examples_used**: el `compose.yaml` real del repo
- **references_app_code**: `compose.yaml`, `compose.prod.yaml`
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Modo dev usa volumen montado para hot-reload; modo prod usa imagen
    construida. El lector cambia entre ambos.

### D03 — Despliegue a Hetzner con Traefik

- **id**: `D03`
- **slug**: `hetzner-traefik-deploy`
- **track**: D
- **ord**: 19
- **title**: "Despliegue real: Hetzner, Traefik, TLS, backups"
- **prerequisites**: [D02]
- **next_hints**: [D04]
- **goal**: "Desplegar la app a un Hetzner CX22 con `compose` + Traefik con
  TLS automático; configurar backups de SQLite (litestream o snapshot)."
- **key_concepts**: VPS, DNS A record, Traefik labels, Let's Encrypt
  automático, secrets en `.env` y por qué no en repo, backups, rollback
- **recurring_examples_used**: BATUTA (cómo se desplegará el agente real)
- **references_app_code**: `infra/traefik/traefik.yml`,
  `compose.prod.yaml`, `infra/scripts/backup.sh`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - Si el lector no tiene Hetzner, el módulo le da el comando para correrlo
    en local con Traefik y un dominio `.localhost`. **Sin acceso real al
    despliegue, el módulo está incompleto para él.**
  - Backups: explicar que SQLite vivo + `cp` es **incorrecto** (puede
    capturar mid-write). Usa `.backup` API o litestream.

### D04 — Observabilidad: logs, métricas, trazas, costos

- **id**: `D04`
- **slug**: `observability-traces-cost`
- **track**: D
- **ord**: 20
- **title**: "Observabilidad de un servicio con agentes: traces, costos,
  Phoenix"
- **prerequisites**: [B02, D02, E02]
- **next_hints**: [E04, E05]
- **goal**: "Configurar logging estructurado en JSON, exportar trazas
  OpenInference de Anthropic SDK a Phoenix self-hosted, y rastrear el costo
  por request en un middleware."
- **key_concepts**: logs estructurados, levels, request_id, OpenTelemetry,
  OpenInference, Phoenix, span, atributos, costo por request, latencia p95
- **recurring_examples_used**: la propia app + un agente que ejecutó una
  auditoría
- **references_app_code**: `app/telemetry.py`, `app/middleware/cost.py`,
  `compose.yaml` (servicio phoenix)
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - Phoenix está elegido por DECISIONS.md §4. Lo seguimos.
  - El ejercicio principal: dado un trace en Phoenix, identificar **dónde**
    está la latencia y proponer una optimización (caching, batches, modelo
    más rápido).

---

## Track E — Agentes IA

### E01 — Anthropic SDK a profundidad

- **id**: `E01`
- **slug**: `anthropic-sdk-deep`
- **track**: E
- **ord**: 21
- **title**: "Anthropic SDK: messages, tools, prompt caching, thinking"
- **prerequisites**: [A06, A07, B02]
- **next_hints**: [E02, E03]
- **goal**: "Construir un loop de agente con `messages.create`, tools, y
  prompt caching con `cache_control`; explicar cuándo prender extended
  thinking."
- **key_concepts**: messages API, content blocks (text, tool_use,
  tool_result), JSON schema de tools, `tool_choice`, `cache_control`
  (ephemeral, 5m/1h), extended thinking, streaming, batches (mención)
- **recurring_examples_used**: el demo `/labs/anthropic/loop` real del repo
- **references_app_code**: `api/app/routers/anthropic_demo.py` (referencia
  de producción ya existente)
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - Verifica con Context7 antes de redactar: el modelo `claude-sonnet-4-6` es
    el que usa el repo; el SDK actual soporta `cache_control` con `ttl`
    explícito (5m o 1h). No inventes parámetros.
  - El lector ejecuta `curl` real contra `/labs/anthropic/loop` y mira la
    traza en Phoenix (cierra el círculo con D04).

### E02 — LangGraph y la equivalencia con el SDK

- **id**: `E02`
- **slug**: `langgraph-equivalence`
- **track**: E
- **ord**: 22
- **title**: "LangGraph: StateGraph, ToolNode, checkpointer, equivalencias"
- **prerequisites**: [E01]
- **next_hints**: [E03, E04]
- **goal**: "Reescribir el mismo agente del módulo anterior como un
  StateGraph; usar un checkpointer SQLite; mapear cada primitiva del SDK a
  su equivalente LangGraph."
- **key_concepts**: StateGraph, nodes, edges, conditional edges,
  `add_messages`, ToolNode, tools_condition, MemorySaver/SqliteSaver
  (checkpointer), `interrupt_before`, subgraphs y `Send`
- **recurring_examples_used**: el demo `/labs/langgraph/loop` real
- **references_app_code**: `api/app/routers/langgraph_demo.py`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - Reusa la tabla de equivalencias del CURRICULUM.md §04, **actualizada**
    contra la versión actual de LangGraph (Context7).
  - Reto explícito: "porta un skill real (que el lector usa en Claude Code) a
    un nodo de LangGraph". Esto es el preview del Capstone.

### E03 — Skills, AGENTS.md, CLAUDE.md, contexto limpio

- **id**: `E03`
- **slug**: `skills-agents-context`
- **track**: E
- **ord**: 23
- **title**: "Skills, AGENTS.md, CLAUDE.md y aislamiento de contexto"
- **prerequisites**: [E01]
- **next_hints**: [E04]
- **goal**: "Diseñar un skill con frontmatter y gating; decidir qué va en
  `AGENTS.md`, qué en `CLAUDE.md`, y qué se carga selectivamente; aplicar
  un agente por caso de uso (no un agente que lo hace todo)."
- **key_concepts**: skill, frontmatter (`name`, `description`, `trigger`),
  gating, system prompt, AGENTS.md vs CLAUDE.md, "un agente, un caso de uso",
  slots de skill por tenant
- **recurring_examples_used**: BATUTA (skill `monthly_audit` con slots
  `tone`, `glossary`, `kpis`)
- **references_app_code**: `app/integrations/skills/monthly_audit/SKILL.md`
  (si se crea como parte del scaffold)
- **estimated_minutes**: 60
- **notes_for_subagent**:
  - Funde y profundiza módulos 13 y 14 del site actual.
  - Anti-patrón: el agente "mayordomo universal" que conoce todo. Se
    desmonta con un ejemplo concreto.

### E04 — Memoria, sesiones, multitenancy del estado

- **id**: `E04`
- **slug**: `memory-sessions-multitenant`
- **track**: E
- **ord**: 24
- **title**: "Memoria de agentes: turno, sesión, largo plazo, por tenant"
- **prerequisites**: [E02, E03, C03]
- **next_hints**: [E05]
- **goal**: "Diferenciar memoria de turno / sesión / largo plazo; persistir
  el estado de un agente LangGraph en SQLite por `(tenant_id, thread_id)`;
  diseñar la regla de retención y compactación."
- **key_concepts**: turn memory, session memory (checkpointer), long-term
  memory (store), `thread_id` como `(tenant, conversation)`, compaction,
  aislamiento por tenant en el storage
- **recurring_examples_used**: ACME + Globex (mostrar que sus sesiones no
  se ven entre sí)
- **references_app_code**: `app/repos/chat.py`,
  `app/services/chat.py`, `app/integrations/anthropic_chat.py`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - El chat tutor de la app es **exactamente** este patrón. Cierra el
    círculo con B06.

### E05 — Temporal, durabilidad y workflows por tenant

- **id**: `E05`
- **slug**: `temporal-durable-workflows`
- **track**: E
- **ord**: 25
- **title**: "Temporal: workflows durables, determinismo, schedules"
- **prerequisites**: [E02, E04, D04]
- **next_hints**: [E06]
- **goal**: "Escribir un workflow Temporal que ejecute un agente como
  activity con heartbeats; aplicar las reglas duras de determinismo;
  programar un schedule cron por tenant."
- **key_concepts**: workflow, activity, determinismo, heartbeat,
  `start_to_close_timeout`, retry policy, schedule, search attributes,
  multitenant con `tenant_id` en search attributes
- **recurring_examples_used**: el workflow `AuditTenantWorkflow` real del
  repo
- **references_app_code**: `api/app/workflows/audit.py`,
  `api/app/activities/agent.py`
- **estimated_minutes**: 90
- **notes_for_subagent**:
  - **Énfasis quirúrgico** en las reglas duras: nada de `datetime.now`,
    `random`, IO, LLMs en workflow code. Detector AST como ejercicio (lo
    teníamos en el site, lo mantenemos).
  - Cuándo NO Temporal: chat interactivo, side-effects idempotentes
    baratos. Lo decimos honesto.

---

### E06 — Capstone: portar un agente real a producción multitenant

- **id**: `E06`
- **slug**: `capstone-real-agent`
- **track**: E
- **ord**: 26
- **title**: "Capstone: portar un agente Claude Code a LangGraph + Temporal
  multitenant en Hetzner"
- **prerequisites**: [C03, D03, D04, E02, E03, E04, E05]
- **next_hints**: []
- **goal**: "Tomar un skill real de `batuta-agent-skills`, portarlo a un
  StateGraph LangGraph, envolverlo en un workflow Temporal, desplegarlo a un
  Hetzner CX22 con Phoenix, y evaluar contra un golden set."
- **key_concepts**: integración de todo lo anterior. Sin conceptos nuevos.
- **recurring_examples_used**: BATUTA real
- **references_app_code**: el capstone vive en
  `app/content/E/capstone-real-agent/` y consume todos los anteriores.
- **use_cases_referenced**: [F-CTA-02]  # auditoría interna como skill base
- **estimated_minutes**: 90 (tiempo dirigido; el trabajo real son 4–8 h)
- **notes_for_subagent**:
  - Este es el módulo del Sonnet **integrador**, no de un Sonnet de módulo
    suelto. Lo escribe al final.
  - Criterios de "listo" del Capstone:
    - El agente corre contra ACME y Globex con `tenant_id` correcto.
    - Hay 5 ejemplos del golden set y se evalúan en CI.
    - Las trazas aparecen en Phoenix.
    - El backup de SQLite se restaura limpio.
    - El workflow se cancela y se reanuda preservando estado.

---

## Track F — Playbook por departamento × industria

Track F es el **catálogo de casos de uso vendibles**. No es lineal: las fichas
se referencian desde módulos técnicos (`use_cases_referenced`) y se navegan
libremente desde un índice por departamento en el site.

### Estructura común de cada ficha (resumen, contrato completo en SHARED §5.8)

- `id`: `F-{DEPT}-{ord:02}`, donde `DEPT` es uno de FIN, CTA, CMP, OPS, VTA,
  MKT, RH, CX, LEG, PRD.
- `track`: `F`.
- `dept`: departamento canónico.
- `related_modules`: lista de ids de Track A–E que aplican.
- `industries_instanced`: ≥ 2 ids de industrias canónicas
  (SHARED §2.1.3).
- `tenants_in_examples`: ≥ 2 slugs de tenants (SHARED §2.1).
- `big_corp_vendors`: 2–4 nombres de vendor enterprise.
- `latam_tools`: 1–3 ids de herramientas LATAM.
- `key_concepts`: 3–6 términos.
- `estimated_minutes`: 30 / 45 / 60 (lectura, no implementación).
- `deterministic_share`: estimación 0.0–1.0 del peso determinístico del flujo.

### Tabla resumen del Track F

| id | dept | título | industries | det.share |
|----|------|--------|------------|-----------|
| F-FIN-01 | FIN | Conciliación bancaria multi-cuenta | retail, servicios-fin | 0.7 |
| F-FIN-02 | FIN | Forecast de cash flow 13 semanas | manufactura, serv-prof | 0.5 |
| F-FIN-03 | FIN | Cierre mensual asistido | manufactura, salud | 0.6 |
| F-FIN-04 | FIN | Gestión de crédito a clientes (cobranza) | retail, logistica | 0.5 |
| F-CTA-01 | CTA | Clasificación contable de transacciones | servicios-fin, hospitalidad | 0.6 |
| F-CTA-02 | CTA | Auditoría interna: anomalías y duplicados | manufactura, salud | 0.65 |
| F-CTA-03 | CTA | Preparación de declaraciones fiscales | retail, construccion | 0.8 |
| F-CTA-04 | CTA | Conciliación intercompañía | manufactura, energia | 0.75 |
| F-CMP-01 | CMP | Comparación de cotizaciones (RFQ) | manufactura, construccion | 0.5 |
| F-CMP-02 | CMP | Evaluación periódica de proveedores | retail, logistica | 0.4 |
| F-CMP-03 | CMP | OCR + validación de facturas de proveedor | salud, hospitalidad | 0.7 |
| F-CMP-04 | CMP | Gestión de contratos marco (vencimientos) | servicios-fin, construccion | 0.55 |
| F-OPS-01 | OPS | Planeación de producción semanal | manufactura, hospitalidad | 0.6 |
| F-OPS-02 | OPS | Forecast de demanda por SKU/canal | retail, agro | 0.5 |
| F-OPS-03 | OPS | Optimización de inventario (stock-out vs sobrestock) | retail, salud | 0.7 |
| F-OPS-04 | OPS | Planeación de capacidad y staffing | logistica, hospitalidad | 0.55 |
| F-VTA-01 | VTA | Scoring y priorización de leads | servicios-fin, serv-prof | 0.3 |
| F-VTA-02 | VTA | Forecast de cierre del trimestre | retail, manufactura | 0.45 |
| F-VTA-03 | VTA | Pipeline en riesgo y next-actions | servicios-fin, serv-prof | 0.3 |
| F-VTA-04 | VTA | Análisis de churn comercial | serv-prof, energia | 0.4 |
| F-MKT-01 | MKT | Post-mortem de campañas (ROAS) | retail, serv-prof | 0.6 |
| F-MKT-02 | MKT | Segmentación y propuestas de campaña | retail, hospitalidad | 0.3 |
| F-MKT-03 | MKT | Generación de contenido (con guardrails de brand) | hospitalidad, serv-prof | 0.2 |
| F-MKT-04 | MKT | Social listening y monitoreo de menciones | retail, salud | 0.4 |
| F-RH-01  | RH  | Screening de CVs por descripción de cargo | hospitalidad, serv-prof | 0.3 |
| F-RH-02  | RH  | Análisis de encuestas eNPS / clima | salud, manufactura | 0.4 |
| F-RH-03  | RH  | Onboarding personalizado por rol | serv-prof, retail | 0.3 |
| F-RH-04  | RH  | Análisis de turnover y banderas tempranas | hospitalidad, logistica | 0.5 |
| F-CX-01  | CX  | Triage automático de tickets | retail, servicios-fin | 0.4 |
| F-CX-02  | CX  | Resumen + next-action de llamadas | salud, servicios-fin | 0.3 |
| F-CX-03  | CX  | Generación y mantenimiento de KB | retail, hospitalidad | 0.4 |
| F-CX-04  | CX  | Detección de cliente en riesgo (CSAT decaying) | servicios-fin, energia | 0.5 |
| F-LEG-01 | LEG | Revisión de cláusulas en contratos | construccion, servicios-fin | 0.4 |
| F-LEG-02 | LEG | Due diligence preliminar (KYC/AML básico) | servicios-fin, salud | 0.5 |
| F-LEG-03 | LEG | Monitoreo regulatorio sectorial | energia, salud | 0.3 |
| F-LEG-04 | LEG | Gestión de poderes y vigencias | construccion, agro | 0.6 |
| F-PRD-01 | PRD | Análisis de feedback y priorización | retail, serv-prof | 0.4 |
| F-PRD-02 | PRD | Triage de bugs y duplicados | servicios-fin, serv-prof | 0.55 |
| F-PRD-03 | PRD | Generación de specs desde tickets | retail, serv-prof | 0.3 |

> [!nota]
> Algunas industrias aparecen más en unas fichas que en otras. La regla es que
> **cada industria de SHARED §2.1.3 aparezca en al menos 3 fichas distintas**.
> Verificado en la distribución de arriba.

### Fichas — detalle (orden por departamento)

#### FIN — Finanzas y Tesorería

##### F-FIN-01 — Conciliación bancaria multi-cuenta

- **id**: `F-FIN-01`
- **slug**: `conciliacion-bancaria`
- **track**: F
- **dept**: FIN
- **ord**: 1
- **title**: "Conciliación bancaria multi-cuenta"
- **related_modules**: [A05, B03, C03, D04, E01, E05]
- **industries_instanced**: [retail, servicios-fin]
- **tenants_in_examples**: [tiendabox, cooppopular]
- **big_corp_vendors**: [BlackLine, Trintech, FloQast]
- **latam_tools**: [siigo, world_office, belvo]
- **key_concepts**: matching, tolerancias, fuzzy-match, reglas-duras, agente-de-excepciones
- **estimated_minutes**: 60
- **deterministic_share**: 0.7
- **notes_for_subagent**: |
    Determinístico: parsing del extracto + matching exacto por monto+fecha+ref;
    agregación por gateway de pago en retail.
    Agéntico: emparejamiento de transacciones con descripción ambigua,
    clasificar diferencias en timing/error/desconocido.
    Big corp: BlackLine/Trintech (50-250 USD/usuario/mes + setup 20-80k).
    PYME LATAM: extracto PDF de banco + libro contable Excel/Siigo + agente.
    Belvo/Plaid LATAM opcional si el cliente quiere API en vivo.
    Fallback humano: cualquier diferencia >5% sobre el saldo cae a revisión.
    Precio orientativo: 250-700 USD/mes según volumen.

##### F-FIN-02 — Forecast de cash flow 13 semanas

- **id**: `F-FIN-02`
- **slug**: `cashflow-forecast-13w`
- **track**: F
- **dept**: FIN
- **ord**: 2
- **title**: "Forecast de cash flow rolling a 13 semanas"
- **related_modules**: [A06, B02, C01, E01, E05]
- **industries_instanced**: [manufactura, serv-prof]
- **tenants_in_examples**: [acme, consultorabc]
- **big_corp_vendors**: [Workday Adaptive, Anaplan, Cube, Pigment]
- **latam_tools**: [siigo, excel, alegra]
- **key_concepts**: receivables, payables, payroll cycle, runway, escenarios, what-if
- **estimated_minutes**: 60
- **deterministic_share**: 0.5
- **notes_for_subagent**: |
    Determinístico: ingesta AR/AP del ERP, calendario de pagos fijos, cálculo
    de runway en escenario base.
    Agéntico: estimar timing de cobro de cuentas con historial irregular,
    redactar el ejecutivo summary semanal con narrativa.
    Big corp: Workday Adaptive 30-200 USD/u/mes; Anaplan desde 1000 USD/u/mes.
    PYME LATAM: ERP local + dos hojas Excel + agente que reescribe el
    rolling cada lunes 06:00.
    Schedule Temporal aterriza aquí: una corrida programada por tenant.

##### F-FIN-03 — Cierre mensual asistido

- **id**: `F-FIN-03`
- **slug**: `cierre-mensual-asistido`
- **track**: F
- **dept**: FIN
- **ord**: 3
- **title**: "Cierre mensual asistido (rápido + checklist agéntico)"
- **related_modules**: [A06, A07, C02, D04, E03, E05]
- **industries_instanced**: [manufactura, salud]
- **tenants_in_examples**: [acme, sanrafael]
- **big_corp_vendors**: [BlackLine, FloQast, Trintech]
- **latam_tools**: [siigo, contpaq, world_office]
- **key_concepts**: close-checklist, journal-entries, validaciones, holds, sign-off
- **estimated_minutes**: 60
- **deterministic_share**: 0.6
- **notes_for_subagent**: |
    Determinístico: validar que cada cuenta tenga conciliación, depreciaciones
    calculadas, accruals registrados, balances cuadran.
    Agéntico: revisar la narrativa de cierres anteriores y proponer comentarios
    sobre variaciones significativas; clasificar findings como "informar" vs
    "bloquear cierre".
    Compara FloQast (60-150 USD/u/mes) con un agente que vive sobre Siigo.

##### F-FIN-04 — Gestión de crédito a clientes (cobranza)

- **id**: `F-FIN-04`
- **slug**: `gestion-credito-cobranza`
- **track**: F
- **dept**: FIN
- **ord**: 4
- **title**: "Gestión de crédito y cobranza temprana"
- **related_modules**: [B02, B06, C03, E01, E04]
- **industries_instanced**: [retail, logistica]
- **tenants_in_examples**: [tiendabox, expreslog]
- **big_corp_vendors**: [HighRadius, Billtrust, Esker]
- **latam_tools**: [siigo, alegra, kushki, mercadopago]
- **key_concepts**: aging, scoring de riesgo, tono de comunicación, escalamiento
- **estimated_minutes**: 60
- **deterministic_share**: 0.5
- **notes_for_subagent**: |
    Determinístico: aging por bucket (0-30/31-60/61-90/90+), generación de
    listas de seguimiento, plantilla de comunicación.
    Agéntico: ajustar tono por historial de cliente (no mandar el "tono duro"
    a un cliente que paga en 35 días siempre), decidir momento de escalamiento
    a un humano.
    Fallback: cliente VIP marcado en CRM nunca recibe comunicación
    automatizada sin sign-off.

#### CTA — Contabilidad

##### F-CTA-01 — Clasificación contable de transacciones

- **id**: `F-CTA-01`
- **slug**: `clasificacion-contable`
- **track**: F
- **dept**: CTA
- **ord**: 1
- **title**: "Clasificación contable de transacciones bancarias"
- **related_modules**: [A06, B02, C01, E01]
- **industries_instanced**: [servicios-fin, hospitalidad]
- **tenants_in_examples**: [cooppopular, mesonurbano]
- **big_corp_vendors**: [Vic.ai, BlackLine, AppZen]
- **latam_tools**: [siigo, contpaq, alegra, world_office]
- **key_concepts**: PUC (plan único de cuentas), centros de costo, reglas previas, confianza-low
- **estimated_minutes**: 45
- **deterministic_share**: 0.6
- **notes_for_subagent**: |
    Determinístico: aplicar reglas previas del PUC del cliente (palabra clave
    → cuenta), agregaciones por centro de costo.
    Agéntico: clasificar transacciones nuevas que no caen en regla previa,
    proponer creación de regla cuando un patrón se repite.
    Mostrar el patrón "low-confidence batch" donde el agente marca para
    revisión humana cualquier match con probabilidad <0.85.

##### F-CTA-02 — Auditoría interna: anomalías y duplicados

- **id**: `F-CTA-02`
- **slug**: `auditoria-interna-anomalias`
- **track**: F
- **dept**: CTA
- **ord**: 2
- **title**: "Auditoría interna de transacciones (anomalías y duplicados)"
- **related_modules**: [A06, C03, D04, E01, E05]
- **industries_instanced**: [manufactura, salud]
- **tenants_in_examples**: [acme, sanrafael]
- **big_corp_vendors**: [AppZen, MindBridge, Trullion]
- **latam_tools**: [siigo, contpaq]
- **key_concepts**: duplicado-estricto, duplicado-difuso, monto-fuera-de-rango, ronda-mensual
- **estimated_minutes**: 60
- **deterministic_share**: 0.65
- **notes_for_subagent**: |
    Este es el caso **ancla** del Capstone E06: la auditoría mensual de BATUTA.
    Determinístico: detección de duplicados por hash (proveedor + monto + fecha),
    monto fuera de banda histórica por proveedor, gaps en numeración de
    documentos.
    Agéntico: clasificar duplicados borrosos (mismo monto, distinto día,
    misma descripción), redactar el reporte con findings ordenados por riesgo.
    Aquí cae el `monthly_audit` skill de SHARED §2.2.

##### F-CTA-03 — Preparación de declaraciones fiscales

- **id**: `F-CTA-03`
- **slug**: `declaraciones-fiscales`
- **track**: F
- **dept**: CTA
- **ord**: 3
- **title**: "Preparación de declaraciones fiscales mensuales"
- **related_modules**: [B02, C01, E01, E05]
- **industries_instanced**: [retail, construccion]
- **tenants_in_examples**: [tiendabox, andina]
- **big_corp_vendors**: [Vertex, Avalara, Sovos]
- **latam_tools**: [siigo, dian-muisca, sat-mexico, contpaq]
- **key_concepts**: IVA, retención fuente, ICA, conciliación con libros, plantilla regulatoria
- **estimated_minutes**: 45
- **deterministic_share**: 0.8
- **notes_for_subagent**: |
    **Mayoría determinística** — la regulación define las reglas. El agente
    aporta en: detectar inconsistencias (monto reportado vs libro), redactar
    notas explicativas de variaciones, sugerir provisiones si el flujo
    incompleto.
    Riesgo regulatorio: el output **nunca** se presenta sin revisión humana.
    Mostrar el `human_in_the_loop` interrupt antes del `submit_declaration`.

##### F-CTA-04 — Conciliación intercompañía

- **id**: `F-CTA-04`
- **slug**: `conciliacion-intercompania`
- **track**: F
- **dept**: CTA
- **ord**: 4
- **title**: "Conciliación intercompañía (intercompany matching)"
- **related_modules**: [A06, C01, C03, E01]
- **industries_instanced**: [manufactura, energia]
- **tenants_in_examples**: [acme, solenergy]
- **big_corp_vendors**: [BlackLine Intercompany, SAP ICR, Trintech]
- **latam_tools**: [excel-cross-company, siigo-grupos]
- **key_concepts**: AP-AR matching, transfer pricing, FX diff, cut-off
- **estimated_minutes**: 60
- **deterministic_share**: 0.75
- **notes_for_subagent**: |
    Determinístico: match exacto por número de factura intercompañía, cálculo
    de FX diff, validación de cut-off de fecha.
    Agéntico: explicar diferencias residuales, proponer ajuste sugerido con
    justificación.

#### CMP — Compras y Abastecimiento

##### F-CMP-01 — Comparación de cotizaciones (RFQ)

- **id**: `F-CMP-01`
- **slug**: `comparacion-cotizaciones`
- **track**: F
- **dept**: CMP
- **ord**: 1
- **title**: "Comparación de cotizaciones (3+ proveedores) y recomendación"
- **related_modules**: [A06, B02, E01]
- **industries_instanced**: [manufactura, construccion]
- **tenants_in_examples**: [acme, andina]
- **big_corp_vendors**: [Coupa, SAP Ariba, Jaggaer]
- **latam_tools**: [excel, siigo-ordenes-compra]
- **key_concepts**: total-cost-of-ownership, plazos, calidad, scoring multi-criterio
- **estimated_minutes**: 45
- **deterministic_share**: 0.5
- **notes_for_subagent**: |
    Determinístico: normalizar formatos de cotizaciones distintas a una tabla
    comparable; aplicar pesos definidos por el cliente.
    Agéntico: detectar "letra chica" en cotizaciones PDF que cambian el TCO
    (transporte, garantía, condiciones de pago), redactar la recomendación.

##### F-CMP-02 — Evaluación periódica de proveedores

- **id**: `F-CMP-02`
- **slug**: `evaluacion-proveedores`
- **track**: F
- **dept**: CMP
- **ord**: 2
- **title**: "Evaluación trimestral de proveedores (KPI scorecards)"
- **related_modules**: [B02, C01, D04, E01]
- **industries_instanced**: [retail, logistica]
- **tenants_in_examples**: [tiendabox, expreslog]
- **big_corp_vendors**: [SAP Ariba SLP, Coupa, Ivalua]
- **latam_tools**: [excel, world_office]
- **key_concepts**: on-time-delivery, quality-rate, price-stability, escalamiento
- **estimated_minutes**: 45
- **deterministic_share**: 0.4
- **notes_for_subagent**: |
    Determinístico: cálculo de métricas (OTD, defect rate, variación de precio).
    Agéntico: redactar feedback al proveedor con tono profesional, identificar
    patrones (un proveedor que empieza a degradar pero aún cumple).

##### F-CMP-03 — OCR + validación de facturas de proveedor

- **id**: `F-CMP-03`
- **slug**: `ocr-validacion-facturas`
- **track**: F
- **dept**: CMP
- **ord**: 3
- **title**: "OCR + validación de facturas de proveedor (3-way match)"
- **related_modules**: [A06, B02, C01, E01]
- **industries_instanced**: [salud, hospitalidad]
- **tenants_in_examples**: [sanrafael, mesonurbano]
- **big_corp_vendors**: [Esker, Tradeshift, Vic.ai, Tipalti]
- **latam_tools**: [siigo-fe, contpaq-cfdi, alegra]
- **key_concepts**: OCR, parsing, 3-way-match (PO/recepción/factura), tolerancias
- **estimated_minutes**: 60
- **deterministic_share**: 0.7
- **notes_for_subagent**: |
    Determinístico: extracción con `parse_invoice_pdf`, validación contra PO,
    cálculo de tolerancias.
    Agéntico: resolver discrepancias menores (descripción de ítem ligeramente
    distinta, cargo de envío no en PO), redactar consulta al proveedor.
    En LATAM: factura electrónica (DIAN/SAT) en XML facilita el determinismo.

##### F-CMP-04 — Gestión de contratos marco

- **id**: `F-CMP-04`
- **slug**: `contratos-marco-vencimientos`
- **track**: F
- **dept**: CMP
- **ord**: 4
- **title**: "Gestión de contratos marco (renovaciones, cláusulas, vencimientos)"
- **related_modules**: [B02, C01, E01, E05]
- **industries_instanced**: [servicios-fin, construccion]
- **tenants_in_examples**: [cooppopular, andina]
- **big_corp_vendors**: [Ironclad, Icertis, DocuSign CLM]
- **latam_tools**: [excel, drive-shared]
- **key_concepts**: cláusulas-clave, vencimientos, auto-renew, escalamiento
- **estimated_minutes**: 45
- **deterministic_share**: 0.55
- **notes_for_subagent**: |
    Determinístico: indexar PDFs, extraer fechas y partes con `parse_contract_pdf`,
    alerta T-30/T-60/T-90.
    Agéntico: identificar cláusulas riesgosas (auto-renew, exclusividad,
    SLA con penalidades), comparar contra plantilla aprobada y resaltar deltas.

#### OPS — Operaciones y Supply Chain

##### F-OPS-01 — Planeación de producción semanal

- **id**: `F-OPS-01`
- **slug**: `planeacion-produccion-semanal`
- **track**: F
- **dept**: OPS
- **ord**: 1
- **title**: "Planeación de producción semanal (capacidad + demanda + materiales)"
- **related_modules**: [A06, C01, E01, E05]
- **industries_instanced**: [manufactura, hospitalidad]
- **tenants_in_examples**: [acme, mesonurbano]
- **big_corp_vendors**: [SAP IBP, Anaplan, Kinaxis, o9]
- **latam_tools**: [excel, world_office, datup]
- **key_concepts**: MPS, MRP, capacity-constraint, bottleneck, what-if
- **estimated_minutes**: 60
- **deterministic_share**: 0.6
- **notes_for_subagent**: |
    Determinístico: cálculo de requisitos de material desde BOM, validación
    de capacidad por línea, generación de OF.
    Agéntico: priorizar cuando hay conflicto (orden urgente vs cliente
    grande), redactar explicación de cambios al plan respecto a la semana
    anterior.

##### F-OPS-02 — Forecast de demanda por SKU/canal

- **id**: `F-OPS-02`
- **slug**: `forecast-demanda-sku`
- **track**: F
- **dept**: OPS
- **ord**: 2
- **title**: "Forecast de demanda por SKU y canal (mensual rolling)"
- **related_modules**: [A06, C01, D04, E01, E05]
- **industries_instanced**: [retail, agro]
- **tenants_in_examples**: [tiendabox, cafetera]
- **big_corp_vendors**: [SAP IBP, Anaplan, o9, Kinaxis, Blue Yonder]
- **latam_tools**: [excel, datup, world_office]
- **key_concepts**: estacionalidad, promociones, intermittent-demand, MAPE/wMAPE
- **estimated_minutes**: 60
- **deterministic_share**: 0.5
- **notes_for_subagent**: |
    Determinístico: modelos clásicos (ETS/ARIMA) por SKU clase A, agregación
    por canal, cálculo de error.
    Agéntico: identificar SKUs anómalos (lanzamiento, fin de vida), explicar
    qué cambió respecto al mes anterior en lenguaje de planificador.
    Big corp: o9 / Kinaxis 100k-1M USD/año. PYME: Excel + agente sobre Siigo.

##### F-OPS-03 — Optimización de inventario

- **id**: `F-OPS-03`
- **slug**: `optimizacion-inventario`
- **track**: F
- **dept**: OPS
- **ord**: 3
- **title**: "Optimización de inventario (stock-out vs sobrestock)"
- **related_modules**: [A06, C01, E01]
- **industries_instanced**: [retail, salud]
- **tenants_in_examples**: [tiendabox, sanrafael]
- **big_corp_vendors**: [Blue Yonder, ToolsGroup, RELEX]
- **latam_tools**: [excel, world_office]
- **key_concepts**: ROP, safety-stock, ABC-XYZ, días-de-inventario
- **estimated_minutes**: 45
- **deterministic_share**: 0.7
- **notes_for_subagent**: |
    Determinístico: cálculo de ROP, safety stock, clasificación ABC-XYZ.
    Agéntico: explicar por qué un SKU clase A salió de banda, recomendar
    acción (acelerar PO, sustituir SKU, descontinuar).
    En salud: SKUs críticos (medicamentos vitales) **nunca** se reducen sin
    sign-off humano. Mostrar el guardrail.

##### F-OPS-04 — Planeación de capacidad y staffing

- **id**: `F-OPS-04`
- **slug**: `capacidad-staffing`
- **track**: F
- **dept**: OPS
- **ord**: 4
- **title**: "Planeación de capacidad y staffing (turnos, picos)"
- **related_modules**: [B02, C01, E01, E05]
- **industries_instanced**: [logistica, hospitalidad]
- **tenants_in_examples**: [expreslog, mesonurbano]
- **big_corp_vendors**: [Kronos / UKG, Quinyx, Workday Scheduling]
- **latam_tools**: [excel, alegra-nomina]
- **key_concepts**: forecast-tráfico, ratios de servicio, restricciones laborales
- **estimated_minutes**: 45
- **deterministic_share**: 0.55
- **notes_for_subagent**: |
    Determinístico: cálculo de FTE necesario por hora con ratio de servicio
    declarado; respeto a restricciones laborales (descansos, max hours/week).
    Agéntico: proponer ajustes ante eventos no-recurrentes (lanzamiento,
    feriado local, evento corporativo), redactar mensaje a empleados.

#### VTA — Ventas Comercial

##### F-VTA-01 — Scoring y priorización de leads

- **id**: `F-VTA-01`
- **slug**: `scoring-leads`
- **track**: F
- **dept**: VTA
- **ord**: 1
- **title**: "Scoring y priorización de leads desde CRM"
- **related_modules**: [B02, C01, E01]
- **industries_instanced**: [servicios-fin, serv-prof]
- **tenants_in_examples**: [cooppopular, consultorabc]
- **big_corp_vendors**: [Salesforce Einstein, HubSpot AI, 6sense]
- **latam_tools**: [hubspot-starter, pipedrive, excel]
- **key_concepts**: BANT, intent-signals, fit-vs-intent, próxima-acción
- **estimated_minutes**: 45
- **deterministic_share**: 0.3
- **notes_for_subagent**: |
    Determinístico: features explícitos del CRM (industria, tamaño,
    interacciones recientes).
    Agéntico: leer notas libres del vendedor, identificar señales de intent
    (preguntas sobre pricing, comparación con competidor), sugerir next step.

##### F-VTA-02 — Forecast de cierre del trimestre

- **id**: `F-VTA-02`
- **slug**: `forecast-cierre-q`
- **track**: F
- **dept**: VTA
- **ord**: 2
- **title**: "Forecast de cierre del trimestre por vendedor y segmento"
- **related_modules**: [A06, C01, E01, E05]
- **industries_instanced**: [retail, manufactura]
- **tenants_in_examples**: [tiendabox, acme]
- **big_corp_vendors**: [Clari, Salesforce Einstein, BoostUp]
- **latam_tools**: [hubspot, pipedrive, excel]
- **key_concepts**: pipeline-coverage, win-rate, sandbagging, calibración
- **estimated_minutes**: 45
- **deterministic_share**: 0.45
- **notes_for_subagent**: |
    Determinístico: probabilidad por etapa × ARR × edad del deal.
    Agéntico: detectar deals "sandbagged" (vendedor conservador
    sistemáticamente), comparar pronóstico del vendedor con el calculado.

##### F-VTA-03 — Pipeline en riesgo

- **id**: `F-VTA-03`
- **slug**: `pipeline-en-riesgo`
- **track**: F
- **dept**: VTA
- **ord**: 3
- **title**: "Análisis de pipeline en riesgo y próximas acciones"
- **related_modules**: [B02, C01, E01]
- **industries_instanced**: [servicios-fin, serv-prof]
- **tenants_in_examples**: [cooppopular, consultorabc]
- **big_corp_vendors**: [Clari, Gong, Outreach]
- **latam_tools**: [hubspot, pipedrive]
- **key_concepts**: deal-velocity, last-touch, multithreading, escalation
- **estimated_minutes**: 45
- **deterministic_share**: 0.3
- **notes_for_subagent**: |
    Determinístico: días sin actividad, edad vs etapa, threading (cuántos
    contactos en la cuenta).
    Agéntico: leer correos / transcripts de calls, identificar señales de
    estancamiento, sugerir próxima acción concreta.

##### F-VTA-04 — Análisis de churn comercial

- **id**: `F-VTA-04`
- **slug**: `churn-comercial`
- **track**: F
- **dept**: VTA
- **ord**: 4
- **title**: "Análisis de churn comercial y campaña de retención"
- **related_modules**: [A06, B02, C01, D04, E01]
- **industries_instanced**: [serv-prof, energia]
- **tenants_in_examples**: [consultorabc, solenergy]
- **big_corp_vendors**: [Gainsight, ChurnZero, Salesforce]
- **latam_tools**: [hubspot, planilla-csv]
- **key_concepts**: NRR, GRR, cohort-analysis, leading-indicators
- **estimated_minutes**: 45
- **deterministic_share**: 0.4
- **notes_for_subagent**: |
    Determinístico: cálculo de cohort, NRR/GRR, identificación de cuentas que
    se acercan a renovación con uso bajo.
    Agéntico: clasificar el motivo probable de churn desde tickets+notas,
    sugerir oferta de retención apropiada (no dar descuento a un cliente
    que se va por feature gap).

#### MKT — Marketing

##### F-MKT-01 — Post-mortem de campañas (ROAS)

- **id**: `F-MKT-01`
- **slug**: `postmortem-campanas-roas`
- **track**: F
- **dept**: MKT
- **ord**: 1
- **title**: "Post-mortem de campañas digitales (atribución y ROAS)"
- **related_modules**: [A06, B02, C01, E01]
- **industries_instanced**: [retail, serv-prof]
- **tenants_in_examples**: [tiendabox, consultorabc]
- **big_corp_vendors**: [Adobe Analytics, GA4 360, Funnel.io]
- **latam_tools**: [ga4, meta-ads-manager, looker-studio]
- **key_concepts**: ROAS, atribución multi-touch, payback, incrementalidad
- **estimated_minutes**: 45
- **deterministic_share**: 0.6
- **notes_for_subagent**: |
    Determinístico: extracción de Meta/Google Ads, atribución last-click,
    cálculo de ROAS por canal/campaña.
    Agéntico: redactar el resumen ejecutivo, identificar hipótesis de por qué
    una campaña bajó performance, proponer test.

##### F-MKT-02 — Segmentación y propuestas de campaña

- **id**: `F-MKT-02`
- **slug**: `segmentacion-propuestas`
- **track**: F
- **dept**: MKT
- **ord**: 2
- **title**: "Segmentación de clientes y propuesta de campañas"
- **related_modules**: [A06, B02, C01, E01]
- **industries_instanced**: [retail, hospitalidad]
- **tenants_in_examples**: [tiendabox, mesonurbano]
- **big_corp_vendors**: [Salesforce Marketing Cloud, Braze, Klaviyo]
- **latam_tools**: [klaviyo, mailchimp, excel]
- **key_concepts**: RFM, lookalike, propensity, brief-creativo
- **estimated_minutes**: 45
- **deterministic_share**: 0.3
- **notes_for_subagent**: |
    Determinístico: segmentación RFM, agregaciones por cohort.
    Agéntico: nombrar y describir cada segmento en lenguaje de marketing,
    redactar el brief de campaña por segmento.

##### F-MKT-03 — Generación de contenido con guardrails

- **id**: `F-MKT-03`
- **slug**: `generacion-contenido-brand`
- **track**: F
- **dept**: MKT
- **ord**: 3
- **title**: "Generación de contenido con guardrails de brand"
- **related_modules**: [E01, E03]
- **industries_instanced**: [hospitalidad, serv-prof]
- **tenants_in_examples**: [mesonurbano, consultorabc]
- **big_corp_vendors**: [Jasper, Writer.com, Adobe Firefly]
- **latam_tools**: [chatgpt-team, claude-team]
- **key_concepts**: brand-voice, slots, banned-words, eval-rúbrica
- **estimated_minutes**: 45
- **deterministic_share**: 0.2
- **notes_for_subagent**: |
    Determinístico: validación contra banned-words, longitud, formato.
    Agéntico: producción del texto. La diferencia entre demo y producto:
    el skill por tenant (E03) con tono, glosario, KPIs en slots.
    Fallback: el output **pasa** por marketer humano siempre antes de
    publicar.

##### F-MKT-04 — Social listening y monitoreo

- **id**: `F-MKT-04`
- **slug**: `social-listening`
- **track**: F
- **dept**: MKT
- **ord**: 4
- **title**: "Social listening y análisis de menciones"
- **related_modules**: [B02, B06, C01, E01]
- **industries_instanced**: [retail, salud]
- **tenants_in_examples**: [tiendabox, sanrafael]
- **big_corp_vendors**: [Brandwatch, Sprinklr, Talkwalker]
- **latam_tools**: [mention, hootsuite, sprout-social]
- **key_concepts**: sentiment, share-of-voice, crisis-trigger, alerting
- **estimated_minutes**: 45
- **deterministic_share**: 0.4
- **notes_for_subagent**: |
    Determinístico: ingesta de menciones, cálculo de SoV, alerta por umbral.
    Agéntico: clasificar sentiment (más allá de +/-), detectar early signal
    de crisis (palabras + contexto + autor de alta influencia).

#### RH — RRHH y Talento

##### F-RH-01 — Screening de CVs

- **id**: `F-RH-01`
- **slug**: `screening-cvs`
- **track**: F
- **dept**: RH
- **ord**: 1
- **title**: "Screening de CVs por descripción de cargo"
- **related_modules**: [A06, B02, E01, E03]
- **industries_instanced**: [hospitalidad, serv-prof]
- **tenants_in_examples**: [mesonurbano, consultorabc]
- **big_corp_vendors**: [Workday Recruiting, HireVue, Eightfold AI]
- **latam_tools**: [linkedin-recruiter, computrabajo, indeed]
- **key_concepts**: must-have-vs-nice, sesgo-protegido, transparencia
- **estimated_minutes**: 45
- **deterministic_share**: 0.3
- **notes_for_subagent**: |
    Determinístico: filtros explícitos (años de experiencia, idioma,
    certificaciones).
    Agéntico: leer experiencia narrativa, sugerir ranking, **explicar por qué**
    cada candidato sube o baja. Sin sesgo protegido (edad, género, etnia).
    Regulación: GDPR/Ley protección datos. **El agente nunca rechaza
    automáticamente**: solo sugiere ranking para revisión humana.

##### F-RH-02 — Análisis de encuestas eNPS

- **id**: `F-RH-02`
- **slug**: `analisis-enps`
- **track**: F
- **dept**: RH
- **ord**: 2
- **title**: "Análisis de encuestas eNPS y clima organizacional"
- **related_modules**: [A06, C01, E01]
- **industries_instanced**: [salud, manufactura]
- **tenants_in_examples**: [sanrafael, acme]
- **big_corp_vendors**: [Culture Amp, Qualtrics EX, Workday Peakon]
- **latam_tools**: [google-forms, typeform, sharepoint]
- **key_concepts**: eNPS, comentarios-abiertos, anonimato, drivers-de-engagement
- **estimated_minutes**: 45
- **deterministic_share**: 0.4
- **notes_for_subagent**: |
    Determinístico: cálculo de eNPS, agrupación por área/antigüedad.
    Agéntico: análisis temático de comentarios abiertos, identificación de
    drivers, redacción de resumen ejecutivo.
    Anonimato: el agente **nunca** muestra nombres ni IDs de empleados; el
    pipeline filtra antes del modelo.

##### F-RH-03 — Onboarding personalizado

- **id**: `F-RH-03`
- **slug**: `onboarding-personalizado`
- **track**: F
- **dept**: RH
- **ord**: 3
- **title**: "Onboarding personalizado por rol y área"
- **related_modules**: [B02, B03, E01, E03]
- **industries_instanced**: [serv-prof, retail]
- **tenants_in_examples**: [consultorabc, tiendabox]
- **big_corp_vendors**: [Workday Onboarding, Enboarder, Sapling]
- **latam_tools**: [notion, confluence-cloud, sharepoint]
- **key_concepts**: checklist-por-rol, glosario-empresa, mentor-asignado, día-30/60/90
- **estimated_minutes**: 30
- **deterministic_share**: 0.3
- **notes_for_subagent**: |
    Determinístico: checklist por rol, recursos pre-asignados.
    Agéntico: responder preguntas del nuevo empleado en chat usando
    documentación interna; identificar gaps en la doc cuando una pregunta
    se repite.

##### F-RH-04 — Análisis de turnover

- **id**: `F-RH-04`
- **slug**: `analisis-turnover`
- **track**: F
- **dept**: RH
- **ord**: 4
- **title**: "Análisis de turnover y banderas tempranas"
- **related_modules**: [A06, C01, D04, E01]
- **industries_instanced**: [hospitalidad, logistica]
- **tenants_in_examples**: [mesonurbano, expreslog]
- **big_corp_vendors**: [Visier, Workday Prism, Eightfold]
- **latam_tools**: [excel, looker-studio]
- **key_concepts**: turnover-voluntario, cohort, leading-indicators, costo-de-reposición
- **estimated_minutes**: 45
- **deterministic_share**: 0.5
- **notes_for_subagent**: |
    Determinístico: tasa por área/antigüedad, costo de reposición estimado,
    cohort analysis.
    Agéntico: identificar leading indicators (caídas de eNPS por área,
    ausentismo, falta de feedback en 1:1), redactar recomendaciones.

#### CX — Servicio al Cliente

##### F-CX-01 — Triage de tickets

- **id**: `F-CX-01`
- **slug**: `triage-tickets`
- **track**: F
- **dept**: CX
- **ord**: 1
- **title**: "Triage automático de tickets (clasificación, prioridad, ruta)"
- **related_modules**: [A06, B02, C03, E01, E03]
- **industries_instanced**: [retail, servicios-fin]
- **tenants_in_examples**: [tiendabox, cooppopular]
- **big_corp_vendors**: [Zendesk AI, ServiceNow, Salesforce Service Cloud]
- **latam_tools**: [freshdesk, helpscout, hubspot-service]
- **key_concepts**: clasificación-multi-label, SLA, routing-rules, escalation
- **estimated_minutes**: 45
- **deterministic_share**: 0.4
- **notes_for_subagent**: |
    Determinístico: routing por reglas duras (cliente VIP → cola premium),
    SLA timers.
    Agéntico: clasificar el ticket por intent + producto + urgencia desde
    texto libre del cliente; detectar tickets que necesitan escalation
    inmediato (lenguaje legal, amenaza pública).

##### F-CX-02 — Resumen + next-action de llamadas

- **id**: `F-CX-02`
- **slug**: `resumen-llamadas-cx`
- **track**: F
- **dept**: CX
- **ord**: 2
- **title**: "Resumen y next-action de llamadas de soporte"
- **related_modules**: [B02, B06, E01, E04]
- **industries_instanced**: [salud, servicios-fin]
- **tenants_in_examples**: [sanrafael, cooppopular]
- **big_corp_vendors**: [Gong, Chorus, Salesforce Einstein Conversation]
- **latam_tools**: [twilio-flex, whatsapp-business]
- **key_concepts**: transcripción, action-items, sentiment, hand-off
- **estimated_minutes**: 45
- **deterministic_share**: 0.3
- **notes_for_subagent**: |
    Determinístico: transcripción con Whisper/STT.
    Agéntico: extraer action items, identificar sentimiento, decidir si
    necesita hand-off a humano (tema sensible: salud, dinero, queja).
    PII: scrubbing antes del modelo (en salud es obligatorio).

##### F-CX-03 — Generación y mantenimiento de KB

- **id**: `F-CX-03`
- **slug**: `kb-mantenimiento`
- **track**: F
- **dept**: CX
- **ord**: 3
- **title**: "Generación y mantenimiento de base de conocimiento"
- **related_modules**: [B02, C01, E01, E03]
- **industries_instanced**: [retail, hospitalidad]
- **tenants_in_examples**: [tiendabox, mesonurbano]
- **big_corp_vendors**: [Zendesk Guide, Confluence, Notion AI]
- **latam_tools**: [notion, confluence-cloud, freshdesk-kb]
- **key_concepts**: gap-detection, deflection-rate, versionado, ownership
- **estimated_minutes**: 45
- **deterministic_share**: 0.4
- **notes_for_subagent**: |
    Determinístico: detección de tickets sobre temas sin KB existente,
    versionado de artículos.
    Agéntico: redactar borrador de artículo desde 3-5 tickets resueltos,
    identificar artículos desactualizados (señales: tasa de tickets sobre
    el tema vuelve a subir).

##### F-CX-04 — Detección de cliente en riesgo

- **id**: `F-CX-04`
- **slug**: `cliente-en-riesgo`
- **track**: F
- **dept**: CX
- **ord**: 4
- **title**: "Detección de cliente en riesgo (CSAT decaying)"
- **related_modules**: [B02, C01, D04, E01]
- **industries_instanced**: [servicios-fin, energia]
- **tenants_in_examples**: [cooppopular, solenergy]
- **big_corp_vendors**: [Gainsight, Totango, ChurnZero]
- **latam_tools**: [hubspot, salesforce-essentials]
- **key_concepts**: health-score, leading-indicators, save-play, ownership
- **estimated_minutes**: 45
- **deterministic_share**: 0.5
- **notes_for_subagent**: |
    Determinístico: health score = uso × frecuencia × CSAT.
    Agéntico: leer notas/correos del CSM, identificar early signals de churn,
    proponer save play apropiada con dueño.

#### LEG — Legal y Compliance

##### F-LEG-01 — Revisión de cláusulas en contratos

- **id**: `F-LEG-01`
- **slug**: `revision-clausulas-contratos`
- **track**: F
- **dept**: LEG
- **ord**: 1
- **title**: "Revisión de cláusulas en contratos contra plantilla aprobada"
- **related_modules**: [A06, B02, E01, E03]
- **industries_instanced**: [construccion, servicios-fin]
- **tenants_in_examples**: [andina, cooppopular]
- **big_corp_vendors**: [Ironclad, LinkSquares, Kira]
- **latam_tools**: [docusign-clm-essentials, drive-shared]
- **key_concepts**: cláusulas-críticas, diff-vs-plantilla, riesgo-score, hand-off
- **estimated_minutes**: 60
- **deterministic_share**: 0.4
- **notes_for_subagent**: |
    Determinístico: extraer cláusulas con sección/heading conocidos, diff
    contra plantilla.
    Agéntico: identificar cláusulas reformuladas pero equivalentes, marcar
    redacciones riesgosas (no aparecen en plantilla pero deberían).
    Regulación: el agente **nunca** firma; solo prepara comentarios para
    abogado.

##### F-LEG-02 — Due diligence preliminar (KYC/AML)

- **id**: `F-LEG-02`
- **slug**: `due-diligence-kyc-aml`
- **track**: F
- **dept**: LEG
- **ord**: 2
- **title**: "Due diligence preliminar (KYC/AML básico)"
- **related_modules**: [B02, C03, D04, E01, E05]
- **industries_instanced**: [servicios-fin, salud]
- **tenants_in_examples**: [cooppopular, sanrafael]
- **big_corp_vendors**: [Refinitiv World-Check, Dow Jones Risk, ComplyAdvantage]
- **latam_tools**: [registro-mercantil-camaras, listas-clinton-onu]
- **key_concepts**: PEP, listas-sanción, match-vs-similitud, expediente
- **estimated_minutes**: 60
- **deterministic_share**: 0.5
- **notes_for_subagent**: |
    Determinístico: match contra listas oficiales, verificación de
    documentos legales.
    Agéntico: clasificar similitud de nombres (Juan Pérez es común; PEP
    Juan Pérez Gómez con país y fecha es match real), redactar el expediente
    con narrativa de hallazgos.
    Regulación dura: AML/KYC. **Toda decisión final humana**.

##### F-LEG-03 — Monitoreo regulatorio sectorial

- **id**: `F-LEG-03`
- **slug**: `monitoreo-regulatorio`
- **track**: F
- **dept**: LEG
- **ord**: 3
- **title**: "Monitoreo regulatorio sectorial (alertas + impacto)"
- **related_modules**: [B02, E01, E05]
- **industries_instanced**: [energia, salud]
- **tenants_in_examples**: [solenergy, sanrafael]
- **big_corp_vendors**: [Thomson Reuters Regulatory, Wolters Kluwer]
- **latam_tools**: [diario-oficial-rss, dian-circulares, supersalud-resoluciones]
- **key_concepts**: ingesta-rss, clasificación-por-impacto, alerta, deadline
- **estimated_minutes**: 45
- **deterministic_share**: 0.3
- **notes_for_subagent**: |
    Determinístico: ingesta RSS/scraping de fuentes oficiales.
    Agéntico: clasificar el impacto (aplica al sector, urgente, informativo),
    extraer deadlines, redactar alerta dirigida al área responsable.

##### F-LEG-04 — Gestión de poderes y vigencias

- **id**: `F-LEG-04`
- **slug**: `poderes-vigencias`
- **track**: F
- **dept**: LEG
- **ord**: 4
- **title**: "Gestión de poderes y vigencias documentales"
- **related_modules**: [B02, C01, E01, E05]
- **industries_instanced**: [construccion, agro]
- **tenants_in_examples**: [andina, cafetera]
- **big_corp_vendors**: [DocuSign, Adobe Sign Enterprise, Ironclad]
- **latam_tools**: [camaras-comercio-rues, registraduria, drive-shared]
- **key_concepts**: vigencia, persona-autorizada, alcance-poder, renovación
- **estimated_minutes**: 30
- **deterministic_share**: 0.6
- **notes_for_subagent**: |
    Determinístico: tracking de fechas, alertas T-30/T-60.
    Agéntico: extraer alcance del poder desde el PDF (qué puede firmar y por
    cuánto), proponer renovación antes del vencimiento.

#### PRD — Producto / Ingeniería

##### F-PRD-01 — Análisis de feedback y priorización

- **id**: `F-PRD-01`
- **slug**: `feedback-priorizacion`
- **track**: F
- **dept**: PRD
- **ord**: 1
- **title**: "Análisis de feedback (tickets, reseñas, NPS) y priorización"
- **related_modules**: [A06, B02, C01, E01]
- **industries_instanced**: [retail, serv-prof]
- **tenants_in_examples**: [tiendabox, consultorabc]
- **big_corp_vendors**: [Productboard, Aha!, Pendo Feedback]
- **latam_tools**: [notion, linear-starter, github-issues]
- **key_concepts**: clustering-temático, RICE, voice-of-customer
- **estimated_minutes**: 45
- **deterministic_share**: 0.4
- **notes_for_subagent**: |
    Determinístico: clustering por palabras clave, agregación por cliente.
    Agéntico: nombrar y describir cada cluster, asignar RICE preliminar,
    detectar duplicados semánticos.

##### F-PRD-02 — Triage de bugs y duplicados

- **id**: `F-PRD-02`
- **slug**: `triage-bugs-duplicados`
- **track**: F
- **dept**: PRD
- **ord**: 2
- **title**: "Triage de bugs y detección de duplicados"
- **related_modules**: [A06, B02, C01, E01]
- **industries_instanced**: [servicios-fin, serv-prof]
- **tenants_in_examples**: [cooppopular, consultorabc]
- **big_corp_vendors**: [Linear AI, Jira AI, GitHub Copilot for PRs]
- **latam_tools**: [linear, github-issues, sentry]
- **key_concepts**: severidad, repro-steps, dedup, owner-suggestion
- **estimated_minutes**: 45
- **deterministic_share**: 0.55
- **notes_for_subagent**: |
    Determinístico: dedup por hash de stack-trace.
    Agéntico: clasificar severidad desde reporte humano (no técnico),
    sugerir owner por componente afectado.

##### F-PRD-03 — Generación de specs desde tickets

- **id**: `F-PRD-03`
- **slug**: `specs-desde-tickets`
- **track**: F
- **dept**: PRD
- **ord**: 3
- **title**: "Generación de specs desde tickets de soporte"
- **related_modules**: [E01, E03]
- **industries_instanced**: [retail, serv-prof]
- **tenants_in_examples**: [tiendabox, consultorabc]
- **big_corp_vendors**: [Productboard AI, Aha! AI, Linear AI]
- **latam_tools**: [notion, linear]
- **key_concepts**: user-story, acceptance-criteria, edge-cases, dependencies
- **estimated_minutes**: 30
- **deterministic_share**: 0.3
- **notes_for_subagent**: |
    Determinístico: agrupación de tickets relacionados.
    Agéntico: redactar borrador de spec con user story + acceptance criteria,
    listar edge cases mencionados en tickets, sugerir dependencias.
    Fallback: el output siempre **borrador**, PM humano lo finaliza.

---

## Matriz módulo técnico → fichas F sugeridas para la sección "caso de uso real"

Cada módulo técnico (sección 8 del esquema de §4 de ARCHITECTURE.md) referencia
≥1 ficha F. Esta tabla guía al Sonnet del módulo.

| Módulo | Fichas F sugeridas | Motivo |
|--------|---------------------|--------|
| A01 | F-CTA-02 | Setup mínimo para correr el skill `monthly_audit`. |
| A02 | F-CTA-01 | Aliasing en clasificación contable (mutar dict por error). |
| A03 | F-FIN-01, F-OPS-02 | Comprensiones sobre transacciones/forecast. |
| A04 | F-CTA-02, F-CMP-03 | Diseñar errores propios (`DuplicateInvoiceError`). |
| A05 | F-CTA-02 | Estructura de paquete = arquitectura del agente. |
| A06 | F-FIN-02, F-OPS-01 | Modelar `CashFlowRow`, `ProductionOrder`. |
| A07 | F-CX-01, F-MKT-04 | I/O concurrente: fetch en paralelo. |
| B01 | F-CX-01 | Triage como endpoint REST. |
| B02 | F-FIN-04, F-CMP-03 | API real para cobranza/OCR. |
| B03 | F-CX-03 | UI server-rendered para KB. |
| B04 | F-CTA-02 | Las 4 capas en el agente de auditoría. |
| B05 | (meta) | El propio editor del curso. |
| B06 | F-CX-02 | Streaming SSE en resumen de llamadas. |
| C01 | F-FIN-01, F-CTA-01 | Modelos ORM para transacciones. |
| C02 | F-CTA-04 | Migración para soportar intercompañía. |
| C03 | F-LEG-02, F-CTA-02 | Multitenancy en KYC y auditoría. |
| D01 | F-OPS-02 | Imagen Docker del forecast worker. |
| D02 | F-FIN-02 | Compose con scheduler para 13W. |
| D03 | F-CTA-02 | Despliegue del agente mensual. |
| D04 | F-LEG-02, F-OPS-02 | Trazas + costo en KYC/forecast. |
| E01 | F-FIN-01, F-CTA-02 | Tool loop sobre conciliación. |
| E02 | F-FIN-01 | Mismo loop como StateGraph. |
| E03 | F-MKT-03, F-RH-01 | Skills con slots por tenant. |
| E04 | F-CX-02 | Memoria de sesión por cliente. |
| E05 | F-CTA-02, F-FIN-02 | Schedule mensual + 13W rolling. |
| E06 | F-CTA-02 (ancla) | Capstone porta el agente. |

---

## Resumen de cambios respecto al site actual y al BLUEPRINT.md

- **Fusionados**: site 01+02 → A02; 05+06 → A06; 03+07 → A04; 13+14 → E03;
  11+12 → D01+D02 (separados de otra forma).
- **Eliminados como módulos sueltos**: módulo 08 (JSON/YAML) — se integra
  como sección de A06 (dataclass) y B02 (Pydantic).
- **Añadidos** (vs site actual): B01 (HTTP), B04 (capas como módulo dedicado,
  no sección), B06 (SSE + chat por dentro), C02 (Alembic dedicado),
  C03 (multitenancy), D04 (observabilidad), E03 (skills con slots).
- **Reordenado**: el track D (operación) viene **antes** de profundizar en
  E (agentes), porque sin Docker corriendo localmente el lector no puede
  probar nada de E2 en adelante.
- **Capstone único**: el BLUEPRINT proponía un capstone tipo "lista" — lo
  consolidamos en E06 (Track E) con criterios duros de "listo".
- **Track F real**: el BLUEPRINT pedía un catálogo de casos de uso y aquí lo
  materializamos como 39 fichas (10 departamentos, 3–4 por dept.) en lugar
  del esquema "30 base + 60 instancias = 90 piezas" que propuso el BLUEPRINT.
  Cada ficha lleva sus instancias-industria adentro (sección 11 según
  SHARED §5.9), no como artefactos separados. Razón: 90 piezas separadas
  cuesta más coordinar y duplica info; 39 con instancias internas escala
  mejor.
- **Renombrado**: E06 vivía mal etiquetado bajo "Track F"; corregido a
  Track E. Track F queda exclusivamente para fichas de caso de uso.

---

## Changelog

| Fecha       | Versión | Cambio |
|-------------|---------|--------|
| 2026-05-16  | 1.0     | Versión Opus arquitecto: 26 módulos técnicos + 39 fichas Track F. |
