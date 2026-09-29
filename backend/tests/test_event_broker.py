import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.events.broker import EventBroker
from app.events.schemas import EventEnvelope


@pytest.mark.asyncio
async def test_event_broker_publishes_to_subscriber() -> None:
    broker = EventBroker()
    run_id = uuid4()
    queue = broker.subscribe(run_id)
    event = EventEnvelope(
        id=uuid4(),
        run_id=run_id,
        sequence=1,
        type="run.started",
        timestamp=datetime.now(timezone.utc),
        source="test",
        payload={},
    )

    await broker.publish(event)
    received = await queue.get()

    assert received.sequence == 1
    assert received.type == "run.started"
