# CloudForge AI

**Cloud-native AI evaluation and infrastructure engineering portfolio project** built with Python, FastAPI, React, TypeScript, Docker, Terraform, and AWS infrastructure definitions.

CloudForge AI provides a local AI operations dashboard for running evaluations, comparing benchmark results, and reviewing historical metrics. The repository also includes an AWS ECS/Fargate deployment architecture defined with Terraform and a GitHub Actions DevSecOps pipeline.

> **Current status:** The application runs locally, including inside Docker. Terraform has been initialized and validated locally; **the AWS infrastructure has not been provisioned or tested on AWS**. Model comparisons using the default `mock` provider are simulations, not evidence of real model quality.

## Features

- **FastAPI backend:** REST endpoints, input validation, health checks, and interactive OpenAPI documentation.
- **AI evaluations:** Deterministic expected-term coverage scoring for test cases. This is **not** a semantic accuracy or model-quality measure.
- **Provider abstraction:** Local mock inference with optional Groq API integration for live inference.
- **Benchmarking:** Compare up to three model identifiers across up to four test cases in a request, with individual results, aggregated scores, latency, token usage (when reported), and error records.
- **Evaluation history:** SQLite storage for generated evaluation runs and an API for retrieving recent results.
- **Operations dashboard:** React/TypeScript interface for metrics, benchmark execution, comparisons, and evaluation history.
- **Containerization:** Dockerized FastAPI backend, runnable locally.
- **AWS Infrastructure as Code:** Terraform definitions for VPC, two public subnets, security groups, internet gateway, IAM roles, Amazon ECR, Amazon ECS Fargate, Application Load Balancer, and CloudWatch logs.
- **DevSecOps CI:** GitHub Actions workflows for backend tests, frontend lint/build, Terraform validation, and infrastructure/container security scans. Passing status should be checked in GitHub Actions.

## Technology stack

| Layer           | Technologies                                                       |
| --------------- | ------------------------------------------------------------------ |
| Backend         | Python, FastAPI, Pydantic, Pytest                                  |
| Frontend        | React, TypeScript, Vite, CSS                                       |
| AI              | Local mock provider, optional Groq API                             |
| Data            | SQLite (local evaluation history)                                  |
| Infrastructure  | Docker, Terraform, AWS ECS/Fargate, ECR, VPC, ALB, IAM, CloudWatch |
| CI and security | GitHub Actions, Trivy                                              |

## Repository layout

```text
.
├── .github/workflows/       # Continuous integration and security scans
├── app/                     # FastAPI application and evaluation logic
├── frontend/                # React and TypeScript dashboard
├── infrastructure/
│   └── terraform/           # AWS infrastructure definitions
├── tests/                   # Python API and benchmark tests
├── Dockerfile
├── requirements.txt         # Python application + test dependencies
└── README.md
```

## Local development

### Prerequisites

- Python **3.10+** (the project has been run locally with Python 3.10)
- Node.js and npm (Node.js 22 is used in the CI configuration)
- Docker Desktop (optional, for container testing)
- Terraform (optional, for infrastructure validation)

### 1. Start the FastAPI backend

**Windows PowerShell**, from the repository root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

If you use another compatible Python version, replace `py -3.10` with that interpreter.

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

- API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

### 2. Start the React dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Keep the backend running on port `8000` for dashboard API calls.

### 3. Run quality checks

From the repository root:

```powershell
python -m pytest -q
cd frontend
npm run lint
npm run build
```

The last locally reported backend test result was **13 passing tests**. Frontend and CI checks should be confirmed again after changes.

## API endpoints

| Method | Route                 | Purpose                                             |
| ------ | --------------------- | --------------------------------------------------- |
| GET    | `/health`             | Service health                                      |
| GET    | `/api/v1/info`        | Service information                                 |
| POST   | `/api/v1/evaluations` | Evaluate a supplied response against expected terms |
| POST   | `/api/v1/runs`        | Generate, evaluate, and save a run                  |
| GET    | `/api/v1/runs`        | Retrieve recent run history                         |
| POST   | `/api/v1/benchmarks`  | Execute bounded comparison benchmarks               |
| GET    | `/api/v1/metrics`     | Aggregate recent saved-run metrics                  |

Example mock benchmark request to `POST /api/v1/benchmarks`:

```json
{
  "provider": "mock",
  "models": ["model-alpha", "model-beta"],
  "cases": [
    {
      "prompt": "Explain AWS cloud computing",
      "expected_terms": ["AWS", "cloud"]
    }
  ]
}
```

The mock provider requires no external API key. The model names above are demonstration labels and do not represent independently queried LLMs. For live inference, the Groq provider requires a valid `GROQ_API_KEY` and a supported model ID. **Never commit API keys or credentials.**

## Run the backend in Docker

From the repository root:

```bash
docker build -t cloudforge-ai:local .
docker run --rm -p 8002:8000 cloudforge-ai:local
```

Open http://127.0.0.1:8002/health to check the container.

**Storage caveat:** SQLite history stored inside an ephemeral container is not durable across container removal. A persistent external data store will be required for production deployment.

## AWS infrastructure (defined, not deployed)

Terraform configuration is located in `infrastructure/terraform/`. It models:

- VPC and internet gateway with public subnets in two Availability Zones
- Application Load Balancer and inbound security groups
- ECS Fargate service and task definition
- ECR repository for the application container image
- ECS IAM execution and application roles
- CloudWatch log group

To validate locally:

```powershell
cd infrastructure/terraform
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

These commands **do not create AWS resources**. Do not run `terraform apply` until the placeholder container image has been replaced, cost exposure has been reviewed, and a deployment plan has been approved.

### Deployment and security limitations

The current Terraform configuration is a **learning and portfolio architecture**, not a production-hardened deployment. It uses HTTP on the load balancer and publicly networked Fargate tasks. Production improvements include HTTPS, private networking, persistent storage, secrets management, application authentication, controlled egress, monitoring alarms, and tested recovery procedures. The dashboard currently calls a localhost API rather than a deployed service.

## Continuous integration

The GitHub Actions workflow in `.github/workflows/ci.yml` is configured for:

1. Python tests
2. React linting and production build
3. Terraform formatting and validation
4. Infrastructure security scanning
5. Container vulnerability scanning

Check the **Actions** tab for current job results. Security scans may uncover findings that need to be addressed before deployment; configuring a check is not the same as passing it.

## Development status and roadmap

| Area                                                         | Status                                          |
| ------------------------------------------------------------ | ----------------------------------------------- |
| FastAPI backend and local evaluation                         | Implemented and tested locally                  |
| Mock provider, optional Groq integration, SQLite run history | Implemented locally; real provider use optional |
| Benchmark endpoint and metrics                               | Implemented; mock benchmarks verified           |
| React operations dashboard                                   | Running locally                                 |
| Docker backend                                               | Built and health-checked locally                |
| Terraform AWS infrastructure                                 | Defined and locally validated                   |
| GitHub Actions DevSecOps pipeline                            | Configured; review workflow runs                |
| AWS deployment, load testing, cost verification              | Not yet completed                               |

## Cost and credentials

Local application development, Docker, and Terraform validation require **no AWS resource provisioning**. An actual AWS deployment can incur charges for ECS Fargate, load balancing, public IPv4 addresses, logging, storage, and other services. A `$0` current bill is **not** a guarantee that new resources will be free. Review AWS pricing and budgets before deployment, and tear down resources after testing.

Do not commit `.env` files, secrets, credentials, SQLite databases, Terraform state files, or generated build directories.
