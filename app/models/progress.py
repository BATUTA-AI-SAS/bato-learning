"""User progress: visits, exercise attempts, quiz answers."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..db import Base


class ModuleVisit(Base):
    __tablename__ = "module_visit"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("module.id", ondelete="CASCADE"), index=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    seconds_total: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempt"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercise.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(Text)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    output: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    runner: Mapped[str] = mapped_column(String(32), default="pyodide")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class QuizAnswer(Base):
    __tablename__ = "quiz_answer"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quiz.id", ondelete="CASCADE"), index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("quiz_option.id", ondelete="CASCADE"))
    correct: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
