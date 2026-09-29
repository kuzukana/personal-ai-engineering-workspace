import httpx
import pytest

from app.tools.fetch_url import FetchUrlTool


@pytest.mark.asyncio
async def test_fetch_url_extracts_html_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=(
                "<html><head><title>Example</title></head>"
                "<body>Hello world</body></html>"
            ),
            headers={"content-type": "text/html; charset=utf-8"},
            request=request,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        tool = FetchUrlTool(client=client)
        result = await tool.execute({"url": "https://8.8.8.8/page"})
    finally:
        await client.aclose()

    assert result["title"] == "Example"
    assert "Hello world" in result["content"]


@pytest.mark.asyncio
async def test_fetch_url_rejects_redirect_to_private_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "http://127.0.0.1/private"},
            request=request,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        tool = FetchUrlTool(client=client)
        with pytest.raises(ValueError):
            await tool.execute({"url": "https://8.8.8.8/page"})
    finally:
        await client.aclose()
