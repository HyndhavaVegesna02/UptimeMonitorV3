---
id: STORY-009
title: Pull loop with watermarks + validation gate
type: feature
---

## Context
Spec: dossier §8 (ingest & pull loop) + §6 (ports) + §14 T1.3 (validation gate). Zone 3.
The crash-safety guarantee lives in the strict ordering **inside the core ingest port**,
so any adapter (the Dynatrace poller now, push later) inherits it. Two pieces:

1. **Core ingest service** — the concrete `SignalIngestPort`
   (`backend/src/core/services/`), implementing the §8 ordering against the
   `ObservationRepository` / `WatermarkRepository` ports (both already built). Pure core,
   tested with in-memory fakes — no DB, no Dynatrace.
2. **Pull loop** — a thin `asyncio` loop (composition zone) that reads the per-signal
   watermark, queries the Dynatrace adapter (STORY-008) for everything newer with an
   overlap window, normalizes, and hands the batch to the ingest port. The loop only
   calls the ingest port and the adapter; it contains no business logic.

**Depends on STORY-008** (the adapter the loop pulls from). Sequence STORY-008 first.

## Description
Per-signal watermark + overlap window on read; validate-then-quarantine
(`rejected_observations`); dedupe valid rows on `source_event_id`
(`INSERT … ON CONFLICT (source_event_id) DO NOTHING`); advance the watermark to
`max(observed_at)` over **ACCEPTED observations only**; **commit BEFORE** advancing /
sleeping (dossier §8 ordering: validate → dedupe → persist → advance → hand to pipeline →
commit → sleep). The poller runs co-resident in the Railway backend but reaches the core
only through the ingest port.

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: Invalid observations land in `rejected_observations` (quarantined with a reason
      + payload, never silently dropped); the rest of the batch proceeds — no poison pill.
      Order is **validate, then dedupe**, so a bad row is recorded as a rejection rather
      than deduped away.
- [ ] AC2: The watermark advances only over **accepted** observations — a malformed future
      timestamp cannot leap the cursor (the "year-2099" case has an explicit test).
- [ ] AC3: A duplicate `source_event_id` is a no-op (idempotent re-ingest), via
      `ON CONFLICT DO NOTHING`; `IngestResult` reports the true newly-inserted count.
- [ ] AC4: A crash mid-loop loses nothing — proven by interrupting **before commit** and
      re-running: overlap-on-read + commit-before-advance + dedupe-on-write together
      replay cleanly with no loss and no double-count.
- [ ] AC5: The pull loop is a plain `asyncio` periodic task in the composition zone
      (no new scheduling dependency); it calls only the ingest port + the Dynatrace
      adapter and holds no domain logic. `lint-imports` stays green. The core ingest
      service is tested with **in-memory fake repositories** (no live DB).

## Resolved Questions
- Scheduler mechanism: **plain asyncio loop** (no APScheduler). PO-approved at
  refinement, 2026-06-25 — matches the dossier's single persistent-loop description (§8);
  cron-like multi-job scheduling isn't needed.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §8. Status: draft.
- 2026-06-25: refined alongside Sprint 4 planning. Split conceptually into core ingest
  service + asyncio pull loop; AC1–AC5 finalized; scheduler question resolved (asyncio).
  Depends on STORY-008. Estimate held at 5. Status: ready — committed to Sprint 5
  (Sprint 4 commits STORY-008 only; capacity is 6).
