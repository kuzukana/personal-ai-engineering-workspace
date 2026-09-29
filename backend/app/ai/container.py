from app.ai.gateway import ModelGateway
from app.ai.providers.mock import MockProvider
from app.ai.registry import ModelRegistry, RegisteredModel
from app.domain.constants import MOCK_MODEL_ID


def build_model_gateway() -> ModelGateway:
    registry = ModelRegistry()
    mock = MockProvider()
    registry.register(
        RegisteredModel(
            id=str(MOCK_MODEL_ID),
            provider="mock",
            model_key="mock-1",
            display_name="Mock Model",
            capabilities=mock.capabilities("mock-1"),
        )
    )
    gateway = ModelGateway(registry)
    gateway.register_provider(mock)
    return gateway


model_gateway = build_model_gateway()
