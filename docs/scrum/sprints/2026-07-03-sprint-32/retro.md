# Sprint 32 — Retro

**Outcome:** 5 committed / 5 accepted ("accept both", 2026-07-04) — 8th consecutive
full-acceptance sprint. One fix loop (STORY-015d, percent-scale), zero blocked stories,
zero watchdog stalls (first stall-free sprint since 28).

## What went well

- **No implementer stalls.** Both Sonnet dispatches finished cleanly; the sprint-31
  article-by-article wiki-commit amendment got its first live exercise and did its job — no
  tail-recovery needed.
- **The PO-requested live stack paid for itself twice**: it exposed the percent-scale defect at
  review prep AND surfaced the live loop's transient-error fragility (→ STORY-050 draft).
- Estimates accurate; STORY-049's gate-only pipeline was proportionate (clean 2-pointer, no
  reviewer cost); the sample-mode REMOVAL inventory discipline extended naturally to the
  frontend seams.
- First live-browser (Playwright) verification used at review prep — now codified as the
  render-vs-wire spot check amendment.

## What dragged — incidents

1. **STORY-015d fix loop: the percent-scale defect passed 146 green tests and BOTH Opus
   reviewers.** Wire values are 0–1 fractions; the plan's contract section pinned field types
   but not scale, and its "99.87%" example implied percent; the implementer invented
   percent-scale MSW fixtures matching that assumption; both reviewers verified code-vs-fixtures
   (consistent, so green). Only rendering live data showed "1.00%" for a fully-up component.
   Fifth "green tests, wrong contract" incident (rigged AC3 s17, over-mock s20, deleted tests
   s21, committed-tree s14/19 family) — and the first whose root cause sits in PLANNING
   precision, not implementer behavior. → Amendments #1 and #2 below.
2. **Opus session limit killed the second-pass reviewer mid-run** (no verdict) — second sprint
   running with this shape (sprint 31: both first-dispatch reviewers). Fresh re-dispatch after
   the reset passed. External quota, not process — recovery path (fresh agent after reset) is
   established; no amendment.
3. **The live loop crashed on a single transient Grail SSL handshake timeout** (~2.5h in),
   killing the whole process. Filed as STORY-050 (draft defect) with the traceback; refinement
   must settle the transient-vs-fatal error taxonomy. Also relevant to STORY-017 deployment
   (a crash-looping worker on Railway would be an operational hazard).
4. Minor: the harness reaped the background stack processes between turns repeatedly;
   resolved by detaching them (nohup). Operational note only.

## Amendments adopted (PO: "Both", 2026-07-04)

1. **Consumer-DTO planning check pins units/scale; fixtures derive from a real sample** —
   extends the 2026-07-02 agreement; scale/units read from producing code, stated in the plan's
   contract section; MSW fixtures from real response samples, never invented scales.
2. **Live render-vs-wire spot check at review prep for consumer/rendering stories** — when a
   stack is available, compare at least one rendered value against the raw wire value before
   calling the review.

Both appended to `working-agreements.md` (2026-07-04).

## Tooling

No changes proposed (the two allowed moments were available; nothing recurring beyond the Opus
quota, which tooling can't fix).

## For next planning

- **STORY-017 (deployment) is still draft** — deployment is the stated end goal (Railway +
  Vercel + Neon + CORS); recommend refining it next, alongside STORY-050 (live-loop resilience,
  draft) and STORY-043 (.env loading defect, ready) — the three compose into a "runs reliably
  outside a babysat terminal" theme.
- Remaining ready tab stories: 015e (Check History, 3), 015f (Maintenance, 3), 015g
  (Publications, 2); chore STORY-047 (1). STORY-046 still draft (design question open).
- Backlog candidates noted in review.md, not filed (PO's call): live-clock window re-slide;
  threshold-mapped bar color; in-flight spinner on the sample switch.
