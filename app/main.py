from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from typing import Literal
from app.llm import ProviderError, get_provider
from app.history import save_run, list_runs
from pydantic import BaseModel, Field

from fastapi.middleware.cors import CORSMiddleware



from app.observability import (
    monitor_requests,
    prometheus_metrics,
    record_ai_run,
)



app = FastAPI(title="CloudForge AI", version="0.1.0", description="Cloud-native AI evaluation and deployment platform")


app.middleware("http")(monitor_requests)


@app.get("/metrics", include_in_schema=False)
def prometheus_endpoint():
    return prometheus_metrics()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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


class GenerateEvaluationRequest(BaseModel):
    provider: Literal["mock", "groq", "ollama"] = "mock"
    model_name: str = Field(default="demo-model", min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=5000)
    expected_terms: list[str] = Field(default_factory=list, max_length=50)


class GenerationEvaluationResult(EvaluationResult):
    provider: str
    response: str
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None


@app.post("/api/v1/runs", response_model=GenerationEvaluationResult)
def generate_and_evaluate(request: GenerateEvaluationRequest) -> GenerationEvaluationResult:
    """Generate a response, evaluate coverage, and store the run locally."""
    try:
        generated = get_provider(request.provider).generate(request.prompt, request.model_name)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    baseline = evaluate(EvaluationRequest(
        model_name=generated.model,
        prompt=request.prompt,
        response=generated.text,
        expected_terms=request.expected_terms,
    ))
    result = GenerationEvaluationResult(
        **baseline.model_dump(),
        provider=generated.provider,
        response=generated.text,
        latency_ms=generated.latency_ms,
        input_tokens=generated.input_tokens,
        output_tokens=generated.output_tokens,
    )
    save_run(result.model_dump(mode="json"))
    
    record_ai_run(
        provider=result.provider,
        model=result.model_name,
        status=result.status.value,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )



    return result


@app.get("/api/v1/runs", response_model=list[GenerationEvaluationResult])
def history(limit: int = Query(default=20, ge=1, le=100)) -> list[dict]:
    return list_runs(limit)


# Phase 3: AI benchmarking and metrics

class BenchmarkCase(BaseModel):
    prompt: str = Field(min_length=1, max_length=5000)
    expected_terms: list[str] = Field(default_factory=list, max_length=50)


class BenchmarkRequest(BaseModel):
    provider: Literal["mock", "groq", "ollama"] = "mock"
    models: list[str] = Field(min_length=1, max_length=3)
    cases: list[BenchmarkCase] = Field(min_length=1, max_length=4)


@app.post("/api/v1/benchmarks")
def benchmark(request: BenchmarkRequest) -> dict:
    """Compare models across a bounded set of test cases."""

    if len(set(request.models)) != len(request.models):
        raise HTTPException(
            status_code=422,
            detail="Models must be unique"
        )

    results = []
    errors = []

    for model in request.models:
        if not model.strip():
            raise HTTPException(
                status_code=422,
                detail="Model names cannot be blank"
            )

        for case_index, case in enumerate(request.cases):
            try:
                result = generate_and_evaluate(
                    GenerateEvaluationRequest(
                        provider=request.provider,
                        model_name=model,
                        prompt=case.prompt,
                        expected_terms=case.expected_terms,
                    )
                )

                results.append({
                    "case_index": case_index,
                    **result.model_dump(mode="json")
                })

            except HTTPException as exc:
                errors.append({
                    "model": model,
                    "case_index": case_index,
                    "error": str(exc.detail)
                })

    summary = []

    for model in request.models:
        successful = [
            r for r in results
            if r["model_name"] == model
        ]

        summary.append({
            "model": model,
            "completed": len(successful),
            "failed_requests": sum(
                e["model"] == model for e in errors
            ),
            "average_score": (
                round(
                    sum(r["score"] for r in successful)
                    / len(successful), 4
                ) if successful else None
            ),
            "average_latency_ms": (
                round(
                    sum(r["latency_ms"] for r in successful)
                    / len(successful), 2
                ) if successful else None
            ),
            "input_tokens": sum(
                r["input_tokens"] for r in successful
                if r["input_tokens"] is not None
            ),
            "output_tokens": sum(
                r["output_tokens"] for r in successful
                if r["output_tokens"] is not None
            ),
        })

    return {
        "summary": summary,
        "results": results,
        "errors": errors,
        "note": (
            "Score measures keyword coverage, "
            "not semantic correctness."
        )
    }


@app.get("/api/v1/metrics")
def metrics(
    limit: int = Query(default=100, ge=1, le=100)
) -> dict:
    """Summarize recent locally stored evaluations."""

    runs = list_runs(limit)

    return {
        "sample_size": len(runs),
        "average_score": (
            round(
                sum(r["score"] for r in runs)
                / len(runs), 4
            ) if runs else None
        ),
        "pass_rate": (
            round(
                sum(r["status"] == "passed" for r in runs)
                / len(runs), 4
            ) if runs else None
        ),
        "average_latency_ms": (
            round(
                sum(r["latency_ms"] for r in runs)
                / len(runs), 2
            ) if runs else None
        ),
        "known_input_tokens": sum(
            r.get("input_tokens") or 0 for r in runs
        ),
        "known_output_tokens": sum(
            r.get("output_tokens") or 0 for r in runs
        ),
        "note": (
            "Token totals exclude runs without "
            "reported usage."
        )
    }

