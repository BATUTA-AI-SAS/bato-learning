"""Game routes: HTML pages + JSON API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..db import SessionDep
from ..repos import game as game_repo
from ..repos import progress as progress_repo
from ..templating import templates

router = APIRouter(tags=["game"])


# ---------------------------------------------------------------------------
# HTML pages
# ---------------------------------------------------------------------------

@router.get("/game", response_class=HTMLResponse)
async def game_home(request: Request, session: SessionDep):
    user = await progress_repo.get_current_or_default_user(request, session)
    phases = await game_repo.list_phases(session)
    phase_progress = [
        await game_repo.user_phase_progress(session, user.id, p.id)
        for p in phases
    ]
    # Current phase: first incomplete, or last if all done.
    current_phase = None
    for phase, prog in zip(phases, phase_progress):
        if prog["percent"] < 100:
            current_phase = phase
            break
    if current_phase is None and phases:
        current_phase = phases[-1]

    phases_with_progress = [
        {"phase": p, "progress": prog}
        for p, prog in zip(phases, phase_progress)
    ]

    return templates.TemplateResponse(
        request,
        "game/home.html",
        {
            "user": user,
            "current_user": user,
            "phases_with_progress": phases_with_progress,
            "current_phase": current_phase,
            "gam": None,
            "current": None,
        },
    )


@router.get("/game/{phase_slug}", response_class=HTMLResponse)
async def phase_map(phase_slug: str, request: Request, session: SessionDep):
    user = await progress_repo.get_current_or_default_user(request, session)
    phase = await game_repo.get_phase(session, phase_slug)
    if phase is None:
        raise HTTPException(status_code=404, detail="fase no encontrada")

    levels = await game_repo.list_levels_for_phase(session, phase.id)
    # Build per-level passed state.
    from sqlalchemy import select
    from ..models.game import LevelAttempt
    res = await session.execute(
        select(LevelAttempt.level_id)
        .where(
            LevelAttempt.user_id == user.id,
            LevelAttempt.level_id.in_([lv.id for lv in levels]),
            LevelAttempt.passed == 1,
        )
        .distinct()
    )
    passed_ids = set(res.scalars().all())
    levels_state = [
        {"level": lv, "passed": lv.id in passed_ids}
        for lv in levels
    ]

    return templates.TemplateResponse(
        request,
        "game/phase_map.html",
        {
            "user": user,
            "current_user": user,
            "phase": phase,
            "levels_state": levels_state,
            "gam": None,
            "current": None,
        },
    )


@router.get("/game/{phase_slug}/{level_slug}", response_class=HTMLResponse)
async def level_player(
    phase_slug: str, level_slug: str, request: Request, session: SessionDep
):
    user = await progress_repo.get_current_or_default_user(request, session)
    phase = await game_repo.get_phase(session, phase_slug)
    if phase is None:
        raise HTTPException(status_code=404, detail="fase no encontrada")
    level = await game_repo.get_level(session, level_slug)
    if level is None or level.chapter_id != phase.id:
        raise HTTPException(status_code=404, detail="nivel no encontrado")

    seen_concepts = await game_repo.user_seen_concepts(session, user.id)
    # Concepts to introduce: those the level introduces that the user hasn't seen.
    new_concepts: list = []
    all_popups = {p.slug: p for p in await game_repo.list_concept_popups(session)}
    for slug in level.concepts_introduced:
        if slug not in seen_concepts and slug in all_popups:
            new_concepts.append(all_popups[slug])

    return templates.TemplateResponse(
        request,
        "game/level_player.html",
        {
            "user": user,
            "current_user": user,
            "phase": phase,
            "level": level,
            "new_concepts": new_concepts,
            "gam": None,
            "current": None,
        },
    )


@router.get("/journal", response_class=HTMLResponse)
async def journal(request: Request, session: SessionDep):
    user = await progress_repo.get_current_or_default_user(request, session)
    lore_unlocks = await game_repo.user_lore_unlocks(session, user.id)
    recipes = await game_repo.list_recipes(session)
    decisions = await game_repo.user_decision_choices(session, user.id)

    return templates.TemplateResponse(
        request,
        "game/journal.html",
        {
            "user": user,
            "current_user": user,
            "lore_unlocks": lore_unlocks,
            "recipes": recipes,
            "decisions": decisions,
            "gam": None,
            "current": None,
        },
    )


@router.get("/skills", response_class=HTMLResponse)
async def skills_page(request: Request, session: SessionDep):
    user = await progress_repo.get_current_or_default_user(request, session)
    skills = await game_repo.user_skill_mastery(session, user.id)

    return templates.TemplateResponse(
        request,
        "game/skills.html",
        {
            "user": user,
            "current_user": user,
            "skills": skills,
            "gam": None,
            "current": None,
        },
    )


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

class AttemptIn(BaseModel):
    level_slug: str
    passed: bool
    hint_used: bool = False
    payload: dict = {}
    duration_seconds: int | None = None


class ConceptSeenIn(BaseModel):
    concept_slug: str


@router.post("/api/game/attempt")
async def post_attempt(body: AttemptIn, request: Request, session: SessionDep) -> dict:
    user = await progress_repo.get_current_or_default_user(request, session)
    level = await game_repo.get_level(session, body.level_slug)
    if level is None:
        raise HTTPException(status_code=404, detail="nivel no encontrado")

    await game_repo.record_attempt(
        session,
        user_id=user.id,
        level_id=level.id,
        passed=body.passed,
        hint_used=body.hint_used,
        payload=body.payload,
        duration_seconds=body.duration_seconds,
    )
    await session.commit()

    xp_awarded = level.xp if body.passed else 0

    # Update skill mastery when passed.
    newly_unlocked_concepts: list[str] = []
    if body.passed and level.trains_skill:
        await game_repo.increment_skill(
            session, user_id=user.id, skill=level.trains_skill, hint_used=body.hint_used
        )
        await session.commit()

        # Concepts introduced by this level that are new to the user.
        seen = await game_repo.user_seen_concepts(session, user.id)
        newly_unlocked_concepts = [
            c for c in level.concepts_introduced if c not in seen
        ]

    return {"xp_awarded": xp_awarded, "newly_unlocked_concepts": newly_unlocked_concepts}


@router.post("/api/game/concept-seen")
async def post_concept_seen(
    body: ConceptSeenIn, request: Request, session: SessionDep
) -> dict:
    user = await progress_repo.get_current_or_default_user(request, session)
    await game_repo.mark_concept_seen(session, user.id, body.concept_slug)
    await session.commit()
    return {"ok": True}


@router.get("/api/game/progress")
async def get_game_progress(request: Request, session: SessionDep) -> dict:
    user = await progress_repo.get_current_or_default_user(request, session)
    phases = await game_repo.list_phases(session)
    phases_data = []
    for phase in phases:
        prog = await game_repo.user_phase_progress(session, user.id, phase.id)
        levels = await game_repo.list_levels_for_phase(session, phase.id)

        from sqlalchemy import select
        from ..models.game import LevelAttempt
        res = await session.execute(
            select(LevelAttempt.level_id)
            .where(
                LevelAttempt.user_id == user.id,
                LevelAttempt.level_id.in_([lv.id for lv in levels]),
                LevelAttempt.passed == 1,
            )
            .distinct()
        )
        passed_ids = set(res.scalars().all())
        phases_data.append({
            "slug": phase.slug,
            "title": phase.title,
            "progress": prog,
            "levels_passed": list(passed_ids),
        })

    skills = await game_repo.user_skill_mastery(session, user.id)
    decisions = await game_repo.user_decision_choices(session, user.id)

    return {
        "phases": phases_data,
        "skills": [
            {
                "skill": s.skill,
                "level_count": s.level_count,
                "unaided_count": s.unaided_count,
            }
            for s in skills
        ],
        "decisions": [
            {
                "decision_id": d.decision_id,
                "option_index": d.option_index,
            }
            for d in decisions
        ],
    }
