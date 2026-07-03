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

## Acceptance Criteria (draft — refine before sprint entry)
- [ ] AC1 (draft): given a cycle whose ingest raises a transient executor error (e.g.
      `GrailQueryError` from a network timeout), `run_periodic` logs and continues; the NEXT cycle
      runs on schedule. Tested with a fake executor that fails once then succeeds.
- [ ] AC2 (draft): non-transient startup failures (missing secrets, bad config) still fail fast
      and loudly — unchanged behavior, with a test pinning at least one such path.
- [ ] AC3 (draft): repeated consecutive failures are visible (log level/counter), not silently
      swallowed forever. Exact mechanism (threshold? crash after N?) is a refinement question.

## Open Questions
- Transient-vs-fatal error taxonomy: is `GrailQueryError` always retryable? Should publish-path
  errors get the same treatment (they already have best-effort semantics per STORY-016a)?
- Should a failure counter eventually crash the process (supervisor-friendly) or only log?

## History
- 2026-07-03: filed as draft from the live crash observed during Sprint 32's PO-requested local
  stack run (orchestrator observation; estimate TBD at refinement).
