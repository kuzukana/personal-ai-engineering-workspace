import json

import httpx
import pytest

from app.ai.providers.openai_compatible import OpenAICompatibleProvider
from app.ai.schemas import ChatMessage, ModelCapabilities, ModelRequest


def build_provider(handler) -> tuple[OpenAICompatibleProvider, httpx.AsyncClient]:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    provider = OpenAICompatibleProvider(
        name="test-provider",
        api_key="test-key",
        base_url="https://example.test/v1",
        capabilities=ModelCapabilities(
            streaming=True,
            tools=True,
            structured_output=True,
        ),
        client=client,
    )
    return provider, client


@pytest.mark.asyncio
async def test_generate_normalizes_openai_compatible_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == "vendor-model"
        return httpx.Response(
            200,
            json={
                "id": "response-1",
                "choices": [
                    {
                        "message": {"content": "hello", "tool_calls": []},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 4,
                    "completion_tokens": 2,
                    "total_tokens": 6,
                },
            },
        )

    provider, client = build_provider(handler)
    try:
        response = await provider.generate(
            ModelRequest(
                model_id="vendor-model",
                messages=[ChatMessage(role="user", content="hi")],
            )
        )
    finally:
        await client.aclose()

    assert response.provider == "test-provider"
    assert response.content == "hello"
    assert response.usage.total_tokens == 6
    assert response.finish_reason.value == "STOP"


@pytest.mark.asyncio
async def test_stream_normalizes_text_and_usage_events() -> None:
    payload = "\n".join(
        [
            'data: {"choices":[{"delta":{"content":"hello "},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{"content":"world"},"finish_reason":"stop"}]}',
            (
                'data: {"choices":[],"usage":{"prompt_tokens":3,'
                '"completion_tokens":2,"total_tokens":5}}'
            ),
            "data: [DONE]",
            "",
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=payload,
            headers={"content-type": "text/event-stream"},
        )

    provider, client = build_provider(handler)
    try:
        events = [
            event
            async for event in provider.stream(
                ModelRequest(
                    model_id="vendor-model",
                    messages=[ChatMessage(role="user", content="hi")],
                    stream=True,
                )
            )
        ]
    finally:
        await client.aclose()

    assert events[0].type == "model.started"
    deltas = [event.payload["delta"] for event in events if event.type == "model.text.delta"]
    assert "".join(deltas) == "hello world"
    usage = next(event for event in events if event.type == "model.usage")
    assert usage.payload["total_tokens"] == 5
    assert any(event.type == "model.completed" for event in events)
