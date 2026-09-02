import json
import os
import threading

import httpx

from app.settings import get_llm_model


class LLMError(Exception):
    """Raised when the local LLM (Ollama) cannot produce a reply."""


def _base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")


def _model() -> str:
    return get_llm_model()


def list_installed_models() -> list[str]:
    """Model names Ollama actually has pulled locally.

    Returns an empty list when Ollama is unreachable rather than raising —
    callers use this to populate a picker, where "can't reach Ollama" is a
    state to display, not an error to fail on.
    """
    try:
        response = httpx.get(f"{_base_url()}/api/tags", timeout=5.0)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    models = data.get("models")
    if not isinstance(models, list):
        return []
    return sorted(
        model["name"]
        for model in models
        if isinstance(model, dict) and isinstance(model.get("name"), str)
    )


# --------------------------------------------------------------- pulling --
# Pulling a model is a multi-GB download, far too long to hold an HTTP request
# open for. It runs on a background thread and the UI polls this state.

_pull_lock = threading.Lock()
_pull_state: dict = {"model": None, "status": "idle", "percent": 0, "error": None}


def get_pull_state() -> dict:
    with _pull_lock:
        return dict(_pull_state)


def _set_pull_state(**changes) -> None:
    with _pull_lock:
        _pull_state.update(changes)


def _run_pull(model: str) -> None:
    try:
        with httpx.stream(
            "POST",
            f"{_base_url()}/api/pull",
            json={"model": model, "stream": True},
            timeout=httpx.Timeout(30.0, read=None),  # no read cap: big downloads
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue

                if event.get("error"):
                    _set_pull_state(status="error", error=str(event["error"]))
                    return

                total = event.get("total")
                completed = event.get("completed")
                if isinstance(total, int) and isinstance(completed, int) and total > 0:
                    _set_pull_state(percent=round(completed / total * 100))

        _set_pull_state(status="done", percent=100, error=None)
    except httpx.HTTPError as exc:
        _set_pull_state(status="error", error=f"could not pull {model}: {exc}")


def start_pull(model: str) -> dict:
    """Kick off a background `ollama pull`. Raises LLMError if one is already
    running — Ollama handles concurrent pulls poorly and the UI only tracks
    one at a time."""
    with _pull_lock:
        if _pull_state["status"] == "pulling":
            raise LLMError(f"already downloading {_pull_state['model']}")
        _pull_state.update(
            {"model": model, "status": "pulling", "percent": 0, "error": None}
        )

    thread = threading.Thread(target=_run_pull, args=(model,), daemon=True)
    thread.start()
    return get_pull_state()


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
