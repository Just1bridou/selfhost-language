from fastapi.testclient import TestClient

from app.api.router import api_router
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_router_is_empty_and_included():
    assert api_router.routes == []
    assert app.routes


def test_static_mount_returns_404_for_missing_file():
    response = client.get("/nonexistent-file.txt")
    assert response.status_code == 404
