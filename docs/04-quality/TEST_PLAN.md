# Personal AI Engineering Workspace — Test Plan

**Version:** 0.1  
**Status:** Implemented for V0.1 baseline  
**Last Updated:** 2026-09-29

# 1. Principle

Deterministic engineering remains deterministic. AI nondeterminism must not make ordinary CI flaky.

# 2. Current CI Gates

Backend:
- editable install with dev dependencies;
- Ruff;
- Pytest;
- Alembic upgrade from clean PostgreSQL;
- start FastAPI;
- end-to-end HTTP smoke.

Frontend:
- npm install;
- TypeScript typecheck;
- Next.js production build.

# 3. Current Unit / Contract Coverage

Implemented tests cover:
- health endpoints;
- model registry API;
- ORM table registration;
- Model Gateway generate/stream normalization;
- OpenAI-compatible adapter normalization;
- Research report schemas;
- Tool Gateway allowlist;
- Mock Search / Fetch;
- Brave Search response normalization;
- GitHub repository response normalization;
- URL-fetch SSRF checks;
- Run cancellation control;
- event broker;
- capability level validation;
- Knowledge Markdown rendering;
- Run serialization / Agent Lab metrics.

# 4. Deterministic End-to-End Smoke

After Alembic migration, CI starts the real FastAPI application and verifies:

```text
GET models
→ POST research
→ wait for terminal Run
→ GET Research
→ GET Evaluations
→ GET Event history
→ assert required runtime events
→ assert Token/Cost persistence
→ create Technology
→ save Research as Knowledge
→ verify Knowledge↔Technology
→ update Technology
→ upsert Capability
→ create/update Evidence
→ link Capability↔Evidence
→ verify linked Evidence
→ delete Evidence
→ delete Technology
```

The workflow uses Mock Model + Mock Research Tools and therefore does not call paid external APIs.

# 5. Real Provider Tests

Real model/search tests remain separate from ordinary CI because they:
- require secrets;
- cost money;
- can fail because of external availability;
- are nondeterministic.

When credentials are available, they should be run as a manual/secret-backed smoke rather than replacing deterministic CI.

# 6. Security Tests

Current automated checks include:
- unsupported Tool rejection;
- non-http(s) URL rejection;
- localhost/private/link-local URL rejection;
- redirect revalidation;
- public URL acceptance;
- Provider tests use fake credentials and MockTransport.

# 7. Evaluation Tests

Deterministic Research evaluation remains code-driven.

Current runtime evaluation checks include:
- ResearchReport schema existence by construction;
- title present;
- summary present;
- source present.

Future additions:
- citation coverage;
- verification coverage;
- source-quality scoring;
- LLM-as-a-Judge.

# 8. Frontend Verification

Current CI verifies:
- all TypeScript surfaces compile;
- all pages and routes included in the Next.js application production build.

Future:
- component tests;
- EventSource reducer tests;
- browser E2E with Playwright.

# 9. Regression Strategy

Real failures should become deterministic fixtures whenever possible.

Priority regression classes:
- Provider normalization;
- schema validation;
- Run state transitions;
- Event ordering;
- cancellation;
- SSRF;
- Knowledge promotion;
- Capability/Evidence relations;
- migrations.

# 10. Known Gaps

Not yet implemented as CI gates:
- Python static typing beyond runtime/Pydantic and Ruff;
- frontend component/unit test runner;
- secret scanner;
- dependency audit gate;
- Playwright;
- live provider smoke;
- failure-injection matrix for every workflow node;
- performance/load tests.

These are explicit future quality improvements rather than silently assumed V0.1 coverage.

# 11. Final Principle

> Make deterministic engineering deterministic; isolate AI nondeterminism instead of letting it infect the test suite.
