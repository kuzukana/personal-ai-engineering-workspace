import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.run_schemas import RunResponse, RunsResponse
from app.db.models import EvaluationResult, Run, RunEvent
from app.db.session import SessionLocal

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])
TERMINAL_EVENTS = {"run.completed", "run.failed", "run.cancelled"}
TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}


def serialize_run(run: Run) -> dict:
    return {
        "id": str(run.id),
        "status": run.status,
        "task_type": run.task_type,
        "model_id": str(run.model_id),
        "input_text": run.input_text,
        "output_text": run.output_text,
        "structured_output": run.structured_output_json,
        "latency_ms": run.latency_ms,
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "reasoning_tokens": run.reasoning_tokens,
        "currency": run.currency,
        "error_message": run.error_message,
        "estimated_cost": float(run.estimated_cost) if run.estimated_cost is not None else None,
        "error_code": run.error_code,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get("", response_model=RunsResponse)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
) -> dict:
    async with SessionLocal() as session:
        query = select(Run).order_by(Run.created_at.desc(), Run.id).offset(offset).limit(limit)
        if status:
            query = query.where(Run.status == status.upper())
        result = await session.execute(query)
        rows = result.scalars().all()
        return {"data": [serialize_run(row) for row in rows]}


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: UUID) -> dict:
    async with SessionLocal() as session:
        run = await session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return {"data": serialize_run(run)}


@router.post("/{run_id}/cancel", status_code=202)
async def cancel_run(run_id: UUID) -> dict:
    async with SessionLocal() as session:
        run = await session.scalar(select(Run).where(Run.id == run_id).with_for_update())
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        if run.status in TERMINAL_STATUSES:
            raise HTTPException(status_code=409, detail=f"Run is already {run.status.lower()}")
        run.status = "CANCELLATION_REQUESTED"
        await session.commit()
    return {"data": {"run_id": str(run_id), "status": "CANCELLATION_REQUESTED"}}


@router.get("/{run_id}/events/history")
async def event_history(run_id: UUID, after_sequence: int = 0) -> dict:
    async with SessionLocal() as session:
        result = await session.execute(
            select(RunEvent)
            .where(
                RunEvent.run_id == run_id,
                RunEvent.sequence > after_sequence,
            )
            .order_by(RunEvent.sequence)
        )
        rows = result.scalars().all()
        return {
            "data": [
                {
                    "id": str(row.id),
                    "run_id": str(row.run_id),
                    "sequence": row.sequence,
                    "type": row.event_type,
                    "timestamp": row.created_at.isoformat(),
                    "payload": row.payload_json or {},
                }
                for row in rows
            ]
        }


@router.get("/{run_id}/events")
async def stream_events(
    run_id: UUID,
    request: Request,
    after_sequence: int = 0,
) -> StreamingResponse:
    header_value = request.headers.get("last-event-id")
    if header_value and header_value.isdigit():
        after_sequence = max(after_sequence, int(header_value))

    async with SessionLocal() as session:
        if await session.get(Run, run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")

    async def stream() -> AsyncIterator[str]:
        last_sequence = after_sequence
        while not await request.is_disconnected():
            async with SessionLocal() as session:
                # Read status first: a committed terminal status includes its event.
                status = await session.scalar(select(Run.status).where(Run.id == run_id))
                result = await session.execute(
                    select(RunEvent)
                    .where(RunEvent.run_id == run_id, RunEvent.sequence > last_sequence)
                    .order_by(RunEvent.sequence)
                )
                rows = result.scalars().all()
            for row in rows:
                last_sequence = row.sequence
                data = {
                    "id": str(row.id),
                    "run_id": str(row.run_id),
                    "sequence": row.sequence,
                    "type": row.event_type,
                    "timestamp": row.created_at.isoformat(),
                    "source": "history",
                    "payload": row.payload_json or {},
                }
                yield (f"id: {row.sequence}\nevent: {row.event_type}\ndata: {json.dumps(data)}\n\n")
                if row.event_type in TERMINAL_EVENTS:
                    return
            if status is None or status in TERMINAL_STATUSES:
                return
            yield ": heartbeat\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{run_id}/evaluations")
async def evaluations(run_id: UUID) -> dict:
    async with SessionLocal() as session:
        result = await session.execute(
            select(EvaluationResult).where(EvaluationResult.run_id == run_id)
        )
        rows = result.scalars().all()
        return {
            "data": [
                {
                    "metric_name": row.metric_name,
                    "evaluation_type": row.evaluation_type,
                    "status": row.status,
                    "evaluator_version": row.evaluator_version,
                    "evidence": row.evidence_json,
                }
                for row in rows
            ]
        }
