# CloudForge AI — Local Inference Performance

## Overview

CloudForge AI is a local-first AI evaluation and monitoring platform. This benchmark measures the performance of Qwen3 1.7B running through Ollama and a containerized FastAPI backend.

## Test Environment

- **GPU:** NVIDIA GeForce RTX 4070 Laptop GPU (8 GB VRAM)
- **CPU:** Intel Core i7-13700HX
- **RAM:** 16 GB
- **Model:** Qwen3 1.7B
- **Backend:** FastAPI
- **Database:** PostgreSQL
- **Monitoring:** Prometheus and Grafana
- **Orchestration:** Docker Compose

## Benchmark Methodology

The benchmark executed one warm-up request followed by ten sequential measured requests across five technical prompts.

Concurrency was set to one, and the warm-up request was excluded from the results. Requests were submitted through the FastAPI evaluation endpoint.

## Results

| Metric                          |      Result |
| ------------------------------- | ----------: |
| Successful requests             |       10/10 |
| Error rate                      |          0% |
| Average API latency             | 1,381.92 ms |
| p50 API latency                 | 1,624.32 ms |
| p95 API latency                 | 1,667.32 ms |
| Minimum latency                 |   378.54 ms |
| Maximum latency                 | 1,679.48 ms |
| Total generated tokens reported |       2,160 |

## Limitations

These measurements represent a small local test, not production-scale performance.

Several responses reached the configured 256-token output limit. Response completeness was not evaluated.

The original benchmark also produced an estimated throughput of 150.56 output tokens per inference second. This is not a verified GPU decoding-throughput measurement.

Some internal inference timings exceeded client-observed request timings, so those measurements require investigation before drawing detailed conclusions.

The p95 result is calculated from only ten requests and should not be treated as a statistically reliable production latency estimate.

## Reproduction

Start the CloudForge AI application and ensure Ollama has the Qwen3 1.7B model installed.

Run:

```powershell
docker compose up -d

python scripts/benchmark_performance.py --model qwen3:1.7b --runs 10
```

The script produces JSON and CSV benchmark reports.

## Future Improvements

- Record Ollama's native generation duration.
- Detect responses stopped by output-token limits.
- Repeat benchmarks with larger sample sizes.
- Separate model generation latency from total API request latency.
- Compare Qwen3 1.7B against Qwen3 4B.
