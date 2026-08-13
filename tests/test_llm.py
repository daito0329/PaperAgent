import httpx

from paper_agent.llm import LLMError, OllamaClient


def test_ollama_client_wraps_invalid_response_json(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("invalid json")

    def fake_post(url, json, timeout):
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)

    try:
        OllamaClient().generate("prompt")
    except LLMError as exc:
        assert "invalid JSON" in str(exc)
    else:
        raise AssertionError("Expected LLMError")
