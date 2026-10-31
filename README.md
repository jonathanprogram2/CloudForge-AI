# CloudForge AI

A cloud-native AI infrastructure and evaluation platform, built in phases to demonstrate production engineering skills on AWS. **Phase 1 runs locally and makes no AWS or LLM API calls.**

## Current features (Phase 1)

- FastAPI REST API, health endpoint, and interactive OpenAPI docs
- Deterministic response term-coverage evaluator for test fixtures (NOT a model-quality or accuracy metric)
- Pydantic validation and Pytest integration tests
- Docker image with non-root user and health check
- GitHub Actions tests and Docker build validation

## Requirements

- Python 3.12+
- Docker Desktop (optional for running the container)

## Local setup

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

If `py -3.12` is not available, try `python -m venv .venv` with Python 3.12+.

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for interactive API docs or http://localhost:8000/health for a health check.

## Run tests

```bash
python -m pytest -q
```

## Docker

```bash
docker build -t cloudforge-ai:local .
docker run --rm -p 8000:8000 cloudforge-ai:local
```

## Example evaluation request

POST http://localhost:8000/api/v1/evaluations

```json
{
  "model_name": "demo-model",
  "prompt": "Describe cloud computing",
  "response": "AWS provides cloud services and scalable infrastructure.",
  "expected_terms": ["AWS", "scalable"]
}
```

Results are not persisted yet. The baseline checks for expected phrases and is not an actual LLM benchmark. Later phases will include durable storage, provider inference, evaluation pipelines, AWS infrastructure, and observability.

## Roadmap

1. **Foundation:** API, deterministic evaluator, Docker, tests, CI (this package)
2. **Application layer:** Persistent evaluation runs, provider adapters, auth, telemetry
3. **Infrastructure as code:** VPC, IAM, ECR, ECS/Fargate, ALB, storage, Terraform
4. **Delivery and operations:** CI/CD deployment, secrets, logs, monitoring, security checks
5. **Verification:** Load tests, failure recovery, cost reports, architecture diagram, demo

## Cost guardrail

Phase 1 has no AWS charges. Future AWS phases require explicit provisioning and may incur charges; make budgets and teardown part of deployment. Never commit secrets or AWS credentials.
