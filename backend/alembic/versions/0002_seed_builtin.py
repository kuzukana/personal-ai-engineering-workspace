"""Seed built-in mock model and research agent.

Revision ID: 0002_seed_builtin
Revises: 0001_initial
Create Date: 2026-09-29
"""

from datetime import datetime, timezone
from uuid import UUID

from alembic import op

from app.db.models import Agent, AgentVersion, Model, Provider

revision = "0002_seed_builtin"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

PROVIDER_ID = UUID("00000000-0000-0000-0000-000000000001")
MODEL_ID = UUID("00000000-0000-0000-0000-000000000002")
AGENT_ID = UUID("00000000-0000-0000-0000-000000000003")
AGENT_VERSION_ID = UUID("00000000-0000-0000-0000-000000000004")


def upgrade() -> None:
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        Provider.__table__,
        [
            {
                "id": PROVIDER_ID,
                "name": "Mock",
                "provider_type": "mock",
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )
    op.bulk_insert(
        Model.__table__,
        [
            {
                "id": MODEL_ID,
                "provider_id": PROVIDER_ID,
                "model_key": "mock-1",
                "display_name": "Mock Model",
                "status": "ACTIVE",
                "supports_streaming": True,
                "supports_tools": True,
                "supports_parallel_tools": False,
                "supports_structured_output": True,
                "supports_vision": False,
                "supports_reasoning": False,
                "supports_system_prompt": True,
                "context_window": 32000,
                "max_output_tokens": 4096,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )
    op.bulk_insert(
        Agent.__table__,
        [
            {
                "id": AGENT_ID,
                "agent_key": "research-agent",
                "name": "Research Agent",
                "description": "Source-backed technical research workflow",
                "purpose": "Research, verify and synthesize technical information",
                "status": "ACTIVE",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )
    op.bulk_insert(
        AgentVersion.__table__,
        [
            {
                "id": AGENT_VERSION_ID,
                "agent_id": AGENT_ID,
                "version": "0.1",
                "runtime_type": "langgraph",
                "workflow_key": "research-v1",
                "system_prompt_version": "research-system-v1",
                "model_policy_json": {
                    "required": ["streaming", "structured_output"]
                },
                "tool_policy_json": {"allow": ["web_search"]},
                "memory_policy_json": {"write": "suggest_only"},
                "permission_policy_json": {"max_risk": "LOW"},
                "evaluation_policy_json": {
                    "evaluator": "research-deterministic"
                },
                "created_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        AgentVersion.__table__.delete().where(
            AgentVersion.id == AGENT_VERSION_ID
        )
    )
    op.execute(Agent.__table__.delete().where(Agent.id == AGENT_ID))
    op.execute(Model.__table__.delete().where(Model.id == MODEL_ID))
    op.execute(Provider.__table__.delete().where(Provider.id == PROVIDER_ID))
