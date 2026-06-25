---
id: STORY-025
title: Enforce the Verdict maintenance<->health invariant at construction
type: chore
---

## Context
Follow-up from Sprint 6 review (STORY-010 quality-review minor #1, non-blocking). The `Verdict`
domain type (`backend/src/core/domain/verdict.py`) represents both a normal health verdict and a
maintenance cycle in one type: a maintenance verdict is `under_maintenance=True, health=None`; a
normal verdict is `under_maintenance=False` with a set `health`. That invariant is DOCUMENTED but
not ENFORCED — an incoherent `Verdict(under_maintenance=True, health=Health.UP)` or
`Verdict(under_maintenance=False, health=None)` constructs fine today. It is currently latent
(only `collapse` builds `Verdict`s, and it always honors the invariant), but a future hand-built
`Verdict` reaching `streak` would surface as an opaque pydantic enum `ValidationError` rather than
a legible message. Closing it is consistent with the house "validate at construction so bad data
surfaces immediately" stance (see `signal.py`'s `observed_at` validator).

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: Constructing a `Verdict` violating the invariant raises a clear validation error:
      `under_maintenance=True` requires `health is None`; `under_maintenance=False` requires a
      set `health`. Implemented as a Pydantic `model_validator` (mode="after") on `Verdict`,
      matching the frozen-model construction-time-validation pattern in `signal.py`.
- [ ] AC2: The two valid shapes still construct fine (normal verdict with a health; maintenance
      verdict with `health=None`); `collapse`/`streak` and all existing STORY-010 tests pass
      unchanged.
- [ ] AC3: A test covers both invalid shapes (raises) and both valid shapes (constructs).
      `lint-imports` stays green (change is confined to `core/domain/`).

## Resolved Questions
- None. Approach fixed (a `model_validator(mode="after")` on `Verdict`) at refinement, 2026-06-25.

## History
- 2026-06-25: created from Sprint 6 review (PO asked the Verdict-invariant minor become a
  follow-up story). Status: ready — no open questions; comment confined to `core/domain/verdict.py`.
  Estimate: 1.
