import pytest

from app.ai.gateway import ModelGateway
from app.ai.providers.mock import MockProvider
from app.ai.registry import ModelRegistry, RegisteredModel
from app.ai.schemas import ChatMessage, ModelRequest


def build_gateway() -> ModelGateway:
    provider = MockProvider(response_text="hello world")
    registry = ModelRegistry()
    registry.register(
        RegisteredModel(
            id="mock/test",
            provider="mock",
            model_key="test",
            display_name="Test",
            capabilities=provider.capabilities("test"),
        )
    )
    gateway = ModelGateway(registry)
    gateway.register_provider(provider)
    return gateway


@pytest.mark.asyncio
async def test_generate_uses_registered_provider() -> None:
    gateway = build_gateway()
    request = ModelRequest(
        model_id="mock/test",
        messages=[ChatMessage(role="user", content="hi")],
    )
    response = await gateway.generate(request)
    assert response.provider == "mock"
    assert response.content == "hello world"
    assert response.usage.total_tokens is not None


@pytest.mark.asyncio
async def test_stream_normalizes_events() -> None:
    gateway = build_gateway()
    request = ModelRequest(
        model_id="mock/test",
        messages=[ChatMessage(role="user", content="hi")],
        stream=True,
    )
    events = [event async for event in gateway.stream(request)]
    assert events[0].type == "model.started"
    assert any(event.type == "model.text.delta" for event in events)
    assert events[-1].type == "model.completed"
