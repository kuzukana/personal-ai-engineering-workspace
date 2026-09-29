from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    name: str
    risk_level: str = "LOW"

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class MockWebSearchTool(Tool):
    name = "web_search"

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", ""))
        return {
            "results": [
                {
                    "url": "https://example.com/mock-source",
                    "title": "Mock research source",
                    "snippet": f"Mock source for: {query}",
                    "source_type": "OTHER",
                }
            ]
        }


class ToolGateway:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            tool = self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Tool is not allowed or registered: {tool_name}") from exc
        return await tool.execute(arguments)


tool_gateway = ToolGateway()
tool_gateway.register(MockWebSearchTool())
