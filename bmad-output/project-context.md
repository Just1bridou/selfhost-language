# Project Context — Self-Hosted Voice Language Tutor

> The project **constitution**. This document is loaded by every BMAD planning skill
> so they all share the same ground truth. Keep it tight, current, and authoritative.
> When a major decision changes scope, update this file and append the change to
> `decision-log.md`.

- **Track:** quick-flow  _(quick-flow | bmad-method | enterprise)_
- **Created:** 2026-09-02T07:37:21Z

---

## Project Goal

Deliver a containerized application that lets a user practice speaking a foreign
language by holding spoken conversations with a voice AI, across multiple selectable
practice scenarios. All AI inference (speech-to-text, conversational model,
text-to-speech) runs locally on the user's machine — no calls to external/cloud AI
APIs. "Done and successful" = the user can pick a scenario, speak into the app, and
get a natural spoken reply from a local model, in a container they can self-host.

## Primary Users

The builder themself, initially: a solo learner who wants low-friction, private,
offline-capable spoken practice in a target language. Future users are anyone who
wants to rehearse real conversational scenarios (ordering food, job interview, etc.)
without a human conversation partner or a cloud subscription.

## Scope

- Containerized deployment (Docker / Docker Compose) of the full stack.
- Voice input pipeline: microphone capture → local speech-to-text.
- Conversational engine: local LLM (or comparable local model) driving the AI's
  side of the conversation, scenario-aware.
- Voice output pipeline: local text-to-speech for the AI's replies.
- Multiple practice scenarios (distinct prompts/personas/goals the user can choose
  between), stored/configured so more can be added later.
- Minimal UI/interface to start a session, pick a scenario, and talk.

## Core Constraints

- **Local-only inference**: STT, conversational model, and TTS must all run on the
  user's own hardware — no external AI API calls (privacy, cost, and offline use
  are the driving reasons).
- **Containerized**: the app must run via Docker/Compose for portability and
  self-hosting, consistent with the project's self-hosted framing.
- Must support a usably responsive voice conversation loop (listen → think → speak)
  on consumer hardware — exact latency/hardware targets to be pinned down in the
  tech-spec.

## Non-Goals

- No multi-tenant / multi-account system in this first pass — single local user.
- No mobile app; container-based/local web or desktop client only.
- No cloud hosting/deployment story — self-hosted/local only.
- No video avatar or visual character — audio-only interaction for now.
- No language-content authoring tools beyond a small set of built-in scenarios.

## Key Stakeholders / Roles

Solo builder (project owner) — decides, builds, and reviews. No other teams
involved (Quick Flow track).

## Glossary

- **STT** — Speech-to-Text, converts the user's spoken audio to text.
- **TTS** — Text-to-Speech, converts the AI's text reply to spoken audio.
- **Local model** — an AI model (STT/LLM/TTS) that runs entirely on the user's own
  hardware, with no network call to an external provider.
- **Scenario** — a defined conversational context/persona/goal the user practices
  against (e.g. ordering at a restaurant, a job interview).

---

## Decision Thread

Running decisions live in [`decision-log.md`](./decision-log.md). The first entry is
the track choice from initialization. Consult it before making decisions that might
contradict earlier ones.

## Planning Status (count-based)

- **Track:** quick-flow
- **Stories defined:** _(updated by sprint-planning / story creation)_
- **Stories remaining:** _(count-based delivery — no points, no velocity)_

_This document plans the work. Implementation is handed to external dev tools via
ready-for-dev story files; the planning plugin never writes or tests application code._
