# Sprint 7 — Retrospective

**Committed/accepted:** 6/6 pts (STORY-011 = 5, STORY-025 = 1). Both accepted, merged to main
(`205e1fe`). Velocity history now 8 / 6 / 6 / 6 / 5 / 6 / 6 / 6.

## What went well
- **The skew split kept STORY-011 a clean 5.** Splitting the cross-signal skew flag into STORY-026
  at refinement (the third successful split — after STORY-010's pipeline and STORY-011 itself) left a
  focused two-grain-math + rollup story that reviewed cleanly.
- **The reviewer split earned its keep again.** Spec PASSed all 6 AC; quality independently caught a
  subtle CRITICAL (floor-vs-ceil cycle bucketing) that no AC-level check would have surfaced.
- **The fresh-agent fix loop landed first try**, and the implementer correctly flagged + handled a
  STORY-025 edge: an existing test asserted the very shape the new invariant forbids, so it was
  replaced (a legitimate, flagged exception to "existing tests pass unchanged").

## What dragged
- **A reviewer hit a session limit** (the first STORY-011 quality reviewer returned nothing); a fresh
  one was re-dispatched cleanly (reviews are read-only, so safe to retry). Second session-limit this
  project — environmental, not a process flaw.
- **The CRITICAL slipped to review because every test used a divisible window.** The partial-tail
  (non-aligned) case — the realistic "last 24h from now" shape — was untested.
- **A wiki coverage gap went undetected for two sprints.** `canonical-types-and-ports.md` documented
  `pipeline.py`'s collapse/streak Facts but never listed `pipeline.py` in its `code_refs`, so those
  Facts were uncovered by the staleness check (silent-rot risk). The compile pass found it and
  extracted [[core-pipeline-and-availability]].

## Estimate vs actual
- STORY-011: estimated 5, actual ~5 (one fix loop, within normal pipeline). STORY-025: 1, clean.

## Wiki drift
No article stale ≥3 sprints. The narrowed `architecture-boundary.md` again did not go falsely stale.
The catch-all coverage gap is now fixed by extraction + amendment #1 below.

## Amendments adopted (PO-approved 2026-06-25 — both written to working-agreements.md)
1. **Every wiki Fact's cited file must be covered by the article's `code_refs`** — a Fact citing an
   uncovered file is a DoD/compile-pass finding (extend code_refs or split). (Motivated by the
   two-sprint pipeline.py coverage gap.)
2. **Range/window math must test a NON-aligned boundary case, not just clean inputs** — extends the
   sprint-6 empty-input agreement. (Motivated by the floor/ceil CRITICAL that all-divisible tests
   missed.)

## Carried into Sprint 8
- STORY-024 (anti-flap + decide, 5, draft) — STILL needs the per-app config mechanism resolved
  (may need a config-loading precursor story); it has blocked two sprints of Zone 4 completion.
- STORY-026 (skew flag, 3, draft) — two open questions (peer-set source, result shape).
- STORY-027 (hoist the lazy test import, 1, ready) — Sprint 7 review follow-up.
