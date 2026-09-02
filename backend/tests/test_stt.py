from pathlib import Path
from types import SimpleNamespace

import pytest

from app.pipeline import stt
from app.pipeline.stt import TranscriptionError, transcribe

FIXTURE_AUDIO = Path(__file__).parent / "fixtures" / "sample_audio.wav"


class _StubSegment:
    def __init__(self, text: str):
        self.text = text


class _StubModel:
    def transcribe(self, path, language=None):
        return [_StubSegment(" hello "), _StubSegment(" world ")], SimpleNamespace(language="en")


class _BrokenModel:
    def transcribe(self, path, language=None):
        raise RuntimeError("cannot decode audio")


def test_transcribe_raises_on_empty_audio():
    with pytest.raises(TranscriptionError):
        transcribe(b"")


def test_transcribe_joins_segments_from_model(monkeypatch):
    monkeypatch.setattr(stt, "_get_model", lambda: _StubModel())
    assert transcribe(b"fake-wav-bytes") == "hello world"


def test_transcribe_raises_on_decode_failure(monkeypatch):
    monkeypatch.setattr(stt, "_get_model", lambda: _BrokenModel())
    with pytest.raises(TranscriptionError):
        transcribe(b"not-real-audio-but-not-empty")


def test_transcribe_does_not_use_network(monkeypatch):
    """AC#5: no outbound network call during transcription itself (model
    loading/download is a separate one-time setup step, analogous to
    `ollama pull` for the LLM)."""
    import socket

    monkeypatch.setattr(stt, "_get_model", lambda: _StubModel())

    def _blocked(*args, **kwargs):
        raise AssertionError("transcribe() must not open network sockets")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    assert transcribe(b"fake-wav-bytes") == "hello world"


@pytest.mark.skipif(not FIXTURE_AUDIO.exists(), reason="fixture audio not present")
def test_transcribe_real_audio_matches_expected_content():
    audio_bytes = FIXTURE_AUDIO.read_bytes()
    text = transcribe(audio_bytes).lower()
    assert "hello" in text
    assert "world" in text


def test_transcribe_uses_filename_extension_as_decode_hint(monkeypatch):
    """A browser MediaRecorder blob is rarely actually WAV (webm/opus, ogg,
    mp4...); the temp file's suffix should match so the decoder's format
    probing has an accurate hint instead of always claiming .wav."""
    seen_paths = []

    class _RecordingModel:
        def transcribe(self, path, language=None):
            seen_paths.append(path)
            return [_StubSegment("ok")], SimpleNamespace(language="en")

    monkeypatch.setattr(stt, "_get_model", lambda: _RecordingModel())

    transcribe(b"fake-webm-bytes", filename="turn.webm")
    assert seen_paths[-1].endswith(".webm")

    transcribe(b"fake-ogg-bytes", filename="turn.ogg")
    assert seen_paths[-1].endswith(".ogg")

    transcribe(b"fake-bytes", filename=None)
    assert seen_paths[-1].endswith(".wav")

    transcribe(b"fake-bytes", filename="no-extension")
    assert seen_paths[-1].endswith(".wav")
