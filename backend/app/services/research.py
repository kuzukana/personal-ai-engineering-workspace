from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.agents.research.agent import research_agent
from app.ai.container import model_gateway
from app.db.models import ResearchItem, ResearchSource, Run, RunEvent
from app.db.session import SessionLocal
from app.domain.constants import RESEARCH_AGENT_VERSION_ID
from app.evaluation.research import evaluate_research
from app.events.publisher import event_publisher
from app.runtime.run_control import RunCancelled, run_control
from app.services.model_registry import ensure_registered_model


class ResearchService:
    async def create_run(self, query: str, model_id: UUID) -> Run:
        async with SessionLocal() as session:
            registered_model = model_gateway.registry.get(str(model_id))
            await ensure_registered_model(session, model_id, registered_model)
            run = Run(
                agent_version_id=RESEARCH_AGENT_VERSION_ID,
                model_id=model_id,
                status="PENDING",
                task_type="research",
                input_text=query,
            )
            session.add(run)
            await session.flush()
            await event_publisher.emit(
                session,
                run.id,
                "run.created",
                "api",
                {
                    "agent_id": "research-agent",
                    "agent_version": "0.1",
                    "model_id": str(model_id),
                },
            )
            return run

    async def execute(self, run_id: UUID, query: str, model_id: UUID) -> None:
        started = datetime.now(UTC)
        async with SessionLocal() as session:
            try:
                run = await session.scalar(select(Run).where(Run.id == run_id).with_for_update())
                if run is None or run.status not in {"PENDING", "CANCELLATION_REQUESTED"}:
                    return
                if run.status == "CANCELLATION_REQUESTED":
                    raise RunCancelled(f"Run cancelled: {run_id}")
                run.status = "RUNNING"
                run.started_at = started
                await event_publisher.emit(
                    session,
                    run_id,
                    "run.started",
                    "agent_runtime",
                    {"task_type": "research"},
                )
                await event_publisher.emit(
                    session,
                    run_id,
                    "agent.started",
                    "agent_runtime",
                    {"agent_id": "research-agent", "agent_version": "0.1"},
                )

                run_control.raise_if_cancelled(run_id)
                report = await research_agent.run(
                    session,
                    run_id,
                    query,
                    str(model_id),
                )
                run_control.raise_if_cancelled(run_id)

                await event_publisher.emit(
                    session,
                    run_id,
                    "agent.completed",
                    "agent_runtime",
                    {},
                )
                await event_publisher.emit(
                    session,
                    run_id,
                    "evaluation.started",
                    "evaluation_engine",
                    {
                        "evaluator_key": "research-deterministic",
                        "evaluator_version": "0.1",
                    },
                )

                try:
                    evaluations = await evaluate_research(session, run_id, report)
                except Exception:
                    await session.rollback()
                    await event_publisher.emit(
                        session,
                        run_id,
                        "evaluation.failed",
                        "evaluation_engine",
                        {"message": "Evaluation failed"},
                    )
                    raise
                for evaluation in evaluations:
                    await event_publisher.emit(
                        session,
                        run_id,
                        "evaluation.metric.completed",
                        "evaluation_engine",
                        {
                            "metric_name": evaluation.metric_name,
                            "evaluation_type": evaluation.evaluation_type,
                            "status": evaluation.status,
                        },
                    )

                await event_publisher.emit(
                    session,
                    run_id,
                    "evaluation.completed",
                    "evaluation_engine",
                    {"metric_count": len(evaluations)},
                )

                finished = datetime.now(UTC)
                run = await session.get(Run, run_id)
                if run is None:
                    return

                usage_result = await session.execute(
                    select(RunEvent).where(
                        RunEvent.run_id == run_id,
                        RunEvent.event_type == "model.usage",
                    )
                )
                usage_events = usage_result.scalars().all()
                input_tokens = 0
                output_tokens = 0
                reasoning_tokens = 0
                estimated_cost = Decimal("0")
                currency = None
                has_input_tokens = False
                has_output_tokens = False
                has_reasoning_tokens = False
                has_cost = False

                for usage_event in usage_events:
                    payload = usage_event.payload_json or {}
                    if payload.get("input_tokens") is not None:
                        input_tokens += int(payload["input_tokens"])
                        has_input_tokens = True
                    if payload.get("output_tokens") is not None:
                        output_tokens += int(payload["output_tokens"])
                        has_output_tokens = True
                    if payload.get("reasoning_tokens") is not None:
                        reasoning_tokens += int(payload["reasoning_tokens"])
                        has_reasoning_tokens = True
                    if payload.get("estimated_cost") is not None:
                        estimated_cost += Decimal(str(payload["estimated_cost"]))
                        has_cost = True
                    if payload.get("currency"):
                        currency = str(payload["currency"])

                run = await session.scalar(
                    select(Run)
                    .where(Run.id == run_id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
                if run.status == "CANCELLATION_REQUESTED":
                    raise RunCancelled(f"Run cancelled: {run_id}")
                run_control.raise_if_cancelled(run_id)
                item = ResearchItem(
                    run_id=run_id,
                    title=report.title,
                    query=query,
                    summary=report.summary,
                    report_markdown=report.summary,
                    structured_result_json=report.model_dump(mode="json"),
                    status="COMPLETED",
                )
                session.add(item)
                await session.flush()

                for source in report.sources:
                    session.add(
                        ResearchSource(
                            research_item_id=item.id,
                            url=str(source.url),
                            title=source.title,
                            source_type=source.source_type,
                            content_excerpt=source.snippet,
                            verification_status=source.verification_status,
                        )
                    )

                run.status = "COMPLETED"
                run.output_text = report.summary
                run.structured_output_json = report.model_dump(mode="json")
                run.completed_at = finished
                run.latency_ms = int((finished - started).total_seconds() * 1000)
                run.input_tokens = input_tokens if has_input_tokens else None
                run.output_tokens = output_tokens if has_output_tokens else None
                run.reasoning_tokens = reasoning_tokens if has_reasoning_tokens else None
                run.estimated_cost = estimated_cost if has_cost else None
                run.currency = currency
                await event_publisher.emit(
                    session,
                    run_id,
                    "run.completed",
                    "agent_runtime",
                    {"latency_ms": run.latency_ms, "warnings": []},
                )
            except RunCancelled:
                await session.rollback()
                run = await session.get(Run, run_id)
                if run is not None:
                    run.status = "CANCELLED"
                    run.completed_at = datetime.now(UTC)
                    await event_publisher.emit(
                        session,
                        run_id,
                        "run.cancelled",
                        "agent_runtime",
                        {"reason": "user_cancelled"},
                    )
            except Exception:
                await session.rollback()
                run = await session.get(Run, run_id)
                if run is not None and run.status not in {"COMPLETED", "CANCELLED"}:
                    run.status = "FAILED"
                    run.error_code = "WORKFLOW_ERROR"
                    run.error_message = "Research workflow failed"
                    run.completed_at = datetime.now(UTC)
                    await event_publisher.emit(
                        session,
                        run_id,
                        "run.failed",
                        "agent_runtime",
                        {
                            "error_code": "WORKFLOW_ERROR",
                            "message": "Research workflow failed",
                            "recoverable": False,
                        },
                    )
                raise
            finally:
                run_control.clear(run_id)

    async def get_run(self, run_id: UUID) -> Run | None:
        async with SessionLocal() as session:
            return await session.get(Run, run_id)

    async def get_research_by_run(self, run_id: UUID) -> ResearchItem | None:
        async with SessionLocal() as session:
            result = await session.execute(
                select(ResearchItem).where(ResearchItem.run_id == run_id)
            )
            return result.scalar_one_or_none()


research_service = ResearchService()
