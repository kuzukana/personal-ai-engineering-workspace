"""Enforce one Knowledge item per source without silently deleting user data."""

import sqlalchemy as sa

from alembic import op

revision = "0004_knowledge_source_unique"
down_revision = "0003_knowledge_technologies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    duplicate = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT source_research_id FROM knowledge_items "
                "WHERE source_research_id IS NOT NULL GROUP BY source_research_id "
                "HAVING count(*) > 1 LIMIT 1"
            )
        )
        .first()
    )
    if duplicate:
        raise RuntimeError("Duplicate Knowledge sources exist; reconcile them before migration")
    op.create_unique_constraint("uq_knowledge_source", "knowledge_items", ["source_research_id"])


def downgrade() -> None:
    op.drop_constraint("uq_knowledge_source", "knowledge_items", type_="unique")
