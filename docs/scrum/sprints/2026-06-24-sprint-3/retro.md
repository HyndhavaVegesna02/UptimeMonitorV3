# Sprint 3 — Retrospective

**Date:** 2026-06-25 · Process inspection, not product.

## Health metrics
- **Velocity 6/6 accepted** — fourth consecutive clean sprint (S0 8/8, S1 6/6, S2 6/6, S3 6/6;
  trailing-3 mean = 6).
- Estimates accurate: STORY-019 (3) and STORY-007 (3) both delivered at estimate. STORY-019's
  overrun was infra crashes, not under-estimation.
- One fix loop (STORY-019) — the review pipeline working as designed (a real MAJOR caught before
  the PO saw it), not a process miss. Zero estimate misses, zero hotfixes.

## What we inspected
1. **Agent connection-drop crashes (the disruptive event).** Resuming the STORY-019 implementer
   for its fix loop crashed twice with `API Error: Connection closed mid-response` — an artifact
   of a large transcript producing a long response. It left uncommitted work and a leaked
   `test_zz_*.py` artifact in `backend/tests/`. Recovery worked only because I stopped re-resuming:
   preserved the coherent committed work, cleaned the artifact, and finished via a fresh
   tight-brief implementer (small transcript → completed first try).
2. **A MAJOR slipped past the implementer (spawn-time container leak).** Caught by quality review,
   so the outcome was fine — but the implementer brief had described the container lifecycle
   without explicitly demanding teardown on partial-setup failure.
3. **Recurring `lint-imports.exe` launcher corruption.** Surfaced again at the green-baseline check
   and during reviews; I had been repeating the "regenerate it" instruction in every brief.

## Amendments (PO decisions — BOTH adopted)
- **ADOPTED — Fix loops use a fresh agent; verify the tree after any agent crash.** Working
  agreement added (2026-06-25): for fix loops / continuations on a large-transcript agent,
  dispatch a fresh focused-brief subagent instead of re-resuming; after any crash, inspect the
  tree (preserve coherent work, discard scraps, clean leaked artifacts) before proceeding.
- **ADOPTED — Resource-lifecycle stories require teardown-on-failure in the brief.** Working
  agreement added (2026-06-25): stories creating containers/temp files/connections/subprocesses
  must have the brief demand teardown on every failure path (including mid-setup) + a no-leak
  regression test.

## Wiki drift
- No stale articles. STORY-019/007 folded; `architecture-boundary.md` re-verified; new
  `persistence-adapters.md` created. Five articles, all re-stamped to the merge commit `08917c0`
  except `canonical-types-and-ports.md` (core unchanged → stays accurate at `ac1d468`).
- Folded the recurring `lint-imports.exe` "won't launch → regenerate" gotcha into
  `dev-setup-and-dod.md` so briefs can point to it instead of repeating the instruction.
- No article stale ≥3 sprints. Link-lint clean.

## Carry-forward
- Zone 2 complete (spine schema + repository adapters) + the shared throwaway-DB harness.
- Next (Sprint 4 planning): Zone 3 ingest — STORY-008 (Dynatrace adapter + DQL normalization, 5),
  STORY-009 (pull loop + watermarks + validation gate, 5). Both `draft` — refine before planning.
