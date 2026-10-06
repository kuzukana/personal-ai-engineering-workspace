"""Run only against a disposable, migrated PostgreSQL database."""

import asyncio
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from starlette.requests import Request

from app.agents.research import agent
from app.agents.research.schemas import ResearchReport
from app.api.routes import capabilities, knowledge, runs
from app.db.models import KnowledgeItem, ResearchItem, Run, RunEvent
from app.domain.constants import MOCK_MODEL_ID
from app.events.publisher import event_publisher
from app.services import research

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="requires disposable TEST_DATABASE_URL"
)


@pytest_asyncio.fixture
async def database(monkeypatch):
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"], poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    for module in (research, runs, knowledge, capabilities):
        monkeypatch.setattr(module, "SessionLocal", factory)
    yield factory
    await engine.dispose()


async def create_run(query="test"):
    return await research.research_service.create_run(query, MOCK_MODEL_ID)


@pytest.mark.parametrize("length", [230, 231, 10_000])
async def test_persist_full_query_and_bounded_title(database, monkeypatch, length):
    from app.ai.providers.mock import MockProvider
    from app.tools.gateway import MockFetchUrlTool, MockWebSearchTool

    mock = MockProvider()

    async def tool(name, arguments):
        return await (MockWebSearchTool() if name == "web_search" else MockFetchUrlTool()).execute(
            arguments
        )

    monkeypatch.setattr(agent.tool_gateway, "execute", tool)
    monkeypatch.setattr(agent.model_gateway, "generate", mock.generate)
    query = "x" * length
    before_creation = datetime.now(UTC)
    run = await create_run(query)
    after_creation = datetime.now(UTC)
    await research.research_service.execute(run.id, query, MOCK_MODEL_ID)
    async with database() as session:
        saved = await session.get(Run, run.id)
        item = await session.scalar(select(ResearchItem).where(ResearchItem.run_id == run.id))
        assert saved.status == "COMPLETED"
        assert item.query == query and len(item.title) == 240
        assert before_creation <= saved.created_at <= after_creation


async def test_cancel_during_evaluation_prevents_report(database, monkeypatch):
    run = await create_run()
    monkeypatch.setattr(
        research.research_agent,
        "run",
        AsyncMock(return_value=ResearchReport(title="test", summary="test")),
    )

    async def evaluator(*args):
        await runs.cancel_run(run.id)
        return []

    monkeypatch.setattr(research, "evaluate_research", evaluator)
    await research.research_service.execute(run.id, "test", MOCK_MODEL_ID)
    async with database() as session:
        assert (await session.get(Run, run.id)).status == "CANCELLED"
        assert (
            await session.scalar(select(ResearchItem).where(ResearchItem.run_id == run.id)) is None
        )
    with pytest.raises(HTTPException) as error:
        await knowledge.save_research_to_knowledge(run.id)
    assert error.value.status_code == 409


async def test_evaluation_failure_is_atomic_and_traced(database, monkeypatch):
    run = await create_run()
    monkeypatch.setattr(
        research.research_agent,
        "run",
        AsyncMock(return_value=ResearchReport(title="test", summary="test")),
    )
    monkeypatch.setattr(
        research, "evaluate_research", AsyncMock(side_effect=RuntimeError("failed"))
    )
    with pytest.raises(RuntimeError):
        await research.research_service.execute(run.id, "test", MOCK_MODEL_ID)
    async with database() as session:
        assert (await session.get(Run, run.id)).status == "FAILED"
        assert (
            await session.scalar(select(ResearchItem).where(ResearchItem.run_id == run.id)) is None
        )
        events = (
            await session.scalars(select(RunEvent.event_type).where(RunEvent.run_id == run.id))
        ).all()
        assert "evaluation.failed" in events and "run.failed" in events


async def test_concurrent_promotion_and_terminal_sse(database, monkeypatch):
    run = await create_run()
    monkeypatch.setattr(
        research.research_agent,
        "run",
        AsyncMock(return_value=ResearchReport(title="test", summary="test")),
    )
    await research.research_service.execute(run.id, "test", MOCK_MODEL_ID)
    results = await asyncio.gather(
        *(knowledge.save_research_to_knowledge(run.id) for _ in range(6))
    )
    assert len({r["data"]["id"] for r in results}) == 1
    assert sum(r["meta"]["created"] for r in results) == 1
    async with database() as session:
        last = await session.scalar(
            select(func.max(RunEvent.sequence)).where(RunEvent.run_id == run.id)
        )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(KnowledgeItem)
                .where(KnowledgeItem.id == results[0]["data"]["id"])
            )
            == 1
        )
    request = Request(
        {"type": "http", "headers": [(b"last-event-id", str(last).encode())]},
        receive=AsyncMock(return_value={"type": "http.request", "body": b""}),
    )
    stream = await runs.stream_events(run.id, request)
    assert [chunk async for chunk in stream.body_iterator] == []
    with pytest.raises(HTTPException) as error:
        await runs.stream_events(uuid4(), request)
    assert error.value.status_code == 404
    with pytest.raises(HTTPException) as error:
        await runs.cancel_run(run.id)
    assert error.value.status_code == 409


async def test_concurrent_event_sequences(database):
    run = await create_run()

    async def emit():
        async with database() as session:
            return await event_publisher.emit(session, run.id, "test.concurrent", "test")

    events = await asyncio.gather(*(emit() for _ in range(8)))
    assert sorted(e.sequence for e in events) == list(range(2, 10))


async def test_cancel_races_final_commit(database, monkeypatch):
    run = await create_run()
    monkeypatch.setattr(
        research.research_agent,
        "run",
        AsyncMock(return_value=ResearchReport(title="race", summary="race")),
    )
    reached = asyncio.Event()
    finish = asyncio.Event()
    original_emit = event_publisher.emit

    async def emit(session, run_id, kind, source, payload=None):
        if kind == "run.completed":
            reached.set()
            await finish.wait()
        return await original_emit(session, run_id, kind, source, payload)

    monkeypatch.setattr(event_publisher, "emit", emit)
    execution = asyncio.create_task(
        research.research_service.execute(run.id, "race", MOCK_MODEL_ID)
    )
    await asyncio.wait_for(reached.wait(), 5)
    cancellation = asyncio.create_task(runs.cancel_run(run.id))
    finish.set()
    await execution
    with pytest.raises(HTTPException) as error:
        await cancellation
    assert error.value.status_code == 409
    async with database() as session:
        assert (await session.get(Run, run.id)).status == "COMPLETED"


async def test_registration_and_relation_concurrency(database):
    from app.ai.registry import RegisteredModel
    from app.ai.schemas import ModelCapabilities
    from app.db.models import Model, Provider
    from app.domain.constants import configured_model_id
    from app.services.model_registry import ensure_registered_model

    provider = "test-" + uuid4().hex
    model_id = configured_model_id(provider, "one")
    registered = RegisteredModel(
        id=str(model_id),
        provider=provider,
        model_key="one",
        display_name="test",
        capabilities=ModelCapabilities(),
    )

    async def register():
        async with database() as session:
            await ensure_registered_model(session, model_id, registered)
            await session.commit()

    await asyncio.gather(*(register() for _ in range(5)))
    async with database() as session:
        assert (
            await session.scalar(
                select(func.count()).select_from(Model).where(Model.id == model_id)
            )
            == 1
        )
        assert (
            await session.scalar(
                select(func.count()).select_from(Provider).where(Provider.provider_type == provider)
            )
            == 1
        )

    tech = await capabilities.create_technology(capabilities.TechnologyCreate(name=uuid4().hex))
    tech_id = UUID(tech["data"]["technology"]["id"])
    results = await asyncio.gather(
        *(
            capabilities.upsert_capability(tech_id, capabilities.CapabilityUpdate(level=2))
            for _ in range(5)
        )
    )
    assert len({r["data"]["capability"]["id"] for r in results}) == 1
    evidence = await capabilities.create_evidence(
        capabilities.EvidenceCreate(title="test", evidence_type="PROJECT")
    )
    capability_id = UUID(results[0]["data"]["capability"]["id"])
    evidence_id = UUID(evidence["data"]["id"])
    await asyncio.gather(
        *(capabilities.link_capability_evidence(capability_id, evidence_id) for _ in range(5))
    )
    assert len((await capabilities.list_capability_evidences(capability_id))["data"]) == 1


async def test_sse_recovers_terminal_event_from_database(database):
    run = await create_run()
    request = Request(
        {"type": "http", "headers": []},
        receive=AsyncMock(return_value={"type": "http.request", "body": b""}),
    )
    stream = await runs.stream_events(run.id, request, after_sequence=1)
    assert await anext(stream.body_iterator) == ": heartbeat\n\n"
    async with database() as session:
        saved = await session.get(Run, run.id)
        saved.status = "CANCELLED"
        await event_publisher.emit(session, run.id, "run.cancelled", "test")
    event = await asyncio.wait_for(anext(stream.body_iterator), 3)
    assert "event: run.cancelled" in event
    with pytest.raises(StopAsyncIteration):
        await anext(stream.body_iterator)
