"""Load modules + exercises + quizzes from `app/content/` into the DB.

Filesystem layout:

    app/content/
      A/
        A01.md                # Markdown with frontmatter (ext_id, slug, ord, ...)
        A01.exercises.yaml    # optional
        A01.quizzes.yaml      # optional
      ...
      F/
        F-FIN-01.md
        ...

The loader computes a stable hash of the file set per module and re-seeds only what
changed.

Quiz YAML supports an optional `kind` field:
  - radio  (default) — existing multiple-choice behavior
  - match  — pair-matching; requires `pairs: [{left: ..., right: ...}, ...]`
  - predict — show code, user types expected output; requires `code` field
  - tf     — true/false with optional bonus window; requires `options` with 2 entries

An optional `meta` dict is serialized to JSON in `meta_json`. Example for tf:
  meta:
    bonus_window_ms: 5000
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import frontmatter
import structlog
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Exercise, Module, Quiz, QuizOption
from ..settings import settings

log = structlog.get_logger(__name__)


def _hash_for_files(*paths: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        if p.exists():
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:32]


async def _upsert_module(session: AsyncSession, md_path: Path) -> Module:
    post = frontmatter.load(md_path)
    meta = post.metadata
    # tolerate `id:` as alias of `ext_id:` (common slip in module frontmatter)
    ext_id = str(meta.get("ext_id") or meta.get("id") or "").strip()
    if not ext_id:
        raise ValueError(f"frontmatter missing ext_id/id in {md_path}")
    slug = str(meta["slug"])

    ex_yaml = md_path.with_suffix(".exercises.yaml")
    qz_yaml = md_path.with_suffix(".quizzes.yaml")

    content_hash = _hash_for_files(md_path, ex_yaml, qz_yaml)

    res = await session.execute(select(Module).where(Module.ext_id == ext_id))
    mod = res.scalar_one_or_none()
    if mod and mod.content_hash == content_hash:
        return mod  # nothing changed

    if mod is None:
        mod = Module(ext_id=ext_id, slug=slug, track=meta["track"], ord=int(meta["ord"]))
        session.add(mod)

    mod.slug = slug
    mod.track = meta["track"]
    mod.ord = int(meta["ord"])
    mod.title = str(meta["title"])
    mod.summary = str(meta.get("summary", ""))
    mod.estimated_minutes = int(meta.get("estimated_minutes", 30))
    mod.body_md = post.content
    mod.content_hash = content_hash

    await session.flush()
    await _replace_exercises(session, mod, ex_yaml)
    await _replace_quizzes(session, mod, qz_yaml)
    await session.commit()
    return mod


async def _replace_exercises(session: AsyncSession, mod: Module, path: Path) -> None:
    res = await session.execute(select(Exercise).where(Exercise.module_id == mod.id))
    for e in res.scalars().all():
        await session.delete(e)
    await session.flush()  # ensure deletes hit the DB before re-inserts
    if not path.exists():
        return
    data = yaml.safe_load(path.read_text()) or []
    for ord_, item in enumerate(data, start=1):
        ex = Exercise(
            module_id=mod.id,
            slug=str(item["slug"]),
            ord=ord_,
            title=str(item.get("title", item["slug"])),
            prompt_md=_pick(item, "prompt", "prompt_md"),
            hint_md=_pick(item, "hint", "hint_md"),
            starter_code=_pick(item, "starter", "starter_code"),
            test_code=_pick(item, "test", "test_code"),
            solution_code=_pick(item, "solution", "solution_code"),
            runner=str(item.get("runner", "pyodide")),
            kind=str(item.get("kind", "code")),
        )
        session.add(ex)


def _pick(item: dict, *keys: str, default: str = "") -> str:
    for k in keys:
        if k in item and item[k] is not None:
            return str(item[k])
    return default


async def _replace_quizzes(session: AsyncSession, mod: Module, path: Path) -> None:
    res = await session.execute(select(Quiz).where(Quiz.module_id == mod.id))
    for q in res.scalars().all():
        await session.delete(q)
    await session.flush()  # ensure deletes hit the DB before re-inserts
    if not path.exists():
        return
    data = yaml.safe_load(path.read_text()) or []
    for ord_, item in enumerate(data, start=1):
        # G8: kind defaults to "radio" for backward compatibility.
        # Accepted: radio | match | predict | tf
        kind = str(item.get("kind", "radio"))

        # Build meta_json: merge explicit `meta` dict with type-specific fields.
        meta: dict = {}
        if "meta" in item and isinstance(item["meta"], dict):
            meta.update(item["meta"])
        # For match quizzes, store pairs in meta_json so the template can read them.
        if kind == "match" and "pairs" in item:
            meta["pairs"] = item["pairs"]
        # For predict quizzes, store expected_output and code block.
        if kind == "predict":
            if "code" in item:
                meta["code"] = item["code"]
            if "expected_output" in item:
                meta["expected_output"] = item["expected_output"]

        q = Quiz(
            module_id=mod.id,
            slug=str(item["slug"]),
            ord=ord_,
            question_md=_pick(item, "question", "question_md"),
            explanation_md=_pick(item, "explanation", "explanation_md"),
            kind=kind,
            meta_json=json.dumps(meta) if meta else "",
        )
        session.add(q)
        await session.flush()

        # For match/predict, options may be absent — that's fine.
        for o_ord, opt in enumerate(item.get("options", []), start=1):
            is_correct = opt.get("correct")
            if is_correct is None:
                is_correct = opt.get("is_correct", False)
            session.add(
                QuizOption(
                    quiz_id=q.id,
                    ord=o_ord,
                    text_md=_pick(opt, "text", "text_md"),
                    is_correct=bool(is_correct),
                    feedback_md=_pick(opt, "feedback", "feedback_md"),
                )
            )


async def load_all(session: AsyncSession, content_dir: Path | None = None) -> int:
    """Load every `<ext_id>.md` under content_dir. Returns count of modules touched.

    Each module is loaded in its own savepoint so a single bad file doesn't poison
    the whole transaction.
    """
    base = Path(content_dir or settings.content_dir)
    if not base.exists():
        log.warning("content_dir.missing", path=str(base))
        return 0
    count = 0
    for md_path in sorted(base.rglob("*.md")):
        if md_path.name.startswith("_"):
            continue
        if md_path.name.endswith(".exercises.md") or md_path.name.endswith(".quizzes.md"):
            continue
        try:
            await _upsert_module(session, md_path)
            count += 1
        except Exception as exc:  # noqa: BLE001
            log.error("content.load_failed", path=str(md_path), error=str(exc))
            # ensure the session can continue with the next module
            try:
                await session.rollback()
            except Exception:  # noqa: BLE001
                pass
    log.info("content.loaded", count=count, base=str(base))
    return count
