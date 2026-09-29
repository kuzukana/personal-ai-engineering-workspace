from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.tools.gateway import Tool

_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def parse_repository(value: str) -> tuple[str, str]:
    candidate = value.strip()
    if candidate.startswith("http://") or candidate.startswith("https://"):
        parsed = urlparse(candidate)
        if parsed.hostname not in {"github.com", "www.github.com"}:
            raise ValueError("Only github.com repository URLs are supported")
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise ValueError("GitHub URL must point to a repository")
        candidate = f"{parts[0]}/{parts[1].removesuffix('.git')}"

    if not _REPOSITORY_PATTERN.fullmatch(candidate):
        raise ValueError("Repository must use owner/name format")
    owner, name = candidate.split("/", 1)
    return owner, name


class GitHubRepositoryTool(Tool):
    name = "github_repository"
    risk_level = "LOW"

    def __init__(
        self,
        token: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token = token
        self._client = client or httpx.AsyncClient(timeout=30.0)

    def _headers(
        self,
        accept: str = "application/vnd.github+json",
    ) -> dict[str, str]:
        headers = {
            "Accept": accept,
            "User-Agent": "PersonalAIEngineeringWorkspace/0.1",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        owner, repo = parse_repository(str(arguments.get("repository", "")))
        base = f"https://api.github.com/repos/{owner}/{repo}"

        metadata_response = await self._client.get(
            base,
            headers=self._headers(),
        )
        metadata_response.raise_for_status()
        metadata = metadata_response.json()

        readme = ""
        readme_response = await self._client.get(
            f"{base}/readme",
            headers=self._headers("application/vnd.github.raw+json"),
        )
        if readme_response.status_code == 200:
            readme = readme_response.text[:50_000]
        elif readme_response.status_code != 404:
            readme_response.raise_for_status()

        return {
            "full_name": metadata.get("full_name"),
            "description": metadata.get("description"),
            "html_url": metadata.get("html_url"),
            "default_branch": metadata.get("default_branch"),
            "language": metadata.get("language"),
            "topics": metadata.get("topics") or [],
            "stargazers_count": metadata.get("stargazers_count"),
            "forks_count": metadata.get("forks_count"),
            "open_issues_count": metadata.get("open_issues_count"),
            "pushed_at": metadata.get("pushed_at"),
            "readme": readme,
        }
