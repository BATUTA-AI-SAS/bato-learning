"""Async SQLAlchemy engine + session factory.

We use a single engine for the whole app. Each request gets its own session via the
`get_session` dependency.
"""
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .settings import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
