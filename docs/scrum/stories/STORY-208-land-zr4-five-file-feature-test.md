---
id: STORY-208
title: Land ZR-4's guard — extend test_zone_layout to assert the five-file api feature SHAPE
type: chore
points: 1
status: draft
filed: 2026-07-31
---

> **DRAFT — needs a refinement pass before it may enter a sprint** (Definition of Ready: approved AC
> + estimate + no open questions). The estimate below is the audit's or the orchestrator's first cut,
> not a refined one.

## Context

Filed during sprint 66, the boundary/code-discipline audit. **Authoritative detail:**
`docs/scrum/wiki/zone-rules.md` — `ZR-4`'s Coverage verdict; STORY-196 §8 verified all ten features.

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
backend/tests/test_zone_layout.py TODAY asserts feature-SET equality against the
api-feature-independence contract and router registration -- but NOT the
five-file shape, which is why ZR-4 exists at all.
Sketch (zone-rules.md ZR-4): for each feature from discover_features(v1_dir)
except an ENUMERATED exception list, assert the file set equals exactly
{__init__.py, controller.py, models.py, validation.py, service.py}.
`health` is the ONE documented exception (2 files: it is a static liveness stub
whose own docstring explains it exists to give api-feature-independence a second
feature so the contract is non-vacuous). Verified across all ten features by
STORY-196: nine conform, health is the single deviation.
Smallest of the four deferred guards.
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (1 point) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
