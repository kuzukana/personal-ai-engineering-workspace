from __future__ import annotations

from typing import Any

import httpx

from app.tools.gateway import Tool


class BraveWebSearchTool(Tool):
    name = "web_search"
    risk_level = "LOW"
    endpoint = "https://api.search.brave.com/res/v1/web/search"

    def __init__(
        self,
        api_key: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ValueError("web_search requires a query")

        count = int(arguments.get("count", 10))
        count = max(1, min(count, 20))
        response = await self._client.get(
            self.endpoint,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self._api_key,
            },
            params={"q": query, "count": count},
        )
        response.raise_for_status()
        body = response.json()
        results = []
        for item in (body.get("web") or {}).get("results") or []:
            url = item.get("url")
            title = item.get("title")
            if not url or not title:
                continue
            results.append(
                {
                    "url": url,
                    "title": title,
                    "snippet": item.get("description"),
                    "source_type": "OTHER",
                }
            )
        return {"results": results}
