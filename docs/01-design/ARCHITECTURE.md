# Personal AI Engineering Workspace — Architecture Overview

**Version:** 0.1  
**Status:** Draft  
**Last Updated:** 2026-09-29

# 1. Context

The workspace is a personal, AI-native full-stack application. Workspace Mode completes real tasks; Lab Mode exposes how AI completed them.

# 2. System Diagram

Browser
→ Next.js
→ REST / SSE
→ FastAPI
→ Workspace Services / Agent Runtime / Lab Services
→ Model Gateway / Tool Gateway / Evaluation Engine
→ PostgreSQL + Redis
→ External Model Providers / Search / GitHub / future MCP.

# 3. Frontend Boundary

Next.js owns presentation, navigation, user interaction, API calls and SSE consumption. It never holds model-provider secrets and never orchestrates Agent workflows.

# 4. Backend Boundary

FastAPI owns validation, services, agent runtime, providers, tools, persistence, security boundaries and event publication.

Layers:

API → Services → Domain/Agent → Infrastructure → Persistence/External APIs.

# 5. AI Boundary

Agent code depends on internal Model Gateway and Tool Gateway contracts, never vendor SDKs directly.

AgentSpec → Runtime Adapter → Workflow → Model Gateway / Tool Gateway → normalized events.

# 6. Data Boundary

PostgreSQL is the system of record for long-lived structured data. Redis is short-lived runtime/event/cache infrastructure. Redis is not the business source of truth.

# 7. Execution Model

A user task creates a Run. A Run emits ordered Events and can produce ToolCalls, Research artifacts and EvaluationResults. Run completion and task quality are separate concepts.

# 8. Event Model

All meaningful runtime transitions use the normalized EVENT_SPEC. Provider-native streaming events are translated before reaching clients.

# 9. Research Flow

User query → ResearchService → Run → ResearchAgent → ModelGateway + Tools → Structured Report → Evaluation → ResearchItem → optional Knowledge save.

# 10. Knowledge / Capability Flow

Research → Knowledge → Technology → Capability ↔ Evidence.

The system tracks not only what the user read, but what the user can demonstrably build/debug/explain.

# 11. Security Boundary

External content is untrusted. Secrets remain backend-only. Agents use explicit tool allowlists and least privilege. High-risk actions require future Human Approval.

# 12. Deployment

Development: local Next.js/FastAPI plus Docker PostgreSQL/Redis.

Future: containerized frontend/backend, worker process for long Runs, managed database/Redis, TLS/authentication/secret store.

# 13. Scaling Path

V0.1 begins as a single-user application. Long-running Agent execution is designed around Run IDs and Events so it can later move from in-process background tasks to queue/worker execution without changing the product contract.

# 14. Replaceability

Replaceable implementations include Model Provider, Agent Runtime, Search Provider, Embedding Model, Tool implementation and future vector strategy.

Stable contracts include ModelRequest/Response, AgentSpec, Tool contract, Event envelope, Run and Evaluation semantics.

# 15. Architecture Rule

> Stable contracts, replaceable implementations.
