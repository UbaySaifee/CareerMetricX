"""FastAPI Dependency Injection definitions."""


from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.base import BaseAIProvider
from app.ai.factory import get_ai_provider
from app.core.database import get_database


def get_current_ai_provider() -> BaseAIProvider:
    """Dependency providing the active AI provider instance."""
    return get_ai_provider()


async def get_db_session(
    db: AsyncIOMotorDatabase | None = Depends(get_database)
) -> AsyncIOMotorDatabase | None:
    """Dependency providing the active MongoDB session."""
    return db
