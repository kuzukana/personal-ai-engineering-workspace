from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.ai.container import model_gateway
from app.services.research import research_service

router = APIRouter(prefix="/api/v1/research", tags=["research"])


class ResearchCreate(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    model_id: UUID


@router.post("", status_code=202)
async def create_research(
    request: ResearchCreate,
    background_tasks: BackgroundTasks,
) -> dict:
    model_key = str(request.model_id)
    try:
        model_gateway.registry.get(model_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Model not found") from exc

    run = await research_service.create_run(
        request.query,
        request.model_id,
    )
    background_tasks.add_task(
        research_service.execute,
        run.id,
        request.query,
        request.model_id,
    )
    return {
        "data": {
            "run_id": str(run.id),
            "status": run.status,
            "events_url": f"/api/v1/runs/{run.id}/events",
        }
    }


@router.get("/{run_id}")
async def get_research_by_run(run_id: UUID) -> dict:
    item = await research_service.get_research_by_run(run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")
    return {
        "data": {
            "id": str(item.id),
            "run_id": str(item.run_id) if item.run_id else None,
            "title": item.title,
            "query": item.query,
            "summary": item.summary,
            "status": item.status,
            "structured_result": item.structured_result_json,
        }
    }
