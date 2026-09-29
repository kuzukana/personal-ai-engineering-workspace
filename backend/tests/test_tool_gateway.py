import pytest

from app.tools.gateway import MockWebSearchTool, ToolGateway


@pytest.mark.asyncio
async def test_mock_web_search_tool() -> None:
    gateway = ToolGateway()
    gateway.register(MockWebSearchTool())

    result = await gateway.execute("web_search", {"query": "LangGraph"})
    assert result["results"]
    assert result["results"][0]["url"].startswith("https://")


@pytest.mark.asyncio
async def test_unregistered_tool_is_denied() -> None:
    gateway = ToolGateway()

    with pytest.raises(KeyError):
        await gateway.execute("shell", {})
