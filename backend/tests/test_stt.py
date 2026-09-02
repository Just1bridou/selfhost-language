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
    def transcribe(self, path):
        return [_StubSegment(" hello "), _StubSegment(" world ")], SimpleNamespace(language="en")


class _BrokenModel:
    def transcribe(self, path):
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
