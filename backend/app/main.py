"""CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform.
Main Application Entrypoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import db_manager
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event lifecycle manager."""
    logger.info("Initializing %s v%s in %s environment...", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    # Connect to persistent storage
    await db_manager.connect()

    yield

    # Graceful shutdown
    logger.info("Shutting down %s...", settings.APP_NAME)
    await db_manager.disconnect()


def create_application() -> FastAPI:
    """Application factory for CareerMetricX."""
    application = FastAPI(
        title="CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform",
        description="Production-quality platform transforming career readiness from keyword matching into an evidence-grounded capability mapping and interview verification loop.",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # CORS Middleware
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Mount Versioned API Router
    application.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @application.get("/", tags=["System"])
    async def root():
        """Root status route."""
        return {
            "title": "CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform",
            "tagline": "Measure your skills. Prove your readiness.",
            "version": settings.APP_VERSION,
            "status": "online",
            "docs_url": "/docs",
            "api_prefix": settings.API_V1_PREFIX
        }

    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
