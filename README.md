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

### Stopping the stack

```
docker compose down
```

Add `-v` only if you also want to delete the pulled Ollama models.
