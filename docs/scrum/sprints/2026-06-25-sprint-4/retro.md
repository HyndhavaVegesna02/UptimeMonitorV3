# Sprint 4 — Retrospective

**Committed/accepted:** 5/5 pts (STORY-008). One story, accepted at review, merged to main
(`40ed985`). Velocity history now 8 / 6 / 6 / 6 / 5.

## What went well
- **Single-story sizing was honest and accurate.** Capacity was 6; we committed 5 and
  delivered 5 with no effort-cap pressure and no carry. Resisting the 10-pt "both stories"
  overcommit kept the review non-empty-handed.
- **The fresh-agent fix loop landed first try.** The Sprint 3 amendment (fix loops use a fresh,
  tightly-briefed agent) paid off directly — the duplication MAJOR was fixed in one dispatch
  with no transcript-bloat crashes.
- **The reviewer split did its job.** Spec review (Opus) confirmed all 5 AC genuinely tested
  (expected-value assertions, multi-location + mixed-batch coverage); quality review (Opus)
  independently caught the real duplication the spec lane correctly ignored.
- **No blockers, no hotfixes, no stale wiki.** All five pre-existing articles stayed current;
  one new verified article (`dynatrace-adapter.md`) folded in the sprint's learning.

## What dragged
- **A predictable duplication MAJOR cost a fix loop.** Two per-type normalizers flattening to
  the same canonical shape copy-pasted the assembly. Foreseeable from the story shape; the brief
  described the per-type pattern but never said "share the common assembly."
- **The implementer wrote board state in a non-standard format.** The implementer rewrote
  `sprint-current.yaml`'s `dod_evidence` as free strings and set blast-radius/pause fields, which
  the orchestrator had to reconcile back to the structured schema before closing.

## Estimate vs actual
- STORY-008: estimated 5, actual ~5 (one fix loop, within normal pipeline). Estimate held.

## Amendments adopted (PO-approved 2026-06-25 — both written to working-agreements.md)
1. **Parallel-shape stories carry a "share the assembly" instruction** — briefs for N-variant
   same-shape work must direct extracting the common assembly up front; checked by the quality
   reviewer. (Motivated by the STORY-008 duplication MAJOR + fix loop.)
2. **Implementers never write sprint board state** — implementers report DoD evidence/blast-radius
   in their final message only; the orchestrator is the sole writer of `sprint-current.yaml`.
   (Motivated by the STORY-008 non-standard evidence rewrite.)

## Wiki drift
None stale ≥3 sprints. All articles verified within the last two sprints.

## Carried into Sprint 5
- STORY-009 (pull loop + watermarks, 5 pts) — refined this session (scheduler = asyncio),
  `ready`, consumes this sprint's `fetch_observations` adapter entry point.
- STORY-020 + STORY-021 — `draft` follow-up chores from this review (named malformed-row error;
  native_id DQL guard). STORY-021 has an open question (reject vs escape) to resolve at refinement.
