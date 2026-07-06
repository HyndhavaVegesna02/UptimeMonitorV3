# Sprint 36 — retro (2026-07-06)

**Outcome:** 6/6 accepted (STORY-050 + STORY-043 + STORY-047), fast-forward merged to main
at `f81c7d4`. Eleventh consecutive clean sprint, and the first to deliver above measured
velocity (a PO-directed 6/5 over-commit that never bit). No hotfixes, no effort-cap trips,
no blocked stories; wiki current at every gate.

## What went well
- Three clean single dispatches, strictly sequential over the shared `composition/run.py`
  surface — no collisions, no rework.
- The full pipeline earned its cost on 050: the spec reviewer's design-pin coverage table
  caught the one honest gap (the AC-literal ≥3-consecutive-failures case), fixed in a
  ten-line same-session follow-up; the quality reviewer independently verified the asyncio
  sharp edges (try-block extent, CancelledError in 3.13, no busy-loop) — verdict
  "exemplary".
- Crash recovery (2026-06-25 rule) absorbed its second real incident this week
  (sprint-35's implementer session-limit death) with zero lost work — the commit-per-green
  cadence plus the trivial-tail rule is functioning as the safety net it was designed as.
- Parked-sprint bookkeeping worked: sprint 35 stayed untouched on its branch with a
  verbatim board snapshot; sprint 36 ran from main without entangling the two.

## The near-miss (and the amendment it produced)
STORY-043's entrypoint `load_dotenv()` would have made four pre-existing entrypoint tests
silently load the REAL repo `.env` (live secrets) into the test process. The implementer
caught and patched all four unprompted — but nothing in the standing process required that
audit; the save was diligence, not design. **Amendment (PO-approved, appended to
working-agreements.md):** a story adding side effects to a process entrypoint must
enumerate and hermetically audit every existing test driving that entrypoint, in the same
story, with the audit stated in the implementer's report.

## Carry-over notes
- Sprint 35 (deployment) remains parked; resume recipe in `sprint-current.yaml`'s PARKED
  SPRINT NOTE. Its rebase onto the new main WILL conflict in `pyproject.toml` (uvicorn
  move vs the new python-dotenv line), `CLAUDE.md`, and `.scrum/` files — expected and
  documented; nine-gate re-run required after the rebase (edge-case #2).
- Standing observability thread (three sightings now): STORY-050's log-only decision +
  the debug-sprint's loop-liveness candidate + STORY-051's no-per-cycle-telemetry note all
  point at the same future story — "the loop's health is visible somewhere other than
  logs." Worth refining once deployment lands.
- Remaining backlog after this sprint: STORY-017 (parked, 5), drafts 046 (2), 052 (1),
  053 (3). The known project tail is ~11 points.
