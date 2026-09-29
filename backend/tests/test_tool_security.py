import pytest

from app.tools.security import validate_public_http_url


@pytest.mark.asyncio
async def test_public_literal_ip_is_allowed() -> None:
    assert await validate_public_http_url("https://8.8.8.8/example") == (
        "https://8.8.8.8/example"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]",
        "file:///etc/passwd",
    ],
)
async def test_private_and_non_http_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        await validate_public_http_url(url)
