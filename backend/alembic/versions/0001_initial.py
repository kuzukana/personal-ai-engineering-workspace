"""Initial core schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "providers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("provider_type", sa.String(80), nullable=False),
        sa.Column("base_url", sa.Text()),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("config_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "models",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("model_key", sa.String(160), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("supports_streaming", sa.Boolean(), nullable=False),
        sa.Column("supports_tools", sa.Boolean(), nullable=False),
        sa.Column("supports_parallel_tools", sa.Boolean(), nullable=False),
        sa.Column("supports_structured_output", sa.Boolean(), nullable=False),
        sa.Column("supports_vision", sa.Boolean(), nullable=False),
        sa.Column("supports_reasoning", sa.Boolean(), nullable=False),
        sa.Column("supports_system_prompt", sa.Boolean(), nullable=False),
        sa.Column("context_window", sa.Integer()),
        sa.Column("max_output_tokens", sa.Integer()),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider_id", "model_key"),
    )
    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agent_key", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("purpose", sa.Text()),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agent_id", sa.Uuid(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("runtime_type", sa.String(80), nullable=False),
        sa.Column("workflow_key", sa.String(120), nullable=False),
        sa.Column("system_prompt_version", sa.String(120)),
        sa.Column("model_policy_json", sa.JSON(), nullable=False),
        sa.Column("tool_policy_json", sa.JSON(), nullable=False),
        sa.Column("memory_policy_json", sa.JSON(), nullable=False),
        sa.Column("permission_policy_json", sa.JSON(), nullable=False),
        sa.Column("evaluation_policy_json", sa.JSON(), nullable=False),
        sa.Column("config_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("agent_id", "version"),
    )
    op.create_table(
        "runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("agent_version_id", sa.Uuid(), sa.ForeignKey("agent_versions.id"), nullable=False),
        sa.Column("model_id", sa.Uuid(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("task_type", sa.String(80)),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text()),
        sa.Column("structured_output_json", sa.JSON()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("latency_ms", sa.BigInteger()),
        sa.Column("input_tokens", sa.BigInteger()),
        sa.Column("output_tokens", sa.BigInteger()),
        sa.Column("reasoning_tokens", sa.BigInteger()),
        sa.Column("estimated_cost", sa.Numeric(18, 8)),
        sa.Column("currency", sa.String(8)),
        sa.Column("error_code", sa.String(80)),
        sa.Column("error_message", sa.Text()),
        sa.Column("warnings_json", sa.JSON()),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runs_status", "runs", ["status"])
    op.create_table(
        "run_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("payload_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "sequence"),
    )
    op.create_index("ix_run_events_run_id", "run_events", ["run_id"])
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("tool_call_id", sa.String(160)),
        sa.Column("tool_name", sa.String(120), nullable=False),
        sa.Column("tool_version", sa.String(40)),
        sa.Column("risk_level", sa.String(16)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("input_json", sa.JSON()),
        sa.Column("output_json", sa.JSON()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("latency_ms", sa.BigInteger()),
        sa.Column("error_code", sa.String(80)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tool_calls_run_id", "tool_calls", ["run_id"])
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("evaluation_type", sa.String(40), nullable=False),
        sa.Column("metric_name", sa.String(120), nullable=False),
        sa.Column("evaluator_key", sa.String(120), nullable=False),
        sa.Column("evaluator_version", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("score", sa.Numeric(12, 4)),
        sa.Column("value_json", sa.JSON()),
        sa.Column("evidence_json", sa.JSON()),
        sa.Column("judge_model_id", sa.Uuid(), sa.ForeignKey("models.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluation_results_run_id", "evaluation_results", ["run_id"])
    op.create_table(
        "research_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("runs.id")),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("report_markdown", sa.Text()),
        sa.Column("structured_result_json", sa.JSON()),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "research_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("research_item_id", sa.Uuid(), sa.ForeignKey("research_items.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("domain", sa.String(255)),
        sa.Column("source_type", sa.String(40)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("relevance_score", sa.Numeric(8, 4)),
        sa.Column("verification_status", sa.String(40)),
        sa.Column("content_excerpt", sa.Text()),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_research_sources_research_item_id", "research_sources", ["research_item_id"])
    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("knowledge_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("content_markdown", sa.Text()),
        sa.Column("source_research_id", sa.Uuid(), sa.ForeignKey("research_items.id")),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "technologies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False, unique=True),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("category", sa.String(80)),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "capabilities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("technology_id", sa.Uuid(), sa.ForeignKey("technologies.id"), nullable=False, unique=True),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("next_target_level", sa.SmallInteger()),
        sa.Column("next_action", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("level >= 0 AND level <= 5", name="ck_capability_level"),
    )
    op.create_table(
        "evidences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("evidence_type", sa.String(48), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("url", sa.Text()),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "capability_evidences",
        sa.Column("capability_id", sa.Uuid(), sa.ForeignKey("capabilities.id"), primary_key=True),
        sa.Column("evidence_id", sa.Uuid(), sa.ForeignKey("evidences.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for name in [
        "capability_evidences", "evidences", "capabilities", "technologies",
        "knowledge_items", "research_sources", "research_items", "evaluation_results",
        "tool_calls", "run_events", "runs", "agent_versions", "agents", "models", "providers"
    ]:
        op.drop_table(name)
