"""game schema: chapter, game_level, recipe, decision, lore_drop, user_progress,
level_attempt, skill_mastery, decision_choice, lore_unlock

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-16
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chapter",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(8), nullable=False, unique=True),  # CHA01..CHA15
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("setting", sa.String(256), nullable=False, server_default=""),
        sa.Column("palette_hex", sa.String(32), nullable=False, server_default="#888888"),
        sa.Column("intro_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("outro_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("theme", sa.String(128), nullable=False, server_default=""),
        sa.Column("est_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("content_hash", sa.String(64), nullable=False, server_default=""),
    )
    op.create_index("ix_chapter_ord", "chapter", ["ord"])
    op.create_index("ix_chapter_code", "chapter", ["code"])

    op.create_table(
        "game_level",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chapter_id", sa.Integer(),
            sa.ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column(
            "kind", sa.String(32), nullable=False
        ),  # order_steps | multi_choice | predict | fill_blank | tf | code | boss
        sa.Column("scenario_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("hint_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("solution_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("est_seconds", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("requires_skill", sa.String(60), nullable=True),
        sa.Column("trains_skill", sa.String(60), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False, server_default=""),
    )
    op.create_index("ix_game_level_chapter_id", "game_level", ["chapter_id"])
    op.create_index("ix_game_level_ord", "game_level", ["ord"])

    op.create_table(
        "recipe",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chapter_id", sa.Integer(),
            sa.ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("body_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("ingredients_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("yields_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_hash", sa.String(64), nullable=False, server_default=""),
    )
    op.create_index("ix_recipe_chapter_id", "recipe", ["chapter_id"])

    op.create_table(
        "decision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chapter_id", sa.Integer(),
            sa.ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("prompt_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("options_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("content_hash", sa.String(64), nullable=False, server_default=""),
    )
    op.create_index("ix_decision_chapter_id", "decision", ["chapter_id"])

    op.create_table(
        "lore_drop",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("module_ref", sa.String(60), nullable=False, server_default=""),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("summary_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("unlock_after_level_slug", sa.String(128), nullable=True),
        sa.Column("reading_minutes", sa.Integer(), nullable=False, server_default="5"),
    )

    op.create_table(
        "user_progress",
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, primary_key=True
        ),
        sa.Column(
            "chapter_id", sa.Integer(),
            sa.ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False, primary_key=True
        ),
        sa.Column("levels_passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_progress_user_id", "user_progress", ["user_id"])
    op.create_index("ix_user_progress_chapter_id", "user_progress", ["chapter_id"])

    op.create_table(
        "level_attempt",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "level_id", sa.Integer(),
            sa.ForeignKey("game_level.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("passed", sa.Integer(), nullable=False, server_default="0"),   # 0/1
        sa.Column("hint_used", sa.Integer(), nullable=False, server_default="0"),  # 0/1
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
    )
    op.create_index("ix_level_attempt_user_id", "level_attempt", ["user_id"])
    sa.Index("ix_level_attempt_level_id", "level_id")
    op.create_index("ix_level_attempt_level_id", "level_attempt", ["level_id"])

    op.create_table(
        "skill_mastery",
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, primary_key=True
        ),
        sa.Column("skill", sa.String(60), nullable=False, primary_key=True),
        sa.Column("level_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unaided_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_passed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_passed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_skill_mastery_user_id", "skill_mastery", ["user_id"])

    op.create_table(
        "decision_choice",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "decision_id", sa.Integer(),
            sa.ForeignKey("decision.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("option_index", sa.Integer(), nullable=False),
        sa.Column("chosen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_decision_choice_user_id", "decision_choice", ["user_id"])
    op.create_index("ix_decision_choice_decision_id", "decision_choice", ["decision_id"])

    op.create_table(
        "lore_unlock",
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, primary_key=True
        ),
        sa.Column(
            "lore_drop_id", sa.Integer(),
            sa.ForeignKey("lore_drop.id", ondelete="CASCADE"), nullable=False, primary_key=True
        ),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_lore_unlock_user_id", "lore_unlock", ["user_id"])


def downgrade() -> None:
    op.drop_table("lore_unlock")
    op.drop_table("decision_choice")
    op.drop_table("skill_mastery")
    op.drop_table("level_attempt")
    op.drop_table("user_progress")
    op.drop_table("lore_drop")
    op.drop_table("decision")
    op.drop_table("recipe")
    op.drop_table("game_level")
    op.drop_table("chapter")
