
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_benchmark_and_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLOUDFORGE_DB_PATH",
        str(tmp_path / "bench.db")
    )

    response = client.post("/api/v1/benchmarks", json={
        "provider": "mock",
        "models": ["demo-a", "demo-b"],
        "cases": [
            {
                "prompt": "Explain AWS",
                "expected_terms": ["AWS"]
            },
            {
                "prompt": "Explain S3",
                "expected_terms": ["S3", "Lambda"]
            }
        ]
    })

    assert response.status_code == 200, response.text

    payload = response.json()

    assert len(payload["results"]) == 4
    assert len(payload["summary"]) == 2
    assert payload["summary"][0]["average_score"] == 0.75
    assert payload["errors"] == []

    metrics = client.get("/api/v1/metrics").json()

    assert metrics["sample_size"] == 4
    assert metrics["average_score"] == 0.75


def test_benchmark_limits():
    response = client.post("/api/v1/benchmarks", json={
        "models": ["one", "two", "three", "four"],
        "cases": [{"prompt": "hey"}]
    })

    assert response.status_code == 422

    response = client.post("/api/v1/benchmarks", json={
        "models": ["same", "same"],
        "cases": [{"prompt": "hey"}]
    })

    assert response.status_code == 422


def test_metrics_empty(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLOUDFORGE_DB_PATH",
        str(tmp_path / "empty.db")
    )

    result = client.get("/api/v1/metrics").json()

    assert result["sample_size"] == 0
    assert result["average_score"] is None
