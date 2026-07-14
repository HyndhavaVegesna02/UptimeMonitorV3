---
id: STORY-083
title: DynamoDB adapters — signals, components, watermarks, sample-mode
type: chore
---

## Context
AWS migration epic (see STORY-082 Context for the approved table design and decisions).
This story ports the four simple repositories onto the `uptime-control` table. The
Postgres adapters remain wired in composition; the new adapters ship alongside, proven
by tests against the `dynamo_local` fixture (STORY-082). Cutover is STORY-087.

Item shapes (approved plan): `TOPOLOGY` partition — `SK=APP#<id>` / `COMPONENT#<id>` /
`SIGNAL#<signal_key>` (SK sort gives list_signals ordering for free);
`WATERMARK#<signal_key>` / `META`; `CONFIG` / `SAMPLE_MODE` (absent item → False).
All decision-path GetItems use ConsistentRead=True.

## Description
Implement `DynamoSignalRepository`, `DynamoComponentRepository`,
`DynamoWatermarkRepository`, `DynamoSampleModeRepository` in
`backend/src/adapters/persistence/`, each satisfying its unchanged core port.

## Acceptance Criteria
- [ ] AC1 (signals): `list_signals()` returns every seeded signal ordered by
      `signal_key`; `get()` returns None on miss — behavior-identical to the Postgres
      adapter, proven by running the same port-contract test scenarios against
      `dynamo_local`.
- [ ] AC2 (components): `list_components()` / `get()` parity; `set_status()` uses a
      conditional update (`attribute_exists`) and raises `ComponentNotFoundError` on a
      missing component (never a silent no-op).
- [ ] AC3 (watermarks): `get()` returns a tz-aware UTC datetime or None;
      `advance()` upserts (PutItem); round-trip preserves the instant exactly
      (canonical fixed-width ISO-8601 UTC serialization, `+00:00` spelling,
      microseconds always padded).
- [ ] AC4 (sample-mode): `is_enabled()` returns False when the item has never been
      written (default-OFF); `set_enabled()` is an idempotent upsert; toggle round-trips.
- [ ] AC5 (boundaries + gates): import-linter contracts pass; the six backend DoD gates
      stay green; new adapters are not yet wired into `composition/app.py`/`run.py`.

## Open Questions
None.

## History
- 2026-07-14: drafted at AWS-migration refinement. Status: draft, 3 points proposed.
- 2026-07-14: PO approved AC + estimate ("approve all") → ready.
