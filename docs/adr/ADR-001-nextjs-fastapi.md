# ADR-001 — Next.js + FastAPI

**Status:** Accepted  
**Date:** 2026-09-29

## Context

项目需要现代全栈 UI、SSE 交互，同时 AI/ML/Agent 生态以 Python 为主。

## Decision

Frontend 使用 Next.js + React + TypeScript；Backend 使用 FastAPI + Python + Pydantic。

## Consequences

优点：前端生态成熟；AI Python 生态直接可用；API 边界清晰；可独立测试和部署。

代价：双语言栈；需要维护 API contract；开发环境比单体框架略复杂。

## Alternatives

全 TypeScript：AI Python 集成成本更高。全 Python UI：前端产品能力较弱。Next.js API Routes only：不利于 Python Agent 生态。

## Guardrail

Frontend 不直接调用 Model Provider；所有 AI 能力经过 FastAPI。
