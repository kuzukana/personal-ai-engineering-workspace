import math
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.retrieval.chunks import split_content
from app.retrieval.embeddings import EmbeddingFailure, Embeddings
from app.retrieval.service import build_context


@pytest.mark.parametrize(
    "text",
    ["", "short", "中文引用" * 1000, "a " * 10_000],
    ids=["empty", "short", "unicode", "long"],
)
def test_chunk_offsets_cover_content(text):
    chunks = split_content(text)
    covered = set()
    for chunk in chunks:
        assert chunk.text == text[chunk.start : chunk.end]
        assert len(chunk.text) <= 900
        covered.update(range(chunk.start, chunk.end))
    assert covered == set(range(len(text)))


@pytest.mark.parametrize("size,overlap", [(0, 0), (10, 10), (10, -1)])
def test_invalid_chunk_parameters(size, overlap):
    with pytest.raises(ValueError):
        split_content("test", size, overlap)


async def test_demo_retrieval_evaluation():
    provider = Embeddings(Settings(_env_file=None, embedding_provider="mock"))
    documents = [
        "PostgreSQL database transactions rollback commit",
        "React browser component state rendering",
        "Python asyncio concurrent coroutines event loop",
    ]
    vectors = await provider.embed(documents)
    queries = ["database rollback", "React component", "asyncio coroutines"]
    query_vectors = await provider.embed(queries)
    ranks = []
    for expected, query in enumerate(query_vectors):
        ranking = sorted(
            range(3),
            key=lambda i: -math.fsum(x * y for x, y in zip(query, vectors[i], strict=True)),
        )
        ranks.append(ranking.index(expected) + 1)
    assert ranks == [1, 1, 1]  # Demo regression Recall@1=1, MRR=1, not a semantic-quality claim.
    assert provider.info()["mode"] == "demo"


async def test_http_embedding_response_order_and_normalization():
    def handler(request):
        assert request.url.path == "/v1/embeddings"
        return httpx.Response(
            200,
            json={"data": [{"index": 1, "embedding": [0, 3]}, {"index": 0, "embedding": [4, 0]}]},
        )

    settings = Settings(
        _env_file=None,
        embedding_provider="http",
        embedding_dimensions=2,
        embedding_model="test",
        embedding_base_url="https://example.com/v1",
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await Embeddings(settings, client).embed(["first", "second"]) == [[1, 0], [0, 1]]


@pytest.mark.parametrize("vectors", [[[0, 0]], [[1]], [[float("nan"), 1]], [[True, 1]], []])
def test_invalid_vectors_rejected(vectors):
    provider = Embeddings(Settings(_env_file=None, embedding_dimensions=2))
    with pytest.raises(EmbeddingFailure):
        provider.validate(vectors, 1)


def test_context_budget_retains_citation_and_provenance():
    hits = [
        {"knowledge_id": str(uuid4()), "ordinal": i, "start_offset": 0, "text": "引用证据" * 1000}
        for i in range(3)
    ]
    context, included = build_context(hits, 256)
    assert len(context.encode()) <= 256
    assert len(included) == 1 and included[0]["citation"] == "K1"
    assert hits[0]["knowledge_id"] in context
    assert included[0]["text"] in context
