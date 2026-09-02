import httpx
import pytest

from app import settings

from app.pipeline.llm import LLMError, _base_url, generate_reply


class _FakeResponse:
    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        return None

    def json(self):
        return self._json


def test_generate_reply_returns_text(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        return _FakeResponse({"message": {"content": "  hello there  "}})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert generate_reply([{"role": "user", "content": "hi"}]) == "hello there"


def test_generate_reply_uses_configured_url_and_model(monkeypatch, tmp_path):
    """OLLAMA_BASE_URL is read per call; OLLAMA_MODEL is now only the *default*
    seeded into the settings store on first read (the model is changeable at
    runtime via /api/models), so the cache has to be reset for a new env value
    to take effect."""
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse({"message": {"content": "ok"}})

    monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom-host:9999")
    monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    settings.reset_cache()
    monkeypatch.setattr(httpx, "post", fake_post)

    try:
        generate_reply([{"role": "user", "content": "hi"}])
        assert captured["url"] == "http://custom-host:9999/api/chat"
        assert captured["json"]["model"] == "custom-model"
    finally:
        settings.reset_cache()


def test_generate_reply_raises_on_connection_error(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMError):
        generate_reply([{"role": "user", "content": "hi"}])


def test_generate_reply_raises_on_timeout(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMError):
        generate_reply([{"role": "user", "content": "hi"}])


def test_generate_reply_raises_on_malformed_response(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        return _FakeResponse({"unexpected": "shape"})

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMError):
        generate_reply([{"role": "user", "content": "hi"}])


def _ollama_reachable() -> bool:
    try:
        httpx.get(f"{_base_url()}/api/tags", timeout=2.0)
        return True
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not _ollama_reachable(), reason="ollama service not reachable")
def test_generate_reply_against_real_ollama():
    text = generate_reply("Say the single word: hello")
    assert isinstance(text, str)
    assert text


def test_reply_is_trimmed_when_the_model_writes_both_sides(monkeypatch):
    """Observed with gemma4:e2b: the model answers, then keeps going and
    hallucinates the user's next line and its own reply to it. Only the
    model's own next turn should survive."""
    runaway = (
        "¡Buen día! ¿Vives cerca de aquí?\n"
        "User: Sí, tengo una casa cerca. ¿De dónde eres?\n"
        "Assistant: Soy de Madrid."
    )

    def fake_post(url, json=None, timeout=None):
        return _FakeResponse({"message": {"content": runaway}})

    monkeypatch.setattr(httpx, "post", fake_post)

    reply = generate_reply([{"role": "user", "content": "hola"}])
    assert reply == "¡Buen día! ¿Vives cerca de aquí?"
    assert "User:" not in reply
    assert "Madrid" not in reply


def test_reply_uses_the_chat_endpoint_with_roles(monkeypatch):
    """/api/generate would make the model continue a raw transcript; /api/chat
    applies the model's own template, which closes each turn."""
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse({"message": {"content": "hola"}})

    monkeypatch.setattr(httpx, "post", fake_post)
    messages = [
        {"role": "system", "content": "be a waiter"},
        {"role": "user", "content": "hola"},
    ]
    generate_reply(messages)

    assert captured["url"].endswith("/api/chat")
    assert captured["json"]["messages"] == messages
    assert "prompt" not in captured["json"]
