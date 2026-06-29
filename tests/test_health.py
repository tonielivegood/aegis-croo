from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_health_reports_dry_run_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "aegis-risk-oracle",
        "mode": "dry-run",
    }
