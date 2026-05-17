"""Game routes: HTML pages + JSON API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
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
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/game/world", status_code=302)


@router.get("/game/world", response_class=HTMLResponse)
async def game_world(request: Request, session: SessionDep):
    """The RPG world view — canvas-based room navigation."""
    import json as _json
    from ..services.auth import require_user

    user = await require_user(request, session)
    phases = await game_repo.list_phases(session)

    # Build game state for JS
    rooms_state = {}
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
        passed_slugs = [lv.slug for lv in levels if lv.id in passed_ids]

        # A room is unlocked if it's the first OR previous room has >= 70%
        phase_idx = phases.index(phase)
        unlocked = phase_idx == 0
        if phase_idx > 0:
            prev_prog = await game_repo.user_phase_progress(session, user.id, phases[phase_idx - 1].id)
            unlocked = prev_prog["percent"] >= 70

        rooms_state[phase.slug] = {
            "unlocked": unlocked,
            "levels_passed": passed_slugs,
            "percent": prog["percent"],
        }

    # Total XP from passed levels
    total_xp = 0
    for phase in phases:
        levels = await game_repo.list_levels_for_phase(session, phase.id)
        for lv in levels:
            if lv.slug in rooms_state[phase.slug]["levels_passed"]:
                total_xp += lv.xp

    game_state = {
        "player_name": user.display_name or user.name or "Jugador",
        "rooms": rooms_state,
        "total_xp": total_xp,
    }

    return templates.TemplateResponse(
        request,
        "game/world.html",
        {"game_state_json": _json.dumps(game_state, ensure_ascii=False)},
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

    # JSON-serializable list for JS
    import json as _json
    new_concepts_json = _json.dumps([
        {
            "slug":       p.slug,
            "title":      p.title,
            "analogy_md": p.analogy_md,
            "example_md": p.example_md,
        }
        for p in new_concepts
    ])

    # Next level in this phase (or back to phase map if last)
    all_levels = await game_repo.list_levels_for_phase(session, phase.id)
    next_level = None
    for idx, lv in enumerate(all_levels):
        if lv.id == level.id and idx + 1 < len(all_levels):
            next_level = all_levels[idx + 1]
            break
    next_level_url = (
        f"/game/{phase.slug}/{next_level.slug}" if next_level else f"/game/{phase.slug}"
    )

    # Detect if coming from RPG world
    from_world = request.query_params.get("from") == "world"

    # If from world, return to world after completion instead of next level
    if from_world:
        next_level_url = "/game/world"

    return templates.TemplateResponse(
        request,
        "game/level_player.html",
        {
            "user": user,
            "current_user": user,
            "phase": phase,
            "level": level,
            "new_concepts": new_concepts,
            "new_concepts_json": new_concepts_json,
            "next_level": next_level,
            "next_level_url": next_level_url,
            "from_world": from_world,
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


@router.get("/api/game/level/{level_slug}")
async def get_level_data(level_slug: str, request: Request, session: SessionDep) -> dict:
    """Return level data for inline puzzle rendering."""
    from ..services.auth import require_user
    user = await require_user(request, session)
    level = await game_repo.get_level(session, level_slug)
    if level is None:
        raise HTTPException(status_code=404, detail="nivel no encontrado")

    # Check which concepts are new to this user
    seen_concepts = await game_repo.user_seen_concepts(session, user.id)
    new_concepts = []
    all_popups = {p.slug: p for p in await game_repo.list_concept_popups(session)}
    for slug in level.concepts_introduced:
        if slug not in seen_concepts and slug in all_popups:
            p = all_popups[slug]
            new_concepts.append({
                "slug": p.slug,
                "title": p.title,
                "analogy_md": p.analogy_md,
                "example_md": p.example_md,
            })

    return {
        "slug": level.slug,
        "title": level.title,
        "kind": level.kind,
        "scenario_md": level.scenario_md,
        "payload": level.payload,
        "hint_md": level.hint_md,
        "xp": level.xp,
        "est_seconds": level.est_seconds,
        "new_concepts": new_concepts,
    }


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


# ---------------------------------------------------------------------------
# Game mentor chat (SSE) — minimal system prompt, no module context needed
# ---------------------------------------------------------------------------

_GAME_TUTOR_SYSTEM = """Eres Don Ramón, un contador veterano de 60 años con 30 años en ACME Manufacturing.
Llevas gafas gruesas y siempre tienes un café en la mano.
Hablas con sabiduría práctica y humor seco mexicano.
Tuteas al jugador. Lo llamas "mijo" o "chamaco" ocasionalmente.
Comparas programación con contabilidad cuando aplica.
NUNCA das la respuesta directa. Haces preguntas que guían al descubrimiento.
Máximo 3 oraciones por respuesta. Siempre en español.
Si el jugador se frustra, lo calmas con una anécdota breve."""


class GameChatBody(BaseModel):
    message: str
    context: str | None = None
    level_slug: str | None = None


@router.post("/api/game/chat")
async def game_chat(body: GameChatBody, request: Request, session: SessionDep):
    """SSE stream for the game-level mentor panel. No module_id required."""
    import json as _json
    from ..services.deepseek_client import stream_chat

    extra = ""
    if body.level_slug:
        extra = f"\nNivel activo: {body.level_slug}"
    if body.context:
        extra += f"\nContexto: {body.context}"

    system = _GAME_TUTOR_SYSTEM + extra
    messages = [{"role": "user", "content": body.message}]

    def _sse(event: str, payload: dict) -> bytes:
        return f"event: {event}\ndata: {_json.dumps(payload, ensure_ascii=False)}\n\n".encode()

    async def gen():
        async for chunk in stream_chat(system=system, messages=messages):
            if chunk.text:
                yield _sse("delta", {"text": chunk.text})
            if chunk.done:
                yield _sse("done", {"usage": chunk.usage or {}})

    return StreamingResponse(gen(), media_type="text/event-stream")
