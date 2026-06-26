---
id: STORY-029
title: Audit frozen value/result types for unenforced coherence invariants
type: chore
---

## Context
Follow-up from Sprint 8 review. Three sprints running, the quality reviewer has raised the SAME
MAJOR: a frozen value/result type whose fields carry a coherence invariant that is documented but
not ENFORCED at construction — `Verdict` (STORY-025, maintenance↔health-is-None), `AntiFlapOutcome`
(STORY-028, not(`proposed_status` set AND `internal_warning`)), and `SkewResult` (STORY-026,
`skewed == bool(lagging_signals)`). Each was fixed reactively with a `model_validator(mode="after")`.
This chore checks whether any OTHER existing frozen type in `core/` has the same latent gap, so the
pattern is closed proactively rather than caught one-more-time in a future review. Pairs with the
sprint-8 working agreement that requires such invariants be enforced + tested going forward.

## Acceptance Criteria (refined — PO-approved 2026-06-26)
- [ ] AC1: Every frozen Pydantic value/result type under `backend/src/core/` is reviewed for a
      cross-field coherence invariant (mutually-exclusive fields; a flag that must agree with a
      payload; an Optional that must be set/unset based on another field). The audit list + finding
      per type is recorded in this story file.
- [ ] AC2: Any type found with an unenforced invariant gains a `model_validator(mode="after")`
      enforcing it + a test for both the rejected and the valid shapes (mirroring `Verdict` /
      `AntiFlapOutcome` / `SkewResult`). If NONE are found, that is a valid outcome — record "no
      further gaps" with the audited list.
- [ ] AC3: `lint-imports` green; all existing tests pass unchanged; `pytest` green.

## Resolved Questions
- None. Scope is `backend/src/core/` frozen value/result types only (domain + services).

## History
- 2026-06-26: created from Sprint 8 review (PO asked for a follow-up to the recurring value-object
  coherence MAJOR). Status: ready — bounded audit, no open questions. Estimate: 1.
