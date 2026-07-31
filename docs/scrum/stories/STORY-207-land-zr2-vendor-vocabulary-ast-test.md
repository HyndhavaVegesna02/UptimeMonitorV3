---
id: STORY-207
title: Land ZR-2's guard — an AST test that vendor vocabulary never becomes an identifier inside core/
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
`docs/scrum/wiki/zone-rules.md` — `ZR-2`'s Coverage verdict names the exact AST node types and the residue.

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
Sketch is written in zone-rules.md ZR-2's coverage verdict, including the node
types it must walk (FunctionDef/ClassDef names, arg, Name, Attribute.attr,
keyword.arg, and Constant values that are NOT the sole value of an Expr
statement -- the last exclusion is what keeps the two PROSE forms compliant).
THE RESIDUE IS ALREADY STATED and must be carried into the test's docstring
rather than quietly dropped: a vendor word in a STRING annotation and a
DYNAMICALLY CONSTRUCTED identifier are invisible to a static AST walk. The
guard may not be described as fully enforcing ZR-2.
The detection word list is a RECALL AID, explicitly non-exhaustive -- the RULE
is the FORM distinction, which is closed and decidable without any word list.
Mutation proof: add e.g. `dynatrace_code: str` to a core/ domain model, confirm
RED, revert.
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (2 points) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
