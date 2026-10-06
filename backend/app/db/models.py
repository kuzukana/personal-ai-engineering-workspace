from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def uuid_pk() -> Mapped[UUID]:
    return mapped_column(primary_key=True, default=uuid4)


def now_col() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Provider(Base):
    __tablename__ = "providers"
    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), unique=True)
    provider_type: Mapped[str] = mapped_column(String(80))
    base_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    config_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = now_col()
    updated_at: Mapped[datetime] = now_col()


class Model(Base):
    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("provider_id", "model_key"),)
    id: Mapped[UUID] = uuid_pk()
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("providers.id"))
    model_key: Mapped[str] = mapped_column(String(160))
    display_name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_tools: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_parallel_tools: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_structured_output: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_reasoning: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_system_prompt: Mapped[bool] = mapped_column(Boolean, default=True)
    context_window: Mapped[int | None]
    max_output_tokens: Mapped[int | None]
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = now_col()
    updated_at: Mapped[datetime] = now_col()


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[UUID] = uuid_pk()
    agent_key: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    purpose: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = now_col()
    updated_at: Mapped[datetime] = now_col()


class AgentVersion(Base):
    __tablename__ = "agent_versions"
    __table_args__ = (UniqueConstraint("agent_id", "version"),)
    id: Mapped[UUID] = uuid_pk()
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id"))
    version: Mapped[str] = mapped_column(String(40))
    runtime_type: Mapped[str] = mapped_column(String(80))
    workflow_key: Mapped[str] = mapped_column(String(120))
    system_prompt_version: Mapped[str | None] = mapped_column(String(120))
    model_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    tool_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    memory_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    permission_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    evaluation_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    config_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = now_col()


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[UUID] = uuid_pk()
    agent_version_id: Mapped[UUID] = mapped_column(ForeignKey("agent_versions.id"))
    model_id: Mapped[UUID] = mapped_column(ForeignKey("models.id"))
    status: Mapped[str] = mapped_column(String(40), default="PENDING", index=True)
    task_type: Mapped[str | None] = mapped_column(String(80))
    input_text: Mapped[str] = mapped_column(Text)
    output_text: Mapped[str | None] = mapped_column(Text)
    structured_output_json: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int | None] = mapped_column(BigInteger)
    input_tokens: Mapped[int | None] = mapped_column(BigInteger)
    output_tokens: Mapped[int | None] = mapped_column(BigInteger)
    reasoning_tokens: Mapped[int | None] = mapped_column(BigInteger)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    currency: Mapped[str | None] = mapped_column(String(8))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    warnings_json: Mapped[list | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = now_col()


class RunEvent(Base):
    __tablename__ = "run_events"
    __table_args__ = (UniqueConstraint("run_id", "sequence"),)
    id: Mapped[UUID] = uuid_pk()
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), index=True)
    sequence: Mapped[int] = mapped_column(BigInteger)
    event_type: Mapped[str] = mapped_column(String(120))
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = now_col()


class ToolCall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[UUID] = uuid_pk()
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), index=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(160))
    tool_name: Mapped[str] = mapped_column(String(120))
    tool_version: Mapped[str | None] = mapped_column(String(40))
    risk_level: Mapped[str | None] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32))
    input_json: Mapped[dict | None] = mapped_column(JSON)
    output_json: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int | None] = mapped_column(BigInteger)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_col()


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[UUID] = uuid_pk()
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), index=True)
    evaluation_type: Mapped[str] = mapped_column(String(40))
    metric_name: Mapped[str] = mapped_column(String(120))
    evaluator_key: Mapped[str] = mapped_column(String(120))
    evaluator_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40))
    score: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    value_json: Mapped[dict | None] = mapped_column(JSON)
    evidence_json: Mapped[dict | None] = mapped_column(JSON)
    judge_model_id: Mapped[UUID | None] = mapped_column(ForeignKey("models.id"))
    created_at: Mapped[datetime] = now_col()


class ResearchItem(Base):
    __tablename__ = "research_items"
    id: Mapped[UUID] = uuid_pk()
    run_id: Mapped[UUID | None] = mapped_column(ForeignKey("runs.id"))
    title: Mapped[str] = mapped_column(String(240))
    query: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    report_markdown: Mapped[str | None] = mapped_column(Text)
    structured_result_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    created_at: Mapped[datetime] = now_col()
    updated_at: Mapped[datetime] = now_col()


class ResearchSource(Base):
    __tablename__ = "research_sources"
    id: Mapped[UUID] = uuid_pk()
    research_item_id: Mapped[UUID] = mapped_column(ForeignKey("research_items.id"), index=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(255))
    source_type: Mapped[str | None] = mapped_column(String(40))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    verification_status: Mapped[str | None] = mapped_column(String(40))
    content_excerpt: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = now_col()


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    __table_args__ = (UniqueConstraint("source_research_id", name="uq_knowledge_source"),)
    id: Mapped[UUID] = uuid_pk()
    knowledge_type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str | None] = mapped_column(Text)
    content_markdown: Mapped[str | None] = mapped_column(Text)
    source_research_id: Mapped[UUID | None] = mapped_column(ForeignKey("research_items.id"))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = now_col()
    updated_at: Mapped[datetime] = now_col()


class Technology(Base):
    __tablename__ = "technologies"
    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(160), unique=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True)
    category: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_col()
    updated_at: Mapped[datetime] = now_col()


class KnowledgeTechnology(Base):
    __tablename__ = "knowledge_technologies"
    knowledge_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_items.id"),
        primary_key=True,
    )
    technology_id: Mapped[UUID] = mapped_column(
        ForeignKey("technologies.id"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = now_col()


class Capability(Base):
    __tablename__ = "capabilities"
    __table_args__ = (CheckConstraint("level >= 0 AND level <= 5", name="ck_capability_level"),)
    id: Mapped[UUID] = uuid_pk()
    technology_id: Mapped[UUID] = mapped_column(ForeignKey("technologies.id"), unique=True)
    level: Mapped[int] = mapped_column(SmallInteger)
    reason: Mapped[str | None] = mapped_column(Text)
    next_target_level: Mapped[int | None] = mapped_column(SmallInteger)
    next_action: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_col()
    updated_at: Mapped[datetime] = now_col()


class Evidence(Base):
    __tablename__ = "evidences"
    id: Mapped[UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String(240))
    evidence_type: Mapped[str] = mapped_column(String(48))
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = now_col()
    updated_at: Mapped[datetime] = now_col()


class CapabilityEvidence(Base):
    __tablename__ = "capability_evidences"
    capability_id: Mapped[UUID] = mapped_column(ForeignKey("capabilities.id"), primary_key=True)
    evidence_id: Mapped[UUID] = mapped_column(ForeignKey("evidences.id"), primary_key=True)
    created_at: Mapped[datetime] = now_col()
