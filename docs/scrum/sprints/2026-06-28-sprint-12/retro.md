# Sprint 12 — Retrospective

**Outcome:** 7/7 points accepted (STORY-034 2 + STORY-014 5). Zone 6 is open: the five-file
API convention + the 4th `lint-imports` contract (`api-feature-independence`) are live.
Velocity history now `…, 6, 6, 4, 7`; last-3 mean **5.67**.

## What went well
- **STORY-034 cleared the sprint-11 wiki debt in one pass** — 7 reformat-stale articles
  rehabbed to symbol-based citations and re-verified, gate-only, no rework.
- **The blast-radius machinery did its job twice:** STORY-014's diff was matched against the
  (now-verified) `architecture-boundary.md`, and at the compile pass the orchestrator's own
  inline fix was caught drifting 4 articles (the stale "resolve raises ValueError" Fact, the
  undocumented `get()` method, the "3 contracts" count) — all corrected before review.
- No blockers, no effort-cap trips, no hotfixes.

## What dragged — one fix loop on STORY-014 (3 findings)
1. **Quality MAJOR — concurrent double-submit returned HTTP 500 instead of 409.** A check-then-act
   (TOCTOU) race: `get()` saw the proposal OPEN, a concurrent approve resolved it, then `resolve()`
   raised a bare `ValueError` the edge didn't map. The plan specified resolve's edge behavior but
   not that it must raise a *mapped domain error* provable under a forced race.
2. **Spec AC1 — controller imported the core service.** The DI provider was placed in the
   controller. Root cause: the five-file convention was brand-new and DI-provider placement wasn't
   concretely specified for the external implementer.
3. **Spec AC1 — no five-file *shape* test** (only DTO distinctness was asserted).

All three were verifiable mechanically and closed in one PO-authorized inline fix (`eb147ef`),
which also cleared the requested non-blocking minors.

## Process changes (PO-approved)
1. **New working agreement (2026-06-28):** *Check-then-act across a port raises a mapped domain
   error, proven under a forced race.* — the write side of a guarded conditional write must raise a
   named domain error on a 0-row write, the edge must map it (e.g. → 409), and a forced-race test
   must prove the mapped outcome; fake and real adapter raise the same error. (Generalizes the
   STORY-014 race→500 MAJOR; written to `working-agreements.md`.)
2. **Not amended — captured in the wiki instead:** the DI-placement lesson (keep the controller
   import-clean by putting the provider in the feature `service.py`) lives in
   `api-five-file-convention.md`, which every future five-file feature's brief carries. Avoided
   a redundant agreement.

## Follow-up
- **STORY-035** (draft) created for the two non-blocking minors: dispose the app engine on
  shutdown; migrate off the deprecated Starlette `TestClient`/`httpx` path.
- **STORY-014b** (draft) carries the five read-only tab endpoints — refine with STORY-015.

## Tooling note
The `httpx`/`starlette.testclient` deprecation warning is folded into STORY-035 (its resolution
may involve a dependency change — a planning/retro tooling decision when that story is scheduled).
