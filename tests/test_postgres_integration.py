
import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_postgres_save_and_retrieve():
    url = os.getenv("DATABASE_URL")

    if not url:
        pytest.skip("DATABASE_URL not configured")

    model_name = f"ci-postgres-{uuid4().hex}"

    response = client.post(
        "/api/v1/runs",
        json={
            "provider": "mock",
            "model_name": model_name,
            "prompt": "Explain PostgreSQL",
            "expected_terms": ["PostgreSQL"],
        },
    )

    assert response.status_code == 200, response.text

    run_id = response.json()["id"]

    try:
        # Verify that FastAPI actually persisted the result.
        with psycopg.connect(url) as connection:
            row = connection.execute(
                """
                SELECT data->>'model_name'
                FROM runs
                WHERE id = %s
                """,
                (run_id,),
            ).fetchone()

        assert row is not None
        assert row[0] == model_name

        # Verify that the API reads the stored result.
        history = client.get(
            "/api/v1/runs?limit=100"
        )

        assert history.status_code == 200

        assert any(
            item["id"] == run_id
            for item in history.json()
        )

        assert client.get("/ready").status_code == 200

    finally:
        # Clean up only the record created by this test.
        with psycopg.connect(url) as connection:
            connection.execute(
                "DELETE FROM runs WHERE id = %s",
                (run_id,),
            )
