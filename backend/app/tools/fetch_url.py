from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin

import httpx

from app.tools.gateway import Tool
from app.tools.security import validate_public_http_url


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)

    def text(self) -> str:
        return " ".join(self.parts)


def _html_title(content: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(.*?)</title>",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    return unescape(re.sub(r"\s+", " ", match.group(1)).strip())


def _html_text(content: str) -> str:
    parser = _TextExtractor()
    parser.feed(content)
    return unescape(parser.text())


class FetchUrlTool(Tool):
    name = "fetch_url"
    risk_level = "LOW"

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        max_bytes: int = 1_000_000,
        max_redirects: int = 3,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=False,
        )
        self._max_bytes = max_bytes
        self._max_redirects = max_redirects

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        current_url = str(arguments.get("url", "")).strip()
        if not current_url:
            raise ValueError("fetch_url requires a URL")

        for redirect_index in range(self._max_redirects + 1):
            await validate_public_http_url(current_url)
            async with self._client.stream(
                "GET",
                current_url,
                headers={
                    "User-Agent": "PersonalAIEngineeringWorkspace/0.1",
                    "Accept": (
                        "text/html,text/plain,application/json;q=0.9,*/*;q=0.1"
                    ),
                },
            ) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Redirect response is missing Location")
                    if redirect_index >= self._max_redirects:
                        raise ValueError("Too many redirects")
                    current_url = urljoin(current_url, location)
                    continue

                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                allowed = (
                    content_type.startswith("text/")
                    or "application/json" in content_type
                    or "application/xml" in content_type
                )
                if not allowed:
                    raise ValueError(
                        f"Unsupported content type: {content_type or 'unknown'}"
                    )

                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > self._max_bytes:
                        raise ValueError("Fetched document exceeds size limit")
                    chunks.append(chunk)

                raw = b"".join(chunks)
                encoding = response.encoding or "utf-8"
                content = raw.decode(encoding, errors="replace")
                if "html" in content_type:
                    title = _html_title(content)
                    text = _html_text(content)
                else:
                    title = None
                    text = content

                return {
                    "url": str(response.url),
                    "title": title or arguments.get("title"),
                    "content": text[:100_000],
                    "content_type": content_type,
                }

        raise ValueError("Unable to fetch URL")
