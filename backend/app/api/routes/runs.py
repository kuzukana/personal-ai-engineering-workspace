import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.db.models import EvaluationResult, Run, RunEvent
from app.db.session import SessionLocal
from app.events.broker import event_broker

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])
TERMINAL_EVENTS = {"run.completed", "run.failed", "run.cancelled"}


@router.get("/{run_id}")
async def get_run(run_id: UUID) -> dict:
    async with SessionLocal() as session:
        run = await session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            "data": {
                "id": str(run.id),
                "status": run.status,
                "input_text": run.input_text,
                "output_text": run.output_text,
                "structured_output": run.structured_output_json,
                "latency_ms": run.latency_ms,
                "error_code": run.error_code,
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
