from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(monkeypatch) -> None:
    from unittest.mock import AsyncMock

    from app.api.routes import health

    session = AsyncMock()
    session.__aenter__.return_value = session
    monkeypatch.setattr(health, "SessionLocal", lambda: session)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["dependencies"]["database"] == "ready"
    session.execute.side_effect = RuntimeError("database down")
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["dependencies"]["database"] == "unavailable"
