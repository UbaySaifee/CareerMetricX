"""Repository for persisting and retrieving career analysis evaluation reports."""

from typing import Any, Optional
from app.core.database import DatabaseManager, db_manager


class AnalysisRepository:
    """Repository abstraction over MongoDB / in-memory storage for analysis reports."""

    def __init__(self, manager: DatabaseManager = db_manager) -> None:
        self.db_manager = manager

    async def save_evaluation(self, data: dict[str, Any]) -> str:
        """Save analysis evaluation report and return evaluation ID."""
        return await self.db_manager.save_evaluation(data)

    async def get_evaluation(self, report_id: str) -> Optional[dict[str, Any]]:
        """Retrieve evaluation report by report_id."""
        return await self.db_manager.get_evaluation(report_id)


analysis_repo = AnalysisRepository()
