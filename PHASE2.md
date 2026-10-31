# Phase 2: Local LLM Runs + History

New endpoints:
- `POST /api/v1/runs`: Generate from a selected provider, run deterministic keyword scoring, save results in SQLite.
- `GET /api/v1/runs`: List the latest saved runs (limit 1-100).

## Zero-cost test in Swagger UI

At `http://127.0.0.1:8000/docs`, choose `POST /api/v1/runs` and use:

```json
{
  "provider": "mock",
  "model_name": "demo-model",
  "prompt": "Explain AWS scaling",
  "expected_terms": ["AWS", "scaling"]
}
```

The mock provider returns a predictable local response for testing. **This is not a real LLM answer, and keyword coverage is not a reliable measure of semantic correctness.** The run is saved to `data/cloudforge.db` (ignored by Git).

For optional live Groq calls, set `GROQ_API_KEY` in the terminal environment and select `provider: groq` with a currently supported model ID. External provider billing/free allowance may apply. Never commit credentials or use live providers in unit tests.

The older `POST /api/v1/evaluations` remains unchanged for backward compatibility.
