# Sprint 9 — Retrospective

**Committed/accepted:** 6/6 pts (STORY-012 = 3, STORY-013 = 3). Both accepted, merged to main
(`f5efa16`). Velocity history now 8/6/6/6/5/6/6/6/6/6. **First sprint implemented externally
(PO / Gemini); orchestrator planned + reviewed.**

## What went well
- **The new external-implementation workflow held cleanly.** Gemini built faithfully to `plan.md`,
  respected the boundaries (never touched `sprint-current.yaml` or `working-agreements.md`), kept
  `lint-imports` green throughout, and the one MAJOR routed back and was fixed correctly in a single
  loop. The mechanical floor + the Opus spec/quality reviews did their job on externally-written code.
- **The value-object coherence agreement was applied PROACTIVELY.** `StatusProposal` shipped with its
  `model_validator` from the start — the MAJOR that recurred three sprints running (Verdict →
  AntiFlapOutcome → SkewResult) did NOT recur on the new value type. The sprint-8 amendment worked.
- **Estimates held** (both 3s; STORY-013 clean, STORY-012 one contained fix loop).

## What dragged
- **One MAJOR: a fake/adapter behavior divergence.** `PostgresProposalRepository.resolve` silently
  no-oped on a bad/terminal id while `FakeProposalRepository.resolve` RAISED — so the fake-backed
  unit tests gave false confidence; only the quality reviewer caught it. Compounding cause: `plan.md`
  specified `resolve` as "move an open proposal" without stating the error-on-not-open behavior, and
  an external implementer builds literally to the plan.
- **Wiki line-citation drift again** — Gemini's `proposal_repository.py` citations were slightly off
  and the fix loop shifted them further; caught + corrected at the compile pass (the cited files were
  code_ref-covered, so the staleness check held; only the line anchors drifted).
- **Environmental:** Docker Desktop was down at lock, so the DB-gated baseline couldn't run then
  (re-confirmed green once Docker was back; no schema change since Sprint 8).

## Estimate vs actual
- STORY-012: 3 / ~3 (one fix loop). STORY-013: 3 / 3 (clean).

## Wiki drift
No article stale ≥3 sprints. `architecture-boundary.md` rehabilitated (first `adapters/outbound` +
2nd `composition` both-sides importer; contracts unchanged). Recurring line-citation drift is real
but bounded — caught every compile pass; not worth a process change yet beyond the existing
"Facts cite addresses" discipline.

## Amendments adopted (PO-approved 2026-06-26 — both written to working-agreements.md)
1. **A port's fake and its real adapter must AGREE on edge-case behavior**, verified by the same
   contract test run against both. (Motivated by the `resolve` fake-raised / adapter-no-oped MAJOR.)
2. **The plan must specify a port/repository method's edge/error behavior explicitly** (not-found,
   wrong-state, conflict, empty), since external implementation builds literally to the plan.
   (Same incident, planning-side.)

## Carried into Sprint 10
- STORY-024 (decide, stage 4, 3, draft) — both halves it needs (proposals + publish) now exist;
  resolve its "current published status" read seam at refinement, then it ties Zone 4→5 together.
- Chores: STORY-027 / 029 / 030 / 031 (1 pt each, ready).
