import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    try:
        async with asyncio.timeout(2), SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "dependencies": {"database": "unavailable", "redis": "optional"},
            },
        )
    return {
        "status": "ready",
        "dependencies": {"database": "ready", "redis": "optional"},
    }
