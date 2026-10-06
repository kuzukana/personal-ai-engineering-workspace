import hashlib
import json
import math
import re
from urllib.parse import urlsplit

import httpx

from app.core.config import Settings
from app.retrieval.chunks import CHUNK_VERSION


class EmbeddingFailure(RuntimeError):
    pass


class Embeddings:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self.client = client
        self.dimensions = settings.embedding_dimensions
        self.demo = settings.embedding_provider == "mock"
        self.model = "lexical-demo-v1" if self.demo else settings.embedding_model
        identity = [
            settings.embedding_provider,
            self.model,
            self.dimensions,
            settings.embedding_base_url,
            CHUNK_VERSION,
        ]
        self.profile = hashlib.sha256(json.dumps(identity).encode()).hexdigest()

    def info(self) -> dict:
        return {
            "profile": self.profile,
            "model": self.model,
            "dimensions": self.dimensions,
            "mode": "demo" if self.demo else "semantic",
        }

    def validate(self, values: list, count: int) -> list[list[float]]:
        if len(values) != count:
            raise EmbeddingFailure("Embedding provider returned the wrong number of vectors")
        normalized = []
        for value in values:
            if not isinstance(value, list) or len(value) != self.dimensions:
                raise EmbeddingFailure("Embedding dimensions do not match configuration")
            if any(type(x) not in (int, float) or not math.isfinite(x) for x in value):
                raise EmbeddingFailure("Embedding provider returned invalid vector values")
            norm = math.hypot(*value)
            if norm == 0 or not math.isfinite(norm):
                raise EmbeddingFailure("Embedding provider returned a zero or invalid vector")
            normalized.append([float(x / norm) for x in value])
        return normalized

    def _demo_vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        words = re.findall(r"[a-z0-9_]+|[\u3400-\u9fff]", text.lower())
        # Deterministic lexical approximation for offline plumbing tests, not a semantic model.
        for word in words or ["<empty>"]:
            digest = hashlib.sha256(word.encode()).digest()
            vector[int.from_bytes(digest[:4]) % self.dimensions] += 1
        return vector

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.demo:
            return self.validate([self._demo_vector(text) for text in texts], len(texts))
        base = self.settings.embedding_base_url
        if not base or not self.model:
            raise EmbeddingFailure("Configure EMBEDDING_BASE_URL and EMBEDDING_MODEL first")
        try:
            url = urlsplit(base)
        except ValueError as exc:
            raise EmbeddingFailure("Embedding base URL is invalid") from exc
        if url.username or url.password or url.query or url.fragment or not url.hostname:
            raise EmbeddingFailure("Embedding base URL must not contain credentials/query/fragment")
        if url.scheme != "https" and not (
            url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1", "::1"}
        ):
            raise EmbeddingFailure("Embedding endpoint must use HTTPS or local HTTP")
        headers = {}
        if self.settings.embedding_api_key:
            headers["Authorization"] = f"Bearer {self.settings.embedding_api_key}"

        async def request(client):
            response = await client.post(
                base.rstrip("/") + "/embeddings",
                json={"model": self.model, "input": texts},
                headers=headers,
                follow_redirects=False,
            )
            response.raise_for_status()
            rows = response.json()["data"]
            if sorted(row["index"] for row in rows) != list(range(len(texts))):
                raise EmbeddingFailure("Embedding response indices do not match inputs")
            return self.validate(
                [row["embedding"] for row in sorted(rows, key=lambda x: x["index"])], len(texts)
            )

        try:
            if self.client is not None:
                return await request(self.client)
            async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
                return await request(client)
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            raise EmbeddingFailure(
                "Embedding request failed; check provider configuration"
            ) from exc
