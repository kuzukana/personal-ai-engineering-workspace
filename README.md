# Personal AI Engineering Workspace

An AI-native workspace for turning real research, learning and engineering work into reusable knowledge, verifiable capability and evidence.

## Current stage

V0.1 — Research Loop foundation.

Current priorities:
- FastAPI + Next.js application skeleton
- PostgreSQL + Redis infrastructure
- Model Gateway and provider abstraction
- Research Agent
- SSE run events and Agent Lab
- Knowledge / Capability / Evidence persistence
- deterministic AI evaluation

## Architecture

Browser → Next.js → FastAPI → Agent Runtime / Model Gateway / Tool Gateway → PostgreSQL + Redis.

See docs/00-project/PRD.md and docs/01-design/TECHNICAL_DESIGN.md for the full design.

## Local development

1. Copy .env.example to .env and fill only the providers you want to use.
2. Start infrastructure with Docker Compose.
3. Run backend and frontend independently during development.

Backend:

    cd backend
    python -m venv .venv
    pip install -e .[dev]
    uvicorn app.main:app --reload

Frontend will be initialized in the next implementation phase.

## Tests

    cd backend
    pytest

## Security

Never commit .env or API keys. Provider credentials are backend-only.

## Core principle

> Use AI to improve how I learn and work, and use my real work to learn how to build better AI agents.
