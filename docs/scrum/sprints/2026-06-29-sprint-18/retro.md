# Sprint 18 — Retrospective

**Outcome:** 5/5 points accepted (STORY-040). Neon is now the **seeded read model** — the
`signals.component_id` migration, an idempotent `seed_topology` upsert, a CLI, and app-startup seed
wiring are live; `GET /api/v1/components` returns the seeded Sock Shop components. **The backend
monitoring loop is complete end-to-end with a populated spine.** Velocity history now `…, 5, 5, 5`;
last-3 mean **5.0**.

## What went well — the cleanest sprint to date
- **Both Opus reviewers passed on the FIRST pass — no fix loop.** The new spec-rigor agreement
  (2026-06-29) worked: the spec reviewer traced each "tested" clause to genuinely drive the AC's named
  path (idempotency runs twice and compares values; status-preservation sets `degraded` then re-seeds;
  boot wiring goes through the lifespan; CLI exits 0/1/2).
- **The implementer improved.** It proactively added a `clean_topology` truncate fixture — extending
  STORY-039's DB-isolation pattern to the topology tables that fixture intentionally left alone — and
  the quality reviewer confirmed two consecutive reused-DB suite runs both green. The accumulated
  working agreements are visibly shaping implementer behavior (correct idempotency, status preserved,
  reversible migration, fail-fast boot).

## What surfaced — an orchestrator process slip
- The orchestrator merged STORY-040 to main immediately after the minor-fix commits, BEFORE committing
  the wiki compile pass + board + review.md on the sprint branch (those were done on main afterward).
  No lasting harm — the PO had accepted, the gate was green, and the wiki was re-verified to the
  post-merge HEAD — but main briefly carried a wiki stale against the merge commit, and the branch did
  not hold the full sprint record before landing.

## Process change (PO-approved)
1. **New working agreement (2026-06-29):** merge to main is the LAST step at sprint close — after the
   wiki compile pass (sweep ALL articles current at branch HEAD), the board update, and `review.md` are
   committed on the sprint branch. The merge never precedes the compile pass.

## Backend status & roadmap
The core monitoring pipeline + seeded spine are done. Remaining before frontend:
- **STORY-037** — Publications feature module (the last pure-backend feature; records Statuspage
  publish history for the Publications tab).
- Then creds/account-gated: **STORY-016** (live e2e demo — Dynatrace Executor + Statuspage wiring incl.
  `BestEffortPublisher`), **STORY-017** (deploy).
- **STORY-015** (frontend) — deferred until backend is done.
