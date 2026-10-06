# Personal AI Engineering Workspace

An AI-native workspace for turning real research, learning and engineering work into reusable knowledge, verifiable capability and inspectable evidence.

## Current stage

**V0.1 — Research Loop implemented.**

The current vertical slice supports:

- Next.js / React / TypeScript frontend;
- FastAPI / Python backend;
- PostgreSQL persistence and Alembic migrations;
- Model Gateway with a deterministic Mock Provider plus configurable OpenAI-compatible providers;
- LangGraph Research Agent;
- normalized Run / Agent / Model / Tool / Evaluation events;
- SSE live Research timeline;
- Brave Search adapter and SSRF-protected URL fetching when configured;
- GitHub repository inspection tool in the Tool Gateway;
- deterministic Research evaluation;
- Research → Knowledge promotion;
- Knowledge ↔ Technology relations;
- Technology / Capability / Evidence tracking;
- Agent Lab Run inspection;
- CI lint, tests, migration, frontend build and end-to-end smoke.

Core loop:

```text
Research Task
    ↓
Research Agent
    ↓
Search / Read / Verify / Synthesize
    ↓
Run Events + Evaluation
    ↓
Knowledge
    ↓
Technology / Capability / Evidence
    ↓
Agent Lab inspection
```

## Architecture

```text
Browser
  ↓
Next.js
  ↓ REST / SSE
FastAPI
  ├── Research Service
  ├── Agent Runtime
  ├── Model Gateway
  ├── Tool Gateway
  ├── Evaluation
  └── Knowledge / Capability APIs
        ↓
   PostgreSQL
```

Redis is present in the development topology for future runtime/cache/worker use, but V0.1 business state does not depend on Redis.

See:

- `docs/00-project/PRD.md`
- `docs/00-project/ROADMAP.md`
- `docs/01-design/TECHNICAL_DESIGN.md`
- `docs/03-contracts/API_SPEC.md`

## Local development

### 1. Start infrastructure

From the repository root:

```bash
docker compose up -d postgres redis
```

### 2. Configure backend environment

Copy the root example file into the backend working directory:

```bash
cp .env.example backend/.env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example backend/.env
```

You can leave all external-provider keys empty. In that case the application runs with deterministic Mock Model / Mock Research Tools.

For live web research, configure:

```text
BRAVE_SEARCH_API_KEY=
```

For a real model, configure a provider key plus its model name. Example:

```text
OPENAI_API_KEY=
OPENAI_MODEL=
```

DeepSeek and Kimi can also be configured through the OpenAI-compatible adapter using their model and base URL environment variables.

### 3. Backend

```bash
cd backend
uv sync --locked --extra dev
uv run --no-sync alembic upgrade head
uv run --no-sync uvicorn app.main:app --host 127.0.0.1 --reload
```

API:

```text
http://localhost:8000
```

OpenAPI:

```text
http://localhost:8000/docs
```

Python 3.12 is the default development version; 3.12–3.14 are supported, with 3.12 and 3.14 in CI. To use an installed 3.14, add `--python 3.14` to `uv sync` and `uv run`. Commit `backend/uv.lock` and `frontend/package-lock.json`; CI installs these exact resolutions.

### 4. Frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Frontend:

```text
http://localhost:3000
```

## Main product surfaces

- `/research` — run Research Agent tasks and watch the event stream;
- `/knowledge` — browse promoted Research knowledge;
- `/capabilities` — maintain Technology, Capability and Evidence;
- `/lab` — inspect Runs, events, model/tool activity and evaluations.

## Tests

Backend:

```bash
cd backend
uv run --no-sync ruff check app tests alembic
uv run --no-sync pytest -q
uv run --no-sync alembic upgrade head
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

GitHub Actions additionally starts the migrated API and runs an end-to-end smoke covering:

```text
Research
→ Run completion
→ Events
→ Evaluation
→ Knowledge
→ Technology
→ Capability
→ Evidence
→ relations
```

No real paid model/search API is required for the deterministic CI path.

## Security

- never commit `.env` or API keys;
- provider credentials remain backend-only;
- live `fetch_url` pins connections to validated public IPs, preserves Host/TLS names, ignores proxy environment variables, and re-validates redirects;
- Research Agent V0.1 only uses LOW-risk tools;
- external content is isolated as untrusted evidence under system instructions, with bounded excerpts and a conservative context budget. Set `RESEARCH_CONTEXT_WINDOW` / `RESEARCH_MAX_OUTPUT_TOKENS` to the smallest limits of your configured live models; defaults are 32768 / 2048. These controls reduce prompt-injection risk; they do not establish factual correctness.

## Known V0.1 limits

- single-user local mode;
- no authentication yet;
- Agent execution still uses in-process background tasks;
- real-provider smoke requires your own credentials and is intentionally separate from deterministic CI;
- GitHub repository tool exists in the Tool Gateway but is not yet automatically routed by the Research workflow;
- no semantic retrieval / embeddings yet;
- no Learning Agent or Coding Agent yet;
- no multi-agent orchestration yet.

Those are V0.2+ concerns, not hidden V0.1 requirements.

## Core principle

> Use AI to improve how I learn and work, and use my real work to learn how to build better AI agents.
