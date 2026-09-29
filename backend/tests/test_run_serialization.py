from datetime import UTC, datetime
from uuid import uuid4

from app.api.routes.runs import serialize_run
from app.db.models import Run


def test_serialize_run_exposes_lab_metrics() -> None:
    run = Run(
        id=uuid4(),
        agent_version_id=uuid4(),
        model_id=uuid4(),
        status="COMPLETED",
        task_type="research",
        input_text="Compare frameworks",
        output_text="Result",
        latency_ms=1200,
        input_tokens=100,
        output_tokens=50,
        estimated_cost=0.0123,
        currency="USD",
        created_at=datetime.now(UTC),
    )

    payload = serialize_run(run)

    assert payload["task_type"] == "research"
    assert payload["latency_ms"] == 1200
    assert payload["input_tokens"] == 100
    assert payload["output_tokens"] == 50
    assert payload["estimated_cost"] == 0.0123
