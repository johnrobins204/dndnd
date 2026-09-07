from typing import Protocol

import httpx

from dndnd.config import Settings


class IntelligenceError(RuntimeError):
    pass


OllamaError = IntelligenceError


class IntelligenceClient(Protocol):
    def generate(self, prompt: str, *, model: str | None = None) -> str: ...


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_url.rstrip("/")
        self._default_model = settings.ollama_model
        self._timeout = settings.request_timeout_seconds

    def _available_models(self) -> str:
        try:
            tags = (
                httpx.get(f"{self._base_url}/api/tags", timeout=10)
                .json()
                .get("models", [])
            )
            return (
                ", ".join(tag.get("model", tag.get("name", "?")) for tag in tags)
                or "none"
            )
        except Exception:
            return "unknown"

    def generate(self, prompt: str, *, model: str | None = None) -> str:
        model_name = model or self._default_model
        try:
            response = httpx.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            content = response.json().get("message", {}).get("content")
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                detail = (
                    f"model '{model_name}' not found. "
                    f"Available models: {self._available_models()}"
                )
            else:
                detail = error.response.text or str(error)
            raise IntelligenceError(f"Intelligence request failed: {detail}") from error
        except (httpx.HTTPError, ValueError) as error:
            raise IntelligenceError(f"Intelligence request failed: {error}") from error
        if not content:
            raise IntelligenceError("Intelligence endpoint returned an empty response.")
        return str(content)


__all__ = ["IntelligenceClient", "IntelligenceError", "OllamaClient", "OllamaError"]
