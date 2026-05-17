"""Smoke tests for the app. Run from repo root: `uv run pytest -x`."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.repos import modules as modules_repo
from app.repos import progress as progress_repo
from app.services.content_loader import load_all
from app.services.exercise_runner import run_backend_exercise


async def test_user_is_created(session):
    user = await progress_repo.get_or_create_user(session)
    assert user.id == 1
    again = await progress_repo.get_or_create_user(session)
    assert again.id == 1


async def test_loader_round_trip(session, tmp_path: Path):
    track_dir = tmp_path / "A"
    track_dir.mkdir()
    (track_dir / "A99.md").write_text(
        "---\next_id: A99\nslug: test-module\ntrack: A\nord: 99\n"
        'title: "Test"\nestimated_minutes: 15\n---\n\n# body\n'
    )
    (track_dir / "A99.exercises.yaml").write_text(
        "- slug: x1\n  title: Foo\n  prompt: ''\n  starter: ''\n  test: 'assert True'\n  solution: 'pass'\n"
    )
    (track_dir / "A99.quizzes.yaml").write_text(
        "- slug: q1\n  question: 'q?'\n  options:\n"
        "    - text: a\n      correct: true\n      feedback: ok\n"
        "    - text: b\n      correct: false\n      feedback: nope\n"
    )
    count = await load_all(session, content_dir=tmp_path)
    assert count == 1
    mod = await modules_repo.get_by_slug(session, "test-module")
    assert mod is not None
    assert mod.ext_id == "A99"
    assert len(mod.exercises) == 1
    assert len(mod.quizzes) == 1
    assert len(mod.quizzes[0].options) == 2


async def test_progress_summary(session):
    user = await progress_repo.get_or_create_user(session)
    summary = await progress_repo.progress_summary(session, user.id)
    assert summary["modules_total"] == 0
    assert summary["modules_visited"] == 0
    assert summary["attempts"] == 0


def test_backend_runner_assert_passes():
    res = asyncio.run(run_backend_exercise("x = 1 + 2", "assert x == 3"))
    assert res["passed"] is True


def test_backend_runner_assert_fails():
    res = asyncio.run(run_backend_exercise("x = 1 + 1", "assert x == 3"))
    assert res["passed"] is False
    assert res["error"]  # any non-empty error message


def test_backend_runner_syntax_error():
    res = asyncio.run(run_backend_exercise("def (\n", ""))
    assert res["passed"] is False
