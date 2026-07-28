# Sprint 62 Plan — "the fleet exists, and it flows"

- **Sprint goal:** Make a realistic multi-component / multi-signal / multi-location fleet flow
  through the **real** pipeline without Dynatrace, on a config shape that communicates the
  component → monitor → location hierarchy, and close the one anti-flap damping hole that goes
  live the moment a second location exists. **Backend only — no frontend work this sprint.**
- **Mode:** `in-process` (standing directive after the sprint-60 external rejection: "you only
  implement").
- **Size:** 11 pts across 4 stories, deliberately near the ~9 baseline. The PO approved scope
  option (a) but directed *"do it multi sprint, with carefull verification, no need to rush in
  single stretch"* — so option (a)'s ~21 pts are split, with the frontend landing in sprint 63+
  (see `program-roadmap.md`).
- **Stories & order** (dependencies first, then blast radius, then risk, then size):
  1. **STORY-146** (3) — config authoring shape. First: highest blast radius (7 consumers), and
     the demo config in 148 must be authored in the final shape rather than twice.
  2. **STORY-147** (2) — `group` + `description`. Second: same config files as 146, so adjacent
     work avoids rework; also lets 148's demo config carry groups/descriptions immediately.
  3. **STORY-148** (5) — the demo engine. Third: highest risk (new component, vendor wire-shape
     fidelity), and it consumes both config stories.
  4. **STORY-149** (1) — anti-flap `DEGRADED` streak check. Last: fully independent, 4 lines,
     and its scenario-level verification benefits from 148 existing.
- **Plan-verifier: TO BE DISPATCHED** (not skipped). This sprint IS contract-sensitive by the
  skill's own test: STORY-148 must reproduce a **vendor wire contract** exactly, and STORY-146
  changes a shape read by seven consumers. The PO asked for the stories to be written first, so
  `yt-plan-verifier` runs against this plan before the sprint locks.
- **Live-data caveat:** the Dynatrace trial expired 2026-07-28 (memory: `dynatrace-trial-expired`).
  Nothing can be reality-gated against real vendor data. STORY-148 exists to replace that, and
  its own reality gate is therefore a **wire-shape comparison against real captured fixtures**,
  not "the loop didn't crash". STORY-154 (map the real failure codes) stays blocked on renewal.
- **Safety precondition for every demo run:** `decide` publishes recoveries with **no human
  gate** (`core/services/decide.py:122-126`). A demo run wired to the real publisher would post
  fake statuses to the live public Statuspage. STORY-148 AC4 makes the stub a tested guarantee,
  and no demo loop is started before it exists.

---

## STORY-146 — config authoring shape (3 pts)

### Verified contracts / constraints (cited)

- `ComponentConfig` (`backend/src/composition/config.py:57-73`) — `id`, `name`,
  `statuspage_component_id`. `SignalConfig` (`:76-113`) — `signal_key`, `native_id`, `name`,
  `component_id`, `interval_seconds` (+ positive-int validator at `:105`).
- `AppConfig` (`:116-140`) holds flat `components` + `signals`; its `model_validator` enforces
  three invariants, including **referential integrity** `signal.component_id → declared
  component` at `:182-188` — this is the check nesting makes unrepresentable.
- **Seven consumers of `app.signals` that must not move:** `config.py:174`, `:183`, `:236`,
  `:360`; `run.py:136`; `seed_dynamo.py:56`; `vendor_health.py:97`.
- Real location values are opaque vendor entity ids —
  `"dt.entity.synthetic_location": "SYNTHETIC_LOCATION-000000000000005C"`
  (`backend/tests/fixtures/dynatrace/grail_synthetic_events.json:12`, real captured sample).
  The friendly `us-east-1` strings appear only in hand-written fixtures.
- `Config` already exposes `component_for_signal`, `thresholds_for`, `statuspage_mapping()`
  (`config.py:219-298`) — these are the downstream values AC5 pins.
- `config/` sits outside `backend/` on purpose (dossier §4): editing it is a topology change,
  which is why `group`/`monitors` are config-authored rather than enum-coded.

### Steps

- [ ] 1. Failing test: a nested-shape YAML fixture loads, and each monitor's resolved
      `component_id` equals its parent component's id (no `component_id` field authored).
- [ ] 2. Add `MonitorConfig` (nested; `signal_key`/`native_id`/`name`/`interval_seconds`/
      optional `expected_locations`), nest it under `ComponentConfig`, keep the positive-int
      interval validator. Delete the now-unrepresentable referential validator (`:182-188`)
      **and its test**, replacing the test with AC1's structural assertion.
- [ ] 3. Failing test: `locations:` map (alias → `native_id` + `label`); an
      `expected_locations` alias with no declaration raises a **named** error naming the monitor
      and the alias. Then implement.
- [ ] 4. Failing test: `freshness:` block — defaults `stale_after_cycles: 3`,
      `reentry_cycles: 2`; zero/negative rejected. Then implement + expose on `Config`.
- [ ] 5. Add the flattened per-signal accessor (synthesizing `component_id` from the parent).
      Test that it returns the same tuples the old `app.signals` did for an equivalent config.
- [ ] 6. Migrate `config/apps/httpcheck.yaml` to the nested shape. AC5 test: assert
      `signal_key`, `native_id`, `interval_seconds`, `component_for_signal`, `thresholds_for`,
      and `statuspage_mapping()` against **literals captured before the migration** — not
      recomputed from the new file.
- [ ] 7. Verify the seven consumer lines are untouched in the story diff (`git diff` check,
      recorded in the story History).
- [ ] 8. Wiki blast radius: articles whose `code_refs` include `composition/config.py`,
      `seed_dynamo.py`, `run.py` — update or re-verify + bump `verified_sha`.

### Reality gate (146)

Run the real loop against the **existing** single real monitor with the migrated config
(`python -m src.composition.run`, DynamoDB Local) and confirm the topology seed writes the same
`COMPONENT#`/`SIGNAL#` items as before the migration — a byte-level before/after comparison of
the seeded items. This is executable today with no Dynatrace: the seed runs at startup,
independent of whether any observation ever arrives.

---

## STORY-147 — component `group` + `description` (2 pts)

### Verified contracts / constraints (cited)

- The full vertical slice: `ComponentConfig` (`config.py:57`) → `seed_dynamo.py:42-52`
  (`update_item` with `if_not_exists` preserving `status`) → `Component`
  (`core/domain/component.py:22-33`: `id`, `name`, `status`, `app_id`) → Dynamo component
  repository → `ComponentDTO` (`api/v1/components/models.py:12-19`).
- `statuspage_mapping()` (`config.py:292-298`) includes only components declaring a non-None
  `statuspage_component_id` — this is the payload AC4 pins as unchanged.
- Dossier §4 rationale for config-authored (not enum-coded) categories.

### Steps

- [ ] 1. Failing test: `group: Commerce`, `COMMERCE`, `commerce` all load as `commerce`.
      Implement slug normalization at load.
- [ ] 2. Failing test: a non-slug-safe `group` and an 81-char `description` each raise a
      **named** error naming the component and field. Implement (no silent truncation).
- [ ] 3. Failing test: both fields absent → `Component`/`ComponentDTO` carry `None`, and
      `GET /api/v1/components` serializes `null` (asserted on the JSON, not the model).
- [ ] 4. Thread through `seed_dynamo` → domain → repository → DTO; round-trip test against
      DynamoDB Local.
- [ ] 5. AC4 test: Statuspage publish payload + `statuspage_mapping()` byte-identical to before.
- [ ] 6. Confirm every existing components-endpoint test passes untouched (additive optional).
- [ ] 7. Wiki blast radius for `api/v1/components/*`, `core/domain/component.py`.

### Reality gate (147)

Author `group`/`description` on the real `http-check` component, run the boot-time seed against
DynamoDB Local, and read them back over live HTTP from `GET /api/v1/components` — a real
end-to-end read of the new fields through the running API, then confirm the Statuspage mapping
is unchanged. No Dynatrace needed (the seed and the components endpoint are independent of
observations).

---

## STORY-148 — Grail-shaped demo engine (5 pts)

### Verified contracts / constraints (cited)

- **The seam:** `Executor = Callable[[str], list[dict]]` (`adapters/inbound/dynatrace/query.py:32`),
  documented for injected fakes. Real one built by `make_grail_executor(env_url, api_token)`.
- **Query shape to honour** (`query.py:85-100`): exactly
  `dt.synthetic.monitor.id == "<native_id>"` AND `event.type == "http_monitor_execution"`,
  plus `timestamp >= toTimestamp("<iso>")` when a watermark exists; emitted as
  `fetch dt.synthetic.events | filter … | sort timestamp asc`. `toTimestamp()` is load-bearing —
  a bare string literal silently matches nothing (STORY-051, live-confirmed).
- **Required row fields** (subscripted directly, `_assembly.py:24`): `timestamp`, `event.id`,
  `dt.synthetic.monitor.id`, `event.type`, `dt.entity.synthetic_location`. Optional via `.get`:
  `result.statistics.duration` → `latency_ms`; `result.statistics.response_status_code` →
  **a STRING-typed number on the real wire** (`_assembly.py:80-84`).
- **One row = one location execution**; the normalizer never aggregates
  (`http_normalizer.py:4-7`); dispatch registry maps `event.type` → normalizer
  (`dispatch.py:44-46`) and raises `UnsupportedMonitorTypeError` otherwise.
- **Health mapping is deliberately partial:** `map_synthetic_status` maps only `"0"`/`"HEALTHY"`
  → `UP` and **raises** on anything else (`health_mapping.py:65-70`). Failure codes are
  unobserved; anything we emit is an assumption (AC5).
- **Publish danger:** `decide` publishes recoveries ungated (`decide.py:122-126`) via the
  publisher built in `run.py:121-128` from `statuspage_page_id`/`statuspage_api_token`.
- Import-linter contracts cover `src.*`; `tools/` is outside them, so nothing new to declare.

### Steps

- [ ] 1. Failing test first (fidelity before features): a hand-built demo row is compared
      field-by-field against `grail_synthetic_events.json` — same keys, same value **types**,
      including `response_status_code` as a string. Then write the row builder.
- [ ] 2. Failing test: scenario file → per-signal, per-cycle, per-location outcome sequence;
      the player expands it into timestamped rows at the signal's interval. Then implement.
- [ ] 3. Failing test: query parsing honours the monitor-id filter (monitor A's query never
      returns B's rows) and the `toTimestamp` lower bound (older rows excluded); output sorted
      `timestamp asc`. Then implement.
- [ ] 4. Wrap it in an HTTP server answering the same POST `make_grail_executor` issues; test
      through the **real** executor against the local server (this is what option (b) buys over
      a fake callable).
- [ ] 5. **AC4 before any loop run:** demo composition wires a recording/no-op publisher; test
      asserts the demo wiring's publisher is not the real HTTP one. Document the guard in the
      demo README.
- [ ] 6. Author the demo config directory (≥12 components, ≥40 signals, ≥4 locations) in
      STORY-146's nested shape with STORY-147's groups/descriptions. Aliases deliberately not
      AWS region names.
- [ ] 7. Scenario set covering the cases the discussion identified: a clean fleet; a degradation
      crossing the anti-flap ladder to an open proposal; a minority-location failure; a fully
      dark location; two monitors on one component disagreeing (the STORY-151 bug, reproducible
      on demand).
- [ ] 8. AC5: collect every invented vendor code into ONE named constant with the
      unverified-assumption comment; README states plainly what "failure path tested" means.
- [ ] 9. AC6: verify the story diff touches no file under `backend/src/` (mechanical check over
      the commit range, recorded in the story History).
- [ ] 10. Document the demo recipe in `CLAUDE.md` (append-only) — the two env vars and the
      publisher guard.

### Reality gate (148)

Two parts, both executable without Dynatrace:

1. **Wire fidelity** — the AC1 field-by-field comparison against the real captured fixture. This
   is the story's core claim and is proven mechanically, not by inspection.
2. **Real loop, real fleet** — start DynamoDB Local, point `DYNATRACE_ENV_URL` at the demo
   engine and `CONFIG_DIR` at the demo config, run the **unmodified**
   `python -m src.composition.run`, and show: observations landing for ≥12 components / ≥40
   signals / ≥4 locations; `GET /api/v1/components` + `/api/v1/topology` returning that fleet
   over live HTTP; a scripted degradation producing a real open proposal on
   `GET /api/v1/approvals`; and the recording publisher proving no Statuspage call was attempted.

**Honest limit to state in the evidence:** every failure-state row rests on assumed vendor
codes. The pipeline's handling of them is verified; the codes themselves are not.

---

## STORY-149 — anti-flap `DEGRADED` streak check (1 pt)

### Verified contracts / constraints (cited)

- The defect: `pipeline.py:226-227` proposes `degraded` for a `DEGRADED` streak of any length,
  with no threshold comparison — asymmetric with the `DOWN` ladder at `:215-224`, which checks
  `major` → `partial` → `degraded` and returns `_INTERNAL_WARNING` for `length == 1`.
- `_collapse_health` (`:84-97`): `DOWN` only when **every** location is down; **any** mix →
  `DEGRADED`. So the unguarded path is near-dead at 1 location and hot at 3+.
- `thresholds.degraded` already means "consecutive bad cycles before degraded"
  (`AntiFlapThresholds`, `:146-147`) — no new config.
- `AntiFlapOutcome` enforces the status↔warning coherence invariant at construction (`:171+`),
  so the warning outcome cannot be conflated with a proposed status.
- **Out of scope:** Phase 2 (breadth ceiling, D1/D2) — STORY-150.

### Steps

- [ ] 1. Failing test: `DEGRADED` streak of 1 → internal warning (`proposed_status is None`,
      `internal_warning is True`), NOT a `degraded` proposal.
- [ ] 2. Failing test: `DEGRADED` streak above 1 but below `thresholds.degraded` → nothing
      proposed, no warning (use `thresholds.degraded > 2` to make the band reachable).
- [ ] 3. Failing test: `DEGRADED` streak `>= thresholds.degraded` → proposes `degraded`
      (unchanged sustained behaviour).
- [ ] 4. Implement the four-line symmetry in the `DEGRADED` branch.
- [ ] 5. AC5: confirm every existing `DOWN`/`UP` anti-flap assertion passes **untouched** — the
      two ladders byte-identical in the diff, nothing weakened or deleted.
- [ ] 6. Revert-check (AC4): revert the fix, confirm the streak-of-1 test fails, restore.
      Recorded as evidence that the test is load-bearing.

### Reality gate (149)

A demo-engine scenario (from 148) that makes exactly one location of one monitor fail for a
single cycle, run through the real loop: confirm **no proposal appears** on
`GET /api/v1/approvals`, and that extending the same failure past `thresholds.degraded` **does**
open one. This is the defect's real-world shape — a single-location blip — exercised end to end
rather than only at the unit boundary. (Rests on assumed failure codes; stated in the evidence.)

---

## Sprint close

- **Mid-sprint gates:** scoped `yt_gate.py --only` to what each story's diff can affect
  (backend-only sprint → `pytest`, import-linter, `ruff check`, `ruff format --check`;
  `cfn-lint` only if `infra/` is touched, which it should not be).
- **Final gate:** the FULL five-command backend gate on the final HEAD, clean tree — this is the
  evidence of record. No frontend gates apply (no `frontend/` diff this sprint).
- **Wiki compile pass** before review: fold in the config-shape change, the demo engine as a new
  article, and the anti-flap correction; rehabilitate anything the sweep marks stale; lint links.
- **Demo script:** migrated real config seeds identically (146) → new fields live over HTTP
  (147) → demo engine wire-fidelity proof, then the real loop running a 12-component fleet with
  a real open proposal and a silent publisher (148) → single-location blip proposes nothing,
  sustained failure does (149).
- **Not in this sprint, and stated at review so scope is unambiguous:** all frontend work
  (sprint 63+), STORY-150 breadth model, STORY-151 per-component rollup, STORY-152 expected-
  locations completeness, STORY-153 rejection suppression, STORY-154 failure codes (blocked on
  trial renewal), STORY-155 sample_mode removal.
