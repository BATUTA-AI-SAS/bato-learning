"""Progress JSON for client-side widgets."""
from fastapi import APIRouter, HTTPException, Request

from ..db import SessionDep
from ..repos import gamification as gam_repo
from ..repos import modules as modules_repo
from ..repos import progress as progress_repo

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("")
async def get_progress(request: Request, session: SessionDep) -> dict:
    user = await progress_repo.get_current_or_default_user(request, session)
    summary = await progress_repo.progress_summary(session, user.id)
    visited = sorted(await progress_repo.visited_module_ids(session, user.id))
    snap = await gam_repo.snapshot(session, user_id=user.id)
    return {
        "summary": summary,
        "visited_module_ids": visited,
        "near_unlocks": snap.get("near_unlocks", []),
    }


# Separate router for checkpoint events (different prefix avoids prefix clash)
checkpoint_router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])


@checkpoint_router.post("/{module_id}/{checkpoint_id}")
async def record_checkpoint(
    module_id: int,
    checkpoint_id: str,
    request: Request,
    session: SessionDep,
) -> dict:
    """Idempotent: award XP once per (user, module, checkpoint).

    Returns ``{xp_awarded, newly_unlocked}``.
    """
    mod = await modules_repo.get_by_id(session, module_id)
    if mod is None:
        raise HTTPException(status_code=404, detail="módulo no encontrado")
    user = await progress_repo.get_current_or_default_user(request, session)
    xp = await gam_repo.record_checkpoint_xp(
        session,
        user_id=user.id,
        module_id=module_id,
        checkpoint_id=checkpoint_id,
        track=mod.track,
    )
    newly: list[str] = []
    if xp > 0:
        snap = await gam_repo.snapshot(session, user_id=user.id)
        newly = list(snap.get("newly_unlocked", []))
    return {"xp_awarded": xp, "newly_unlocked": newly}
