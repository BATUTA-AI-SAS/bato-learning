# bato-learning

App interactiva de aprendizaje **full-stack para construir un servicio de agentes IA
en producción** — desde Python hasta deploy en Hetzner, pasando por Anthropic SDK,
LangGraph, Temporal, multitenancy con Postgres+RLS y un catálogo de casos de uso
por departamento × industria para PYMES LATAM.

La app **es** el ejemplo de lo que enseña: el código fuente que lees en `app/` es lo
que cada módulo referencia en su sección "Para profundizar".

## Stack

Decisiones canónicas en `_team/ARCHITECTURE.md` y `DECISIONS.md`. Resumen:

- **Backend**: FastAPI · SQLAlchemy 2.x async · Alembic.
- **DB**: SQLite local (un archivo, sin servidor). El curso explica por qué Postgres
  en producción y monta el patrón RLS multitenant en Track C.
- **Frontend**: Jinja2 server-rendered + HTMX 2.x + Tailwind CDN + CodeMirror 6 +
  Pyodide para ejecutar Python en el navegador.
- **Chat tutor**: SSE streaming con Anthropic SDK (`cache_control` con `ttl="1h"`)
  e inyección de contexto: cuerpo del módulo + intentos recientes del lector +
  código del editor en vivo.
- **Infra**: Docker + docker compose, con override de producción para Hetzner.
- **Observabilidad**: structlog en la app; el catálogo cubre Phoenix (OpenInference)
  para los agentes que vivirán fuera de esta app.

## Cómo se levanta (local con Docker Desktop)

```bash
cp .env.example .env       # añade ANTHROPIC_API_KEY (opcional; el chat se desactiva sin clave)
make up                    # build + migrate + seed + servir en :8080
make logs                  # tail de la app
```

Abre `http://localhost:8080`.

Sin Docker, también puedes:

```bash
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed
uv run uvicorn app.main:app --reload --port 8080
```

## Cómo se aprende

Cada módulo del curso tiene:

1. Hilo conductor con el módulo previo.
2. Idea central definida con precisión.
3. Por qué importa, conectado a un caso de uso real.
4. Cómo funciona por dentro (mecanismo, no analogía).
5. Ejemplo conducido en código.
6. 2–4 ejercicios ejecutables con tests automáticos.
7. 2–3 quizzes con feedback explicativo.
8. Tabla "determinístico vs agéntico" — el insight central del oficio.
9. Errores típicos.
10. Para profundizar: link al archivo concreto de esta app.
11. Chat sugerido: 3 prompts pre-armados para el tutor.
12. Salida esperada con verbo accionable.

El **chat tutor** (panel lateral derecho) vive con cada módulo. Le inyectas tu pregunta
y él ve: el cuerpo del módulo, tus últimos intentos y el código de tu editor. Guarda
el historial por módulo en SQLite.

Tu **progreso** se guarda en SQLite (módulos visitados, ejercicios pasados, quizzes
respondidos, tokens y costo del chat). Al apagar y volver a levantar, retomas
exactamente donde quedaste.

## Mapa del curso

| Track | Foco | Módulos |
|-------|------|---------|
| A | Python pragmático | A01–A07 |
| B | Web full-stack (HTTP, FastAPI, SQLAlchemy, Alembic, Jinja+HTMX, capas) | B01–B06 |
| C | Datos y persistencia (Postgres, RLS, backups) | C01–C03 |
| D | Operación (Docker, Compose, Hetzner, observabilidad) | D01–D04 |
| E | Agentes IA (Anthropic SDK, skills/AGENTS.md, LangGraph, equivalencias, Temporal, Capstone) | E01–E06 |
| F | Playbook: casos de uso por departamento × industria | 39 fichas |

El catálogo Track F cubre 10 departamentos operativos (FIN/CTA/CMP/OPS/VTA/MKT/RH/CX/LEG/PRD)
× 5+ industrias (retail, manufactura, servicios financieros, salud, logística, construcción,
hospitalidad, servicios profesionales, agro, energía). Cada ficha clasifica explícitamente
los tramos **determinísticos** (parse, ETL, reglas duras) vs **agénticos** (razonamiento
contextual) — el insight central de BATUTA.

## Estructura del repo

```
bato-learning/
├── app/                            # la app de aprendizaje (lo que estamos enseñando)
│   ├── main.py                     # FastAPI entry
│   ├── settings.py                 # pydantic-settings
│   ├── db.py                       # SQLAlchemy async engine + session dep
│   ├── logging_setup.py            # structlog
│   ├── templating.py               # Jinja2 con filtros markdown
│   ├── models/                     # ORM: User, Module, Exercise, Quiz, ChatSession, ...
│   ├── repos/                      # consultas SQLAlchemy
│   ├── services/                   # content_loader, exercise_runner, anthropic_client, context_builder
│   ├── routers/                    # pages, exercises, quizzes, chat (SSE), progress, health
│   ├── templates/                  # Jinja2: _layout, index, module, progress, partials/
│   ├── static/                     # CSS + JS (vanilla): pyodide_runner, chat (SSE), app
│   └── content/                    # el currículum: A/, B/, C/, D/, E/, F/
├── alembic/                        # migraciones
│   ├── env.py
│   └── versions/
├── scripts/seed.py                 # bootstrap user + load content
├── _team/                          # outputs del Opus arquitecto y notas del agents team
│   ├── ARCHITECTURE.md
│   ├── SHARED.md
│   ├── MODULES.md
│   └── MODULES_STATUS.md           # bitácora del agents team
├── api/                            # backend de referencia técnica (Temporal + LangGraph reales)
├── infra/                          # Traefik, Hetzner prod, etc.
├── compose.yaml                    # docker compose principal (app + volumen SQLite)
├── docker-compose.yml              # compose alternativo para el stack de referencia api/
├── Dockerfile                      # imagen de la app de aprendizaje
├── Makefile                        # up / down / logs / sh / seed / reset / fmt / test
├── pyproject.toml
├── alembic.ini
├── BLUEPRINT.md                    # propuesta inicial (auditada por Opus → ARCHITECTURE.md)
├── DECISIONS.md                    # ADR cortos
└── CLAUDE.md                       # guía para futuros agentes Claude Code
```

## Cómo añadir o editar un módulo

El contenido vive en `app/content/{TRACK}/{EXT_ID}.{md,exercises.yaml,quizzes.yaml}`.
Lee `app/content/_HOWTO.md` para el formato exacto. El loader es tolerante con
sinónimos comunes (`question` o `question_md`, `text` o `text_md`, `id` o `ext_id`)
porque distintos agentes escribieron con convenciones diferentes y se normalizan
al cargar.

Tras editar:

```bash
make seed         # re-siembra DB sin perder progreso
```

El loader hashea cada módulo y solo re-seedea lo que cambió.

## Deploy a Hetzner

Track D03 del curso es la guía paso a paso. Resumen:

1. `hcloud server create --type cx22 ...`
2. DNS A record a la IP.
3. SSH + `git pull` + `docker compose -f compose.yaml -f infra/hetzner/compose.prod.yml up -d`.
4. Traefik se encarga del TLS automático con Let's Encrypt.
5. Backups SQLite vía `make backup` (a Hetzner Storage Box).

## Para futuros agentes Claude Code

Ver `CLAUDE.md`.
