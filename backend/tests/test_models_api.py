from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import settings
from app.languages import LANGUAGES
from app.main import app
from app.pipeline import llm, tts

client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path, monkeypatch):
    """Point the settings store at a temp dir and reset its in-memory copy, so
    these tests never read or write the real settings file."""
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    settings.reset_cache()
    yield
    settings.reset_cache()


def test_get_models_reports_all_three_engines():
    response = client.get("/api/models")
    assert response.status_code == 200
    body = response.json()

    assert body["stt"]["engine"] == "faster-whisper"
    assert body["stt"]["model"] in body["stt"]["options"]

    assert body["llm"]["engine"] == "Ollama"
    assert body["llm"]["model"]
    assert "installed" in body["llm"]

    assert body["tts"]["engine"] == "Piper"
    assert {v["code"] for v in body["tts"]["voices"]} == set(LANGUAGES)
    for entry in body["tts"]["voices"]:
        assert entry["voice"] in entry["options"]


def test_update_stt_model_persists_and_is_used():
    response = client.put("/api/models", json={"stt_model": "small"})
    assert response.status_code == 200
    assert response.json()["stt"]["model"] == "small"
    assert settings.get_stt_model() == "small"


def test_update_rejects_unknown_stt_model():
    response = client.put("/api/models", json={"stt_model": "enormous"})
    assert response.status_code == 400
    assert "enormous" in response.json()["detail"]
    # the rejected value must not have been applied
    assert settings.get_stt_model() != "enormous"


def test_update_llm_model_is_used_by_the_pipeline():
    client.put("/api/models", json={"llm_model": "qwen2.5:7b"})
    assert llm._model() == "qwen2.5:7b"


def test_update_rejects_blank_llm_model():
    response = client.put("/api/models", json={"llm_model": "   "})
    assert response.status_code == 400


def test_update_tts_voice_changes_the_voice_actually_used():
    default_voice = LANGUAGES["fr"].voice
    alternative = LANGUAGES["fr"].voices[1]
    assert tts._voice_for_language("fr") == default_voice

    response = client.put("/api/models", json={"tts_voices": {"fr": alternative}})
    assert response.status_code == 200
    assert tts._voice_for_language("fr") == alternative
    # other languages are untouched
    assert tts._voice_for_language("de") == LANGUAGES["de"].voice


def test_update_rejects_voice_that_does_not_belong_to_the_language():
    response = client.put(
        "/api/models", json={"tts_voices": {"fr": LANGUAGES["de"].voice}}
    )
    assert response.status_code == 400
    assert tts._voice_for_language("fr") == LANGUAGES["fr"].voice


def test_update_rejects_unknown_language():
    response = client.put("/api/models", json={"tts_voices": {"klingon": "x"}})
    assert response.status_code == 400


def test_settings_survive_a_reload_from_disk():
    client.put("/api/models", json={"stt_model": "small", "llm_model": "mistral"})

    # simulate a restart: drop the in-memory copy, re-read the file
    settings.reset_cache()

    assert settings.get_stt_model() == "small"
    assert settings.get_llm_model() == "mistral"


def test_corrupt_settings_file_falls_back_to_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text("{not valid json", encoding="utf-8")
    settings.reset_cache()

    # must not raise — a corrupt file means "no overrides", not a broken app
    assert settings.get_stt_model() in settings.STT_MODEL_SIZES


def test_installed_models_returns_empty_when_ollama_unreachable(monkeypatch):
    import httpx

    def unreachable(*args, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "get", unreachable)
    assert llm.list_installed_models() == []


def test_catalog_offers_models_including_small_gemma():
    body = client.get("/api/models").json()
    catalog = body["llm"]["catalog"]

    names = [m["name"] for m in catalog]
    assert "gemma3:1b" in names
    assert "gemma3:4b" in names
    # every entry carries what the UI needs to make an informed choice
    assert all(m["label"] and m["size_gb"] > 0 and m["note"] for m in catalog)
    # ordered smallest-first, since disk space is the real constraint
    assert [m["size_gb"] for m in catalog] == sorted(m["size_gb"] for m in catalog)


def test_pull_status_starts_idle_and_reports_state(monkeypatch):
    from app.pipeline import llm

    llm._pull_state.update(
        {"model": None, "status": "idle", "percent": 0, "error": None}
    )
    body = client.get("/api/models/llm/pull").json()
    assert body["status"] == "idle"


def test_pull_rejects_a_blank_model_name():
    assert client.post("/api/models/llm/pull", json={"model": "  "}).status_code == 400


def test_pull_starts_in_the_background_and_reports_progress(monkeypatch):
    """The endpoint must return immediately rather than blocking for the whole
    multi-GB download."""
    from app.pipeline import llm

    started = {}

    def fake_thread_target(model):
        started["model"] = model
        llm._set_pull_state(status="done", percent=100)

    monkeypatch.setattr(llm, "_run_pull", fake_thread_target)
    llm._pull_state.update(
        {"model": None, "status": "idle", "percent": 0, "error": None}
    )

    response = client.post("/api/models/llm/pull", json={"model": "gemma3:1b"})
    assert response.status_code == 200
    assert response.json()["model"] == "gemma3:1b"

    # the worker thread runs on its own; give it a moment then check it ran
    import time

    for _ in range(50):
        if started.get("model"):
            break
        time.sleep(0.02)
    assert started["model"] == "gemma3:1b"


def test_pull_refuses_a_second_concurrent_download():
    from app.pipeline import llm

    llm._pull_state.update(
        {"model": "gemma3:4b", "status": "pulling", "percent": 10, "error": None}
    )
    try:
        response = client.post("/api/models/llm/pull", json={"model": "mistral:7b"})
        assert response.status_code == 409
        assert "gemma3:4b" in response.json()["detail"]
    finally:
        llm._pull_state.update(
            {"model": None, "status": "idle", "percent": 0, "error": None}
        )


def test_catalog_includes_gemma3n_with_real_download_sizes():
    """The E2B/E4B names refer to effective inference parameters, not disk
    footprint — the catalogue must show the real download size so a 7.5 GB
    model isn't mistaken for a small one."""
    catalog = client.get("/api/models").json()["llm"]["catalog"]
    by_name = {m["name"]: m for m in catalog}

    assert by_name["gemma3n:e2b"]["size_gb"] == 5.6
    assert by_name["gemma3n:e4b"]["size_gb"] == 7.5
    # E4B really is heavier on disk than the 7B models it sits next to
    assert by_name["gemma3n:e4b"]["size_gb"] > by_name["qwen2.5:7b"]["size_gb"]


def test_models_endpoint_reports_free_disk_space():
    body = client.get("/api/models").json()
    free = body["llm"]["disk_free_gb"]
    assert free is None or free >= 0


def test_free_disk_reports_the_most_constrained_filesystem(monkeypatch):
    """A container sees the Docker VM's roomy virtual disk at "/", but that
    image lives on the host filesystem reached through the bind mount. The
    smaller number is the one that decides whether a pull can finish."""
    import shutil as shutil_mod

    from app.api import models as models_api

    fake = {
        "/": SimpleNamespace(free=46_000_000_000, total=0, used=0),
        "/data": SimpleNamespace(free=3_200_000_000, total=0, used=0),
    }
    monkeypatch.setenv("APP_DATA_DIR", "/data")
    monkeypatch.setattr(shutil_mod, "disk_usage", lambda path: fake[path])

    assert models_api._disk_free_gb() == 3.2
