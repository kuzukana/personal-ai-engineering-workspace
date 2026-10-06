from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RunData(BaseModel):
    id: UUID
    status: str
    task_type: str | None
    model_id: UUID
    input_text: str
    output_text: str | None
    structured_output: dict | None
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None
    estimated_cost: float | None
    currency: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class RunResponse(BaseModel):
    data: RunData


class RunsResponse(BaseModel):
    data: list[RunData]
