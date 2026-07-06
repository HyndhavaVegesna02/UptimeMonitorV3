# Sprint 34 — retro (2026-07-06)

**Outcome:** 5/5 accepted (STORY-051 + STORY-015f), fast-forward merged to main at
`72f323d`. Tenth consecutive clean sprint. No hotfixes, no effort-cap trips, no blocked
stories, no estimate misses, wiki drift zero at every gate.

## What went well
- Both stories passed first-pass: 051 was a pure gate close-out of an already-live-verified
  fix; 015f went implementer → spec PASS (all ACs MET) → quality APPROVE (0C/0M) → gate →
  live spot check with zero fix loops.
- **The pipeline's cross-checking caught the orchestrator's own error.** The 015f
  implementer noticed `test_post_maintenance_invalid_times` contradicted its brief's
  contract pin and flagged it rather than building silently to the wrong pin — exactly the
  independent-eyes behavior the multi-stage pipeline exists for. The quality reviewer then
  traced the precise live failure surface (the Pydantic blob mapping to the Component
  field), sharpening STORY-052's re-scope.
- The 2026-07-04 pair of agreements earned their keep again on their second outing: the
  pinned wire sample flowed verbatim into fixtures, and the live render-vs-wire spot check
  confirmed the half-open state derivation against reality.
- The debug-sprint → planning → sprint chain worked: the morning's debug evidence (two
  live verifications of the 051 fix) let the sprint carry the fix as a 2-point gate-only
  close-out instead of re-deriving anything.

## The incident (and the amendment it produced)
The planning consumer-DTO check WRONGLY concluded the backend does not 422
end-before-start maintenance windows: it read one file (`maintenance/validation.py`) and
live-probed only a valid window. The ordering check lives in the DOMAIN layer. Cost: an
unnecessary PO decision at planning (the AC3 trim — which happened to stay true-but-
narrower), a falsely-scoped STORY-052 requiring same-day correction (`8b46295`), and a
disclosure at review. Root cause: the 2026-07-04 agreements pin units/scale from producing
code but nothing required EXERCISING claimed-absent failure behavior.

**Amendment (PO-approved, appended to working-agreements.md):** Planning contract checks
prove claimed producer gaps by probing the failure path live — "the producer lacks X" must
be shown by a live probe of X actually failing (or the producer's own endpoint test
driving that exact case), never inferred from reading one validator/layer, before it may
amend an AC or be filed as a defect.

## Carry-over notes
- STORY-052 (draft, re-scoped): clean edge message for the ordering 422 + inline frontend
  mapping; carries two sprint-34 quality minors in the same area.
- Remaining 015f minors (awareness-level, recorded in the sprint board's open_minors):
  FieldError JSX dedup, aria-describedby association, datetime NaN guard, select focus
  ring — none filed as stories; candidates if the PO wants a frontend-polish chore.
- Sprint-35 outlook (non-binding): STORY-043 (.env loading, 2) + STORY-047 (minors chore,
  1) are the two ready stories; STORY-052/046/050/017 need refinement first. Deployment
  (STORY-017) remains the PO's stated end goal for the local-stack era.
