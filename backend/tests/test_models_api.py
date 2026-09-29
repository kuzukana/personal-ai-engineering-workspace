from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_models() -> None:
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] >= 1
    assert body["data"][0]["provider"] == "mock"
