from __future__ import annotations

from collections.abc import AsyncIterator

from app.ai.providers.base import ProviderAdapter
from app.ai.registry import ModelRegistry
from app.ai.schemas import ModelEvent, ModelRequest, ModelResponse


class ModelGateway:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
        self.providers: dict[str, ProviderAdapter] = {}

    def register_provider(self, provider: ProviderAdapter) -> None:
        self.providers[provider.name] = provider

    def _provider_for(self, model_id: str) -> ProviderAdapter:
        model = self.registry.get(model_id)
        if not model.enabled:
            raise ValueError(f"Model is disabled: {model_id}")
        try:
            return self.providers[model.provider]
        except KeyError as exc:
            raise RuntimeError(f"Provider is not registered: {model.provider}") from exc

    async def generate(self, request: ModelRequest) -> ModelResponse:
        provider = self._provider_for(request.model_id)
        return await provider.generate(request)

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        provider = self._provider_for(request.model_id)
        async for event in provider.stream(request):
            yield event
