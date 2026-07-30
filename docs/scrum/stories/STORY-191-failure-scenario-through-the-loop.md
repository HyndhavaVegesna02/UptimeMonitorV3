---
id: STORY-191
title: Drive a real DOWN through the loop — failure scenarios end to end on the demo fleet
type: feature
points: 5
status: ready
refined: 2026-07-30
repointed: 2026-07-30   # 3 -> 5 on the plan-verifier's independent judgement, PO-approved
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

**This story deliberately makes the publish path fire for the first time in the project's history.**

`decide` publishes recoveries with **no human gate** (`core/services/decide.py:115-126` sets
`publish_change` and returns `PUBLISHED_RECOVERY`; `:171-172` calls `publish()`).

**Corrected mechanism (this story's first draft had it wrong; verified against code by
`yt-plan-verifier` 2026-07-30).** A `DOWN`-then-`UP` observation ladder **cannot publish anything**:

- a **degradation never publishes** — `decide` opens a proposal and publishes nothing
  (`decide.py:128-136`);
- a **recovery publishes** only when `severity_rank(proposed) < severity_rank(current)`
  (`decide.py:115-117`), and `STATUS_SEVERITY` is `OPERATIONAL 0, DEGRADED 1, PARTIAL_OUTAGE 2,
  MAJOR_OUTAGE 3` (`core/domain/status.py:63-68`);
- every component seeds **`OPERATIONAL`** (`composition/seed_dynamo.py:49`), and the only writer of
  component status is `StatusWritebackPublisher.publish` (`publish_helper.py:179`).

So from a seeded baseline the ladder yields `PROPOSED` then at most `OBSOLETED`
(`decide.py:157-169`) — nothing published. **This story reaches the publish path by pre-setting one
demo component's stored status to `MAJOR_OUTAGE`** (a real, reachable state: a previously-approved
degradation) and then running an all-`UP` ladder, so `anti_flap` proposes `OPERATIONAL` and trips the
recovery branch. A useful consequence: this works with the **static, past-anchored store and one
cycle per signal** the harness already builds — no live row injection is required.

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

Backward compatibility is an AC, not a nicety: five scenario files and **9 rejection-test functions /
11 collected cases** depend on the list form (`backend/tests/demo_engine/test_scenario.py:334, 351,
374, 388, 403, 417, 438, 453, 467` — `test_load_scenario_file_missing_required_field_raises` is
parametrized ×3). Earlier drafts said "seven"; that number was never counted and is wrong.

The `down` / `degraded` outcomes emit rows carrying STORY-177's single provisional constant, imported
from `src.adapters.inbound.dynatrace.health_mapping` — **never a redeclared literal** (STORY-177 AC2
fixes the direction: `tools/` imports `src.*`, never the reverse).

### Scenarios to author in `config/demo/scenarios/`

1. **A `DOWN` ladder** — enough consecutive `down` cycles to cross a **named** threshold. The demo
   fleets declare `thresholds: {major: 5, partial: 3, degraded: 2, recovery: 2}`
   (`config/demo/fleet-core.yaml:38`, `fleet-edge.yaml:39`, `fleet-platform.yaml:39`) and these are
   **consecutive-CYCLE counts**, not seconds or percentages — `anti_flap` compares them to
   `streak_.length` (`core/services/pipeline.py:219-239`). So say which: `MAJOR_OUTAGE` needs 5,
   while `degraded: 2` also "crosses a threshold". Keep the ladder **≤ 7 cycles**, because
   `orchestrate.py:98` computes `since = until − (max_threshold + 2) × interval` — a 7-cycle window
   for these fleets — so a longer ladder loses its head.
2. **A partial/breadth case** — `down` at some locations while others stay `up` in the same cycle, the
   shape STORY-150 and STORY-151 will need. **Note:** `_collapse_health` (`pipeline.py:85-98`) maps
   both this and the all-`degraded` case to `Health.DEGRADED`, so their `Verdict`s are **identical**.
   The distinguishing evidence is per-location `SignalObservation.health` — assert on that.
3. **A degraded case** — `degraded` outcomes, so `Health.DEGRADED` travels the real path.
4. **A poison-row case** — a status code **still** unmapped after STORY-177, proving STORY-190's
   quarantine in a real run. **The poison row must be an EXTRA row alongside four good locations**,
   never a location's only row: a quarantined row is never persisted, so otherwise that signal shows
   3 of 4 locations, `_assert_ac3_ingest`'s `signals_with_under_4_locations` (`harness.py:287-290`)
   fails and `_wait_for_last_signal`'s `>= 4` poll (`:187`) times out — which working agreement A7
   calls a FAILURE, not partial evidence.
5. **A recovery case** — the pre-set-`MAJOR_OUTAGE` component with an all-`UP` ladder (see the safety
   section), which is what actually fires the publish path.

**Two harness constraints that are not optional.** `run_positive_side`
(`tools/demo_loop_gate/harness.py:335-339`) takes **no** store or scenario parameter and `:419`
hardcodes `build_fleet_row_store(cfg, end_time=run_start)`. Add a keyword-only seam, and **MERGE** the
new rows into that fleet store — **never substitute it**, because `_assert_ac3_ingest` (`:279-295`)
requires all 41 signals × 4 locations and `_assert_ac4_vendor_health` (`:298-310`) requires zero
drift. And use a **distinct event-id namespace** (e.g. a `fail-` prefix): `expand_scenario` emits
`f"{signal_key}-{seq}"`, so overlapping the fleet store yields identical ids and `save_new`'s `EVT#`
dedupe marker (`backend/src/adapters/persistence/dynamo_observation_repository.py:57-61`) **silently
drops the second set with no error.**

## Acceptance Criteria

- [ ] **AC1** — A scenario cycle can declare per-location `up` / `down` / `degraded`, and
      `expand_scenario` emits rows whose status code/message come from STORY-177's single constant.
      The literal code strings appear nowhere in `tools/`.
- [ ] **AC2** — **Backward compatible**: all five existing `config/demo/scenarios/*.yaml` load and
      expand byte-identically to before, and **all 11 collected rejection cases across the 9
      functions** listed above pass **unmodified**. A malformed outcome (unknown word, wrong type)
      raises `InvalidScenarioError` naming the file, signal key and cycle index, matching the
      existing convention.
- [ ] **AC3** — A **real loop run** through `harness.py::run_positive_side` ingests the failure
      ladder and reaches a `DOWN` decision: asserted from persisted state (the observations, the
      streak/anti-flap outcome and the resulting decision), not from parsed log text.
- [ ] **AC4** — `Health.DEGRADED` and a partial-breadth cycle both travel the real path and are
      asserted in persisted state.
- [ ] **AC5** — The poison row is **quarantined, not fatal**: the run's other rows ingest, the
      watermark advances past it, and the rejected row is retrievable — STORY-190's fix proven at
      loop scale.
- [ ] **AC6** — **The publish path fired AND nothing reached Statuspage — both proven from persisted
      state, neither from logs or stdout.** The guard must be under genuine load, or this AC proves
      nothing, so both sides are required:
      - **It fired:** the pre-set component's status in the control table changed `MAJOR_OUTAGE` →
        `OPERATIONAL`. `StatusWritebackPublisher.publish` (`publish_helper.py:179`) is the **only**
        component-status writer and **is** in the safe chain (`:230-231`), so that change is proof the
        recovery publish executed.
      - **Nothing left the process:** the **publications table is empty**. `RecordingPublisher`
        (`publish_helper.py:212-227`) writes a `publications` row on **every** attempt (STORY-072) and
        exists **only** in the credentialed+mapping chain — it is absent from the `LoggingPublisher`
        fallback. An empty publications table *with* a recovery publish having occurred is the
        discriminator.
      - Additionally, `guard_reality_gate.py` is run and its **exit code** recorded (A7: values read
        from stdout are not evidence). Note it reconstructs the chain **in-process** (`:83-128`) and
        never observes the subprocess — it corroborates the two persisted checks, it does not replace
        them.
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
