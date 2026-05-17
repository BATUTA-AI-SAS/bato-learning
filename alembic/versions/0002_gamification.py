"""gamification: xp events + achievement unlocks

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-16
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "xp_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("event_type", sa.String(length=48), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ref_kind", sa.String(length=32), nullable=False, server_default=""),
        sa.Column("ref_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id", "event_type", "ref_kind", "ref_id",
            name="uq_xp_event_unique_per_ref",
        ),
    )
    op.create_index("ix_xp_event_user_id", "xp_event", ["user_id"])
    op.create_index("ix_xp_event_event_type", "xp_event", ["event_type"])
    op.create_index("ix_xp_event_created_at", "xp_event", ["created_at"])

    op.create_table(
        "achievement_unlock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("code", sa.String(length=48), nullable=False),
        sa.Column(
            "unlocked_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", "code", name="uq_achievement_unlock_user_code"),
    )
    op.create_index("ix_achievement_unlock_user_id", "achievement_unlock", ["user_id"])
    op.create_index("ix_achievement_unlock_code", "achievement_unlock", ["code"])


def downgrade() -> None:
    op.drop_table("achievement_unlock")
    op.drop_table("xp_event")
