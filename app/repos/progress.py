"""Progress reads/writes."""
from __future__ import annotations

from fastapi import Request
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Exercise,
    ExerciseAttempt,
    Module,
    ModuleVisit,
    QuizAnswer,
    QuizOption,
    User,
)


async def get_current_or_default_user(request: Request, session: AsyncSession) -> User:
    """Return the session-authenticated user, or the singleton legacy user."""
    # Lazy import to avoid circular dependency (auth imports models; repos import models).
    from ..services.auth import get_current_user  # noqa: PLC0415

    current = await get_current_user(request, session)
    if current is not None:
        return current
    return await get_or_create_user(session)


async def get_or_create_user(session: AsyncSession, name: str = "tú") -> User:
    user = await session.get(User, 1)
    if user is None:
        user = User(id=1, name=name)
        session.add(user)
        await session.commit()
    return user


async def touch_visit(session: AsyncSession, user_id: int, module_id: int) -> ModuleVisit:
    res = await session.execute(
        select(ModuleVisit).where(
            ModuleVisit.user_id == user_id, ModuleVisit.module_id == module_id
        )
    )
    visit = res.scalar_one_or_none()
    if visit is None:
        visit = ModuleVisit(user_id=user_id, module_id=module_id)
        session.add(visit)
    await session.commit()
    return visit


async def add_attempt(
    session: AsyncSession,
    *,
    user_id: int,
    exercise_id: int,
    code: str,
    passed: bool,
    output: str = "",
    error: str = "",
    runner: str = "pyodide",
    duration_ms: int = 0,
) -> ExerciseAttempt:
    attempt = ExerciseAttempt(
        user_id=user_id,
        exercise_id=exercise_id,
        code=code,
        passed=passed,
        output=output[:8000],
        error=error[:4000],
        runner=runner,
        duration_ms=duration_ms,
    )
    session.add(attempt)
    await session.commit()
    return attempt


async def recent_attempts_for_module(
    session: AsyncSession, *, user_id: int, module_id: int, limit: int = 5
) -> list[ExerciseAttempt]:
    res = await session.execute(
        select(ExerciseAttempt)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .where(
            ExerciseAttempt.user_id == user_id,
            Exercise.module_id == module_id,
        )
        .order_by(desc(ExerciseAttempt.created_at))
        .limit(limit)
    )
    return list(res.scalars().all())


async def add_quiz_answer(
    session: AsyncSession,
    *,
    user_id: int,
    quiz_id: int,
    option_id: int,
) -> tuple[QuizAnswer, bool]:
    opt = await session.get(QuizOption, option_id)
    correct = bool(opt and opt.is_correct)
    ans = QuizAnswer(user_id=user_id, quiz_id=quiz_id, option_id=option_id, correct=correct)
    session.add(ans)
    await session.commit()
    return ans, correct


async def progress_summary(session: AsyncSession, user_id: int) -> dict:
    total_modules = (
        await session.execute(select(func.count()).select_from(Module))
    ).scalar_one()
    visited = (
        await session.execute(
            select(func.count(func.distinct(ModuleVisit.module_id))).where(
                ModuleVisit.user_id == user_id
            )
        )
    ).scalar_one()
    attempts = (
        await session.execute(
            select(func.count()).select_from(ExerciseAttempt).where(
                ExerciseAttempt.user_id == user_id
            )
        )
    ).scalar_one()
    passed = (
        await session.execute(
            select(func.count()).select_from(ExerciseAttempt).where(
                ExerciseAttempt.user_id == user_id, ExerciseAttempt.passed.is_(True)
            )
        )
    ).scalar_one()
    quizzes_correct = (
        await session.execute(
            select(func.count()).select_from(QuizAnswer).where(
                QuizAnswer.user_id == user_id, QuizAnswer.correct.is_(True)
            )
        )
    ).scalar_one()
    quizzes_total = (
        await session.execute(
            select(func.count(func.distinct(QuizAnswer.quiz_id))).where(
                QuizAnswer.user_id == user_id
            )
        )
    ).scalar_one()
    return {
        "modules_total": total_modules,
        "modules_visited": visited,
        "attempts": attempts,
        "attempts_passed": passed,
        "quizzes_answered": quizzes_total,
        "quizzes_correct": quizzes_correct,
    }


async def visited_module_ids(session: AsyncSession, user_id: int) -> set[int]:
    res = await session.execute(
        select(ModuleVisit.module_id).where(ModuleVisit.user_id == user_id)
    )
    return {row[0] for row in res.all()}
