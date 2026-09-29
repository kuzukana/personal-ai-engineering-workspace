# Personal AI Engineering Workspace — API Specification

**Document Type:** API Contract Specification  
**Version:** 0.1  
**Status:** Draft  
**Project Stage:** MVP Contract Design  
**Owner:** Project Owner  
**Last Updated:** 2026-09-29  

**Related Documents:** `DATA_MODEL.md`, `EVENT_SPEC.md`, `../01-design/TECHNICAL_DESIGN.md`, `../02-ai/AGENT_SPEC.md`

---

# 1. Purpose

本文档定义前端与 FastAPI 后端之间的 V0.1 HTTP/SSE 契约。数据库模型不是 API 模型；所有请求和响应必须经过 Pydantic Schema。

基础路径：

```text
/api/v1
```

响应 JSON 使用 `snake_case`。时间使用 UTC RFC3339。ID 使用 UUID 字符串。

# 2. General Response Rules

成功：
```json
{"data": {}, "meta": {}}
```

列表：
```json
{"data": [], "meta": {"limit": 20, "offset": 0, "total": 0}}
```

错误：
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": {},
    "request_id": "uuid"
  }
}
```

禁止返回原始 traceback、secret 或 vendor exception。

# 3. Health

## GET /health

用途：进程存活检查。

响应：
```json
{"status":"ok"}
```

## GET /ready

用途：依赖就绪检查。

响应可包含：
```json
{
  "status":"ready",
  "dependencies":{"database":"ok","redis":"ok"}
}
```

# 4. Models

## GET /models

返回启用模型。

Query：
- `provider` optional
- `capability` optional

响应项：
```json
{
  "id":"uuid",
  "provider":{"id":"uuid","name":"OpenAI"},
  "model_key":"...",
  "display_name":"...",
  "status":"ACTIVE",
  "capabilities":{
    "streaming":true,
    "tools":true,
    "structured_output":true,
    "vision":false,
    "reasoning":true
  }
}
```

## GET /models/{model_id}

返回模型详细能力。

# 5. Research

## POST /research

创建 Research Run。

请求：
```json
{
  "query":"Compare LangGraph and PydanticAI",
  "model_id":"uuid",
  "options":{
    "save_draft":false
  }
}
```

响应：`202 Accepted`

```json
{
  "data":{
    "run_id":"uuid",
    "status":"PENDING",
    "events_url":"/api/v1/runs/{run_id}/events"
  }
}
```

该接口不等待 Agent 完整执行。

## GET /research/{research_id}

返回保存后的研究结果，包括 summary、report、sources、related technologies。

## GET /research

支持：
- `limit`
- `offset`
- `status`
- `query`

# 6. Runs

## GET /runs

Query：
- `agent_id`
- `status`
- `model_id`
- `limit`
- `offset`

返回 Run 摘要。

## GET /runs/{run_id}

返回：
```json
{
  "data":{
    "id":"uuid",
    "status":"RUNNING",
    "agent":{"key":"research-agent","version":"0.1"},
    "model":{"id":"uuid","display_name":"..."},
    "input_text":"...",
    "output_text":null,
    "metrics":{
      "latency_ms":null,
      "input_tokens":null,
      "output_tokens":null,
      "estimated_cost":null
    },
    "created_at":"..."
  }
}
```

## POST /runs/{run_id}/cancel

请求取消尚未结束的 Run。

响应：
```json
{"data":{"run_id":"uuid","status":"CANCELLED"}}
```

取消是 best-effort；已发生的外部副作用不会自动回滚。

# 7. Run Events

## GET /runs/{run_id}/events

Content-Type：
```text
text/event-stream
```

支持：
- HTTP `Last-Event-ID`
- `after_sequence` optional query

SSE：
```text
id: 12
event: agent.step.started
data: {"id":"...","run_id":"...","sequence":12,"type":"agent.step.started",...}

```

未知 event type 必须允许客户端安全忽略。

## GET /runs/{run_id}/events/history

用于非流式读取历史 Event。

Query：
- `after_sequence`
- `limit`

# 8. Evaluations

## GET /runs/{run_id}/evaluations

返回该 Run 的所有 EvaluationResult。

## POST /runs/{run_id}/evaluations

V0.1 仅内部/开发用途，用于手动触发 post-run deterministic evaluation。

请求：
```json
{"evaluator_key":"research-deterministic"}
```

# 9. Knowledge

## POST /knowledge

用于用户确认后保存 Knowledge。

请求：
```json
{
  "knowledge_type":"RESEARCH",
  "title":"LangGraph vs PydanticAI",
  "summary":"...",
  "content_markdown":"...",
  "source_research_id":"uuid",
  "technology_ids":["uuid"]
}
```

## GET /knowledge

支持：
- `type`
- `query`
- `technology_id`
- pagination

## GET /knowledge/{knowledge_id}

## PATCH /knowledge/{knowledge_id}

只允许可编辑字段；不允许修改 ID / created_at。

# 10. Technologies

## GET /technologies

支持 `query`。

## POST /technologies

请求：
```json
{"name":"LangGraph","category":"agent-framework"}
```

名称和 slug 必须唯一。

# 11. Capabilities

## GET /capabilities

可按 `technology_id` / `level` 过滤。

## GET /capabilities/{capability_id}

## PUT /capabilities/{capability_id}

请求：
```json
{
  "level":2,
  "reason":"Can run and modify examples",
  "next_target_level":3,
  "next_action":"Implement a stateful research workflow"
}
```

Level 必须为 0–5。

AI 可以建议，但 V0.1 用户确认后才能更新正式 Capability。

# 12. Evidence

## POST /evidence

请求：
```json
{
  "title":"Implemented SSE research streaming",
  "evidence_type":"GIT_COMMIT",
  "description":"...",
  "url":"https://github.com/...",
  "capability_ids":["uuid"]
}
```

## GET /evidence

## GET /evidence/{evidence_id}

# 13. Providers / Settings

V0.1 API 只暴露非 secret Provider 配置。

## GET /providers

返回：
- name
- status
- base_url
- connection status

不得返回 API Key。

Future 写 Provider Secret 使用独立安全接口，不在 V0.1 实现。

# 14. Validation

FastAPI/Pydantic 负责输入结构校验。

业务层负责：
- model capability compatibility
- entity existence
- run state transitions
- capability level rules
- permission rules

# 15. HTTP Status Codes

```text
200 OK
201 Created
202 Accepted
204 No Content
400 Bad Request
401 Unauthorized (future)
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Rate Limited
500 Internal Server Error
503 Service Unavailable
```

# 16. Error Codes

内部稳定错误码至少包括：

```text
VALIDATION_ERROR
NOT_FOUND
CONFLICT
MODEL_CAPABILITY_ERROR
PROVIDER_AUTH_ERROR
PROVIDER_RATE_LIMIT
PROVIDER_TIMEOUT
PROVIDER_UNAVAILABLE
TOOL_ERROR
TOOL_TIMEOUT
TOOL_PERMISSION_DENIED
STRUCTURED_OUTPUT_ERROR
WORKFLOW_ERROR
DATABASE_ERROR
RUN_NOT_CANCELLABLE
UNKNOWN_ERROR
```

# 17. Idempotency

Future 对创建类接口支持：
```text
Idempotency-Key
```

V0.1 不强制，但 Research Service 设计不能阻碍后续加入。

# 18. Pagination

V0.1：
```text
limit
offset
```

默认 limit 20，最大值由后端配置。

未来数据量增长后可迁移 cursor pagination。

# 19. API Security

- Browser 永远不直接获得 Provider Secret；
- 服务端验证所有输入；
- 外部 URL/内容视为 untrusted；
- 高风险 Tool 未来必须 approval；
- 错误响应不泄露内部 stack trace；
- CORS 在环境配置中显式允许。

# 20. Versioning

Breaking API change 通过新路径：
```text
/api/v2
```

增加 optional field 通常视为 non-breaking。

# 21. OpenAPI

FastAPI 自动生成 OpenAPI，但代码实现必须遵循本规范。

OpenAPI 是机器可读接口事实来源；本文件解释语义、生命周期与设计约束。

# 22. MVP Required Endpoints

```text
GET  /health
GET  /ready

GET  /api/v1/models

POST /api/v1/research
GET  /api/v1/research
GET  /api/v1/research/{id}

GET  /api/v1/runs
GET  /api/v1/runs/{id}
POST /api/v1/runs/{id}/cancel
GET  /api/v1/runs/{id}/events
GET  /api/v1/runs/{id}/evaluations

GET  /api/v1/knowledge
POST /api/v1/knowledge

GET  /api/v1/technologies
POST /api/v1/technologies

GET  /api/v1/capabilities
PUT  /api/v1/capabilities/{id}

GET  /api/v1/evidence
POST /api/v1/evidence
```

# 23. Acceptance Criteria

1. API Schema 与 ORM 解耦；
2. Research 创建接口立即返回 run_id；
3. SSE 使用 EVENT_SPEC 统一事件；
4. Secret 永不出现在 Provider Response；
5. 所有错误返回稳定 error.code；
6. Run cancellation 有明确状态约束；
7. Capability level 有 0–5 校验；
8. OpenAPI 可生成；
9. API integration tests 覆盖核心路径；
10. Frontend 不需要了解 Provider SDK。

# 24. Final Principle

> **The API exposes stable product and runtime contracts, not database internals or vendor-specific AI APIs.**
