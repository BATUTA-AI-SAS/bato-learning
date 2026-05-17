"""game: add concepts_introduced, concepts_reinforced to game_level; add concept_popup and user_concept_seen tables.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"


def upgrade() -> None:
    op.add_column("game_level", sa.Column("concepts_introduced", sa.Text(), server_default="[]"))
    op.add_column("game_level", sa.Column("concepts_reinforced", sa.Text(), server_default="[]"))

    op.create_table(
        "concept_popup",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(60), unique=True, index=True, nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("analogy_md", sa.Text(), server_default=""),
        sa.Column("example_md", sa.Text(), server_default=""),
        sa.Column("content_hash", sa.String(64), server_default=""),
    )

    op.create_table(
        "user_concept_seen",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("concept_slug", sa.String(60), primary_key=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("user_concept_seen")
    op.drop_table("concept_popup")
    op.drop_column("game_level", "concepts_reinforced")
    op.drop_column("game_level", "concepts_introduced")
