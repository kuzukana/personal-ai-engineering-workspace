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
            id="internal-model-id",
            provider="mock",
            model_key="vendor-model-key",
            display_name="Test",
            capabilities=provider.capabilities("vendor-model-key"),
        )
    )
    gateway = ModelGateway(registry)
    gateway.register_provider(provider)
    return gateway


@pytest.mark.asyncio
async def test_generate_uses_registered_provider_and_preserves_internal_id() -> None:
    gateway = build_gateway()
    request = ModelRequest(
        model_id="internal-model-id",
        messages=[ChatMessage(role="user", content="hi")],
    )
    response = await gateway.generate(request)
    assert response.provider == "mock"
    assert response.content == "hello world"
    assert response.model_id == "internal-model-id"
    assert response.usage.total_tokens is not None


@pytest.mark.asyncio
async def test_stream_normalizes_events_and_internal_model_id() -> None:
    gateway = build_gateway()
    request = ModelRequest(
        model_id="internal-model-id",
        messages=[ChatMessage(role="user", content="hi")],
        stream=True,
    )
    events = [event async for event in gateway.stream(request)]
    assert events[0].type == "model.started"
    assert events[0].payload["model_id"] == "internal-model-id"
    assert any(event.type == "model.text.delta" for event in events)
    assert events[-1].type == "model.completed"
