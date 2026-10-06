# Personal AI Engineering Workspace — Roadmap

**Version:** 0.2 (first slice)
**Status:** V0.1 accepted in PR #2; V0.2 retrieval slice implemented
**Last Updated:** 2026-10-06

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

**Status: Complete.**

Implemented documentation includes PRD, Technical Design, Architecture, AI System Spec, Model Spec, Agent Spec, Evaluation, Data/API/Event contracts, Security, Observability, Test Plan, Deployment and ADRs.

## Phase 1 — Application Foundation

**Status: Complete.**

Implemented:
- FastAPI application;
- Next.js application;
- PostgreSQL development infrastructure;
- Redis development service;
- settings / health / readiness;
- Docker Compose;
- GitHub Actions CI.

Verified by CI:
- backend lint;
- backend tests;
- Alembic migration from clean PostgreSQL;
- frontend typecheck;
- frontend production build.

## Phase 2 — Model Gateway

**Status: Complete for V0.1.**

Implemented:
- ProviderAdapter contract;
- ModelRegistry;
- MockProvider;
- OpenAI-compatible HTTP adapter;
- configurable OpenAI / DeepSeek / Kimi registrations;
- normalized ModelRequest / ModelResponse / ModelEvent;
- streaming / usage normalization;
- model list API.

Native Anthropic adapter remains future work; V0.1 does not claim native Anthropic support.

## Phase 3 — Run / Event Infrastructure

**Status: Complete.**

Implemented:
- Run persistence;
- Event publisher;
- monotonic per-Run sequence;
- persisted RunEvent history;
- SSE endpoint;
- Last-Event-ID / after_sequence direction;
- cancellation request;
- terminal Run states.

## Phase 4 — Research Agent

**Status: Complete.**

Workflow:

```text
Understand
→ Plan Search
→ Search
→ Select Sources
→ Read Sources
→ Extract Findings
→ Verify
→ Synthesize
```

Implemented:
- LangGraph runtime;
- Mock model and tools for deterministic development;
- structured ResearchReport;
- source provenance;
- conservative PARTIALLY_VERIFIED / UNVERIFIED handling;
- deterministic post-run evaluation;
- live Research UI.

## Phase 5 — Real Research Tools

**Status: Complete for implementation.**

Implemented:
- Brave Web Search adapter;
- `fetch_url` with scheme validation, DNS/IP validation, private-network blocking, redirect revalidation and response-size limits;
- GitHub repository metadata + README tool;
- tool configuration through backend environment variables.

When `BRAVE_SEARCH_API_KEY` is absent, Research automatically uses deterministic Mock Search / Mock Fetch.

A paid/external real-provider smoke is intentionally not part of ordinary CI.

## Phase 6 — Knowledge

**Status: Complete.**

Implemented:
- save Research to Knowledge;
- idempotent promotion by source Research;
- list / detail / search;
- Markdown knowledge rendering;
- source links;
- Knowledge ↔ Technology relation table;
- automatic matching against already-known Technologies;
- manual Knowledge ↔ Technology linking API;
- Knowledge frontend list/detail.

## Phase 7 — Capability + Evidence

**Status: Complete.**

Implemented:
- Technology create / read / update / delete APIs;
- Capability level 0–5 upsert;
- reason / next target / next action;
- Evidence create / read / update / delete APIs;
- CapabilityEvidence relation;
- evidence listing by Capability;
- Capability + Evidence frontend workspace.

## Phase 8 — Agent Lab

**Status: Complete.**

Implemented:
- Run list;
- Run detail;
- persisted timeline;
- model call count;
- tool call count;
- Token aggregation;
- latency;
- estimated cost when available;
- evaluation results;
- errors;
- Agent Lab frontend.

# 4. V0.1 System Acceptance

The 2026-10-04 review findings have been repaired and verified locally. See [Test Plan, section 12](../04-quality/TEST_PLAN.md#12-v01-acceptance-follow-ups-2026-10-04) for regression evidence and external-provider/remote-CI limits.

GitHub Actions executes:

```text
lint
→ unit / contract tests
→ Alembic migration
→ start FastAPI
→ create Research Run
→ wait for completion
→ inspect Research result
→ inspect Event history
→ inspect Evaluation
→ promote Knowledge
→ create/update Technology
→ create/update Evidence
→ update Capability
→ link Evidence
→ verify relations
→ delete CRUD test entities
→ frontend typecheck/build
```

This deterministic path uses Mock Model / Mock Research Tools and therefore does not require paid external APIs.

# 5. Known V0.1 Boundaries

Still intentionally deferred:
- authentication / multi-user authorization;
- remote production deployment hardening;
- semantic retrieval / vector search;
- Learning Agent;
- Engineering Journal;
- Coding Agent;
- shell/filesystem write tools;
- high-risk approval workflow;
- multi-agent orchestration;
- full experiment/benchmark UI;
- LLM-as-a-Judge;
- queue/worker execution;
- automatic GitHub-tool routing inside Research.

# 6. V0.2 — Learning Loop

First slice implemented: versioned Knowledge chunking, deterministic local embedding demo,
configurable HTTP embedding adapter, exact cosine retrieval, citation context budget and
`/retrieval` UI. Content edits invalidate old results; indexing failures preserve prior indexes.
The default demo validates plumbing, not real semantic relevance. See TEST_PLAN section 13.

Remaining acceptance work:
- opt-in live embedding quality evaluation on representative personal queries;
- scalable vector backend when local exact-search limits are reached;
- Learning Agent;
- Engineering Journal;
- incident knowledge;
- practice / evidence suggestions;
- capability-gap workflow;
- richer Knowledge ↔ Technology extraction.

# 7. V0.3 — Build Loop

Planned:
- Coding Agent;
- repository tools inside Coding workflow;
- filesystem / terminal sandbox;
- tests as tools;
- high-risk Human Approval;
- deeper GitHub integration.

# 8. V0.4 — AI Engineering Lab

Planned:
- experiments;
- benchmark datasets;
- model comparison;
- prompt comparison;
- agent-version comparison;
- LLM-as-a-Judge;
- failure taxonomy;
- replay / debugging experiments if real usage justifies them.

# 9. V1.0 Target

Product loop:

```text
Capture → Research → Learn → Build → Evidence → Reflect → Improve
```

AI engineering loop:

```text
Task → Agent → Run → Trace → Evaluate → Experiment → Improve
```

# 10. Release Rule

A phase is complete only when its acceptance path runs, tests exist and the resulting behavior is inspectable. Documentation alone does not count as implementation.
