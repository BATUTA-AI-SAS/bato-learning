"""Quiz answers."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..db import SessionDep
from ..repos import gamification as gam_repo
from ..repos import modules as modules_repo
from ..repos import progress as progress_repo

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


class AnswerBody(BaseModel):
    option_id: int


class AnswerResult(BaseModel):
    correct: bool
    correct_option_id: int
    explanation_md: str
    selected_feedback_md: str
    xp_awarded: int = 0
    newly_unlocked: list[str] = []


@router.post("/{quiz_id}/answer", response_model=AnswerResult)
async def answer(
    quiz_id: int, body: AnswerBody, request: Request, session: SessionDep
) -> AnswerResult:
    quiz = await modules_repo.get_quiz(session, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="quiz no encontrado")
    selected = next((o for o in quiz.options if o.id == body.option_id), None)
    if selected is None:
        raise HTTPException(status_code=400, detail="opción inválida")
    correct_opt = next((o for o in quiz.options if o.is_correct), None)
    user = await progress_repo.get_current_or_default_user(request, session)
    _, correct = await progress_repo.add_quiz_answer(
        session, user_id=user.id, quiz_id=quiz_id, option_id=body.option_id
    )
    xp = 0
    newly: list[str] = []
    if correct:
        xp = await gam_repo.record_quiz_correct_xp(
            session, user_id=user.id, quiz_id=quiz_id
        )
        snap = await gam_repo.snapshot(session, user_id=user.id)
        newly = list(snap.get("newly_unlocked", []))
    return AnswerResult(
        correct=correct,
        correct_option_id=correct_opt.id if correct_opt else 0,
        explanation_md=quiz.explanation_md,
        selected_feedback_md=selected.feedback_md,
        xp_awarded=xp,
        newly_unlocked=newly,
    )
