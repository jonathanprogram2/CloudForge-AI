
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.llm import OllamaProvider, get_provider
from app.main import app

client = TestClient(app)


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({
            "model": "qwen3:1.7b",
            "message": {
                "role": "assistant",
                "content": "Docker Compose manages containers."
            },
            "prompt_eval_count": 18,
            "eval_count": 7,
            
            "eval_duration": 50000000,
            "total_duration": 90000000,
            "done_reason": "stop",

        }).encode("utf-8")


def test_ollama_provider():
    with patch("app.llm.urlopen", return_value=FakeResponse()):
        result = OllamaProvider().generate(
            "Explain Docker Compose",
            "qwen3:1.7b",
        )

    assert result.provider == "ollama"
    assert result.model == "qwen3:1.7b"
    assert result.input_tokens == 18
    assert result.output_tokens == 7
    assert result.latency_ms >= 0


def test_ollama_provider_registered():
    assert isinstance(get_provider("ollama"), OllamaProvider)


def test_ollama_api_integration(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "CLOUDFORGE_DB_PATH",
        str(tmp_path / "ollama.db"),
    )

    with patch("app.llm.urlopen", return_value=FakeResponse()):
        response = client.post(
            "/api/v1/runs",
            json={
                "provider": "ollama",
                "model_name": "qwen3:1.7b",
                "prompt": "Explain Docker Compose",
                "expected_terms": ["Docker", "Compose"],
            },
        )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["provider"] == "ollama"
    assert result["status"] == "passed"
    assert result["input_tokens"] == 18
    assert result["output_tokens"] == 7

    history = client.get("/api/v1/runs").json()
    assert len(history) == 1
    assert history[0]["id"] == result["id"]


def test_ollama_native_performance_fields():
    with patch("app.llm.urlopen", return_value=FakeResponse()):
        result = OllamaProvider().generate(
            "Explain Docker Compose",
            "qwen3:1.7b",
        )

    assert result.generation_duration_ns == 50000000
    assert result.total_duration_ns == 90000000
    assert result.done_reason == "stop"
    assert result.output_tokens == 7
