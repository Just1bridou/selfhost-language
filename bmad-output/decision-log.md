# Decision Log — Self-Hosted Voice Language Tutor

A threaded, append-only record of decisions made across BMAD planning workflows.
Every later skill (brief, PRD, architecture, stories) appends here so the reasoning
behind the plan stays visible and consistent.

**How to use:** add a new entry at the top of the log (newest first). Never rewrite
or delete past entries — supersede them with a new entry that references the old one.

## Entry format

```
### YYYY-MM-DD — <short title>
- **Decision:** <what was decided>
- **Rationale:** <why; alternatives considered>
- **Made by:** <skill/workflow, e.g. bmad-init, prd, architecture>
- **Supersedes:** <link to prior entry, if any>
```

---

### 2026-09-02 — Bug report: recording doesn't seem to capture the user's voice
- **Decision:** User reported that after the browser manual pass, recording
  didn't seem to capture their actual speech. Investigated and shipped two
  defensive fixes: (1) `recorder.js` now explicitly picks a supported
  `MediaRecorder` `mimeType` (webm/opus → ogg/opus → mp4, in that order)
  instead of relying on the browser's unspecified default, since different
  browsers (Safari especially) vary here; (2) the backend (`stt.py`,
  `pipeline/turn.py`, `api/turn.py`) now uses the uploaded file's actual
  extension as a temp-file suffix hint for faster-whisper's decoder, instead
  of always hardcoding `.wav` regardless of the real content. `app.js` also
  now rejects a suspiciously small recording (< 2000 bytes) client-side with
  a clear message pointing at mic permission/input device/volume, instead of
  silently submitting near-empty audio.
- **Root cause NOT confirmed:** built a real WebM/Opus file (via `ffmpeg`,
  matching what a browser's MediaRecorder actually produces) and tested
  `transcribe()` both with and without the extension-hint fix — both
  decoded correctly ("Hello World." either way). So the file-extension
  mismatch, while a legitimate latent correctness issue worth fixing
  defensively, was **not** the actual cause of the user's symptom. The real
  cause is still open — most likely candidates given no reproduction access:
  the browser's default (unset) `mimeType` producing bad/empty audio on this
  specific browser, or macOS's System Settings microphone privacy toggle not
  being enabled for the browser even though the in-page permission prompt
  was accepted (silently yields an empty/muted stream). Asked the user for
  their browser and to check that OS-level setting.
  - **Resolved:** two separate, unrelated causes, neither a code bug. (1) A
    hard refresh fixed an apparent "Record button does nothing" symptom —
    the browser was running a stale cached copy of the pre-fix JS. (2) The
    original "doesn't record my voice" report was user error: recording
    from the wrong/bad microphone input device. The defensive fixes above
    are kept regardless — the size-check message in particular would have
    surfaced "bad mic" faster and more clearly than a silently wrong
    transcript.
- **Made by:** direct implementation (outside the BMAD planning skills),
  investigating a user-reported bug
- **Supersedes:** none

### 2026-09-02 — Wave 10 (story 5.2, error states) implemented, status: review — final story of the backlog
- **Decision:** Built a single shared, dismissible `#error-banner` and routed
  every failure path (mic permission, turn-endpoint failures, scenario-list
  load, session-start) through it, replacing the ad-hoc use of the
  state-indicator text for errors. `recorder.js` now generates friendly
  mic-permission-error messages itself; `app.js` maps the backend's technical
  per-stage `detail` strings (e.g. raw Ollama connection errors) to
  non-technical phrasing per AC#2, live-confirmed against the exact string
  produced by stopping the `ollama` container mid-turn. Added a `Retry`
  button to `scenario_picker.js`'s load-failure state (a necessary scope
  deviation — AC#3 covers `GET /api/scenarios` failures and that's the only
  file where the retry logic could live). Audited every `await` in the
  touched code for AC#5 (no unhandled exceptions) and added a missing
  `try/catch` around `replyAudio.play()`. Left at `review`, same reason as
  every other frontend story this session: no connected browser tool.
- **Rationale:** with `epics.md` now at 12/13 done, this is the last
  planned story in the backlog — once confirmed, the tech-spec's full
  13-story Quick Flow backlog is complete.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Story 5.1 confirmed by user in a real browser, status: done
- **Decision:** User manually tested end session / restart and confirmed it
  works. Flipped 5.1 from `review` to `done` (12/13 done — only 5.2 remains).
- **Made by:** direct implementation (outside the BMAD planning skills),
  confirmed by the user
- **Supersedes:** none

### 2026-09-02 — Wave 9 (story 5.1, session end/restart) implemented, status: review (not done)
- **Decision:** Added an "End session" button, created and inserted by
  `app.js` directly into `#conversation` rather than declared in
  `index.html` (that section is already only visible during an active
  session, so this satisfies AC#1 for free and needed no new cross-story
  file edits — a cleaner outcome than 4.2's wave). `endSession()` best-effort
  stops any in-flight recording/playback, clears session id + transcript +
  scenario-picker selection, and swaps back to the picker view. Added a
  matching `reset()` to `scenario_picker.js`. No backend or Docker changes —
  confirmed AC#3/#5 need none, since the existing `startSession()` call path
  already creates a fully independent new session. Left at `review`, same
  reason as 4.1/4.2: no connected browser tool this session.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Wave 8 (story 4.2, live transcript) implemented, status: review (not done)
- **Decision:** Added `transcript.js` (`clear()`/`appendTurn()`) and hooked it
  into `app.js`'s existing `startSession()`/`submitTurn()`. Also edited
  `index.html` and `styles.css` (both owned by 4.1, not in 4.2's declared
  scope) — necessary, not optional: the panel needs a DOM container + script
  tag somewhere, and AC#3's auto-scroll is meaningless without CSS giving the
  panel a bounded height. Verified JS syntax and re-ran the 4.1 HTTP-sequence
  regression check against the live backend (unaffected, since this story
  only adds transcript calls around existing logic). Left at `review`, same
  reason as 4.1: no connected browser tool this session, so actual rendering,
  speaker-color labeling, scroll behavior, and clear-on-new-session are
  unverified by me.
- **Rationale:** consistent with 4.1's precedent — don't claim `done` for
  behavior only a real browser can confirm.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Story 4.1 confirmed by user in a real browser, status: done
- **Decision:** User manually tested the running stack (scenario pick →
  record → stop → reply played back, status text changing through each
  state) and confirmed it works. Flipped 4.1 from `review` to `done` in the
  story file and `epics.md` (now 10/13 done).
- **Made by:** direct implementation (outside the BMAD planning skills),
  confirmed by the user
- **Supersedes:** none

### 2026-09-02 — Wave 7 (story 4.1, core web UI) implemented, status: review (not done)
- **Decision:** Implemented the full frontend shell: scenario picker, record
  button wrapping `MediaRecorder`, a 4-state status indicator
  (idle/recording/awaiting/playing), and turn submission with base64 audio
  playback. Verified the JS is syntax-valid and, critically, replayed the
  *exact* HTTP call sequence `app.js` performs (scenarios → session start →
  multipart turn submission → 404-on-invalid-id) with a Node script using the
  same `fetch`/`FormData`/`Blob` web APIs — all succeeded against the real
  running backend. Left status at `review`, not `done`, in `epics.md` and the
  story file.
- **Rationale:** this session has no connected browser-automation tool, so
  actual DOM rendering, click-through UX, real microphone capture, and audio
  autoplay were never visually confirmed — only their HTTP-layer correctness
  was. The story's own Testing section calls for manual browser testing with
  no headless harness mandated, so honesty about what's unverified matters
  more than matching the "done" pattern of prior backend-only stories. Asked
  the user to do a quick manual pass (`docker compose up`, open
  `localhost:8000`, record → stop → confirm playback) before flipping to
  `done`.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Wave 6 (story 2.4, turn pipeline) implemented and verified, status: done — Epic 2 and Epic 3 fully complete
- **Decision:** Implemented `POST /api/session/{id}/turn`, wiring STT → a
  scenario-aware prompt → LLM → TTS into one endpoint, extending
  `router.py` a third time (1.2 → 3.3 → 2.4). Response is JSON with
  `user_text`/`ai_text`/`audio_base64` — a data-URI-ready format chosen so
  the frontend (4.1) needs only `fetch()` + JSON, no multipart response
  parsing. Verified with 6 mocked tests, a real end-to-end pytest run (real
  STT/LLM/TTS, ~20s), and a live `curl` multipart upload against a running
  `docker compose up` stack that returned a genuinely on-persona reply and
  real audio. `epics.md` now shows 9/13 done — Epic 2 (Voice Pipeline) and
  Epic 3 (Scenarios) are both fully complete; only Epic 4 (Frontend) and
  Epic 5 (Polish) remain.
- **Follow-up noted, not addressed here:** STT/TTS models download on first
  use per process (established in 2.1/2.3) but aren't cached in a persistent
  volume the way `ollama-models` is — every fresh `backend` container
  re-downloads ~200MB+ before its first real turn (~20-24s observed). Not a
  blocker for any AC in this backlog, but worth a volume similar to 1.1's
  `ollama-models` if startup latency matters later.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Wave 5 (stories 2.3 TTS + 3.3 scenario/session API) implemented and verified, status: done
- **Decision:** Implemented both file-disjoint wave-5 stories together. 2.3:
  `synthesize()` via `piper-tts`, lazily downloading the `en_US-lessac-medium`
  voice on first use (same one-time-download pattern as 2.1/2.2). 3.3:
  `GET /api/scenarios` + `POST /api/session/start`, extending `router.py`
  (empty since 1.2) with two new routers, plus `session_store.py` for
  in-memory session state. `epics.md` now shows 8/13 done — Epic 2 and Epic 3
  are both fully done except for 2.4, which converges them.
- **Bug found and fixed during verification, not a regression in prior
  stories:** `test_scenarios.py` (1.1/1.2/2.1/3.1's tests all still pass, so
  this wasn't previously visible) mutates the scenario loader's module-global
  state via fixture-directory loads and never restored it, which leaked into
  `test_session_api.py` when run in the same pytest process — 3.3's tests
  initially failed seeing 1 fixture scenario ("duplicate-id") instead of the
  real 5. Fixed with an autouse teardown fixture in `test_scenarios.py` that
  reloads the real default directory after each test. Also updated
  `test_health.py`'s now-outdated "router is empty" assertion, since 3.3
  legitimately extends it — expected, not a regression.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Wave 4 (stories 2.2 LLM + 3.2 starter scenarios) implemented and verified, status: done
- **Decision:** Implemented both file-disjoint wave-4 stories together. 2.2:
  `generate_reply()` over Ollama's `/api/generate`, defaulting `OLLAMA_MODEL`
  to `llama3.2:1b` (smaller than tech-spec's "~7-8B class" guidance, chosen
  for a practical dev-loop/CI download-and-run budget on the CPU-only
  baseline). 3.2: all 5 planned scenario YAML files (not just the 3 required
  minimum). Verified together: pulled `llama3.2:1b` into the running Ollama
  container (1.3GB), ran a real (non-mocked) LLM call against it, and
  confirmed AC#4 live by stopping `ollama` mid-test and observing a fast
  `LLMError` rather than a hang. Also confirmed the 5 real scenarios load
  through 3.1's loader with zero errors — the first time that loader has run
  against real (non-fixture) content. Updated `README.md`'s model-pull
  example to match the actual default. `epics.md` now shows 6/13 done.
- **Rationale for the smaller default model:** tech-spec.md's "~7-8B class"
  figure was itself an unconfirmed assumption (see the 2026-09-02 tech-spec
  entry below); `llama3.2:1b` keeps the project's own verification loop fast
  or the download practical on a modest CPU-only host, while `OLLAMA_MODEL`
  remains fully overridable if the user wants a larger/better model.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Wave 3 (stories 2.1 STT + 3.1 scenario schema/loader) implemented and verified, status: done
- **Decision:** Implemented both genuinely-parallel wave-3 stories together
  (file-disjoint, per the parallelization plan). 2.1: `transcribe()` via
  faster-whisper, model loaded once via `lru_cache`, default `base`/`int8` on
  CPU, with a real speech fixture (`sample_audio.wav`, generated via macOS
  `say -v Samantha` piped through `afconvert`) proving actual transcription
  works, not just mocks. 3.1: pydantic `Scenario` schema + `loader.py` that
  loads eagerly at *module import time* rather than via a `main.py` startup
  hook, since `main.py` is locked to story 1.2. Both verified with 15/15 tests
  passing together and a live `docker compose up` showing the app still starts
  and stays healthy. `epics.md` now shows 4/13 done.
- **Rationale:** The "no network call during transcription" AC (2.1#5) is
  interpreted as covering the *inference* call only, not the one-time
  Hugging Face model-weight download on first use — treated the same as the
  project's existing Ollama-model-pull precedent (a one-time setup dependency,
  not a runtime violation of the local-only-inference constraint).
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Story 1.2 (backend-skeleton) implemented and verified live, status: done
- **Decision:** Implemented the FastAPI app skeleton (`app/main.py`, empty
  `app/api/router.py` aggregator, `app/{api,pipeline,scenarios,state}` package
  stubs, `backend/tests/test_health.py`). Wired the real `uvicorn` entrypoint and a
  `/health`-targeted healthcheck into `backend/Dockerfile` and `docker-compose.yml`
  (both owned by 1.1, not 1.2 — see below), and added a `./frontend:/app/frontend:ro`
  bind mount so Epic 4 can populate `frontend/` with zero backend changes. All 3
  unit tests pass (`python -m pytest`, run inside the built image) and all 6 ACs
  verified live via `docker compose up`. Flipped 1.2's status to `done`; `epics.md`
  now shows 2/13 done.
- **Rationale / scope note:** touching `backend/Dockerfile` and `docker-compose.yml`
  deviates from 1.2's declared Owned Scope (they belong to 1.1), but this exact
  interaction was pre-announced in 1.1's own Dev Agent Record ("1.2 replaces both
  the CMD and the healthcheck target"), so it was expected, not accidental scope
  creep. Implementation here is sequential, not parallel dev-tool agents, so there
  was no real collision risk — recorded for traceability against the documented
  contract, in case a future parallel-plan re-run treats these two stories as
  independently schedulable.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Story 1.1 (compose-skeleton) implemented and verified live, status: done
- **Decision:** Implemented `docker-compose.yml`, `backend/Dockerfile`,
  `backend/requirements/.gitkeep`, and `README.md` per story 1.1, then verified all 6
  ACs live with `docker compose up -d --build` (see the story's Dev Agent Record for
  the full verification log). Flipped 1.1's status to `done` and updated
  `epics.md`'s delivery tracking to 1/13 done.
- **Rationale:** The user asked to start implementing wave 1, which is this
  planning plugin's boundary — implementation itself is not a planning-skill
  activity, so this was done directly rather than via a BMAD skill.
- **Environment note:** first `docker compose up` attempt failed on a Docker VM
  disk I/O error, root-caused to the host Mac being at 99% disk capacity. User
  freed space; a Docker Desktop restart cleared a stale containerd metadata-DB
  error left over from the failed write. No story-file or compose/Dockerfile
  changes were needed once the environment was healthy.
- **Made by:** direct implementation (outside the BMAD planning skills)
- **Supersedes:** none

### 2026-09-02 — Parallelization plan: 10 waves, maxParallel=3, real concurrency in waves 3-5
- **Decision:** Built `dependency-graph.json` and `waves.json` from the 13 ready-for-dev
  stories and rendered `parallelization-plan.md`. Result: 10 waves; only waves 3, 4, and 5
  have 2 concurrent stories each (2.1+3.1, 2.2+3.2, 2.3+3.3); the other 7 waves are solo.
- **Rationale:** The backlog is genuinely more sequential than parallel for a solo-builder
  Quick Flow project — one shared `frontend/app.js` serializes 4.1→4.2→5.1→5.2, and one
  shared `backend/app/api/router.py` serializes 1.2→3.3→2.4. Concurrency is real only in
  the STT/LLM/TTS-vs-scenario window (waves 3-5), which is disjoint by file scope.
- **Also found and fixed a tooling gap:** `build-dependency-graph.py`'s parser only
  detects a Dependency Maps bullet starting with the literal text `blocked by`; this
  project's stories follow the official template's bold format
  (`- **Blocked by:** ...`), which the parser does not match. The first graph-build run
  produced 0 `depends_on` edges (only same-epic sequencing survived), which would have let
  the wave planner co-schedule stories with real cross-epic dependencies (e.g. 2.1 with
  1.2, or 4.1 before 2.4/3.3 landed). Manually added the 10 missing edges to
  `dependency-graph.json`, sourced directly from each story's own Dependency Maps section,
  before running `plan-parallel-waves.py`. No story file content was changed for this fix.
- **Made by:** bmad-parallel-plan
- **Supersedes:** none

### 2026-09-02 — Sharded tech-spec.md into epics.md + 13 story files
- **Decision:** Grouped the 13-story tech-spec backlog into 5 epics (Infrastructure,
  Voice Pipeline, Scenarios, Frontend, Polish) and compiled each story as a full
  context object under `bmad-output/stories/`. Since Quick Flow has no separate
  prd.md/architecture.md, all Dev Notes citations point to `tech-spec.md` instead.
  Introduced two file-layout conventions specifically to keep story scopes
  disjoint: (1) per-story dependency files under `backend/requirements/*.txt`
  instead of one shared `requirements.txt`; (2) no central `config.py` — each
  pipeline module reads its own env vars inline; (3) an empty `app/api/router.py`
  aggregator (created in 1.2) that 3.3 then 2.4 extend in sequence, so `main.py`
  is only ever touched by 1.2.
- **Rationale:** Keeps the story count at 13 (under the 15-story Quick Flow
  ceiling) while maximizing how many stories can run in parallel once their real
  dependencies are satisfied.
- **Made by:** bmad-epics-and-stories
- **Supersedes:** none

### 2026-09-02 — Scope-conflict check: 10 conflicts, all intentionally serialized
- **Decision:** Ran `scope-conflict-check.sh` over all 13 stories: 10 conflicting
  pairs were reported (1.1×1.2 on `README.md`; 1.2×2.4, 1.2×3.3, 2.4×3.3 on
  `backend/app/api/router.py`; and 4.1×4.2, 4.1×5.1, 4.1×5.2, 4.2×5.1, 4.2×5.2,
  5.1×5.2 on `frontend/app.js`/`frontend/styles.css`). Every conflicting pair
  already has a direct or transitive Blocked-by relationship in its Dependency
  Maps, so no re-slicing was done — all 13 stories are marked `ready-for-dev` as
  written, per REFERENCE.md's "intentionally serialized" resolution path.
- **Rationale:** These are genuine dependency chains, not accidental scope
  bleed (e.g. `app.js` is legitimately extended by 4.1 → 4.2 → 5.1 → 5.2 in
  sequence). Re-slicing further would fragment small files for no real
  parallelism gain. The scope-conflict-check output itself is the authoritative
  "do not schedule these together" signal for any later parallel-planning step,
  independent of whether every pair also has an explicit Blocked-by edge.
- **Made by:** bmad-epics-and-stories
- **Supersedes:** none

### 2026-09-02 — Tech-spec technical approach: two-container Docker Compose stack
- **Decision:** Backend (FastAPI + faster-whisper STT + Piper TTS, in-process) and
  a separate `ollama` container for the LLM. Push-to-talk voice turns (not live
  streaming). Scenarios defined as YAML config, no database.
- **Rationale:** Keeps the Quick Flow footprint minimal — STT/TTS are light enough
  to embed in the backend process; the LLM already ships as its own server via
  Ollama. Push-to-talk avoids real-time audio-streaming complexity for the MVP.
- **Made by:** bmad-tech-spec
- **Supersedes:** none

### 2026-09-02 — Three unconfirmed assumptions baked into tech-spec.md
- **Decision:** Proceeded with (1) CPU-only hardware baseline, (2) Ollama as the
  LLM runtime, (3) one target language for the initial release — without explicit
  user confirmation, since the clarifying questions went unanswered.
- **Rationale:** Auto-mode bias toward forward progress; all three are reasonable,
  reversible defaults documented in `tech-spec.md`'s Assumptions section. Flagged
  there for the user to confirm or override before/during story creation, since
  they shape nearly every downstream story.
- **Made by:** bmad-tech-spec
- **Supersedes:** none

### 2026-09-02 — Track selected: quick-flow
- **Decision:** Initialized this project on the **quick-flow** track.
- **Rationale:** Solo builder, no compliance/infra mandate, and the user estimated
  1-15 stories for the first planning pass. The heuristic script's default
  suggestion (bmad-method) was overridden per the user's explicit scope answer —
  when unsure, BMAD guidance is to prefer the lighter track and promote later if
  the containerized voice pipeline (STT/local-LLM/TTS + scenario system) turns out
  to need more than a tech-spec.
- **Made by:** bmad-init
- **Supersedes:** none
