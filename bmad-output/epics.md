# Epics — Self-Hosted Voice Language Tutor

> The epic MAP. A thin index, not a context object. Each epic lists its goal, the
> requirements it covers (cited to tech-spec.md), its ordered stories, and cross-epic
> dependencies. Story detail lives in the individual {epic}.{story}.{slug}.story.md files.
>
> Track: Quick Flow
> Sources: tech-spec.md (this track has no separate prd.md/architecture.md — tech-spec.md
> plays both roles), project-context.md

---

## Epic 1: Infrastructure & Containerization

**Goal:** Stand up the Docker Compose skeleton and backend service shell so every
pipeline story has a running foundation to build on.

**In scope (cited):**
- FR-006 — Fully local, one-command stack via Docker Compose [Source: tech-spec.md#fr-006-fully-local-one-command-stack]

**Architecture touchpoints:** Docker Compose (`backend` + `ollama` services), FastAPI
app skeleton [Source: tech-spec.md#technology-stack]

**Out of scope:** STT/LLM/TTS integration logic (Epic 2), scenario content (Epic 3),
UI (Epic 4)

**Stories (ordered):**

| ID | Slug | Intent | Status |
|------|------|--------|--------|
| 1.1 | compose-skeleton | Docker Compose skeleton (backend + ollama services, health checks) | done |
| 1.2 | backend-skeleton | FastAPI app skeleton with config loading | done |

**Cross-epic dependencies:**
- Blocked by: none — this is the foundation epic
- Blocks: Epic 2, Epic 3, Epic 4, Epic 5 — all need the running compose stack + backend shell

---

## Epic 2: Voice Pipeline

**Goal:** Wire the end-to-end voice turn — capture audio, transcribe it locally,
generate a scenario-aware reply from the local LLM, and speak it back — entirely
on-device.

**In scope (cited):**
- FR-003 — Local speech-to-text [Source: tech-spec.md#fr-003-local-speech-to-text-must]
- FR-004 — Scenario-aware AI reply [Source: tech-spec.md#fr-004-scenario-aware-ai-reply-must]
- FR-005 — Local text-to-speech playback [Source: tech-spec.md#fr-005-local-text-to-speech-playback-must]

**Architecture touchpoints:** faster-whisper (in-process STT), Ollama container
(LLM), Piper TTS (in-process), Backend Orchestrator component
[Source: tech-spec.md#key-components]

**Out of scope:** scenario content authoring and schema (Epic 3), browser UI (Epic 4)

**Stories (ordered):**

| ID | Slug | Intent | Status |
|------|------|--------|--------|
| 2.1 | stt-integration | Integrate local STT (faster-whisper): audio in → text out | done |
| 2.2 | llm-integration | Integrate local LLM via Ollama: text in → reply text out | done |
| 2.3 | tts-integration | Integrate local TTS (Piper): text in → audio out | done |
| 2.4 | turn-pipeline | Wire STT → scenario-aware LLM → TTS into one backend turn endpoint | done |

**Cross-epic dependencies:**
- Blocked by: Epic 1 — needs the compose stack and backend skeleton
- Blocked by: Epic 3 (stories 3.1 and 3.3 only, for story 2.4) — the turn endpoint
  needs the scenario schema/loader to build a scenario-aware prompt, and needs a
  startable session (3.3) before a turn can be submitted to it
- Blocks: Epic 4 — the UI needs the turn endpoint (2.4) to submit audio and get a reply

---

## Epic 3: Scenarios

**Goal:** Define the scenario config system and expose it so a user can choose from
multiple practice contexts before starting a session.

**In scope (cited):**
- FR-001 — Start a scenario session [Source: tech-spec.md#fr-001-start-a-scenario-session-must]
- FR-008 — Multiple selectable scenarios [Source: tech-spec.md#fr-008-multiple-selectable-scenarios-should]

**Architecture touchpoints:** Scenario Engine component, YAML scenario config files
[Source: tech-spec.md#scenario-engine]

**Out of scope:** pipeline wiring that consumes the scenario prompt (Epic 2), UI
rendering of the scenario list (Epic 4)

**Stories (ordered):**

| ID | Slug | Intent | Status |
|------|------|--------|--------|
| 3.1 | scenario-schema-loader | Define scenario YAML schema + loader/validator | done |
| 3.2 | starter-scenarios | Author 3-5 starter scenarios (restaurant, job interview, small talk, directions, shopping) | done |
| 3.3 | scenario-selection-api | Scenario list + session-start API (`GET /api/scenarios`, `POST /api/session/start`) | done |

**Cross-epic dependencies:**
- Blocked by: Epic 1 — needs the backend skeleton
- Blocks: Epic 2 (story 3.1 gates 2.4) — the turn pipeline needs the scenario schema
- Blocks: Epic 4 — the scenario picker UI needs 3.3's API

---

## Epic 4: Frontend

**Goal:** Give the user a browser UI to pick a scenario, record their voice, hear
the AI's spoken reply, and follow along with a live transcript.

**In scope (cited):**
- FR-002 — Capture spoken input [Source: tech-spec.md#fr-002-capture-spoken-input-must]
- FR-007 — Visible transcript [Source: tech-spec.md#fr-007-visible-transcript-should]

**Architecture touchpoints:** Static web app, browser MediaRecorder API
[Source: tech-spec.md#technology-stack]

**Out of scope:** backend pipeline logic (Epic 2), scenario content authoring (Epic 3)

**Stories (ordered):**

| ID | Slug | Intent | Status |
|------|------|--------|--------|
| 4.1 | web-ui-core | Minimal web UI: scenario picker, record button, reply playback | done |
| 4.2 | live-transcript | Live transcript display for both sides of the conversation | done |

**Cross-epic dependencies:**
- Blocked by: Epic 2 (needs the 2.4 turn endpoint), Epic 3 (needs the 3.3 scenario API)
- Blocks: Epic 5 — the polish stories build on top of the core UI

---

## Epic 5: Polish

**Goal:** Round out the experience with session restart and clear user-facing error
handling so the app degrades gracefully instead of failing silently.

**In scope (cited):**
- FR-009 — Restart with a different scenario [Source: tech-spec.md#fr-009-restart-with-a-different-scenario-could]
- FR-010 — In-memory session history [Source: tech-spec.md#fr-010-in-memory-session-history-could]

**Architecture touchpoints:** Backend session state, frontend status messaging
[Source: tech-spec.md#error-handling-strategy]

**Out of scope:** none additional — this epic only adds to the Epic 4 UI and Epic 1/2
backend session state

**Stories (ordered):**

| ID | Slug | Intent | Status |
|------|------|--------|--------|
| 5.1 | session-end-restart | Session end/restart flow without restarting containers | done |
| 5.2 | error-states | User-facing error states (mic denied, model unavailable, pipeline failure) | review |

**Cross-epic dependencies:**
- Blocked by: Epic 4 — needs the core UI to attach restart/error affordances to
- Blocks: none

---

## Delivery Tracking (count-based)

No story points, velocity, or burndown. Track by COUNT only:

- Total stories: 13
- Done: 12
- Remaining: 1
- Completion rate: 92%

## Notes

Sequencing follows the natural dependency chain: Infrastructure (1) unblocks
everything; Voice Pipeline stories 2.1-2.3 and Scenario stories 3.1-3.2 can proceed
in parallel once Infrastructure lands, but turn-pipeline (2.4) is additionally
blocked on scenario-schema-loader (3.1) and scenario-selection-api (3.3) — not all
of Epic 3, just those two; Frontend (4) needs both 2 and 3 to expose real
endpoints; Polish (5) is last since it layers onto the working UI, and its two
stories plus 4.1/4.2 are chained (not parallel) because they all touch
`frontend/app.js`. See `bmad-output/stories/*.story.md` Owned File/Module Scope
and Dependency Maps sections for the exact per-story graph, and run
`scope-conflict-check.sh` (or the `bmad-parallel-plan` skill) before scheduling
any stories concurrently — 10 of the 13 stories share a contended file with at
least one sibling and must not run in the same wave as that sibling. The three
tech-spec assumptions (CPU-only baseline, Ollama runtime, single target language)
apply across all epics — see `tech-spec.md#assumptions` and `decision-log.md` if
they change.
