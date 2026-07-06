---
id: STORY-051
title: Defect — DQL watermark bound compared as a bare string; ingestion silently stalls after the first cycle
type: defect
---

## Context
Reported by the PO 2026-07-04 ("even when sample mode is on, I can see in check history as up
… dynatrace monitor is running no problem"). Debugged on branch `debug/ingest-stall-sample-mode`
per PO direction, following the systematic-debugging protocol.

**Symptom chain:** sample mode marks *incoming* observations DOWN (STORY-048 D4 decorator) —
but ingestion had persisted nothing since 2026-07-03 13:29 UTC, so there were no incoming
observations to mark. Check History showing stale "up" rows was downstream of a total
ingestion stall.

**Evidence (live probes, 2026-07-04):**
- DB: exactly 120 observations (11:30→13:29 UTC Jul 3 — one backfill window); watermark
  last written 13:30:05 Jul 3; `rejected_observations` empty; loop logs show healthy
  Grail 202/200 polling throughout.
- The exact per-cycle query (`timestamp >= "2026-07-03T13:24:17.931000Z"`) returned **0 rows**
  against live Grail, while the same query WITHOUT the time bound returned **120 fresh rows
  from Jul 4** (the monitor was healthy all along — PO was right).
- Same query with `timestamp >= toTimestamp("…")` → **120 rows** up to the current minute.

## Root cause
`backend/src/adapters/inbound/dynatrace/query.py::build_dql_query` emitted the watermark lower
bound as `timestamp >= "<ISO string>"`. DQL does not coerce a bare string literal for
comparison against the `timestamp` field — the predicate silently matches NOTHING (no error,
no warning). The first-ever cycle (watermark `None`) omits the clause and ingests Grail's
default ~2h scan window; every later cycle fetches 0 rows, ingests nothing, never advances the
watermark → permanent stall. Every live demo to date looked alive only because it ran shortly
after a fresh DB's first-cycle backfill.

Why nothing caught it: the unit tests pinned the (wrong) query STRING shape, not its live
semantics; the executor treats 0 rows as a legitimate result (it is); the loop has no per-cycle
observability; and the STORY-016b/c live verifications ran against a fresh watermark-less state.

## Fix (this branch, TDD)
`toTimestamp()` wraps the bound: `timestamp >= toTimestamp("<ISO>")` — one line in
`build_dql_query`, covering test rewritten to pin the new contract AND forbid the bare-string
form regressing (`'timestamp >= "' not in q`). Live-verified end-to-end: loop restarted on the
fixed code ingests fresh rows and advances the watermark (see AC).

## Acceptance Criteria
- [x] AC1: `build_dql_query` with a watermark emits `timestamp >= toTimestamp("<ISO Z>")`;
      a test pins the exact form and asserts the bare-string form is absent.
- [x] AC2: live verification — with the fix deployed to the local stack, new observations
      (observed_at > restart instant) are persisted and the watermark advances past its stuck
      value within one cycle.
- [x] AC3: full six-command backend DoD gate exits 0 on the clean committed tree.
      (Sprint 34, 2026-07-06 @ 362fb52: 498 passed / 5 contracts kept / 11 FKs 0 violations /
      alembic OK / ruff check + format clean.)

## Out of scope (filed as observations for refinement)
- Grail's default scan timeframe (~2h) bounds any backfill: data older than the scan window at
  fetch time is unreachable by this query shape (the 13:30 Jul 3 → fix-time gap stays lost;
  availability reports it honestly as gap verdicts). An explicit query timeframe would widen
  recovery — candidate follow-up.
- The loop has NO per-cycle log line (fetched/accepted/rejected counts) — this stall was
  invisible for ~19h. Candidate follow-up: minimal cycle telemetry.
- Related but distinct: STORY-050 (loop crashes on transient errors).

## History
- 2026-07-04: filed + fixed on `debug/ingest-stall-sample-mode` (PO-directed debug session);
  root cause live-confirmed by A/B query probe; fix commit c1839e4.
