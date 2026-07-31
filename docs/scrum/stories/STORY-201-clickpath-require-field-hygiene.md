---
id: STORY-201
title: Clickpath normalizer hygiene — use require_field for execution.outcome
type: chore
points: 1
status: draft
refined: 2026-07-31
---

## Context

Filed from the sprint-66 audit's quality-review fix round (STORY-195,
`docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §4). A latent, currently-unreachable
hygiene gap found while adjudicating why the raw-vendor-row question in the rejected-observation path
is `CLEARED` (F3) — checking a neighboring `except ValueError` claim surfaced a bare dict-subscript
that bypasses the package's own documented error-handling policy.

## Description

`backend/src/adapters/inbound/dynatrace/clickpath_normalizer.py:39` reads
`row["execution.outcome"]` directly, bypassing `_assembly.require_field` — against the documented
policy at `backend/src/adapters/inbound/dynatrace/_assembly.py:20-30` and the pattern
`backend/src/adapters/inbound/dynatrace/http_normalizer.py:22-23` follows correctly
(`code = str(require_field(row, "result.status.code"))`). A missing `execution.outcome` here raises a
bare `KeyError`, NOT a `ValueError` subclass, so it would escape `normalize_rows_lenient`'s
`except ValueError` net entirely — the exact stall shape STORY-190 closed, reopened for this one
field.

**Currently unreachable, not a live defect:** `dispatch.py`'s `_NORMALIZERS` registry
(`backend/src/adapters/inbound/dynatrace/dispatch.py:45-47`) maps only `"http_monitor_execution"` to
`normalize_http_row`; nothing calls `normalize_clickpath_row` in production today. This is preventive
hygiene — the fix is one line and removes a landmine for whoever next wires clickpath into the live
dispatch path.

## Acceptance Criteria

- [ ] **AC1** — `normalize_clickpath_row` reads `execution.outcome` via
      `_assembly.require_field(row, "execution.outcome")`, matching `http_normalizer.py`'s pattern,
      raising `MalformedDqlRowError` (a `ValueError` subclass, quarantine-net-compatible) on a missing
      field instead of a bare `KeyError`.
- [ ] **AC2** — A test asserts a clickpath row missing `execution.outcome` raises
      `MalformedDqlRowError`, not `KeyError`.
- [ ] **AC3** — Existing `clickpath_normalizer` tests continue to pass unchanged for present-field
      inputs.

## Open Questions

None.

## History

- 2026-07-31: filed from STORY-195's quality-review fix round (batched MINOR,
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §4/§6).
