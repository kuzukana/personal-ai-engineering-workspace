# Personal AI Engineering Workspace — Model Specification

**Document Type:** Model Integration Specification  
**Version:** 0.1  
**Status:** Draft  
**Project Stage:** MVP AI Infrastructure Design  
**Owner:** Project Owner  
**Last Updated:** 2026-09-28  

**Related Documents:**
- `AI_SYSTEM_SPEC.md`
- `AGENT_SPEC.md`
- `EVALUATION.md`
- `../01-design/TECHNICAL_DESIGN.md`
- `../03-contracts/API_SPEC.md`
- `../03-contracts/EVENT_SPEC.md`
- `../adr/ADR-002-model-gateway.md`

---

# 1. Purpose

本文档定义系统中的：

```text
Provider

Model

Model Capability

Model Request

Model Response

Streaming Event

Tool Calling

Structured Output

Usage

Error

Retry

Fallback

Routing
```

等统一规范。

目标是确保：

> 上层 Agent 不需要理解不同模型厂商之间的 API 差异。

---

# 2. Design Principle

核心原则：

> **Stable model contract, replaceable provider implementation.**

Agent 只依赖：

```text
Model Gateway
```

而不是：

```text
OpenAI SDK
Anthropic SDK
DeepSeek SDK
Kimi SDK
```

---

# 3. Core Concepts

## 3.1 Provider

Provider 表示模型服务来源。

例如：

```text
OpenAI
Anthropic
DeepSeek
Kimi
Google
Alibaba
Local
```

---

## 3.2 Model

Model 是 Provider 提供的具体推理模型。

关系：

```text
Provider
   │
   ├── Model A
   ├── Model B
   └── Model C
```

Provider 与 Model 必须分离建模。

---

# 4. Initial Provider Scope

V0.1 优先考虑：

```text
OpenAI
Anthropic
DeepSeek
Kimi
```

未来扩展：

```text
Gemini
Qwen
GLM
MiniMax
Ollama
vLLM
OpenAI-compatible local endpoints
```

---

# 5. Provider Adapter Architecture

统一结构：

```text
Agent
  ↓
Model Gateway
  ↓
Provider Adapter
  ↓
Vendor API
```

Provider Adapter 负责：

```text
Request Conversion

Response Conversion

Streaming Conversion

Error Normalization

Usage Normalization

Capability Detection
```

---

# 6. Provider Interface

每个 Provider Adapter 应实现统一接口：

```text
generate()

stream()

health_check()

normalize_error()

get_capabilities()
```

Future 可增加：

```text
count_tokens()

list_models()

estimate_cost()
```

---

# 7. Model Request Contract

统一内部请求对象：

```text
ModelRequest
```

建议字段：

```text
request_id

model_id

messages

system_prompt

tools

tool_choice

temperature

top_p

max_output_tokens

structured_schema

stream

metadata
```

---

# 8. Message Contract

统一消息结构：

```text
role

content

name

metadata
```

role 支持：

```text
system

user

assistant

tool
```

内部消息格式不直接暴露厂商特有字段。

---

# 9. Content Types

Future 统一支持多模态：

```text
text

image

file

audio
```

V0.1 先保证：

```text
text
```

完整工作。

---

# 10. Model Response Contract

统一：

```text
ModelResponse
```

字段：

```text
request_id

model_id

provider

content

tool_calls

structured_output

usage

finish_reason

latency_ms

provider_metadata
```

---

# 11. Tool Call Contract

统一 Tool Call：

```text
tool_call_id

tool_name

arguments

status
```

不同 Provider 的 function/tool-call 表达方式必须转成统一结构。

---

# 12. Structured Output

如果模型支持原生 Structured Output：

```text
prefer native mode
```

否则：

```text
prompt + JSON parsing + schema validation
```

统一最终结果必须通过：

```text
Pydantic Schema Validation
```

---

# 13. Model Capability Registry

每个 Model 必须声明 capability。

建议字段：

```text
supports_streaming

supports_tools

supports_parallel_tools

supports_structured_output

supports_vision

supports_audio

supports_reasoning

supports_system_prompt

supports_json_mode

context_window

max_output_tokens
```

---

# 14. Capability Requirement

Agent 可声明最低能力要求。

例如 Research Agent：

```text
requires_streaming = true

requires_tools = true

requires_structured_output = true
```

Gateway 在执行前检查：

```text
Agent Requirement
vs
Model Capability
```

---

# 15. Unsupported Capability Handling

如果能力不满足：

```text
reject
```

或：

```text
select compatible fallback
```

禁止：

```text
silent downgrade
```

除非策略明确允许。

---

# 16. Model Registry

Model Registry 保存系统中可使用的 Model。

字段建议：

```text
id

provider_id

model_key

display_name

capabilities

enabled

default_temperature

default_max_output_tokens
```

Future：

```text
pricing

region

availability

benchmark_metadata
```

---

# 17. Provider Registry

Provider Registry：

```text
id

name

type

base_url

enabled

configuration
```

Secret 不直接存普通配置字段。

---

# 18. OpenAI-Compatible Adapter

系统提供：

```text
OpenAICompatibleProvider
```

用于支持具有兼容接口的模型服务。

配置：

```text
provider_name

base_url

api_key_reference

default_headers
```

这样可以降低：

```text
DeepSeek
Kimi
Qwen
Local endpoint
```

等接入成本。

---

# 19. Native Adapter Strategy

如果某 Provider 有关键能力无法通过 Compatible Adapter 充分表达，则使用：

```text
Native Provider Adapter
```

例如：

```text
vendor-specific reasoning controls

special streaming events

special tool calling semantics
```

---

# 20. Model Gateway Responsibilities

Model Gateway 负责：

```text
Resolve Model

Check Capability

Resolve Provider

Build Provider Request

Execute

Normalize Response

Emit Events

Record Usage

Handle Retry

Handle Fallback
```

---

# 21. Manual Model Selection

V0.1 默认：

```text
User selects model
```

例如：

```text
Research Agent
Run with:
Claude
```

---

# 22. Automatic Routing

Future 支持：

```text
Task
↓
Requirement
↓
Routing Policy
↓
Model
```

Routing 可考虑：

```text
quality

latency

cost

context length

tool support

vision support

reasoning capability
```

---

# 23. Model Policy

Agent 不绑定 Model，但可以定义 Model Policy。

例如：

```text
preferred_model

allowed_models

required_capabilities

fallback_models

budget_policy
```

---

# 24. Streaming

所有 Provider Streaming Event 必须统一。

内部事件包括：

```text
model.started

text.delta

reasoning.delta

tool_call.started

tool_call.arguments.delta

tool_call.completed

usage.updated

model.completed

model.failed
```

---

# 25. Provider Event Translation

示例：

```text
Vendor Event
    ↓
Provider Adapter
    ↓
Internal Model Event
```

Frontend 和 Agent Runtime 不读取 Vendor Event。

---

# 26. Time to First Token

记录：

```text
ttft_ms
```

用于比较不同模型的实际交互体验。

---

# 27. Latency

每次模型调用至少记录：

```text
started_at

first_token_at

completed_at

ttft_ms

total_latency_ms
```

---

# 28. Token Usage

统一 Usage：

```text
input_tokens

output_tokens

reasoning_tokens

cached_input_tokens

total_tokens
```

不支持的字段：

```text
null
```

不要伪造为 0。

---

# 29. Cost

系统可以记录：

```text
estimated_cost
```

但必须明确：

```text
estimated
```

而不是账单最终金额。

---

# 30. Pricing Metadata

Future Model Registry 可保存：

```text
input_price

output_price

reasoning_price

cache_price

currency

effective_date
```

价格属于时间敏感配置。

不得硬编码在业务逻辑中。

---

# 31. Finish Reason

统一：

```text
STOP

LENGTH

TOOL_CALL

CONTENT_FILTER

ERROR

UNKNOWN
```

Provider 特有值转成内部枚举。

---

# 32. Error Model

统一错误：

```text
ProviderAuthenticationError

ProviderRateLimitError

ProviderTimeoutError

ProviderUnavailableError

ModelNotFoundError

ModelCapabilityError

StructuredOutputError

ContentPolicyError

UnknownProviderError
```

---

# 33. Error Normalization

例如不同 Provider 的：

```text
429
rate_limit
quota exceeded
```

统一映射：

```text
ProviderRateLimitError
```

Agent 不读取 Vendor Error Class。

---

# 34. Retry Policy

默认只对可恢复错误 retry：

```text
Timeout

Temporary 5xx

Rate Limit
```

策略：

```text
exponential backoff
+
jitter
+
max retry count
```

---

# 35. Non-Retry Errors

以下通常不重试：

```text
Authentication Error

Invalid Request

Unsupported Capability

Content Validation Error
```

---

# 36. Fallback

Future 支持：

```text
Primary Model
 ↓
Recoverable Failure
 ↓
Fallback Model
```

Fallback 必须记录：

```text
primary_model

failure_reason

fallback_model
```

---

# 37. Fallback Rules

禁止所有错误都 fallback。

例如：

```text
Invalid Prompt
```

换模型并不能真正解决问题。

Fallback 应针对：

```text
provider unavailable

rate limit

model temporarily unavailable
```

等明确场景。

---

# 38. Context Window

Model Registry 必须保存：

```text
context_window
```

Context Builder 使用此值进行：

```text
truncation

retrieval selection

summarization
```

---

# 39. Token Budget

每次调用可以定义：

```text
input_budget

output_budget

total_budget
```

Future Agent Run 还可以定义：

```text
run_token_budget
```

---

# 40. Cost Budget

Future：

```text
max_cost_per_call

max_cost_per_run

daily_budget
```

超过预算：

```text
stop

ask user

route cheaper model
```

---

# 41. Temperature

Temperature 不应由页面随意散落配置。

优先由：

```text
Model Policy
```

或：

```text
Agent Configuration
```

管理。

---

# 42. Deterministic-Oriented Tasks

对于：

```text
classification

structured extraction

validation
```

默认倾向较低随机性。

---

# 43. Creative Tasks

对于：

```text
brainstorming

writing

ideation
```

可允许较高随机性。

---

# 44. Reasoning Controls

不同 Provider 对 reasoning 支持不同。

内部可定义抽象：

```text
reasoning_effort
```

例如：

```text
low

medium

high
```

Adapter 决定如何映射到 Vendor API。

如果不支持：

```text
ignore only if explicitly allowed
```

否则 capability validation。

---

# 45. System Prompt Support

部分 Provider 的 system instruction 表达不同。

统一内部：

```text
system_prompt
```

Adapter 负责映射。

---

# 46. Tool Support

如果 Agent 要使用 Tool：

```text
model must support tool calling
```

或者由 Runtime 使用兼容模式模拟。

V0.1 优先使用原生 Tool Calling。

---

# 47. Parallel Tool Calls

Model Capability 中声明：

```text
supports_parallel_tools
```

Agent Runtime 不应默认所有模型都支持。

---

# 48. Vision

Future：

```text
ImageContent
```

经过统一 Message Content Contract 发送。

V0.1 不作为硬性要求。

---

# 49. Local Models

Future 支持：

```text
Ollama

vLLM

OpenAI-compatible local server
```

本地模型应该和云模型一样通过：

```text
Provider Adapter
```

接入。

---

# 50. Privacy Policy

Model 调用前 Future 可根据任务数据分类：

```text
PUBLIC

PERSONAL

SENSITIVE
```

Routing Policy 可规定：

```text
Sensitive
→ local model only
```

---

# 51. Provider Health

Provider Adapter 支持：

```text
health_check()
```

记录：

```text
available

latency

last_success

last_failure
```

Future Model Router 可使用这些信息。

---

# 52. Model Status

Model 可处于：

```text
ACTIVE

DISABLED

DEPRECATED

UNAVAILABLE
```

Deprecated Model 不应继续作为新 Agent 默认配置。

---

# 53. Model Version Drift

模型供应商可能在不改变名称的情况下更新行为。

因此实验结果必须保存：

```text
provider

model identifier

run timestamp

provider metadata
```

以便解释长期行为变化。

---

# 54. Model Evaluation

不同模型比较时必须使用：

```text
same task

same agent version

same prompt version

same tools

same evaluation
```

否则比较缺乏意义。

---

# 55. Benchmark Dimensions

Model Benchmark 可比较：

```text
Task Success

Output Quality

Tool Success

Citation Quality

Latency

TTFT

Tokens

Cost

Failure Rate
```

---

# 56. Statistical Considerations

由于 LLM 非确定性：

```text
one run
```

不能代表模型总体表现。

Future benchmark 应：

```text
repeat runs

aggregate metrics

report variance
```

---

# 57. Model Experiment

实验对象：

```text
Model A
vs
Model B
```

控制：

```text
Agent

Prompt

Tools

Task

Evaluation
```

---

# 58. Model Selection UI

V0.1 UI 至少显示：

```text
Provider

Model Name
```

Future 可显示：

```text
Tool Support

Vision

Context

Cost

Latency
```

---

# 59. Provider Settings UI

Settings：

```text
Provider

Connection Status

Base URL

Default Model

Enabled
```

API Key 不能再次以明文展示。

---

# 60. Secret Storage

V0.1 本地：

```text
.env
```

例如：

```text
OPENAI_API_KEY

ANTHROPIC_API_KEY

DEEPSEEK_API_KEY

KIMI_API_KEY
```

禁止：

```text
commit .env
```

---

# 61. Secret Reference

系统内部配置 Future 应保存：

```text
secret_reference
```

而不是：

```text
raw secret
```

---

# 62. Provider Logging

Provider Log 可以记录：

```text
provider

model

request_id

status

latency

usage
```

禁止记录：

```text
API key
```

---

# 63. Raw Provider Response

是否长期保存 raw provider response 需要谨慎。

V0.1：

```text
do not persist full raw response by default
```

只保存：

```text
normalized response
+
necessary metadata
```

---

# 64. Model Metadata

允许保存 Vendor metadata：

```text
request identifier

cache metadata

model revision metadata
```

但必须通过：

```text
provider_metadata
```

隔离，不污染核心 Contract。

---

# 65. Model Gateway Failure Boundary

如果 Provider Adapter 崩溃：

```text
Agent Runtime
```

应该收到：

```text
normalized AI error
```

而不是 SDK traceback。

详细 traceback 写入 server log。

---

# 66. Testing Strategy

Provider Adapter 需要：

```text
unit tests

mock integration tests
```

真实 Provider：

```text
smoke test
```

避免测试套件每次都产生高额 API 成本。

---

# 67. Contract Tests

所有 Adapter 必须通过统一 Contract Test：

```text
generate text

stream text

return usage

normalize error

structured output
```

若支持 Tool：

```text
tool calling test
```

---

# 68. Provider Mock

需要提供：

```text
MockProvider
```

用于：

```text
local development

unit tests

CI
```

避免所有开发依赖真实 LLM。

---

# 69. Mock Model

MockModel 可以返回：

```text
fixed response

scripted tool call

streamed chunks

simulated error
```

这对测试 SSE 和 Agent Workflow 非常重要。

---

# 70. Configuration Structure

推荐：

```text
ai/
  providers/
    base.py
    openai.py
    anthropic.py
    openai_compatible.py
    mock.py

  gateway/
    gateway.py

  registry/
    models.py
    providers.py

  schemas/
    request.py
    response.py
    usage.py
    events.py
```

---

# 71. MVP Provider Implementation Order

建议：

```text
1. MockProvider

2. OpenAI Provider

3. Anthropic Provider

4. OpenAI-Compatible Provider

5. DeepSeek configuration

6. Kimi configuration
```

先 Mock 是为了尽早验证整体架构。

---

# 72. MVP Acceptance Criteria

V0.1 Model Layer 必须满足：

1. Agent 通过统一 Gateway 调用模型；
2. 至少支持两个真实 Provider；
3. 同一 Agent 可切换模型；
4. Streaming 可被统一处理；
5. Tool Call 可统一解析；
6. Usage 可记录；
7. Error 可统一归类；
8. Model capability 可查询；
9. Structured Output 可验证；
10. Mock Provider 可用于自动测试。

---

# 73. Future Model Features

后续可加入：

```text
automatic routing

cost-aware routing

quality-aware routing

fallback

load balancing

local-first routing

model benchmark dashboard

provider health dashboard

dynamic pricing metadata
```

---

# 74. Key Risks

## Vendor API Drift

厂商 API 变化。

Mitigation：

```text
Provider Adapter Boundary
```

---

## Capability Mismatch

不同模型能力差异。

Mitigation：

```text
Capability Registry
```

---

## Cost Explosion

多个 Agent 调用高成本模型。

Mitigation：

```text
usage tracking

budget

routing
```

---

## Hidden Fallback

用户不知道模型实际被换掉。

Mitigation：

```text
fallback event + trace
```

---

## Model Behavior Drift

模型升级导致行为变化。

Mitigation：

```text
regression benchmark
+
run history
```

---

# 75. Model Design Rules

禁止：

```text
Agent directly imports vendor SDK
```

禁止：

```text
Hardcoded model name across business logic
```

禁止：

```text
Silent provider fallback
```

禁止：

```text
Assuming all providers support the same features
```

要求：

```text
Every model call is traceable.
```

---

# 76. Final Model Architecture

最终结构：

```text
Agent
  ↓
Model Policy
  ↓
Model Gateway
  ↓
Capability Validation
  ↓
Provider Adapter
  ↓
Model
  ↓
Normalized Response
  ↓
Run / Trace / Evaluation
```

核心原则：

> **Models are interchangeable execution engines, not hardcoded application dependencies.**

该设计保证系统未来可以持续引入新的：

```text
GPT

Claude

DeepSeek

Kimi

Qwen

Gemini

Local Models
```

而不破坏上层 Agent 和产品业务逻辑。