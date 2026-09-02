from dataclasses import dataclass

from app.difficulty import get_difficulty
from app.languages import get_language
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


def _compose_messages(
    scenario,
    history: list[dict],
    user_text: str,
    language_code: str,
    difficulty_code: str,
) -> list[dict]:
    """Build a role-tagged message list for Ollama's /api/chat.

    Prior turns are replayed as real `user`/`assistant` messages rather than
    being flattened into one "User: ... Assistant: ..." string. Besides being
    what the chat endpoint expects, it means the model can tell its own past
    turns from the user's, and its chat template closes each turn properly
    instead of inviting it to write the next one itself.
    """
    language = get_language(language_code)
    language_label = language.label if language else language_code
    difficulty = get_difficulty(difficulty_code)

    system = [
        "You are roleplaying a character for a language-practice conversation. "
        f"Speak only {language_label}, even if the user says something in "
        "another language, and stay in character for the entire conversation.",
        f"Persona: {scenario.persona_prompt}",
        f"Goal: {scenario.goal}",
    ]
    if difficulty:
        system.append(f"Level: {difficulty.prompt_instruction}")
    system.append(
        "Reply with your character's next line only. Never write the user's "
        "side of the conversation and never label speakers."
    )

    messages = [{"role": "system", "content": "\n".join(system)}]
    for turn in history:
        messages.append({"role": "user", "content": turn["user_text"]})
        messages.append({"role": "assistant", "content": turn["ai_text"]})
    messages.append({"role": "user", "content": user_text})
    return messages


def run_turn(session_id: str, audio_bytes: bytes, filename: str | None = None) -> TurnResult:
    """Run one full conversation turn: STT -> scenario-aware LLM -> TTS.

    `filename` is passed through to `transcribe()` as a format hint (see its
    docstring) and is not otherwise significant.

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
        user_text = transcribe(audio_bytes, filename=filename, language=session.language)
    except TranscriptionError as exc:
        raise TurnError(f"speech-to-text failed: {exc}", status_code=502) from exc

    messages = _compose_messages(
        scenario, session.history, user_text, session.language, session.difficulty
    )

    try:
        ai_text = generate_reply(messages)
    except LLMError as exc:
        raise TurnError(f"language model failed: {exc}", status_code=502) from exc

    try:
        audio_reply = synthesize(ai_text, language=session.language)
    except SynthesisError as exc:
        raise TurnError(f"text-to-speech failed: {exc}", status_code=502) from exc

    session.history.append({"user_text": user_text, "ai_text": ai_text})

    return TurnResult(user_text=user_text, ai_text=ai_text, audio_bytes=audio_reply)
