# Personal AI Engineering Workspace — API Specification

**Document Type:** Implemented API Contract  
**Version:** 0.1  
**Status:** Implemented V0.1  
**Last Updated:** 2026-09-29

# 1. Purpose

This document describes the HTTP/SSE contract that is implemented by the current V0.1 code.

Base path for product APIs:

```text
/api/v1
```

Health endpoints remain top-level.

FastAPI OpenAPI at `/docs` is the machine-readable source of truth. This file documents product semantics and lifecycle expectations.

# 2. Response Conventions

Most successful endpoints return:

```json
{"data": {}}
```

Lists return:

```json
{"data": []}
```

Some creation endpoints also include `meta`.

V0.1 still uses FastAPI's normal `{"detail": ...}` error responses. A project-wide structured error envelope remains future work.

# 3. Health

## GET /health

Returns process liveness.

## GET /ready

Returns dependency readiness information.

# 4. Models

## GET /api/v1/models

Returns models currently registered in the in-process Model Registry.

The Mock Model is always present. Real models appear only when the corresponding key/model/base-url configuration is available.

# 5. Research

## POST /api/v1/research

Request:

```json
{
  "query": "Compare LangGraph and PydanticAI.",
  "model_id": "uuid"
}
```

Response: `202 Accepted`

```json
{
  "data": {
    "run_id": "uuid",
    "status": "PENDING",
    "events_url": "/api/v1/runs/{run_id}/events"
  }
}
```

Execution continues in a FastAPI background task.

## GET /api/v1/research/{run_id}

Returns the persisted ResearchItem for a completed Run.

# 6. Runs

## GET /api/v1/runs

Query:
- `limit`
- `offset`
- `status`

Returns newest Runs first.

## GET /api/v1/runs/{run_id}

Returns:
- status;
- task type;
- model ID;
- input / output;
- structured output;
- latency;
- input/output/reasoning tokens;
- estimated cost and currency when available;
- error code/message;
- timestamps.

## POST /api/v1/runs/{run_id}/cancel

Returns `202` with `CANCELLATION_REQUESTED`.

Cancellation remains cooperative: it does not interrupt an in-flight HTTP call. The request is persisted as `CANCELLATION_REQUESTED` and checked at workflow boundaries and finalization. Cancellation and final commit lock the same Run row: cancellation committed first prevents successful result publication; finalization committed first makes cancellation return 409. A completed Research result, Run terminal status and terminal event are committed together. Evaluation execution failure emits `evaluation.failed` and fails the Run without publishing a Research result.

# 7. Run Events

## GET /api/v1/runs/{run_id}/events/history

Returns persisted events ordered by sequence.

Query:
- `after_sequence`

## GET /api/v1/runs/{run_id}/events

Content-Type:

```text
text/event-stream
```

Supports:
- `Last-Event-ID`;
- `after_sequence`.

Unknown Runs return 404 before streaming. Events are read from PostgreSQL, with one-second polling/heartbeats and no open DB session while waiting on the client. A terminal Run with no remaining events closes immediately; reconnect does not depend on an in-process broker.

Terminal event types:
- `run.completed`
- `run.failed`
- `run.cancelled`

# 8. Evaluation

## GET /api/v1/runs/{run_id}/evaluations

Returns persisted deterministic EvaluationResult rows.

V0.1 does not expose a public "run evaluator now" mutation endpoint.

# 9. Knowledge

## POST /api/v1/knowledge/from-research/{run_id}

Promotes a completed ResearchItem into Knowledge.

Behavior:
- idempotent by `source_research_id`;
- generates Markdown;
- preserves query/run metadata;
- automatically links Technologies whose names occur in the saved research content.

## GET /api/v1/knowledge

Query:
- `limit`
- `offset`
- `q`

Search checks title, summary and Markdown content.

## GET /api/v1/knowledge/{knowledge_id}

Returns Knowledge plus linked Technologies.

## POST /api/v1/knowledge/{knowledge_id}/technologies/{technology_id}

Manually links Knowledge and Technology.

# 10. Capability Workspace

All Technology, Capability and Evidence endpoints live under:

```text
/api/v1/capabilities
```

## GET /api/v1/capabilities

Returns each Technology with its optional Capability.

## POST /api/v1/capabilities/technologies

Creates a Technology.

## GET /api/v1/capabilities/technologies/{technology_id}

Returns Technology + optional Capability.

## PATCH /api/v1/capabilities/technologies/{technology_id}

Updates Technology metadata/name.

## DELETE /api/v1/capabilities/technologies/{technology_id}

Deletes the Technology and removes its capability/relationship rows.

## PUT /api/v1/capabilities/technologies/{technology_id}

Upserts Capability for that Technology.

Request:

```json
{
  "level": 2,
  "reason": "Can run and modify workflows.",
  "next_target_level": 3,
  "next_action": "Implement a real integration."
}
```

Level and next target must be 0–5.

# 11. Evidence

## GET /api/v1/capabilities/evidences

Lists Evidence.

## POST /api/v1/capabilities/evidences

Creates Evidence.

## GET /api/v1/capabilities/evidences/{evidence_id}

Returns one Evidence.

## PATCH /api/v1/capabilities/evidences/{evidence_id}

Updates Evidence.

## DELETE /api/v1/capabilities/evidences/{evidence_id}

Deletes Evidence and removes CapabilityEvidence links.

## GET /api/v1/capabilities/{capability_id}/evidences

Lists Evidence linked to a Capability.

## POST /api/v1/capabilities/{capability_id}/evidences/{evidence_id}

Creates the CapabilityEvidence relation. Repeated linking is tolerated.

# 12. Model / Tool Configuration

Provider secrets are not exposed through HTTP APIs.

Backend environment variables configure:
- model provider keys/model names/base URLs;
- Brave Search;
- optional GitHub token.

The frontend never receives Provider secrets.

# 13. Research Tool Contract

The V0.1 Research workflow uses:

```text
web_search
fetch_url
```

If `BRAVE_SEARCH_API_KEY` is configured:
- `web_search` uses Brave Search;
- `fetch_url` uses the SSRF-protected HTTP implementation.

Otherwise both are deterministic mocks.

The Tool Gateway also registers:

```text
github_repository
```

but automatic workflow routing to that tool is deferred.

# 14. HTTP Statuses Used

Common statuses:

```text
200 OK
201 Created
202 Accepted
204 No Content
404 Not Found
409 Conflict
422 Validation Error
5xx runtime/provider/infrastructure failure
```

# 15. Security Contract

- Browser does not receive Provider secrets.
- External URLs are untrusted.
- Live URL fetching only allows public HTTP(S) destinations.
- Redirect destinations are revalidated.
- Research Agent V0.1 only uses LOW-risk tools.
- High-risk mutations are not part of the V0.1 Agent toolset.

# 16. V0.1 Acceptance

The CI end-to-end smoke verifies:
- model discovery;
- Research creation;
- Run completion;
- persisted Events;
- deterministic Evaluation;
- Token/Cost persistence;
- Knowledge promotion;
- Knowledge↔Technology relation;
- Technology CRUD;
- Capability upsert;
- Evidence CRUD;
- Capability↔Evidence relation.

# 17. Future Contract Work

Planned:
- stable structured error envelope;
- authentication / authorization;
- idempotency keys on more mutations;
- cursor pagination;
- public experiment/benchmark APIs;
- approval APIs;
- provider administration APIs;
- versioned semantic Knowledge search.
