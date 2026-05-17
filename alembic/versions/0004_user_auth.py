"""user: add email, password_hash, display_name, is_active, last_login_at

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-16
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("display_name", sa.String(64), nullable=False, server_default="tú"))
    op.add_column("user", sa.Column("email", sa.String(120), nullable=True))
    op.add_column("user", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("user", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")))
    op.add_column("user", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))

    # Backfill display_name from existing name column.
    op.execute("UPDATE \"user\" SET display_name = name WHERE display_name = 'tú'")

    # Partial unique index on email: only enforced where email IS NOT NULL.
    op.create_index(
        "ix_user_email",
        "user",
        ["email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
        sqlite_where=sa.text("email IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_user_email", table_name="user")
    op.drop_column("user", "last_login_at")
    op.drop_column("user", "is_active")
    op.drop_column("user", "password_hash")
    op.drop_column("user", "email")
    op.drop_column("user", "display_name")
