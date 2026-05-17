"""Exercise attempts. Pyodide-runner POSTs outcome; backend-runner executes here."""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..db import SessionDep
from ..repos import gamification as gam_repo
from ..repos import modules as modules_repo
from ..repos import progress as progress_repo
from ..services.exercise_runner import run_backend_exercise

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


class PyodideAttempt(BaseModel):
    code: str
    passed: bool
    output: str = ""
    error: str = ""
    duration_ms: int = 0


class BackendAttempt(BaseModel):
    code: str


class AttemptResult(BaseModel):
    passed: bool
    output: str
    error: str
    attempt_id: int
    xp_awarded: int = 0
    newly_unlocked: list[str] = []


@router.post("/{exercise_id}/pyodide", response_model=AttemptResult)
async def submit_pyodide(
    exercise_id: int, body: PyodideAttempt, request: Request, session: SessionDep
) -> AttemptResult:
    ex = await modules_repo.get_exercise(session, exercise_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="ejercicio no encontrado")
    user = await progress_repo.get_current_or_default_user(request, session)
    att = await progress_repo.add_attempt(
        session,
        user_id=user.id,
        exercise_id=exercise_id,
        code=body.code,
        passed=body.passed,
        output=body.output,
        error=body.error,
        runner="pyodide",
        duration_ms=body.duration_ms,
    )
    xp = 0
    newly: list[str] = []
    if body.passed:
        xp = await gam_repo.record_exercise_passed_xp(
            session, user_id=user.id, exercise_id=exercise_id
        )
        snap = await gam_repo.snapshot(session, user_id=user.id)
        newly = list(snap.get("newly_unlocked", []))
    return AttemptResult(
        passed=body.passed, output=body.output, error=body.error, attempt_id=att.id,
        xp_awarded=xp, newly_unlocked=newly,
    )


@router.post("/{exercise_id}/backend", response_model=AttemptResult)
async def submit_backend(
    exercise_id: int, body: BackendAttempt, request: Request, session: SessionDep
) -> AttemptResult:
    ex = await modules_repo.get_exercise(session, exercise_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="ejercicio no encontrado")
    start = time.monotonic()
    outcome = await run_backend_exercise(body.code, ex.test_code)
    dur = int((time.monotonic() - start) * 1000)
    user = await progress_repo.get_current_or_default_user(request, session)
    att = await progress_repo.add_attempt(
        session,
        user_id=user.id,
        exercise_id=exercise_id,
        code=body.code,
        passed=outcome["passed"],
        output=outcome["output"],
        error=outcome["error"],
        runner="backend",
        duration_ms=dur,
    )
    xp = 0
    newly: list[str] = []
    if outcome["passed"]:
        xp = await gam_repo.record_exercise_passed_xp(
            session, user_id=user.id, exercise_id=exercise_id
        )
        snap = await gam_repo.snapshot(session, user_id=user.id)
        newly = list(snap.get("newly_unlocked", []))
    return AttemptResult(
        passed=outcome["passed"],
        output=outcome["output"],
        error=outcome["error"],
        attempt_id=att.id,
        xp_awarded=xp,
        newly_unlocked=newly,
    )
