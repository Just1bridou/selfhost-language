"""Registry of practice languages the app can speak.

Each entry maps an ISO-639-1 code — what Whisper expects as a language hint,
and what a session stores — to display labels and the Piper voices that can
speak it. Piper voices are language-specific, so a new language needs voices
here, not just a prompt change.

`voices` lists the selectable voices for a language, best-default first. They
are curated on purpose rather than fetched from the Piper index at runtime, so
the app stays usable offline. To offer another, add a name from
https://huggingface.co/rhasspy/piper-voices — voices download lazily on first
use, so listing one costs nothing until someone picks it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str
    label: str  # English name, used in the LLM prompt
    native_label: str  # shown in the main-menu picker
    voices: tuple[str, ...]  # selectable Piper voices, default first

    @property
    def voice(self) -> str:
        """The default voice for this language."""
        return self.voices[0]


LANGUAGES: dict[str, Language] = {
    "en": Language(
        "en",
        "English",
        "English",
        ("en_US-lessac-medium", "en_US-amy-medium", "en_US-hfc_male-medium"),
    ),
    "fr": Language(
        "fr",
        "French",
        "Français",
        ("fr_FR-siwis-medium", "fr_FR-tom-medium", "fr_FR-upmc-medium"),
    ),
    "es": Language(
        "es",
        "Spanish",
        "Español",
        ("es_ES-davefx-medium", "es_ES-sharvard-medium"),
    ),
    "de": Language(
        "de",
        "German",
        "Deutsch",
        ("de_DE-thorsten-medium", "de_DE-thorsten-high", "de_DE-mls-medium"),
    ),
    "it": Language(
        "it",
        "Italian",
        "Italiano",
        ("it_IT-paola-medium", "it_IT-serena-medium"),
    ),
    "pt": Language(
        "pt",
        "Portuguese",
        "Português",
        ("pt_BR-faber-medium", "pt_BR-cadu-medium", "pt_BR-jeff-medium"),
    ),
    "nl": Language(
        "nl",
        "Dutch",
        "Nederlands",
        ("nl_NL-alex-medium", "nl_NL-pim-medium", "nl_NL-ronnie-medium"),
    ),
}

DEFAULT_LANGUAGE = "en"


def get_language(code: str | None) -> Language | None:
    if not code:
        return None
    return LANGUAGES.get(code)


def list_languages() -> list[Language]:
    return list(LANGUAGES.values())
