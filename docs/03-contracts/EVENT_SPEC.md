# Personal AI Engineering Workspace — Event Specification

**Document Type:** Event Contract Specification  
**Version:** 0.1  
**Status:** Draft  
**Project Stage:** MVP Contract Design  
**Owner:** Project Owner  
**Last Updated:** 2026-09-29  

**Related Documents:**
- `../01-design/TECHNICAL_DESIGN.md`
- `../02-ai/AI_SYSTEM_SPEC.md`
- `../02-ai/AGENT_SPEC.md`
- `../02-ai/MODEL_SPEC.md`
- `../02-ai/EVALUATION.md`
- `DATA_MODEL.md`
- `API_SPEC.md`
- `../04-quality/OBSERVABILITY.md`
- `../adr/ADR-004-sse-streaming.md`

---

# 1. Purpose

本文档定义 Personal AI Engineering Workspace V0.1 的统一事件模型。

事件系统用于连接：

```text
Agent Runtime

Model Gateway

Tool Gateway

Evaluation Engine

Persistence

SSE

Frontend Agent Lab
```

目标是确保：

- 所有 Agent 执行行为可以被追踪；
- 不同 Provider 的 Streaming Event 可以统一；
- Frontend 不依赖厂商事件格式；
- Run Timeline 可以稳定重建；
- Tool、Model、Evaluation 行为可以统一观察；
- 未来可以支持 Replay、Debugging、Experiment 和 Observability。

核心原则：

> **Every meaningful runtime transition should produce a normalized, ordered and traceable event.**

---

# 2. Event System Role

事件系统不是业务数据库的替代品。

它负责：

```text
what happened
when it happened
in what order
within which run
```

例如：

```text
Run started
↓
Agent step started
↓
Model call started
↓
Tool call started
↓
Tool call completed
↓
Model completed
↓
Agent step completed
↓
Run completed
```

---

# 3. Event Design Principles

## 3.1 Normalized

内部事件格式与 OpenAI、Anthropic、DeepSeek、Kimi 等 Provider 解耦。

---

## 3.2 Ordered

同一个 Run 中 Event 必须有稳定顺序。

使用：

```text
sequence
```

而不是只依赖 timestamp。

---

## 3.3 Append-only

历史 Event 默认不可修改。

错误修正通过：

```text
append new event
```

完成。

---

## 3.4 Traceable

所有 Event 至少关联：

```text
run_id
```

必要时再关联：

```text
agent_step
model_call_id
tool_call_id
evaluation_id
```

---

## 3.5 Forward-compatible

新 Event Type 可以增加，但老 Frontend 不应因此崩溃。

未知 Event：

```text
ignore safely
```

并保留 Raw Payload。

---

# 4. Event Envelope

所有事件统一使用 Event Envelope。

建议结构：

```json
{
  "id": "uuid",
  "run_id": "uuid",
  "sequence": 42,
  "type": "tool.completed",
  "timestamp": "2026-09-29T12:00:00Z",
  "source": "tool_gateway",
  "payload": {},
  "metadata": {}
}
```

---

# 5. Required Event Fields

必须字段：

```text
id

run_id

sequence

type

timestamp

source

payload
```

可选：

```text
metadata
```

---

# 6. Event ID

`id`：

```text
UUID
```

用于：

- 去重；
- 持久化；
- Debug；
- Future distributed processing。

---

# 7. Run ID

每个 Event 必须有：

```text
run_id
```

所有 Runtime Event 都属于一个 Run。

Future 非 Run 型系统事件可以另建 Event Domain，不复用本 Contract。

---

# 8. Sequence

`sequence`：

```text
positive monotonic integer per run
```

例如：

```text
1
2
3
4
...
```

唯一约束：

```text
(run_id, sequence)
```

---

# 9. Timestamp

统一：

```text
RFC 3339 / ISO 8601
UTC
```

例如：

```text
2026-09-29T12:34:56.123Z
```

Frontend 根据用户时区展示。

---

# 10. Source

建议枚举：

```text
api

agent_runtime

model_gateway

provider_adapter

tool_gateway

evaluation_engine

system
```

Future 可扩展。

---

# 11. Event Type Naming

统一格式：

```text
domain.action
```

例如：

```text
run.started

agent.step.started

model.completed

tool.failed

evaluation.completed
```

不使用：

```text
RUN_STARTED
```

避免和数据库 Enum 混淆。

---

# 12. Core Event Domains

V0.1：

```text
run.*

agent.*

model.*

tool.*

evaluation.*
```

Future：

```text
approval.*

memory.*

experiment.*

system.*
```

---

# 13. Run Events

V0.1：

```text
run.created

run.started

run.completed

run.failed

run.cancelled
```

Future：

```text
run.paused

run.resumed

run.warning
```

---

# 14. run.created

表示 Run 已持久化，但尚未开始执行。

Payload：

```json
{
  "agent_id": "research-agent",
  "agent_version": "0.1",
  "model_id": "uuid"
}
```

---

# 15. run.started

表示 Runtime 已开始处理任务。

Payload：

```json
{
  "task_type": "research"
}
```

---

# 16. run.completed

表示 Runtime 正常结束。

注意：

```text
run.completed
```

只表示：

```text
runtime lifecycle completed
```

不等于：

```text
evaluation passed
```

Payload：

```json
{
  "latency_ms": 12345,
  "warnings": []
}
```

---

# 17. run.failed

表示 Run 无法继续完成。

Payload：

```json
{
  "error_code": "MODEL_ERROR",
  "message": "Provider request failed",
  "recoverable": false
}
```

禁止在 Event 中暴露：

```text
API key
secret
full stack trace
```

详细 traceback 写 Server Log。

---

# 18. run.cancelled

表示用户或系统主动终止 Run。

Payload：

```json
{
  "reason": "user_cancelled"
}
```

---

# 19. Agent Events

V0.1：

```text
agent.started

agent.step.started

agent.step.completed

agent.step.failed

agent.completed
```

---

# 20. agent.started

Payload：

```json
{
  "agent_id": "research-agent",
  "agent_version": "0.1"
}
```

---

# 21. agent.step.started

Payload：

```json
{
  "step_key": "plan_search",
  "step_name": "Plan Search",
  "step_index": 2
}
```

---

# 22. agent.step.completed

Payload：

```json
{
  "step_key": "plan_search",
  "step_index": 2,
  "latency_ms": 850
}
```

---

# 23. agent.step.failed

Payload：

```json
{
  "step_key": "verify_claims",
  "step_index": 6,
  "error_code": "STRUCTURED_OUTPUT_ERROR",
  "message": "Verification output failed validation",
  "recoverable": true
}
```

---

# 24. agent.completed

表示 Agent Workflow 本身结束。

通常先于：

```text
run.completed
```

因为后面可能还有：

```text
post-run evaluation
persistence
cleanup
```

---

# 25. Model Events

V0.1：

```text
model.started

model.text.delta

model.reasoning.delta

model.tool_call.started

model.tool_call.arguments.delta

model.tool_call.completed

model.usage

model.completed

model.failed
```

---

# 26. model.started

Payload：

```json
{
  "model_call_id": "uuid",
  "provider": "openai",
  "model": "model-key"
}
```

---

# 27. model.text.delta

用于 Streaming 文本。

Payload：

```json
{
  "model_call_id": "uuid",
  "delta": "partial text"
}
```

此事件通常：

```text
high frequency
```

Frontend 应增量拼接。

---

# 28. model.reasoning.delta

仅当 Provider 明确允许返回可展示 reasoning-like stream 时使用。

Payload：

```json
{
  "model_call_id": "uuid",
  "delta": "..."
}
```

如果 Provider 不提供，不生成该事件。

禁止伪造 reasoning。

---

# 29. model.tool_call.started

Payload：

```json
{
  "model_call_id": "uuid",
  "tool_call_id": "provider-or-internal-id",
  "tool_name": "web_search"
}
```

---

# 30. model.tool_call.arguments.delta

用于 Streaming Tool Arguments。

Payload：

```json
{
  "model_call_id": "uuid",
  "tool_call_id": "id",
  "delta": "{\"query\":"
}
```

Frontend 通常不需要直接展示该事件。

主要用于 Debug / Trace。

---

# 31. model.tool_call.completed

Payload：

```json
{
  "model_call_id": "uuid",
  "tool_call_id": "id",
  "tool_name": "web_search",
  "arguments": {
    "query": "LangGraph PydanticAI"
  }
}
```

---

# 32. model.usage

用于统一 Token Usage。

Payload：

```json
{
  "model_call_id": "uuid",
  "input_tokens": 1200,
  "output_tokens": 450,
  "reasoning_tokens": null,
  "cached_input_tokens": null,
  "estimated_cost": 0.0123,
  "currency": "USD"
}
```

未知值使用：

```text
null
```

而不是 0。

---

# 33. model.completed

Payload：

```json
{
  "model_call_id": "uuid",
  "finish_reason": "STOP",
  "latency_ms": 2200,
  "ttft_ms": 340
}
```

---

# 34. model.failed

Payload：

```json
{
  "model_call_id": "uuid",
  "error_code": "PROVIDER_RATE_LIMIT",
  "message": "Rate limited by provider",
  "recoverable": true
}
```

---

# 35. Provider Event Normalization

Provider 原生事件：

```text
OpenAI event

Anthropic event

DeepSeek event

Kimi event
```

必须先进入：

```text
Provider Adapter
```

再转换成：

```text
Internal Event Contract
```

Frontend 不解析 Vendor Event。

---

# 36. Tool Events

V0.1：

```text
tool.started

tool.completed

tool.failed

tool.denied
```

Future：

```text
tool.cancelled

tool.retrying
```

---

# 37. tool.started

Payload：

```json
{
  "tool_call_id": "uuid",
  "tool_name": "web_search",
  "tool_version": "0.1",
  "risk_level": "LOW"
}
```

---

# 38. tool.completed

Payload：

```json
{
  "tool_call_id": "uuid",
  "tool_name": "web_search",
  "latency_ms": 720,
  "result_summary": {
    "result_count": 8
  }
}
```

不要默认把完整网页内容塞进 Event Payload。

完整 Tool Output 保存在 ToolCall persistence 或专用存储中。

---

# 39. tool.failed

Payload：

```json
{
  "tool_call_id": "uuid",
  "tool_name": "fetch_url",
  "error_code": "TOOL_TIMEOUT",
  "message": "Request timed out",
  "recoverable": true
}
```

---

# 40. tool.denied

表示 Permission Policy 阻止 Tool Execution。

Payload：

```json
{
  "tool_call_id": "uuid",
  "tool_name": "git_push",
  "reason": "approval_required"
}
```

---

# 41. Evaluation Events

V0.1：

```text
evaluation.started

evaluation.metric.completed

evaluation.failed

evaluation.completed
```

---

# 42. evaluation.started

Payload：

```json
{
  "evaluator_key": "research-deterministic",
  "evaluator_version": "0.1"
}
```

---

# 43. evaluation.metric.completed

Payload：

```json
{
  "metric_name": "report_schema_valid",
  "evaluation_type": "DETERMINISTIC",
  "status": "PASS",
  "score": null
}
```

---

# 44. evaluation.failed

表示 Evaluator 自身失败。

Payload：

```json
{
  "evaluator_key": "research-quality-judge",
  "error_code": "PROVIDER_TIMEOUT",
  "message": "Judge model unavailable"
}
```

这不会自动把 Run 改为 FAILED。

---

# 45. evaluation.completed

Payload：

```json
{
  "evaluator_key": "research-deterministic",
  "metric_count": 7,
  "failed_metric_count": 0
}
```

---

# 46. Approval Events

Future Human-in-the-loop：

```text
approval.requested

approval.approved

approval.rejected
```

V0.1 可以预留 Event Type，但不要求完整实现。

---

# 47. approval.requested

建议 Payload：

```json
{
  "approval_id": "uuid",
  "action_type": "tool_call",
  "tool_name": "git_push",
  "risk_level": "HIGH",
  "summary": "Push changes to remote repository"
}
```

---

# 48. Event Metadata

metadata 用于辅助信息。

例如：

```json
{
  "trace_id": "uuid",
  "span_id": "uuid",
  "schema_version": "1"
}
```

核心业务字段不要隐藏在 metadata。

---

# 49. Event Schema Version

V0.1 建议 Event Envelope 加：

```text
schema_version
```

可以放：

```text
metadata.schema_version
```

Future Contract 稳定后可升级为顶层字段。

---

# 50. SSE Transport

Frontend 通过：

```text
GET /api/v1/runs/{run_id}/events
```

订阅 Run Event Stream。

传输协议：

```text
Server-Sent Events
```

---

# 51. SSE Event Format

建议：

```text
id: <event-id>
event: <event-type>
data: <json>

```

例如：

```text
id: 018...
event: agent.step.started
data: {"run_id":"...","sequence":4,...}

```

---

# 52. SSE id

SSE 的：

```text
id:
```

优先使用：

```text
sequence
```

或稳定 Event ID。

V0.1 推荐：

```text
sequence
```

便于断线续传。

---

# 53. Reconnect

Browser SSE 断线后可以带：

```text
Last-Event-ID
```

Server 应根据 sequence 从数据库 / runtime buffer 中恢复后续事件。

Future 如果 Event 数量很大，可做 retention / compaction。

---

# 54. Initial Snapshot

Frontend 打开一个已经运行一半的 Run 时：

```text
GET Run
↓
GET existing events
↓
subscribe SSE
```

或者 SSE Endpoint 支持从：

```text
after_sequence
```

开始返回。

具体 API 在 API_SPEC 中定义。

---

# 55. Event Persistence

以下事件建议持久化：

```text
run.*

agent.*

model.started

model.completed

model.failed

model.usage

tool.*

evaluation.*
```

高频：

```text
model.text.delta
model.reasoning.delta
model.tool_call.arguments.delta
```

是否全部长期持久化需要权衡。

---

# 56. Streaming Delta Persistence

V0.1 推荐：

```text
stream to frontend
```

但不要求把每个 Token Delta 永久存数据库。

可以选择：

```text
buffer
↓
aggregate
↓
persist final model output
```

否则 RunEvent 表可能极度膨胀。

---

# 57. Persistent vs Ephemeral Events

Persistent：

```text
run.started
agent.step.*
model.started
model.completed
model.failed
model.usage
tool.*
evaluation.*
run.completed
run.failed
```

Ephemeral Candidate：

```text
model.text.delta
model.reasoning.delta
model.tool_call.arguments.delta
```

---

# 58. Event Delivery Guarantees

V0.1 不承诺：

```text
exactly once delivery
```

应按：

```text
at-least-once tolerant
```

设计 Frontend。

因此 Event Consumer 应能根据：

```text
event id / sequence
```

去重。

---

# 59. Ordering Guarantee

系统保证：

```text
ordered within a run
```

不保证：

```text
global ordering across different runs
```

这足以支撑 Agent Timeline。

---

# 60. Event Generation Ownership

每个事件必须由明确组件负责。

例如：

```text
run.*              → Run Service / Runtime

agent.*            → Agent Runtime

model.*            → Model Gateway / Provider Adapter

tool.*             → Tool Gateway

evaluation.*       → Evaluation Engine
```

避免多个组件重复发同一语义事件。

---

# 61. Duplicate Event Prevention

例如：

```text
model.completed
```

只应由：

```text
Model Gateway
```

产生。

Agent Runtime 不应再复制一份 model.completed。

---

# 62. Error Event Relationship

Error Event 应和具体失败对象关联。

例如：

```text
tool.failed
```

有：

```text
tool_call_id
```

```text
model.failed
```

有：

```text
model_call_id
```

便于 Failure Attribution。

---

# 63. Error Codes

Event 中的 error_code 使用内部标准错误码，而不是 Vendor 原始字符串。

例如：

```text
PROVIDER_RATE_LIMIT

PROVIDER_TIMEOUT

MODEL_CAPABILITY_ERROR

TOOL_TIMEOUT

TOOL_PERMISSION_DENIED

STRUCTURED_OUTPUT_ERROR

WORKFLOW_ERROR

DATABASE_ERROR
```

详细 Error Taxonomy 在代码实现阶段统一 Enum。

---

# 64. User-facing Message

Event Payload 中的：

```text
message
```

必须适合日志和 UI。

不要返回：

```text
raw exception repr
```

---

# 65. Sensitive Data Redaction

Event Payload 不得包含：

```text
API key

password

OAuth token

Authorization header

secret environment variable
```

Tool Input 也需要经过敏感字段过滤后再持久化。

---

# 66. Prompt Data in Events

V0.1 不默认把完整 Prompt 写入 Event。

Run / Model Call 记录：

```text
prompt_version
```

必要时在受控 Debug 模式下保存 Prompt Snapshot。

原因：

- 可能包含个人数据；
- Event Payload 会膨胀；
- Prompt 应有独立版本管理。

---

# 67. Tool Output Data in Events

Event 只保存摘要。

例如：

```json
{
  "result_count": 10
}
```

完整 Tool Output：

```text
tool_calls.output_json
```

或 Future Blob Storage。

---

# 68. Agent State in Events

不建议每一步把完整 State 写入 Event。

可以保存：

```text
changed_keys

summary
```

Future Debug 模式可以保存 State Snapshot。

---

# 69. Example Research Run Timeline

```text
1  run.created
2  run.started
3  agent.started
4  agent.step.started       understand
5  model.started
6  model.completed
7  agent.step.completed     understand
8  agent.step.started       plan_search
9  model.started
10 model.completed
11 agent.step.completed     plan_search
12 agent.step.started       search
13 tool.started             web_search
14 tool.completed           web_search
15 agent.step.completed     search
16 agent.step.started       read
17 tool.started             fetch_url
18 tool.completed           fetch_url
19 agent.step.completed     read
20 agent.step.started       verify
21 model.started
22 model.completed
23 agent.step.completed     verify
24 agent.step.started       synthesize
25 model.started
26 model.completed
27 agent.step.completed     synthesize
28 agent.completed
29 evaluation.started
30 evaluation.metric.completed
31 evaluation.completed
32 run.completed
```

---

# 70. Frontend Timeline Mapping

Frontend 不应该自己猜测状态。

例如：

```text
agent.step.started
→ step status = RUNNING

agent.step.completed
→ step status = COMPLETED

agent.step.failed
→ step status = FAILED
```

---

# 71. UI Progress

Research Progress UI：

```text
✓ Understand task

✓ Plan search

● Reading sources

○ Verify claims

○ Generate report
```

应由 Event Stream 驱动。

---

# 72. Event Replay

Future Replay：

```text
load persisted events
↓
reapply in sequence order
↓
reconstruct timeline
```

V0.1 只要求 Timeline Reconstruction，不要求真正重新执行 Agent。

---

# 73. Event Compaction

如果长期 Event 数据过大，Future 可以：

```text
compact high-frequency events
```

例如将多个：

```text
model.text.delta
```

聚合成：

```text
model.output.snapshot
```

V0.1 暂不实现。

---

# 74. Event Retention

单用户 V0.1 可以长期保留持久化 Event。

Future SaaS：

```text
retention policy
```

单独定义。

---

# 75. Observability Integration

Event 与 Log 不完全相同。

Event：

```text
domain behavior
```

Log：

```text
implementation diagnostics
```

例如：

```text
tool.failed
```

是 Event。

```text
aiohttp connection pool exhausted
```

是 Log。

---

# 76. OpenTelemetry Direction

Future Event metadata 可以包含：

```text
trace_id

span_id
```

实现：

```text
Run Event
↔
OpenTelemetry Trace
```

V0.1 不要求完整接入。

---

# 77. Event Testing

Event Contract 必须有测试。

至少验证：

```text
required fields

valid event type

sequence monotonicity

JSON serialization

secret redaction

SSE serialization
```

---

# 78. Workflow Event Test

Research Agent 集成测试应验证关键事件顺序。

例如：

```text
run.started
before
agent.started

agent.step.started
before
agent.step.completed

run.completed
after
agent.completed
```

---

# 79. Provider Streaming Contract Test

不同 Adapter 必须验证：

```text
vendor stream
↓
normalized internal events
```

例如：

```text
text delta

tool call

usage

completion
```

---

# 80. Event Consumer Rules

Consumer 必须：

```text
ignore unknown event types safely

deduplicate by id/sequence

respect sequence

not trust arrival timestamp for order

not assume every optional event exists
```

---

# 81. Backward Compatibility

增加新 Event Type：

```text
non-breaking
```

删除 / 重命名 Event Type：

```text
breaking
```

修改必填 Payload 字段：

```text
potentially breaking
```

---

# 82. Event Version Evolution

Future Event Schema 大版本升级时：

```text
schema_version
```

用于 Consumer 分支解析。

V0.1 先保持：

```text
schema_version = 1
```

---

# 83. MVP Required Event Types

第一版代码至少实现：

```text
run.created
run.started
run.completed
run.failed
run.cancelled

agent.started
agent.step.started
agent.step.completed
agent.step.failed
agent.completed

model.started
model.text.delta
model.usage
model.completed
model.failed

tool.started
tool.completed
tool.failed

evaluation.started
evaluation.metric.completed
evaluation.completed
evaluation.failed
```

---

# 84. MVP Acceptance Criteria

Event Layer V0.1 完成标准：

1. 所有 Event 使用统一 Envelope；
2. 同一 Run 内有单调递增 sequence；
3. Run / Agent / Model / Tool / Evaluation 均有基础事件；
4. Provider Streaming 被转换为内部事件；
5. Frontend 可以通过 SSE 接收事件；
6. SSE 断线后能够根据 sequence 恢复；
7. Unknown Event 不导致 Frontend 崩溃；
8. Secret 不进入 Event Payload；
9. Tool 完整大输出不直接写 Event；
10. 持久化 Event 可以重建 Run Timeline；
11. Evaluation Failure 不错误地转成 Run Failure；
12. Event Contract 有自动测试。

---

# 85. Future Event Types

后续可能增加：

```text
approval.*

memory.*

experiment.*

benchmark.*

artifact.*

coding.*

system.*
```

新增前必须确认是否属于：

```text
runtime domain event
```

而不是普通 Log。

---

# 86. Anti-patterns

禁止：

## Vendor Events in Frontend

让前端分别理解 OpenAI / Anthropic Event。

## Timestamp-only Ordering

只靠毫秒时间判断执行顺序。

## Full State Dump per Event

每一步保存巨大 Agent State。

## Full Tool Content in Event

把整篇网页塞进 tool.completed。

## Secrets in Trace

把 Authorization Header 等保存到 Event。

## Event as Database Replacement

所有业务状态只存在 Event Payload，不存在正式业务表。

---

# 87. Final Event Architecture

整体结构：

```text
Agent Runtime
Model Gateway
Tool Gateway
Evaluation Engine
      │
      ▼
 Event Publisher
      │
      ├── Persistence
      │
      └── SSE Stream
              │
              ▼
           Frontend
```

事件流最终支持：

```text
Live Progress

Run Timeline

Observability

Evaluation

Debugging

Regression

Future Replay
```

核心原则：

> **Events describe the execution history of a run; they are normalized, ordered, append-only and safe to consume across providers and clients.**
