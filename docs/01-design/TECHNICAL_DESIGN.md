# Personal AI Engineering Workspace — Technical Design

**Document Type:** Technical Design Document  
**Version:** 0.1  
**Status:** Draft  
**Project Stage:** MVP Architecture Design  
**Owner:** Project Owner  
**Last Updated:** 2026-09-28  

**Related Documents:**
- `../00-project/PRD.md`
- `../02-ai/AI_SYSTEM_SPEC.md`
- `../03-contracts/API_SPEC.md`
- `../03-contracts/DATA_MODEL.md`
- `../03-contracts/EVENT_SPEC.md`
- `../04-quality/SECURITY.md`
- `../04-quality/OBSERVABILITY.md`
- `../adr/ADR-001-nextjs-fastapi.md`
- `../adr/ADR-002-model-gateway.md`
- `../adr/ADR-003-langgraph-runtime.md`
- `../adr/ADR-004-sse-streaming.md`

---

# 1. Purpose

本文档描述 Personal AI Engineering Workspace V0.1 的总体技术设计。

本文档重点回答：

- 系统由哪些组件组成；
- 前端与后端如何划分；
- AI Agent 如何运行；
- 多个 LLM Provider 如何统一接入；
- Tool / MCP 如何接入；
- Agent 执行过程如何通过 SSE 实时返回；
- 数据如何存储；
- Agent Run 如何追踪；
- 错误如何处理；
- 安全边界在哪里；
- 系统如何部署；
- 后续如何扩展。

本文档不负责描述完整产品需求，产品需求见 `PRD.md`。

---

# 2. Design Goals

V0.1 技术设计需要满足以下目标。

## 2.1 Modularity

核心模块彼此解耦：

```text
Frontend

Backend API

Workspace Services

Agent Runtime

Model Gateway

Tool Gateway

Persistence

Observability
```

避免：

```text
React
→ directly calls OpenAI
```

或者：

```text
Research Agent
→ hardcoded Claude SDK
```

---

## 2.2 Replaceability

以下组件必须可以被替换：

```text
LLM Provider

Model

Agent Framework

Search Provider

Embedding Model

Vector Store Strategy

Tool Implementation
```

例如：

```text
Research Agent
```

不应该因为：

```text
Claude → DeepSeek
```

而修改业务逻辑。

---

# 3. MVP Technical Scope

V0.1 实现以下核心能力：

```text
Next.js Frontend

FastAPI Backend

PostgreSQL

Redis

Multi-model Gateway

Research Agent

Web Search Tool

GitHub Research Tool

SSE Streaming

Agent Run Trace

Knowledge Storage

Capability Tracking
```

V0.1 暂不实现：

```text
Coding Agent

Full Browser Automation

Multi-Agent Runtime

Complex Memory

Agent Replay

MCP Marketplace

Automatic Model Router

Enterprise RBAC

Billing

Multi-tenancy
```

---

# 4. System Context

系统初期是：

```text
Single User
+
Self-hosted / Local Development
```

但架构应该允许未来扩展为：

```text
Multiple Users

Remote Deployment

Cloud-hosted Service
```

系统主要外部依赖：

```text
LLM APIs

Search API

GitHub API

Future MCP Servers
```

---

# 5. High-Level Architecture

总体架构：

```text
┌───────────────────────────────────────────────┐
│                   Browser                     │
└─────────────────────┬─────────────────────────┘
                      │
                      │ HTTPS
                      ▼
┌───────────────────────────────────────────────┐
│                  Next.js                      │
│                                               │
│ Workspace UI                                  │
│ Agent Lab UI                                  │
│ SSE Client                                    │
└─────────────────────┬─────────────────────────┘
                      │
                REST API + SSE
                      │
                      ▼
┌───────────────────────────────────────────────┐
│                  FastAPI                      │
│                                               │
│ API Layer                                     │
│ Service Layer                                 │
│ Agent Runtime                                 │
│ Model Gateway                                 │
│ Tool Gateway                                  │
│ Event System                                  │
└───────────────┬───────────────┬───────────────┘
                │               │
                ▼               ▼
         PostgreSQL           Redis
                │
                ▼
            pgvector

External Services:

FastAPI
   │
   ├── OpenAI
   ├── Anthropic
   ├── DeepSeek
   ├── Kimi
   ├── Search Provider
   ├── GitHub
   └── Future MCP Servers
```

---

# 6. Architectural Layers

Backend 采用分层架构：

```text
API Layer
    ↓
Service Layer
    ↓
Domain / Agent Layer
    ↓
Infrastructure Layer
    ↓
Persistence / External APIs
```

职责严格分离。

---

# 7. Frontend Architecture

## 7.1 Technology

Frontend：

```text
Next.js

React

TypeScript

Tailwind CSS
```

---

## 7.2 Responsibilities

Frontend 负责：

```text
UI Rendering

User Interaction

Navigation

API Communication

SSE Consumption

Client-side State

Agent Progress Visualization
```

Frontend 不负责：

```text
LLM API Authentication

Agent Workflow

Tool Execution

Model Routing

Secret Management
```

---

# 8. Frontend Application Areas

V0.1 页面：

```text
/

Home

/research

/knowledge

/capabilities

/lab/runs

/settings
```

未来：

```text
/learning

/projects

/career

/journal

/lab/agents

/lab/models

/lab/experiments
```

---

# 9. Frontend Component Structure

建议：

```text
frontend/

app/
├── page.tsx
├── research/
├── knowledge/
├── capabilities/
├── lab/
│   └── runs/
└── settings/

components/
├── layout/
├── common/
├── research/
├── knowledge/
├── capability/
└── runs/

lib/
├── api/
├── sse/
├── types/
└── utils/
```

---

# 10. Core Frontend Components

V0.1：

```text
CaptureInput

ModelSelector

ResearchComposer

ResearchProgress

ResearchReport

SourceList

KnowledgeCard

CapabilityCard

RunList

RunTimeline

RunMetrics

ProviderStatus
```

---

# 11. Frontend State

V0.1 不引入过重状态管理。

优先：

```text
React state

React Context

Server Components

URL state
```

如果后期跨页面状态复杂，再评估：

```text
Zustand

Redux Toolkit
```

避免提前增加依赖。

---

# 12. Backend Technology

Backend：

```text
Python

FastAPI

Pydantic

SQLAlchemy

Alembic

PostgreSQL

Redis
```

Agent Runtime：

```text
LangGraph
```

---

# 13. Backend Directory Structure

建议：

```text
backend/

app/
├── main.py
│
├── api/
│   ├── routes/
│   └── dependencies/
│
├── core/
│   ├── config.py
│   ├── logging.py
│   ├── errors.py
│   └── security.py
│
├── schemas/
│
├── models/
│
├── services/
│
├── repositories/
│
├── agents/
│   └── research/
│
├── ai/
│   ├── providers/
│   ├── gateway/
│   ├── registry/
│   └── events/
│
├── tools/
│
└── db/
```

---

# 14. API Layer

API Layer 只负责：

```text
HTTP Request

Validation

Authentication

Serialization

HTTP Response
```

禁止直接写：

```text
database query

agent orchestration

model SDK call
```

例如：

```text
POST /api/research
```

应该调用：

```text
ResearchService
```

而不是直接运行 LangGraph。

---

# 15. Service Layer

核心 Service：

```text
ResearchService

RunService

KnowledgeService

CapabilityService

ModelService
```

职责：

```text
Business Workflow

Transaction Coordination

Domain Validation

Repository Orchestration
```

---

# 16. Repository Layer

Repository 负责：

```text
Database Access
```

例如：

```text
RunRepository

ResearchRepository

KnowledgeRepository

CapabilityRepository
```

Service 不应该直接：

```text
db.execute(...)
```

这样后续数据库变化时业务逻辑保持稳定。

---

# 17. AI Layer

AI Layer 负责所有模型访问。

目录：

```text
ai/

providers/
gateway/
registry/
events/
```

AI Layer 不知道：

```text
Research business logic
```

它只知道：

```text
send request

receive response

stream events

normalize usage

normalize errors
```

---

# 18. Model Gateway

Model Gateway 是系统核心基础设施。

结构：

```text
Agent
  │
  ▼
Model Gateway
  │
  ├── OpenAI Provider
  ├── Anthropic Provider
  └── OpenAI-Compatible Provider
           │
           ├── DeepSeek
           ├── Kimi
           ├── Qwen
           └── future providers
```

---

# 19. Provider Interface

所有 Provider 统一实现：

```text
generate()

stream()

supports()

health_check()
```

统一输入对象：

```text
ModelRequest
```

包含：

```text
model

messages

tools

temperature

max_tokens

structured_schema

metadata
```

统一输出：

```text
ModelResponse
```

包含：

```text
content

tool_calls

usage

finish_reason

latency

provider_metadata
```

---

# 20. Provider Capability Differences

不能假设：

```text
OpenAI
=
Claude
=
DeepSeek
=
Kimi
```

因此维护 Model Capability Registry。

例如：

```text
supports_streaming

supports_tools

supports_structured_output

supports_vision

supports_reasoning
```

上层 Agent 根据 capability 使用模型。

---

# 21. Model Registry

数据库中保存：

```text
provider

model_key

display_name

capabilities

enabled
```

Provider 配置与具体 Model 配置分离。

例如：

```text
Provider:
Anthropic

Models:
Claude A
Claude B
```

---

# 22. Agent Runtime

V0.1 使用 LangGraph。

原因：

Research Agent 本身是明确的状态工作流：

```text
Understand
↓
Plan
↓
Search
↓
Read
↓
Verify
↓
Synthesize
```

LangGraph 适合：

```text
State

Node

Conditional Edge

Checkpoint

Interrupt
```

但业务代码不得深度绑定 LangGraph API。

---

# 23. Agent Abstraction

Agent 业务定义：

```text
AgentSpec
```

概念上包含：

```text
id

name

version

workflow

model_policy

tools

prompt

permissions

evaluation_policy
```

LangGraph 是：

```text
runtime implementation
```

而不是 Agent 本身。

---

# 24. Research Agent

V0.1 Workflow：

```text
START
  ↓
Understand Task
  ↓
Plan Search
  ↓
Search
  ↓
Select Sources
  ↓
Read Sources
  ↓
Extract Findings
  ↓
Verify Claims
  ↓
Synthesize
  ↓
Structured Output
  ↓
END
```

---

# 25. Research State

Research Agent State：

```text
query

research_goal

search_queries

sources

selected_sources

findings

claims

verification_results

report

structured_result

errors
```

每个 Node 读取 State 并产生更新。

---

# 26. Agent Node Design

节点应该：

```text
small

testable

observable
```

例如：

```text
plan_search()
```

只负责生成搜索计划。

不要一个节点完成：

```text
search + read + summarize + save database
```

这样后续无法调试和评估。

---

# 27. Tool Gateway

Agent 不直接依赖：

```text
GitHub SDK

Search SDK

MCP SDK
```

统一：

```text
Agent
  ↓
Tool Gateway
  ↓
Tool
```

---

# 28. Tool Interface

Tool 至少定义：

```text
name

description

input_schema

risk_level

timeout

retry_policy

execute()
```

V0.1：

```text
web_search

fetch_url

github_repository
```

Future：

```text
browser

filesystem

terminal

python

database

MCP
```

---

# 29. Tool Risk Model

## LOW

```text
search
read
fetch
```

允许自动执行。

## MEDIUM

```text
write local file
modify note
```

未来可配置。

## HIGH

```text
delete

git push

send external message

shell execution
```

必须 Human Approval。

---

# 30. MCP Integration

MCP 放在 Tool Gateway 下。

```text
Agent
  ↓
Tool Gateway
  ↓
MCP Adapter
  ↓
MCP Server
```

这样 Agent 不需要区分：

```text
native tool

MCP tool
```

上层统一使用 Tool Contract。

---

# 31. SSE Architecture

V0.1 使用 SSE。

典型流程：

```text
Frontend

POST /api/research

      ↓

Backend creates Run

      ↓

returns run_id

      ↓

Frontend connects:

GET /api/runs/{run_id}/events

      ↓

SSE stream
```

---

# 32. Event Flow

例如：

```text
run.started

agent.started

agent.step

tool.started

tool.completed

model.started

text.delta

model.completed

run.completed
```

Frontend 根据事件实时更新 UI。

---

# 33. Why SSE Before WebSocket

当前主要需求：

```text
Server
→
Client
```

例如：

```text
agent progress

token streaming

tool status
```

SSE：

```text
simple

HTTP-native

automatic reconnect

suitable for streaming
```

因此 V0.1 不引入 WebSocket。

Coding Agent 等需要实时：

```text
pause

approve

cancel

interactive terminal
```

时再引入 WebSocket。

---

# 34. Event Bus

V0.1 可以采用：

```text
in-process event publisher
+
Redis Pub/Sub
```

结构：

```text
Agent Runtime
    ↓
Event Publisher
    ↓
Redis
    ↓
SSE Endpoint
    ↓
Frontend
```

本地开发初期可以简化为 in-process queue。

但 Event API 应保持统一。

---

# 35. Run Lifecycle

Run 状态：

```text
PENDING

RUNNING

COMPLETED

FAILED

CANCELLED
```

状态转换：

```text
PENDING
   ↓
RUNNING
   ├── COMPLETED
   ├── FAILED
   └── CANCELLED
```

禁止出现不明确状态。

---

# 36. Persistence

Primary Database：

```text
PostgreSQL
```

原因：

系统核心数据高度结构化并具有关系：

```text
Research

Knowledge

Technology

Capability

Evidence

Agent

Run

Event
```

---

# 37. Vector Retrieval

使用：

```text
pgvector
```

而不是 MVP 初期额外引入独立 Vector DB。

原因：

```text
simpler deployment

transaction consistency

lower operational complexity
```

后期规模增长后再重新评估。

---

# 38. Redis Responsibilities

Redis 初期负责：

```text
event streaming

runtime state

short-lived cache
```

后期可增加：

```text
task queue

rate limit

distributed locks
```

Redis 不作为长期业务数据存储。

---

# 39. Core Data Entities

V0.1：

```text
Provider

Model

Agent

AgentVersion

Run

RunEvent

ToolCall

ResearchItem

ResearchSource

KnowledgeItem

Technology

Capability

Evidence
```

详细 Schema 由：

```text
DATA_MODEL.md
```

维护。

---

# 40. Research Data Flow

完整流程：

```text
User Input

↓

POST /research

↓

ResearchService

↓

Create Run

↓

Research Agent

↓

Model Gateway

↓

Search Tool

↓

Sources

↓

Verification

↓

Report

↓

Persist Research

↓

Persist Run Metrics

↓

SSE Complete Event

↓

Frontend
```

---

# 41. Knowledge Data Flow

```text
Research Report

↓

User clicks Save

↓

KnowledgeService

↓

Extract Technology / Concept

↓

Create Knowledge Items

↓

Create Relations

↓

Update Search Index
```

V0.1 不需要完全自动保存。

默认：

```text
AI suggests
User confirms
```

避免 Knowledge Pollution。

---

# 42. Capability Data Flow

```text
Technology

↓

Capability

↓

Evidence

↓

Level Update
```

Capability 不由 AI 无条件修改。

AI 可以：

```text
suggest level
```

但最终：

```text
user confirms
```

V0.1 保持 Human-in-the-loop。

---

# 43. Error Architecture

统一定义错误分类：

```text
VALIDATION_ERROR

MODEL_ERROR

PROVIDER_ERROR

TOOL_ERROR

WORKFLOW_ERROR

DATABASE_ERROR

AUTH_ERROR

RATE_LIMIT_ERROR

TIMEOUT_ERROR

UNKNOWN_ERROR
```

API 不允许所有异常统一变成：

```text
500
```

---

# 44. Error Normalization

不同 Provider：

```text
OpenAI RateLimit

Anthropic RateLimit

DeepSeek 429
```

统一为：

```text
ProviderRateLimitError
```

上层 Agent 不需要知道具体 SDK Exception。

---

# 45. Retry Strategy

Retry 只用于：

```text
temporary failures
```

例如：

```text
429

timeout

temporary 5xx
```

采用：

```text
exponential backoff
+
maximum retry count
```

逻辑错误禁止 blind retry。

---

# 46. Fallback Strategy

Future：

```text
Primary Model
   ↓ failure
Fallback Model
```

但每次 fallback 必须记录：

```text
original model

failure reason

fallback model
```

确保 Run 可解释。

---

# 47. Security Boundaries

系统主要安全边界：

```text
Browser
│
▼
Backend
│
├── Secrets
├── Tools
└── External Services
```

API Key 永远只能存在：

```text
Backend
```

不能：

```text
Browser

Git Repository

Run Event Payload
```

---

# 48. Secret Management

Local V0.1：

```text
.env
```

仓库只保存：

```text
.env.example
```

禁止提交：

```text
.env
```

后期：

```text
Encrypted Secret Store
```

---

# 49. Prompt Injection Boundary

所有外部内容默认：

```text
UNTRUSTED DATA
```

例如：

```text
website

README

PDF

GitHub issue
```

不得将其中的：

```text
instructions
```

自动视为 Agent 指令。

必须区分：

```text
System Instruction

User Instruction

External Content
```

---

# 50. Tool Security

任何 Tool Call 都应该知道：

```text
who requested

which agent

which run

what input

risk level

result
```

为以后：

```text
audit
```

提供基础。

---

# 51. Observability

传统服务指标：

```text
request count

error rate

latency

database errors
```

AI 指标：

```text
provider

model

tokens

cost

tool calls

agent steps

run success

tool failures
```

---

# 52. Trace Correlation

所有日志和事件包含：

```text
run_id
```

未来还可加入：

```text
trace_id

span_id
```

目标兼容：

```text
OpenTelemetry
```

---

# 53. Logging

结构化日志示例：

```text
timestamp

level

service

run_id

event

model

tool

message
```

禁止记录：

```text
API keys

passwords

secret tokens
```

---

# 54. AI Versioning

Run 必须能够回答：

> 当时究竟是什么版本产生了这个结果？

至少记录：

```text
agent_version

model

provider

prompt_version

tool_version
```

后期加入：

```text
evaluation_version
```

---

# 55. Reproducibility

LLM 是非确定性系统。

因此：

```text
reproducible
```

不是要求输出文本完全相同。

而是保存：

```text
input

context

model

model parameters

agent version

prompt version

tools

tool outputs

events
```

从而支持重新执行和比较。

---

# 56. Evaluation Architecture

V0.1：

```text
Deterministic Validation
```

包括：

```text
structured output valid

required fields exist

sources exist

tool execution valid
```

V0.2+：

```text
citation evaluation

source quality

LLM judge

human evaluation

benchmark
```

Evaluation 独立于 Agent Workflow。

---

# 57. Testing Architecture

测试分层：

```text
Unit

Integration

API

Agent Workflow

Evaluation

Regression
```

普通逻辑：

```text
必须 deterministic test
```

不能用：

```text
LLM judge
```

代替单元测试。

---

# 58. Development Environment

Local：

```text
Windows

VS Code

Git

Docker Desktop

Python

Node.js
```

运行方式未来统一：

```text
docker compose up
```

但开发阶段允许：

```text
frontend dev server

backend dev server
```

分别启动。

---

# 59. Deployment Topology

V0.1：

```text
Docker Compose

├── frontend
├── backend
├── postgres
└── redis
```

External：

```text
LLM APIs
Search API
GitHub API
```

---

# 60. Configuration

配置通过：

```text
environment variables
```

例如：

```text
DATABASE_URL

REDIS_URL

OPENAI_API_KEY

ANTHROPIC_API_KEY

DEEPSEEK_API_KEY

KIMI_API_KEY
```

应用层通过统一：

```text
Settings
```

读取。

禁止在代码中散落：

```text
os.getenv(...)
```

---

# 61. Database Migration

使用：

```text
Alembic
```

所有 Schema 修改必须通过 migration。

禁止：

```text
手动修改生产数据库结构
```

---

# 62. API Versioning

初期：

```text
/api
```

当产生 breaking API change 时升级：

```text
/api/v1
```

V0.1 可以直接采用：

```text
/api/v1
```

避免后续迁移成本。

---

# 63. API Style

采用：

```text
REST
```

例如：

```text
POST /api/v1/research

GET /api/v1/research/{id}

GET /api/v1/runs/{id}

GET /api/v1/runs/{id}/events
```

具体 Contract 在：

```text
API_SPEC.md
```

---

# 64. Idempotency

对于可能重复提交的操作：

```text
Research Start
```

未来应考虑：

```text
idempotency key
```

V0.1 可以暂不实现，但接口设计不要阻碍后续加入。

---

# 65. Performance Metrics

V0.1 关注：

```text
Time To First Event

Total Run Latency

Model Latency

Tool Latency
```

暂不设高并发指标。

后续：

```text
P50

P95

P99
```

---

# 66. Cost Metrics

每次 Model Call 记录：

```text
input tokens

output tokens

estimated cost
```

Run 聚合：

```text
total tokens

total estimated cost
```

Future：

```text
daily budget

per-agent budget

model budget
```

---

# 67. Scalability Strategy

V0.1：

```text
Single backend instance
```

未来扩展：

```text
stateless FastAPI instances

Redis shared runtime state

background workers

task queue
```

Agent Runtime 与 HTTP Request 生命周期最终需要解耦。

V0.1 可先简化。

---

# 68. Background Tasks

Research Agent 运行时间可能：

```text
10s

30s

minutes
```

长期架构不应把 Agent Run 永久绑定在：

```text
single HTTP request
```

最终结构：

```text
API
↓
create task
↓
worker
↓
events
↓
SSE
```

V0.1 初期可以直接后台 Task。

V0.2 再引入正式 Queue。

---

# 69. Key Technical Trade-offs

## LangGraph vs Custom Runtime

当前：

```text
LangGraph
```

优势：

```text
stateful workflow

checkpoint support

ecosystem
```

缺点：

```text
framework dependency
```

通过 Agent Abstraction 降低锁定。

---

## PostgreSQL + pgvector vs Dedicated Vector DB

当前：

```text
PostgreSQL + pgvector
```

优势：

```text
simple

fewer services

transaction consistency
```

缺点：

```text
large-scale vector workload less specialized
```

MVP 更适合 simplicity。

---

## SSE vs WebSocket

当前：

```text
SSE
```

因为主要：

```text
server → client
```

未来 Coding Agent 需要双向实时交互再升级。

---

# 70. Architecture Decision Records

以下重要决策必须单独记录：

```text
ADR-001
Next.js + FastAPI

ADR-002
Model Gateway

ADR-003
LangGraph Runtime

ADR-004
SSE Streaming
```

后续预计：

```text
ADR-005
PostgreSQL + pgvector

ADR-006
Redis event layer

ADR-007
OpenTelemetry

ADR-008
MCP tool architecture
```

---

# 71. MVP Technical Acceptance Criteria

V0.1 完成时系统必须支持：

```text
1. Frontend 与 Backend 正常通信

2. PostgreSQL 正常持久化

3. 至少两个不同 Provider 可通过 Model Gateway 调用

4. 用户能够选择 Model

5. Research Agent 能运行完整 workflow

6. Tool Call 可被记录

7. Agent progress 通过 SSE 实时展示

8. Run 保存 Model / Token / Latency / Error

9. Research Result 可以保存

10. Knowledge 可以查询

11. Capability 可以维护

12. Agent Lab 可以查看 Run Timeline
```

---

# 72. Failure Acceptance Criteria

以下场景必须能够正确处理：

```text
Provider timeout

Provider 429

Tool error

Invalid structured output

Database error

SSE disconnect

Agent workflow error
```

用户不能只看到：

```text
Something went wrong
```

应该至少获得：

```text
error category

human-readable message

run status
```

---

# 73. Security Acceptance Criteria

V0.1 至少保证：

```text
API key 不发送到浏览器

API key 不提交 Git

外部内容与 System Prompt 分离

高风险 Tool 暂不启用

Run Log 不存 Secret
```

---

# 74. Open Technical Questions

当前暂未锁定：

```text
Search Provider

Embedding Model

GitHub REST API vs MCP

Redis 是否 V0.1 即引入

Background Task Framework

Prompt Storage

Agent Version Persistence

Tool Version Strategy

OpenTelemetry integration timing

Evaluation Dataset
```

这些问题后续通过：

```text
ADR
```

逐项决策。

---

# 75. Implementation Order

推荐技术实现顺序：

```text
Phase 1
Frontend + Backend skeleton

Phase 2
PostgreSQL

Phase 3
Model Gateway

Phase 4
Multi-model integration

Phase 5
SSE

Phase 6
Research Agent

Phase 7
Run Trace

Phase 8
Knowledge

Phase 9
Capability

Phase 10
Evaluation
```

避免：

```text
同时开发所有 Agent
```

---

# 76. Architecture Principle

整个项目遵循：

> **Stable contracts, replaceable implementations.**

即：

```text
Agent Contract
stable

Model Provider
replaceable

Tool Provider
replaceable

Storage implementation
replaceable
```

---

# 77. AI Engineering Principle

所有 AI 能力必须满足：

```text
Observable

Evaluable

Versionable

Replaceable
```

即：

> Every AI component should be observable, evaluable, versionable, and replaceable.

---

# 78. Final Architecture Statement

Personal AI Engineering Workspace 不将 AI 作为单独功能添加到传统 Web App 中。

系统从架构层面围绕：

```text
Task

Agent

Model

Tool

Run

Knowledge

Capability

Evidence
```

构建。

系统最终形成两个持续循环。

个人成长：

```text
CAPTURE
↓
RESEARCH
↓
LEARN
↓
BUILD
↓
EVIDENCE
↓
REFLECT
↓
IMPROVE
```

AI 工程：

```text
TASK
↓
AGENT
↓
RUN
↓
TRACE
↓
EVALUATE
↓
EXPERIMENT
↓
IMPROVE
```

这两个循环共同构成系统的长期技术架构。