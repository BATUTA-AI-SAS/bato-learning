"""HTML pages: home, module view, progress dashboard."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from ..db import SessionDep
from ..repos import gamification as gam_repo
from ..repos import modules as modules_repo
from ..repos import progress as progress_repo
from ..services.auth import get_current_user
from ..templating import templates

router = APIRouter()


def _track_groups(modules):
    """Group modules by track for the sidebar."""
    groups: dict[str, list] = {}
    for m in modules:
        groups.setdefault(m.track, []).append(m)
    return [(t, groups[t]) for t in sorted(groups)]


def _continue_target(all_modules, visited: set[int]):
    """Pick the module the user should resume.

    Heuristic: the lowest-`ord` unvisited module. If none, the lowest-`ord`
    visited module (re-read). Returns None if there are no modules.
    """
    for m in all_modules:
        if m.id not in visited:
            return m
    return all_modules[0] if all_modules else None


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/game", status_code=302)


@router.get("/legacy-home", response_class=HTMLResponse)
async def legacy_home(request: Request, session: SessionDep):
    current_user = await get_current_user(request, session)
    user = current_user or await progress_repo.get_or_create_user(session)
    all_modules = await modules_repo.list_all(session)
    summary = await progress_repo.progress_summary(session, user.id)
    visited = await progress_repo.visited_module_ids(session, user.id)
    snapshot = await gam_repo.snapshot(session, user_id=user.id)
    track_progress = await gam_repo.per_track_progress(session, user_id=user.id)
    cont = _continue_target(all_modules, visited)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "current_user": current_user,
            "groups": _track_groups(all_modules),
            "summary": summary,
            "visited": visited,
            "modules": all_modules,
            "current": None,
            "gam": snapshot,
            "track_progress": track_progress,
            "continue_module": cont,
        },
    )


@router.get("/m/{slug}", response_class=HTMLResponse)
async def module_page(slug: str, request: Request, session: SessionDep):
    current_user = await get_current_user(request, session)
    user = current_user or await progress_repo.get_or_create_user(session)
    mod = await modules_repo.get_by_slug(session, slug)
    if mod is None:
        raise HTTPException(status_code=404, detail="módulo no encontrado")
    # Visit + idempotent XP event for first-time visits.
    await progress_repo.touch_visit(session, user_id=user.id, module_id=mod.id)
    awarded = await gam_repo.record_module_visit_xp(
        session, user_id=user.id, module=mod
    )
    all_modules = await modules_repo.list_all(session)
    visited = await progress_repo.visited_module_ids(session, user.id)
    snapshot = await gam_repo.snapshot(session, user_id=user.id)
    track_progress = await gam_repo.per_track_progress(session, user_id=user.id)
    # Next module CTA — strictly the next in ord order. If none, repeat self.
    nxt = await gam_repo.next_module(
        session, user_id=user.id, current_module_id=mod.id
    )
    return templates.TemplateResponse(
        request,
        "module.html",
        {
            "user": user,
            "current_user": current_user,
            "module": mod,
            "groups": _track_groups(all_modules),
            "modules": all_modules,
            "visited": visited,
            "current": mod,
            "gam": snapshot,
            "track_progress": track_progress,
            "next_module": nxt,
            "xp_awarded_on_visit": awarded,
        },
    )


@router.get("/progreso", response_class=HTMLResponse)
async def progress_page(request: Request, session: SessionDep):
    current_user = await get_current_user(request, session)
    user = current_user or await progress_repo.get_or_create_user(session)
    summary = await progress_repo.progress_summary(session, user.id)
    all_modules = await modules_repo.list_all(session)
    visited = await progress_repo.visited_module_ids(session, user.id)
    snapshot = await gam_repo.snapshot(session, user_id=user.id)
    track_progress = await gam_repo.per_track_progress(session, user_id=user.id)
    return templates.TemplateResponse(
        request,
        "progress.html",
        {
            "user": user,
            "current_user": current_user,
            "summary": summary,
            "modules": all_modules,
            "visited": visited,
            "groups": _track_groups(all_modules),
            "current": None,
            "gam": snapshot,
            "track_progress": track_progress,
        },
    )
