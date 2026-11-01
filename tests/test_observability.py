
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_prometheus_endpoint():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "cloudforge_ai_runs_total" in response.text
    assert "cloudforge_http_requests_total" in response.text


def test_http_request_counter():
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert 'path="/health"' in response.text


def test_inference_latency_metric_exists():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert (
        "cloudforge_ai_inference_duration_seconds"
        in response.text
    )
