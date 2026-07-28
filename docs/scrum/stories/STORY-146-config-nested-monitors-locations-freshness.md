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

**The mechanism that keeps consumption unchanged (named, because two ACs depend on it):**
`AppConfig.signals` **survives as an `AppConfig` attribute**, synthesized from
`components[].monitors` by a `model_validator(mode="before")` that stamps each monitor's
parent component id onto the derived `SignalConfig`. It is not replaced by a `Config`-level
accessor — every existing consumer reads `app.signals` off an `AppConfig`
(`run.py:136`, `seed_dynamo.py:56`, `composition/vendor_health.py:97`,
`scripts/seed_topology.py:44`), so a `Config` method would not serve them.

Deliberately NOT in scope: a `kind:` field on a monitor. `native_kind` is discovered from the
vendor's `event.type` per row (`dispatch.py:44`); a declared field nothing reads would let
config lie (`kind: clickpath` while `build_dql_query` still fetches
`http_monitor_execution`, `query.py:87`). The nested shape holds the slot for when clickpath
ingest lands.

## Acceptance Criteria

- [ ] **AC1 (nesting)** — `ComponentConfig` accepts a nested `monitors:` list, each entry
      carrying `signal_key`, `native_id`, `name`, `interval_seconds`, and optional
      `expected_locations`. A monitor has **no `component_id` field** — ownership is
      structural. A test asserts a monitor's resolved `component_id` is always its parent's id.
- [ ] **AC2 (the deleted validator loses nothing)** — The referential validator that enforced
      "every `signal.component_id` references a declared component"
      (`backend/src/composition/config.py:182-189`) is deleted, **and a raw top-level
      `signals:` key in a config file is rejected with a named error**. Both halves are
      required: because `AppConfig.signals` remains a settable attribute (see Description),
      deleting the validator without rejecting flat authoring would silently accept a bogus
      `component_id`. A test asserts a file containing `signals:` is rejected, and a second
      asserts the nested path cannot express the state the old validator caught.
      **Two existing tests assert the deleted rule and are removed with it:**
      `backend/tests/test_config.py:112-121` (model level) and `:244-262` (loader level).
- [ ] **AC3 (declared locations)** — A top-level `locations:` mapping keyed by a short alias,
      each value carrying `native_id` (the vendor entity id matched against
      `dt.entity.synthetic_location`) and `label` (operator-facing name). Every
      `expected_locations` entry MUST reference a declared alias.
- [ ] **AC4 (freshness)** — A top-level `freshness:` block with `stale_after_cycles`
      (default 3) and `reentry_cycles` (default 2), both validated as positive ints. **Both are
      cycle COUNTS, not seconds** — each is multiplied by the owning monitor's own
      `interval_seconds` at the point of use. This story performs **no** multiplication and
      stores no derived seconds; it loads, validates, and exposes the counts. (The consumer is
      STORY-151/152.)
- [ ] **AC5 (error classes named, and raised where they survive)** — Add a `ConfigError(ValueError)`
      base with `UndeclaredLocationAliasError`, `FlatSignalsRejectedError`, and
      `InvalidFreshnessError`. Each message names the offending file and the offending
      monitor/alias/field. **These checks run in `load_config` OUTSIDE the
      `try/except (TypeError, ValueError)` at `config.py:343-357`** — verified by probe, a
      `ValueError` subclass raised inside a pydantic `model_validator` is converted to
      `ValidationError` (losing the subclass) and would then be re-raised as a bare
      `ValueError(f"Invalid config in {file}: …")`, so a validator-based implementation cannot
      satisfy this AC. A test asserts `pytest.raises(UndeclaredLocationAliasError)` — the
      specific class, not `ValueError`.
- [ ] **AC6 (scoping is per-app, stated)** — `locations:` and `freshness:` are **per-app**
      (per-file) blocks held on `AppConfig` as `locations: dict[str, LocationConfig]` and
      `freshness: FreshnessConfig`. `Config` exposes `locations_for(app_id)` and
      `freshness_for(app_id)`, matching the existing `thresholds_for` precedent
      (`config.py:242-299`). There is deliberately no global merge, so two app files declaring
      different aliases or freshness values cannot conflict. A test covers two apps with
      different `freshness` values resolving independently.
- [ ] **AC7 (consumers untouched — EIGHT of them)** — All eight existing readers of
      `app.signals` keep working with no edit: `composition/config.py` (×4 — lines 174, 183,
      236, 360), `composition/run.py:136`, `adapters/persistence/…/seed_dynamo.py:56`,
      `composition/vendor_health.py:97`, and `scripts/seed_topology.py:44`. Verified
      mechanically: those eight call-site lines are **untouched in this story's diff**.
- [ ] **AC8 (real config migrated, downstream values identical)** — `config/apps/httpcheck.yaml`
      is migrated to the nested shape, and `load_config` yields **byte-identical downstream
      values**: same `signal_key`, `native_id`, `interval_seconds`, `component_for_signal`
      mapping, `thresholds_for` result, and `statuspage_mapping()`. A test asserts equality
      against pre-migration values captured as **literals**, not recomputed from the new file.
      **The migration changes nesting ONLY** — the real file gains no `locations:` and no
      `expected_locations`, because real Dynatrace location ids and names cannot be verified
      while the trial is expired and inventing them would put fabricated vendor identifiers
      into live config.
- [ ] **AC9** — All five backend DoD gate commands exit 0 (`pytest`, import-linter,
      `ruff check`, `ruff format --check`, `cfn-lint`).

## Open Questions

None.

Alias vocabulary is settled: aliases are **short, non-cloud-provider** strings
(e.g. `loc-a`, `mumbai`, `dublin`) and deliberately NOT AWS region names, so no reader
mistakes a probe location for an AWS deployment region. This supersedes the illustrative
`us-east-1`/`eu-west-1` aliases in `config-shape-proposal.yaml`, which were placeholder text
in a shape sketch, not an approved vocabulary; the proposal file has been amended to match.
Only demo/fixture configs declare locations at all (see AC8).

## History

- 2026-07-28: drafted from the sprint-62 planning discussion. PO approved the shape
  ("this shape looks good"). Decisions recorded in
  `docs/scrum/sprints/2026-07-28-sprint-62/ui-backend-gap-analysis.md` §3a and
  `decisions-and-future-work.md`. `expected_locations` declaration is in scope here;
  *consuming* it in the completeness denominator is a separate future story.
- 2026-07-28: **amended after `yt-plan-verifier` (pre-lock, verdict GAPS).** Six corrections,
  each traced to verified code: (1) the eighth consumer `scripts/seed_topology.py:44` was
  missing from the untouched-lines list; (2) the flattened-accessor mechanism was unnamed and
  AC4-as-written contradicted itself (`Config` accessor vs consumers reading `AppConfig`) —
  now named as a derived `AppConfig.signals`; (3) deleting the referential validator DOES lose
  a real check unless flat `signals:` authoring is rejected, now AC2; (4) the "named error"
  AC was unsatisfiable as specified — probe showed pydantic converts a `ValueError` subclass
  raised in a validator to `ValidationError`, which `config.py:356` then re-raises bare, so
  AC5 now names the classes and pins them outside that try block; (5) `freshness` units
  (cycle counts, not seconds) and per-app-vs-global scoping were undefined, now AC4/AC6;
  (6) the migrated real config is now explicitly forbidden from gaining unverifiable vendor
  location ids, and the alias-vocabulary contradiction against the shape proposal is resolved.
</content>
