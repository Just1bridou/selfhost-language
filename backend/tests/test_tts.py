import socket

import pytest

from app.pipeline import tts
from app.pipeline.tts import SynthesisError, synthesize


class _StubVoice:
    def synthesize_wav(self, text, wav_file):
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 100)


class _BrokenVoice:
    def synthesize_wav(self, text, wav_file):
        raise RuntimeError("synthesis backend crashed")


def test_synthesize_raises_on_empty_text():
    with pytest.raises(SynthesisError):
        synthesize("")


def test_synthesize_raises_on_whitespace_only_text():
    with pytest.raises(SynthesisError):
        synthesize("   ")


def test_synthesize_returns_valid_wav_bytes(monkeypatch):
    monkeypatch.setattr(tts, "_get_voice", lambda voice_name=None: _StubVoice())
    audio = synthesize("hello world")
    assert audio[:4] == b"RIFF"
    assert audio[8:12] == b"WAVE"
    assert len(audio) > 44


def test_synthesize_raises_on_backend_failure(monkeypatch):
    monkeypatch.setattr(tts, "_get_voice", lambda voice_name=None: _BrokenVoice())
    with pytest.raises(SynthesisError):
        synthesize("hello")


def test_synthesize_does_not_use_network(monkeypatch):
    monkeypatch.setattr(tts, "_get_voice", lambda voice_name=None: _StubVoice())

    def _blocked(*args, **kwargs):
        raise AssertionError("synthesize() must not open network sockets")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    audio = synthesize("hello world")
    assert audio[:4] == b"RIFF"


def test_synthesize_real_voice_produces_playable_audio():
    audio = synthesize("Hello world, this is a test.")
    assert audio[:4] == b"RIFF"
    assert audio[8:12] == b"WAVE"
    assert len(audio) > 1000
