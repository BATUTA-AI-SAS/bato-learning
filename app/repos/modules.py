"""Queries for modules / exercises / quizzes."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Exercise, Module, Quiz


async def list_all(session: AsyncSession) -> list[Module]:
    res = await session.execute(select(Module).order_by(Module.ord))
    return list(res.scalars().all())


async def list_by_track(session: AsyncSession, track: str) -> list[Module]:
    res = await session.execute(
        select(Module).where(Module.track == track).order_by(Module.ord)
    )
    return list(res.scalars().all())


async def get_by_slug(session: AsyncSession, slug: str) -> Module | None:
    res = await session.execute(
        select(Module)
        .where(Module.slug == slug)
        .options(
            selectinload(Module.exercises),
            selectinload(Module.quizzes).selectinload(Quiz.options),
        )
    )
    return res.scalar_one_or_none()


async def get_by_id(session: AsyncSession, module_id: int) -> Module | None:
    return await session.get(Module, module_id)


async def get_exercise(session: AsyncSession, exercise_id: int) -> Exercise | None:
    return await session.get(Exercise, exercise_id)


async def get_quiz(session: AsyncSession, quiz_id: int) -> Quiz | None:
    res = await session.execute(
        select(Quiz).where(Quiz.id == quiz_id).options(selectinload(Quiz.options))
    )
    return res.scalar_one_or_none()
