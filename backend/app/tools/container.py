from app.core.config import get_settings
from app.tools.fetch_url import FetchUrlTool
from app.tools.gateway import MockFetchUrlTool, MockWebSearchTool, ToolGateway
from app.tools.github_repository import GitHubRepositoryTool
from app.tools.web_search import BraveWebSearchTool


def build_tool_gateway() -> ToolGateway:
    settings = get_settings()
    gateway = ToolGateway()

    if settings.brave_search_api_key:
        gateway.register(BraveWebSearchTool(settings.brave_search_api_key))
        gateway.register(FetchUrlTool())
    else:
        gateway.register(MockWebSearchTool())
        gateway.register(MockFetchUrlTool())

    gateway.register(GitHubRepositoryTool(token=settings.github_token))
    return gateway


tool_gateway = build_tool_gateway()
