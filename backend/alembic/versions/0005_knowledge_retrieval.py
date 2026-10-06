"""Versioned Knowledge chunks and embeddings for exact local retrieval."""

import sqlalchemy as sa

from alembic import op

revision = "0005_knowledge_retrieval"
down_revision = "0004_knowledge_source_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_indexes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "knowledge_id",
            sa.Uuid(),
            sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("profile", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("knowledge_id", "profile", name="uq_knowledge_index_profile"),
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "index_id",
            sa.Uuid(),
            sa.ForeignKey("knowledge_indexes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.UniqueConstraint("index_id", "ordinal", name="uq_knowledge_chunk_ordinal"),
    )
    op.create_index("ix_knowledge_chunks_index_id", "knowledge_chunks", ["index_id"])


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_indexes")
