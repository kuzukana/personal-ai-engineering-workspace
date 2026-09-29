"""Add knowledge to technology relations.

Revision ID: 0003_knowledge_technologies
Revises: 0002_seed_builtin
Create Date: 2026-09-29
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_knowledge_technologies"
down_revision = "0002_seed_builtin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_technologies",
        sa.Column(
            "knowledge_id",
            sa.Uuid(),
            sa.ForeignKey("knowledge_items.id"),
            primary_key=True,
        ),
        sa.Column(
            "technology_id",
            sa.Uuid(),
            sa.ForeignKey("technologies.id"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("knowledge_technologies")
