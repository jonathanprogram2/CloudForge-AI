
from fastapi.testclient import TestClient

from app import main
from app.llm import ProviderError

client = TestClient(main.app)


def test_ready_with_sqlite(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "CLOUDFORGE_DB_PATH",
        str(tmp_path / "ready.db"),
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_ready_when_database_is_down(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://invalid:invalid@127.0.0.1:1/missing",
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"


def test_ollama_provider_failure(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "CLOUDFORGE_DB_PATH",
        str(tmp_path / "provider_failure.db"),
    )

    class FailingProvider:
        def generate(self, prompt, model):
            raise ProviderError("Ollama unavailable")

    monkeypatch.setattr(
        main,
        "get_provider",
        lambda name: FailingProvider(),
    )

    response = client.post(
        "/api/v1/runs",
        json={
            "provider": "ollama",
            "model_name": "qwen3:1.7b",
            "prompt": "Test unavailable Ollama",
        },
    )

    assert response.status_code == 502
    assert "Ollama unavailable" in response.json()["detail"]

    # Failed inference must not create a saved evaluation.
    assert client.get("/api/v1/runs").json() == []
