"""Curated catalogue of local LLMs worth using for language practice.

Only models that exist in the Ollama library are listed (each tag here was
checked against registry.ollama.ai). They're ordered smallest-first, since
disk space and CPU speed are the real constraints on a self-hosted box.

`multilingual` flags the ones that hold up reasonably outside English — the
1B-class models are usable for English practice but produce clumsy French,
Spanish and German, so the UI can steer people toward a bigger model when
they're practicing something else.

`size_gb` is the real download size, summed from each tag's registry
manifest. That matters most for Gemma 4's "E" variants: E2B/E4B name the
*effective* parameters used at inference (Per-Layer Embeddings keep the memory
footprint down), not what they occupy on disk. It is genuinely counter-
intuitive — `gemma4:e4b` stores 9.6 GB, more than the denser `gemma4:12b` at
7.6 GB — so the size shown here is measured, never inferred from the name.

Gemma 4 supersedes the Gemma 3n line, so only the current generation of the
on-device family is listed; the 26B and 31B Gemma 4 tags are omitted as
impractical (18-20 GB) for the CPU-only box this project targets.
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
        "gemma4:e2b",
        "Gemma 4 · E2B",
        7.2,
        True,
        "Newest on-device Gemma: runs like a 2B model but stores 7.2 GB.",
    ),
    CatalogModel(
        "gemma4:12b",
        "Gemma 4 · 12B",
        7.6,
        True,
        "Denser than E4B and smaller on disk, but needs far more memory to run.",
    ),
    CatalogModel(
        "gemma4:e4b",
        "Gemma 4 · E4B",
        9.6,
        True,
        "Most capable on-device Gemma 4. Runs like a 4B model, stores 9.6 GB.",
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
