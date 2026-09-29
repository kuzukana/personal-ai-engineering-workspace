from __future__ import annotations

from collections.abc import AsyncIterator

from app.ai.providers.base import ProviderAdapter
from app.ai.registry import ModelRegistry, RegisteredModel
from app.ai.schemas import ModelEvent, ModelRequest, ModelResponse


class ModelGateway:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
        self.providers: dict[str, ProviderAdapter] = {}

    def register_provider(self, provider: ProviderAdapter) -> None:
        self.providers[provider.name] = provider

    def _resolve(self, model_id: str) -> tuple[RegisteredModel, ProviderAdapter]:
        model = self.registry.get(model_id)
        if not model.enabled:
            raise ValueError(f"Model is disabled: {model_id}")
        try:
            provider = self.providers[model.provider]
        except KeyError as exc:
            raise RuntimeError(f"Provider is not registered: {model.provider}") from exc
        return model, provider

    async def generate(self, request: ModelRequest) -> ModelResponse:
        model, provider = self._resolve(request.model_id)
        provider_request = request.model_copy(update={"model_id": model.model_key})
        response = await provider.generate(provider_request)
        return response.model_copy(update={"model_id": request.model_id})

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        model, provider = self._resolve(request.model_id)
        provider_request = request.model_copy(update={"model_id": model.model_key})
        async for event in provider.stream(provider_request):
            payload = dict(event.payload)
            if payload.get("model_id") == model.model_key:
                payload["model_id"] = request.model_id
            yield event.model_copy(update={"payload": payload})
