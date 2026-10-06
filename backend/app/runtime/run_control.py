from uuid import UUID

from sqlalchemy import select

from app.db.models import Run


class RunCancelled(RuntimeError):
    pass


class RunControl:
    def __init__(self) -> None:
        self._cancelled: set[UUID] = set()

    def request_cancel(self, run_id: UUID) -> None:
        self._cancelled.add(run_id)

    def is_cancelled(self, run_id: UUID) -> bool:
        return run_id in self._cancelled

    def raise_if_cancelled(self, run_id: UUID) -> None:
        if self.is_cancelled(run_id):
            raise RunCancelled(f"Run cancelled: {run_id}")

    def clear(self, run_id: UUID) -> None:
        self._cancelled.discard(run_id)

    async def checkpoint(self, session, run_id: UUID) -> None:
        self.raise_if_cancelled(run_id)
        status = await session.scalar(select(Run.status).where(Run.id == run_id))
        if status == "CANCELLATION_REQUESTED":
            raise RunCancelled(f"Run cancelled: {run_id}")


run_control = RunControl()
