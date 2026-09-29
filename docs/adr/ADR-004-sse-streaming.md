# ADR-004 — SSE for MVP Streaming

**Status:** Accepted  
**Date:** 2026-09-29

## Context

V0.1 主要需要 server → client 的 Agent progress、model text、tool status 和 run events。

## Decision

使用 Server-Sent Events 作为 MVP 实时通道。

## Consequences

优点：HTTP-native；浏览器支持；自动 reconnect；实现简单；适合单向流。

代价：不适合高频双向交互和交互式 terminal。

## Alternatives

WebSocket：能力更强但 MVP 复杂度不必要。Polling：简单但延迟和负载差。

## Guardrail

当 Coding Agent 需要实时双向 terminal/approval 时再评估 WebSocket；Run/Event contract 不依赖传输协议。
