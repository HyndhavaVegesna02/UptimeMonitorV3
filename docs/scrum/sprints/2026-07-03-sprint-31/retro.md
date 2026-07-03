# Sprint 31 — Retrospective

**Sprint result:** STORY-048 accepted 5/5 (velocity now 3, 5, 5, 5, 5 over the last five).
Third consecutive zero-fix-loop sprint; seventh consecutive clean accept.

## What went well
- **The removability directive survived implementation intact:** the PO's temporary-feature
  order was turned into a first-class AC (AC7) + plan decisions at lock, and both reviewers
  verified it STRUCTURALLY — seam-comment grep over the whole tree, byte-identical
  `core/domain`/`core/services`, object-identity OFF-path tests, and an entry-by-entry check of
  the REMOVAL inventory against the actual diff. Deleting this feature later is a mechanical
  1-pointer with a written recipe.
- **Zero blocking review findings again** — spec PASS (all 46 story tests reviewer-run,
  DB-gated halves executed), quality APPROVE with only two cosmetic minors.
- **Crash recovery + fresh-agent rules both fired and both worked:** the implementer stall lost
  zero work (T1–T5 committed; coherent T6 tail recovered), and the mid-run reviewer kills were
  absorbed by clean re-dispatches.

## What dragged (incidents)
1. **Second consecutive implementer 600s-watchdog stall, in the IDENTICAL spot** (sprint 29:
   STORY-045; sprint 31: STORY-048): all code committed, the complete wiki pass finished but
   uncommitted as one batch. Root cause: the wiki pass is briefed as one monolithic final task,
   so none of it commits until all of it is done — the commit-after-green cadence was being
   applied to code but not to prose. → Amendment adopted (below).
2. **Both first-dispatch Opus reviewers were terminated mid-run by a session limit** (no
   verdicts; resets 8:50pm IST). External constraint, not process: the 2026-06-25 fresh-agent
   rule was the correct response and both re-dispatches passed. Observation only — no rule; the
   only lesson is that a killed reviewer's partial notes are never treated as a verdict, which
   was already honored.

## Wiki drift stats
- Sweep at compile pass: 13/13 CURRENT, 0 broken links (run independently twice — orchestrator
  and spec reviewer). No article stale ≥1 sprint.
- New article: `sample-mode.md` — carries the feature's Facts AND its deletion recipe; the
  first article in the wiki whose primary job is to make future REMOVAL safe.
- Standing note (from sprint 30, still open): `composition/seed.py` is in no article's
  `code_refs` — candidate future compile-pass cleanup.

## Amendments
- **Proposed 1, adopted 1 (PO approved 2026-07-03):** *The wiki blast-radius pass commits
  article-by-article.* Appended to `working-agreements.md` with the sprint-29/31 stall pattern
  as the motivating incident. Every future implementer brief carries it.

## Tooling friction
None. No tooling change requested.

## Carry-forward notes for next planning
- **STORY-049 (Dashboard sample-switch toggle, 2) is now unblocked** — its API landed. Natural
  pairing: 049 + STORY-015d (Availability tab, 3) = 5 pts, giving the sprint a visible
  demo: flip the switch in the UI, watch availability drop on the new two-grain tab.
- Also ready: STORY-015e (3), STORY-015f (3), STORY-015g (2), STORY-043 (.env defect, 2),
  STORY-047 (chore, 1 — now five folded items). STORY-017 (deployment) remains draft — the PO's
  stated end goal; refine before it can enter a sprint.
- Reminder for the sample switch's lifetime: the PO flips it via `PUT /api/v1/sample-mode`
  (curl) until 049 ships the UI toggle; simulated rows are always `raw_ref LIKE 'sample-mode%'`.
