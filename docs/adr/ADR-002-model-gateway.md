# ADR-002 — Model Gateway

**Status:** Accepted  
**Date:** 2026-09-29

## Context

系统需要 GPT、Claude、DeepSeek、Kimi 以及未来本地模型，不能让 Agent 绑定单一 Vendor SDK。

## Decision

建立统一 Model Gateway + Provider Adapter + Model Capability Registry。

## Consequences

优点：Agent 可切模型；统一 usage/error/streaming；方便 benchmark/fallback。

代价：需要维护内部 contract；厂商新特性需显式适配，无法零成本获得所有 vendor-specific feature。

## Alternatives

Agent 直接调用 SDK：简单但严重 vendor lock-in。只使用 OpenAI-compatible：无法可靠覆盖所有供应商独特语义。

## Guardrail

业务 Agent 禁止直接 import vendor SDK。
