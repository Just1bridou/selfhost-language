"""Runtime-changeable model settings.

Which STT size, LLM model and TTS voices to use were originally fixed by
environment variables read at call time. They're now overridable from the UI,
so those env vars become the *defaults* and any override is persisted here.

Settings live in a JSON file under $APP_DATA_DIR (a bind-mounted directory in
compose), so a change survives `docker compose up` — otherwise switching model
would silently revert on the next restart. A missing or unreadable file simply
means "no overrides yet"; it is never fatal.
"""

import json
import os
import threading
from pathlib import Path

from app.languages import LANGUAGES

# Whisper sizes faster-whisper accepts, smallest first. Bigger transcribes
# more accurately but downloads more and runs slower on CPU.
STT_MODEL_SIZES = ("tiny", "base", "small", "medium", "large-v3")

_APP_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_DATA_DIR = _APP_DIR / "data"

_lock = threading.Lock()
_overrides: dict | None = None


def _settings_path() -> Path:
    data_dir = Path(os.environ.get("APP_DATA_DIR", str(_DEFAULT_DATA_DIR)))
    return data_dir / "settings.json"


def _defaults() -> dict:
    return {
        "stt_model": os.environ.get("STT_MODEL_SIZE", "base"),
        "llm_model": os.environ.get("OLLAMA_MODEL", "llama3.2:1b"),
        # language code -> voice name; empty means "use the language default"
        "tts_voices": {},
    }


def _load() -> dict:
    global _overrides
    if _overrides is not None:
        return _overrides

    stored = {}
    path = _settings_path()
    try:
        if path.is_file():
            stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stored = {}  # unreadable/corrupt settings must not break startup

    merged = _defaults()
    if isinstance(stored, dict):
        if isinstance(stored.get("stt_model"), str):
            merged["stt_model"] = stored["stt_model"]
        if isinstance(stored.get("llm_model"), str):
            merged["llm_model"] = stored["llm_model"]
        if isinstance(stored.get("tts_voices"), dict):
            merged["tts_voices"] = {
                code: voice
                for code, voice in stored["tts_voices"].items()
                if isinstance(voice, str)
            }

    _overrides = merged
    return _overrides


def _persist(settings: dict) -> None:
    path = _settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    except OSError:
        # A read-only or missing data dir shouldn't break the app — the change
        # still applies for this process, it just won't survive a restart.
        pass


def get_stt_model() -> str:
    return _load()["stt_model"]


def get_llm_model() -> str:
    return _load()["llm_model"]


def get_tts_voice(language_code: str | None) -> str | None:
    """The voice override for a language, or None to use its default."""
    if not language_code:
        return None
    return _load()["tts_voices"].get(language_code)


def as_dict() -> dict:
    settings = _load()
    return {
        "stt_model": settings["stt_model"],
        "llm_model": settings["llm_model"],
        "tts_voices": dict(settings["tts_voices"]),
    }


class InvalidSetting(ValueError):
    """Raised when an update is rejected for an unsupported value."""


def update(
    stt_model: str | None = None,
    llm_model: str | None = None,
    tts_voices: dict | None = None,
) -> dict:
    """Apply and persist a partial settings update. Only known STT sizes and
    voices the language registry actually offers are accepted, so a bad value
    can't wedge the pipeline into never producing audio again."""
    with _lock:
        settings = dict(_load())
        settings["tts_voices"] = dict(settings["tts_voices"])

        if stt_model is not None:
            if stt_model not in STT_MODEL_SIZES:
                raise InvalidSetting(f"unsupported speech-to-text model: {stt_model!r}")
            settings["stt_model"] = stt_model

        if llm_model is not None:
            if not llm_model.strip():
                raise InvalidSetting("language model name cannot be empty")
            settings["llm_model"] = llm_model.strip()

        if tts_voices is not None:
            for code, voice in tts_voices.items():
                language = LANGUAGES.get(code)
                if language is None:
                    raise InvalidSetting(f"unknown language: {code!r}")
                if voice not in language.voices:
                    raise InvalidSetting(
                        f"voice {voice!r} is not available for {language.label}"
                    )
                settings["tts_voices"][code] = voice

        global _overrides
        _overrides = settings
        _persist(settings)
        return as_dict()


def reset_cache() -> None:
    """Drop the in-memory copy so the next read re-reads from disk (tests)."""
    global _overrides
    _overrides = None
