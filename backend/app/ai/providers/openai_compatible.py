from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

import app.ai.schemas as ai_schemas
from app.ai.providers.base import ProviderAdapter


_FINISH_REASON_MAP = {
    "stop": ai_schemas.FinishReason.STOP,
    "length": ai_schemas.FinishReason.LENGTH,
    "tool_calls": ai_schemas.FinishReason.TOOL_CALL,
    "content_filter": ai_schemas.FinishReason.CONTENT_FILTER,
}


class OpenAICompatibleProvider(ProviderAdapter):
    def __init__(
        self,
        *,
        name: str,
        api_key: str,
        base_url: str,
        capabilities: ai_schemas.ModelCapabilities,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.name = name
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._capabilities = capabilities
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=60.0)

    def capabilities(self, model_id: str) -> ai_schemas.ModelCapabilities:
        return self._capabilities

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _messages(self, request: ai_schemas.ModelRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.extend(
            {
                "role": message.role,
                "content": message.content,
                **({"name": message.name} if message.name else {}),
            }
            for message in request.messages
        )
        return messages

    def _payload(self, request: ai_schemas.ModelRequest, *, stream: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": request.model_id,
            "messages": self._messages(request),
            "stream": stream,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_output_tokens is not None:
            payload["max_tokens"] = request.max_output_tokens
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in request.tools
            ]
        if request.structured_schema is not None and self._capabilities.structured_output:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_response",
                    "schema": request.structured_schema,
                },
            }
        if stream:
            payload["stream_options"] = {"include_usage": True}
        return payload

    @staticmethod
    def _normalize_finish_reason(value: str | None) -> ai_schemas.FinishReason:
        if value is None:
            return ai_schemas.FinishReason.UNKNOWN
        return _FINISH_REASON_MAP.get(value, ai_schemas.FinishReason.UNKNOWN)

    @staticmethod
    def _usage(payload: dict[str, Any] | None) -> ai_schemas.ModelUsage:
        payload = payload or {}
        input_tokens = payload.get("prompt_tokens")
        output_tokens = payload.get("completion_tokens")
        return ai_schemas.ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=payload.get("total_tokens"),
            cached_input_tokens=(
                payload.get("prompt_tokens_details", {}) or {}
            ).get("cached_tokens"),
            reasoning_tokens=(
                payload.get("completion_tokens_details", {}) or {}
            ).get("reasoning_tokens"),
        )

    @staticmethod
    def _tool_calls(message: dict[str, Any]) -> list[ai_schemas.ToolCall]:
        calls: list[ai_schemas.ToolCall] = []
        for item in message.get("tool_calls") or []:
            function = item.get("function") or {}
            raw_arguments = function.get("arguments") or "{}"
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                arguments = {"_raw": raw_arguments}
            calls.append(
                ai_schemas.ToolCall(
                    id=str(item.get("id", "")),
                    name=str(function.get("name", "")),
                    arguments=arguments,
                )
            )
        return calls

    async def generate(self, request: ai_schemas.ModelRequest) -> ai_schemas.ModelResponse:
        response = await self._client.post(
            f"{self._base_url}/chat/completions",
            headers=self._headers(),
            json=self._payload(request, stream=False),
        )
        response.raise_for_status()
        body = response.json()
        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        structured_output = None
        content = message.get("content") or ""
        if request.structured_schema is not None and content:
            try:
                structured_output = json.loads(content)
            except json.JSONDecodeError:
                structured_output = None
        return ai_schemas.ModelResponse(
            request_id=request.request_id,
            model_id=request.model_id,
            provider=self.name,
            content=content,
            tool_calls=self._tool_calls(message),
            structured_output=structured_output,
            usage=self._usage(body.get("usage")),
            finish_reason=self._normalize_finish_reason(choice.get("finish_reason")),
            provider_metadata={"id": body.get("id")},
        )

    async def stream(self, request: ai_schemas.ModelRequest) -> AsyncIterator[ai_schemas.ModelEvent]:
        yield ai_schemas.ModelEvent(
            type="model.started",
            payload={"model_id": request.model_id, "provider": self.name},
        )
        async with self._client.stream(
            "POST",
            f"{self._base_url}/chat/completions",
            headers=self._headers(),
            json=self._payload(request, stream=True),
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if not data or data == "[DONE]":
                    continue
                body = json.loads(data)
                if body.get("usage"):
                    yield ai_schemas.ModelEvent(
                        type="model.usage",
                        payload=self._usage(body["usage"]).model_dump(),
                    )
                for choice in body.get("choices") or []:
                    delta = choice.get("delta") or {}
                    if delta.get("content"):
                        yield ai_schemas.ModelEvent(
                            type="model.text.delta",
                            payload={"delta": delta["content"]},
                        )
                    if choice.get("finish_reason"):
                        yield ai_schemas.ModelEvent(
                            type="model.completed",
                            payload={
                                "finish_reason": self._normalize_finish_reason(
                                    choice["finish_reason"]
                                ).value
                            },
                        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(
                f"{self._base_url}/models",
                headers=self._headers(),
            )
            return response.status_code < 500
        except httpx.HTTPError:
            return False

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
