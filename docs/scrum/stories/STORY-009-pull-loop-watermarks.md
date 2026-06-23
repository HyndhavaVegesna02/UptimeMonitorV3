---
id: STORY-009
title: Pull loop with watermarks + validation gate
type: feature
---

## Context
Spec: dossier §8 (ingest & pull loop) + T1.3 (validation gate). Zone 3. The crash-safety
guarantee from strict ordering inside the ingest port.

## Description
Per-signal watermark + overlap window on read; validate-then-quarantine
(`rejected_observations`); dedupe valid rows on `source_event_id`
(`INSERT … ON CONFLICT DO NOTHING`); advance the watermark to `max(observed_at)` over
ACCEPTED observations only; commit BEFORE advancing/sleeping. The poller runs inside the
Railway backend but only calls the ingest port.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Invalid observations land in `rejected_observations` (quarantined, never
      silently dropped); the rest of the batch proceeds (no poison pill).
- [ ] AC2: The watermark advances only on accepted observations (a malformed future
      timestamp cannot leap the cursor — the "year-2099" case is covered by a test).
- [ ] AC3: A duplicate `source_event_id` is a no-op (idempotent re-ingest).
- [ ] AC4: A crash mid-loop loses nothing — proven by interrupting before commit and
      re-running (overlap + commit-before-advance + dedupe).

## Open Questions
- Confirm the scheduler mechanism (asyncio loop vs APScheduler) at refinement.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §8. Status: draft — refine before its sprint.
