import os

import httpx


class LLMError(Exception):
    """Raised when the local LLM (Ollama) cannot produce a reply."""


def _base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")


def _model() -> str:
    return os.environ.get("OLLAMA_MODEL", "llama3.2:1b")


def generate_reply(prompt: str) -> str:
    """Generate a reply to `prompt` using the local Ollama instance.

    Raises LLMError if Ollama is unreachable, errors, times out, or returns a
    response this function cannot parse. Never calls any LLM endpoint other
    than the configured local Ollama service.
    """
    url = f"{_base_url()}/api/generate"
    payload = {"model": _model(), "prompt": prompt, "stream": False}

    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise LLMError(f"failed to reach Ollama at {url}: {exc}") from exc
    except ValueError as exc:
        raise LLMError(f"Ollama returned a non-JSON response: {exc}") from exc

    reply = data.get("response")
    if not isinstance(reply, str) or not reply.strip():
        raise LLMError(f"Ollama response did not contain usable text: {data!r}")

    return reply.strip()
