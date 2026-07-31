---
id: STORY-203
title: Batch the four MINOR ZR-3 duplications — tools/ should import shared literals from backend/src/
type: chore
points: 2
status: draft
filed: 2026-07-31
---

> **DRAFT — needs a refinement pass before it may enter a sprint** (Definition of Ready: approved AC
> + estimate + no open questions). The estimate below is the audit's or the orchestrator's first cut,
> not a refined one.

## Context

Filed during sprint 66, the boundary/code-discipline audit. **Authoritative detail:**
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §6 — four testable AC, one per duplication.

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
Source: audit-api-composition-tools.md section 6, four testable AC.
NONE is a live defect today -- every value currently agrees. Each is a DRIFT
risk the next person touching the backend/src/ side has no way to learn about
from tools/'s own code.
  harness.py:747,750 "uptime-observations"/"uptime-control" vs settings.py:21-22
    -- this is the ZR-3 AC3 REFERENCE CASE the sweep had to prove it could find
  env_matrix.py:39 aws_region default vs settings.py:20
  failure_path_reality_gate.py:149 _REGION vs the same settings.py:20
  store.py:22 VENDOR_HEALTH_WINDOW = timedelta(hours=2) vs vendor_health.py:37
    _HEALTH_CHECK_WINDOW = "2h" -- the CROSS-REPRESENTATION case, which the
    literal-equality sweep STRUCTURALLY CANNOT SEE (found by direct reading).
    That is the standing limit of any value-comparison sweep and is worth
    remembering before trusting an empty ZR-3 result in future.
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (2 points) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
