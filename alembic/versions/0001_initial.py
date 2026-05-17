"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-16
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False, server_default="tú"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "module",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("ext_id", sa.String(length=16), nullable=False),
        sa.Column("track", sa.String(length=2), nullable=False),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("content_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_module_slug"),
        sa.UniqueConstraint("ext_id", name="uq_module_ext_id"),
    )
    op.create_index("ix_module_slug", "module", ["slug"])

    op.create_table(
        "exercise",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_id", sa.Integer(), sa.ForeignKey("module.id", ondelete="CASCADE")),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("prompt_md", sa.Text(), nullable=False),
        sa.Column("hint_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("starter_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("test_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("solution_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("runner", sa.String(length=32), nullable=False, server_default="pyodide"),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="code"),
        sa.UniqueConstraint("module_id", "slug", name="uq_exercise_slug_per_module"),
    )
    op.create_index("ix_exercise_module_id", "exercise", ["module_id"])

    op.create_table(
        "quiz",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_id", sa.Integer(), sa.ForeignKey("module.id", ondelete="CASCADE")),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.Column("question_md", sa.Text(), nullable=False),
        sa.Column("explanation_md", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("module_id", "slug", name="uq_quiz_slug_per_module"),
    )
    op.create_index("ix_quiz_module_id", "quiz", ["module_id"])

    op.create_table(
        "quiz_option",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quiz_id", sa.Integer(), sa.ForeignKey("quiz.id", ondelete="CASCADE")),
        sa.Column("ord", sa.Integer(), nullable=False),
        sa.Column("text_md", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("feedback_md", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_quiz_option_quiz_id", "quiz_option", ["quiz_id"])

    op.create_table(
        "module_visit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE")),
        sa.Column("module_id", sa.Integer(), sa.ForeignKey("module.id", ondelete="CASCADE")),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("seconds_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_module_visit_user_id", "module_visit", ["user_id"])
    op.create_index("ix_module_visit_module_id", "module_visit", ["module_id"])

    op.create_table(
        "exercise_attempt",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE")),
        sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercise.id", ondelete="CASCADE")),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("output", sa.Text(), nullable=False, server_default=""),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("runner", sa.String(length=32), nullable=False, server_default="pyodide"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_exercise_attempt_user_id", "exercise_attempt", ["user_id"])
    op.create_index("ix_exercise_attempt_exercise_id", "exercise_attempt", ["exercise_id"])
    op.create_index("ix_exercise_attempt_created_at", "exercise_attempt", ["created_at"])

    op.create_table(
        "quiz_answer",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE")),
        sa.Column("quiz_id", sa.Integer(), sa.ForeignKey("quiz.id", ondelete="CASCADE")),
        sa.Column("option_id", sa.Integer(), sa.ForeignKey("quiz_option.id", ondelete="CASCADE")),
        sa.Column("correct", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quiz_answer_user_id", "quiz_answer", ["user_id"])
    op.create_index("ix_quiz_answer_quiz_id", "quiz_answer", ["quiz_id"])
    op.create_index("ix_quiz_answer_created_at", "quiz_answer", ["created_at"])

    op.create_table(
        "chat_session",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE")),
        sa.Column("module_id", sa.Integer(), sa.ForeignKey("module.id", ondelete="CASCADE")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_session_user_id", "chat_session", ["user_id"])
    op.create_index("ix_chat_session_module_id", "chat_session", ["module_id"])

    op.create_table(
        "chat_message",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id", sa.Integer(), sa.ForeignKey("chat_session.id", ondelete="CASCADE")
        ),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_cache_read", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_cache_write", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_message_session_id", "chat_message", ["session_id"])


def downgrade() -> None:
    for t in (
        "chat_message",
        "chat_session",
        "quiz_answer",
        "exercise_attempt",
        "module_visit",
        "quiz_option",
        "quiz",
        "exercise",
        "module",
        "user",
    ):
        op.drop_table(t)
