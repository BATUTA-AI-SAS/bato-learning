"""Minimal test: game loader upserts chapter + levels from a fake directory."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.content_loader_game import load
from app.repos.game import list_chapters, list_levels_for_chapter


async def test_game_loader_upserts_chapter_and_levels(session, tmp_path: Path):
    chapter_dir = tmp_path / "CHA01"
    chapter_dir.mkdir()
    (chapter_dir / "_chapter.yaml").write_text(
        "slug: el-despertar\ncode: CHA01\nord: 1\ntitle: El despertar\n"
        "setting: despacho\npalette_hex: '#1a1a2e'\n"
    )
    (chapter_dir / "paso-a-paso.yaml").write_text(
        "slug: paso-a-paso\ntitle: Paso a paso\nkind: order_steps\n"
        "trains_skill: secuenciar\nscenario_md: Ordena los pasos.\n"
        "payload:\n  steps: [a, b, c]\n  correct_order: [0, 1, 2]\n"
    )
    (chapter_dir / "decision-simple.yaml").write_text(
        "slug: decision-simple\ntitle: Decision\nkind: multi_choice\n"
        "trains_skill: decidir\nscenario_md: Elige.\n"
        "payload:\n  options:\n    - text: Si\n      correct: true\n"
    )

    totals = await load(session, game_dir=tmp_path)

    assert totals["chapters"] == 1
    assert totals["levels"] == 2

    chapters = await list_chapters(session)
    assert len(chapters) == 1
    assert chapters[0].slug == "el-despertar"

    levels = await list_levels_for_chapter(session, chapters[0].id)
    assert len(levels) == 2
    slugs = {lv.slug for lv in levels}
    assert "paso-a-paso" in slugs
    assert "decision-simple" in slugs
