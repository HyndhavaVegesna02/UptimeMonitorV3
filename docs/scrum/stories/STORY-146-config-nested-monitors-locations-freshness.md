---
id: STORY-146
title: Config authoring shape — nested monitors, declared locations, freshness block
type: chore
---

## Context

`config/apps/httpcheck.yaml` declares `components:` and `signals:` as flat sibling lists
joined by a `component_id` foreign key, so the component → monitor hierarchy only exists if
a reader traces ids by eye. The PO confirmed (2026-07-28) the single `http-check` component
is temporary and "many more components will come along sooner", each potentially with
several monitors of different kinds — so the authoring shape has to communicate that
hierarchy before the fleet is authored, not after.

Two further gaps the same edit closes:

1. **Probe locations have no declared identity.** The real wire value in
   `dt.entity.synthetic_location` is an opaque vendor entity id —
   `SYNTHETIC_LOCATION-000000000000005C` (`backend/tests/fixtures/dynatrace/grail_synthetic_events.json:12`,
   a real captured sample). There is nowhere for an operator-facing name to come from, so the
   cockpit would show operators the raw entity id.
2. **`completeness_pct` uses *observed* locations, not expected ones.**
   `distinct_locations` is `COUNT(DISTINCT location)` over what arrived
   (`backend/src/core/queries/availability.py:74`), so a location that goes fully dark leaves
   its own denominator and completeness reads ~100%. Declaring expected locations is the only
   way config can know a location was missing. (Consuming them in the calculator is a
   SEPARATE story — this one only establishes the declaration.)

The freshness numbers agreed for the per-component rollup (`stale_after_cycles`,
`reentry_cycles`) also need a home, and belong with topology rather than in code.

Full analysis: `docs/scrum/sprints/2026-07-28-sprint-62/config-shape-proposal.yaml` and
`calculations-under-new-config.md`.

## Description

Change the **authoring** shape of `config/apps/*.yaml` — nest monitors under their component,
declare locations once per app, add a freshness block — while keeping the **consumption**
shape unchanged so no existing consumer has to move.

The word `monitors:` is deliberate: what an operator configures is a monitor; what it produces
is a signal. `monitors: [ { signal_key: … } ]` reads as "this monitor produces this signal",
which is the actual model (one `native_id` = one vendor monitor, fanning out across
locations — `adapters/inbound/dynatrace/query.py:86`, `http_normalizer.py:4`).

Deliberately NOT in scope: a `kind:` field on a monitor. `native_kind` is discovered from the
vendor's `event.type` per row (`dispatch.py:44`); a declared field nothing reads would let
config lie (`kind: clickpath` while `build_dql_query` still fetches
`http_monitor_execution`, `query.py:87`). The nested shape holds the slot for when clickpath
ingest lands.

## Acceptance Criteria

- [ ] **AC1** — `ComponentConfig` accepts a nested `monitors:` list, each entry carrying
      `signal_key`, `native_id`, `name`, `interval_seconds`, and optional
      `expected_locations`. A monitor has **no `component_id` field** — ownership is
      structural. The referential validator that enforced
      "every `signal.component_id` references a declared component"
      (`backend/src/composition/config.py:182-188`) is **deleted**, because the state it
      guarded is now unrepresentable. A test asserts a monitor's resolved `component_id` is
      always its parent's id.
- [ ] **AC2** — A top-level `locations:` mapping keyed by a short alias, each value carrying
      `native_id` (the vendor entity id matched against `dt.entity.synthetic_location`) and
      `label` (operator-facing name). Every `expected_locations` entry MUST reference a
      declared alias; an undeclared alias raises a **named** error that identifies the
      offending monitor and alias (not a bare `KeyError`/`ValueError`).
- [ ] **AC3** — A top-level `freshness:` block with `stale_after_cycles` (default 3) and
      `reentry_cycles` (default 2), both validated as positive ints, expressed in multiples of
      each monitor's own interval. Values are exposed on `Config` for a later consumer; this
      story only loads and validates them.
- [ ] **AC4** — `Config` exposes a flattened per-signal accessor equivalent to today's
      `app.signals`, synthesizing `component_id` from the parent, so **all seven existing
      consumers keep working unchanged**: `config.py` (×4 — lines 174, 183, 236, 360),
      `run.py:136`, `seed_dynamo.py:56`, `vendor_health.py:97`. Verified mechanically: those
      seven call-site lines are **untouched in this story's diff**.
- [ ] **AC5** — The real `config/apps/httpcheck.yaml` is migrated to the new shape, and
      `load_config` yields **byte-identical downstream values**: same `signal_key`,
      `native_id`, `interval_seconds`, `component_for_signal` mapping, `thresholds_for`
      result, and `statuspage_mapping()`. A test asserts equality against the pre-migration
      expected values captured as literals (not recomputed from the new config).
- [ ] **AC6** — All five backend DoD gate commands exit 0 (`pytest`, import-linter,
      `ruff check`, `ruff format --check`, `cfn-lint`).

## Open Questions

None. (Alias vocabulary is provisional: real Dynatrace location ids/names cannot be obtained
while the trial is expired — see `decisions-and-future-work.md` D4 constraint 2. Aliases are
deliberately NOT borrowed AWS region names.)

## History

- 2026-07-28: drafted from the sprint-62 planning discussion. PO approved the shape
  ("this shape looks good"). Decisions recorded in
  `docs/scrum/sprints/2026-07-28-sprint-62/ui-backend-gap-analysis.md` §3a and
  `decisions-and-future-work.md`. `expected_locations` declaration is in scope here;
  *consuming* it in the completeness denominator is a separate future story.
