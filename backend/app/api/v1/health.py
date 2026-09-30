"""Health Check API route."""

from fastapi import APIRouter, Depends

from app.ai.base import BaseAIProvider
from app.api.deps import get_current_ai_provider
from app.core.config import settings
from app.core.database import db_manager
from app.schemas.health import HealthResponse

router = APIRouter(tags=["System Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health(
    ai_provider: BaseAIProvider = Depends(get_current_ai_provider)
) -> HealthResponse:
    """Return system liveness, database connectivity, and active AI engine mode."""
    db_connected = await db_manager.ping()

    # System is healthy if API and AI provider are operational; DB connectivity is reported
    overall_status = "healthy" if db_connected else "degraded"

    return HealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database={
            "connected": db_connected,
            "database_name": settings.MONGODB_DB_NAME,
            "host": settings.MONGODB_URI.split("@")[-1] if "@" in settings.MONGODB_URI else settings.MONGODB_URI
        },
        ai_provider={
            "active_provider": ai_provider.provider_name,
            "configured_mode": settings.AI_PROVIDER,
            "deterministic_fallback_available": True
        }
    )
