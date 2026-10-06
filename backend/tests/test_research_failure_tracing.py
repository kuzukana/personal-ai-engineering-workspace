from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.agents.research import agent as research_module
from app.domain.constants import MOCK_MODEL_ID


async def _capture_events(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(research_module.run_control, "checkpoint", AsyncMock())

    async def fake_emit(
        session,
        run_id,
        event_type: str,
        source: str,
        payload: dict | None = None,
    ):
        events.append((event_type, payload or {}))
        return None

    monkeypatch.setattr(research_module.event_publisher, "emit", fake_emit)
    return events


@pytest.mark.asyncio
async def test_research_agent_traces_tool_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    events = await _capture_events(monkeypatch)

    async def fail_tool(tool_name: str, arguments: dict) -> dict:
        assert tool_name == "web_search"
        raise RuntimeError("search unavailable")

    monkeypatch.setattr(research_module.tool_gateway, "execute", fail_tool)

    with pytest.raises(RuntimeError, match="search unavailable"):
        await research_module.ResearchAgent().run(
            session=object(),
            run_id=uuid4(),
            query="Compare two agent frameworks",
            model_id=str(MOCK_MODEL_ID),
        )

    event_types = [event_type for event_type, _ in events]
    assert "tool.failed" in event_types
    assert "agent.step.failed" in event_types

    tool_failure = next(payload for event_type, payload in events if event_type == "tool.failed")
    assert tool_failure["tool_name"] == "web_search"
    assert tool_failure["error_code"] == "RUNTIMEERROR"

    step_failure = next(
        payload for event_type, payload in events if event_type == "agent.step.failed"
    )
    assert step_failure["step_key"] == "search"
    assert step_failure["step_index"] == 3


@pytest.mark.asyncio
async def test_research_agent_traces_model_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    events = await _capture_events(monkeypatch)

    async def fake_tool(tool_name: str, arguments: dict) -> dict:
        if tool_name == "web_search":
            return {
                "results": [
                    {
                        "url": "https://example.com/source",
                        "title": "Example source",
                        "snippet": "Useful evidence",
                        "source_type": "OTHER",
                    }
                ]
            }
        if tool_name == "fetch_url":
            return {
                "url": arguments["url"],
                "title": arguments.get("title"),
                "content": "Useful evidence",
            }
        raise AssertionError(f"Unexpected tool: {tool_name}")

    async def fail_model(request):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(research_module.tool_gateway, "execute", fake_tool)
    monkeypatch.setattr(research_module.model_gateway, "generate", fail_model)

    with pytest.raises(RuntimeError, match="provider unavailable"):
        await research_module.ResearchAgent().run(
            session=object(),
            run_id=uuid4(),
            query="Compare two agent frameworks",
            model_id=str(MOCK_MODEL_ID),
        )

    event_types = [event_type for event_type, _ in events]
    assert "model.failed" in event_types
    assert "agent.step.failed" in event_types

    model_failure = next(payload for event_type, payload in events if event_type == "model.failed")
    assert model_failure["error_code"] == "RUNTIMEERROR"

    step_failure = next(
        payload for event_type, payload in events if event_type == "agent.step.failed"
    )
    assert step_failure["step_key"] == "synthesize"
    assert step_failure["step_index"] == 8
