"""Data access helpers for the game tables.

Pure data access — no business logic about unlocks, XP awards, or skill thresholds.
That belongs in services, not here.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.game import (
    Chapter,
    ConceptPopup,
    Decision,
    DecisionChoice,
    GameLevel,
    LoreDrop,
    LoreUnlock,
    LevelAttempt,
    Recipe,
    SkillMastery,
    UserConceptSeen,
    UserProgress,
)


# ---------------------------------------------------------------------------
# Phase aliases (task requirement uses "phase" terminology)
# ---------------------------------------------------------------------------

async def list_phases(session: AsyncSession) -> list[Chapter]:
    return await list_chapters(session)


async def get_phase(session: AsyncSession, slug: str) -> Chapter | None:
    return await get_chapter(session, slug)


async def list_levels_for_phase(
    session: AsyncSession, phase_id: int
) -> list[GameLevel]:
    return await list_levels_for_chapter(session, phase_id)


# ---------------------------------------------------------------------------
# Core chapter/level queries
# ---------------------------------------------------------------------------

async def list_chapters(session: AsyncSession) -> list[Chapter]:
    res = await session.execute(select(Chapter).order_by(Chapter.ord))
    return list(res.scalars().all())


async def get_chapter(session: AsyncSession, slug: str) -> Chapter | None:
    res = await session.execute(
        select(Chapter)
        .where(Chapter.slug == slug)
        .options(
            selectinload(Chapter.levels),
            selectinload(Chapter.recipes),
            selectinload(Chapter.decisions),
        )
    )
    return res.scalar_one_or_none()


async def list_levels_for_chapter(
    session: AsyncSession, chapter_id: int
) -> list[GameLevel]:
    res = await session.execute(
        select(GameLevel)
        .where(GameLevel.chapter_id == chapter_id)
        .order_by(GameLevel.ord)
    )
    return list(res.scalars().all())


async def get_level(session: AsyncSession, slug: str) -> GameLevel | None:
    res = await session.execute(
        select(GameLevel).where(GameLevel.slug == slug)
    )
    return res.scalar_one_or_none()


async def record_attempt(
    session: AsyncSession,
    *,
    user_id: int,
    level_id: int,
    passed: bool,
    hint_used: bool,
    attempt_count: int = 1,
    payload: dict | None = None,
    duration_seconds: int | None = None,
) -> LevelAttempt:
    attempt = LevelAttempt(
        user_id=user_id,
        level_id=level_id,
        passed=int(passed),
        hint_used=int(hint_used),
        attempt_count=attempt_count,
        completed_at=datetime.now(timezone.utc),
        duration_seconds=duration_seconds,
    )
    attempt._payload_json = json.dumps(payload or {})
    session.add(attempt)
    await session.flush()
    return attempt


async def mark_pass(
    session: AsyncSession,
    *,
    user_id: int,
    level_id: int,
    passed: bool,
    hint_used: bool = False,
    payload: dict | None = None,
    duration_seconds: int | None = None,
) -> LevelAttempt:
    """Record a completed attempt (pass or fail)."""
    return await record_attempt(
        session,
        user_id=user_id,
        level_id=level_id,
        passed=passed,
        hint_used=hint_used,
        payload=payload,
        duration_seconds=duration_seconds,
    )


async def user_progress_summary(
    session: AsyncSession, user_id: int
) -> list[UserProgress]:
    res = await session.execute(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    return list(res.scalars().all())


async def skill_mastery_for(
    session: AsyncSession, user_id: int
) -> list[SkillMastery]:
    res = await session.execute(
        select(SkillMastery).where(SkillMastery.user_id == user_id)
    )
    return list(res.scalars().all())


async def unlock_lore(
    session: AsyncSession, *, user_id: int, lore_drop_id: int
) -> LoreUnlock:
    res = await session.execute(
        select(LoreUnlock).where(
            LoreUnlock.user_id == user_id,
            LoreUnlock.lore_drop_id == lore_drop_id,
        )
    )
    existing = res.scalar_one_or_none()
    if existing:
        return existing
    unlock = LoreUnlock(user_id=user_id, lore_drop_id=lore_drop_id)
    session.add(unlock)
    await session.flush()
    return unlock


async def record_decision_choice(
    session: AsyncSession,
    *,
    user_id: int,
    decision_id: int,
    option_index: int,
) -> DecisionChoice:
    choice = DecisionChoice(
        user_id=user_id,
        decision_id=decision_id,
        option_index=option_index,
    )
    session.add(choice)
    await session.flush()
    return choice


# ---------------------------------------------------------------------------
# Concepts
# ---------------------------------------------------------------------------

async def list_concept_popups(session: AsyncSession) -> list[ConceptPopup]:
    res = await session.execute(select(ConceptPopup))
    return list(res.scalars().all())


async def mark_concept_seen(
    session: AsyncSession, user_id: int, concept_slug: str
) -> None:
    existing = await session.get(UserConceptSeen, (user_id, concept_slug))
    if existing is None:
        session.add(UserConceptSeen(user_id=user_id, concept_slug=concept_slug))
        await session.flush()


async def user_seen_concepts(session: AsyncSession, user_id: int) -> set[str]:
    res = await session.execute(
        select(UserConceptSeen.concept_slug).where(UserConceptSeen.user_id == user_id)
    )
    return set(res.scalars().all())


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

async def list_recipes(session: AsyncSession) -> list[Recipe]:
    res = await session.execute(select(Recipe))
    return list(res.scalars().all())


# ---------------------------------------------------------------------------
# Decisions for a phase
# ---------------------------------------------------------------------------

async def list_decisions_for_phase(
    session: AsyncSession, phase_id: int
) -> list[Decision]:
    res = await session.execute(
        select(Decision).where(Decision.chapter_id == phase_id)
    )
    return list(res.scalars().all())


# ---------------------------------------------------------------------------
# Skill mastery helpers
# ---------------------------------------------------------------------------

async def user_skill_mastery(session: AsyncSession, user_id: int) -> list[SkillMastery]:
    return await skill_mastery_for(session, user_id)


async def increment_skill(
    session: AsyncSession, user_id: int, skill: str, hint_used: bool
) -> None:
    now = datetime.now(timezone.utc)
    mastery = await session.get(SkillMastery, (user_id, skill))
    if mastery is None:
        mastery = SkillMastery(
            user_id=user_id,
            skill=skill,
            level_count=0,
            unaided_count=0,
            first_passed_at=now,
        )
        session.add(mastery)
    mastery.level_count += 1
    if not hint_used:
        mastery.unaided_count += 1
    mastery.last_passed_at = now
    await session.flush()


# ---------------------------------------------------------------------------
# Per-phase progress dict
# ---------------------------------------------------------------------------

async def user_phase_progress(
    session: AsyncSession, user_id: int, phase_id: int
) -> dict:
    """Return {levels_passed, total, percent} for a user/phase pair."""
    levels = await list_levels_for_chapter(session, phase_id)
    if not levels:
        return {"levels_passed": 0, "total": 0, "percent": 0}
    level_ids = [lv.id for lv in levels]
    res = await session.execute(
        select(LevelAttempt.level_id)
        .where(
            LevelAttempt.user_id == user_id,
            LevelAttempt.level_id.in_(level_ids),
            LevelAttempt.passed == 1,
        )
        .distinct()
    )
    passed_count = len(set(res.scalars().all()))
    total = len(levels)
    return {
        "levels_passed": passed_count,
        "total": total,
        "percent": round(passed_count / total * 100) if total else 0,
    }


# ---------------------------------------------------------------------------
# Lore unlocks for user (used by journal)
# ---------------------------------------------------------------------------

async def user_lore_unlocks(session: AsyncSession, user_id: int) -> list[LoreUnlock]:
    res = await session.execute(
        select(LoreUnlock)
        .where(LoreUnlock.user_id == user_id)
        .options(selectinload(LoreUnlock.lore_drop))
    )
    return list(res.scalars().all())


# ---------------------------------------------------------------------------
# Decision choices made by user
# ---------------------------------------------------------------------------

async def user_decision_choices(
    session: AsyncSession, user_id: int
) -> list[DecisionChoice]:
    res = await session.execute(
        select(DecisionChoice)
        .where(DecisionChoice.user_id == user_id)
        .options(selectinload(DecisionChoice.decision))
    )
    return list(res.scalars().all())
