# Sprint 19 — Retrospective

**Outcome:** 5/5 points accepted (STORY-037). **The entire backend is now complete** — ingest →
pipeline → proposals → approve/reject → recorded best-effort publish, with a seeded spine and the full
six-tab read/write API. Velocity history `…, 5, 5, 5`; last-3 mean **5.0**.

## Milestone
Every backend story is Done (001–013, 024/026/028, 014/014b/014c, 016a, 035, 036, 037, 038, 039, 040,
040a). The system, end to end (with fakes for the live edges): pulls observations → collapses/streaks/
anti-flaps → decides proposals → human approve/reject → best-effort publish (recorded to the
publications table), reads everything back through the six-tab API, all over a config-seeded spine. The
only remaining work before/around the frontend is credential-gated.

## What went well
- **Second consecutive clean sprint** — both Opus reviewers passed STORY-037 on the first pass; the two
  minors were non-actionable. The accumulated agreements (spec-rigor, parity, DB-isolation, frozen-type
  invariants, the maintenance/components feature template) now reliably shape the implementer's output.
- STORY-037 mirrored the maintenance template closely; the one new shape (`RecordingPublisher`) composed
  cleanly with the existing `BestEffortPublisher`.

## What surfaced — implementer hygiene
- The implementer left a `ruff format` reflow UNCOMMITTED, so the committed HEAD would have failed
  `ruff format --check` — only the dirty working tree passed, and the "ruff clean" report reflected the
  uncommitted state. The orchestrator's clean-tree inspection caught it and committed the fix
  (`b80552d`). A variant of Sprint 14's "implementer green ≠ committed-tree green."

## Process change (PO-approved)
1. **New working agreement (2026-06-29):** the DoD gate counts only on a CLEAN, committed tree — the
   committed HEAD must BE the gate-green state; the orchestrator runs the gate only after `git status`
   is clean (committing/discarding any leftover first).

## Roadmap — the pivot to "go live" and the frontend
The backend is done; what remains is credential-/account-gated or the frontend:
- **STORY-016** — live e2e demo: the real Dynatrace Executor (HTTP DQL client + `DYNATRACE_ENV_URL` /
  `DYNATRACE_API_TOKEN`) and the live publisher chain
  `BestEffortPublisher(RecordingPublisher(StatuspagePublisher))`, wired into `run_periodic`. Needs the
  PO's Dynatrace + Statuspage credentials.
- **STORY-017** — deploy topology (Railway/Vercel/Neon); migrate → seed → serve.
- **STORY-015** — frontend dashboard (six tabs); MUST be split before it enters a sprint; needs the
  frontend tooling decision (Vitest/Playwright). The read/write API it consumes is fully built.
