from typing import Protocol

import httpx

from dndnd.config import Settings


class IntelligenceError(RuntimeError):
	pass


OllamaError = IntelligenceError


class IntelligenceClient(Protocol):
	def generate(self, prompt: str, *, model: str | None = None) -> str:
		...


class OllamaClient:
	def __init__(self, settings: Settings) -> None:
		self._base_url = settings.ollama_url.rstrip("/")
		self._default_model = settings.ollama_model
		self._timeout = settings.request_timeout_seconds

	def generate(self, prompt: str, *, model: str | None = None) -> str:
		try:
			response = httpx.post(
				f"{self._base_url}/api/chat",
				json={
					"model": model or self._default_model,
					"messages": [{"role": "user", "content": prompt}],
					"stream": False,
				},
				timeout=self._timeout,
			)
			response.raise_for_status()
			content = response.json().get("message", {}).get("content")
		except (httpx.HTTPError, ValueError) as error:
			raise IntelligenceError(f"Intelligence request failed: {error}") from error
		if not content:
			raise IntelligenceError("Intelligence endpoint returned an empty response.")
		return str(content)

__all__ = ["IntelligenceClient", "IntelligenceError", "OllamaClient", "OllamaError"]
