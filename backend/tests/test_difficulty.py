from pathlib import Path

from fastapi.testclient import TestClient

from app.difficulty import DIFFICULTIES, get_difficulty
from app.main import app
from app.pipeline import turn
from app.state import session_store

client = TestClient(app)


def _flatten(messages):
    """Prompt assertions read the whole conversation the model was
    handed, now that it is a role-tagged list rather than one string."""
    return " ".join(m["content"] for m in messages)


FIXTURE_AUDIO = Path(__file__).parent / "fixtures" / "sample_audio.wav"


def _start_session(difficulty: str = "beginner", scenario_id: str = "restaurant"):
    return client.post(
        "/api/session/start",
        json={"scenario_id": scenario_id, "language": "en", "difficulty": difficulty},
    )


def _capture_prompt(monkeypatch, session_id: str) -> str:
    prompts = []
    monkeypatch.setattr(
        turn, "transcribe", lambda audio_bytes, filename=None, language=None: "hello"
    )
    monkeypatch.setattr(turn, "synthesize", lambda text, language=None: b"fake-audio")

    def fake_generate_reply(messages):
        prompts.append(_flatten(messages))
        return "Hi there!"

    monkeypatch.setattr(turn, "generate_reply", fake_generate_reply)

    response = client.post(
        f"/api/session/{session_id}/turn",
        files={"audio": ("turn.wav", FIXTURE_AUDIO.read_bytes(), "audio/wav")},
    )
    assert response.status_code == 200
    return prompts[0]


def test_difficulties_endpoint_lists_four_levels():
    response = client.get("/api/difficulties")
    assert response.status_code == 200
    levels = response.json()

    assert len(levels) == 4
    assert [level["code"] for level in levels] == [
        "beginner",
        "elementary",
        "intermediate",
        "advanced",
    ]
    assert all(level["label"] and level["hint"] for level in levels)


def test_start_session_stores_the_chosen_difficulty():
    response = _start_session("advanced")
    assert response.status_code == 200
    body = response.json()
    assert body["difficulty"] == "advanced"
    assert session_store.get_session(body["session_id"]).difficulty == "advanced"


def test_start_session_rejects_unknown_difficulty():
    response = _start_session("impossible")
    assert response.status_code == 400
    assert "impossible" in response.json()["detail"]


def test_beginner_prompt_asks_for_the_simplest_words(monkeypatch):
    session_id = _start_session("beginner").json()["session_id"]
    prompt = _capture_prompt(monkeypatch, session_id)

    assert "beginner" in prompt.lower()
    assert "short sentences" in prompt.lower()
    assert "do not use idioms" in prompt.lower()


def test_advanced_prompt_asks_for_no_simplification(monkeypatch):
    session_id = _start_session("advanced").json()["session_id"]
    prompt = _capture_prompt(monkeypatch, session_id)

    assert "advanced" in prompt.lower()
    assert "do not simplify" in prompt.lower()


def test_each_level_produces_a_distinct_instruction(monkeypatch):
    """The whole point of the feature: a different level must actually change
    what the model is told, not just relabel the session."""
    prompts = {}
    for code in DIFFICULTIES:
        session_id = _start_session(code).json()["session_id"]
        prompts[code] = _capture_prompt(monkeypatch, session_id)

    assert len(set(prompts.values())) == len(DIFFICULTIES)


def test_get_difficulty_lookup():
    assert get_difficulty("beginner").label == "Beginner"
    assert get_difficulty("nonsense") is None
    assert get_difficulty(None) is None
