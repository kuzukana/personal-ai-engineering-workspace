# Personal AI Engineering Workspace — Deployment Specification

**Version:** 0.1  
**Status:** Local/CI baseline implemented  
**Last Updated:** 2026-09-29

# 1. V0.1 Topology

```text
Browser
  ↓
Next.js
  ↓
FastAPI
  ├── PostgreSQL
  ├── optional model providers
  ├── optional Brave Search
  └── optional GitHub API
```

Redis is included in Docker Compose for the future runtime/cache/worker path. Long-lived V0.1 business facts are stored in PostgreSQL.

# 2. Local Infrastructure

From repository root:

```bash
docker compose up -d postgres redis
```

Services:
- PostgreSQL 17;
- Redis 7.

PostgreSQL data uses the `postgres_data` Docker volume.

# 3. Backend Environment

Backend settings load from `backend/.env` when the application is started from `backend/`.

Copy:

```bash
cp .env.example backend/.env
```

Production/remote secrets must use a deployment secret store rather than files baked into images.

# 4. Database Migration

V0.1 uses Alembic.

Development:

```bash
cd backend
uv run --no-sync alembic upgrade head
```

Current migrations include:
- core schema;
- built-in Mock Model / Research Agent seed;
- Knowledge↔Technology relation.

No manual schema drift should be introduced outside migrations.

# 5. Backend Start

```bash
cd backend
uv sync --locked --extra dev
uv run --no-sync uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Development may add `--reload`.

# 6. Frontend Start

```bash
cd frontend
npm ci
npm run dev
```

Default frontend expects:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

# 7. Health

- `/health` — process liveness;
- `/ready` — database readiness with a two-second deadline; 503 when unavailable. Redis is optional.

# 8. CI

Every push/PR to main runs:
- backend install;
- Ruff;
- Pytest;
- Alembic migration;
- API end-to-end smoke;
- frontend typecheck;
- frontend production build.

The API smoke starts Uvicorn against migrated PostgreSQL and exercises the core product loop.

# 9. External Provider Configuration

V0.1 can operate fully with mocks.

Optional live integrations:
- OpenAI-compatible model providers;
- Brave Search;
- GitHub API token.

External credentials are intentionally not required by ordinary CI.

# 10. Security Boundaries

- Provider/API secrets are backend-only.
- `.env` is not committed.
- URL Fetch performs SSRF checks.
- PostgreSQL should not be internet-exposed in remote deployment.
- Remote deployment must use TLS.
- V0.1 has no authentication and therefore should be treated as local/single-user unless protected externally.

# 11. Background Execution

V0.1 Research uses FastAPI in-process background tasks.

The Run/Event contract is intentionally independent of this choice so a future queue/worker implementation can preserve API semantics.

# 12. Remote Deployment Preconditions

Before a production-like remote deployment, add:
- authentication / authorization;
- TLS termination;
- secret store;
- database backup/restore verification;
- rate limiting;
- monitoring;
- retention policy;
- worker/queue strategy for long-running Runs;
- explicit allowed origins;
- deployment rollback procedure.

# 13. Rollback

Application rollback and database rollback are separate concerns.

Future destructive migrations should follow expand → migrate → contract rather than assuming every downgrade is safe.

# 14. Final Principle

> Deployment should reproduce the same product contracts across environments while keeping secrets, data and runtime state explicitly separated.


## V0.1 repair operations (2026-10-04)

- Local Compose publishes PostgreSQL and Redis only on 127.0.0.1. Apply port changes with `docker compose up -d --wait postgres redis`; named PostgreSQL data is retained. Do not use `down -v` for this change.
- Migration `0004_knowledge_source_unique` prevents duplicate Knowledge promotion. It refuses existing duplicate source groups rather than deleting records. Reconcile duplicates explicitly if its preflight fails.
- ORM timestamp defaults now use aware UTC. Existing naive-default records are not automatically shifted: identify the writer timezone and affected records (for example, by comparing Run creation with event times), back up data and scope any historical correction. Rows written in UTC environments must not receive an unconditional +8-hour shift.
- A single local API process remains the supported execution topology. Persisted SSE/cancellation and serialized event sequences improve recovery, but there is still no durable queue or automatic resumption after process death.
- The review fixes were checked without paid model/search calls. Configure context limits for live providers before enabling them; real-provider behavior needs a separate opt-in smoke.
