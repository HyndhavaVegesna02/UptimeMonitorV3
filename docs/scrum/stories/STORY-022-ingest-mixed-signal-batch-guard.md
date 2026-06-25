---
id: STORY-022
title: Fail loud on a mixed-signal batch in the ingest service
type: chore
---

## Context
Follow-up from Sprint 5 review (STORY-009 quality-review minor #1, non-blocking). The core
`IngestService.ingest_observations` (`backend/src/core/services/ingest_service.py:106-108`)
advances the watermark using `signal_key = valid[0].signal_key` and a single
`max(observed_at)` over the whole batch — it ASSUMES the batch is scoped to one signal per
pull cycle. That holds for the only current producer (the Dynatrace adapter's
`fetch_observations` returns one signal per cycle) and is documented, but it is unguarded:
a future mixed-signal batch (a push webhook batching several monitors, or a future
"ingest everything newer" path) would advance only the FIRST signal's watermark to a max
computed across OTHER signals' timestamps — silently over-advancing one cursor and
freezing the others. That is exactly the class of failure the §8 ordering exists to prevent,
so the assumption should fail LOUD rather than be silently trusted.

## Description
Make `IngestService` reject a batch that spans more than one distinct `signal_key` with a
clear named error, rather than trusting `valid[0]`. Keep the happy path (single-signal
batch) unchanged.

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: Given a batch whose observations span >1 distinct `signal_key`, `ingest_observations`
      raises a clear named error (e.g. `MixedSignalBatchError`) naming the offending keys,
      checked UP FRONT over the WHOLE batch — before any validation, persistence, or watermark
      work — so it never silently advances one signal's watermark using another's timestamps.
- [ ] AC2: A single-signal batch (the current producer's shape) behaves exactly as today; an
      empty batch is still a clean no-op; all existing STORY-009 ingest tests pass unchanged.
- [ ] AC3: A test covers the mixed-signal batch case. `lint-imports` stays green (the error
      type lives in core).

## Resolved Questions
- Guard scope: **the WHOLE batch, up front** (PO-approved 2026-06-25) — a mixed-signal batch is
  an upstream programming error; surface it before doing any work, not after partial processing.

## History
- 2026-06-25: created from Sprint 5 review (PO asked minor #1 become a follow-up story).
- 2026-06-25: refined for Sprint 6. Open question resolved (whole-batch, up-front guard);
  AC1–AC3 finalized; estimate 1. Status: ready.
