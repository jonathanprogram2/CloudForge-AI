from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_mock_run_and_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDFORGE_DB_PATH", str(tmp_path / "runs.db"))
    result = client.post("/api/v1/runs", json={
        "provider": "mock", "model_name": "test-model",
        "prompt": "Explain AWS", "expected_terms": ["AWS", "Azure"],
    })
    assert result.status_code == 200
    data = result.json()
    assert data["provider"] == "mock"
    assert data["status"] == "failed"
    assert data["score"] == 0.5
    assert data["input_tokens"] is None
    found = client.get("/api/v1/runs").json()
    assert len(found) == 1
    assert found[0]["id"] == data["id"]


def test_run_validation():
    result = client.post("/api/v1/runs", json={"provider": "unknown", "prompt": "hi"})
    assert result.status_code == 422


def test_groq_without_key(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDFORGE_DB_PATH", str(tmp_path / "empty.db"))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = client.post("/api/v1/runs", json={"provider": "groq", "model_name": "example", "prompt": "hi"})
    assert result.status_code == 502
    assert "GROQ_API_KEY" in result.json()["detail"]


def test_history_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDFORGE_DB_PATH", str(tmp_path / "runs.db"))
    for i in range(3):
        response = client.post("/api/v1/runs", json={"prompt": f"prompt {i}"})
        assert response.status_code == 200
    assert len(client.get("/api/v1/runs?limit=2").json()) == 2
    assert client.get("/api/v1/runs?limit=101").status_code == 422
