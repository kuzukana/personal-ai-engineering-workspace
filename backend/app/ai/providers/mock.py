from __future__ import annotations

from collections.abc import AsyncIterator

from app.ai.providers.base import ProviderAdapter
from app.ai.schemas import (
    FinishReason,
    ModelCapabilities,
    ModelEvent,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)


class MockProvider(ProviderAdapter):
    name = "mock"

    def __init__(self, response_text: str = "Mock response") -> None:
        self.response_text = response_text

    def capabilities(self, model_id: str) -> ModelCapabilities:
        return ModelCapabilities(
            streaming=True,
            tools=True,
            structured_output=True,
            reasoning=False,
            context_window=32_000,
            max_output_tokens=4_096,
        )

    async def generate(self, request: ModelRequest) -> ModelResponse:
        usage = ModelUsage(
            input_tokens=10,
            output_tokens=max(1, len(self.response_text.split())),
            total_tokens=10 + max(1, len(self.response_text.split())),
            estimated_cost=0.0,
            currency="USD",
        )
        structured = None
        if request.structured_schema is not None:
            structured = {"mock": True, "content": self.response_text}
        return ModelResponse(
            request_id=request.request_id,
            model_id=request.model_id,
            provider=self.name,
            content=self.response_text,
            structured_output=structured,
            usage=usage,
            finish_reason=FinishReason.STOP,
            latency_ms=1,
        )

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        yield ModelEvent(type="model.started", payload={"model_id": request.model_id})
        for chunk in self.response_text.split(" "):
            yield ModelEvent(type="model.text.delta", payload={"delta": chunk + " "})
        yield ModelEvent(
            type="model.usage",
            payload={"input_tokens": 10, "output_tokens": len(self.response_text.split())},
        )
        yield ModelEvent(type="model.completed", payload={"finish_reason": "STOP"})
