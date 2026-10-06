# Personal AI Engineering Workspace — Test Plan

**Version:** 0.1  
**Status:** Implemented for V0.1 baseline  
**Last Updated:** 2026-10-04

# 1. Principle

Deterministic engineering remains deterministic. AI nondeterminism must not make ordinary CI flaky.

# 2. Current CI Gates

Backend:
- `uv sync --locked --extra dev` on Python 3.12 and 3.14;
- Ruff;
- Pytest;
- Alembic upgrade from clean PostgreSQL;
- start FastAPI;
- end-to-end HTTP smoke.

Frontend:
- `npm ci`;
- TypeScript typecheck;
- Next.js production build;
- Playwright browser regression tests.

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
- Research Agent tool/model/step failure event tracing.

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

Playwright currently covers Research lifecycle/old-response isolation and save target, Knowledge search races and safe Markdown, and mutation error/retry behavior. API responses are mocked for deterministic UI testing. Component-level coverage remains future work.

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
- live provider smoke;
- failure-injection matrix for every workflow node;
- performance/load tests.

These are explicit future quality improvements rather than silently assumed V0.1 coverage.

# 11. Final Principle

> Make deterministic engineering deterministic; isolate AI nondeterminism instead of letting it infect the test suite.

# 12. V0.1 Acceptance Follow-ups (2026-10-04)

The earlier review at `2f82247` identified real defects despite passing baseline tests. The findings below were merged in PR #2 (main commit 60e3afc); this maintained checklist replaces the standalone dated review file. GitHub Actions run 37400491661 passed both backend matrices and frontend.

| IDs | Repair | Regression evidence |
| --- | --- | --- |
| V01-01 | Aware UTC ORM defaults; no blanket historical data rewrite. | UTC assertion and real PostgreSQL creation-time checks. |
| V01-02 | Display title capped at 240 characters; complete query retained. | Agent and DB persistence for 230, 231 and 10,000 characters. |
| V01-03 | Validated IP is the actual HTTP target; preserve Host/TLS name, disable ambient proxies, recheck redirects, reject non-global and credential URLs. | DNS-rebinding simulation checks one resolution and numeric target/SNI; redirect change to private address rejected. |
| V01-04, V01-14 | Compose and local API instructions bind loopback. | Actual Compose PostgreSQL/Redis bindings checked after recreation; data volume retained. |
| V01-05 | Persist cancellation and serialize it with final commit via the Run row lock. | Cancellation during evaluation prevents a result; final-commit winner returns 409 to late cancellation. |
| V01-06 | Source uniqueness migration plus serialized promotion; only completed Runs/results may be promoted. | Six simultaneous saves yield one Knowledge ID and exactly one created result. |
| V01-07 | SSE validates Run, reads durable status/events, sends heartbeats and closes exhausted terminal replay. | Unknown Run 404, terminal cursor exhaustion, and active-stream recovery from persisted terminal event. |
| V01-08, V01-09 | System-level trust instructions, separate external JSON, bounded excerpts, conservative byte/token budget and explicit output budget; live model limits configurable. | Adversarial/large Unicode and escaped text under 2048/8192/32768 contexts; oversized task rejected. No real-model attack claim. |
| V01-10 | Bounded database readiness probe; 503 on failure, Redis optional. | Healthy/down dependency tests and local readiness check. |
| V01-11 | Explicit Run response schema including currency, error_message and reasoning_tokens. | Serialization contract and HTTP smoke. |
| V01-12 | Error feedback, pending states and duplicate-submission guards for capability/technology/evidence writes. | Browser 409/retry test. |
| V01-13, V01-16 | Research generation guards, lifecycle updates, cancellation UI and fallback polling; save target must match displayed report. | Browser delayed-old-result test, RUNNING display and correct save target. |
| V01-15 | Publish Research only with successful final Run/event transaction; trace evaluator exceptions. | Injected evaluation failure leaves FAILED Run, no Research result and evaluation.failed event. |
| V01-17 | Knowledge search ignores superseded async responses. | Browser out-of-order search regression. |

Additional repairs: safe Markdown rendering with HTML disabled; Knowledge/Run pagination controls; batched Knowledge relations instead of N+1; concurrency control for initial model registration, capability upsert and relation linking; serialized event-sequence allocation. Concurrent database tests cover registration, evidence linking and eight event publishers. Dependency locks are included for both runtimes, and CI installs them strictly.

## Verification

- Python 3.12 and 3.14: 55 tests passed, including PostgreSQL regressions; Ruff passed. Tests use isolated disposable databases. The previous asyncio deprecation warnings are gone after the test dependency update.
- Clean database upgrade to 0004, downgrade to 0003 and upgrade again passed; Alembic check found no model/schema difference.
- Full HTTP Mock Research → events/evaluation → Knowledge → Technology/Capability/Evidence smoke passed on both Python versions.
- Frontend clean `npm ci`, type generation/check, production build and three Playwright browser tests passed. Local browser tests use installed Chrome because the bundled browser download timed out; CI installs Chromium.
- Business database upgraded to 0004 without deleting/merging rows. Existing timestamps were not automatically rewritten.
- No paid provider calls or live SSRF penetration tests were performed. Remote GitHub Actions passed for PR #2. Prompt separation reduces risk; it does not prove immunity to prompt injection or validate factual answer quality.

## Reproduction and remaining scope

Run ordinary unit tests with `uv run --no-sync pytest -q`; PostgreSQL tests skip unless `TEST_DATABASE_URL` points to an explicitly disposable, migrated database. These tests create data. Never point that variable at a personal/business database. CI uses its throwaway PostgreSQL service.

Use `npm ci`, `npm run typecheck`, `npm run build`, `npx playwright install chromium`, then `npm run test:e2e`. `PLAYWRIGHT_CHANNEL=chrome` can select an installed Chrome for local testing.

Python 3.12 is the default; 3.12–3.14 are supported, with 3.12 and 3.14 tested locally and configured in CI. Locks make installed dependency versions reproducible; platform wheels and Python compatibility markers may differ.

V0.1 remains a local, single-user background-task application. Authentication, durable queue/restart recovery, factual verification, semantic retrieval and agents for later phases remain explicitly outside this repair. Historical timestamp corrections require a separately scoped data audit, not an unconditional shift.


# 13. V0.2 retrieval acceptance

Regression coverage: source chunk offsets (including Unicode), vector count/dimensions/finite
values, response ordering/normalization, UTF-8 citation budget, concurrent indexing idempotency,
provider failure preservation, stale-content exclusion, edits during provider execution, atomic
refresh, profile isolation and exact citation offsets. Browser coverage verifies delayed old
search responses cannot replace new results, citation navigation, index failure and retry.
The HTTP smoke extends Research → Knowledge with index → search → citation.

`test_demo_retrieval_evaluation` uses three fixed documents and three lexical queries with
expected Recall@1=1 and MRR=1. This is a deterministic plumbing regression, not evidence of
semantic relevance, factual correctness or provider-model quality. A representative user corpus
and opt-in live provider evaluation remain necessary before semantic quality acceptance.

Migration 0005 is checked against models and exercised upgrade/downgrade/upgrade on disposable
PostgreSQL. Never use TEST_DATABASE_URL against business data. No paid embedding calls are
required by CI. Production limitations and indexing cost behavior are documented in README.


First-slice CI run 37401978295 passed: Python 3.12/3.14, 75 backend tests,
Ruff, migration consistency, HTTP smoke, frontend build/typecheck and four browser tests.
Local Windows connection diagnosis measured localhost at about 2.1 seconds versus IPv4
loopback at about 0.03 seconds; database defaults now match the Compose IPv4 binding.
The UTC regression checks creation-time bounds instead of depending on total task duration.
