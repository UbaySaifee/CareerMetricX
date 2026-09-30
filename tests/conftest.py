"""Pytest fixtures for CareerMetricX."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.main import app


@pytest.fixture
def test_settings():
    """Fixture providing test configuration."""
    return settings


@pytest.fixture
def client():
    """Synchronous TestClient for API integration tests."""
    with TestClient(app) as test_client:
        yield test_client
