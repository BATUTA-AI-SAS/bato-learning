"""Seed the DB: ensure user row, load content from app/content/."""
from __future__ import annotations

import asyncio

import structlog

from app.db import SessionFactory
from app.logging_setup import configure_logging
from app.repos import progress as progress_repo
from app.services.content_loader import load_all
from app.services.content_loader_game import load_game_content


async def main() -> None:
    configure_logging()
    log = structlog.get_logger("seed")
    async with SessionFactory() as session:
        await progress_repo.get_or_create_user(session)
        count = await load_all(session)
        game_totals = await load_game_content(session)
    log.info("seed.done", modules=count)
    log.info(
        "game.seed.done",
        chapters=game_totals["chapters"],
        levels=game_totals["levels"],
        concepts=game_totals["concepts"],
        recipes=game_totals["recipes"],
        decisions=game_totals["decisions"],
    )


if __name__ == "__main__":
    asyncio.run(main())
