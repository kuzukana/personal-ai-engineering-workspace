import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.db.models import EvaluationResult, Run, RunEvent
from app.db.session import SessionLocal
from app.events.broker import event_broker
from app.runtime.run_control import run_control

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
        "estimated_cost": float(run.estimated_cost) if run.estimated_cost is not None else None,
        "error_code": run.error_code,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get("")
async def list_runs(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
) -> dict:
    async with SessionLocal() as session:
        query = select(Run).order_by(Run.created_at.desc()).offset(offset).limit(limit)
        if status:
            query = query.where(Run.status == status.upper())
        result = await session.execute(query)
        rows = result.scalars().all()
        return {"data": [serialize_run(row) for row in rows]}


@router.get("/{run_id}")
async def get_run(run_id: UUID) -> dict:
    async with SessionLocal() as session:
        run = await session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return {"data": serialize_run(run)}


@router.post("/{run_id}/cancel", status_code=202)
async def cancel_run(run_id: UUID) -> dict:
    async with SessionLocal() as session:
        run = await session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        if run.status in TERMINAL_STATUSES:
            raise HTTPException(status_code=409, detail=f"Run is already {run.status.lower()}")
    run_control.request_cancel(run_id)
    return {
        "data": {
            "run_id": str(run_id),
            "status": "CANCELLATION_REQUESTED",
        }
    }


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

    async def stream() -> AsyncIterator[str]:
        queue = event_broker.subscribe(run_id)
        last_sequence = after_sequence
        try:
            async with SessionLocal() as session:
                result = await session.execute(
                    select(RunEvent)
                    .where(
                        RunEvent.run_id == run_id,
                        RunEvent.sequence > last_sequence,
                    )
                    .order_by(RunEvent.sequence)
                )
                for row in result.scalars().all():
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
                    yield (
                        f"id: {row.sequence}\n"
                        f"event: {row.event_type}\n"
                        f"data: {json.dumps(data)}\n\n"
                    )
                    if row.event_type in TERMINAL_EVENTS:
                        return

            while True:
                event = await queue.get()
                if event.sequence <= last_sequence:
                    continue
                last_sequence = event.sequence
                data = event.model_dump(mode="json")
                yield (
                    f"id: {event.sequence}\n"
                    f"event: {event.type}\n"
                    f"data: {json.dumps(data)}\n\n"
                )
                if event.type in TERMINAL_EVENTS:
                    return
        finally:
            event_broker.unsubscribe(run_id, queue)

    return StreamingResponse(stream(), media_type="text/event-stream")


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
