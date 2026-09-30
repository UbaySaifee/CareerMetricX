"""Application Configuration module for CareerMetricX."""

import json
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings validated by Pydantic."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application Runtime
    ENVIRONMENT: str = "development"
    APP_NAME: str = "CareerMetricX"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:80"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                pass
        elif isinstance(v, list):
            return [str(item) for item in v]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "careermetricx_dev"
    MONGODB_TEST_DB_NAME: str = "careermetricx_test"
    MONGODB_MAX_POOL_SIZE: int = 50
    MONGODB_MIN_POOL_SIZE: int = 10

    # Security & JWT
    SECRET_KEY: str = "careermetricx-insecure-dev-secret-key-replace-in-production-min32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Provider Settings
    AI_PROVIDER: str = "deterministic"  # "deterministic" | "openai" | "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL_NAME: str = "gpt-4o-mini"
    AI_TEMPERATURE: float = 0.2
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES: int = 2

    # Uploads & Storage
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "docx", "txt"]
    UPLOAD_DIR: str = "./storage/uploads"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Enforce production security safeguards per docs/SECURITY.md."""
        if self.ENVIRONMENT.lower() == "production":
            if "insecure" in self.SECRET_KEY.lower() or len(self.SECRET_KEY) < 32:
                raise ValueError("In production, SECRET_KEY must be a cryptographically secure key of at least 32 characters.")
            if isinstance(self.BACKEND_CORS_ORIGINS, list) and "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("In production, BACKEND_CORS_ORIGINS cannot contain wildcard '*'.")
        return self


settings = Settings()
