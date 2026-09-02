from fastapi.testclient import TestClient

from app.main import app
from app.state import session_store

client = TestClient(app)

EXPECTED_SCENARIO_IDS = {
    "restaurant",
    "job-interview",
    "small-talk",
    "asking-directions",
    "shopping",
}


def test_get_scenarios_returns_real_starter_set():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert {s["id"] for s in scenarios} == EXPECTED_SCENARIO_IDS
    assert all(s["target_language"] == "en" for s in scenarios)


def test_start_session_with_valid_scenario_returns_session_id():
    response = client.post("/api/session/start", json={"scenario_id": "restaurant", "language": "en", "difficulty": "beginner"})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]

    session = session_store.get_session(body["session_id"])
    assert session.scenario_id == "restaurant"
    assert session.history == []


def test_start_session_with_unknown_scenario_returns_4xx():
    response = client.post("/api/session/start", json={"scenario_id": "does-not-exist", "language": "en", "difficulty": "beginner"})
    assert 400 <= response.status_code < 500


def test_concurrent_sessions_have_independent_state():
    r1 = client.post("/api/session/start", json={"scenario_id": "restaurant", "language": "en", "difficulty": "beginner"})
    r2 = client.post("/api/session/start", json={"scenario_id": "job-interview", "language": "en", "difficulty": "beginner"})
    id1, id2 = r1.json()["session_id"], r2.json()["session_id"]
    assert id1 != id2

    s1 = session_store.get_session(id1)
    s2 = session_store.get_session(id2)
    s1.history.append({"role": "user", "text": "hi"})
    assert s2.history == []
