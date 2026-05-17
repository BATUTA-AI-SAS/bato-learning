"""Game models: chapter map, levels, recipes, decisions, lore, progress.

JSON columns use Text + property getter/setter (same pattern as Quiz.meta_json).
Boolean flags (passed, hint_used) stored as Integer 0/1 for SQLite compatibility.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db import Base


class Chapter(Base):
    __tablename__ = "chapter"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    ord: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True)  # CHA01..CHA15
    title: Mapped[str] = mapped_column(String(256))
    setting: Mapped[str] = mapped_column(Text, default="")
    palette_hex: Mapped[str] = mapped_column(String(32), default="#888888")
    intro_md: Mapped[str] = mapped_column(Text, default="")
    outro_md: Mapped[str] = mapped_column(Text, default="")
    theme: Mapped[str] = mapped_column(String(128), default="")
    est_minutes: Mapped[int] = mapped_column(Integer, default=30)
    content_hash: Mapped[str] = mapped_column(String(64), default="")

    levels: Mapped[list[GameLevel]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="GameLevel.ord",
    )
    recipes: Mapped[list[Recipe]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[list[Decision]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
    )


class GameLevel(Base):
    __tablename__ = "game_level"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapter.id", ondelete="CASCADE"), index=True
    )
    ord: Mapped[int] = mapped_column(Integer, index=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    kind: Mapped[str] = mapped_column(String(32))  # order_steps|multi_choice|predict|fill_blank|tf|code|boss
    scenario_md: Mapped[str] = mapped_column(Text, default="")
    _payload_json: Mapped[str] = mapped_column("payload_json", Text, default="{}")
    hint_md: Mapped[str] = mapped_column(Text, default="")
    solution_md: Mapped[str] = mapped_column(Text, default="")
    xp: Mapped[int] = mapped_column(Integer, default=10)
    est_seconds: Mapped[int] = mapped_column(Integer, default=90)
    requires_skill: Mapped[str | None] = mapped_column(String(60), nullable=True)
    trains_skill: Mapped[str] = mapped_column(String(60))
    _concepts_introduced_json: Mapped[str] = mapped_column("concepts_introduced", Text, default="[]")
    _concepts_reinforced_json: Mapped[str] = mapped_column("concepts_reinforced", Text, default="[]")
    content_hash: Mapped[str] = mapped_column(String(64), default="")

    chapter: Mapped[Chapter] = relationship(back_populates="levels")
    attempts: Mapped[list[LevelAttempt]] = relationship(
        back_populates="level",
        cascade="all, delete-orphan",
    )

    @property
    def payload(self) -> dict:
        raw = self._payload_json or "{}"
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return {}

    @payload.setter
    def payload(self, value: dict) -> None:
        self._payload_json = json.dumps(value)

    @property
    def concepts_introduced(self) -> list[str]:
        try:
            return json.loads(self._concepts_introduced_json or "[]")
        except (ValueError, TypeError):
            return []

    @concepts_introduced.setter
    def concepts_introduced(self, value: list[str]) -> None:
        self._concepts_introduced_json = json.dumps(value)

    @property
    def concepts_reinforced(self) -> list[str]:
        try:
            return json.loads(self._concepts_reinforced_json or "[]")
        except (ValueError, TypeError):
            return []

    @concepts_reinforced.setter
    def concepts_reinforced(self, value: list[str]) -> None:
        self._concepts_reinforced_json = json.dumps(value)


class ConceptPopup(Base):
    """Just-in-time micro-lesson (≤15s) shown the first time a level requires a concept."""
    __tablename__ = "concept_popup"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    analogy_md: Mapped[str] = mapped_column(Text, default="")
    example_md: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="")


class UserConceptSeen(Base):
    """Tracks which concept popups a user has already seen."""
    __tablename__ = "user_concept_seen"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    concept_slug: Mapped[str] = mapped_column(String(60), primary_key=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Recipe(Base):
    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapter.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    body_md: Mapped[str] = mapped_column(Text, default="")
    _ingredients_json: Mapped[str] = mapped_column("ingredients_json", Text, default="[]")
    yields_md: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="")

    chapter: Mapped[Chapter] = relationship(back_populates="recipes")

    @property
    def ingredients(self) -> list:
        raw = self._ingredients_json or "[]"
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return []

    @ingredients.setter
    def ingredients(self, value: list) -> None:
        self._ingredients_json = json.dumps(value)


class Decision(Base):
    __tablename__ = "decision"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapter.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    prompt_md: Mapped[str] = mapped_column(Text, default="")
    _options_json: Mapped[str] = mapped_column("options_json", Text, default="[]")
    content_hash: Mapped[str] = mapped_column(String(64), default="")

    chapter: Mapped[Chapter] = relationship(back_populates="decisions")
    choices: Mapped[list[DecisionChoice]] = relationship(
        back_populates="decision",
        cascade="all, delete-orphan",
    )

    @property
    def options(self) -> list:
        raw = self._options_json or "[]"
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return []

    @options.setter
    def options(self, value: list) -> None:
        self._options_json = json.dumps(value)


class LoreDrop(Base):
    __tablename__ = "lore_drop"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    module_ref: Mapped[str] = mapped_column(String(60), default="")
    title: Mapped[str] = mapped_column(String(256))
    summary_md: Mapped[str] = mapped_column(Text, default="")
    body_md: Mapped[str] = mapped_column(Text, default="")
    unlock_after_level_slug: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reading_minutes: Mapped[int] = mapped_column(Integer, default=5)

    unlocks: Mapped[list[LoreUnlock]] = relationship(
        back_populates="lore_drop",
        cascade="all, delete-orphan",
    )


class UserProgress(Base):
    __tablename__ = "user_progress"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapter.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    levels_passed: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class LevelAttempt(Base):
    __tablename__ = "level_attempt"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    level_id: Mapped[int] = mapped_column(
        ForeignKey("game_level.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # SQLite stores as INTEGER 0/1; bool coercion happens via Python
    passed: Mapped[int] = mapped_column(Integer, default=0)
    hint_used: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    _payload_json: Mapped[str] = mapped_column("payload_json", Text, default="{}")
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    level: Mapped[GameLevel] = relationship(back_populates="attempts")

    @property
    def payload(self) -> dict:
        raw = self._payload_json or "{}"
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return {}

    @payload.setter
    def payload(self, value: dict) -> None:
        self._payload_json = json.dumps(value)


class SkillMastery(Base):
    __tablename__ = "skill_mastery"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    skill: Mapped[str] = mapped_column(String(60), primary_key=True)
    level_count: Mapped[int] = mapped_column(Integer, default=0)
    unaided_count: Mapped[int] = mapped_column(Integer, default=0)
    first_passed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_passed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DecisionChoice(Base):
    __tablename__ = "decision_choice"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    decision_id: Mapped[int] = mapped_column(
        ForeignKey("decision.id", ondelete="CASCADE"), index=True
    )
    option_index: Mapped[int] = mapped_column(Integer)
    chosen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    decision: Mapped[Decision] = relationship(back_populates="choices")


class LoreUnlock(Base):
    __tablename__ = "lore_unlock"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    lore_drop_id: Mapped[int] = mapped_column(
        ForeignKey("lore_drop.id", ondelete="CASCADE"), primary_key=True
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    lore_drop: Mapped[LoreDrop] = relationship(back_populates="unlocks")
