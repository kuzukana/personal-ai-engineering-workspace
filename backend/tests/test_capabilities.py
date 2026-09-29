import pytest
from pydantic import ValidationError

from app.api.routes.capabilities import CapabilityUpdate, slugify_technology


def test_slugify_technology() -> None:
    assert slugify_technology(" LangGraph / Agents ") == "langgraph-agents"


def test_slugify_technology_rejects_empty_slug() -> None:
    with pytest.raises(ValueError):
        slugify_technology("___")


def test_capability_level_is_bounded() -> None:
    with pytest.raises(ValidationError):
        CapabilityUpdate(level=6)
