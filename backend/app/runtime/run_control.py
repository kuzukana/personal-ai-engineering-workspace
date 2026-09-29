from uuid import UUID


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


run_control = RunControl()
