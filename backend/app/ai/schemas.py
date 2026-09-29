from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FinishReason(StrEnum):
    STOP = "STOP"
    LENGTH = "LENGTH"
    TOOL_CALL = "TOOL_CALL"
    CONTENT_FILTER = "CONTENT_FILTER"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class ModelCapabilities(BaseModel):
    streaming: bool = True
    tools: bool = False
    parallel_tools: bool = False
    structured_output: bool = False
    vision: bool = False
    reasoning: bool = False
    system_prompt: bool = True
    context_window: int | None = None
    max_output_tokens: int | None = None


class ModelUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    cached_input_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None
    currency: str | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str
    content: str
    name: str | None = None


class ModelRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    model_id: str
    messages: list[ChatMessage]
    system_prompt: str | None = None
    tools: list[ToolDefinition] = Field(default_factory=list)
    temperature: float | None = None
    max_output_tokens: int | None = None
    structured_schema: dict[str, Any] | None = None
    stream: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    request_id: UUID
    model_id: str
    provider: str
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    structured_output: dict[str, Any] | None = None
    usage: ModelUsage = Field(default_factory=ModelUsage)
    finish_reason: FinishReason = FinishReason.STOP
    latency_ms: int | None = None
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class ModelEvent(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
