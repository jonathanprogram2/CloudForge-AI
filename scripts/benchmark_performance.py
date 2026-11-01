
import argparse
import csv
import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROMPTS = [
    "Explain Docker Compose in three sentences.",
    "Explain why PostgreSQL is useful for AI applications.",
    "Explain what Prometheus monitors.",
    "Explain how an AI inference API works.",
    "Explain the difference between latency and throughput.",
]


def percentile(values, percent):
    ordered = sorted(values)
    if not ordered:
        return None

    index = (len(ordered) - 1) * percent / 100
    low = math.floor(index)
    high = math.ceil(index)

    return ordered[low] + (
        ordered[high] - ordered[low]
    ) * (index - low)


def request_model(api_url, model, prompt, timeout):
    payload = json.dumps({
        "provider": "ollama",
        "model_name": model,
        "prompt": prompt,
        "expected_terms": [],
    }).encode("utf-8")

    request = Request(
        f"{api_url.rstrip('/')}/api/v1/runs",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.perf_counter()

    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)

        return {
            "success": True,
            "request_latency_ms": round(
                (time.perf_counter() - start) * 1000, 2
            ),
            "inference_latency_ms": result["latency_ms"],
            "input_tokens": result.get("input_tokens"),
            "output_tokens": result.get("output_tokens"),
            
            "generation_duration_ns": result.get("generation_duration_ns"),
            "done_reason": result.get("done_reason"),

            "error": "",
        }

    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return {
            "success": False,
            "request_latency_ms": round(
                (time.perf_counter() - start) * 1000, 2
            ),
            "inference_latency_ms": None,
            "input_tokens": None,
            "output_tokens": None,
            
            "generation_duration_ns": None,
            "done_reason": None,

            "error": str(exc),
        }


def run_benchmark(args):
    results = []

    print(f"Model: {args.model}")
    print("Running warm-up request...")

    warmup = request_model(
        args.api, args.model, PROMPTS[0], args.timeout
    )

    if not warmup["success"]:
        raise SystemExit(
            f"Warm-up failed: {warmup['error']}"
        )

    print("Warm-up complete.\n")

    for index in range(args.runs):
        prompt = PROMPTS[index % len(PROMPTS)]

        result = request_model(
            args.api, args.model, prompt, args.timeout
        )

        result["run"] = index + 1
        result["model"] = args.model
        result["prompt"] = prompt

        results.append(result)

        status = "PASS" if result["success"] else "FAIL"

        print(
            f"Run {index + 1}/{args.runs} | "
            f"{status} | "
            f"{result['request_latency_ms']:.1f} ms"
        )

    successful = [r for r in results if r["success"]]

    latencies = [
        r["request_latency_ms"] for r in successful
    ]

    total_output = sum(
        r["output_tokens"] or 0 for r in successful
    )

    inference_seconds = sum(
        (r["inference_latency_ms"] or 0) / 1000
        for r in successful
    )

    
    generation_ns = sum(
        r["generation_duration_ns"] or 0
        for r in successful
    )

    native_throughput = (
        round(total_output / (generation_ns / 1e9), 2)
        if generation_ns > 0
        and all(r["generation_duration_ns"] for r in successful)
        else None
    )

    truncated_count = sum(
        r["done_reason"] == "length"
        for r in successful
    )


    report = {
        "model": args.model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "warmup_excluded": True,
        "concurrency": 1,
        "total_requests": len(results),
        "successful_requests": len(successful),
        "failed_requests": len(results) - len(successful),
        "error_rate_percent": round(
            (len(results) - len(successful))
            / len(results) * 100, 2
        ),
        "average_latency_ms": (
            round(statistics.mean(latencies), 2)
            if latencies else None
        ),
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "min_latency_ms": min(latencies) if latencies else None,
        "max_latency_ms": max(latencies) if latencies else None,
        "total_output_tokens": total_output,
        "estimated_output_tokens_per_inference_second": (
            round(total_output / inference_seconds, 2)
            if inference_seconds > 0 else None
        ),
        "results": results,
        
        "native_generation_tokens_per_second": native_throughput,
        "responses_stopped_at_length_limit": truncated_count,

    }

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    json_path = output / "benchmark_report.json"
    csv_path = output / "benchmark_results.csv"

    json_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "run", "model", "prompt", "success",
                "request_latency_ms", "inference_latency_ms",
                "input_tokens", "output_tokens", "error",
                "generation_duration_ns", "done_reason",

            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print("\n=== CLOUDFORGE AI PERFORMANCE REPORT ===")
    for key, value in report.items():
        if key != "results":
            print(f"{key}: {value}")

    print(f"\nSaved: {json_path}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark CloudForge local AI inference"
    )
    parser.add_argument("--model", default="qwen3:1.7b")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument(
        "--api", default="http://127.0.0.1:8000"
    )
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--output", default="reports/performance"
    )

    args = parser.parse_args()

    if not 1 <= args.runs <= 100:
        parser.error("--runs must be between 1 and 100")

    run_benchmark(args)
