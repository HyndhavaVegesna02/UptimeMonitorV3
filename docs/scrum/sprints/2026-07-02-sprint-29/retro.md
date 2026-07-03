# Sprint 29 — Retrospective

**Held:** 2026-07-03, immediately after review. **Verdict context:** STORY-045 accepted 5/5 with
follow-up chore STORY-047; fifth consecutive clean sprint (first-pass PASS/APPROVE, zero fix
loops).

## What went well
- **Estimate on target.** 5 pts, 1 attempt, no effort-cap pressure. The plan's pinned design
  decisions (D1–D5) held up — neither reviewer found a design-level fault, and the one plan
  inaccuracy (the "export via `__init__`" note for the domain error) was correctly overridden by
  the implementer mirroring the real peer convention.
- **The commit-after-green cadence proved itself under a real crash.** The implementer stalled
  (600s stream watchdog) at the end of the story; all four code steps were already committed, so
  recovery per the 2026-06-25 agreement cost one orchestrator inspection + one commit — no
  re-dispatch, no lost work, no fix loop.
- **The Sprint-28 retro amendment (single non-concurrent DB-gated runs) was followed** — one clean
  pytest run (444 passed), no false reds, no diagnose/reset cycle.
- **The mechanical wiki sweep caught what hand-picking missed** (2 articles stale via shared
  `code_refs`: `run.py` in ingest-service-and-pull-loop, `settings.py` in migrations-and-db) —
  the 2026-06-28 sweep agreement functioning exactly as designed.

## What dragged
- **The implementer stall itself** — cause external (stream watchdog, likely a long transcript
  late in a 5-pt story), but it stranded the entire finished 5-article wiki batch UNCOMMITTED,
  because docs were treated as commit-at-the-end work. Recovery was cheap this time; a stall one
  step earlier (mid-edit) would have forced a re-dispatch for the whole T5.
- **Blast-radius hand-picking** — the implementer updated the 5 obvious articles and missed the 2
  reachable only via shared-file `code_refs`, leaving the orchestrator sweep to do story-level
  work at the compile pass.

## Amendments
Two were proposed; the PO approved **neither** (2026-07-03) — rationale: both incidents were
absorbed by existing mechanisms (crash-recovery agreement; orchestrator compile-pass sweep), so no
new rule is warranted on this evidence.
1. *Rejected:* wiki/doc edits commit with the same cadence as code steps.
2. *Rejected:* implementer briefs carry the sweep one-liner; implementers run it before reporting.
Per ceremony rules, neither is re-proposed unless new evidence accumulates (e.g. a stall that
actually loses doc work, or a third hand-picking miss).

## Tooling
No friction, no changes proposed. (Tooling unchanged this sprint: none added at planning either.)

## Carry-forward
- STORY-047 (1 pt, ready) — the two quality minors, filed at review.
- Sprint-30 planning candidate flagged at Sprint-29 planning: STORY-044 (availability/topology
  API, 5 pts, ready) — unblocks the last two data tabs 015d/015e. STORY-043 (.env defect, 2 pts,
  ready) also open; STORY-046 and STORY-017 still drafts (need refinement before any sprint).
