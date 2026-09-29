from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RunEvent
from app.events.broker import event_broker
from app.events.schemas import EventEnvelope


class EventPublisher:
    async def emit(
        self,
        session: AsyncSession,
        run_id: UUID,
        event_type: str,
        source: str,
        payload: dict[str, Any] | None = None,
    ) -> EventEnvelope:
        result = await session.execute(
            select(func.coalesce(func.max(RunEvent.sequence), 0)).where(RunEvent.run_id == run_id)
        )
        sequence = int(result.scalar_one()) + 1
        timestamp = datetime.now(timezone.utc)
        row = RunEvent(
            id=uuid4(),
            run_id=run_id,
            sequence=sequence,
            event_type=event_type,
            payload_json=payload or {},
            created_at=timestamp,
        )
        session.add(row)
        await session.commit()
        event = EventEnvelope(
            id=row.id,
            run_id=run_id,
            sequence=sequence,
            type=event_type,
            timestamp=timestamp,
            source=source,
            payload=payload or {},
        )
        await event_broker.publish(event)
        return event


event_publisher = EventPublisher()
