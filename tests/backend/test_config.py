"""Unit tests for configuration and settings."""

from app.core.config import Settings


def test_default_settings():
    """Verify default configuration attributes and constraints."""
    config = Settings()
    assert config.APP_NAME == "CareerMetricX"
    assert config.API_V1_PREFIX == "/api/v1"
    assert config.AI_PROVIDER == "deterministic"
    assert config.MAX_UPLOAD_SIZE_MB == 10
    assert "pdf" in config.ALLOWED_EXTENSIONS
    assert "docx" in config.ALLOWED_EXTENSIONS


def test_cors_origins_parsing():
    """Verify CORS origin parsing handles both json lists and string representations."""
    cfg = Settings(BACKEND_CORS_ORIGINS='["http://example.com", "http://localhost:5173"]')
    assert "http://example.com" in cfg.BACKEND_CORS_ORIGINS
    assert "http://localhost:5173" in cfg.BACKEND_CORS_ORIGINS


def test_production_settings_validation():
    """Verify insecure SECRET_KEY is rejected in production."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="careermetricx-insecure-dev-secret-key-replace-in-production-min32chars"
        )


def test_production_cors_wildcard_rejection():
    """Verify CORS wildcard is rejected in production."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            BACKEND_CORS_ORIGINS='["*"]'
        )

