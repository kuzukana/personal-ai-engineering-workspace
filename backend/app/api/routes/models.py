from fastapi import APIRouter

from app.ai.container import model_gateway

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("")
async def list_models() -> dict[str, object]:
    data = []
    for model in model_gateway.registry.list_enabled():
        data.append(
            {
                "id": model.id,
                "provider": model.provider,
                "model_key": model.model_key,
                "display_name": model.display_name,
                "capabilities": model.capabilities.model_dump(),
            }
        )
    return {"data": data, "meta": {"total": len(data)}}
