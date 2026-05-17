"""Gamification: XP events and unlocked achievements.

The XP catalog (`event_type -> points`) and the achievement catalog
(`code -> rule`) live in code (`app.services.gamification`). The DB only
stores the immutable journal of what already happened, so we can recompute
XP, level, streak and unlocked achievements at any time. No PII, no tenants:
this is the same single-user assumption as the rest of the app.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..db import Base


class XpEvent(Base):
    """One row per scoring event. Append-only.

    `event_type` is a short code from the XP catalog (e.g. `module_visit`,
    `exercise_passed`, `quiz_correct`, `streak_bonus`). `points` is the XP
    awarded at the moment the event was recorded; the catalog can change
    later without rewriting history. `ref_kind` + `ref_id` let us avoid
    duplicate awards (e.g. only one `module_visit` per module).
    """

    __tablename__ = "xp_event"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "event_type", "ref_kind", "ref_id",
            name="uq_xp_event_unique_per_ref",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(48), index=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    ref_kind: Mapped[str] = mapped_column(String(32), default="")
    ref_id: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class AchievementUnlock(Base):
    """One row per achievement unlocked. `code` is the catalog key."""

    __tablename__ = "achievement_unlock"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_achievement_unlock_user_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(48), index=True)
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
