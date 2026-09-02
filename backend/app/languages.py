"""Registry of practice languages the app can speak.

Each entry maps an ISO-639-1 code — what Whisper expects as a language hint,
and what a session stores — to display labels and the Piper voice used to
speak it. Piper voices are language-specific, so a new language needs a voice
here, not just a prompt change.

To offer another language, add an entry with a voice name from
https://huggingface.co/rhasspy/piper-voices. Voices download lazily on first
use, so listing a language costs nothing until someone practices it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str
    label: str  # English name, used in the LLM prompt
    native_label: str  # shown in the main-menu picker
    voice: str  # Piper voice model name


LANGUAGES: dict[str, Language] = {
    "en": Language("en", "English", "English", "en_US-lessac-medium"),
    "fr": Language("fr", "French", "Français", "fr_FR-siwis-medium"),
    "es": Language("es", "Spanish", "Español", "es_ES-davefx-medium"),
    "de": Language("de", "German", "Deutsch", "de_DE-thorsten-medium"),
    "it": Language("it", "Italian", "Italiano", "it_IT-paola-medium"),
    "pt": Language("pt", "Portuguese", "Português", "pt_BR-faber-medium"),
    "nl": Language("nl", "Dutch", "Nederlands", "nl_NL-alex-medium"),
}

DEFAULT_LANGUAGE = "en"


def get_language(code: str | None) -> Language | None:
    if not code:
        return None
    return LANGUAGES.get(code)


def list_languages() -> list[Language]:
    return list(LANGUAGES.values())
