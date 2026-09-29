from app.ai.gateway import ModelGateway
from app.ai.providers.mock import MockProvider
from app.ai.providers.openai_compatible import OpenAICompatibleProvider
from app.ai.registry import ModelRegistry, RegisteredModel
from app.ai.schemas import ModelCapabilities
from app.core.config import get_settings
from app.domain.constants import MOCK_MODEL_ID, configured_model_id


def _register_configured_model(
    *,
    gateway: ModelGateway,
    registry: ModelRegistry,
    provider_name: str,
    api_key: str | None,
    model_key: str | None,
    base_url: str | None,
    display_name: str,
    capabilities: ModelCapabilities,
) -> None:
    if not api_key or not model_key or not base_url:
        return

    provider = OpenAICompatibleProvider(
        name=provider_name,
        api_key=api_key,
        base_url=base_url,
        capabilities=capabilities,
    )
    model_id = configured_model_id(provider_name, model_key)
    registry.register(
        RegisteredModel(
            id=str(model_id),
            provider=provider_name,
            model_key=model_key,
            display_name=display_name,
            capabilities=capabilities,
        )
    )
    gateway.register_provider(provider)


def build_model_gateway() -> ModelGateway:
    settings = get_settings()
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

    _register_configured_model(
        gateway=gateway,
        registry=registry,
        provider_name="openai",
        api_key=settings.openai_api_key,
        model_key=settings.openai_model,
        base_url=settings.openai_base_url,
        display_name=f"OpenAI · {settings.openai_model}" if settings.openai_model else "OpenAI",
        capabilities=ModelCapabilities(
            streaming=True,
            tools=True,
            structured_output=True,
            system_prompt=True,
        ),
    )
    _register_configured_model(
        gateway=gateway,
        registry=registry,
        provider_name="deepseek",
        api_key=settings.deepseek_api_key,
        model_key=settings.deepseek_model,
        base_url=settings.deepseek_base_url,
        display_name=(
            f"DeepSeek · {settings.deepseek_model}" if settings.deepseek_model else "DeepSeek"
        ),
        capabilities=ModelCapabilities(
            streaming=True,
            tools=False,
            structured_output=False,
            system_prompt=True,
        ),
    )
    _register_configured_model(
        gateway=gateway,
        registry=registry,
        provider_name="kimi",
        api_key=settings.kimi_api_key,
        model_key=settings.kimi_model,
        base_url=settings.kimi_base_url,
        display_name=f"Kimi · {settings.kimi_model}" if settings.kimi_model else "Kimi",
        capabilities=ModelCapabilities(
            streaming=True,
            tools=False,
            structured_output=False,
            system_prompt=True,
        ),
    )
    return gateway


model_gateway = build_model_gateway()
