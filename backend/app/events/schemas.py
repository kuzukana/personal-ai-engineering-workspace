from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    id: UUID
    run_id: UUID
    sequence: int
    type: str
    timestamp: datetime
    source: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=lambda: {"schema_version": "1"})
