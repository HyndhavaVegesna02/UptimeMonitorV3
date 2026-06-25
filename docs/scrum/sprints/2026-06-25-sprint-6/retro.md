# Sprint 6 — Retrospective

**Committed/accepted:** 6/6 pts (STORY-010 = 3, STORY-021/022/023 = 1 each). All accepted, merged
to main (`01ea878`). Velocity history now 8 / 6 / 6 / 6 / 5 / 6 / 6.

## What went well
- **The STORY-010 split was the right call.** Judging the 4-stage pipeline as ≥8 at refinement and
  shipping just stages 1–2 (collapse + streak, 3 pts) gave a clean, well-reviewed slice instead of
  a bloated story that would likely have blocked on the missing per-app config mechanism. Stages
  3–4 are a properly-scoped STORY-024 for later.
- **The sprint-5 narrowed-`code_refs` amendment paid off.** `architecture-boundary.md` did NOT go
  falsely stale this sprint even though we added `core/domain/verdict.py` + `core/services/
  pipeline.py` — exactly the every-sprint busywork the amendment was written to kill. The
  staleness check now flags it only when the boundary itself changes.
- **All three carried chores cleared**, closing the small debt from Sprints 4–5 (native_id guard,
  mixed-signal guard, stop-check comment). The mixed-signal guard turned a documented latent hazard
  into an enforced one.
- **Estimates accurate**; the one fix loop was a contained edge-case miss, not a complexity miss.

## What dragged
- **STORY-010's fix loop was a foreseeable empty-input edge case.** `collapse([])` ran `max(...)`
  on an empty generator and leaked `ValueError: max() iterable argument is empty` — a stdlib
  iterable message, not a domain statement — while its sibling `streak([])` already returned
  `None`. The asymmetry between two sibling functions was the tell; the quality reviewer caught it,
  costing a fix-loop dispatch.

## Estimate vs actual
- STORY-010: estimated 3 (post-split), actual ~3 (one fix loop, within normal pipeline). The split
  estimate held.
- STORY-021/022/023: each 1, each landed clean (STORY-023 comment-only, done directly by the
  orchestrator under the sprint-5 trivial-change agreement).

## Wiki drift
No article stale ≥3 sprints. The narrowed `architecture-boundary.md` stayed current without a
rehab pass — first sprint that amendment was tested, and it held. Pipeline Facts currently live in
`canonical-types-and-ports.md`; when STORY-024 grows the pipeline, extract a dedicated
`core-pipeline.md` article (noted for the next compile pass).

## Amendment adopted (PO-approved 2026-06-25 — written to working-agreements.md)
1. **A function over a collection must define and TEST its empty-input behavior** — raise a clear
   domain error (not a leaked stdlib message) or return a documented default; the empty-input test
   ships with the function, and its absence is a review finding. (Motivated by the STORY-010
   `collapse([])` MAJOR + fix loop.)

(A second candidate — extending the "orchestrator finishes trivial changes" agreement to comment-
only chores — was proposed and NOT adopted; the existing agreement's spirit already covered it.)

## Carried into Sprint 7
- STORY-024 (anti-flap + decide, 5, draft) — needs refinement: per-app config mechanism + proposal
  seam (two open questions).
- STORY-011 (availability calculator, 5, draft) — depends on collapse (now built).
- STORY-025 (enforce the Verdict maintenance↔health invariant, 1, ready) — review follow-up.
