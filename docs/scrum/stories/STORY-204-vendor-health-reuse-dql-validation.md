---
id: STORY-204
title: Reuse the adapter's DQL builder validation inside composition/vendor_health.py (GAP-2)
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
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §4 (`GAP-2`) and §6 — three testable AC.

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
deliberately NOT landed in zone-rules.md by the audit -- mirroring GAP-1's
precedent, where promotion happened in a later fix round).
composition/vendor_health.py:40-53 build_vendor_health_query duplicates the
DQL-building of adapters/inbound/dynatrace/query.py:41-49,79-82 WITHOUT reusing
its InvalidNativeIdError validation, so a native_id containing a DQL-breaking
character (" \ newline CR) silently builds a malformed query on one path and
raises a named error on the other.
No live-observed vendor error has ever exercised this path (CLAUDE.md's "two
things to know"), which is why it is a chore rather than a defect.
REFINEMENT DECIDES THE SHAPE (a shared validator both builders call, vs
vendor_health composing around a quote-and-validate helper query.py exports) --
the audit deliberately did not prescribe the fix.
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (2 points) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
