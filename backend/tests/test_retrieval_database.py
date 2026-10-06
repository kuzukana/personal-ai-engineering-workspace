import asyncio
import os
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.db.models import KnowledgeChunk, KnowledgeIndex, KnowledgeItem
from app.retrieval import service
from app.retrieval.embeddings import EmbeddingFailure, Embeddings

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="disposable database only"
)


@pytest_asyncio.fixture
async def retrieval(monkeypatch):
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"], poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(service, "SessionLocal", factory)
    embeddings = Embeddings(Settings(_env_file=None, embedding_provider="mock"))
    runtime = service.RetrievalService(embeddings)
    async with factory() as session:
        item = KnowledgeItem(
            knowledge_type="RESEARCH",
            title="Database evidence",
            content_markdown="PostgreSQL database transactions rollback commit",
            status="ACTIVE",
        )
        session.add(item)
        await session.commit()
        knowledge_id = item.id
    try:
        yield runtime, factory, knowledge_id
    finally:
        async with factory() as session:
            await session.execute(delete(KnowledgeItem).where(KnowledgeItem.id == knowledge_id))
            await session.commit()
        await engine.dispose()


async def test_concurrent_index_is_idempotent_and_search_has_provenance(retrieval):
    runtime, factory, knowledge_id = retrieval
    results = await asyncio.gather(*(runtime.index(knowledge_id) for _ in range(4)))
    assert sum(r["changed"] for r in results) == 1
    result = await runtime.search("PostgreSQL rollback", 5, 2000)
    assert result["hits"][0]["knowledge_id"] == str(knowledge_id)
    assert result["hits"][0]["citation"] == "K1"
    async with factory() as session:
        index = await session.scalar(
            select(KnowledgeIndex).where(KnowledgeIndex.knowledge_id == knowledge_id)
        )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(KnowledgeChunk)
                .where(KnowledgeChunk.index_id == index.id)
            )
            == 1
        )


async def test_provider_failure_keeps_old_index_and_stale_content_is_excluded(
    retrieval, monkeypatch
):
    runtime, factory, knowledge_id = retrieval
    await runtime.index(knowledge_id)
    async with factory() as session:
        item = await session.get(KnowledgeItem, knowledge_id)
        item.content_markdown = "changed knowledge"
        await session.commit()
    monkeypatch.setattr(
        runtime.embeddings, "embed", AsyncMock(side_effect=EmbeddingFailure("down"))
    )
    with pytest.raises(EmbeddingFailure):
        await runtime.index(knowledge_id)
    async with factory() as session:
        assert (
            await session.scalar(
                select(KnowledgeIndex).where(KnowledgeIndex.knowledge_id == knowledge_id)
            )
            is not None
        )
    result = await runtime.search("query", 5, 2000)
    assert result["stale_documents"] >= 1
    assert not any(h["knowledge_id"] == str(knowledge_id) for h in result["hits"])


async def test_edit_during_embedding_cannot_publish_obsolete_index(retrieval, monkeypatch):
    runtime, factory, knowledge_id = retrieval
    embed = runtime.embeddings.embed

    async def change_then_embed(texts):
        async with factory() as session:
            item = await session.get(KnowledgeItem, knowledge_id)
            item.content_markdown = "concurrent edit"
            await session.commit()
        return await embed(texts)

    monkeypatch.setattr(runtime.embeddings, "embed", change_then_embed)
    with pytest.raises(HTTPException) as error:
        await runtime.index(knowledge_id)
    assert error.value.status_code == 409
    async with factory() as session:
        assert (
            await session.scalar(
                select(KnowledgeIndex).where(KnowledgeIndex.knowledge_id == knowledge_id)
            )
            is None
        )


async def test_refresh_replaces_chunks_and_model_switch_requires_new_index(retrieval):
    runtime, factory, knowledge_id = retrieval
    await runtime.index(knowledge_id)
    async with factory() as session:
        item = await session.get(KnowledgeItem, knowledge_id)
        item.content_markdown = "Python asyncio coroutines " * 100
        await session.commit()
    assert (await runtime.index(knowledge_id))["changed"]
    result = await runtime.search("asyncio coroutines", 5, 256)
    assert result["hits"]
    async with factory() as session:
        item = await session.get(KnowledgeItem, knowledge_id)
        for hit in result["hits"]:
            assert item.content_markdown[hit["start_offset"] : hit["end_offset"]] == hit["text"]
        assert (
            await session.scalar(
                select(func.count())
                .select_from(KnowledgeIndex)
                .where(KnowledgeIndex.knowledge_id == knowledge_id)
            )
            == 1
        )
    other = service.RetrievalService(
        Embeddings(Settings(_env_file=None, embedding_provider="mock", embedding_dimensions=128))
    )
    assert (await other.search("asyncio", 5, 1000))["indexed_documents"] == 0


async def test_capacity_is_checked_before_embedding_request(retrieval, monkeypatch):
    runtime, factory, knowledge_id = retrieval
    await runtime.index(knowledge_id)
    monkeypatch.setattr(service, "MAX_SEARCH_CHUNKS", 0)
    mocked = AsyncMock(side_effect=AssertionError("must reject before provider call"))
    monkeypatch.setattr(runtime.embeddings, "embed", mocked)
    with pytest.raises(HTTPException) as error:
        await runtime.search("query", 5, 2000)
    assert error.value.status_code == 409
    mocked.assert_not_called()
