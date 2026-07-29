---
id: STORY-184
title: Move the demo scenario interval invariant onto SignalScenario itself
type: defect
---

## Context

STORY-176's fix round (sprint 63) answered a quality finding by adding type and sign validation to
`load_scenario_file` (`tools/demo_engine/scenario.py:57-148`): a scenario **file** declaring
`interval_seconds: -30`, `"30"`, `30.5`, `true` or `0` is now rejected with a named
`InvalidScenarioError` naming both the file and the offending signal key. That part is done and
tested.

The invariant did **not** land on the type. Verified by the orchestrator at source, post-fix:

```python
s = SignalScenario(signal_key="x", monitor_id="M", interval_seconds=-30, cycles=[["L1"], ["L1"]])
expand_scenario(s, end_time=datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc))
# -> ['2026-07-30T12:00:30.000000000Z', '2026-07-30T12:00:00.000000000Z']
```

A row **30 seconds after `end_time`** — in the future. Meanwhile `expand_scenario`'s own docstring
(`scenario.py:158-160`) still states, with no precondition:

> the whole ladder sits at or before `end_time`, never after (AC2f: never in the future)

`CLAUDE.md` and `docs/scrum/wiki/demo-engine.md` both gained the precondition during the fix round.
So of the **three** sites making this claim, the round corrected two and left the strongest one — the
function's own contract — unqualified. A docstring that promises an invariant the function does not
enforce is the failure mode sprint 62's STORY-149 was about: article and code agreeing on something
untrue.

**Why this is not an acceptable boundary.** STORY-182's live loop run is next. A scenario player
whose only guard is the file loader will be constructed directly the first time someone scripts a
scenario in code — and the consequence is silent: `ingest_service.py:37` sets
`FUTURE_TOLERANCE = 5min`, `:119-125` quarantines any observation past it into the rejected
repository, and `run.py` passes no `on_cycle`, so the rejected count is **discarded — nothing logs
it.** The player would appear to work and produce no verdicts.

**In-repo precedent for this exact field, twice:** `composition/config.py:34-51`
(`_require_positive_interval`, shared by `MonitorConfig.interval_seconds` and
`SignalConfig.interval_seconds`) and `core/domain/topology.py:50-55`
(`Signal._require_positive_interval_when_set`). Plus the standing checklist item at
`.scrum/checklists/implementer.md:32` — frozen value types enforce their own invariants, with tests
for both the rejected and the valid shape.

## Description

Put the type and sign invariant on `SignalScenario` itself, so **no construction path** can produce
a player that expands into the future. Then `load_scenario_file` catches and re-raises as
`InvalidScenarioError` so its path- and signal-key-prefixed messages survive unchanged — the file
path is information the type cannot have, and the existing loader tests must keep passing.

Either shape is acceptable: a `__post_init__` on the existing frozen dataclass, or converting to the
pydantic `frozen=True` + `model_validator(mode="after")` shape the domain already uses. The pydantic
route matches `topology.py`; the dataclass route keeps `tools/` dependency-light. Implementer's call
— state which and why.

`tools/` only. No file under `backend/src/` changes.

## Acceptance Criteria

- [ ] **AC1 (the type rejects it)** — Constructing `SignalScenario` directly with a non-positive
      `interval_seconds` raises, and a test asserts it for both `-30` and `0`. A test also asserts a
      valid positive value constructs fine (both the rejected and the valid shape, per the checklist
      item).
- [ ] **AC2 (the type rejects wrong types too)** — Direct construction with a non-`int`
      `interval_seconds` raises: `"30"`, `30.5`, and `True` (a `bool` is an `int` subclass and must
      be rejected — this case is currently unpinned by any test even at the loader).
- [ ] **AC3 (the loader's messages are unchanged)** — `load_scenario_file` still raises
      `InvalidScenarioError` naming the file and the signal key for every shape it rejects today.
      The seven existing rejection tests pass **unmodified** — if any needs editing, the story has
      changed the loader's contract and that must be called out, not absorbed.
- [ ] **AC4 (the docstring's claim is now true)** — `expand_scenario`'s "never after `end_time`"
      statement is either left unconditional *because it is now enforced*, or states the one
      remaining caller-side caveat (a caller may still pass a future `end_time`; the guarantee is
      "at or before `end_time`", not "at or before now"). Whichever is chosen, no site claims more
      than the code enforces.
- [ ] **AC5 (the future-row path is pinned, not just described)** — A test proves that the
      previously-reachable future-row outcome is now unreachable: the construction that produced
      `end_time + 30s` rows raises instead. This is the assertion that would have failed before this
      story.
- [ ] **AC6 (production untouched)** — `git diff` touches no file under `backend/src/`.
- [ ] **AC7** — The DoD gate commands the diff can affect exit 0. The test count moves only by the
      tests this story adds.

## Open Questions

None. The dataclass-vs-pydantic choice is deliberately left to the implementer by the Description.

## History

- 2026-07-30: filed from the STORY-176 fix-round quality re-review, which the PO authorised **after**
  accepting sprint 63 ("i accept, and if any reviews are to be done, you can go ahead and do them").
  The re-review returned `FIX_REQUIRED` with this as its single MAJOR; because STORY-176 was already
  accepted, it lands here as a follow-up rather than re-opening a closed story. The orchestrator
  reproduced the defect at source before filing. Estimated 1 point — the change is small, the tests
  are the substance. **Sequencing: land with or before STORY-182** (sprint 64), for the same reason
  as [STORY-183](STORY-183-demo-engine-token-cache-retention.md): the long-running run is when it
  bites.
