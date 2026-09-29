from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from app.db.models import KnowledgeItem, ResearchItem
from app.db.session import SessionLocal

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


def render_knowledge_markdown(research: ResearchItem) -> str:
    result = research.structured_result_json or {}
    lines = [f"# {research.title}", ""]

    summary = result.get("summary") or research.summary
    if summary:
        lines.extend([str(summary), ""])

    findings = result.get("key_findings") or []
    if findings:
        lines.extend(["## Key findings", ""])
        lines.extend(f"- {item}" for item in findings)
        lines.append("")

    sources = result.get("sources") or []
    if sources:
        lines.extend(["## Sources", ""])
        for source in sources:
            title = source.get("title") or source.get("url") or "Source"
            url = source.get("url")
            if url:
                lines.append(f"- [{title}]({url})")
            else:
                lines.append(f"- {title}")
        lines.append("")

    next_actions = result.get("next_actions") or []
    if next_actions:
        lines.extend(["## Next actions", ""])
        lines.extend(f"- {item}" for item in next_actions)
        lines.append("")

    return "\n".join(lines).strip()


def serialize_knowledge(item: KnowledgeItem) -> dict:
    return {
        "id": str(item.id),
        "knowledge_type": item.knowledge_type,
        "title": item.title,
        "summary": item.summary,
        "content_markdown": item.content_markdown,
        "source_research_id": (
            str(item.source_research_id) if item.source_research_id else None
        ),
        "status": item.status,
        "metadata": item.metadata_json or {},
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


@router.post("/from-research/{run_id}", status_code=201)
async def save_research_to_knowledge(run_id: UUID) -> dict:
    async with SessionLocal() as session:
        research_result = await session.execute(
            select(ResearchItem).where(ResearchItem.run_id == run_id)
        )
        research = research_result.scalar_one_or_none()
        if research is None:
            raise HTTPException(status_code=404, detail="Research item not found")

        existing_result = await session.execute(
            select(KnowledgeItem).where(
                KnowledgeItem.source_research_id == research.id
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            return {
                "data": serialize_knowledge(existing),
                "meta": {"created": False},
            }

        item = KnowledgeItem(
            knowledge_type="RESEARCH",
            title=research.title,
            summary=research.summary,
            content_markdown=render_knowledge_markdown(research),
            source_research_id=research.id,
            status="ACTIVE",
            metadata_json={
                "run_id": str(run_id),
                "query": research.query,
            },
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)

        return {
            "data": serialize_knowledge(item),
            "meta": {"created": True},
        }


@router.get("")
async def list_knowledge(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = None,
) -> dict:
    async with SessionLocal() as session:
        query = (
            select(KnowledgeItem)
            .where(KnowledgeItem.status == "ACTIVE")
            .order_by(KnowledgeItem.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if q:
            pattern = f"%{q.strip()}%"
            query = query.where(
                or_(
                    KnowledgeItem.title.ilike(pattern),
                    KnowledgeItem.summary.ilike(pattern),
                    KnowledgeItem.content_markdown.ilike(pattern),
                )
            )

        result = await session.execute(query)
        rows = result.scalars().all()
        return {"data": [serialize_knowledge(row) for row in rows]}


@router.get("/{knowledge_id}")
async def get_knowledge(knowledge_id: UUID) -> dict:
    async with SessionLocal() as session:
        item = await session.get(KnowledgeItem, knowledge_id)
        if item is None or item.status != "ACTIVE":
            raise HTTPException(status_code=404, detail="Knowledge item not found")
        return {"data": serialize_knowledge(item)}
