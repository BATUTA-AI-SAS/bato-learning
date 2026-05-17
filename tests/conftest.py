"""Pytest fixtures: in-memory SQLite for tests."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def session():
    from app.db import Base, engine, SessionFactory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionFactory() as s:
        yield s

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
