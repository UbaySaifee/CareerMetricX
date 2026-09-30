"""Integration tests for root and health check endpoints."""


def test_root_endpoint(client):
    """Verify root endpoint returns system metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform"
    assert data["tagline"] == "Measure your skills. Prove your readiness."
    assert data["status"] == "online"
    assert data["api_prefix"] == "/api/v1"


def test_health_endpoint(client):
    """Verify health endpoint returns liveness, database status, and AI provider info."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "CareerMetricX"
    assert "status" in data
    assert "database" in data
    assert "ai_provider" in data
    assert data["ai_provider"]["deterministic_fallback_available"] is True
