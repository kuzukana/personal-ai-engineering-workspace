from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, object]:
    # Dependency probes are added when database/Redis clients are wired.
    return {
        "status": "ready",
        "dependencies": {"database": "not_configured", "redis": "not_configured"},
    }
