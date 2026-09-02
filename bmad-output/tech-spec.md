# Technical Specification: Self-Hosted Voice Language Tutor

**Date:** 2026-09-02
**Author:** Justin Anthoine-Milhomme (solo builder)
**Version:** 1.0
**Track:** Quick Flow (1-15 stories)
**Status:** Draft

> **Quick Flow track** — this document replaces a separate PRD and architecture file for
> small-scope work. If scope grows beyond ~15 stories, migrate to the BMad Method track
> (bmad-prd + bmad-architecture) before continuing.

---

## Related Documents

- Project context: `bmad-output/project-context.md`
- Decision log: `bmad-output/decision-log.md`

---

## Problem & Solution

### Problem Statement

Practicing spoken conversation in a foreign language usually requires either a human
partner (scheduling friction, cost) or a cloud-based AI service (recurring cost,
privacy exposure of voice data, requires network access). There is no low-friction,
private, self-hosted way to rehearse realistic spoken scenarios on demand.

### Proposed Solution

A containerized application that lets the user talk out loud with a voice AI to
practice a target language across multiple selectable conversation scenarios (e.g.
ordering food, a job interview, small talk). The entire pipeline — speech-to-text,
the conversational model, and text-to-speech — runs locally on the user's own
hardware via Docker, with no calls to external AI APIs at runtime.

### Goals

- Let the user hold a spoken, scenario-driven conversation with a local AI in a
  target language.
- Keep 100% of AI inference on-device; no audio or transcript ever leaves the
  machine.
- Ship as a small number of Docker Compose services the user can run with one
  command.

---

## Scope

### In Scope

- Docker Compose stack: web UI, backend orchestrator, local STT, local LLM, local
  TTS.
- Push-to-talk voice conversation loop (record → transcribe → generate reply →
  speak reply).
- A small library of built-in, config-driven scenarios (3-5 to start).
- Scenario picker and live transcript in the web UI.
- One target language for the initial release, with the scenario/model
  configuration structured so more languages can be added later.

### Out of Scope

- Multi-user accounts, auth, or multi-tenant hosting.
- Mobile or native desktop client (web UI only).
- Cloud deployment/hosting story (self-hosted/local only).
- Visual avatar or video — audio-only interaction.
- Real-time (sub-second, continuously streaming) speech; MVP uses push-to-talk
  turns, not live barge-in conversation.

---

## Requirements

### Functional Requirements

#### FR-001: Start a scenario session [MUST]

The user can select a scenario from a list and start a voice conversation session
for it.

**Acceptance Criteria:**
- Scenario list is fetched from the backend and rendered before a session starts.
- Starting a session initializes conversation state scoped to that scenario.

---

#### FR-002: Capture spoken input [MUST]

The user can record their spoken turn via the browser microphone (push-to-talk).

**Acceptance Criteria:**
- A record button starts/stops capture; captured audio is sent to the backend.
- Clear UI feedback while recording and while awaiting a reply.

---

#### FR-003: Local speech-to-text [MUST]

The backend transcribes the user's captured audio to text using a local STT model.

**Acceptance Criteria:**
- Transcription happens without any network call to an external service.
- Transcript text is returned to the client and shown in the transcript view.

---

#### FR-004: Scenario-aware AI reply [MUST]

The backend generates the AI's next conversational turn using a local LLM,
conditioned on the scenario's persona/goal and the conversation so far.

**Acceptance Criteria:**
- The LLM prompt includes the scenario's system prompt/persona and prior turns.
- Reply is generated entirely by the local Ollama instance, no external API.

---

#### FR-005: Local text-to-speech playback [MUST]

The AI's text reply is converted to spoken audio locally and played back to the
user.

**Acceptance Criteria:**
- TTS audio is generated on-device and streamed/returned to the browser.
- Browser plays the audio automatically once received.

---

#### FR-006: Fully local, one-command stack [MUST]

The whole pipeline runs via `docker compose up` with no calls to external/cloud AI
APIs at runtime (initial model downloads at build/first-run are the only network
dependency).

**Acceptance Criteria:**
- No outbound calls to third-party AI endpoints occur during an active session.
- README documents the one-command startup and first-run model download step.

---

#### FR-007: Visible transcript [SHOULD]

The user can see a running text transcript of both sides of the conversation
alongside the audio.

**Acceptance Criteria:**
- Each turn (user + AI) appears in the transcript in order, in real time.

---

#### FR-008: Multiple selectable scenarios [SHOULD]

At least 3-5 built-in scenarios are available and selectable before a session
starts, each with a distinct persona/goal.

**Acceptance Criteria:**
- Scenarios are defined in config (not hardcoded in application logic) so more can
  be added without code changes to the pipeline.

---

#### FR-009: Restart with a different scenario [COULD]

The user can end a session and start a new one with a different scenario without
restarting the containers.

**Acceptance Criteria:**
- Ending a session clears conversation state; picking a new scenario starts clean.

---

#### FR-010: In-memory session history [COULD]

Conversation history persists for the lifetime of the running session/container
(not across restarts).

**Acceptance Criteria:**
- No database is required; history is held in backend process memory per session.

---

### Non-Functional Requirements

#### Performance

Target CPU-only consumer hardware (see Assumptions). Aim for end-to-end turn
latency (end of user speech → start of AI audio playback) under roughly 5-8
seconds using small/quantized models; treat this as a guidance target to validate
once the pipeline is running, not a hard gate.

#### Security

No audio, transcript, or conversation content leaves the user's machine at
runtime. If the stack is later exposed beyond localhost (e.g. on a home LAN), add
basic access control before doing so — out of scope for this pass.

#### Accessibility / Compliance

No formal accessibility target for this pass; the live transcript (FR-007) doubles
as a captioning aid for the audio content. No regulatory compliance scope (single
local user, no personal data leaves the device).

#### Other

**Offline-capable after setup**: once container images and models are pulled, the
app should function with no internet connection.

---

## Technical Approach

### Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Static web app (HTML/JS, e.g. vanilla or a lightweight framework) | Browser mic capture (MediaRecorder API), served by the backend container |
| Backend / orchestrator | Python + FastAPI | Coordinates STT → LLM → TTS pipeline; owns scenario and session state |
| Speech-to-text | faster-whisper (local, CPU-friendly) | Runs in-process inside the backend container |
| Conversational LLM | Ollama, serving a small quantized instruct model (e.g. an 7-8B class model) | Separate container, REST API on the compose network |
| Text-to-speech | Piper TTS (local, CPU-friendly neural TTS) | Runs in-process inside the backend container |
| Scenario definitions | YAML files | Loaded at startup; id, persona/system prompt, goal, target language |
| Packaging | Docker Compose | Two services: `backend` (web UI + FastAPI + STT + TTS) and `ollama` (LLM) |

### Architecture Overview

```
Browser (mic capture, playback, transcript UI)
        │  HTTP/WebSocket
        ▼
backend container (FastAPI)
  ├─ STT (faster-whisper)      — audio in  → text
  ├─ Scenario engine           — builds prompt from scenario config + history
  ├─ HTTP call ────────────────► ollama container — text in → reply text
  └─ TTS (Piper)                — text in  → audio out
        │
        ▼
Browser plays AI audio, appends transcript turn
```

Two containers keep the Quick Flow footprint small: STT and TTS are lightweight
enough to run in-process alongside the FastAPI app, while the LLM (heavier, and
already packaged as a server by Ollama) gets its own container.

### Key Components

#### Backend Orchestrator (FastAPI)

**Purpose:** Coordinate a conversation turn end-to-end and hold per-session state.

**Responsibilities:**
- Receive recorded audio from the client and run it through STT.
- Build the LLM prompt from the active scenario config + conversation history.
- Call Ollama for the reply, then run TTS on the result.
- Serve the static frontend and the scenario list.

**Interfaces / Contracts:**
- `GET /api/scenarios` — list available scenarios.
- `POST /api/session/start` — start a session for a given scenario id.
- `POST /api/session/{id}/turn` — submit recorded audio, receive transcript + AI
  audio for that turn (or an equivalent WebSocket exchange).

---

#### Scenario Engine

**Purpose:** Turn a scenario config + conversation history into an LLM prompt, and
own the small config format scenarios are authored in.

**Responsibilities:**
- Load and validate scenario YAML files at startup.
- Compose the system prompt (persona, goal, target language) with prior turns.

**Interfaces / Contracts:**
- Scenario YAML schema: `id`, `title`, `target_language`, `persona_prompt`, `goal`,
  `difficulty`.

---

### Data Model

No persistent database for this pass (see FR-010, Out of Scope). Scenario
definitions are static YAML files on disk; conversation history lives in backend
process memory for the duration of a session and is discarded on restart.

### API Design

Minimal HTTP/WebSocket surface between the frontend and backend only (see Backend
Orchestrator interfaces above). No public/external API — the surface exists solely
to connect the bundled web UI to the bundled backend.

### Error Handling Strategy

Surface pipeline failures (mic permission denied, STT/LLM/TTS error, Ollama
unreachable) as clear, user-facing status messages in the UI rather than silent
failures or raw stack traces. Backend logs the underlying error for debugging.

---

## Story List

| # | Epic | Story Title | Notes |
|---|------|-------------|-------|
| 1 | Infrastructure | Docker Compose skeleton (backend + ollama services) | Health checks, shared network, model volume |
| 2 | Infrastructure | Backend service skeleton (FastAPI app, config loading) | Base for all pipeline stories |
| 3 | Voice Pipeline | Integrate local STT (faster-whisper) | Audio in → text out |
| 4 | Voice Pipeline | Integrate local LLM via Ollama | Text + scenario context in → reply text out |
| 5 | Voice Pipeline | Integrate local TTS (Piper) | Text in → audio out |
| 6 | Voice Pipeline | Wire end-to-end turn flow (STT → LLM → TTS) | Ties 3-5 into one backend endpoint |
| 7 | Scenarios | Define scenario YAML schema + loader | Validates and loads configs at startup |
| 8 | Scenarios | Author 3-5 starter scenarios | e.g. restaurant, job interview, small talk, directions, shopping |
| 9 | Scenarios | Scenario list + selection API | `GET /api/scenarios`, `POST /api/session/start` |
| 10 | Frontend | Minimal web UI: scenario picker, record button, playback | Core user-facing flow |
| 11 | Frontend | Live transcript display | Renders each turn as it completes (FR-007) |
| 12 | Polish | Session end/restart flow | Clear state, pick a new scenario without restarting containers |
| 13 | Polish | User-facing error states | Mic denied, model unavailable, pipeline failure messaging |

**Total stories:** 13 (Quick Flow ceiling: 15)

---

## Testing Strategy

### Unit Testing Focus

Scenario YAML loading/validation; prompt-construction logic (scenario + history →
final LLM prompt); request/response shaping for the turn endpoint.

### Integration / End-to-End Scenarios

A canned audio sample run through the full STT → LLM → TTS pipeline, asserting a
non-empty transcript, a scenario-appropriate reply, and returned audio bytes.
Manual end-to-end check in a browser for the golden path (pick scenario → speak →
hear reply → see transcript) before calling a story done.

### Performance / Load Considerations

Measure turn latency (mic stop → audio playback start) on the target CPU-only
hardware once the pipeline is wired up; use it to decide if smaller models are
needed, per the NFR performance guidance above. No concurrent-load testing needed
— single local user.

### Security Testing Notes

Confirm no outbound network calls occur during an active session (aside from the
one-time model pull), e.g. by monitoring container network traffic during a manual
test run.

---

## Dependencies

### External Dependencies

| Dependency | Version / Constraint | Purpose | Risk |
|------------|---------------------|---------|------|
| Ollama | latest stable, pinned image tag | Serves the local conversational LLM | Model download size/time on first run |
| faster-whisper | >=1.0 | Local speech-to-text | Accuracy/latency tradeoff on CPU-only hardware |
| Piper TTS | latest stable release | Local text-to-speech | Voice quality/availability varies by target language |
| FastAPI + uvicorn | latest stable | Backend web/API framework | Low risk, widely used |
| Docker / Docker Compose | current stable | Packaging and orchestration | Requires Docker installed on the host |

### Internal / Shared Dependencies

- None — this is a standalone project with no shared internal services.

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| CPU-only hardware makes the LLM/STT/TTS pipeline too slow to feel conversational | Medium-High | Medium | Default to small/quantized models; treat latency target as guidance; make model choice configurable |
| Docker on Mac can't access the host GPU, capping performance even on capable hardware | Medium | High (given Apple Silicon default) | Design for CPU baseline; document an optional native (non-container) Ollama run to use Metal acceleration if the user wants it |
| Browser mic capture / audio format quirks across browsers | Low-Medium | Medium | Start with push-to-talk (record-then-send) instead of live streaming to keep the client simple |
| First-run model download size/time surprises the user | Low | Medium | Document expected download sizes and first-run time in the README |

---

## Assumptions & Constraints

### Assumptions

1. Target hardware is CPU-only by default (no GPU passthrough assumed), matching
   what Docker containers can reliably access, including on this Mac — a decision
   made without user confirmation and open to revisiting once real latency is
   measured.
2. Ollama is the LLM runtime, chosen as the simplest to containerize/self-host —
   also made without explicit user confirmation.
3. The initial release targets one practice language, with scenario/model config
   structured to add more languages later.

### Constraints

1. All AI inference (STT, LLM, TTS) must run locally — no external AI API calls at
   runtime (from `project-context.md`).
2. The stack must be containerized via Docker/Docker Compose (from
   `project-context.md`).

---

## Success Criteria

How we know this work is complete:

- [ ] User can pick a scenario, speak, and hear a scenario-appropriate spoken AI
      reply, entirely via `docker compose up`.
- [ ] No outbound AI-API network calls occur during an active session.
- [ ] All MUST functional requirements implemented and accepted.
- [ ] Non-functional targets met (see NFR section).
- [ ] All stories reach `done` status.

---

## Decisions Log Summary

| Decision | Rationale | Date |
|----------|-----------|------|
| Track: Quick Flow | Solo builder, ~13-story estimate, no compliance/infra mandate | 2026-09-02 |
| Hardware baseline: CPU-only | Portable default; Docker on Mac can't reach host GPU anyway; not confirmed with user | 2026-09-02 |
| LLM runtime: Ollama | Simplest to containerize/self-host with broad model support; not confirmed with user | 2026-09-02 |
| Language scope: one target language to start | Smallest scope fitting Quick Flow, extensible via scenario/model config | 2026-09-02 |
| Two-container topology (backend + ollama) | STT/TTS are light enough to run in-process; keeps compose stack minimal | 2026-09-02 |
| Push-to-talk instead of live streaming | Reduces client/audio complexity for the MVP | 2026-09-02 |

---

## Next Steps

This tech spec is the Quick Flow planning artifact. Proceed to story creation:

1. Use **bmad-epics-and-stories** to expand the Story List into full story files under
   `bmad-output/stories/`.
2. Story file naming: `{epic}.{story}.{slug}.story.md`
   (e.g., `1.1.compose-skeleton.story.md`)
3. Once stories reach `ready-for-dev` status, hand off to your dev tool / plugin.

If scope has grown beyond 15 stories, switch to the BMad Method track before creating
stories: run **bmad-prd** to capture full requirements, then **bmad-architecture** to
design the system, then return to story planning.

The three unconfirmed assumptions above (hardware baseline, LLM runtime, language
scope) are worth a quick explicit confirmation from the user before or during story
creation, since they shape nearly every downstream story.

---

*Technical Specification — Quick Flow Track — BMAD Method by the BMAD Code Organization*
