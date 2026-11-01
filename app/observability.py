
from time import perf_counter

from fastapi import Request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response


HTTP_REQUESTS = Counter(
    "cloudforge_http_requests_total",
    "Total HTTP requests handled by CloudForge",
    ["method", "path", "status"],
)

HTTP_DURATION = Histogram(
    "cloudforge_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

AI_RUNS = Counter(
    "cloudforge_ai_runs_total",
    "Completed AI evaluation runs",
    ["provider", "model", "status"],
)

AI_LATENCY = Histogram(
    "cloudforge_ai_inference_duration_seconds",
    "Time spent generating an AI response",
    ["provider", "model"],
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60, 120),
)

AI_TOKENS = Counter(
    "cloudforge_ai_tokens_total",
    "Tokens reported by AI model providers",
    ["provider", "model", "direction"],
)


def record_ai_run(
    provider: str,
    model: str,
    status: str,
    latency_ms: float,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    AI_RUNS.labels(provider, model, status).inc()

    AI_LATENCY.labels(provider, model).observe(
        latency_ms / 1000
    )

    if input_tokens is not None:
        AI_TOKENS.labels(
            provider, model, "input"
        ).inc(input_tokens)

    if output_tokens is not None:
        AI_TOKENS.labels(
            provider, model, "output"
        ).inc(output_tokens)


async def monitor_requests(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)

    path = request.url.path

    # Avoid exposing dynamic URL values as metric labels.
    known_paths = {
        "/health",
        "/api/v1/info",
        "/api/v1/evaluations",
        "/api/v1/runs",
        "/api/v1/benchmarks",
        "/api/v1/metrics",
    }

    if path in known_paths:
        method = request.method

        HTTP_REQUESTS.labels(
            method, path, str(response.status_code)
        ).inc()

        HTTP_DURATION.labels(method, path).observe(
            perf_counter() - start
        )

    return response


def prometheus_metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
