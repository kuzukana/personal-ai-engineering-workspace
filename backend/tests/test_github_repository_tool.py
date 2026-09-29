import httpx
import pytest

from app.tools.github_repository import GitHubRepositoryTool, parse_repository


def test_parse_repository_url() -> None:
    assert parse_repository("https://github.com/openai/openai-python") == (
        "openai",
        "openai-python",
    )


@pytest.mark.asyncio
async def test_github_repository_tool_reads_metadata_and_readme() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/readme"):
            return httpx.Response(
                200,
                text="# Example\nRepository README",
                request=request,
            )
        return httpx.Response(
            200,
            json={
                "full_name": "owner/repo",
                "description": "Example repository",
                "html_url": "https://github.com/owner/repo",
                "default_branch": "main",
                "language": "Python",
                "topics": ["agents"],
                "stargazers_count": 10,
                "forks_count": 2,
                "open_issues_count": 1,
                "pushed_at": "2026-09-29T00:00:00Z",
            },
            request=request,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        tool = GitHubRepositoryTool(client=client)
        result = await tool.execute({"repository": "owner/repo"})
    finally:
        await client.aclose()

    assert result["full_name"] == "owner/repo"
    assert result["language"] == "Python"
    assert result["readme"].startswith("# Example")
