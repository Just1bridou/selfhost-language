# Self-Hosted Voice Language Tutor

A containerized app for practicing spoken language conversations with a voice AI.
Everything — speech-to-text, the conversational model, and text-to-speech — runs
locally; no audio, transcript, or conversation data ever leaves your machine.

## Running the stack

```
docker compose up
```

This builds and starts two services:

- `backend` — the FastAPI application, served on http://localhost:8000
  (`/health` for a liveness check)
- `ollama` — the local LLM server, served on http://localhost:11434

The first run downloads the `ollama/ollama` image and builds the `backend` image
from scratch, so it will take longer than subsequent runs. `docker compose up`
again afterward reuses the cached images.

### Pulling a language model

Starting the stack does **not** download a conversational model by itself — it
only brings up the empty Ollama server. The backend defaults to `llama3.2:1b`
(overridable via the `OLLAMA_MODEL` env var), so pull that into the running
`ollama` container before starting a conversation:

```
docker compose exec ollama ollama pull llama3.2:1b
```

Pulled models are stored in a named Docker volume (`ollama-models`) and persist
across `docker compose down` / `docker compose up` cycles — you only need to pull
a given model once.

### Practice languages

Pick the language you're practicing on the main menu — the AI speaks it back
to you, and it drives the whole pipeline (the prompt, the speech-to-text
language hint, and the text-to-speech voice).

Seven languages ship by default: English, French, Spanish, German, Italian,
Portuguese, and Dutch. To add another, add an entry to
`backend/app/languages.py` with a voice name from
[the Piper voices list](https://huggingface.co/rhasspy/piper-voices). Voice
models download automatically the first time a language is used, so listing a
language you never pick costs nothing.

> **Note on model quality:** the default `llama3.2:1b` is small and its
> non-English output is noticeably rough. For serious practice in a language
> other than English, set `OLLAMA_MODEL` to something larger (and `ollama pull`
> it first).

### Stopping the stack

```
docker compose down
```

Add `-v` only if you also want to delete the pulled Ollama models.
