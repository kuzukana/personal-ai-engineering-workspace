# ADR-003 — LangGraph as Initial Agent Runtime

**Status:** Accepted  
**Date:** 2026-09-29

## Context

Research Agent 是明确的 stateful workflow，需要节点、条件边、checkpoint/human-interrupt 演进能力。

## Decision

V0.1 使用 LangGraph 作为第一个 Runtime，但 AgentSpec、State、Model/Tool contracts 与 LangGraph API 解耦。

## Consequences

优点：适合可观察状态工作流；生态成熟；利于后续 HITL。

代价：引入 framework dependency；需要 Runtime Adapter 降低锁定。

## Alternatives

自研 runtime：控制力高但初期成本过大。PydanticAI/OpenAI Agents SDK：保留为未来实验 runtime。

## Guardrail

LangGraph 是 runtime implementation，不是 Agent domain model。
