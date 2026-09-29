import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.db.models import (
    Capability,
    CapabilityEvidence,
    Evidence,
    Technology,
)
from app.db.session import SessionLocal

router = APIRouter(prefix="/api/v1/capabilities", tags=["capabilities"])


class TechnologyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    description: str | None = None


class CapabilityUpdate(BaseModel):
    level: int = Field(ge=0, le=5)
    reason: str | None = None
    next_target_level: int | None = Field(default=None, ge=0, le=5)
    next_action: str | None = None


class EvidenceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    evidence_type: str = Field(min_length=1, max_length=48)
    description: str | None = None
    url: str | None = None


def slugify_technology(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ValueError("Technology name must contain letters or numbers")
    return slug[:180]


def serialize_capability(
    technology: Technology,
    capability: Capability | None,
) -> dict:
    return {
        "technology": {
            "id": str(technology.id),
            "name": technology.name,
            "slug": technology.slug,
            "category": technology.category,
            "description": technology.description,
        },
        "capability": (
            {
                "id": str(capability.id),
                "level": capability.level,
                "reason": capability.reason,
                "next_target_level": capability.next_target_level,
                "next_action": capability.next_action,
                "updated_at": capability.updated_at.isoformat(),
            }
            if capability
            else None
        ),
    }


def serialize_evidence(evidence: Evidence) -> dict:
    return {
        "id": str(evidence.id),
        "title": evidence.title,
        "evidence_type": evidence.evidence_type,
        "description": evidence.description,
        "url": evidence.url,
        "metadata": evidence.metadata_json or {},
        "created_at": evidence.created_at.isoformat(),
        "updated_at": evidence.updated_at.isoformat(),
    }


@router.get("")
async def list_capabilities() -> dict:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Technology, Capability)
            .outerjoin(Capability, Capability.technology_id == Technology.id)
            .order_by(Technology.name)
        )
        return {
            "data": [
                serialize_capability(technology, capability)
                for technology, capability in result.all()
            ]
        }


@router.post("/technologies", status_code=201)
async def create_technology(request: TechnologyCreate) -> dict:
    name = request.name.strip()
    try:
        slug = slugify_technology(name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    async with SessionLocal() as session:
        duplicate = await session.execute(
            select(Technology).where(
                (Technology.name == name) | (Technology.slug == slug)
            )
        )
        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Technology already exists")

        technology = Technology(
            name=name,
            slug=slug,
            category=request.category,
            description=request.description,
        )
        session.add(technology)
        await session.commit()
        await session.refresh(technology)
        return {"data": serialize_capability(technology, None)}


@router.put("/technologies/{technology_id}")
async def upsert_capability(
    technology_id: UUID,
    request: CapabilityUpdate,
) -> dict:
    async with SessionLocal() as session:
        technology = await session.get(Technology, technology_id)
        if technology is None:
            raise HTTPException(status_code=404, detail="Technology not found")

        result = await session.execute(
            select(Capability).where(Capability.technology_id == technology_id)
        )
        capability = result.scalar_one_or_none()
        if capability is None:
            capability = Capability(
                technology_id=technology_id,
                level=request.level,
                reason=request.reason,
                next_target_level=request.next_target_level,
                next_action=request.next_action,
            )
            session.add(capability)
        else:
            capability.level = request.level
            capability.reason = request.reason
            capability.next_target_level = request.next_target_level
            capability.next_action = request.next_action
            capability.updated_at = datetime.now(UTC)

        await session.commit()
        await session.refresh(capability)
        return {"data": serialize_capability(technology, capability)}


@router.get("/evidences")
async def list_evidences() -> dict:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Evidence).order_by(Evidence.updated_at.desc())
        )
        return {"data": [serialize_evidence(row) for row in result.scalars().all()]}


@router.post("/evidences", status_code=201)
async def create_evidence(request: EvidenceCreate) -> dict:
    async with SessionLocal() as session:
        evidence = Evidence(
            title=request.title.strip(),
            evidence_type=request.evidence_type.strip().upper(),
            description=request.description,
            url=request.url,
        )
        session.add(evidence)
        await session.commit()
        await session.refresh(evidence)
        return {"data": serialize_evidence(evidence)}


@router.get("/{capability_id}/evidences")
async def list_capability_evidences(capability_id: UUID) -> dict:
    async with SessionLocal() as session:
        capability = await session.get(Capability, capability_id)
        if capability is None:
            raise HTTPException(status_code=404, detail="Capability not found")

        result = await session.execute(
            select(Evidence)
            .join(
                CapabilityEvidence,
                CapabilityEvidence.evidence_id == Evidence.id,
            )
            .where(CapabilityEvidence.capability_id == capability_id)
            .order_by(Evidence.updated_at.desc())
        )
        return {"data": [serialize_evidence(row) for row in result.scalars().all()]}


@router.post("/{capability_id}/evidences/{evidence_id}", status_code=201)
async def link_capability_evidence(
    capability_id: UUID,
    evidence_id: UUID,
) -> dict:
    async with SessionLocal() as session:
        capability = await session.get(Capability, capability_id)
        evidence = await session.get(Evidence, evidence_id)
        if capability is None:
            raise HTTPException(status_code=404, detail="Capability not found")
        if evidence is None:
            raise HTTPException(status_code=404, detail="Evidence not found")

        existing = await session.get(
            CapabilityEvidence,
            {
                "capability_id": capability_id,
                "evidence_id": evidence_id,
            },
        )
        if existing is None:
            session.add(
                CapabilityEvidence(
                    capability_id=capability_id,
                    evidence_id=evidence_id,
                )
            )
            await session.commit()

        return {
            "data": {
                "capability_id": str(capability_id),
                "evidence_id": str(evidence_id),
            }
        }
