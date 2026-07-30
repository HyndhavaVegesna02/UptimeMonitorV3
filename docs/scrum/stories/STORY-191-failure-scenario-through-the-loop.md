---
id: STORY-191
title: Drive a real DOWN through the loop — failure scenarios end to end on the demo fleet
type: feature
points: 3
status: ready
refined: 2026-07-30
---

## Context

STORY-182 (sprint 64) started the loop for the first time in this repo's history and proved a clean
fleet ingests: 13 components, 41 signals, 4 locations, through the real unmodified
`python -m src.composition.run`. But it could only ever prove the **healthy** half, because the demo
engine emits `UP` and absence only — a consequence of `map_synthetic_status` raising on every
non-`HEALTHY` code.

STORY-190 makes a bad row survivable and STORY-177 lands a provisional failure mapping. Neither is
exercised by a real loop run on its own. **This story is the payoff**: a scripted failure ladder
driven through the same harness, so the repo can finally stop saying "nothing here may be described
as 'the failure path is tested'."

What already exists and is reused, not rebuilt:

- `tools/demo_loop_gate/harness.py::run_positive_side` — drives the real
  `python -m src.composition.run` as an OS subprocess against an embedded demo engine, with
  `CONFIG_DIR=config/demo` on both it and a real `uvicorn` API subprocess, fresh throwaway
  DynamoDB tables (`env_matrix.py::fresh_table_names`), and deliberately fake vendor credentials.
- `tools/demo_loop_gate/guard_reality_gate.py` — verifies the publish guard independently, with no
  network call.
- `tools/demo_engine/rows.py::build_row` already takes `status_code` / `status_message`
  (`:59-60`), so the **row builder needs no change**. Only the scenario vocabulary does.

## ⚠ Safety escalation — read before planning this story

**This is the first story in the project's history in which the publish path can genuinely fire.**

`decide` publishes recoveries with **no human gate** (`core/services/decide.py:122-126` decides,
`:171-172` publishes). Throughout STORY-182 that was inert in practice: an `UP`-and-absence-only
engine can never produce a degradation, so there was never a recovery to publish. This story
introduces `DOWN` → `UP` transitions, which means a real recovery decision and a real publish
attempt inside a demo run.

So the config-only publish guard stops being theoretical and becomes the thing standing between a
demo run and the **live public Statuspage**. The guard is that `config/demo/` declares no
`statuspage_component_id` on any component, so `Config.statuspage_mapping()` is `{}` and
`build_publisher` (`publish_helper.py:211`) falls through to a `LoggingPublisher` **even with real
credentials present** — and the repo-root `.env` does supply real credentials from any launch
directory (`run.py:178`'s `load_dotenv()` walks up from the source file, not CWD).

Both composition roots must point at `config/demo`, or neither does: the loop
(`composition/run.py::main` → `build_live_loop`, reading `settings.config_dir`) **and** the API's
approve trigger (`composition/app.py::create_app`, which does consume Statuspage secrets at
`app.py:169-183`). `config/apps/httpcheck.yaml:8` declares a real component id, so a process that
falls back to the default `config/apps` is genuinely dangerous. Demo component ids are also kept
disjoint from `config/apps`'s, because `StatuspagePublisher` keys on the canonical component id
(`adapters/outbound/statuspage/__init__.py:41-46`).

AC6 below makes proving this a blocking condition of the story, not a precaution.

## Description

Teach the scenario player to express failure outcomes, author failure scenarios, and drive them
through the existing harness to a verified decision — with nothing reaching Statuspage.

### Scenario vocabulary (the only real design work)

`SignalScenario.cycles` is `list[list[str]]` today — each entry is the list of locations reporting
`UP` that cycle, and absence is the only other expressible outcome (`scenario.py` module docstring).
Extend it so a cycle entry may be **either**:

- the current `list[str]` — every named location reports `UP` (**unchanged**, so all five
  checked-in `config/demo/scenarios/*.yaml` and the loader's rejection tests keep working); **or**
- a mapping of location id → outcome, where outcome is one of `up` / `down` / `degraded`.

Backward compatibility is an AC, not a nicety: five scenario files and seven loader rejection tests
depend on the list form.

The `down` / `degraded` outcomes emit rows carrying STORY-177's single provisional constant, imported
from `src.adapters.inbound.dynatrace.health_mapping` — **never a redeclared literal** (STORY-177 AC2
fixes the direction: `tools/` imports `src.*`, never the reverse).

### Scenarios to author in `config/demo/scenarios/`

1. **A failure ladder** — a signal reporting `UP`, then `DOWN` from all locations for enough
   consecutive cycles to cross the anti-flap threshold, then `UP` again (the recovery that makes the
   publish path fire).
2. **A partial/breadth case** — `DOWN` from some locations while others stay `UP` in the same cycle,
   which is the shape STORY-150 and STORY-151 will need and which nothing has ever produced.
3. **A degraded case** — `degraded` outcomes, so `Health.DEGRADED` travels the real path.
4. **A poison-row case** — at least one row carrying a status code that is **still** unmapped after
   STORY-177, to prove STORY-190's quarantine works in a real run and not only in unit tests.

## Acceptance Criteria

- [ ] **AC1** — A scenario cycle can declare per-location `up` / `down` / `degraded`, and
      `expand_scenario` emits rows whose status code/message come from STORY-177's single constant.
      The literal code strings appear nowhere in `tools/`.
- [ ] **AC2** — **Backward compatible**: all five existing `config/demo/scenarios/*.yaml` load and
      expand byte-identically to before, and the seven existing loader rejection tests pass
      unmodified. A malformed outcome (unknown word, wrong type) raises `InvalidScenarioError` naming
      the file, signal key and cycle index, matching the existing convention.
- [ ] **AC3** — A **real loop run** through `harness.py::run_positive_side` ingests the failure
      ladder and reaches a `DOWN` decision: asserted from persisted state (the observations, the
      streak/anti-flap outcome and the resulting decision), not from parsed log text.
- [ ] **AC4** — `Health.DEGRADED` and a partial-breadth cycle both travel the real path and are
      asserted in persisted state.
- [ ] **AC5** — The poison row is **quarantined, not fatal**: the run's other rows ingest, the
      watermark advances past it, and the rejected row is retrievable — STORY-190's fix proven at
      loop scale.
- [ ] **AC6** — **Nothing reached Statuspage, proven not assumed.** `guard_reality_gate.py` is run
      and its **exit code** recorded (working agreement A7: values read from stdout are not
      evidence); the publisher resolved for the run is asserted to be the `LoggingPublisher`
      delegate; and the run is shown to have made **no outbound Statuspage HTTP call**. Because this
      is the first story in which a recovery can actually be decided, AC6 additionally requires
      demonstrating that a recovery **was** decided during the run — otherwise the guard was never
      actually under load and this AC proves nothing.
- [ ] **AC7** — The artifact ends with an explicit verdict and a **non-zero exit on failure**, and is
      **shown failing on deliberately bad input** (working agreement A7). A polling timeout is a
      FAILURE, not partial evidence. The board records the exit code.
- [ ] **AC8** — Zone discipline: all new code stays in `tools/`; nothing under `backend/src/` imports
      `tools/`; the eight `lint-imports` contracts pass unedited.
- [ ] **AC9** — The five backend DoD gate commands exit 0 with pass/skip counts recorded, run with
      `REQUIRE_DYNAMO=1` (working agreement A6). A nonzero skip count is an incomplete gate.
- [ ] **AC10** — `docs/scrum/wiki/demo-engine.md` is updated: the `UP`-and-absence-only Facts are
      rewritten (not merely re-stamped) with their superseded note, and `code_refs` cover every file
      this story touches.

## Dependencies

- **Depends on STORY-190 and STORY-177** — sequenced last of the three. It is the reality gate for
  STORY-177 AC1 at loop scale and for STORY-190 AC1/AC2 in a real run.
- Overlaps STORY-189 (`demo-engine.md` `code_refs` gap). AC10 here and STORY-189 must not conflict —
  whichever lands second reconciles.

## Risk note

Highest-risk story in sprint 65 and deliberately sequenced last: it is the only one that starts real
OS subprocesses, the only one where the publish path can fire, and external mode historically ships
about one MAJOR per 3-point story. A fix round here blocks nothing else.

## History

- 2026-07-30: created at sprint-65 refinement as the payoff story for STORY-177 + STORY-190, per the
  PO's choice to take sprint 65 "all the way through the loop" rather than stopping at the adapter.
  Estimated 3 points on the basis that the harness, the row builder and the guard gate all already
  exist; the new work is scenario vocabulary, four scenario files and the assertions.
