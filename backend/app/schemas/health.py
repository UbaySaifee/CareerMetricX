"""Health Check schemas for CareerMetricX."""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health and status response model."""
    status: str = Field(..., description="Overall service status (healthy, degraded, unhealthy)")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    database: dict[str, Any] = Field(..., description="Database connectivity and details")
    ai_provider: dict[str, Any] = Field(..., description="Active AI provider status and mode")
