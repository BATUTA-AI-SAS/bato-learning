"""Authentication helpers: hashing, register, login, session management."""
from __future__ import annotations

import re
from datetime import datetime, timezone

import bcrypt
from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# bcrypt truncates at 72 bytes; we trim silently to stay safe.
_MAX_PW_BYTES = 72


def hash_password(plain: str) -> str:
    pw_bytes = plain.encode("utf-8")[:_MAX_PW_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pw_bytes = plain.encode("utf-8")[:_MAX_PW_BYTES]
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


async def register(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    display_name: str = "tú",
) -> User:
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Correo electrónico inválido.")
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con ese correo.")
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name.strip() or "tú",
        name=display_name.strip() or "tú",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> User | None:
    email = email.strip().lower()
    res = await session.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = res.scalar_one_or_none()
    if user is None or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()
    return user


def login_user(request: Request, user: User) -> None:
    request.session["user_id"] = user.id


def logout_user(request: Request) -> None:
    request.session.clear()


async def get_current_user(request: Request, session: AsyncSession) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


async def require_user(request: Request, session: AsyncSession) -> User:
    user = await get_current_user(request, session)
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida.")
    return user
