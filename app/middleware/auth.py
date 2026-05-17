"""Require authentication for all routes except public ones."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

PUBLIC_PATHS = frozenset({"/", "/login", "/register", "/health"})
PUBLIC_PREFIXES = ("/static/",)


class RequireAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)
        if not request.session.get("user_id"):
            if path.startswith("/api/"):
                return JSONResponse({"detail": "auth required"}, status_code=401)
            return RedirectResponse("/login", status_code=303)
        return await call_next(request)
