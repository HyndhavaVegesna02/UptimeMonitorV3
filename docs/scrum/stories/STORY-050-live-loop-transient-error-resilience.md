---
id: STORY-050
title: Defect — a single transient Grail/network error crashes the whole live loop
type: defect
---

## Context
Observed 2026-07-03 while running the STORY-042 local stack alongside Sprint 32: the live loop
(`python -m src.composition.run`) died with exit 1 after ~2.5h of healthy operation. Traceback:
`GrailQueryError: HTTP request to Grail failed: _ssl.c:1015: The handshake operation timed out`
propagating from `adapters/inbound/dynatrace/grail_executor.py::executor` →
`composition/pull_loop.py::run_cycle` → `run_periodic` → `asyncio.gather` in
`composition/run.py::main` — one transient SSL handshake timeout terminated the entire process.

A pull-based monitor loop must ride out transient vendor/network blips: the next cycle would very
likely have succeeded (the same tenant answered normally before and after). Related but distinct:
STORY-043 (.env not loaded — startup concern); this story is about steady-state resilience.
Deployment relevance (Railway, STORY-017): a crash-looping worker on transient upstream errors is
an operational hazard; local supervision hides it, production won't.

## Description
Make the live loop survive transient per-cycle failures: a failed cycle logs the error (with the
signal_key and cause) and the loop continues to the next scheduled cycle, rather than the
exception escaping `run_periodic` and killing the process. Deliberate scope question for
refinement: which errors are "transient" (network/HTTP/Grail-5xx?) vs which should still crash
fast (config errors, auth failures — fail-fast is a design value per the config-layer fail-fast
loader).

## Acceptance Criteria (refined 2026-07-06, PO-approved at sprint-36 planning)
- [ ] AC1: given a cycle that raises (e.g. `GrailQueryError` from a network timeout),
      `run_periodic` logs the error with the signal_key + cause and continues — the NEXT cycle
      runs on schedule. Tested with a fake executor that fails once then succeeds, asserting the
      second cycle's ingest actually ran.
- [ ] AC2: startup failures stay fail-fast — missing secrets (`MissingLiveSecretError`) and bad
      config still terminate before any loop starts (these paths run BEFORE `run_periodic`;
      unchanged behavior, pinned by test). Publish-path errors are OUT of scope (already
      best-effort per STORY-016a/045).
- [ ] AC3 (PO decision 2026-07-06: LOG-ONLY, never crash): every failed cycle logs at ERROR
      with its consecutive-failure count for that signal; a success resets the counter; the
      loop NEVER exits on cycle failures — pinned by a test driving many consecutive failures
      and asserting the loop is still scheduling. Accepted trade-off (recorded): a persistent
      failure (e.g. mis-rotated token) is visible only in logs — pairs with the loop-liveness
      surface candidate from the 2026-07-06 debug sprint.

## Open Questions
None — taxonomy resolved (ALL per-cycle exceptions are survivable, no per-error classification;
fail-fast is preserved structurally because startup runs before the loop), and the
crash-vs-log question resolved by the PO (log only).

## History
- 2026-07-03: filed as draft from the live crash observed during Sprint 32's PO-requested local
  stack run (orchestrator observation; estimate TBD at refinement).
- 2026-07-06: refined to READY at sprint-36 planning. PO decisions: AC3 = log-only (never
  crash); simple taxonomy (catch-all per cycle, startup untouched). Estimate 3.
