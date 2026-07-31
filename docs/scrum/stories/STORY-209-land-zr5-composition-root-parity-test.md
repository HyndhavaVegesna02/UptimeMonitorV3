---
id: STORY-209
title: Land ZR-5's guard — a composition-root parity test for CONFIG_DIR resolution (code-level half only)
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
`docs/scrum/wiki/zone-rules.md` — `ZR-5`'s Coverage verdict, which states the scope limit precisely.

This file exists so the story is visible in `docs/scrum/stories/` alongside every other story —
it was originally landed as a `.scrum/backlog.yaml` entry only, which made it findable at planning
but invisible here.

## The finding, as recorded when it was filed

```
*** READ THE SCOPE LIMIT BEFORE ESTIMATING: this guard CANNOT cover the failure
that actually caused the sprint-64 incident. *** The loop and the API are
separate OS PROCESSES, each reading its own environment, so setting CONFIG_DIR
in one does not propagate to the other. No single-process test sees across a
process boundary. That half is UNGUARDABLE by a unit test and stays runbook
discipline; only tools/demo_loop_gate/harness.py's own env-setting on BOTH child
processes covers it operationally.
WHAT THE GUARD CAN DO (and must not overclaim beyond): patch CONFIG_DIR to an
arbitrary value and assert load_settings().config_dir resolves to it, plus a
source-level assertion that NEITHER composition/run.py::main NOR
composition/app.py::create_app reads os.environ["CONFIG_DIR"] directly -- both
must route through load_settings(). That catches the regression shape "one root
starts reading independently of the other", which is real.
Both roots agree today (verified independently twice, STORY-195 and STORY-196),
so the proof is a mutation.
```

## Acceptance Criteria

- [ ] To be lifted from the source above and approved at refinement. The source already states
      testable AC for this story; refinement's job is to confirm they are still accurate against the
      code, not to invent new ones.

## Open Questions

Refinement must confirm the estimate (2 points) and check
every `file:line` citation still resolves — this sprint repeatedly found citations that had drifted.
