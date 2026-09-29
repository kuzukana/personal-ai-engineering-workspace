# Personal AI Engineering Workspace — Data Model Specification

**Document Type:** Data Model Specification  
**Version:** 0.1  
**Status:** Draft  
**Project Stage:** MVP Contract Design  
**Owner:** Project Owner  
**Last Updated:** 2026-09-29  

**Related Documents:**
- `../00-project/PRD.md`
- `../01-design/TECHNICAL_DESIGN.md`
- `../02-ai/AI_SYSTEM_SPEC.md`
- `../02-ai/MODEL_SPEC.md`
- `../02-ai/AGENT_SPEC.md`
- `../02-ai/EVALUATION.md`
- `API_SPEC.md`
- `EVENT_SPEC.md`

---

# 1. Purpose

本文档定义 Personal AI Engineering Workspace V0.1 的核心数据模型、实体关系、字段语义、约束和生命周期。

目标是把前面产品与 AI 设计中的抽象概念正式落成可实现、可迁移、可版本化的数据契约。

本规范重点回答：

- 系统有哪些核心实体；
- Provider 与 Model 如何建模；
- Agent 与 Agent Version 如何建模；
- Run、Run Event、Tool Call 如何关联；
- Research、Source、Knowledge 如何沉淀；
- Technology、Capability、Evidence 如何关联；
- Evaluation 如何独立存储；
- 哪些字段属于稳定契约；
- 哪些数据适合 JSONB；
- 哪些关系需要显式外键；
- 哪些对象必须版本化；
- 哪些历史数据不可被原地覆盖。

---

# 2. Data Modeling Principles

## 2.1 Relational First

MVP 主数据库采用 PostgreSQL。

优先使用关系模型保存：

```text
identity
ownership
version
status
timestamps
relationships
```

JSONB 只用于：

```text
provider-specific metadata
event payload
flexible evaluation evidence
tool payload
```

不使用 JSONB 替代本应明确建模的核心关系。

---

## 2.2 Immutable History

以下对象一旦被 Run 引用，不应被原地覆盖：

```text
Agent Version
Prompt Version
Evaluation Version
```

历史行为必须可追踪。

---

## 2.3 Explicit Provenance

Research、Knowledge、Evaluation 等重要数据必须尽可能保留来源。

核心原则：

> **No important AI-generated artifact without provenance.**

---

## 2.4 Soft Evolution

V0.1 避免过度抽象。

优先：

```text
clear tables
clear foreign keys
clear enums
```

而不是提前构建复杂通用 Graph Schema。

---

# 3. High-Level Entity Map

V0.1 核心实体：

```text
Provider
  └── Model

Agent
  └── AgentVersion
        └── Run
              ├── RunEvent
              ├── ToolCall
              └── EvaluationResult

ResearchItem
  ├── ResearchSource
  └── KnowledgeItem

Technology
  └── Capability
        └── CapabilityEvidence
              └── Evidence
```

未来扩展：

```text
Prompt
PromptVersion
Experiment
Benchmark
Memory
Tool
MCPServer
Project
Task
Job
Decision
Incident
```

---

# 4. Entity Naming Convention

数据库表名：

```text
snake_case
plural
```

例如：

```text
providers
models
agent_versions
run_events
research_sources
```

主键统一：

```text
id
```

推荐使用 UUID。

---

# 5. Common Fields

多数核心表建议包含：

```text
id
created_at
updated_at
```

需要软删除时 Future 增加：

```text
deleted_at
```

V0.1 不默认所有表启用 soft delete。

---

# 6. providers

表示模型服务提供方。

字段：

```text
id                  UUID PK
name                VARCHAR UNIQUE NOT NULL
provider_type       VARCHAR NOT NULL
base_url            TEXT NULL
status              VARCHAR NOT NULL
config_json         JSONB NULL
created_at          TIMESTAMPTZ NOT NULL
updated_at          TIMESTAMPTZ NOT NULL
```

示例：

```text
OpenAI
Anthropic
DeepSeek
Kimi
```

API Key 不存入 config_json。

Secret 使用环境变量或未来 Secret Store。

---

# 7. Provider Status

建议枚举：

```text
ACTIVE
DISABLED
UNAVAILABLE
DEPRECATED
```

---

# 8. models

表示具体模型。

字段：

```text
id                          UUID PK
provider_id                 UUID FK -> providers.id
model_key                   VARCHAR NOT NULL
display_name                VARCHAR NOT NULL
status                      VARCHAR NOT NULL
supports_streaming          BOOLEAN NOT NULL
supports_tools              BOOLEAN NOT NULL
supports_parallel_tools     BOOLEAN NOT NULL DEFAULT FALSE
supports_structured_output  BOOLEAN NOT NULL
supports_vision             BOOLEAN NOT NULL DEFAULT FALSE
supports_reasoning          BOOLEAN NOT NULL DEFAULT FALSE
supports_system_prompt      BOOLEAN NOT NULL DEFAULT TRUE
context_window              INTEGER NULL
max_output_tokens           INTEGER NULL
metadata_json               JSONB NULL
created_at                  TIMESTAMPTZ NOT NULL
updated_at                  TIMESTAMPTZ NOT NULL
```

Unique Constraint：

```text
(provider_id, model_key)
```

---

# 9. Model Status

建议：

```text
ACTIVE
DISABLED
DEPRECATED
UNAVAILABLE
```

---

# 10. agents

表示 Agent 的稳定身份。

字段：

```text
id            UUID PK
agent_key     VARCHAR UNIQUE NOT NULL
name          VARCHAR NOT NULL
description   TEXT NULL
purpose       TEXT NULL
status        VARCHAR NOT NULL
created_at    TIMESTAMPTZ NOT NULL
updated_at    TIMESTAMPTZ NOT NULL
```

例如：

```text
agent_key = research-agent
name = Research Agent
```

---

# 11. agent_versions

表示不可变的 Agent 行为版本。

字段：

```text
id                    UUID PK
agent_id              UUID FK -> agents.id
version               VARCHAR NOT NULL
runtime_type          VARCHAR NOT NULL
workflow_key          VARCHAR NOT NULL
system_prompt_version VARCHAR NULL
model_policy_json     JSONB NOT NULL
tool_policy_json      JSONB NOT NULL
memory_policy_json    JSONB NOT NULL
permission_policy_json JSONB NOT NULL
evaluation_policy_json JSONB NOT NULL
config_json           JSONB NULL
created_at            TIMESTAMPTZ NOT NULL
```

Unique：

```text
(agent_id, version)
```

---

# 12. Agent Version Immutability

Agent Version 一旦被 Run 引用：

```text
must not be edited in place
```

行为变化创建新版本。

例如：

```text
research-agent / 0.1
research-agent / 0.2
```

---

# 13. runs

Run 是一次完整 Agent 执行。

字段：

```text
id                    UUID PK
agent_version_id      UUID FK -> agent_versions.id
model_id              UUID FK -> models.id
status                VARCHAR NOT NULL
task_type             VARCHAR NULL
input_text            TEXT NOT NULL
output_text           TEXT NULL
structured_output_json JSONB NULL
started_at            TIMESTAMPTZ NULL
completed_at          TIMESTAMPTZ NULL
latency_ms            BIGINT NULL
input_tokens          BIGINT NULL
output_tokens         BIGINT NULL
reasoning_tokens      BIGINT NULL
estimated_cost        NUMERIC NULL
currency              VARCHAR NULL
error_code            VARCHAR NULL
error_message         TEXT NULL
warnings_json         JSONB NULL
metadata_json         JSONB NULL
created_at            TIMESTAMPTZ NOT NULL
```

---

# 14. Run Status

V0.1：

```text
PENDING
RUNNING
WAITING_FOR_APPROVAL
COMPLETED
FAILED
CANCELLED
```

Future：

```text
PAUSED
COMPLETED_WITH_WARNINGS
```

---

# 15. Run Success Semantics

Run status 只表达运行生命周期。

不要把：

```text
COMPLETED
```

等同于：

```text
task_success
```

任务质量由 EvaluationResult 单独表达。

---

# 16. run_events

保存 Run 的事件流。

字段：

```text
id            UUID PK
run_id        UUID FK -> runs.id
sequence      BIGINT NOT NULL
event_type    VARCHAR NOT NULL
payload_json  JSONB NULL
created_at    TIMESTAMPTZ NOT NULL
```

Unique：

```text
(run_id, sequence)
```

---

# 17. Run Event Properties

Event 必须满足：

```text
ordered
append-only
traceable
```

V0.1 不修改历史 Event。

如需补充信息，追加新 Event。

---

# 18. tool_calls

表示一次 Tool 执行。

字段：

```text
id                UUID PK
run_id            UUID FK -> runs.id
tool_call_id      VARCHAR NULL
tool_name          VARCHAR NOT NULL
tool_version       VARCHAR NULL
risk_level         VARCHAR NULL
status             VARCHAR NOT NULL
input_json         JSONB NULL
output_json        JSONB NULL
started_at         TIMESTAMPTZ NULL
completed_at       TIMESTAMPTZ NULL
latency_ms         BIGINT NULL
error_code         VARCHAR NULL
error_message      TEXT NULL
created_at         TIMESTAMPTZ NOT NULL
```

---

# 19. Tool Call Status

建议：

```text
PENDING
RUNNING
COMPLETED
FAILED
CANCELLED
DENIED
```

---

# 20. evaluation_results

Evaluation 独立于 Run 生命周期。

字段：

```text
id                  UUID PK
run_id              UUID FK -> runs.id
evaluation_type     VARCHAR NOT NULL
metric_name         VARCHAR NOT NULL
evaluator_key       VARCHAR NOT NULL
evaluator_version   VARCHAR NOT NULL
status              VARCHAR NOT NULL
score               NUMERIC NULL
value_json           JSONB NULL
evidence_json        JSONB NULL
judge_model_id       UUID FK -> models.id NULL
created_at           TIMESTAMPTZ NOT NULL
```

---

# 21. Evaluation Type

建议：

```text
DETERMINISTIC
TASK_METRIC
MODEL_JUDGE
HUMAN
EXTERNAL_BENCHMARK
```

V0.1 前四种中的前三种优先。

---

# 22. Evaluation Status

建议：

```text
PASS
FAIL
WARNING
NOT_APPLICABLE
ERROR
```

`ERROR` 表示 evaluator 本身失败。

---

# 23. research_items

表示一次被保存的研究成果。

字段：

```text
id                     UUID PK
run_id                 UUID FK -> runs.id NULL
title                  VARCHAR NOT NULL
query                  TEXT NOT NULL
summary                TEXT NULL
report_markdown        TEXT NULL
structured_result_json JSONB NULL
status                 VARCHAR NOT NULL
created_at             TIMESTAMPTZ NOT NULL
updated_at             TIMESTAMPTZ NOT NULL
```

---

# 24. Research Status

建议：

```text
DRAFT
COMPLETED
ARCHIVED
```

---

# 25. research_sources

保存 Research 使用的来源。

字段：

```text
id                   UUID PK
research_item_id     UUID FK -> research_items.id
url                  TEXT NOT NULL
title                TEXT NULL
domain               VARCHAR NULL
source_type          VARCHAR NULL
retrieved_at         TIMESTAMPTZ NULL
relevance_score      NUMERIC NULL
verification_status  VARCHAR NULL
content_excerpt      TEXT NULL
metadata_json        JSONB NULL
created_at           TIMESTAMPTZ NOT NULL
```

---

# 26. Source Type

Future 可以标准化：

```text
OFFICIAL_DOC
GITHUB_REPOSITORY
PAPER
NEWS
BLOG
FORUM
OTHER
```

V0.1 可以先使用字符串枚举。

---

# 27. Source Verification Status

建议：

```text
VERIFIED
PARTIALLY_VERIFIED
UNVERIFIED
CONTRADICTED
NOT_CHECKED
```

注意：

Source Verification 与 Claim Verification 不完全相同。

---

# 28. knowledge_items

表示长期沉淀的用户知识对象。

字段：

```text
id                  UUID PK
knowledge_type      VARCHAR NOT NULL
title               VARCHAR NOT NULL
summary             TEXT NULL
content_markdown    TEXT NULL
source_research_id  UUID FK -> research_items.id NULL
status              VARCHAR NOT NULL
metadata_json       JSONB NULL
created_at          TIMESTAMPTZ NOT NULL
updated_at          TIMESTAMPTZ NOT NULL
```

---

# 29. Knowledge Type

V0.1：

```text
TECHNOLOGY
CONCEPT
RESEARCH
DECISION
NOTE
```

Future：

```text
INCIDENT
PROJECT
JOB
PAPER
SKILL
```

---

# 30. Knowledge Status

建议：

```text
DRAFT
ACTIVE
ARCHIVED
```

---

# 31. Knowledge Write Policy

AI 生成内容默认：

```text
suggest
↓
user review
↓
save
```

因此 Knowledge Item 应区分：

```text
suggested
```

与：

```text
accepted
```

V0.1 可先通过 status / metadata 表达，Future 再显式建模。

---

# 32. technologies

表示技能或技术实体。

字段：

```text
id          UUID PK
name        VARCHAR UNIQUE NOT NULL
slug        VARCHAR UNIQUE NOT NULL
category    VARCHAR NULL
description TEXT NULL
created_at  TIMESTAMPTZ NOT NULL
updated_at  TIMESTAMPTZ NOT NULL
```

示例：

```text
FastAPI
LangGraph
Redis
React
PostgreSQL
```

---

# 33. capabilities

表示用户对于某项 Technology 的能力状态。

字段：

```text
id                UUID PK
technology_id     UUID FK -> technologies.id
level             SMALLINT NOT NULL
reason            TEXT NULL
next_target_level SMALLINT NULL
next_action       TEXT NULL
updated_at        TIMESTAMPTZ NOT NULL
created_at        TIMESTAMPTZ NOT NULL
```

Unique：

```text
technology_id
```

V0.1 单用户，因此每项 Technology 只有一条 Capability。

Future 多用户需要：

```text
(user_id, technology_id)
```

---

# 34. Capability Level Constraint

必须满足：

```text
0 <= level <= 5
```

next_target_level 同样限制在 0–5。

---

# 35. Capability Semantics

```text
0 — 未接触
1 — 理解基本概念
2 — 可以运行和修改示例
3 — 可以独立实现常见功能
4 — 可以独立 Debug / Optimize
5 — 可以设计复杂系统并清晰解释
```

---

# 36. evidences

表示能力证据。

字段：

```text
id            UUID PK
title         VARCHAR NOT NULL
evidence_type VARCHAR NOT NULL
description   TEXT NULL
url           TEXT NULL
metadata_json JSONB NULL
created_at    TIMESTAMPTZ NOT NULL
updated_at    TIMESTAMPTZ NOT NULL
```

---

# 37. Evidence Type

建议：

```text
GIT_COMMIT
REPOSITORY
PROJECT
CODE
EXPERIMENT
RESEARCH
MANUAL_VERIFICATION
```

Future：

```text
CERTIFICATE
TEST_RESULT
DEPLOYMENT
```

---

# 38. capability_evidences

Capability 与 Evidence 为多对多。

字段：

```text
capability_id UUID FK -> capabilities.id
evidence_id   UUID FK -> evidences.id
created_at    TIMESTAMPTZ NOT NULL
```

Primary Key：

```text
(capability_id, evidence_id)
```

---

# 39. Research ↔ Technology Relation

Research Item 可能涉及多个 Technology。

建议增加：

```text
research_technologies
```

字段：

```text
research_item_id UUID FK -> research_items.id
technology_id    UUID FK -> technologies.id
relation_type    VARCHAR NULL
created_at       TIMESTAMPTZ NOT NULL
```

Primary Key：

```text
(research_item_id, technology_id)
```

---

# 40. Knowledge ↔ Technology Relation

Knowledge Item 也可能关联多个 Technology。

建议：

```text
knowledge_technologies
```

字段：

```text
knowledge_item_id UUID FK -> knowledge_items.id
technology_id     UUID FK -> technologies.id
created_at        TIMESTAMPTZ NOT NULL
```

---

# 41. Knowledge Relations

Future 需要显式表达：

```text
related_to
depends_on
compares_with
supersedes
supports
contradicts
```

V0.1 不急于做通用 Knowledge Graph。

先保留 Future 表：

```text
knowledge_relations
```

但不作为 MVP 阻塞项。

---

# 42. Prompt Data Model

Prompt 在架构上需要版本化，但 V0.1 可以先代码文件维护。

Future：

```text
prompts
prompt_versions
```

当 Prompt Experiment 进入 V0.4 后再正式建表。

---

# 43. Tool Data Model

V0.1 Tool Registry 可以代码定义。

Future：

```text
tools

tool_versions

agent_tools
```

当 MCP / Tool 动态管理进入系统后再持久化。

---

# 44. Memory Data Model

复杂 Memory 不属于 V0.1。

Future 预计：

```text
memories

memory_embeddings

memory_links
```

在真实需求出现前不提前锁定 Schema。

---

# 45. Experiments Data Model

V0.4 Future：

```text
experiments

experiment_runs

benchmark_cases

benchmark_versions
```

本规范暂不定义详细字段。

---

# 46. Event Payload Strategy

`run_events.payload_json` 使用 JSONB，因为不同 event_type 的 payload 差异较大。

但：

```text
event_type
sequence
run_id
created_at
```

必须是明确列。

不要把所有 Event 字段都塞进 JSONB。

---

# 47. Metadata JSON Strategy

`metadata_json` 仅用于：

```text
vendor-specific fields

non-core optional metadata

future-compatible extension
```

禁止用于隐藏核心字段。

---

# 48. JSONB Versioning

如果 JSONB 结构成为稳定业务契约，应增加：

```text
schema_version
```

例如：

```json
{
  "schema_version": "1",
  "..."
}
```

---

# 49. Foreign Key Strategy

核心关系应使用数据库 FK。

例如：

```text
models.provider_id
runs.agent_version_id
runs.model_id
run_events.run_id
tool_calls.run_id
evaluation_results.run_id
```

避免只保存字符串 ID 而失去一致性约束。

---

# 50. Delete Strategy

历史 Run 数据需要稳定。

因此：

```text
AgentVersion
Model
Provider
```

如果被历史 Run 引用，不应硬删除。

优先：

```text
DISABLED
DEPRECATED
```

---

# 51. Cascade Policy

谨慎使用：

```text
ON DELETE CASCADE
```

推荐：

- Run 删除时可级联 RunEvent / ToolCall（如果未来允许删除 Run）；
- Provider / Model / AgentVersion 不应因为上层删除而破坏历史；
- Research / Knowledge 删除策略在实现阶段明确。

V0.1 默认以保留历史为优先。

---

# 52. Timestamp Strategy

统一使用：

```text
TIMESTAMPTZ
```

数据库存储 UTC。

Frontend 按用户本地时区展示。

---

# 53. Cost Precision

`estimated_cost` 使用：

```text
NUMERIC
```

不要使用 float。

Currency 保存：

```text
USD
JPY
CNY
...
```

V0.1 预计统一估算为 USD，但字段保持可扩展。

---

# 54. Token Fields

Token 使用量建议：

```text
BIGINT
```

Provider 不支持的 token 类型保存：

```text
NULL
```

不要用 0 伪装为“已知为零”。

---

# 55. IDs

推荐 UUID。

理由：

- 前后端生成和传递方便；
- Future 分布式执行兼容；
- 避免暴露简单自增规模信息。

V0.1 可采用 PostgreSQL UUID 类型。

---

# 56. Index Strategy

V0.1 建议索引：

```text
models(provider_id, model_key)

agent_versions(agent_id, version)

runs(agent_version_id)

runs(model_id)

runs(status)

runs(created_at)

run_events(run_id, sequence)

tool_calls(run_id)

evaluation_results(run_id)

research_sources(research_item_id)

capabilities(technology_id)
```

---

# 57. Search Index

Knowledge 搜索 Future 使用：

```text
PostgreSQL full-text search
+
pgvector
```

V0.1 初期可先实现普通文本搜索。

---

# 58. pgvector Scope

Future embedding 对象：

```text
knowledge_items

research_items

incident-like items
```

不建议 V0.1 一开始为所有表生成 embedding。

---

# 59. Data Ownership

V0.1 为单用户系统。

因此多数业务表暂不需要：

```text
user_id
```

但设计上应明确：

> Future multi-user migration will require ownership columns.

避免把“单用户”错误理解为数据永远没有 owner。

---

# 60. Future Multi-user Migration

未来可能引入：

```text
users

workspaces
```

业务表添加：

```text
workspace_id
```

而不是简单在所有表塞 user_id。

这将在真正进入多用户产品阶段时单独 ADR。

---

# 61. Sensitive Data

以下内容不得存入普通 JSON：

```text
API keys
passwords
OAuth refresh tokens
private secrets
```

使用：

```text
environment variable
secret reference
future encrypted secret store
```

---

# 62. External Raw Content

V0.1 不默认长期保存所有网页全文。

优先保存：

```text
URL

title

retrieved_at

excerpt

metadata
```

如果未来需要完整原文缓存，应单独设计：

- retention；
- copyright；
- storage；
- refresh policy。

---

# 63. Data Retention

V0.1 单用户本地项目可长期保留：

```text
runs

events

research

knowledge

evaluation
```

但未来 SaaS 化必须定义 Retention Policy。

---

# 64. Data Migration

数据库 Schema 通过：

```text
Alembic
```

管理。

禁止手工修改正式数据库结构而没有 migration。

---

# 65. Migration Naming

建议：

```text
0001_create_provider_and_model_tables

0002_create_agent_and_run_tables

0003_create_research_tables

0004_create_capability_tables
```

具体序号由 Alembic revision 实际生成机制决定。

---

# 66. Initial Migration Order

推荐：

```text
1. providers
2. models
3. agents
4. agent_versions
5. runs
6. run_events
7. tool_calls
8. evaluation_results
9. research_items
10. research_sources
11. knowledge_items
12. technologies
13. capabilities
14. evidences
15. capability_evidences
16. research_technologies
17. knowledge_technologies
```

---

# 67. Entity Relationship Overview

```text
providers
   │ 1
   │
   │ N
models
   │
   │ 1
   │
   │ N
runs ───────────────┐
   │                │
   │                │
   ├── run_events   ├── evaluation_results
   └── tool_calls   │
                    │
agents              │
   │                │
   └── agent_versions
          │
          └────────────→ runs


research_items
   ├── research_sources
   ├── knowledge_items
   └── research_technologies ── technologies


technologies
   └── capabilities
           └── capability_evidences ── evidences
```

---

# 68. Research Run Relationship

一个 Run 可以产生：

```text
0 or 1 ResearchItem
```

V0.1 Research Agent 默认一个成功 Research Run 对应一个 ResearchItem。

但数据库不强制所有 Run 都必须有 ResearchItem，因为未来 Coding Agent 等不会产生 ResearchItem。

---

# 69. Evaluation Relationship

一个 Run：

```text
1
↓
N Evaluation Results
```

例如：

```text
report_schema_valid

source_present

tool_success_rate

future faithfulness score
```

分别保存。

---

# 70. Capability Evidence Relationship

一个 Evidence 可能支持多个 Capability。

例如：

```text
Implemented SSE Research Streaming
```

可支持：

```text
FastAPI

SSE

React

Async Python
```

因此必须使用多对多关系。

---

# 71. Auditability

V0.1 核心历史对象至少需要：

```text
created_at
```

Future 对用户手动修改 Knowledge / Capability 等对象可增加：

```text
updated_by
change_reason
audit_log
```

---

# 72. Concurrency

V0.1 单用户并发低。

但更新：

```text
Capability
Knowledge
```

Future 可以增加：

```text
version
```

用于 optimistic concurrency control。

MVP 暂不要求。

---

# 73. API Contract Boundary

数据库 Schema 不是前端 API Schema。

禁止：

```text
return ORM object directly
```

必须经过：

```text
Pydantic API Schema
```

这样数据库字段可以独立演化。

---

# 74. Domain Model Boundary

推荐区分：

```text
Database Model

Domain Model

API Schema
```

V0.1 不必为所有对象创建复杂 Domain Layer，但核心 AI 对象：

```text
Run
AgentSpec
ModelRequest
ModelResponse
EvaluationResult
```

应保持清晰的领域定义。

---

# 75. MVP Required Tables

第一版代码阶段最小必须落地：

```text
providers
models
agents
agent_versions
runs
run_events
tool_calls
evaluation_results
research_items
research_sources
knowledge_items
technologies
capabilities
evidences
capability_evidences
```

关系表可根据 Phase 分批实现。

---

# 76. MVP Data Acceptance Criteria

Data Layer V0.1 完成标准：

1. PostgreSQL Schema 可通过 Alembic 从空库创建；
2. Provider / Model 可以持久化；
3. Agent / AgentVersion 可以持久化并保持历史版本；
4. Run 可以关联 AgentVersion 和 Model；
5. RunEvent 可以按 sequence 正确排序；
6. ToolCall 可以关联 Run；
7. EvaluationResult 可以独立于 Run 生命周期保存；
8. ResearchItem 和 ResearchSource 可以保存来源；
9. KnowledgeItem 可以保存 Research 结果；
10. Technology / Capability / Evidence 可以建立长期能力关系；
11. API Secret 不进入普通业务表；
12. Schema 可以在自动测试中创建和销毁。

---

# 77. Future Data Questions

仍待真实使用验证：

```text
Knowledge graph relation design

Prompt persistence timing

Tool registry persistence

Memory schema

Experiment schema

Benchmark schema

Project / Task schema

Career / Job schema

Incident schema

Multi-user ownership
```

这些问题不在 V0.1 提前锁死。

---

# 78. Data Design Anti-patterns

禁止：

## Everything JSONB

核心关系全部放 JSONB。

## Mutable History

修改旧 AgentVersion 让历史 Run 失去可解释性。

## AI Output Without Provenance

长期保存 Research 结论却没有 Source。

## Secrets in Business Tables

将 API Key 放进普通 Provider 配置。

## Database-as-API

直接把 ORM 数据结构暴露给 Frontend。

## Premature Knowledge Graph

在还没有真实关系需求前构建复杂 Graph DB。

---

# 79. Final Data Model Principle

系统数据设计围绕：

```text
Identity
Version
Execution
Evidence
Knowledge
Capability
Evaluation
```

构建。

最重要的数据链路：

```text
Task
 ↓
Agent Version
 ↓
Run
 ↓
Events / Tools
 ↓
Research
 ↓
Sources
 ↓
Knowledge
 ↓
Capability
 ↓
Evidence
```

同时：

```text
Run
 ↓
Evaluation
 ↓
Experiment / Regression
```

核心原则：

> **Persist enough structure to understand what the AI did, what the user learned, and why the system believed the result was useful.**
