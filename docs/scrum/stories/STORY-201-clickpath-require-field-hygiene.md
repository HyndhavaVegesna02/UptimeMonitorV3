---
id: STORY-201
title: Clickpath normalizer hygiene — use require_field for execution.outcome
type: chore
points: 1
status: ready
refined: 2026-07-31
re_refined: 2026-08-02
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

## Scope limit — state it, do not overclaim it

The Description's claim is that the error becomes quarantine-net-compatible. **That cannot be proven
end-to-end here, and the story must not pretend otherwise.** `normalize_rows_lenient(rows, *,
signal_key)` (`dispatch.py:105-107`) dispatches internally through `_NORMALIZERS`, which maps only
`"http_monitor_execution"`; clickpath's real `event.type` is explicitly unknown and the registry
comment says not to guess it. So no clickpath row can reach the lenient path today.

AC2 therefore tests the normalizer **directly**, and the quarantine-compatibility claim rests on the
type relationship — `MalformedDqlRowError` is a `ValueError` subclass (`_assembly.py:18`) and the
lenient path catches `ValueError`. That is a sound inference, not a demonstration, and should be
described that way in the story's report rather than as "verified through the quarantine path".

## Open Questions

None.

## History

- 2026-07-31: filed from STORY-195's quality-review fix round (batched MINOR,
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §4/§6).
- 2026-08-02: refined to `ready` at sprint-67 planning; estimate confirmed at 1. Citations
  re-derived against HEAD (`86459ea`) and all hold: the bare subscript at
  `clickpath_normalizer.py:39`, the correct pattern at `http_normalizer.py:22-23`,
  `MalformedDqlRowError` at `_assembly.py:18` with the policy docstring through `:27`, and the
  single-entry `_NORMALIZERS` at `dispatch.py:45-47`. Added the scope limit above so the
  quarantine-net claim is not reported as demonstrated when it is inferred.
