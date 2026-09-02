"""Curated catalogue of local LLMs worth using for language practice.

Only models that exist in the Ollama library are listed (each tag here was
checked against registry.ollama.ai). They're ordered smallest-first, since
disk space and CPU speed are the real constraints on a self-hosted box.

`multilingual` flags the ones that hold up reasonably outside English — the
1B-class models are usable for English practice but produce clumsy French,
Spanish and German, so the UI can steer people toward a bigger model when
they're practicing something else.

`size_gb` is the real download size, summed from each tag's registry
manifest. That matters most for the Gemma 3n entries: their "E2B"/"E4B"
names refer to the *effective* parameters used at inference (Per-Layer
Embeddings keep the memory footprint down), not to what they occupy on disk —
E4B stores 7.5 GB, more than any 7B model here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogModel:
    name: str
    label: str
    size_gb: float
    multilingual: bool
    note: str


CATALOG: tuple[CatalogModel, ...] = (
    CatalogModel(
        "gemma3:1b",
        "Gemma 3 · 1B",
        0.8,
        False,
        "Smallest and fastest. Fine for English practice, weak elsewhere.",
    ),
    CatalogModel(
        "llama3.2:1b",
        "Llama 3.2 · 1B",
        1.3,
        False,
        "Fast default. Understands several languages but speaks them clumsily.",
    ),
    CatalogModel(
        "gemma2:2b",
        "Gemma 2 · 2B",
        1.6,
        True,
        "A good step up while staying small.",
    ),
    CatalogModel(
        "qwen2.5:3b",
        "Qwen 2.5 · 3B",
        1.9,
        True,
        "Strong multilingual quality for its size.",
    ),
    CatalogModel(
        "llama3.2:3b",
        "Llama 3.2 · 3B",
        2.0,
        True,
        "Noticeably more natural than the 1B version.",
    ),
    CatalogModel(
        "gemma3:4b",
        "Gemma 3 · 4B",
        3.3,
        True,
        "Recommended for non-English practice if you have the disk space.",
    ),
    CatalogModel(
        "mistral:7b",
        "Mistral · 7B",
        4.1,
        True,
        "Very good French in particular. Slow on CPU-only machines.",
    ),
    CatalogModel(
        "qwen2.5:7b",
        "Qwen 2.5 · 7B",
        4.7,
        True,
        "Excellent multilingual quality, but heavy to run.",
    ),
    CatalogModel(
        "gemma3n:e2b",
        "Gemma 3n · E2B",
        5.6,
        True,
        "Built for on-device use: runs like a 2B model but stores 5.6 GB.",
    ),
    CatalogModel(
        "gemma3n:e4b",
        "Gemma 3n · E4B",
        7.5,
        True,
        "Same family, more capable. Runs like a 4B model but stores 7.5 GB.",
    ),
)


def as_dicts() -> list[dict]:
    return [
        {
            "name": model.name,
            "label": model.label,
            "size_gb": model.size_gb,
            "multilingual": model.multilingual,
            "note": model.note,
        }
        for model in CATALOG
    ]
