from uuid import uuid4

import pytest

from app.runtime.run_control import RunCancelled, RunControl


def test_run_control_requests_and_clears_cancellation() -> None:
    control = RunControl()
    run_id = uuid4()

    assert not control.is_cancelled(run_id)

    control.request_cancel(run_id)
    assert control.is_cancelled(run_id)

    with pytest.raises(RunCancelled):
        control.raise_if_cancelled(run_id)

    control.clear(run_id)
    assert not control.is_cancelled(run_id)
