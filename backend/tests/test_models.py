from app.db.base import Base
from app.db import models  # noqa: F401


def test_expected_tables_are_registered() -> None:
    expected = {
        "providers",
        "models",
        "agents",
        "agent_versions",
        "runs",
        "run_events",
        "tool_calls",
        "evaluation_results",
        "research_items",
        "research_sources",
        "knowledge_items",
        "technologies",
        "capabilities",
        "evidences",
        "capability_evidences",
    }
    assert expected.issubset(set(Base.metadata.tables))
