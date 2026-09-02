from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import turn
from app.pipeline.llm import LLMError, _base_url
from app.pipeline.stt import TranscriptionError
from app.pipeline.tts import SynthesisError
from app.state import session_store

client = TestClient(app)
FIXTURE_AUDIO = Path(__file__).parent / "fixtures" / "sample_audio.wav"


def _start_session(scenario_id: str = "restaurant") -> str:
    response = client.post("/api/session/start", json={"scenario_id": scenario_id})
    assert response.status_code == 200
    return response.json()["session_id"]


def _submit_turn(session_id: str):
    audio_bytes = FIXTURE_AUDIO.read_bytes()
    return client.post(
        f"/api/session/{session_id}/turn",
        files={"audio": ("turn.wav", audio_bytes, "audio/wav")},
    )


def test_turn_full_flow_returns_transcript_reply_and_audio(monkeypatch):
    captured_prompts = []

    monkeypatch.setattr(turn, "transcribe", lambda audio_bytes: "hello there")

    def fake_generate_reply(prompt):
        captured_prompts.append(prompt)
        return "Welcome! What would you like to order?"

    monkeypatch.setattr(turn, "generate_reply", fake_generate_reply)
    monkeypatch.setattr(turn, "synthesize", lambda text: b"RIFF-fake-wav-bytes")

    session_id = _start_session("restaurant")
    response = _submit_turn(session_id)

    assert response.status_code == 200
    body = response.json()
    assert body["user_text"] == "hello there"
    assert body["ai_text"] == "Welcome! What would you like to order?"
    assert body["audio_base64"]

    # AC#2: the prompt includes the scenario's actual persona/goal, not a generic one
    assert "waiter" in captured_prompts[0].lower()
    assert "starter" in captured_prompts[0].lower()

    # AC#4: the completed turn is appended to session history
    session = session_store.get_session(session_id)
    assert session.history == [{"user_text": "hello there", "ai_text": "Welcome! What would you like to order?"}]


def test_turn_prompt_includes_growing_history(monkeypatch):
    monkeypatch.setattr(turn, "transcribe", lambda audio_bytes: "hi")
    prompts = []

    def fake_generate_reply(prompt):
        prompts.append(prompt)
        return f"reply-{len(prompts)}"

    monkeypatch.setattr(turn, "generate_reply", fake_generate_reply)
    monkeypatch.setattr(turn, "synthesize", lambda text: b"fake-audio")

    session_id = _start_session("small-talk")
    _submit_turn(session_id)
    _submit_turn(session_id)

    assert len(prompts) == 2
    assert "reply-1" in prompts[1]
    session = session_store.get_session(session_id)
    assert len(session.history) == 2
    assert session.history[0]["ai_text"] == "reply-1"
    assert session.history[1]["ai_text"] == "reply-2"


def test_turn_missing_session_returns_404():
    response = _submit_turn("does-not-exist")
    assert response.status_code == 404


def test_turn_stt_failure_returns_clear_error_and_leaves_history_untouched(monkeypatch):
    def broken_transcribe(audio_bytes):
        raise TranscriptionError("audio_bytes is empty")

    monkeypatch.setattr(turn, "transcribe", broken_transcribe)
    session_id = _start_session()

    response = _submit_turn(session_id)

    assert response.status_code >= 400
    assert "speech-to-text" in response.json()["detail"].lower()
    assert session_store.get_session(session_id).history == []


def test_turn_llm_failure_returns_clear_error_and_leaves_history_untouched(monkeypatch):
    monkeypatch.setattr(turn, "transcribe", lambda audio_bytes: "hi")

    def broken_generate_reply(prompt):
        raise LLMError("ollama unreachable")

    monkeypatch.setattr(turn, "generate_reply", broken_generate_reply)
    session_id = _start_session()

    response = _submit_turn(session_id)

    assert response.status_code >= 400
    assert "language model" in response.json()["detail"].lower()
    assert session_store.get_session(session_id).history == []


def test_turn_tts_failure_returns_clear_error_and_leaves_history_untouched(monkeypatch):
    monkeypatch.setattr(turn, "transcribe", lambda audio_bytes: "hi")
    monkeypatch.setattr(turn, "generate_reply", lambda prompt: "a reply")

    def broken_synthesize(text):
        raise SynthesisError("voice unavailable")

    monkeypatch.setattr(turn, "synthesize", broken_synthesize)
    session_id = _start_session()

    response = _submit_turn(session_id)

    assert response.status_code >= 400
    assert "text-to-speech" in response.json()["detail"].lower()
    assert session_store.get_session(session_id).history == []


def _ollama_reachable() -> bool:
    try:
        httpx.get(f"{_base_url()}/api/tags", timeout=2.0)
        return True
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not _ollama_reachable(), reason="ollama service not reachable")
def test_turn_real_end_to_end():
    session_id = _start_session("small-talk")

    response = _submit_turn(session_id)

    assert response.status_code == 200
    body = response.json()
    text = body["user_text"].lower()
    assert "hello" in text or "world" in text
    assert body["ai_text"]
    assert body["audio_base64"]
    assert session_store.get_session(session_id).history
