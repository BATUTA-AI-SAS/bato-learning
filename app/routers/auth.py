"""Auth routes: login, register, logout."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ..db import SessionDep
from ..services.auth import authenticate, get_current_user, login_user, logout_user, register
from ..templating import templates

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, session: SessionDep):
    current_user = await get_current_user(request, session)
    if current_user is not None:
        return RedirectResponse("/", status_code=302)
    error = request.session.pop("flash_error", None)
    return templates.TemplateResponse(
        request, "auth/login.html", {"current_user": current_user, "error": error}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    session: SessionDep,
    email: str = Form(...),
    password: str = Form(...),
):
    user = await authenticate(session, email=email, password=password)
    if user is None:
        request.session["flash_error"] = "Correo o contraseña incorrectos."
        return RedirectResponse("/login", status_code=303)
    login_user(request, user)
    return RedirectResponse("/", status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, session: SessionDep):
    current_user = await get_current_user(request, session)
    if current_user is not None:
        return RedirectResponse("/", status_code=302)
    error = request.session.pop("flash_error", None)
    return templates.TemplateResponse(
        request, "auth/register.html", {"current_user": current_user, "error": error}
    )


@router.post("/register")
async def register_submit(
    request: Request,
    session: SessionDep,
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(default="tú"),
):
    try:
        user = await register(session, email=email, password=password, display_name=display_name)
    except HTTPException as exc:
        request.session["flash_error"] = exc.detail
        return RedirectResponse("/register", status_code=303)
    login_user(request, user)
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
async def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=303)
