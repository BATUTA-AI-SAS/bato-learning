"""Load game content from app/content/_game/ into the DB.

Filesystem layout:

    app/content/_game/
      phase1/                      # Phase directories (phaseN or legacy CHA*)
        _phase.yaml                # Optional phase metadata
        L01-terminal.yaml          # Level files (any *.yaml not starting with _)
        L02-variables.yaml
        ...
      phase2/
        ...
      _concepts/                   # Global concept popup files
        terminal.yaml
        variable.yaml
        ...
      _recipes/                    # Global recipe files (chapter_ref for association)
        validacion-datos.yaml
        ...
      _decisions/                  # Global decision files (chapter_ref for association)
        sqlite-vs-postgres.yaml
        ...

Each level YAML requires: slug, title, kind, trains_skill, scenario_md, payload.
Optional: hint_md, solution_md, xp, est_seconds, requires_skill, ord,
          concepts_introduced, concepts_reinforced.

_phase.yaml optional fields: slug, code, ord, title, setting, palette_hex,
intro_md, outro_md, theme, est_minutes. If absent, derived from directory name
(phase1 → ord=1, slug=phase-1, code=CHA01, etc.).

_concepts/*.yaml: slug, title, analogy_md, example_md.

_recipes/*.yaml: slug, title, body_md, ingredients (list), yields_md.
  chapter_ref: phase1  — links to the matching chapter slug or phase dir name.

_decisions/*.yaml: slug, prompt_md, options (list of {label, tradeoff_md, consequence_skill}).
  chapter_ref: phase1

Content hashes are computed per entity for idempotency (skip if unchanged).
Each chapter loads in its own savepoint so one bad chapter won't poison the rest.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import structlog
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.game import Chapter, ConceptPopup, Decision, GameLevel, Recipe

log = structlog.get_logger(__name__)

_PHASE_DIR_RE = re.compile(r"^phase(\d+)$", re.IGNORECASE)
_LEGACY_CHA_RE = re.compile(r"^CHA(\d{2})$", re.IGNORECASE)

GAME_CONTENT_SUBDIR = "_game"


# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------

def _hash_bytes(*parts: bytes) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.hexdigest()[:32]


def _hash_yaml(data: object) -> str:
    return _hash_bytes(json.dumps(data, sort_keys=True, default=str).encode())


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def _pick(d: dict, *keys: str, default: str = "") -> str:
    for k in keys:
        if k in d and d[k] is not None:
            return str(d[k])
    return default


# ---------------------------------------------------------------------------
# Directory → phase metadata derivation
# ---------------------------------------------------------------------------

def _phase_num_from_dir(dir_name: str) -> int | None:
    """Return numeric phase number or None if not a phase directory."""
    m = _PHASE_DIR_RE.match(dir_name)
    if m:
        return int(m.group(1))
    m = _LEGACY_CHA_RE.match(dir_name)
    if m:
        return int(m.group(1))
    return None


def _chapter_code_from_num(num: int) -> str:
    return f"CHA{num:02d}"


def _is_phase_dir(d: Path) -> bool:
    return d.is_dir() and _phase_num_from_dir(d.name) is not None


# ---------------------------------------------------------------------------
# Chapter / phase
# ---------------------------------------------------------------------------

async def _upsert_chapter(session: AsyncSession, phase_dir: Path) -> Chapter:
    dir_name = phase_dir.name
    phase_num = _phase_num_from_dir(dir_name)
    assert phase_num is not None  # caller guarantees this

    # Try both _phase.yaml and legacy _chapter.yaml
    meta_path = phase_dir / "_phase.yaml"
    if not meta_path.exists():
        meta_path = phase_dir / "_chapter.yaml"
    meta: dict = _load_yaml(meta_path) if meta_path.exists() else {}

    code = str(meta.get("code") or _chapter_code_from_num(phase_num))
    slug = str(meta.get("slug") or f"phase-{phase_num}")
    ord_ = int(meta.get("ord") or phase_num)
    title = str(meta.get("title") or dir_name)

    content_hash = _hash_bytes(
        (meta_path.read_bytes() if meta_path.exists() else b""),
        code.encode(),
    )

    res = await session.execute(select(Chapter).where(Chapter.code == code))
    chapter = res.scalar_one_or_none()

    if chapter is None:
        chapter = Chapter(code=code, slug=slug, ord=ord_, title=title)
        session.add(chapter)

    chapter.slug = slug
    chapter.ord = ord_
    chapter.title = title
    chapter.setting = _pick(meta, "setting")
    chapter.palette_hex = str(meta.get("palette_hex") or "#888888")
    chapter.intro_md = _pick(meta, "intro_md")
    chapter.outro_md = _pick(meta, "outro_md")
    chapter.theme = _pick(meta, "theme")
    chapter.est_minutes = int(meta.get("est_minutes") or 30)
    chapter.content_hash = content_hash

    await session.flush()
    return chapter


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------

async def _upsert_levels(
    session: AsyncSession, chapter: Chapter, phase_dir: Path
) -> int:
    count = 0
    level_files = sorted(
        p for p in phase_dir.glob("*.yaml")
        if not p.name.startswith("_")
    )
    for alphabetical_ord, path in enumerate(level_files, start=1):
        try:
            data = _load_yaml(path)
            if not data:
                continue
            slug = str(data.get("slug") or path.stem)
            content_hash = _hash_bytes(path.read_bytes())

            res = await session.execute(select(GameLevel).where(GameLevel.slug == slug))
            level = res.scalar_one_or_none()

            if level is None:
                level = GameLevel(
                    slug=slug,
                    chapter_id=chapter.id,
                    ord=int(data.get("ord") or alphabetical_ord),
                    title=str(data.get("title") or slug),
                    kind=str(data.get("kind") or "multi_choice"),
                    trains_skill=str(data.get("trains_skill") or ""),
                )
                session.add(level)
            elif level.content_hash == content_hash:
                count += 1
                continue

            level.chapter_id = chapter.id
            level.ord = int(data.get("ord") or alphabetical_ord)
            level.title = str(data.get("title") or slug)
            level.kind = str(data.get("kind") or "multi_choice")
            level.scenario_md = _pick(data, "scenario_md", "scenario")
            level.hint_md = _pick(data, "hint_md", "hint")
            level.solution_md = _pick(data, "solution_md", "solution")
            level.xp = int(data.get("xp") or 10)
            level.est_seconds = int(data.get("est_seconds") or 90)
            level.requires_skill = data.get("requires_skill") or None
            level.trains_skill = str(data.get("trains_skill") or "")
            level.content_hash = content_hash

            payload = data.get("payload") or {}
            level._payload_json = json.dumps(payload if isinstance(payload, dict) else {})

            concepts_in = data.get("concepts_introduced") or []
            level._concepts_introduced_json = json.dumps(
                concepts_in if isinstance(concepts_in, list) else []
            )
            concepts_re = data.get("concepts_reinforced") or []
            level._concepts_reinforced_json = json.dumps(
                concepts_re if isinstance(concepts_re, list) else []
            )

            await session.flush()
            count += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("game.level_load_failed", path=str(path), error=str(exc))
    return count


# ---------------------------------------------------------------------------
# Concept popups (global _concepts/ directory)
# ---------------------------------------------------------------------------

async def _upsert_concepts(session: AsyncSession, game_dir: Path) -> int:
    concepts_dir = game_dir / "_concepts"
    if not concepts_dir.exists():
        return 0
    count = 0
    for path in sorted(concepts_dir.glob("*.yaml")):
        try:
            data = _load_yaml(path)
            if not data:
                continue
            slug = str(data.get("slug") or path.stem)
            content_hash = _hash_bytes(path.read_bytes())

            res = await session.execute(
                select(ConceptPopup).where(ConceptPopup.slug == slug)
            )
            concept = res.scalar_one_or_none()

            if concept is not None and concept.content_hash == content_hash:
                count += 1
                continue

            if concept is None:
                concept = ConceptPopup(slug=slug, title=str(data.get("title") or slug))
                session.add(concept)

            concept.title = str(data.get("title") or slug)
            concept.analogy_md = _pick(data, "analogy_md", "analogy")
            concept.example_md = _pick(data, "example_md", "example")
            concept.content_hash = content_hash

            await session.flush()
            count += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("game.concept_load_failed", path=str(path), error=str(exc))
    return count


# ---------------------------------------------------------------------------
# Recipes — per-chapter dir OR global _recipes/ with chapter_ref
# ---------------------------------------------------------------------------

async def _resolve_chapter_ref(
    session: AsyncSession,
    game_dir: Path,
    chapter_ref: str,
    chapter_dirs_by_dirname: dict[str, Chapter],
) -> Chapter | None:
    """Resolve a chapter_ref string to a Chapter row.

    Accepts: dir name (phase1), slug (phase-1), or code (CHA01).
    """
    if not chapter_ref:
        return None
    # By directory name
    if chapter_ref in chapter_dirs_by_dirname:
        return chapter_dirs_by_dirname[chapter_ref]
    # By slug
    res = await session.execute(select(Chapter).where(Chapter.slug == chapter_ref))
    ch = res.scalar_one_or_none()
    if ch:
        return ch
    # By code
    res = await session.execute(select(Chapter).where(Chapter.code == chapter_ref.upper()))
    return res.scalar_one_or_none()


async def _upsert_recipes_from_dir(
    session: AsyncSession,
    chapter: Chapter,
    recipes_dir: Path,
) -> int:
    if not recipes_dir.exists():
        return 0
    count = 0
    for path in sorted(recipes_dir.glob("*.yaml")):
        try:
            data = _load_yaml(path)
            if not data:
                continue
            slug = str(data.get("slug") or path.stem)
            content_hash = _hash_bytes(path.read_bytes())

            res = await session.execute(select(Recipe).where(Recipe.slug == slug))
            recipe = res.scalar_one_or_none()

            if recipe is not None and recipe.content_hash == content_hash:
                count += 1
                continue

            if recipe is None:
                recipe = Recipe(
                    slug=slug,
                    chapter_id=chapter.id,
                    title=str(data.get("title") or slug),
                )
                session.add(recipe)

            recipe.chapter_id = chapter.id
            recipe.title = str(data.get("title") or slug)
            recipe.body_md = _pick(data, "body_md", "body")
            recipe.yields_md = _pick(data, "yields_md", "yields")
            recipe.content_hash = content_hash

            ingredients = data.get("ingredients") or []
            recipe._ingredients_json = json.dumps(
                ingredients if isinstance(ingredients, list) else []
            )

            await session.flush()
            count += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("game.recipe_load_failed", path=str(path), error=str(exc))
    return count


async def _upsert_global_recipes(
    session: AsyncSession,
    game_dir: Path,
    chapter_dirs_by_dirname: dict[str, Chapter],
    fallback_chapter: Chapter | None,
) -> int:
    recipes_dir = game_dir / "_recipes"
    if not recipes_dir.exists():
        return 0
    count = 0
    for path in sorted(recipes_dir.glob("*.yaml")):
        try:
            data = _load_yaml(path)
            if not data:
                continue
            chapter_ref = str(data.get("chapter_ref") or "")
            chapter = await _resolve_chapter_ref(
                session, game_dir, chapter_ref, chapter_dirs_by_dirname
            ) or fallback_chapter
            if chapter is None:
                log.warning("game.recipe_no_chapter", path=str(path), chapter_ref=chapter_ref)
                continue
            slug = str(data.get("slug") or path.stem)
            content_hash = _hash_bytes(path.read_bytes())

            res = await session.execute(select(Recipe).where(Recipe.slug == slug))
            recipe = res.scalar_one_or_none()

            if recipe is not None and recipe.content_hash == content_hash:
                count += 1
                continue

            if recipe is None:
                recipe = Recipe(
                    slug=slug,
                    chapter_id=chapter.id,
                    title=str(data.get("title") or slug),
                )
                session.add(recipe)

            recipe.chapter_id = chapter.id
            recipe.title = str(data.get("title") or slug)
            recipe.body_md = _pick(data, "body_md", "body")
            recipe.yields_md = _pick(data, "yields_md", "yields")
            recipe.content_hash = content_hash

            ingredients = data.get("ingredients") or []
            recipe._ingredients_json = json.dumps(
                ingredients if isinstance(ingredients, list) else []
            )

            await session.flush()
            count += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("game.recipe_load_failed", path=str(path), error=str(exc))
    return count


# ---------------------------------------------------------------------------
# Decisions — per-chapter dir OR global _decisions/ with chapter_ref
# ---------------------------------------------------------------------------

async def _upsert_decisions_from_dir(
    session: AsyncSession,
    chapter: Chapter,
    decisions_dir: Path,
) -> int:
    if not decisions_dir.exists():
        return 0
    count = 0
    for path in sorted(decisions_dir.glob("*.yaml")):
        try:
            data = _load_yaml(path)
            if not data:
                continue
            slug = str(data.get("slug") or path.stem)
            content_hash = _hash_bytes(path.read_bytes())

            res = await session.execute(select(Decision).where(Decision.slug == slug))
            decision = res.scalar_one_or_none()

            if decision is not None and decision.content_hash == content_hash:
                count += 1
                continue

            if decision is None:
                decision = Decision(slug=slug, chapter_id=chapter.id)
                session.add(decision)

            decision.chapter_id = chapter.id
            decision.prompt_md = _pick(data, "prompt_md", "prompt")
            decision.content_hash = content_hash

            options = data.get("options") or []
            decision._options_json = json.dumps(
                options if isinstance(options, list) else []
            )

            await session.flush()
            count += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("game.decision_load_failed", path=str(path), error=str(exc))
    return count


async def _upsert_global_decisions(
    session: AsyncSession,
    game_dir: Path,
    chapter_dirs_by_dirname: dict[str, Chapter],
    fallback_chapter: Chapter | None,
) -> int:
    decisions_dir = game_dir / "_decisions"
    if not decisions_dir.exists():
        return 0
    count = 0
    for path in sorted(decisions_dir.glob("*.yaml")):
        try:
            data = _load_yaml(path)
            if not data:
                continue
            chapter_ref = str(data.get("chapter_ref") or "")
            chapter = await _resolve_chapter_ref(
                session, game_dir, chapter_ref, chapter_dirs_by_dirname
            ) or fallback_chapter
            if chapter is None:
                log.warning(
                    "game.decision_no_chapter", path=str(path), chapter_ref=chapter_ref
                )
                continue
            slug = str(data.get("slug") or path.stem)
            content_hash = _hash_bytes(path.read_bytes())

            res = await session.execute(select(Decision).where(Decision.slug == slug))
            decision = res.scalar_one_or_none()

            if decision is not None and decision.content_hash == content_hash:
                count += 1
                continue

            if decision is None:
                decision = Decision(slug=slug, chapter_id=chapter.id)
                session.add(decision)

            decision.chapter_id = chapter.id
            decision.prompt_md = _pick(data, "prompt_md", "prompt")
            decision.content_hash = content_hash

            options = data.get("options") or []
            decision._options_json = json.dumps(
                options if isinstance(options, list) else []
            )

            await session.flush()
            count += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("game.decision_load_failed", path=str(path), error=str(exc))
    return count


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

async def load_game_content(
    session: AsyncSession,
    base_dir: Path = Path("app/content/_game"),
) -> dict[str, int]:
    """Walk _game/ directory and upsert all game content.

    Handles phase1/, phase2/, ... directories as well as legacy CHA01/ naming.
    Global _concepts/, _recipes/, and _decisions/ directories are also processed;
    recipes and decisions use a chapter_ref field for association.

    Returns: {"chapters": N, "levels": N, "concepts": N, "recipes": N, "decisions": N}
    """
    game_dir = base_dir
    # If a relative path was given, resolve it from cwd
    if not game_dir.is_absolute():
        game_dir = Path.cwd() / game_dir

    if not game_dir.exists():
        log.info("game.content_dir.missing", path=str(game_dir))
        return {"chapters": 0, "levels": 0, "concepts": 0, "recipes": 0, "decisions": 0}

    totals: dict[str, int] = {
        "chapters": 0,
        "levels": 0,
        "concepts": 0,
        "recipes": 0,
        "decisions": 0,
    }

    # Build chapter map: dir_name → Chapter (populated as we upsert)
    chapter_dirs_by_dirname: dict[str, Chapter] = {}

    phase_dirs = sorted(
        d for d in game_dir.iterdir()
        if _is_phase_dir(d)
    )

    # First pass: upsert all chapters + their embedded content
    for phase_dir in phase_dirs:
        try:
            async with session.begin_nested():
                chapter = await _upsert_chapter(session, phase_dir)
                chapter_dirs_by_dirname[phase_dir.name] = chapter

                level_count = await _upsert_levels(session, chapter, phase_dir)

                # Per-phase embedded _recipes/ and _decisions/ dirs
                recipe_count = await _upsert_recipes_from_dir(
                    session, chapter, phase_dir / "_recipes"
                )
                decision_count = await _upsert_decisions_from_dir(
                    session, chapter, phase_dir / "_decisions"
                )

            totals["chapters"] += 1
            totals["levels"] += level_count
            totals["recipes"] += recipe_count
            totals["decisions"] += decision_count

        except Exception as exc:  # noqa: BLE001
            log.error(
                "game.phase_load_failed",
                phase_dir=str(phase_dir),
                error=str(exc),
            )
            try:
                await session.rollback()
            except Exception:  # noqa: BLE001
                pass

    # Determine a fallback chapter for global assets without chapter_ref
    fallback_chapter: Chapter | None = None
    if chapter_dirs_by_dirname:
        # Use the first (lowest ord) chapter as fallback
        first_key = sorted(
            chapter_dirs_by_dirname,
            key=lambda k: chapter_dirs_by_dirname[k].ord,
        )[0]
        fallback_chapter = chapter_dirs_by_dirname[first_key]

    # Global _concepts/
    try:
        async with session.begin_nested():
            concept_count = await _upsert_concepts(session, game_dir)
        totals["concepts"] += concept_count
    except Exception as exc:  # noqa: BLE001
        log.error("game.concepts_load_failed", error=str(exc))
        try:
            await session.rollback()
        except Exception:  # noqa: BLE001
            pass

    # Global _recipes/ (only if fallback_chapter exists to assign orphaned entries)
    try:
        async with session.begin_nested():
            recipe_count = await _upsert_global_recipes(
                session, game_dir, chapter_dirs_by_dirname, fallback_chapter
            )
        totals["recipes"] += recipe_count
    except Exception as exc:  # noqa: BLE001
        log.error("game.global_recipes_load_failed", error=str(exc))
        try:
            await session.rollback()
        except Exception:  # noqa: BLE001
            pass

    # Global _decisions/
    try:
        async with session.begin_nested():
            decision_count = await _upsert_global_decisions(
                session, game_dir, chapter_dirs_by_dirname, fallback_chapter
            )
        totals["decisions"] += decision_count
    except Exception as exc:  # noqa: BLE001
        log.error("game.global_decisions_load_failed", error=str(exc))
        try:
            await session.rollback()
        except Exception:  # noqa: BLE001
            pass

    log.info(
        "game.loaded",
        chapters=totals["chapters"],
        levels=totals["levels"],
        concepts=totals["concepts"],
        recipes=totals["recipes"],
        decisions=totals["decisions"],
    )
    return totals


# Backward-compatible alias (seed.py imports this as `load`)
async def load(
    session: AsyncSession, game_dir: Path | None = None
) -> dict[str, int]:
    """Legacy entry point — wraps load_game_content.

    Kept for backward compatibility; seed.py imports `load`.
    If game_dir is None, resolves from settings.content_dir.
    """
    if game_dir is None:
        from ..settings import settings
        resolved = settings.content_dir / GAME_CONTENT_SUBDIR
    else:
        resolved = game_dir
    return await load_game_content(session, base_dir=resolved)
