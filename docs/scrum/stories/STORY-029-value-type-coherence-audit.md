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
- [x] AC1: Every frozen Pydantic value/result type under `backend/src/core/` is reviewed for a
      cross-field coherence invariant (mutually-exclusive fields; a flag that must agree with a
      payload; an Optional that must be set/unset based on another field). The audit list + finding
      per type is recorded in this story file.
- [x] AC2: Any type found with an unenforced invariant gains a `model_validator(mode="after")`
      enforcing it + a test for both the rejected and the valid shapes (mirroring `Verdict` /
      `AntiFlapOutcome` / `SkewResult`). If NONE are found, that is a valid outcome — record "no
      further gaps" with the audited list.
- [x] AC3: `lint-imports` green; all existing tests pass unchanged; `pytest` green.

## Audit Findings

We audited all 12 frozen Pydantic models under `backend/src/core/` (plus the DecideAction enum):

1. **`Provenance`** (`src.core.domain.signal`):
   - Fields: `system`, `native_id`, `native_kind`
   - Invariant: None (fields represent independent metadata)
   - Status: Enforced (N/A)
2. **`SignalObservation`** (`src.core.domain.signal`):
   - Fields: `signal_key`, `observed_at`, `health`, `source_event_id`, `source`, `location`, `latency_ms`, `raw_ref`
   - Invariant: None (independent telemetry run attributes)
   - Status: Enforced (N/A)
3. **`StatusChange`** (`src.core.domain.status`):
   - Fields: `component_id`, `status`
   - Invariant: None
   - Status: Enforced (N/A)
4. **`IngestResult`** (`src.core.domain.status`):
   - Fields: `accepted`, `rejected`
   - Invariant: None
   - Status: Enforced (N/A)
5. **`Verdict`** (`src.core.domain.verdict`):
   - Fields: `signal_key`, `observed_at`, `health`, `under_maintenance`
   - Invariant: `under_maintenance` <-> `health is None`
   - Status: Enforced (`_require_maintenance_health_coherence` at `verdict.py:54`)
6. **`StatusProposal`** (`src.core.domain.proposal`):
   - Fields: `component_id`, `from_status`, `to_status`, `state`, `reason`, `proposed_at`, `resolved_at`, `id`
   - Invariant: `state == ProposalState.OPEN` <-> `resolved_at is None`
   - Status: Enforced (`_require_resolved_at_coherence` at `proposal.py:66`)
7. **`Streak`** (`src.core.services.pipeline`):
   - Fields: `health`, `length`
   - Invariant: None
   - Status: Enforced (N/A)
8. **`AntiFlapThresholds`** (`src.core.services.pipeline`):
   - Fields: `major`, `partial`, `degraded`, `recovery`
   - Invariant: None
   - Status: Enforced (N/A)
9. **`AntiFlapOutcome`** (`src.core.services.pipeline`):
   - Fields: `proposed_status`, `internal_warning`
   - Invariant: `proposed_status is not None` and `internal_warning` are mutually exclusive
   - Status: Enforced (`_require_status_warning_coherence` at `pipeline.py:171`)
10. **`SignalFeeder`** (`src.core.services.skew`):
    - Fields: `signal_key`, `watermark`, `interval`
    - Invariant: None
    - Status: Enforced (N/A)
11. **`SkewResult`** (`src.core.services.skew`):
    - Fields: `skewed`, `lagging_signals`
    - Invariant: `skewed == bool(lagging_signals)`
    - Status: Enforced (`_require_skewed_lagging_signals_coherence` at `skew.py:75`)
12. **`AvailabilityResult`** (`src.core.services.availability`):
    - Fields: `availability_pct`, `completeness_pct`, `total_verdicts`, `passing_verdicts`, `maintenance_verdicts`, `gap_verdicts`, `distinct_locations`, `window`, `computed_at`
    - Invariant:
      - `availability_pct` is None iff `total_verdicts - gap_verdicts - maintenance_verdicts == 0` (degenerate availability denominator).
      - `completeness_pct` is None iff `total_verdicts * distinct_locations == 0` (degenerate completeness denominator).
    - Status: **UNENFORCED** (Gaps identified!)

13. **`DecideAction`** (`src.core.services.decide`):
    - Fields: None (Enum)
    - Invariant: None
    - Status: Enforced (N/A)

## Resolved Questions
- None. Scope is `backend/src/core/` frozen value/result types only (domain + services).

## History
- 2026-06-26: created from Sprint 8 review (PO asked for a follow-up to the recurring value-object
  coherence MAJOR). Status: ready — bounded audit, no open questions. Estimate: 1.
- 2026-06-27: performed audit during Sprint 10; identified gaps in `AvailabilityResult`.

