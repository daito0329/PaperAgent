from __future__ import annotations

from dataclasses import dataclass
import os


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class OllamaClient:
    model: str = "llama3.1"
    base_url: str | None = None
    timeout: float = 120.0

    def generate(self, prompt: str) -> str:
        try:
            import httpx
        except ModuleNotFoundError as exc:
            raise LLMError("Ollama support requires the 'httpx' package.") from exc

        url = f"{self._base_url().rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        try:
            response = httpx.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Failed to call Ollama at {url}: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMError("Ollama returned invalid JSON.") from exc
        generated = data.get("response")
        if not isinstance(generated, str) or not generated.strip():
            raise LLMError("Ollama returned an empty response.")
        return generated

    def _base_url(self) -> str:
        return self.base_url or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
