"""Content catalog: modules, exercises, quizzes.

Content is the source of truth in files under `app/content/`. The DB is a cache
populated by `services/content_loader.py`. A `content_hash` lets the loader re-seed
only what changed.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db import Base


class Module(Base):
    __tablename__ = "module"
    __table_args__ = (UniqueConstraint("slug", name="uq_module_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    ext_id: Mapped[str] = mapped_column(String(16), unique=True)  # A01, B03, F-FIN-01...
    track: Mapped[str] = mapped_column(String(2))                 # A, B, C, D, E, F
    ord: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(256))
    summary: Mapped[str] = mapped_column(Text, default="")
    body_md: Mapped[str] = mapped_column(Text, default="")
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    exercises: Mapped[list[Exercise]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="Exercise.ord"
    )
    quizzes: Mapped[list[Quiz]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="Quiz.ord"
    )


class Exercise(Base):
    __tablename__ = "exercise"
    __table_args__ = (UniqueConstraint("module_id", "slug", name="uq_exercise_slug_per_module"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("module.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(128))
    ord: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(256))
    prompt_md: Mapped[str] = mapped_column(Text)
    hint_md: Mapped[str] = mapped_column(Text, default="")
    starter_code: Mapped[str] = mapped_column(Text, default="")
    test_code: Mapped[str] = mapped_column(Text, default="")
    solution_code: Mapped[str] = mapped_column(Text, default="")
    runner: Mapped[str] = mapped_column(String(32), default="pyodide")  # pyodide | backend
    kind: Mapped[str] = mapped_column(String(32), default="code")       # code | design

    module: Mapped[Module] = relationship(back_populates="exercises")


class Quiz(Base):
    __tablename__ = "quiz"
    __table_args__ = (UniqueConstraint("module_id", "slug", name="uq_quiz_slug_per_module"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("module.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(128))
    ord: Mapped[int] = mapped_column(Integer)
    question_md: Mapped[str] = mapped_column(Text)
    explanation_md: Mapped[str] = mapped_column(Text, default="")
    # G8: new micro-interactive types. kind defaults to "radio" (existing behavior).
    # Accepted values: radio | match | predict | tf
    kind: Mapped[str] = mapped_column(String(32), default="radio")
    # meta_json stores type-specific payload as JSON string (pairs for match,
    # bonus_window_ms for tf, etc.). Empty string = no extra metadata.
    meta_json: Mapped[str] = mapped_column(Text, default="")

    module: Mapped[Module] = relationship(back_populates="quizzes")
    options: Mapped[list[QuizOption]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan", order_by="QuizOption.ord"
    )


class QuizOption(Base):
    __tablename__ = "quiz_option"

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quiz.id", ondelete="CASCADE"), index=True)
    ord: Mapped[int] = mapped_column(Integer)
    text_md: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback_md: Mapped[str] = mapped_column(Text, default="")

    quiz: Mapped[Quiz] = relationship(back_populates="options")
