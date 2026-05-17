# GAME_DESIGN.md — the platform IS the game

`learning.batutaai.com` is not a learning site with games inside; it is a **guided learning game** whose primary surface is gameplay. Plain text is opt-in lore.

Single source of truth for all subagents authoring backend, UI, content, tutor, deploy.

---

## 1. Pillars (binding rules)

1. **Game-first.** Default surface is the level player. Reading is unlocked lore, never a prerequisite.
2. **Tomb Raider arc.** 15 numbered chapters, each set in a metaphoric "site" (la oficina, el almacén, el banco, la planta, el laboratorio, el centro de datos…). Each chapter has its own visual palette and journal pages.
3. **Minecraft/Roblox mechanics.** Recipes ("para construir un agente que envía alertas necesitas: variables + diccionario + función + tool_use + cron") and trade-offs ("SQLite vs Postgres — escoge"). The player crafts; consequences ripple.
4. **Socratic tutor.** The DeepSeek helper never returns full code. It asks one question per turn, references the journal page where the concept lives, and waits.
5. **Reinforcement over content.** A skill is "learned" only after the player solves N levels using it without hints. Tracked in `skill_mastery`.
6. **No PII, no hardcoded tenant.** All scenarios use the canonical fictional companies from `_team/SHARED.md`.

---

## 2. Narrative arc — 15 chapters

| # | Chapter (Spanish) | Setting (Tomb Raider–like) | Core skills | Boss (mini-project) |
|---|---|---|---|---|
| 1 | El despertar — pensar en pasos | despacho con planos | secuenciar acciones | Ordena el ritual de cierre del día contable |
| 2 | El umbral — decidir si/no | puerta con código | condicionales | Filtra facturas marcadas para revisión |
| 3 | El eco — repetir sin cansarse | sala de espejos | bucles | Cuenta visitantes por hora |
| 4 | Los nombres de las cosas — variables | biblioteca olvidada | naming / scope | Etiqueta el inventario del laboratorio |
| 5 | El cofre — listas y diccionarios | bóveda con artefactos | colecciones | Cataloga los hallazgos del expedicionario |
| 6 | El cazador — filtrar y contar | río con peces | filter/count | Detecta gastos anómalos en el extracto |
| 7 | El alquimista — transformar | taller de pociones | map / convert | Convierte monedas históricas a EUR |
| 8 | El estratega — reglas compuestas | sala de mando | if-and-or-not encadenado | Política de descuentos por cliente |
| 9 | El escriba — texto y formatos | scriptorium | strings / fechas / dinero | Genera reporte mensual en plantilla |
| 10 | El arquitecto — funciones | obrador medieval | encapsular procesos | Construye un módulo `audit.py` |
| 11 | El guardián — errores | torre con trampas | try/except, validación | Manejar facturas corruptas |
| 12 | El archivero — archivos | biblioteca subterránea | leer/escribir CSV/JSON | Ingiere extracto bancario |
| 13 | El oráculo — determinístico vs agéntico | templo brumoso | cuándo regla, cuándo IA | Diseña la separación de un flujo |
| 14 | El mensajero — APIs | aeropuerto antiguo | HTTP, JSON, retries | Llama a la API de Slack |
| 15 | La ciudad — despliegue | metrópolis al amanecer | Docker, Coolify, dominios | Despliega tu agente |

Each chapter:
- **10 levels** (the existing 15 worlds × 10 mapping in `_team/ARENA_DESIGN.md` is reused 1:1, renamed to chapters).
- **1 boss room** = a mini-project assembled from unlocked recipes.
- **1 recipe** unlocked at chapter end (e.g., "Receta: filtrar+contar = `[x for x in xs if cond]`").
- **1 decision room** at chapter end (a tradeoff that affects the next chapter's variant).

Total static content: 15 × (10 levels + 1 boss + 1 recipe + 1 decision) = **195 puzzle entries + 15 recipes + 15 decisions**. Plus 127 lore drops (the existing modules reframed).

---

## 3. Data model (migration 0005)

### Tables (all FK to existing `user` table from migration 0004)

```sql
chapter(
  id, slug, ord, code (CHA01..CHA15), title, setting, palette_hex,
  intro_md, outro_md, theme, est_minutes
)

game_level(
  id, chapter_id FK, ord, slug, title,
  kind ENUM('order_steps','multi_choice','predict','fill_blank','tf','code','boss'),
  scenario_md, payload_json, hint_md, solution_md,
  xp INT DEFAULT 10, est_seconds INT DEFAULT 90,
  requires_skill VARCHAR(60) NULL,  -- skill check before allowing level
  trains_skill VARCHAR(60) NOT NULL -- the skill reinforced
)

recipe(
  id, chapter_id FK, slug, title, body_md,
  ingredients_json,  -- ["variable","loop","filter"] (skill slugs)
  yields_md          -- "Un script que…"
)

decision(
  id, chapter_id FK, slug, prompt_md,
  options_json       -- [{label, tradeoff_md, consequence_skill}, …]
)

lore_drop(
  id, slug, module_ref VARCHAR(60), title, summary_md,
  body_md (rendered from existing module), unlock_after_level_slug,
  reading_minutes INT
)

user_progress(
  user_id PK FK, chapter_id PK FK, levels_passed INT DEFAULT 0,
  best_streak INT DEFAULT 0, completed_at TIMESTAMP NULL
)

level_attempt(
  id, user_id FK, level_id FK, started_at, completed_at,
  passed BOOL, hint_used BOOL, attempt_count INT,
  payload_json,        -- what the user submitted
  duration_seconds
)

skill_mastery(
  user_id PK FK, skill VARCHAR(60) PK,
  level_count INT DEFAULT 0,         -- levels solved with this skill
  unaided_count INT DEFAULT 0,       -- solved without hint
  first_passed_at TIMESTAMP, last_passed_at TIMESTAMP
)

decision_choice(
  id, user_id FK, decision_id FK, option_index INT,
  chosen_at TIMESTAMP
)

lore_unlock(
  user_id PK FK, lore_drop_id PK FK, unlocked_at TIMESTAMP,
  read_at TIMESTAMP NULL
)
```

### Unlock rules

- Chapter N unlocks when ≥7/10 levels of chapter N-1 are passed.
- Boss room unlocks when 10/10 of the chapter's levels are passed.
- Each lore drop unlocks via `unlock_after_level_slug`.
- Decision room appears after the boss is solved.

---

## 4. Puzzle kinds (binding spec)

All level YAML files live in `app/content/_game/CHA{NN}/<level_slug>.yaml`. The loader walks the tree and upserts.

### kind = `order_steps`
```yaml
slug: cierre-contable-pasos
title: "Ritual de cierre del día"
kind: order_steps
trains_skill: secuenciar
scenario_md: |
  Al cerrar el día contable la oficina hace cuatro cosas. Si el orden se rompe,
  el balance no cuadra. Ordena los pasos.
payload:
  steps:
    - "Confirmar que el total de ventas coincide con el POS"
    - "Generar el reporte diario en PDF"
    - "Imprimir el resumen y guardarlo en la carpeta del día"
    - "Recibir el ticket de venta del cajero"
  correct_order: [3, 0, 1, 2]
hint_md: "¿Qué pasa antes de poder confirmar un total?"
solution_md: "Primero llega el ticket. Sin dato no hay confirmación."
xp: 10
```

### kind = `multi_choice`
```yaml
payload:
  options:
    - text: "Sumar todo, luego filtrar"
      correct: false
      feedback: "Operas sobre datos que vas a descartar."
    - text: "Filtrar primero, luego sumar"
      correct: true
      feedback: "Estrechas el universo, después calculas."
```

### kind = `predict`
```yaml
payload:
  code: |
    total = 1500 * 0.21
    print(f"IVA: {total}")
  expected_output: "IVA: 315.0"
```

### kind = `fill_blank`
```yaml
payload:
  code_template: |
    iva = base * ___
  blanks:
    - {label: "tasa", correct: ["0.21", "21/100"]}
```

### kind = `tf`
```yaml
payload:
  statement: "Una factura sin IVA no necesita revisión."
  correct: false
  bonus_window_ms: 5000
```

### kind = `code` (Pyodide)
```yaml
payload:
  starter: |
    def is_high_value(amount: float) -> bool:
        ...
  tests: |
    assert is_high_value(1500) is True
    assert is_high_value(50) is False
```

### kind = `boss` (compound)
```yaml
payload:
  steps:                # sub-puzzles in order; player must clear all
    - {kind: order_steps, ...}
    - {kind: multi_choice, ...}
    - {kind: code, ...}
```

---

## 5. Recipes (Minecraft-style)

```yaml
slug: filtrar-y-contar
title: "Receta: filtrar y contar"
chapter_ref: CHA06
ingredients:
  - variable
  - list
  - condicion
yields_md: |
  Una expresión que te dice "cuántos hay que cumplen la condición":
  `len([x for x in xs if x > 100])`
unlocked_by_level: contar-altos
```

Recipes appear in a "Libro de recetas" tab. They render with their `yields_md` *and* a sandbox "Probar esta receta" button that opens a Pyodide editor pre-seeded with the expression and a dataset.

---

## 6. Decision rooms (tradeoffs)

```yaml
slug: sqlite-vs-postgres
chapter_ref: CHA12
prompt_md: |
  Tu jefe quiere persistir los reportes generados. Tienes dos opciones reales:
options:
  - label: "SQLite local (un archivo)"
    tradeoff_md: |
      + Cero infraestructura. + Cabe en backup zip.
      − No multiusuario. − No vive bien en contenedores con réplicas.
    consequence_skill: persistencia-archivo
  - label: "Postgres en Coolify"
    tradeoff_md: |
      + Multiusuario. + Pruebas reales de migraciones.
      − Un servicio extra que mantener.
    consequence_skill: persistencia-servidor
```

The player's choice rewards `consequence_skill` and may surface or hide future levels.

---

## 7. Tutor — Socratic rewrite (mandatory)

The DeepSeek tutor's `TUTOR_RULES` block (`app/services/context_builder.py`) is replaced with:

```
Eres el mentor del juego learning.batutaai.com. El jugador está atrapado en un
nivel y te pidió ayuda. Tu rol es enseñar, NUNCA resolver.

Reglas duras:
- NO escribas la solución. NUNCA. Si la respuesta correcta es código, no lo
  escribas, ni completo ni parcial, ni en bloque, ni en línea.
- Una pregunta socrática por turno. Una sola.
- La pregunta debe partir de lo que el jugador escribió (su intento), no de la
  consigna ideal. Si no hay intento, pregunta primero "¿qué crees que hace
  falta antes que nada?".
- Si necesitas referenciar un concepto: nombra la página del diario donde vive
  ("revisa la página *El umbral* sobre condiciones"), no expliques el concepto
  en chat.
- Si el jugador pega código y pregunta "¿está bien?", responde con UNA pregunta
  diagnóstica ("¿qué pasa si `amount` es exactamente 1000?"), no con corrección.
- Si el jugador pide la respuesta directamente, responde: "te quemarías el
  músculo que vinimos a entrenar; dime qué intentaste hasta ahora".
- Máximo 3 oraciones por respuesta.
- Habla en español.

Estás prohibido de:
- Pegar bloques ```` ``` ```` con la solución.
- Escribir `def`, `for`, `if` seguido de su cuerpo completo.
- Dar más de una pista útil por turno.
```

### Output filter

A post-processing function in `app/services/tutor_filter.py`:
- Detects code fences containing executable answers; trims them.
- If the model emits a full `def name(...):` body, replace with an inline note "(omitido por el mentor)".

---

## 8. UI surface (replace, not augment)

- `/` becomes the **game home**: avatar + skill tree + current chapter card + "continuar" CTA.
- `/game/{chapter_slug}` = the chapter map (Tomb Raider tile-map vibe).
- `/game/{chapter}/{level_slug}` = the level player.
- `/journal` = diario unlocked lore + recipes + decision history.
- `/lore/{slug}` = a specific lore drop (the old `/m/{slug}` is aliased here).
- `/skills` = skill tree heatmap.
- `/login`, `/register` already exist (Sonnet B).

The old `/m/{slug}` paths still work but are reframed as lore. Nav top-level: `Jugar · Diario · Habilidades · Salir`. The flat course nav goes away from the default surface.

### Tomb-Raider styling cues
- Each chapter has a hex palette in DB (`palette_hex`).
- Chapter map uses an ornate parchment background (CSS only, no images), tinted with the palette.
- Level cards look like waxed-paper notes.
- Journal pages use a serif font (`Cormorant Garamond` via Google Fonts) with marginalia for the dynamic player notes.
- Player avatar: a circular monogram of their `display_name[0]` over a colored gradient.

The frontend-design Skill is used to render mockups for: chapter map, level player, journal page, recipe card, decision modal.

---

## 9. Implementation plan & Sonnet fan-out

Phases:

1. **Phase A — schema & loader** (1 Sonnet, blocks the rest).
2. **Phase B — backend routers & repos** (1 Sonnet).
3. **Phase C — tutor rewrite + filter** (1 Sonnet, independent).
4. **Phase D — UI mockups via frontend-design** (skill invocation by parent).
5. **Phase E — UI implementation** (1–2 Sonnets).
6. **Phase F — content authoring** (15 Sonnets in waves of 5).
7. **Phase G — lore reframe** (1 Sonnet, scripted).
8. **Phase H — deploy** (parent + Coolify API).

Phases A, B, C can start in parallel after this doc lands. D unblocks E. F can start as soon as A is done (yaml is independent of backend code).

---

## 10. Acceptance criteria (binding)

- A new visitor lands at `/`, registers, sees chapter 1, and solves level 1 without ever reading prose.
- Tutor in any level can be prompted "dame la solución" and refuses with a Socratic redirect.
- Boss of chapter 1 is solvable without unlocking lore.
- 15 chapter records, ≥150 level records, ≥15 recipes, ≥15 decisions in DB after seeding.
- All routes 200 (logged in or not where applicable).
- DB migrates from 0004 → 0005 cleanly. SQLite, same volume mount.
- Deployed at `https://learning.batutaai.com` via Coolify with `SESSION_SECRET_KEY`, `DEEPSEEK_API_KEY` injected, persistent volume for the SQLite file.

Done means all of the above. The auth/tutor/UI/content/deploy threads must converge here.
