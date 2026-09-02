import os
import tempfile
from functools import lru_cache


class TranscriptionError(Exception):
    """Raised when audio cannot be transcribed."""


@lru_cache(maxsize=1)
def _get_model():
    from faster_whisper import WhisperModel

    model_size = os.environ.get("STT_MODEL_SIZE", "base")
    compute_type = os.environ.get("STT_COMPUTE_TYPE", "int8")
    return WhisperModel(model_size, device="cpu", compute_type=compute_type)


def transcribe(audio_bytes: bytes) -> str:
    """Transcribe `audio_bytes` to text entirely locally via faster-whisper.

    Raises TranscriptionError for empty input or audio that cannot be decoded.
    A valid recording containing no speech (e.g. silence) is not an error and
    may return an empty string.
    """
    if not audio_bytes:
        raise TranscriptionError("audio_bytes is empty")

    model = _get_model()

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file.flush()
        try:
            segments, _info = model.transcribe(tmp_file.name)
            return " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:
            raise TranscriptionError(f"failed to transcribe audio: {exc}") from exc
