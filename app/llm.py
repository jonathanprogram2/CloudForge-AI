import json
import os
from dataclasses import dataclass
from time import perf_counter
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class Generation:
    text: str
    model: str
    provider: str
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    generation_duration_ns: int | None = None
    total_duration_ns: int | None = None
    done_reason: str | None = None



class Provider(Protocol):
    def generate(self, prompt: str, model: str) -> Generation: ...


class ProviderError(Exception):
    pass


class MockProvider:
    def generate(self, prompt: str, model: str) -> Generation:
        start = perf_counter()
        response = f"Mock response to: {prompt}"
        return Generation(response, model, "mock", round((perf_counter() - start) * 1000, 2))


class GroqProvider:
    def generate(self, prompt: str, model: str) -> Generation:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ProviderError("GROQ_API_KEY is missing. Set it in your environment to enable Groq.")
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }).encode("utf-8")
        req = Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        start = perf_counter()
        try:
            with urlopen(req, timeout=30) as response:
                data = json.load(response)
        except HTTPError as exc:
            raise ProviderError(f"Groq API returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, ValueError, KeyError) as exc:
            raise ProviderError(f"Groq API request failed: {type(exc).__name__}") from exc
        try:
            usage = data.get("usage") or {}
            return Generation(
                text=data["choices"][0]["message"]["content"],
                model=data.get("model", model),
                provider="groq",
                latency_ms=round((perf_counter() - start) * 1000, 2),
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Unexpected Groq API response structure") from exc



class OllamaProvider:
    def generate(self, prompt: str, model: str) -> Generation:
        base_url = os.getenv(
            "OLLAMA_BASE_URL",
            "http://127.0.0.1:11434"
        ).rstrip("/")

        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "think": False,
            "keep_alive": "2m",
            "options": {
                "temperature": 0,
                "num_predict": 256,
                "num_ctx": 2048,
            }
        }).encode("utf-8")

        request = Request(
            f"{base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        start = perf_counter()

        try:
            with urlopen(request, timeout=120) as response:
                data = json.load(response)

        except HTTPError as exc:
            raise ProviderError(
                f"Ollama returned HTTP {exc.code}. "
                "Check that the model is installed."
            ) from exc

        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ProviderError(
                "Cannot reach Ollama. Check that it is "
                "running and accessible from the API."
            ) from exc

        try:
            generated_text = data["message"]["content"]

            if not generated_text.strip():
                raise ProviderError(
                    "Ollama returned an empty response."
                )

            return Generation(
                text=generated_text,
                model=data.get("model", model),
                provider="ollama",
                latency_ms=round(
                    (perf_counter() - start) * 1000, 2
                ),
                input_tokens=data.get("prompt_eval_count"),
                output_tokens=data.get("eval_count"),
                
                generation_duration_ns=data.get("eval_duration"),
                total_duration_ns=data.get("total_duration"),
                done_reason=data.get("done_reason"),

            )

        except (KeyError, TypeError, AttributeError) as exc:
            raise ProviderError(
                "Unexpected Ollama response format."
            ) from exc




def get_provider(name: str) -> Provider:
    if name == "mock":
        return MockProvider()
    if name == "groq":
        return GroqProvider()
    if name == "ollama":
        return OllamaProvider()

    raise ValueError(f"Unsupported provider: {name}")
