from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.capabilities import router as capabilities_router
from app.api.routes.health import router as health_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.models import router as models_router
from app.api.routes.research import router as research_router
from app.api.routes.runs import router as runs_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Personal AI Engineering Workspace API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(capabilities_router)
app.include_router(health_router)
app.include_router(knowledge_router)
app.include_router(models_router)
app.include_router(research_router)
app.include_router(runs_router)
