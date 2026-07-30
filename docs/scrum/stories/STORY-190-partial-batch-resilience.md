---
id: STORY-190
title: One unmappable row stalls a signal forever — quarantine the row, keep the batch
type: defect
points: 3
status: ready
refined: 2026-07-30
---

## Context

Split out of STORY-177's AC4 at sprint-65 refinement (2026-07-30), after the defect turned out to
be materially worse than STORY-177 described it.

**What STORY-177 said:** `dispatch.py:80` normalizes rows in a bare list comprehension, so one bad
row raises and the whole batch for that signal in that cycle is discarded.

**What is actually true** (traced 2026-07-30, all citations verified):

1. `normalize_rows` (`backend/src/adapters/inbound/dynatrace/dispatch.py:80`) is
   `[normalize_row(row, ...) for row in rows]` — the first raising row aborts the whole list.
2. That runs inside `fetch_observations` (`adapter.py:44`), which `run_cycle` calls at
   `pull_loop.py:102` — **before** `ingest_port.ingest_observations(batch)` at `pull_loop.py:109`.
3. So the watermark advance, `self._watermark_repo.advance(...)` at
   `core/services/ingest_service.py:139`, is **never reached**.
4. `run_periodic` catches the exception, increments a consecutive-failure counter, logs at ERROR,
   and proceeds to the next cycle (`pull_loop.py:200-207`) — deliberately, per STORY-050: a cycle
   that raises is survived, never fatal.
5. The next cycle reads the same unadvanced watermark and re-queries **the same window**, which
   still contains the same unmappable row.

The consequence is not a lost batch. **That signal never advances again** — it re-fetches, re-fails
and re-logs every cycle indefinitely, until the offending row ages out of the vendor's retention
window (if it ever does). Healthy rows behind it in the same window are never ingested. The loop
keeps running and looks alive.

This is the same failure shape `composition/vendor_health.py` exists to catch — a pipeline that is
well-formed, answers HTTP 200, raises nothing fatal, and silently ingests nothing (that module's
docstring `:1-10` describes the 30-day version of it, fixed by hotfix `79bfbb3`). Here it is louder
(there IS an ERROR log per cycle) but the stall is permanent rather than self-healing.

This defect exists **today**, independent of STORY-177 — any unrecognised `event.type`
(`UnsupportedMonitorTypeError`), any missing required field (`MalformedDqlRowError`) or any
unrecognised status (`UnknownVendorStatusError`) triggers it. STORY-177 raises the odds by adding
row variety, which is why this is sequenced first.

## Description

Make one bad row cost that row, not the signal. A row that cannot be normalized is **quarantined
and surfaced**; the rest of the batch normalizes, ingests, and advances the watermark past it.

### Zone constraint (binding — CLAUDE.md §4, and the reason this is its own story)

**The tempting implementation is wrong and the mechanical gate will not catch it.** Having the
inbound adapter import `src.core.ports.rejected_observation_repository` and write quarantine rows
itself **passes all eight `lint-imports` contracts** — verified against `pyproject.toml:38-105`:
`core-independence` (`:41-42`) has `src.core` as *source* (wrong direction), `adapters-independence`
(`:53-56`) lists only the three adapter subpackages, and `adapters-edge-only` (`:83-87`) forbids only
`src.api`/`src.composition`. It still turns a pure translation layer into an orchestrator with a
persistence dependency. Do not do it. This paragraph and the quality review are the only guards.

**The gate catches only half the trap.** Reaching for the *concrete*
`src.adapters.persistence.dynamo_rejected_observation_repository` instead **does** break
`adapters-independence` (`pyproject.toml:53-56`). Only the **core-port** route is invisible. So a red
gate here means you took the concrete route — but a **green gate does not mean you took the right
one.**

Required shape:

- **The inbound adapter stays a pure function.** It returns values and persists nothing. It gains no
  reference to any repository port.
- **`composition` decides what happens to the failures** — it is the one zone permitted to see both
  sides (CLAUDE.md §4).
- **The failure value type is adapter-local, not a core domain type.** It carries the raw vendor row
  dict, so it must not enter `core/`. Define it in
  `adapters/inbound/dynatrace/dispatch.py`; `composition` may import it (composition imports both
  sides). Do **not** add it to `core/domain/`.
- **No new port and no new domain type are needed.** `RejectedObservationRepository.save()` already
  takes exactly the right shape — `signal_key: str | None`, `reason: str`, `payload: dict`,
  `rejected_at: datetime` — and its docstring already states the intent:
  *"Rejection is never a poison pill — the caller persists this and moves on to the rest of the
  batch."* It was written for validation rejects; it fits normalization rejects unchanged. The raw
  row goes in as an opaque `payload` dict, so no vendor shape reaches `core`.

### Required design (external mode — build this literally, infer nothing)

**Names are prescribed. Do not invent alternatives** — sprint 65 is external, so an unnamed type is a
coin flip.

1. In `dispatch.py`, a frozen dataclass **`RowNormalizationFailure`** with exactly two fields:
   `row: dict` (the raw vendor row) and `reason: str` (the caught exception's `str()`, which already
   names the offending code / `event.type` / field). **Adapter-local — NOT in `core/domain/`.**
2. In `dispatch.py`, a frozen dataclass **`NormalizationOutcome`** with exactly two fields:
   `observations: list[SignalObservation]` and `failures: list[RowNormalizationFailure]`.
3. In `dispatch.py`, a new function **`normalize_rows_lenient(rows, *, signal_key) ->
   NormalizationOutcome`**, catching exactly `UnknownVendorStatusError`,
   `UnsupportedMonitorTypeError` and `MalformedDqlRowError` per row; observations keep **input
   order**. **Leave `normalize_rows` itself byte-for-byte unchanged and strict** — it is the fail-loud
   unit, called by `backend/tests/test_dynatrace_adapter.py:169,193,247,255,297`,
   `backend/tests/demo_engine/test_via_grail_executor.py:47,87` and
   `test_scenario_coverage.py:55`. (Verified exhaustively: those 8 test sites plus the one production
   caller `adapter.py:44` are the complete set.) None may change behaviour.
4. `fetch_observations` (`adapter.py:24-44`) uses the lenient path and returns
   **`NormalizationOutcome`** — the same named type, not a bare tuple. This is the intended contract
   change and the reason this story reviews separately from STORY-177.
5. **`run_cycle` AND `run_periodic` both gain a keyword-only `rejected_repo:
   RejectedObservationRepository | None = None`.** This is the step most likely to be got wrong:
   **`build_live_loop` calls `run_periodic` (`run.py:137-150`), never `run_cycle`**, and
   `run_periodic` builds the `run_cycle` call itself at `pull_loop.py:186-199`. Adding the parameter
   only to `run_cycle` wires nothing and production quarantines nothing.
6. `run_cycle` ingests `outcome.observations` exactly as today, so **`run_cycle`'s return type and
   `on_cycle`'s type (`pull_loop.py:82` and `:147-150`) are UNCHANGED — do not widen them.** For each
   failure it calls `rejected_repo.save(signal_key=..., reason=failure.reason, payload=failure.row,
   rejected_at=<clock now>)` and logs at **WARNING** naming the signal_key and reason. The watermark
   advances on the good rows, so the signal moves past the bad one.
7. `rejected_repo` is already constructed at the composition root (it is passed to `IngestService`);
   thread it from there through `build_live_loop` → `run_periodic` → `run_cycle`. When it is `None`,
   failures must still be **logged at WARNING** — never silently dropped, which would recreate the
   "trusted-and-wrong" pipeline this repo has already been burned by twice.

## Acceptance Criteria

- [ ] **AC1** — A batch of N rows containing one unnormalizable row ingests the other N-1 and
      quarantines the one. Asserted for all three existing failure modes:
      `UnknownVendorStatusError`, `UnsupportedMonitorTypeError`, `MalformedDqlRowError`.
- [ ] **AC2** — **The stall is proven gone.** A test drives two consecutive `run_cycle` calls over a
      window containing one bad row and asserts the watermark **advanced** after the first, so the
      second cycle does not re-fetch the same window. A test that only checks "good rows survived"
      does not satisfy this AC — the permanent stall is the defect, and the watermark advance is the
      only evidence it is fixed.
- [ ] **AC3** — **The stall is reproduced first.** A test (or a documented, re-runnable
      demonstration) shows the CURRENT behaviour failing — watermark unadvanced, same window
      re-queried — and is then shown passing after the fix. Per working agreement A7 (sprint-64),
      an artifact asserting a fix must be shown failing on the pre-fix state; a green-only test is
      not evidence.
- [ ] **AC4** — Each quarantined row is persisted via `RejectedObservationRepository.save()` with
      the raw row as `payload`, a `reason` naming the actual cause, and the correct `signal_key`.
- [ ] **AC5** — Each quarantined row logs at WARNING naming the signal_key and the reason
      (`caplog`-asserted). A fully-healthy batch logs **no** such warning.
- [ ] **AC6** — **Zone constraint held**: no file under `backend/src/adapters/inbound/` imports any
      repository port or any `persistence` module; the new failure value type is **not** in
      `core/domain/`; `core/` is unchanged except where genuinely required (expected: not at all);
      the eight `lint-imports` contracts pass **unedited**.
- [ ] **AC7** — `normalize_rows` keeps its current strict, fail-loud behaviour and signature; every
      existing call site listed above passes unmodified.
- [ ] **AC8** — The five backend DoD gate commands exit 0, with pass/skip counts recorded. A nonzero
      skip count is an incomplete gate (working agreement A6). Run with `REQUIRE_DYNAMO=1`.

## Dependencies

- **Sequenced BEFORE STORY-177.** 177 adds row variety to a path where a single unrecognised code
  currently stalls a signal; fixing the stall first means the mapping lands on a path that already
  degrades gracefully.
- **STORY-191 exercises this at loop scale** — its scenario includes a row the mapping still cannot
  handle, to prove quarantine works in a real run and not only in unit tests.

## History

- 2026-07-30: split out of STORY-177 AC4 at sprint-65 refinement, PO-approved, estimated 3 points,
  sequenced first. The split was chosen over keeping it in STORY-177 because it changes the
  `fetch_observations` → `run_cycle` contract — a wider blast radius than the mapping itself — and
  so earns its own spec review; and because if the contract change goes sideways, the mapping still
  ships.
