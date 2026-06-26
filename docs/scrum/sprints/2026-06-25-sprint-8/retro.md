# Sprint 8 — Retrospective

**Committed/accepted:** 6/6 pts (STORY-028 = 3, STORY-026 = 3). Both accepted, merged to main
(`a5b7f7e`). Velocity history now 8 / 6 / 6 / 6 / 5 / 6 / 6 / 6 / 6.

## What went well
- **The STORY-024 split worked — the fourth successful "split the 8, ship the clean half."** Pulling
  anti-flap (stage 3, injectable thresholds) out of STORY-024 and leaving decide (stage 4, blocked on
  proposals) gave two clean, reviewable 3-pt stories. Zone 4's pure-logic surface is now complete
  (collapse, streak, anti-flap, availability, skew).
- **Both new stories were pure + injectable** (thresholds; peer watermarks) — no config-loading or
  proposal-persistence dependency dragged in, consistent with the established Zone 4 pattern.
- **The sprint-7 wiki-coverage agreement held:** the new `skew.py` was added to the article's
  `code_refs` proactively, so its Facts are staleness-covered from day one.
- **Estimates held**; both fix loops were contained single-MAJOR loops.

## What dragged
- **The SAME quality MAJOR for the third sprint running.** Both `AntiFlapOutcome` (STORY-028) and
  `SkewResult` (STORY-026) shipped a documented-but-unenforced cross-field coherence invariant — the
  identical finding to `Verdict` (STORY-025). Each cost a fix-loop dispatch to add a `model_validator`
  after the fact. The implementers documented the invariant but didn't enforce it; the reviewer briefs
  cited the precedent, but the implementer briefs didn't direct it.
- **Leftover-container friction:** a stuck `uptime_pg_pytest` docker container held port 55432 and
  broke `dev_db.py up` (~twice), needing a manual `docker rm -f` before retry.
- **Wiki line-citation drift:** `file:line` addresses in the Zone 4 article had drifted as the module
  grew; caught and corrected at the compile pass (addresses only, code unchanged).

## Estimate vs actual
- STORY-028: 3 estimated, ~3 actual (one fix loop). STORY-026: 3 estimated, ~3 actual (one fix loop).

## Wiki drift
No article stale ≥3 sprints. The Zone 4 article's drifted line citations were re-aligned this compile
pass; the convention "Facts cite addresses" is otherwise holding.

## Amendments adopted (PO-approved 2026-06-26)
1. **A frozen value/result type with a cross-field coherence invariant must ENFORCE it at construction**
   (a `model_validator(mode="after")` + a test, in the same story; the implementer brief must direct
   it). Written to working-agreements.md. (Motivated by the three-sprint recurring MAJOR.) STORY-029
   audits existing types for the same gap.
2. **Make `dev_db.py up` idempotent against a leftover container** — a concrete code fix, tracked as
   chore **STORY-030** (ready) rather than a vague rule. (Motivated by the port-55432 friction.)

## Carried into Sprint 9
- STORY-012 (proposal lifecycle, 5, draft) — Zone 5; the natural unblock for STORY-024 (decide).
- STORY-024 (decide, stage 4, 3, draft) — depends on STORY-012.
- Chores: STORY-027 (lazy import), STORY-029 (value-type audit), STORY-030 (dev_db idempotency) — all
  ready, 1 pt each.
