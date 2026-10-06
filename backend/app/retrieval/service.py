import math
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.models import KnowledgeChunk, KnowledgeIndex, KnowledgeItem
from app.db.session import SessionLocal
from app.retrieval.chunks import content_hash, split_content
from app.retrieval.embeddings import Embeddings

MAX_CONTENT_CHARS = 200_000
MAX_SEARCH_CHUNKS = 10_000


def document(item: KnowledgeItem) -> str:
    return item.content_markdown or item.summary or item.title


def build_context(hits: list[dict], byte_budget: int) -> tuple[str, list[dict]]:
    context = ""
    included = []
    for hit in hits:
        label = f"K{len(included) + 1}"
        prefix = f"[{label}] knowledge:{hit['knowledge_id']} chunk:{hit['ordinal']}\n"
        available = byte_budget - len((context + prefix + "\n\n").encode())
        if available < 32:
            break
        excerpt = hit["text"].encode()[:available].decode("utf-8", errors="ignore")
        context += prefix + excerpt + "\n\n"
        included.append(
            {
                **hit,
                "citation": label,
                "text": excerpt,
                "end_offset": hit["start_offset"] + len(excerpt),
            }
        )
    return context.rstrip(), included


class RetrievalService:
    def __init__(self, embeddings: Embeddings | None = None):
        self.embeddings = embeddings or Embeddings(get_settings())

    async def index(self, knowledge_id: UUID) -> dict:
        async with SessionLocal() as session:
            item = await session.get(KnowledgeItem, knowledge_id)
            if item is None or item.status != "ACTIVE":
                raise HTTPException(404, "Knowledge not found")
            content = document(item)
            digest = content_hash(content)
            existing = await session.scalar(
                select(KnowledgeIndex).where(
                    KnowledgeIndex.knowledge_id == knowledge_id,
                    KnowledgeIndex.profile == self.embeddings.profile,
                )
            )
            if existing and existing.content_hash == digest:
                return {
                    "knowledge_id": str(knowledge_id),
                    "changed": False,
                    "chunk_count": existing.chunk_count,
                    **self.embeddings.info(),
                }
        if len(content) > MAX_CONTENT_CHARS:
            raise HTTPException(413, "Knowledge exceeds the 200,000-character indexing limit")
        chunks = split_content(content)
        vectors = []
        for start in range(0, len(chunks), 32):
            vectors.extend(
                await self.embeddings.embed([c.text for c in chunks[start : start + 32]])
            )
        async with SessionLocal() as session:
            # Provider calls finish before locking; no partial replacement on provider failure.
            item = await session.scalar(
                select(KnowledgeItem).where(KnowledgeItem.id == knowledge_id).with_for_update()
            )
            if item is None or item.status != "ACTIVE" or content_hash(document(item)) != digest:
                raise HTTPException(409, "Knowledge changed during indexing; retry")
            existing = await session.scalar(
                select(KnowledgeIndex).where(
                    KnowledgeIndex.knowledge_id == knowledge_id,
                    KnowledgeIndex.profile == self.embeddings.profile,
                )
            )
            if existing and existing.content_hash == digest:
                return {
                    "knowledge_id": str(knowledge_id),
                    "changed": False,
                    "chunk_count": existing.chunk_count,
                    **self.embeddings.info(),
                }
            if existing:
                await session.delete(existing)
                await session.flush()
            index = KnowledgeIndex(
                knowledge_id=knowledge_id,
                profile=self.embeddings.profile,
                content_hash=digest,
                dimensions=self.embeddings.dimensions,
                chunk_count=len(chunks),
            )
            session.add(index)
            await session.flush()
            for chunk, vector in zip(chunks, vectors, strict=True):
                session.add(
                    KnowledgeChunk(
                        index_id=index.id,
                        ordinal=chunk.ordinal,
                        start_offset=chunk.start,
                        end_offset=chunk.end,
                        content=chunk.text,
                        embedding=vector,
                    )
                )
            await session.commit()
        return {
            "knowledge_id": str(knowledge_id),
            "changed": True,
            "chunk_count": len(chunks),
            **self.embeddings.info(),
        }

    async def search(self, query: str, top_k: int, budget: int) -> dict:
        async with SessionLocal() as session:
            conditions = (
                KnowledgeItem.status == "ACTIVE",
                KnowledgeIndex.profile == self.embeddings.profile,
            )
            # Bound source and vector allocations before loading JSON vectors into Python.
            source = func.coalesce(
                func.nullif(KnowledgeItem.content_markdown, ""),
                func.nullif(KnowledgeItem.summary, ""),
                KnowledgeItem.title,
            )
            characters, cells, chunk_count = (
                await session.execute(
                    select(
                        func.sum(func.length(source)),
                        func.sum(KnowledgeIndex.chunk_count * KnowledgeIndex.dimensions),
                        func.sum(KnowledgeIndex.chunk_count),
                    )
                    .join(KnowledgeItem, KnowledgeItem.id == KnowledgeIndex.knowledge_id)
                    .where(*conditions)
                )
            ).one()
            if (
                (characters or 0) > 5_000_000
                or (cells or 0) > 2_000_000
                or (chunk_count or 0) > MAX_SEARCH_CHUNKS
            ):
                raise HTTPException(
                    409, "Index exceeds exact-search capacity; use a vector backend"
                )
            pairs = (
                await session.execute(
                    select(KnowledgeIndex, KnowledgeItem)
                    .join(KnowledgeItem, KnowledgeItem.id == KnowledgeIndex.knowledge_id)
                    .where(
                        KnowledgeItem.status == "ACTIVE",
                        KnowledgeIndex.profile == self.embeddings.profile,
                    )
                )
            ).all()
            valid = {
                index.id: (index, item)
                for index, item in pairs
                if index.content_hash == content_hash(document(item))
            }
            stale_count = len(pairs) - len(valid)
            if not valid:
                return {
                    "hits": [],
                    "context": "",
                    "stale_documents": stale_count,
                    "indexed_documents": 0,
                    **self.embeddings.info(),
                }
            chunks = (
                await session.scalars(
                    select(KnowledgeChunk)
                    .where(KnowledgeChunk.index_id.in_(valid))
                    .limit(MAX_SEARCH_CHUNKS + 1)
                )
            ).all()
        if len(chunks) > MAX_SEARCH_CHUNKS:
            raise HTTPException(409, "Index exceeds exact-search capacity; use a vector backend")
        vector = (await self.embeddings.embed([query]))[0]
        scored = []
        for chunk in chunks:
            index, item = valid[chunk.index_id]
            if index.dimensions != len(vector) or len(chunk.embedding) != len(vector):
                raise HTTPException(409, "Index dimensions changed; reindex Knowledge")
            score = math.fsum(x * y for x, y in zip(vector, chunk.embedding, strict=True))
            if score <= 0:
                continue
            scored.append(
                {
                    "knowledge_id": str(item.id),
                    "title": item.title,
                    "source_research_id": str(item.source_research_id)
                    if item.source_research_id
                    else None,
                    "ordinal": chunk.ordinal,
                    "start_offset": chunk.start_offset,
                    "end_offset": chunk.end_offset,
                    "content_hash": index.content_hash,
                    "score": min(1.0, score),
                    "text": chunk.content,
                }
            )
        scored.sort(key=lambda x: (-x["score"], x["knowledge_id"], x["ordinal"]))
        context, hits = build_context(scored[:top_k], budget)
        return {
            "hits": hits,
            "context": context,
            "stale_documents": stale_count,
            "indexed_documents": len(valid),
            **self.embeddings.info(),
        }
