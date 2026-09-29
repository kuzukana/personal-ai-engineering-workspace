from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.ai.schemas import ModelCapabilities, ModelEvent, ModelRequest, ModelResponse


class ProviderAdapter(ABC):
    name: str

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        if False:
            yield ModelEvent(type="noop")
        raise NotImplementedError

    @abstractmethod
    def capabilities(self, model_id: str) -> ModelCapabilities:
        raise NotImplementedError

    async def health_check(self) -> bool:
        return True
