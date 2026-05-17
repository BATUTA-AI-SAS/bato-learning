"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .logging_setup import configure_logging
from .routers import chat, exercises, game, health, pages, progress, quizzes
from .routers import auth as auth_router
from .routers.progress import checkpoint_router
from .settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(title="bato-learning", lifespan=lifespan)

# SessionMiddleware must be added before routers so request.session is available.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age_seconds,
    https_only=False,
    same_site="lax",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health.router)
app.include_router(auth_router.router)
app.include_router(pages.router)
app.include_router(exercises.router)
app.include_router(quizzes.router)
app.include_router(chat.router)
app.include_router(progress.router)
app.include_router(checkpoint_router)
app.include_router(game.router)
