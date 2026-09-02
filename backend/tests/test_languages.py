from fastapi.testclient import TestClient

from app.languages import DEFAULT_LANGUAGE, LANGUAGES, get_language
from app.main import app
from app.pipeline import tts, turn
from app.pipeline.tts import _voice_for_language
from app.state import session_store

client = TestClient(app)


def _flatten(messages):
    """Prompt assertions read the whole conversation the model was
    handed, now that it is a role-tagged list rather than one string."""
    return " ".join(m["content"] for m in messages)


def _start_session(scenario_id: str = "restaurant", language: str = "fr"):
    return client.post(
        "/api/session/start",
        json={"scenario_id": scenario_id, "language": language, "difficulty": "beginner"},
    )


def test_languages_endpoint_lists_supported_languages():
    response = client.get("/api/languages")
    assert response.status_code == 200
    languages = response.json()

    assert {lang["code"] for lang in languages} == set(LANGUAGES)
    assert all(lang["label"] and lang["native_label"] for lang in languages)

    french = next(lang for lang in languages if lang["code"] == "fr")
    assert french["label"] == "French"
    assert french["native_label"] == "Français"


def test_start_session_stores_the_chosen_language():
    response = _start_session(language="fr")
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "fr"
    assert session_store.get_session(body["session_id"]).language == "fr"


def test_start_session_rejects_unsupported_language():
    response = _start_session(language="klingon")
    assert 400 <= response.status_code < 500
    assert "klingon" in response.json()["detail"]


def test_start_session_requires_a_language_and_difficulty():
    assert client.post(
        "/api/session/start",
        json={"scenario_id": "restaurant", "difficulty": "beginner"},
    ).status_code == 422
    assert client.post(
        "/api/session/start", json={"scenario_id": "restaurant", "language": "fr"}
    ).status_code == 422


def test_prompt_instructs_the_ai_to_speak_the_session_language(monkeypatch):
    prompts = []

    monkeypatch.setattr(
        turn, "transcribe", lambda audio_bytes, filename=None, language=None: "bonjour"
    )
    monkeypatch.setattr(turn, "synthesize", lambda text, language=None: b"fake-audio")

    def fake_generate_reply(messages):
        prompts.append(_flatten(messages))
        return "Bonjour !"

    monkeypatch.setattr(turn, "generate_reply", fake_generate_reply)

    session_id = _start_session(language="fr").json()["session_id"]
    from pathlib import Path

    audio = (Path(__file__).parent / "fixtures" / "sample_audio.wav").read_bytes()
    response = client.post(
        f"/api/session/{session_id}/turn",
        files={"audio": ("turn.wav", audio, "audio/wav")},
    )

    assert response.status_code == 200
    assert "French" in prompts[0]
    # The scenario file's own target_language ("en") must not win over the
    # language the user actually chose for this session.
    assert "English" not in prompts[0]


def test_turn_passes_session_language_to_stt_and_tts(monkeypatch):
    seen = {}

    def fake_transcribe(audio_bytes, filename=None, language=None):
        seen["stt_language"] = language
        return "bonjour"

    def fake_synthesize(text, language=None):
        seen["tts_language"] = language
        return b"fake-audio"

    monkeypatch.setattr(turn, "transcribe", fake_transcribe)
    monkeypatch.setattr(turn, "generate_reply", lambda messages: "Bonjour !")
    monkeypatch.setattr(turn, "synthesize", fake_synthesize)

    session_id = _start_session(language="fr").json()["session_id"]
    from pathlib import Path

    audio = (Path(__file__).parent / "fixtures" / "sample_audio.wav").read_bytes()
    client.post(
        f"/api/session/{session_id}/turn",
        files={"audio": ("turn.wav", audio, "audio/wav")},
    )

    assert seen["stt_language"] == "fr"
    assert seen["tts_language"] == "fr"


def test_each_language_resolves_a_distinct_voice():
    voices = {code: _voice_for_language(code) for code in LANGUAGES}
    assert len(set(voices.values())) == len(LANGUAGES)
    assert _voice_for_language("fr").startswith("fr_")
    assert _voice_for_language("de").startswith("de_")


def test_unknown_language_falls_back_to_the_default_voice():
    assert _voice_for_language(None) == LANGUAGES[DEFAULT_LANGUAGE].voice
    assert _voice_for_language("klingon") == LANGUAGES[DEFAULT_LANGUAGE].voice


def test_get_language_lookup():
    assert get_language("fr").label == "French"
    assert get_language("klingon") is None
    assert get_language(None) is None


def test_voice_cache_is_keyed_per_voice(monkeypatch):
    """Switching languages must not evict/reuse another language's voice."""
    loaded = []

    class _StubVoice:
        def __init__(self, name):
            self.name = name

    def fake_load(voice_name):
        loaded.append(voice_name)
        return _StubVoice(voice_name)

    tts._get_voice.cache_clear()
    monkeypatch.setattr(tts, "_get_voice", fake_load)

    assert tts._get_voice(_voice_for_language("fr")).name.startswith("fr_")
    assert tts._get_voice(_voice_for_language("en")).name.startswith("en_")
    assert len(set(loaded)) == 2
