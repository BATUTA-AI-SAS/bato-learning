# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`bato-learning` v2 is a **full-stack, runnable** interactive learning app that teaches how to build a production-grade AI agent service for LATAM SMBs. The repo has two related but distinct parts:

- **`app/`** — the learning app itself. FastAPI + SQLAlchemy 2.x async + Alembic + Jinja2 + HTMX + Pyodide. Single-user, runs locally with `make up` (Docker compose). **The app's source code is the example each module references**: when a module on "FastAPI dependency injection" says "see `app/routers/exercises.py`", that file actually exists and is what's being taught.
- **`api/`** — an older technical companion (FastAPI + Temporal + LangGraph workflows). Kept as reference; modules in Track E point into it for real workflow code.

Content lives in `app/content/{TRACK}/` (markdown + yaml). It's authored by a coordinated team of subagents and seeded into SQLite by `app/services/content_loader.py`. Prose is in **Spanish**; code, README, ADRs, this file in **English**.

## Common commands

```bash
make up                            # build + alembic upgrade + seed + serve on :8080
make logs                          # tail app logs
make sh                            # bash inside container
make seed                          # re-seed content after editing app/content/
make reset                         # wipe data/ volume and start over
make fmt                           # ruff --fix
make test                          # pytest inside container

# without Docker:
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed
uv run uvicorn app.main:app --reload --port 8080
```

URLs when running: `http://localhost:8080` (home, `/m/{slug}` module pages, `/progreso`, `/api/progress`, `/api/chat` SSE).

## Architecture you need to read multiple files to grasp

### The learning-loop is the product

Each module page is `/m/{slug}` and renders:

- Module body (markdown rendered server-side via markdown-it-py).
- Exercises (CodeMirror-like textarea + Pyodide runner in browser, or backend subprocess runner via `POST /api/exercises/{id}/backend`).
- Quizzes (HTMX-style click → `POST /api/quizzes/{id}/answer`).
- Chat tutor side-panel (SSE to `POST /api/chat`).

All three persist in SQLite (`exercise_attempt`, `quiz_answer`, `chat_message`). Visiting the page records a `module_visit`. The `/progreso` page summarizes everything.

### Capas (router → service → repo → model)

Strict separation, enforced by convention. `app/routers/pages.py` calls `repos/modules.py` directly because the logic is trivial; complex flows (chat) go through services. Module B06 of the curriculum teaches exactly this layering using these files as the example.

### Content loader

`app/services/content_loader.py` walks `app/content/**/*.md`, parses frontmatter (`ext_id`, `slug`, `track`, `ord`, `title`, optionally `summary`, `estimated_minutes`), reads sibling `*.exercises.yaml` and `*.quizzes.yaml`, computes a content hash, and upserts. It is **tolerant of synonyms**: `id` works as `ext_id`, `question_md` as `question`, `text_md` as `text`, `correct` or `is_correct`. This matters because subagents authoring content sometimes use either set. Don't tighten the loader unless you also normalize all existing yaml.

Each module loads in its own savepoint — a single bad file does not poison the rest.

### Tutor chat (SSE) and prompt caching

`app/services/anthropic_client.py` streams from the SDK and emits a `StreamChunk(done=True, usage=..., cost_usd=...)` at the end. `app/services/context_builder.py` builds the cached system blocks: rules + module body, both with `cache_control={"type":"ephemeral", "ttl":"1h"}`. Dynamic context (recent attempts summary, editor code) goes inside the **user** message, not system, so cache hits stay high. If you change the system block layout, cache hit rate drops to 0 for the next hour — measure with `tokens_cache_read` in the `chat_message` table.

### Async ergonomics

`app/db.py` exposes `SessionDep = Annotated[AsyncSession, Depends(get_session)]`. All routers and services use it. The Pyodide runner is fully in-browser; the **backend** runner (`app/services/exercise_runner.py`) spawns a `python3` subprocess with a 8s timeout for exercises that need real libraries (`runner: backend` in the exercise yaml).

### `_team/` coordination

Three documents produced by the Opus architect coordinate the subagent team:

- `_team/ARCHITECTURE.md` — pedagogical thesis, stack decisions, canonical module shape, chat tutor rules.
- `_team/SHARED.md` — glossary, recurring personas (ACME, Constructora Andina, Clínica San Rafael, Cooperativa Cafetera, Logística Express), code conventions.
- `_team/MODULES.md` — final list of modules and Track F fichas with metadata (prerequisites, goals, app references).
- `_team/MODULES_STATUS.md` — append-only log where each subagent writes "what I left ready" notes.

When writing or editing a module, read those four first. Read **only the grep slice relevant to your IDs** — `MODULES.md` is 1700+ lines.

## Conventions worth respecting

- **Prose in Spanish, code/identifiers in English.** No foo/bar; use the canonical personas from `_team/SHARED.md` §2.
- **Determinístico vs agéntico** is a transversal section of every Track D/E module and the central section of every Track F ficha. Never skip it; it's the central insight of the course.
- Type hints required in new code.
- Module bodies do not duplicate exercises/quizzes — the loader injects them at render time.
- Frontmatter required fields: `ext_id`, `slug`, `track`, `ord`, `title`. Optional: `summary`, `estimated_minutes`.

## Two stacks, on purpose

- The **app** in `app/` uses SQLite. The curriculum **teaches** Postgres + RLS in Track C and the Capstone (E06) requires the lector to migrate the app or a forked agent project to Postgres. Don't migrate the local app to Postgres "to be coherent" — the SQLite simplicity is the didactic point.
- The **companion** in `api/` already runs Temporal + LangGraph + Postgres + Phoenix in `docker-compose.yml`. Modules E03–E05 point into it for real workflow code.
