import pytest

from app.tools.gateway import MockFetchUrlTool, MockWebSearchTool, ToolGateway


@pytest.mark.asyncio
async def test_mock_web_search_tool() -> None:
    gateway = ToolGateway()
    gateway.register(MockWebSearchTool())

    result = await gateway.execute("web_search", {"query": "LangGraph"})
    assert result["results"]
    assert result["results"][0]["url"].startswith("https://")


@pytest.mark.asyncio
async def test_mock_fetch_url_tool() -> None:
    gateway = ToolGateway()
    gateway.register(MockFetchUrlTool())

    result = await gateway.execute(
        "fetch_url",
        {"url": "https://example.com/source", "title": "Example"},
    )
    assert result["url"] == "https://example.com/source"
    assert "Mock fetched content" in result["content"]


@pytest.mark.asyncio
async def test_mock_fetch_url_rejects_relative_url() -> None:
    gateway = ToolGateway()
    gateway.register(MockFetchUrlTool())

    with pytest.raises(ValueError):
        await gateway.execute("fetch_url", {"url": "/relative"})


@pytest.mark.asyncio
async def test_unregistered_tool_is_denied() -> None:
    gateway = ToolGateway()

    with pytest.raises(KeyError):
        await gateway.execute("shell", {})
