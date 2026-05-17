"""Landing page route."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ..db import SessionDep
from ..services.auth import get_current_user
from ..templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request, session: SessionDep):
    user = await get_current_user(request, session)
    if user is not None:
        return RedirectResponse("/game/world", status_code=302)
    return templates.TemplateResponse(request, "landing.html", {})
