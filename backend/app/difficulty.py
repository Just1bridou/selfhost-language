"""Practice difficulty levels.

The scenario files carry their own `difficulty` field, but it was only ever
metadata shown on a card — it never reached the model. These levels are the
user's own choice for a session, and each one carries a `prompt_instruction`
that is injected into the LLM prompt, so picking a lower level genuinely makes
the AI speak with simpler words rather than just relabelling the session.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Difficulty:
    code: str
    label: str
    hint: str  # short description shown in the picker
    prompt_instruction: str


DIFFICULTIES: dict[str, Difficulty] = {
    "beginner": Difficulty(
        "beginner",
        "Beginner",
        "A1 — the simplest words, very short sentences",
        "The user is a beginner. Use only the most common everyday words and "
        "very short sentences of roughly five to eight words. Stay in the "
        "present tense almost all the time. Do not use idioms, slang, phrasal "
        "verbs or subordinate clauses. If the user seems lost, rephrase more "
        "simply rather than adding detail.",
    ),
    "elementary": Difficulty(
        "elementary",
        "Elementary",
        "A2 — simple everyday vocabulary",
        "The user has an elementary level. Use simple, common vocabulary and "
        "sentences of roughly eight to twelve words. Keep to everyday tenses "
        "and simple connectors such as 'and', 'but' and 'because'. Avoid "
        "idioms, slang and rare words.",
    ),
    "intermediate": Difficulty(
        "intermediate",
        "Intermediate",
        "B1–B2 — natural, everyday speech",
        "The user has an intermediate level. Speak naturally with everyday "
        "vocabulary and normal sentence length. Common idioms and a range of "
        "tenses are fine. Do not deliberately simplify, but avoid rare, "
        "literary or technical words.",
    ),
    "advanced": Difficulty(
        "advanced",
        "Advanced",
        "C1+ — rich vocabulary, idioms, native pace",
        "The user is advanced. Speak as you would to a fluent adult native "
        "speaker: precise and varied vocabulary, idiomatic expressions, "
        "nuance and complex sentences are all welcome. Do not simplify.",
    ),
}

DEFAULT_DIFFICULTY = "beginner"


def get_difficulty(code: str | None) -> Difficulty | None:
    if not code:
        return None
    return DIFFICULTIES.get(code)


def list_difficulties() -> list[Difficulty]:
    return list(DIFFICULTIES.values())
