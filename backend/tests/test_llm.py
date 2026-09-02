import httpx
import pytest

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
        return _FakeResponse({"response": "  hello there  "})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert generate_reply("hi") == "hello there"


def test_generate_reply_uses_configured_url_and_model(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse({"response": "ok"})

    monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom-host:9999")
    monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
    monkeypatch.setattr(httpx, "post", fake_post)

    generate_reply("hi")

    assert captured["url"] == "http://custom-host:9999/api/generate"
    assert captured["json"]["model"] == "custom-model"


def test_generate_reply_raises_on_connection_error(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMError):
        generate_reply("hi")


def test_generate_reply_raises_on_timeout(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMError):
        generate_reply("hi")


def test_generate_reply_raises_on_malformed_response(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        return _FakeResponse({"unexpected": "shape"})

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMError):
        generate_reply("hi")


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
