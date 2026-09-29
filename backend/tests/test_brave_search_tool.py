import httpx
import pytest

from app.tools.web_search import BraveWebSearchTool


@pytest.mark.asyncio
async def test_brave_search_normalizes_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-subscription-token"] == "test-key"
        assert request.url.params["q"] == "LangGraph"
        return httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {
                            "title": "LangGraph",
                            "url": "https://example.com/langgraph",
                            "description": "Graph-based agent orchestration.",
                        }
                    ]
                }
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        tool = BraveWebSearchTool("test-key", client=client)
        result = await tool.execute({"query": "LangGraph"})
    finally:
        await client.aclose()

    assert result["results"][0]["title"] == "LangGraph"
    assert result["results"][0]["url"] == "https://example.com/langgraph"
