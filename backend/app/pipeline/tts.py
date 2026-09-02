import io
import os
import wave
from functools import lru_cache
from pathlib import Path

from app.languages import DEFAULT_LANGUAGE, LANGUAGES, get_language


class SynthesisError(Exception):
    """Raised when text cannot be synthesized to audio."""


_APP_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_VOICE_DIR = _APP_DIR / "voices"


def _voice_for_language(code: str | None) -> str:
    """Resolve the Piper voice for a practice language.

    Falls back to $TTS_VOICE (or the default language's voice) when no
    language is given, preserving the single-voice behavior this module had
    before multi-language support.
    """
    language = get_language(code)
    if language:
        return language.voice
    return os.environ.get("TTS_VOICE", LANGUAGES[DEFAULT_LANGUAGE].voice)


def _voice_dir() -> Path:
    return Path(os.environ.get("TTS_VOICE_DIR", str(_DEFAULT_VOICE_DIR)))


@lru_cache(maxsize=len(LANGUAGES) + 1)
def _get_voice(voice_name: str):
    """Load (downloading on first use) one Piper voice, cached per voice so
    switching languages between sessions doesn't reload an already-used one."""
    from piper import PiperVoice
    from piper.download_voices import download_voice

    voice_dir = _voice_dir()
    voice_dir.mkdir(parents=True, exist_ok=True)

    model_path = voice_dir / f"{voice_name}.onnx"
    if not model_path.exists():
        download_voice(voice_name, voice_dir)

    return PiperVoice.load(str(model_path))


def synthesize(text: str, language: str | None = None) -> bytes:
    """Synthesize `text` to WAV audio bytes entirely locally via Piper, using
    the voice for `language` (defaulting to the configured/English voice).

    Raises SynthesisError for empty/whitespace-only input or if the
    underlying synthesis backend fails.
    """
    if not text or not text.strip():
        raise SynthesisError("text is empty")

    voice = _get_voice(_voice_for_language(language))

    buffer = io.BytesIO()
    try:
        with wave.open(buffer, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
    except Exception as exc:
        raise SynthesisError(f"failed to synthesize audio: {exc}") from exc

    audio_bytes = buffer.getvalue()
    if not audio_bytes:
        raise SynthesisError("synthesis produced no audio")

    return audio_bytes
