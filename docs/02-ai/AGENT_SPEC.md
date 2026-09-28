# Personal AI Engineering Workspace — Agent Specification

**Document Type:** Agent Specification  
**Version:** 0.1  
**Status:** Draft  
**Project Stage:** MVP Agent Architecture Design  
**Owner:** Project Owner  
**Last Updated:** 2026-09-28  

**Related Documents:**
- `AI_SYSTEM_SPEC.md`
- `MODEL_SPEC.md`
- `EVALUATION.md`
- `../01-design/TECHNICAL_DESIGN.md`
- `../03-contracts/EVENT_SPEC.md`
- `../04-quality/SECURITY.md`
- `../adr/ADR-003-langgraph-runtime.md`

---

# 1. Purpose

本文档定义系统中 Agent 的统一规范。

重点回答：

- Agent 在系统中是什么；
- Agent 与 Model 的关系；
- Agent 与 Runtime 的关系；
- Agent 如何描述目标和职责；
- Agent 如何绑定 Prompt、Tools、Memory、Permissions；
- Agent 如何声明模型要求；
- Agent 如何管理状态；
- Agent 如何执行 Workflow；
- Agent 如何产生 Run 和 Events；
- Agent 如何版本化；
- Agent 如何评测；
- Agent 如何进入 Human-in-the-loop；
- Agent 如何被比较、调试和迭代。

本规范的目标是确保未来增加 Research Agent、Learning Agent、Coding Agent、Career Agent 等时，不需要重新发明 Agent 架构。

---

# 2. Core Principle

核心原则：

> **Agent is a versioned task-solving specification, not a model wrapper.**

Agent 不是：

```text
Prompt
+
LLM
```

而是：

```text
Goal
+
Workflow
+
Model Policy
+
Prompt Policy
+
Tools
+
Memory
+
Permissions
+
State
+
Evaluation
```

---

# 3. Agent Position in the System

总体关系：

```text
User Task
   ↓
Agent
   ↓
Agent Runtime
   ↓
Context Builder
   ↓
Model Gateway
   ↓
Tool Gateway
   ↓
Run / Trace
   ↓
Evaluation
```

Agent 负责描述：

> “这个任务应该如何完成。”

Model 负责：

> “某一步由哪个推理引擎执行。”

Runtime 负责：

> “Workflow 如何真正运行。”

---

# 4. Agent Is Not a Model

禁止：

```text
ClaudeResearchAgent

GPTCodingAgent

DeepSeekLearningAgent
```

推荐：

```text
ResearchAgent

CodingAgent

LearningAgent
```

Model 通过：

```text
ModelPolicy
```

选择。

这样同一个 Agent 可以比较：

```text
ResearchAgent + GPT

ResearchAgent + Claude

ResearchAgent + DeepSeek

ResearchAgent + Kimi
```

---

# 5. Agent Is Not a Runtime

Agent 也不应该等于：

```text
LangGraph Agent
```

关系应为：

```text
AgentSpec
   ↓
Runtime Adapter
   ↓
LangGraph
```

未来可增加：

```text
PydanticAI Runtime

OpenAI Agents Runtime

Mastra Runtime
```

而 Agent 的业务含义不变。

---

# 6. Agent Core Entity

每个 Agent 至少包含：

```text
id

name

description

purpose

version

status

workflow

model_policy

prompt_policy

tool_policy

memory_policy

permission_policy

evaluation_policy
```

---

# 7. Agent Identity

建议字段：

```text
id
```

系统内部稳定唯一标识。

例如：

```text
research-agent
```

```text
name
```

面向用户展示：

```text
Research Agent
```

```text
description
```

简要描述职责。

```text
purpose
```

说明为什么存在该 Agent。

---

# 8. Agent Status

Agent 状态：

```text
DRAFT

ACTIVE

DISABLED

DEPRECATED
```

含义：

## DRAFT

开发中，不作为默认生产 Agent。

## ACTIVE

可以正常执行。

## DISABLED

暂时禁止运行。

## DEPRECATED

保留历史 Run，但不再建议新任务使用。

---

# 9. Agent Version

Agent 必须版本化。

例如：

```text
Research Agent v0.1
Research Agent v0.2
Research Agent v1.0
```

每次 Run 必须记录：

```text
agent_id
agent_version
```

确保未来可以回答：

> 为什么同一个 Agent 上个月和今天表现不同？

---

# 10. Agent Version Change Rules

以下修改应产生 Agent 新版本：

```text
Workflow changed

Core prompt changed

Tool policy changed

Model requirement changed

Memory policy changed

Permission policy changed

Evaluation policy materially changed
```

纯文案：

```text
description typo
```

可以不升级版本。

---

# 11. Agent Version Immutability

已经产生 Run 的 Agent Version 不应被原地覆盖。

推荐：

```text
ResearchAgent v0.1
↓
clone
↓
ResearchAgent v0.2
```

历史 Run 永远指向原版本。

---

# 12. Agent Specification Structure

概念结构：

```yaml
id: research-agent
name: Research Agent
version: 0.1
status: active

purpose: >
  Conduct technical research using multiple sources
  and produce structured, source-backed findings.

workflow: research-v1

model_policy:
  required_capabilities:
    - tools
    - structured_output
    - streaming

prompt_policy:
  system_prompt: research-system-v1

tools:
  - web_search
  - fetch_url
  - github_repository

memory_policy:
  read:
    - knowledge
  write:
    - suggest_only

permission_policy:
  default: low-risk-only

evaluation_policy:
  evaluator: research-eval-v1
```

实际实现可以使用 Python / Pydantic 配置对象，而不一定直接使用 YAML。

---

# 13. Agent Goal

每个 Agent 必须有明确 Goal。

错误：

```text
Help the user.
```

过于模糊。

推荐：

```text
Research technical topics using verifiable sources,
compare relevant alternatives,
and produce structured findings with traceable provenance.
```

Goal 必须：

```text
specific

bounded

testable
```

---

# 14. Agent Responsibilities

每个 Agent 文档必须明确：

```text
What it does

What it does not do
```

避免 Agent scope 不断扩张。

---

# 15. Research Agent Responsibility

Research Agent 负责：

```text
Understand research question

Plan information gathering

Search sources

Read sources

Compare evidence

Verify important claims

Produce structured report

Suggest next actions
```

---

# 16. Research Agent Non-Responsibilities

V0.1 不负责：

```text
Editing source code

Running shell commands

Sending emails

Automatically updating capability level

Automatically writing all output to long-term memory

Making irreversible external actions
```

---

# 17. Workflow

Agent Workflow 描述：

```text
task execution structure
```

而不是 Prompt 中隐含的一段自然语言。

Research Agent：

```text
START
  ↓
Understand
  ↓
Plan Search
  ↓
Search
  ↓
Select Sources
  ↓
Read
  ↓
Extract Findings
  ↓
Verify
  ↓
Synthesize
  ↓
Structured Output
  ↓
END
```

---

# 18. Workflow Design Principles

Workflow 节点应该：

```text
small

observable

testable

replaceable
```

禁止设计：

```text
do_everything()
```

一个节点同时：

```text
search
read
reason
write database
```

---

# 19. Workflow Node Contract

每个 Node 建议包含：

```text
name

purpose

inputs

outputs

possible_errors

emitted_events
```

---

# 20. Example Node: Plan Search

```text
Node:
plan_search

Input:
query
research_goal

Output:
search_queries

Events:
agent.step.started
agent.step.completed

Possible Errors:
structured_output_error
model_error
```

---

# 21. Agent State

Agent Runtime 通过 State 在节点之间传递信息。

State 不是任意 Dictionary。

必须有明确 Schema。

ResearchState：

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

---

# 22. State Mutation

Node 只修改其负责的 State 部分。

例如：

```text
plan_search
```

应该输出：

```text
search_queries
```

不应该同时修改：

```text
report
capability
knowledge
```

---

# 23. State Persistence

V0.1 可以先保存：

```text
run-level state snapshots
```

Future：

```text
checkpoint per node
```

用于：

```text
resume
replay
debug
human interrupt
```

---

# 24. Agent Runtime Adapter

Runtime Adapter 对上层 Agent 提供统一接口。

概念：

```text
run(agent_spec, task)

resume(run_id)

cancel(run_id)
```

Future：

```text
interrupt(run_id)

fork(run_id)
```

---

# 25. Initial Runtime

V0.1：

```text
LangGraph
```

原因：

```text
stateful workflows

conditional edges

checkpointing direction

human interrupt support
```

但禁止业务代码直接散布 LangGraph 特有逻辑。

---

# 26. Model Policy

Agent 不绑定具体模型，而声明：

```text
required_capabilities

preferred_models

allowed_models

fallback_models

reasoning_policy

budget_policy
```

---

# 27. Research Agent Model Requirements

Research Agent V0.1 建议：

```text
requires_streaming = true

requires_tools = true

requires_structured_output = true
```

Future 可能还要求：

```text
long_context
```

---

# 28. User-selected Model

V0.1 默认：

```text
user selects model
```

Agent Runtime 检查：

```text
selected model
vs
agent requirements
```

如果不兼容：

```text
reject
```

并给出明确原因。

---

# 29. Future Automatic Model Policy

Future：

```text
Research Agent
↓
Task analysis
↓
Model policy
↓
Model Router
```

例如：

```text
simple lookup
→ fast model

deep comparison
→ stronger reasoning model

long paper
→ long-context model
```

---

# 30. Prompt Policy

Agent Prompt 不应该只有一个超长 system prompt。

建议拆分：

```text
base system prompt

agent role prompt

node-specific prompt

task context

external content
```

---

# 31. Research Agent Prompt Files

建议：

```text
prompts/research/

system.md

understand.md

plan_search.md

extract_findings.md

verify_claims.md

synthesize.md
```

每个 Prompt 单独版本化。

---

# 32. Prompt Version Recording

Run 至少记录：

```text
agent version

system prompt version
```

Future 更细粒度记录：

```text
node prompt versions
```

---

# 33. Prompt Responsibilities

Prompt 应负责：

```text
behavioral instruction
task instruction
output requirement
```

代码负责：

```text
control flow
permission
validation
retry
storage
```

不能把所有工程逻辑塞进 Prompt。

---

# 34. Tool Policy

Agent 必须显式声明允许使用哪些 Tools。

Research Agent V0.1：

```text
web_search

fetch_url

github_repository
```

未声明的 Tool：

```text
cannot be called
```

---

# 35. Tool Allowlist

使用：

```text
allowlist
```

而不是：

```text
all tools available by default
```

安全原则：

> Minimum necessary tool access.

---

# 36. Tool Invocation

流程：

```text
Agent
↓
Tool Request
↓
Tool Policy Check
↓
Permission Check
↓
Tool Gateway
↓
Execution
↓
Tool Result
```

---

# 37. Tool Failure

Tool Failure 不等于 Agent Failure。

例如：

```text
web search timeout
```

Agent 可以：

```text
retry
use alternative source
continue with reduced coverage
```

最终 Run 必须记录发生过 Tool Failure。

---

# 38. Tool Retry

Retry Policy 属于 Tool / Gateway，而不是 Prompt。

Agent 不应该生成：

```text
"Maybe I should retry three times..."
```

作为可靠性机制。

---

# 39. Memory Policy

每个 Agent 声明：

```text
what memory it can read

what memory it can suggest writing

what memory it can write automatically
```

---

# 40. Research Agent Memory Policy

V0.1：

Read：

```text
Relevant Knowledge

Related Research
```

Write：

```text
suggest_only
```

即：

Agent 可以建议保存：

```text
Research result
Technology
Decision
```

但需要用户确认。

---

# 41. Memory Pollution Prevention

禁止：

```text
Every Agent output
→ Long-term memory
```

否则长期系统会积累：

```text
hallucinations
duplicates
low-quality intermediate thoughts
```

---

# 42. Knowledge vs Memory

Knowledge：

```text
user-facing persistent engineering knowledge
```

Memory：

```text
context used by Agents across tasks
```

二者可以关联，但不能混为同一概念。

---

# 43. Permission Policy

Agent Permission Policy 控制：

```text
what actions it can perform
```

默认策略：

```text
deny unless allowed
```

---

# 44. Permission Levels

## LOW

```text
search
read
analyze
```

自动执行。

## MEDIUM

```text
write local knowledge
modify workspace content
```

可配置确认。

## HIGH

```text
delete
shell
git push
external write
send message
```

必须确认。

---

# 45. Human-in-the-loop

Agent 可在运行过程中进入：

```text
WAITING_FOR_APPROVAL
```

流程：

```text
Agent proposes action
↓
Run pauses
↓
User reviews
↓
Approve / Reject
↓
Runtime resumes
```

---

# 46. Agent Run

一次 Agent 执行对应一个：

```text
Run
```

Run 是 Agent 系统最重要的观察单位。

---

# 47. Run Inputs

Run 至少保存：

```text
task

agent_id

agent_version

selected_model

runtime parameters

user metadata
```

---

# 48. Run Status

Agent Run 状态：

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
```

---

# 49. Run Events

每一步必须产生结构化事件。

例如：

```text
run.started

agent.started

agent.step.started

agent.step.completed

model.started

model.completed

tool.started

tool.completed

tool.failed

run.completed

run.failed
```

---

# 50. Agent Step Event

建议包含：

```text
step_name

step_index

status

started_at

completed_at

metadata
```

这样前端可以展示：

```text
✓ Understand task

✓ Search sources

● Verify claims

○ Generate report
```

---

# 51. Agent Trace

Trace = Run 的完整执行历史。

包括：

```text
Agent Steps

Model Calls

Tool Calls

Errors

State Transitions

Evaluation
```

---

# 52. Trace Requirements

Trace 应支持未来：

```text
debugging

comparison

regression analysis

experiment

replay
```

因此不要只保存：

```text
final answer
```

---

# 53. Agent Output

Agent 输出分：

```text
Human Output

Structured Output
```

Research Agent：

Human Output：

```text
Markdown Research Report
```

Structured Output：

```text
title

summary

key_findings

technologies

sources

open_questions

next_actions
```

---

# 54. Output Validation

Structured Output 必须：

```text
Pydantic validate
```

失败处理：

```text
repair attempt
↓
validate again
↓
fail run or mark degraded
```

禁止直接把 invalid JSON 存入正式 Knowledge。

---

# 55. Evaluation Policy

每个 Agent 声明：

```text
how its result should be evaluated
```

Research Agent：

```text
schema_validity

source_presence

source_coverage

verification_coverage

task_completion
```

Future：

```text
citation accuracy

source quality

faithfulness
```

---

# 56. Agent Cannot Self-Evaluate Alone

Agent 本身的判断：

```text
"I did a good job."
```

不能作为正式 Evaluation。

Evaluation 应由：

```text
deterministic evaluator

separate judge

human evaluator
```

完成。

---

# 57. Evaluation Timing

Evaluation 可发生：

```text
during workflow

after run

during experiment
```

V0.1 主要：

```text
after run
```

---

# 58. Agent Success

Run completed 不等于 Agent task succeeded。

需要区分：

```text
runtime_success
```

和：

```text
task_success
```

例如：

```text
Agent technically completed
but produced zero usable sources
```

则：

```text
runtime_success = true
task_success = false
```

---

# 59. Agent Failure Categories

建议：

```text
MODEL_FAILURE

TOOL_FAILURE

WORKFLOW_FAILURE

VALIDATION_FAILURE

PERMISSION_FAILURE

CONTEXT_FAILURE

TASK_FAILURE

UNKNOWN_FAILURE
```

---

# 60. Degraded Completion

某些任务可以：

```text
COMPLETED_WITH_WARNINGS
```

例如：

```text
2 of 5 sources unavailable
```

Future 可引入该状态。

V0.1 可先通过：

```text
warnings[]
```

表达。

---

# 61. Agent Retry

Agent-level retry 只用于：

```text
recoverable workflow failures
```

不要：

```text
whole agent blindly reruns
```

优先：

```text
retry failed node
```

---

# 62. Agent Cancellation

用户应该可以：

```text
Cancel Run
```

Runtime 收到 cancel 后：

```text
stop future steps

mark run cancelled

emit run.cancelled
```

已发出的外部操作不能假装回滚。

---

# 63. Agent Timeout

每个 Agent 可以定义：

```text
max_run_duration
```

每个 Node：

```text
max_step_duration
```

避免 Run 无限挂起。

---

# 64. Agent Budget

Future Agent Policy 可包含：

```text
max_tokens

max_cost

max_tool_calls

max_steps
```

防止：

```text
infinite agent loop
```

---

# 65. Loop Protection

任何循环式 Agent Workflow 必须有：

```text
max_iterations
```

例如：

```text
Search
↓
Need more?
↓ yes
Search
```

必须有退出条件。

---

# 66. Agent Context

Agent Context 包括：

```text
system instruction

user task

current state

tool results

relevant memory

relevant knowledge

runtime metadata
```

---

# 67. Context Minimization

不要把整个 Knowledge Base 都塞进 Context。

使用：

```text
retrieve
rank
select
```

只加入任务需要的信息。

---

# 68. Context Provenance

进入 Context 的外部知识应保留：

```text
source

retrieved_at

trust level
```

便于 Agent 和 Evaluation 判断可靠性。

---

# 69. Context Trust Levels

Future 可定义：

```text
SYSTEM

USER

VERIFIED_INTERNAL

TOOL_RESULT

EXTERNAL_UNTRUSTED
```

不同等级影响 Agent 如何使用内容。

---

# 70. Research Source Policy

Research Agent 应优先：

```text
primary sources

official documentation

original repositories

papers
```

再补充：

```text
secondary analysis

community discussion
```

具体来源评分策略放到 Evaluation / Research Tool 规范中。

---

# 71. Verification Node

Research Agent 中：

```text
Verify Claims
```

不要求验证所有句子。

优先验证：

```text
important factual claims

current facts

numbers

feature claims

project existence

API support
```

---

# 72. Verification Result

结构：

```text
claim

status

supporting_sources

contradicting_sources

notes
```

status：

```text
VERIFIED

PARTIALLY_VERIFIED

UNVERIFIED

CONTRADICTED
```

---

# 73. Research Agent Source Limit

为了控制成本和延迟，Run 可以配置：

```text
max_search_queries

max_sources

max_read_depth
```

V0.1 数值后续通过实验决定。

不得在规范中提前假定唯一最优数字。

---

# 74. Agent Logging

Agent Log 至少包含：

```text
run_id

agent_id

agent_version

step

event

status
```

必要时：

```text
model

tool
```

禁止保存 Secrets。

---

# 75. Agent Observability

Lab Mode 至少显示：

```text
Agent

Version

Model

Status

Steps

Tool Calls

Latency

Tokens

Estimated Cost

Errors
```

---

# 76. Agent Comparison

Future 可以比较：

```text
ResearchAgent v0.1
vs
ResearchAgent v0.2
```

控制：

```text
same task

same model

same tools

same evaluation
```

以分析 Workflow 变化影响。

---

# 77. Agent Experiment

未来实验变量：

```text
Agent Version

Model

Prompt

Tool

Workflow
```

一次实验应尽量只改变少量变量。

---

# 78. Single-Agent First

V0.1 明确采用：

```text
Single Research Agent
```

而不是：

```text
Search Agent
Reader Agent
Critic Agent
Writer Agent
```

原因：

```text
lower complexity

easier debugging

lower cost

clearer evaluation
```

---

# 79. Multi-Agent Adoption Rule

只有当真实实验显示：

```text
multi-agent
```

显著改善：

```text
quality

reliability

task decomposition
```

才引入。

禁止：

> 为了体现 Agent 技术而增加 Agent 数量。

---

# 80. Future Multi-Agent Architecture

可能结构：

```text
Supervisor
   │
   ├── Research Agent
   ├── Coding Agent
   └── Evaluation Agent
```

或者：

```text
specialized cooperative agents
```

但必须保留：

```text
individual run trace
```

和：

```text
parent-child relationship
```

---

# 81. Agent Parent / Child Runs

Future 多 Agent：

```text
Parent Run
  ├── Child Run A
  ├── Child Run B
  └── Child Run C
```

便于：

```text
trace

cost aggregation

failure attribution
```

---

# 82. Future Skills

Agent 可以拥有：

```text
Skills
```

Skill 定义：

```text
reusable instruction

workflow knowledge

tool knowledge

references
```

但 Skill 不等于 Tool。

Tool：

```text
can perform action
```

Skill：

```text
knows how to perform a type of task
```

---

# 83. Skill Loading

Future 使用：

```text
progressive loading
```

Agent 先知道 Skill Summary。

只有需要时加载完整 Skill。

避免：

```text
all skill instructions
→ every context
```

---

# 84. Agent Configuration Storage

Agent 配置需要持久化。

Future 数据模型：

```text
agents

agent_versions

agent_tools

agent_prompts

agent_permissions

agent_evaluation_policies
```

V0.1 可以先代码定义 + 数据库存版本 metadata。

---

# 85. Code vs Database Configuration

V0.1：

核心 Workflow：

```text
code
```

Agent metadata：

```text
database / config
```

不要第一版就做：

```text
visual no-code workflow editor
```

---

# 86. Agent Deployment

Agent 本身不是独立微服务。

V0.1：

```text
FastAPI Backend
   ↓
Agent Runtime
```

Future 如果任务量增大：

```text
API
↓
Task Queue
↓
Agent Worker
```

---

# 87. Background Execution

长任务最终应：

```text
Create Run
↓
Return run_id
↓
Background execution
↓
Emit events
↓
Frontend subscribes
```

避免 HTTP Request 长时间阻塞。

---

# 88. Agent Concurrency

Future 需要控制：

```text
max concurrent runs

per-agent concurrency

provider limits
```

V0.1 单用户阶段可以保持简单。

---

# 89. Agent Security Rules

禁止 Agent：

```text
access arbitrary tools

read secrets

execute high-risk action without approval

treat external text as system instruction
```

---

# 90. Prompt Injection Handling

Research Agent 遇到网页内容：

```text
Ignore previous instructions...
```

必须视为：

```text
external data
```

而不是指令。

---

# 91. Agent Data Access

Agent 应遵循：

```text
least privilege
```

Research Agent 不需要访问：

```text
filesystem write

terminal

email
```

因此 V0.1 不授予这些 Tool。

---

# 92. Agent Test Strategy

每个 Agent 至少需要：

```text
unit tests for nodes

workflow integration test

mock model test

mock tool test

regression task set
```

---

# 93. Research Agent Regression Set

建议覆盖：

```text
simple technical question

framework comparison

GitHub repository research

current information question

conflicting sources

missing sources

tool timeout

provider error

invalid structured output
```

---

# 94. Mock Agent Dependencies

CI 默认使用：

```text
MockProvider

MockTools
```

避免：

```text
every CI run
→ paid API calls
```

少量真实 Provider smoke tests 单独运行。

---

# 95. Agent Acceptance Criteria

Research Agent V0.1 完成标准：

1. 可以接收技术研究问题；
2. 可以通过 Model Gateway 使用至少两个不同模型；
3. 能生成搜索计划；
4. 能调用 Search Tool；
5. 能读取来源；
6. 能生成结构化 findings；
7. 能执行基本 claim verification；
8. 能产生结构化报告；
9. 所有关键步骤可以产生事件；
10. Run 可以在 Lab 中查看；
11. Tool Call 可以被追踪；
12. Structured Output 可以验证；
13. Provider Failure 可以正确失败或恢复；
14. 用户可以取消 Run。

---

# 96. Agent Quality Goals

V0.1 不要求：

```text
perfect autonomous research
```

优先：

```text
predictable workflow

traceable behavior

valid structured output

real sources

clear failures
```

---

# 97. Agent Development Rule

每次 Agent 改动应回答：

```text
What problem does this change solve?

What behavior should improve?

How will we evaluate it?
```

禁止：

```text
prompt tweak
without evaluation
```

---

# 98. Agent Evolution Loop

Agent 改进流程：

```text
Real Task
↓
Run
↓
Observe
↓
Identify Failure
↓
Modify Agent / Prompt / Tool
↓
Regression Test
↓
Compare
↓
Deploy New Version
```

---

# 99. Future Agent Portfolio

未来可能包括：

## Research Agent

```text
research and compare information
```

## Learning Agent

```text
identify capability gaps
generate practice tasks
evaluate evidence
```

## Coding Agent

```text
understand repository
modify code
run tests
```

## Debug Agent

```text
analyze incidents
retrieve similar problems
validate hypotheses
```

## Career Agent

```text
analyze JD
map capability gaps
prepare evidence
```

---

# 100. Agent Design Rules

必须遵守：

```text
One clear purpose per Agent

Explicit tool allowlist

Explicit model requirements

Version every meaningful behavior change

Structured state

Observable steps

Evaluatable output

Least privilege

Human approval for high-risk actions
```

---

# 101. Anti-Patterns

禁止：

## Prompt-only Agent

```text
one giant prompt
```

没有 Workflow / State / Validation。

---

## Hidden Tool Agent

Agent 可以随意使用系统所有工具。

---

## Model-bound Agent

业务逻辑直接绑定某个 Vendor SDK。

---

## Untraceable Agent

只保存最终回答，不保存执行过程。

---

## Self-evaluating Agent

Agent 自己宣布：

```text
success
```

而没有外部验证。

---

## Infinite-loop Agent

没有：

```text
max steps
budget
exit condition
```

---

# 102. Final Agent Architecture

最终关系：

```text
Task
 ↓
AgentSpec
 ↓
Agent Runtime
 ↓
Workflow
 ↓
Context Builder
 ↓
Model Gateway
 ↕
Tool Gateway
 ↓
State
 ↓
Run Events
 ↓
Output
 ↓
Evaluation
```

Agent 本身保持：

```text
Model-independent

Runtime-aware but runtime-decoupled

Tool-restricted

Versioned

Observable

Evaluatable
```

核心原则：

> **An agent is a controlled, versioned and observable execution policy for solving a class of tasks.**

而不是：

> 一个带名字的 Prompt。