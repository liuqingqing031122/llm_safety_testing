from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_app_starts():
    response = client.get("/")
    assert response.status_code in [200, 404]


def test_invalid_score_endpoint():
    response = client.post("/api/conversations/999/score")
    assert response.status_code in [400, 404, 422]