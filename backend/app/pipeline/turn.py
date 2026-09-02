from dataclasses import dataclass

from app.pipeline.llm import LLMError, generate_reply
from app.pipeline.stt import TranscriptionError, transcribe
from app.pipeline.tts import SynthesisError, synthesize
from app.scenarios.loader import get_scenario
from app.state.session_store import SessionNotFoundError, get_session


class TurnError(Exception):
    """Raised when a conversation turn cannot be completed."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class TurnResult:
    user_text: str
    ai_text: str
    audio_bytes: bytes


def _compose_prompt(scenario, history: list[dict], user_text: str) -> str:
    lines = [
        "You are roleplaying a character for a language-practice conversation. "
        "Stay in character for the entire conversation and respond only in "
        f"{scenario.target_language}.",
        f"Persona: {scenario.persona_prompt}",
        f"Goal: {scenario.goal}",
        "",
    ]
    for turn in history:
        lines.append(f"User: {turn['user_text']}")
        lines.append(f"Assistant: {turn['ai_text']}")
    lines.append(f"User: {user_text}")
    lines.append("Assistant:")
    return "\n".join(lines)


def run_turn(session_id: str, audio_bytes: bytes) -> TurnResult:
    """Run one full conversation turn: STT -> scenario-aware LLM -> TTS.

    Raises TurnError (with a status_code hint) for a missing session or a
    failure at any pipeline stage. On any failure, session.history is left
    unchanged rather than holding a partial turn.
    """
    try:
        session = get_session(session_id)
    except SessionNotFoundError as exc:
        raise TurnError(str(exc), status_code=404) from exc

    scenario = get_scenario(session.scenario_id)
    if scenario is None:
        raise TurnError(
            f"scenario {session.scenario_id!r} for this session no longer exists",
            status_code=404,
        )

    try:
        user_text = transcribe(audio_bytes)
    except TranscriptionError as exc:
        raise TurnError(f"speech-to-text failed: {exc}", status_code=502) from exc

    prompt = _compose_prompt(scenario, session.history, user_text)

    try:
        ai_text = generate_reply(prompt)
    except LLMError as exc:
        raise TurnError(f"language model failed: {exc}", status_code=502) from exc

    try:
        audio_reply = synthesize(ai_text)
    except SynthesisError as exc:
        raise TurnError(f"text-to-speech failed: {exc}", status_code=502) from exc

    session.history.append({"user_text": user_text, "ai_text": ai_text})

    return TurnResult(user_text=user_text, ai_text=ai_text, audio_bytes=audio_reply)
