from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="CloudForge AI", version="0.1.0", description="Cloud-native AI evaluation and deployment platform")


class EvaluationStatus(str, Enum):
    passed = "passed"
    failed = "failed"


class EvaluationRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=5000)
    response: str = Field(min_length=1, max_length=10000)
    expected_terms: list[str] = Field(default_factory=list, max_length=50)


class EvaluationResult(BaseModel):
    id: str
    model_name: str
    status: EvaluationStatus
    matched_terms: list[str]
    missing_terms: list[str]
    score: float
    evaluated_at: datetime


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "cloudforge-ai"}


@app.get("/api/v1/info")
def info() -> dict[str, str]:
    return {"name": "CloudForge AI", "version": "0.1.0", "mode": "local"}


@app.post("/api/v1/evaluations", response_model=EvaluationResult)
def evaluate(request: EvaluationRequest) -> EvaluationResult:
    """Deterministic baseline evaluator: term coverage, not LLM quality."""
    response_text = request.response.casefold()
    expected = list(dict.fromkeys(term.strip() for term in request.expected_terms if term.strip()))
    matched = [term for term in expected if term.casefold() in response_text]
    missing = [term for term in expected if term.casefold() not in response_text]
    score = len(matched) / len(expected) if expected else 1.0
    return EvaluationResult(
        id=str(uuid4()),
        model_name=request.model_name,
        status=EvaluationStatus.passed if not missing else EvaluationStatus.failed,
        matched_terms=matched,
        missing_terms=missing,
        score=round(score, 4),
        evaluated_at=datetime.now(timezone.utc),
    )
