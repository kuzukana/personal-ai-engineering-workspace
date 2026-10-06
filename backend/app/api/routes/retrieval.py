from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select

from app.db.models import KnowledgeItem
from app.db.session import SessionLocal
from app.retrieval.embeddings import EmbeddingFailure
from app.retrieval.service import RetrievalService

router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])


class SearchRequest(BaseModel):
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    top_k: int = Field(default=5, ge=1, le=20)
    context_budget_bytes: int = Field(default=6000, ge=256, le=16000)


@router.post("/search")
async def search(request: SearchRequest) -> dict:
    try:
        return {
            "data": await RetrievalService().search(
                request.query, request.top_k, request.context_budget_bytes
            )
        }
    except EmbeddingFailure as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/index/{knowledge_id}")
async def index_one(knowledge_id: UUID) -> dict:
    try:
        return {"data": await RetrievalService().index(knowledge_id)}
    except EmbeddingFailure as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/index")
async def index_batch(after_id: UUID | None = None, limit: int = Query(default=20, ge=1, le=50)):
    async with SessionLocal() as session:
        query = select(KnowledgeItem.id).where(KnowledgeItem.status == "ACTIVE")
        if after_id:
            query = query.where(KnowledgeItem.id > after_id)
        ids = list((await session.scalars(query.order_by(KnowledgeItem.id).limit(limit + 1))).all())
    service = RetrievalService()
    results = []
    errors = []
    for knowledge_id in ids[:limit]:
        try:
            results.append(await service.index(knowledge_id))
        except EmbeddingFailure as exc:
            # Do not repeatedly call a broken/billable provider for the rest of the batch.
            raise HTTPException(502, str(exc)) from exc
        except HTTPException as exc:
            errors.append({"knowledge_id": str(knowledge_id), "message": exc.detail})
    return {
        "data": {
            "results": results,
            "errors": errors,
            "next_cursor": str(ids[limit - 1]) if len(ids) > limit else None,
            **service.embeddings.info(),
        }
    }
