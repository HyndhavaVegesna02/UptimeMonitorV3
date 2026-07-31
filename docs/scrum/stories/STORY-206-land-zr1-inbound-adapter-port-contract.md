---
id: STORY-206
title: Land ZR-1's guard — an import-linter contract forbidding inbound adapters from importing repository ports
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
`docs/scrum/wiki/zone-rules.md` — `ZR-1`'s Coverage verdict holds the contract VERBATIM; lift it rather than re-deriving it.

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
highest-severity rules WITH live violations; ZR-1 is clean, so it is deferred).
THE CONTRACT IS ALREADY FULLY WRITTEN in docs/scrum/wiki/zone-rules.md ZR-1 --
lift it verbatim. It enumerates the NINE repository/watermark port modules and
deliberately EXCLUDES src.core.ports.signal_ingest, because that is the core's
documented FRONT DOOR (dossier 6/8) that a driving adapter may legitimately
name; a whole-package ban would fail a shape the design documents.
THE TREE IS CLEAN, so C3's shown-RED proof MUST be a mutation: temporarily add
`from src.core.ports.observation_repository import ObservationRepository` to
adapters/inbound/dynatrace/adapter.py -- even as an unused annotation -- confirm
the contract trips, then revert. A guard that has only ever been green is not
accepted (A7/A9), and spec review must return NOT_MET rather than MET-with-a-note.
Lands inside the EXISTING import-boundary DoD command; it does NOT add a ninth
command (C4). It DOES take the contract count from eight to nine, so
CLAUDE.md (twice), .scrum/definition-of-done.md and any wiki article repeating
the figure must be updated in the SAME commit, with grep evidence before/after.
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (2 points) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
