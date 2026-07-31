---
id: STORY-205
title: composition/seed_dynamo.py must call the persistence adapters' key schema, not re-implement it
type: defect
points: 3
status: draft
filed: 2026-07-31
---

> **DRAFT — needs a refinement pass before it may enter a sprint** (Definition of Ready: approved AC
> + estimate + no open questions). The estimate below is the audit's or the orchestrator's first cut,
> not a refined one.

## Context

Filed during sprint 66, the boundary/code-discipline audit. **Authoritative detail:**
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §6, filed from the STORY-196 quality review — four testable AC.

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
Source: audit-api-composition-tools.md section 6, four testable AC.
*** ARGUABLY THE BEST BOUNDARY FINDING OF THE AUDIT SPRINT. *** It fell through
the crack BETWEEN the two audit passes -- STORY-195 covered adapters/,
STORY-196 covered composition/, and this is composition/ DOING adapters/'s job,
so each pass could reasonably think the other owned it. That is the exact
failure mode a two-pass audit is supposed to prevent, and it took an
independent reviewer pass to catch.
THE DEFECT: seed_dynamo.py:29-30/:43/:58-59 hand-build the DynamoDB key schema
(pk=TOPOLOGY, sk=COMPONENT#<id> / SIGNAL#<key>) with raw table.put_item /
table.update_item and a hand-written UpdateExpression, from the COMPOSITION
zone. That schema is OWNED by dynamo_component_repository.py:39-40,53-54 and
dynamo_signal_repository.py:41-42, so it is now declared in THREE places, on
the boot path of BOTH composition roots.
THE DRIFT HAS ALREADY BITTEN ONCE, and the scar is in the tree:
tools/demo_loop_gate/failure_path_reality_gate.py:163-172's docstring records a
first version using pk=COMPONENT#<id>, sk=META while the repository actually
uses pk=TOPOLOGY, sk=COMPONENT#<id>.
CORROBORATION: docs/scrum/wiki/persistence-adapters.md already lists
seed_dynamo.py in its code_refs and describes seed_topology_dynamo alongside
the repositories (:36) -- the wiki had effectively filed it with the adapters
long before the audit looked.
AC2 IS THE GOOD ONE and must survive refinement: change the key schema INSIDE
a repository and assert seed_topology_dynamo follows AUTOMATICALLY, without
seed_dynamo.py changing -- a behavioural drift test, not a source assertion.
REFINEMENT MUST SIZE THIS BEFORE COMMITTING: the repositories expose no
seed-shaped bulk upsert today (set_status/get are single-item, request-scoped),
and NO repository owns AppConfig-shaped writes (pk=TOPOLOGY, sk=APP#<id>) at
all -- that may need a third method or a small new TopologyRepository port.
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (3 points) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
