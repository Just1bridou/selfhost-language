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
