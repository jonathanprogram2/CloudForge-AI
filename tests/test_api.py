from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_info():
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    assert response.json()["mode"] == "local"


def test_evaluation_pass():
    response = client.post("/api/v1/evaluations", json={
        "model_name": "demo-model", "prompt": "Describe cloud computing",
        "response": "AWS provides cloud services and scalable infrastructure.",
        "expected_terms": ["AWS", "scalable"],
    })
    assert response.status_code == 200
    assert response.json()["status"] == "passed"
    assert response.json()["score"] == 1.0


def test_evaluation_fail():
    response = client.post("/api/v1/evaluations", json={
        "model_name": "demo-model", "prompt": "Describe cloud computing",
        "response": "Cloud resources are elastic.",
        "expected_terms": ["AWS", "elastic"],
    })
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["score"] == 0.5
    assert response.json()["missing_terms"] == ["AWS"]


def test_invalid_request():
    response = client.post("/api/v1/evaluations", json={"model_name": "", "prompt": "", "response": ""})
    assert response.status_code == 422


def test_case_insensitive_and_deduplicated():
    response = client.post("/api/v1/evaluations", json={
        "model_name": "demo", "prompt": "Test", "response": "AWS CLOUD",
        "expected_terms": ["aws", "aws", "cloud"],
    })
    assert response.json()["score"] == 1.0
    assert len(response.json()["matched_terms"]) == 2
