import asyncio
from collections import defaultdict
from uuid import UUID

from app.events.schemas import EventEnvelope


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: dict[UUID, set[asyncio.Queue[EventEnvelope]]] = defaultdict(set)

    def subscribe(self, run_id: UUID) -> asyncio.Queue[EventEnvelope]:
        queue: asyncio.Queue[EventEnvelope] = asyncio.Queue()
        self._subscribers[run_id].add(queue)
        return queue

    def unsubscribe(self, run_id: UUID, queue: asyncio.Queue[EventEnvelope]) -> None:
        subscribers = self._subscribers.get(run_id)
        if subscribers is None:
            return
        subscribers.discard(queue)
        if not subscribers:
            self._subscribers.pop(run_id, None)

    async def publish(self, event: EventEnvelope) -> None:
        for queue in tuple(self._subscribers.get(event.run_id, ())):
            await queue.put(event)


event_broker = EventBroker()
