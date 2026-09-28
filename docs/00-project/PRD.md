# Personal AI Engineering Workspace — Product Requirements Document

**Document Type:** Product Requirements Document  
**Version:** 0.1  
**Status:** Draft  
**Project Stage:** MVP Definition  
**Last Updated:** 2026-09-28  
**Owner:** Project Owner

---

# 1. Product Overview

## 1.1 Product Name

**Personal AI Engineering Workspace**

暂定中文名：

**个人 AI 工程工作台**

---

## 1.2 Product Vision

构建一个由 AI Agents 驱动的个人工程工作台，让 AI 深度参与技术学习、研究、软件开发、问题解决和职业成长。

与此同时，将真实的个人任务作为 AI Engineering 实验环境，用于持续学习、比较和改进：

- 不同大语言模型；
- 不同 Agent 架构；
- 不同 Prompt；
- 不同 Tools；
- 不同 Memory 方案；
- 不同工作流；
- 不同 Evaluation 方法。

核心理念：

> **Use AI to improve how I learn and work, and use my real work to learn how to build better AI agents.**

---

# 2. Background

当前技术学习、工程实践和 AI 使用过程高度碎片化。

用户每天可能同时使用：

- ChatGPT；
- Claude；
- DeepSeek；
- Kimi；
- GitHub；
- 浏览器；
- IDE；
- Terminal；
- Markdown / Notes；
- 各类技术文档和论文。

这些工具分别解决局部问题，但缺少一个统一系统将整个过程连接起来。

典型过程如下：

```text
发现新技术
↓
搜索资料
↓
比较项目
↓
阅读文档
↓
询问 AI
↓
尝试代码
↓
遇到报错
↓
重新搜索
↓
解决问题
↓
写一些笔记
↓
几周后忘记过程
```

结果是：

- 信息被消费，但没有系统沉淀；
- 技术被阅读，但没有转化为能力；
- 问题被解决，但 Debugging 过程丢失；
- 多个 AI 被使用，但能力没有形成统一工作流；
- 项目和求职之间缺少系统映射；
- 历史决策难以回溯。

---

# 3. Problem Statement

本产品重点解决五类核心问题。

---

## P1. 技术信息过载

用户持续接触：

- GitHub 项目；
- 新模型；
- 新框架；
- 技术文章；
- 论文；
- 招聘 JD；
- 工程经验。

真正困难的并不是“找到信息”，而是：

> 哪些内容值得投入时间？

当前通常需要反复执行：

```text
发现
→ 搜索
→ 阅读
→ 对比
→ 判断
→ 重新搜索
```

缺少长期的研究记录和决策依据。

---

## P2. Knowledge 不等于 Capability

传统知识管理系统通常记录：

> 我看过什么。

但工程能力真正需要回答：

> 我能独立做到什么？

例如对于 FastAPI：

```text
知道是什么
✓

能读代码
✓

能运行示例
✓

能自己写 CRUD
✓

能实现 SSE
△

能处理生产问题
✕
```

目前缺少能够连接：

```text
Knowledge
→ Practice
→ Evidence
→ Capability
```

的系统。

---

## P3. 工程问题解决过程持续流失

大量开发问题遵循：

```text
Problem
↓
Attempt
↓
Failure
↓
New Hypothesis
↓
Diagnosis
↓
Solution
```

但最终通常只留下：

> “执行这个命令就好了。”

导致几个月之后遇到类似问题时，又需要重新搜索和分析。

因此需要长期保存：

- 问题背景；
- 环境；
- 错误信息；
- 尝试过程；
- 无效方案；
- 原因；
- 最终解决方案；
- 可复用经验。

---

## P4. 多个 AI 模型彼此割裂

用户可能同时使用：

```text
ChatGPT
Claude
DeepSeek
Kimi
Qwen
Gemini
Local Models
```

当前存在：

- 上下文割裂；
- 无法统一比较；
- 无法统一调用工具；
- Token / Cost 不透明；
- 不同模型行为无法长期观察；
- 更换模型需要重新适配应用逻辑。

因此需要建立统一的：

> **Model Gateway + Agent Runtime**

---

## P5. 学习、项目和职业发展缺少连接

招聘岗位要求可能是：

```text
FastAPI
Redis
SSE
LangGraph
PostgreSQL
```

但用户并不能直接回答：

```text
我会哪些？
会到什么程度？
有什么证据？
哪里还有 Gap？
应该通过什么项目补足？
```

产品需要建立：

```text
Job Requirement
↕
Capability
↕
Learning Task
↕
Project
↕
Evidence
```

的长期映射。

---

# 4. Product Objectives

## 4.1 Primary Objective

建立一个长期使用的 AI-native Engineering Workspace，将用户日常的：

```text
Research
Learning
Coding
Debugging
Career
```

统一连接起来。

---

## 4.2 AI Objective

让 AI 不只是回答问题，而是真正参与任务执行：

```text
Understand
Plan
Search
Use Tools
Analyze
Verify
Generate
Store
Evaluate
```

---

## 4.3 Learning Objective

项目本身需要成为用户学习 AI Engineering 的实验环境。

通过真实使用掌握：

- LLM API；
- Multi-model integration；
- Model Gateway；
- Agent Runtime；
- Tool Calling；
- MCP；
- RAG；
- Memory；
- Streaming；
- Structured Output；
- Evaluation；
- Observability；
- Human-in-the-loop；
- Multi-Agent；
- Agent Debugging。

---

# 5. Non-Goals

MVP 阶段明确不尝试成为：

- ChatGPT 替代产品；
- Dify 替代产品；
- 通用 AI Agent 平台；
- 企业团队协作平台；
- 完整项目管理系统；
- Notion / Obsidian 替代品；
- 大规模 Coding Agent；
- 完全自治 Multi-Agent 系统；
- MCP Marketplace；
- 商业 SaaS。

原则：

> 优先解决真实个人工作流，然后再考虑抽象和扩展。

---

# 6. Target Users

## 6.1 MVP Primary User

V0.x 阶段主要服务：

> **项目开发者本人**

典型特征：

- 持续学习 AI / Software Engineering；
- 经常调研 GitHub 项目；
- 经常阅读论文、技术文章和文档；
- 经常需要使用多个 AI；
- 经常进行代码开发和 Debug；
- 正在积累职业能力和项目 Evidence。

---

## 6.2 Potential Future Users

如果个人使用验证有效，未来可能扩展至：

- AI Engineers；
- Software Engineers；
- Graduate Students；
- Independent Researchers；
- Technical Learners；
- Open-source Developers。

---

# 7. Core Product Principle

系统围绕两个闭环设计。

## 7.1 Personal Growth Loop

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

---

## 7.2 AI Engineering Loop

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

两个闭环相互连接。

```text
AI improves user
↓
Real usage produces problems
↓
Problems drive AI engineering experiments
↓
Agents improve
↓
AI improves user further
```

---

# 8. Product Modes

产品分为两个核心模式。

---

## 8.1 Workspace Mode

目标：

> **让 AI 帮助用户完成真实任务。**

主要领域：

- Research；
- Learning；
- Knowledge；
- Engineering Journal；
- Coding；
- Career；
- Tasks。

---

## 8.2 Lab Mode

目标：

> **理解 AI 如何完成任务，并改进 Agent。**

主要领域：

- Agents；
- Models；
- Providers；
- Tools；
- MCP；
- Runs；
- Traces；
- Evaluations；
- Experiments；
- Benchmarks。

---

# 9. MVP Core Scenarios

V0.1 优先支持以下场景。

---

## Scenario 1 — Technology Research

用户输入：

```text
Compare LangGraph and PydanticAI.
```

系统执行：

```text
Understand
↓
Plan Search
↓
Search
↓
Read Sources
↓
Extract Findings
↓
Verify
↓
Compare
↓
Generate Report
```

最终生成：

- Research Report；
- Source List；
- Key Findings；
- Related Technologies；
- Next Actions。

---

## Scenario 2 — GitHub Repository Research

用户粘贴：

```text
GitHub Repository URL
```

系统分析：

- Repository 基本信息；
- README；
- 技术栈；
- 架构；
- 活跃度；
- 使用场景；
- 与相关项目的区别；
- 学习价值。

结果保存为 Research Item。

---

## Scenario 3 — Knowledge Capture

Research 完成后用户可以：

```text
Save to Knowledge
```

系统提取：

- Technology；
- Concepts；
- Decisions；
- Related Topics；
- Sources。

---

## Scenario 4 — Capability Tracking

例如：

```text
Technology:
LangGraph

Current Level:
2 / 5
```

系统记录：

- 当前能力；
- 能力依据；
- Evidence；
- 缺失能力；
- 下一目标；
- Next Action。

---

## Scenario 5 — Agent Run Inspection

每次 Research Agent 执行后，可以进入 Lab 查看：

```text
Model
Provider
Agent Version
Steps
Tool Calls
Latency
Tokens
Estimated Cost
Errors
```

---

# 10. Universal Capture

系统提供统一入口：

```text
Paste anything...
```

MVP 支持输入：

- Question；
- URL；
- GitHub Repository；
- Job Description；
- Error；
- Plain Text。

系统判断：

```text
Input Type
↓
Suggested Action
```

例如：

```text
GitHub URL

Detected:
Repository

Recommended:
Research
```

用户确认后进入对应 workflow。

---

# 11. Research Agent Requirements

V0.1 使用单 Agent Workflow。

禁止为了展示 Multi-Agent 而人为拆分。

Workflow：

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
Generate Structured Report
↓
END
```

---

# 12. Multi-Model Requirements

V0.1 计划支持：

- OpenAI；
- Anthropic；
- DeepSeek；
- Kimi。

上层 Agent 不直接依赖 Provider。

统一：

```text
Agent
↓
Model Gateway
↓
Provider Adapter
↓
Model
```

用户可以手动选择模型。

Future：

```text
Automatic Model Routing
Fallback
Benchmark
```

---

# 13. Research Output Requirements

Research Agent 不能只输出自由 Markdown。

同时生成：

## Human-readable Output

```text
Summary
Key Findings
Comparison
Recommendation Context
Sources
Next Actions
```

## Structured Output

包含：

```text
title
summary
key_findings
technologies
related_topics
sources
open_questions
next_actions
```

Structured Output 将用于后续自动建立 Knowledge Relation。

---

# 14. Knowledge Requirements

MVP Knowledge 类型：

- technology；
- concept；
- research；
- decision；
- note。

每个 Knowledge Item 应保存：

```text
title
summary
content
type
sources
related items
created_at
updated_at
```

---

# 15. Capability Requirements

Capability Level：

```text
0 — 未接触

1 — 理解基本概念

2 — 可以运行和修改示例

3 — 可以独立实现常见功能

4 — 可以独立 Debug / Optimize

5 — 可以设计复杂系统并清晰解释
```

Level 必须附带：

- Reason；
- Evidence；
- Next Target；
- Next Action。

---

# 16. Evidence Requirements

Evidence 类型包括：

- Git Commit；
- Repository；
- Project；
- Code；
- Experiment；
- Research；
- Manual Verification。

一个 Evidence 可以关联多个 Capability。

例如：

```text
Implemented SSE Research Streaming

supports:

FastAPI
Async Python
SSE
React
```

---

# 17. Agent Lab Requirements

MVP Lab 只需要支持：

> **Runs**

每个 Run 展示：

```text
Input

Agent

Model

Provider

Timeline

Tool Calls

Latency

Tokens

Estimated Cost

Status

Errors
```

---

# 18. Streaming Requirements

Agent 运行过程必须实时反馈。

示例：

```text
✓ Understand task
✓ Search sources
● Reading sources
○ Verify claims
○ Generate report
```

V0.1 优先使用：

```text
SSE
```

而不是 WebSocket。

---

# 19. Trace Requirements

每次 Agent 行为需要产生结构化事件。

至少：

```text
run.started

agent.started

agent.step

model.started

model.completed

tool.started

tool.completed

tool.failed

run.completed

run.failed
```

这些数据是未来：

- Observability；
- Evaluation；
- Replay；
- Debugging；
- Experiment

的基础。

---

# 20. AI Evaluation Requirements

AI 输出不能只依赖人工感觉。

MVP 至少实现：

## Deterministic Validation

例如：

- Structured output valid；
- Required fields exist；
- Source URL exists；
- Tool successfully executed。

Future：

- citation coverage；
- source quality；
- factual verification；
- model-based evaluation；
- benchmark。

---

# 21. Human-in-the-loop Requirements

MVP Research 场景大部分属于低风险操作。

未来 Tool 权限划分：

## Low Risk

```text
Search
Read
Analyze
```

自动执行。

## Medium Risk

```text
Write local knowledge
Modify file
```

可配置确认。

## High Risk

```text
Delete
Git push
Send external message
Execute risky shell command
```

必须显式确认。

---

# 22. MVP Navigation

V0.1 Sidebar：

```text
Home

Research

Knowledge

Capabilities

Agent Lab

Settings
```

Future：

```text
Learning

Projects

Career

Engineering Journal

Agents
```

---

# 23. MVP Functional Scope

V0.1 必须完成：

## P0

- Model Gateway；
- Multi-model configuration；
- Research Agent；
- Web / GitHub Research Tools；
- Streaming；
- Agent Runs；
- Run Timeline；
- Research Report；
- Knowledge Storage。

## P1

- Universal Capture；
- Source Verification；
- Capability Map；
- Evidence。

---

# 24. Out of Scope for V0.1

以下功能暂不实现：

- Multi-Agent；
- Coding Agent；
- Career Agent；
- Learning Agent；
- Browser Computer Use；
- Terminal Execution；
- Complex Memory；
- MCP Marketplace；
- Automatic Model Routing；
- Agent Replay；
- Agent Debugger；
- Full Benchmark Platform；
- Mobile App；
- Team Collaboration。

---

# 25. MVP Acceptance Flow

V0.1 必须完整跑通以下用户流程：

```text
Open Application
↓
Enter:
"Compare LangGraph and PydanticAI"
↓
Select Model
↓
Start Research
↓
See Agent Progress in Real Time
↓
Receive Research Report
↓
View Sources
↓
Save to Knowledge
↓
Create / Link:
LangGraph
PydanticAI
↓
Update Capability
↓
Open Agent Lab
↓
Inspect Run
```

只有这条链完整成立，V0.1 才视为完成。

---

# 26. Success Metrics

V0.1 不以用户数或 GitHub Star 为第一成功指标。

## Personal Usage

关注：

- Weekly active usage；
- Research tasks completed；
- Past research reused；
- Knowledge items revisited；
- Evidence created。

---

## AI Engineering

关注：

- Agent run success rate；
- Tool call success rate；
- Average latency；
- Token usage；
- Estimated cost；
- Failed run reasons。

---

## Personal Growth

关注：

- 重复研究是否减少；
- 历史技术决策是否容易回溯；
- 学习是否开始产生 Evidence；
- 能否更清楚知道下一步应该学什么。

---

# 27. Product Risks

## R1 — Scope Explosion

Risk：

持续加入热门 AI 功能，导致核心闭环无法完成。

Mitigation：

所有 Feature 必须回答：

```text
Does this solve a real workflow problem?
```

---

## R2 — AI Feature for Demo Only

Risk：

为了体现技术含量加入不必要 Multi-Agent / Memory / MCP。

Mitigation：

AI Feature 必须同时具有：

```text
User Value
+
Engineering Learning Value
```

---

## R3 — Knowledge Pollution

Risk：

错误 AI 输出长期进入 Knowledge Base。

Mitigation：

保存：

- Source；
- Provenance；
- Verification status。

---

## R4 — Vendor Lock-in

Risk：

业务逻辑与某一家 Model SDK 深度绑定。

Mitigation：

统一 Model Gateway。

---

## R5 — Project Becomes Another Chat UI

Risk：

最终演化成普通聊天机器人。

Mitigation：

核心对象必须是：

```text
Research
Knowledge
Capability
Evidence
Run
```

而不是：

```text
Conversation
```

---

# 28. Product Assumptions

当前假设：

1. 用户愿意持续使用系统进行技术 Research；
2. AI Research 能节省重复搜索时间；
3. Knowledge + Capability + Evidence 比普通 Note 更有长期价值；
4. 多模型统一接入能够提升 AI Engineering 学习价值；
5. Agent Trace 对理解模型行为有价值；
6. Personal-first 可以降低产品早期复杂度。

这些假设必须通过真实使用逐步验证。

---

# 29. Roadmap Summary

## V0.1

```text
Research Loop
```

核心：

```text
Multi-model
Research Agent
Trace
Knowledge
Capability
```

---

## V0.2

```text
Learning Loop
```

增加：

- Learning Agent；
- Engineering Journal；
- Semantic Search；
- JD Parser。

---

## V0.3

```text
Build Loop
```

增加：

- Coding Agent；
- GitHub Integration；
- Terminal Sandbox；
- Human Approval。

---

## V0.4

```text
AI Engineering Lab
```

增加：

- Experiments；
- Evaluations；
- Model Comparison；
- Agent Comparison；
- Benchmark。

---

## V1.0

形成完整：

```text
Research
↓
Learn
↓
Build
↓
Evidence
↓
Career
```

闭环。

---

# 30. Open Questions

当前仍未最终确定：

- Web Search Provider；
- GitHub API / MCP 接入方式；
- Embedding Model；
- Semantic Retrieval Strategy；
- Prompt Versioning；
- Agent Versioning；
- Knowledge Relation Model；
- Model Pricing Metadata；
- Evaluation Dataset；
- Local Model Integration；
- Browser Automation Strategy。

这些问题应在对应设计阶段通过 ADR 决策，而不是在 PRD 中提前锁死。

---

# 31. Definition of Product Success

这个产品最核心的判断标准不是：

```text
How many features does it have?
```

而是：

> **Would I still use this every week even if nobody starred the GitHub repository?**

如果答案是 Yes，产品首先完成了最重要目标。

在此基础上，再将经过个人验证的工作流抽象成适合其他 AI Engineers、Developers 和 Researchers 使用的开源产品。

---

# 32. Core Product Statement

最终产品使命可以总结为：

> **Build an AI-native workspace that turns everyday research, learning and engineering work into lasting knowledge, verifiable capability and reusable evidence — while using those real tasks to continuously experiment with and improve AI agents.**