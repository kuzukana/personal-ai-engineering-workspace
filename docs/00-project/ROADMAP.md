# Personal AI Engineering Workspace — Roadmap

**Version:** 0.1  
**Status:** Active  
**Last Updated:** 2026-09-29

# 1. Goal

Build a personal AI-native engineering workspace in vertical slices. Every phase must produce something usable, observable and testable.

# 2. Delivery Principles

- Finish one end-to-end loop before expanding scope.
- Prefer one observable Agent before multi-agent complexity.
- Every meaningful AI behavior must be traceable and evaluatable.
- Mock first, real providers second.
- Contracts before implementation details.
- Real personal utility is the final product signal.

# 3. V0.1 — Research Loop

## Phase 0 — Product / Architecture

Status: Complete.

Deliverables: PRD, Technical Design, AI System Spec, Model Spec, Agent Spec, Evaluation, Data/API/Event contracts, Security, Observability, Test Plan, Deployment, ADRs.

## Phase 1 — Application Foundation

Status: In progress.

Deliverables:
- FastAPI application;
- Next.js application;
- PostgreSQL + Redis development infrastructure;
- settings / health / readiness;
- CI baseline.

Exit: frontend and backend build; backend tests pass; database migration works.

## Phase 2 — Model Gateway

Deliverables:
- ProviderAdapter contract;
- ModelRegistry;
- MockProvider;
- OpenAI-compatible adapter;
- Anthropic adapter direction;
- normalized usage/error/streaming;
- model list API.

Exit: same ModelRequest can run through at least Mock + one configured real provider without Agent code changes.

## Phase 3 — Run / Event Infrastructure

Deliverables:
- Run repository/service;
- Event publisher;
- monotonic run sequence;
- SSE endpoint;
- cancellation;
- persisted trace.

Exit: frontend can observe a streamed mock Run and reconstruct timeline from persisted events.

## Phase 4 — Research Agent

Deliverables:
- LangGraph runtime adapter;
- Understand → Plan → Search → Read → Verify → Synthesize;
- Mock search/fetch tools;
- structured ResearchReport;
- deterministic evaluation.

Exit: a complete research task runs end to end with mocks and produces trace + evaluation.

## Phase 5 — Real Research Tools

Deliverables:
- web search provider adapter;
- fetch_url with SSRF protection;
- GitHub repository research tool;
- source provenance.

Exit: real technical research can use live sources without changing Agent workflow.

## Phase 6 — Knowledge

Deliverables:
- save Research to Knowledge;
- list/detail/search;
- source links;
- technology extraction/relations.

Exit: past research can be retrieved and reused.

## Phase 7 — Capability + Evidence

Deliverables:
- Technology CRUD;
- Capability level 0–5;
- Evidence CRUD;
- CapabilityEvidence relations.

Exit: project work can become explicit evidence for skills.

## Phase 8 — Agent Lab

Deliverables:
- Run list/detail;
- timeline;
- model/tool/evaluation metrics;
- errors and costs.

Exit: every Research Run can be inspected without reading backend logs.

# 4. V0.2 — Learning Loop

Planned:
- semantic retrieval;
- Learning Agent;
- Engineering Journal;
- incident knowledge;
- practice / evidence suggestions;
- capability-gap workflow.

# 5. V0.3 — Build Loop

Planned:
- Coding Agent;
- repository tools;
- filesystem / terminal sandbox;
- tests as tools;
- high-risk Human Approval;
- GitHub integration.

# 6. V0.4 — AI Engineering Lab

Planned:
- experiments;
- benchmark datasets;
- model comparison;
- prompt comparison;
- agent-version comparison;
- LLM-as-a-Judge;
- failure taxonomy.

# 7. V1.0

Target loop:

Capture → Research → Learn → Build → Evidence → Reflect → Improve.

AI loop:

Task → Agent → Run → Trace → Evaluate → Experiment → Improve.

# 8. Explicitly Deferred

Until real usage proves need: multi-agent orchestration, autonomous long-term memory, agent replay, visual workflow builder, marketplace, team collaboration, billing and mobile app.

# 9. Release Rule

A phase is complete only when its acceptance path runs, tests exist, and the resulting behavior is inspectable. Documentation alone does not count as implementation.
