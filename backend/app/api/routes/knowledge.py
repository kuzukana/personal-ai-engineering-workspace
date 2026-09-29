from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    KnowledgeItem,
    KnowledgeTechnology,
    ResearchItem,
    Technology,
)
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


async def get_linked_technologies(
    session: AsyncSession,
    knowledge_id: UUID,
) -> list[Technology]:
    result = await session.execute(
        select(Technology)
        .join(
            KnowledgeTechnology,
            KnowledgeTechnology.technology_id == Technology.id,
        )
        .where(KnowledgeTechnology.knowledge_id == knowledge_id)
        .order_by(Technology.name)
    )
    return list(result.scalars().all())


def serialize_knowledge(
    item: KnowledgeItem,
    technologies: list[Technology] | None = None,
) -> dict:
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
        "technologies": [
            {
                "id": str(technology.id),
                "name": technology.name,
                "slug": technology.slug,
                "category": technology.category,
            }
            for technology in technologies or []
        ],
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
            technologies = await get_linked_technologies(session, existing.id)
            return {
                "data": serialize_knowledge(existing, technologies),
                "meta": {"created": False},
            }

        content_markdown = render_knowledge_markdown(research)
        item = KnowledgeItem(
            knowledge_type="RESEARCH",
            title=research.title,
            summary=research.summary,
            content_markdown=content_markdown,
            source_research_id=research.id,
            status="ACTIVE",
            metadata_json={
                "run_id": str(run_id),
                "query": research.query,
            },
        )
        session.add(item)
        await session.flush()

        technology_result = await session.execute(
            select(Technology).order_by(Technology.name)
        )
        candidate_technologies = technology_result.scalars().all()
        searchable = " ".join(
            [
                research.title or "",
                research.summary or "",
                content_markdown,
            ]
        ).lower()
        linked: list[Technology] = []
        for technology in candidate_technologies:
            if technology.name.lower() not in searchable:
                continue
            session.add(
                KnowledgeTechnology(
                    knowledge_id=item.id,
                    technology_id=technology.id,
                )
            )
            linked.append(technology)

        await session.commit()
        await session.refresh(item)

        return {
            "data": serialize_knowledge(item, linked),
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
        data = []
        for row in rows:
            technologies = await get_linked_technologies(session, row.id)
            data.append(serialize_knowledge(row, technologies))
        return {"data": data}


@router.get("/{knowledge_id}")
async def get_knowledge(knowledge_id: UUID) -> dict:
    async with SessionLocal() as session:
        item = await session.get(KnowledgeItem, knowledge_id)
        if item is None or item.status != "ACTIVE":
            raise HTTPException(status_code=404, detail="Knowledge item not found")
        technologies = await get_linked_technologies(session, knowledge_id)
        return {"data": serialize_knowledge(item, technologies)}


@router.post("/{knowledge_id}/technologies/{technology_id}", status_code=201)
async def link_knowledge_technology(
    knowledge_id: UUID,
    technology_id: UUID,
) -> dict:
    async with SessionLocal() as session:
        knowledge = await session.get(KnowledgeItem, knowledge_id)
        technology = await session.get(Technology, technology_id)
        if knowledge is None:
            raise HTTPException(status_code=404, detail="Knowledge item not found")
        if technology is None:
            raise HTTPException(status_code=404, detail="Technology not found")

        existing = await session.get(
            KnowledgeTechnology,
            {
                "knowledge_id": knowledge_id,
                "technology_id": technology_id,
            },
        )
        if existing is None:
            session.add(
                KnowledgeTechnology(
                    knowledge_id=knowledge_id,
                    technology_id=technology_id,
                )
            )
            await session.commit()

        return {
            "data": {
                "knowledge_id": str(knowledge_id),
                "technology_id": str(technology_id),
            }
        }
