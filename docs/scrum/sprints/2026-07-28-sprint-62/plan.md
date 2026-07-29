# Sprint 62 Plan — "the shape and the wire are right"

- **Sprint goal:** Land the config authoring shape that communicates the component → monitor →
  location hierarchy, build a Grail-faithful demo engine wire contract proven against a real
  captured sample, and close the one anti-flap damping hole that goes live the moment a second
  location exists. **Backend only — no frontend work this sprint.** The 12-component fleet run
  itself is STORY-176, opening sprint 63.
- **Mode:** `in-process` (standing directive after the sprint-60 external rejection: "you only
  implement").
- **Size:** 9 pts across 3 stories. The PO approved scope option (a) but directed *"do it multi
  sprint, with carefull verification, no need to rush in single stretch"* — so option (a)'s
  ~21 pts are split across sprints, with the frontend landing in 63+ (see `program-roadmap.md`).
  The goal was restated from "the fleet exists, and it flows" when STORY-176 moved to 63 (D-B).
- **Preconditions (verified, not assumed):** working tree clean apart from two unrelated
  untracked files (`package.json`, `package-lock.json` — a stray `framer-motion` scratch, left
  in place deliberately and not part of this sprint); branch `sprint-62` cut from `main` at
  `517fc38` with `main` untouched; **green baseline at `282be8d`** — all 8 DoD commands exit 0,
  evidence recorded verbatim from `yt_gate.py` in `sprint-current.yaml`. Code baseline holds at
  HEAD (`git diff --name-only 282be8d..HEAD -- backend/ frontend/ config/ infra/` is empty).
- **Stories & order** (dependencies first, then blast radius, then risk, then size):
  1. **STORY-146** (5) — config authoring shape. First: highest blast radius (seven surviving
     consumers of `app.signals`, plus a 13-file test migration), and STORY-176's demo config must
     be authored in the final shape, not twice.
  2. **STORY-148** (3) — the demo engine wire contract. Second: highest risk, and independent of
     the config work, so it verifies on its own terms.
  3. **STORY-149** (1) — anti-flap `DEGRADED` streak check. Last: fully independent, four lines.
- **Two verifier passes run, both GAPS, all gaps closed.** See "Verifier pass" and "Second
  verifier pass" below. This sprint is contract-sensitive by the skill's own test: STORY-148 must
  reproduce a **vendor wire contract** exactly, and STORY-146 changes a shape seven consumers read.
- **Live-data caveat:** the Dynatrace trial expired 2026-07-28 (memory: `dynatrace-trial-expired`).
  Nothing can be reality-gated against real vendor data. STORY-148 exists to replace that, and its
  reality gate is a **field-and-scale comparison against a real captured fixture** plus a round
  trip through the real executor — not "the loop didn't crash". STORY-154 (map the real failure
  codes) stays blocked on renewal, and STORY-177 (a provisional mapping) is the unblocking story
  for failure-path demos.
- **No demo loop runs this sprint**, so the publish-safety precondition does not arise here — it
  moves with STORY-176 (AC3: config-only guard + `CONFIG_DIR` on both processes). The one loop run
  that *does* happen, STORY-146's reality gate, uses the **real** `config/apps` and therefore runs
  with `STATUSPAGE_API_KEY` unset; see that gate.

---

## Verifier pass (`yt-plan-verifier`, pre-lock, 2026-07-28)

Verdict **GAPS** — 13 gaps, 4 risks. Every gap is closed in this revision; I independently
re-verified the eight load-bearing findings against the producing code before acting on them,
and all eight held. What materially changed:

| # | Finding | Fix |
|---|---------|-----|
| G1 | The demo row's required-field set was **5, not 7** — `result.status.code` and `result.status.message` are `require_field` in the *normalizer* (`http_normalizer.py:22-23`). The original list came from `_assembly`'s docstring, which documents only `_assembly`'s needs. A row built to it passes a fidelity test, then raises `MalformedDqlRowError` on the first real row. | STORY-148 AC1 asserts all seven |
| G2 | **Units/scale:** `result.statistics.duration` is a **nanosecond** count carried as a **string** (`"755000000"`, fixture:15 → `//1_000_000`, `_assembly.py:92`). Emitting `"755"` is the same *type* and silently yields `latency_ms == 0` fleet-wide. | STORY-148 AC2 asserts a scale-sane round trip, not just type |
| G3 | The publish guard was **unsatisfiable**: `run.py:121-128` builds the publisher inside `build_live_loop` with no injection point, while AC3 demanded an unmodified `run.py` and AC6 forbade touching `backend/src/`. The real exposure is also larger — `run.py:178 load_dotenv()` walks up from the source file, so the existing repo-root `.env` supplies Statuspage creds from any CWD, and a **second** route exists via the API approve trigger (`app.py:160-182`). | STORY-176 AC3: config-only guard — no `statuspage_component_id` ⇒ `statuspage_mapping() == {}` ⇒ `LoggingPublisher` on both roots (`publish_helper.py:211`), even with real creds |
| G4 | The "named error" ACs were unsatisfiable where the plan put them. **Probed:** a `ValueError` subclass raised in a pydantic `model_validator` becomes `ValidationError`, which `config.py:356` re-raises as a bare `ValueError`. | STORY-146 AC5 / STORY-147 AC1 name the classes and pin them **outside** that try block |
| G5 | "Seven consumers" is **eight** — `scripts/seed_topology.py:44` was missing. And AC4 self-contradicted: a `Config`-level accessor cannot serve consumers reading `AppConfig.signals`. | STORY-146 AC7 lists eight; the mechanism is now named — `AppConfig.signals` survives, synthesized from `components[].monitors` |
| G6 | Deleting the referential validator **does** lose a real check, because `AppConfig.signals` stays settable. Also it has **two** tests, not one. | STORY-146 AC2 rejects flat `signals:` authoring and names both tests |
| G7 | A **second query grammar** exists and was entirely unaccounted for: `composition/vendor_health.py:40-53` (`summarize count()`, `from:now()-2h`, response keyed `"count()"`), run at every startup for every signal (`run.py:192-196`). An ingest-only engine makes startup warn that all 40 monitor ids are dead — polluting the exact evidence the gate collects. | STORY-148 AC5 |
| G8 | The Grail HTTP envelope, endpoints, auth and **async** protocol were never specified; `grail_executor.py:97` returns `[]` **silently** when they are wrong, and a sync-only server exercises only the fallback branch — undercutting D4's stated rationale. | STORY-148 AC6 pins them literally, async mode |
| G9 | The scenario time base was unspecified. Four separate constraints each cause **silent** no-data: the rolling 7-cycle window (`orchestrate.py:94-98`), timestamp format (`signal.py:81-91` rejects naive/non-UTC), monotonicity across queries, and interval length. | STORY-176 AC2 (a)–(d) |
| G10 | The watermark bound **cannot be string-compared**: `query.py:96` emits a 6-digit fraction, rows carry 9, and `'0' < 'Z'` excludes an equal instant — reproducing the STORY-051 stall inside the demo engine. A naive old-vs-new test passes anyway. | STORY-148 AC4, with a precision-boundary case |
| G11 | STORY-149 was **not** self-contained: two existing tests assert the current behaviour (`test_anti_flap.py:185-190`, `:240-248`), the length-0 case was unspecified, and `pipeline.py:210-211` documents the defect verbatim. | STORY-149 AC5/AC6/AC7 |
| G12 | `tools/demo-engine/` is not an importable package name, and `pyproject.toml:29` sets `testpaths = ["backend/tests"]` — tests under `tools/` would **never run** while the gate stayed green. `tools/` is also *not* in ruff's excludes. | STORY-148 AC9: `tools/demo_engine/`, tests under `backend/tests/` |
| G13 | Both demo reality gates were confounded by the known STORY-151 sibling-OBSOLETE path (`decide.py:157-169`) — at ~3 monitors/component a healthy sibling can spoof the proposal evidence in either direction. | STORY-176 AC7 and STORY-149's gate pinned to single-monitor components |

**Risks accepted or actioned:** R1 (STORY-148 under-estimated at 5, real work 7–8) → **split**
into STORY-148 (3, wire contract) + STORY-176 (3, fleet + run), and **STORY-147 deferred to
sprint 63** where its consumer lands, keeping the sprint at 10 pts with verification headroom.
R2 (fabricated vendor location ids reaching live config) → STORY-146 AC8 forbids `locations:`
in the migrated real file; demo-only per STORY-176 AC4. R3 (alias vocabulary contradiction —
the stories forbade AWS region names the PO-approved sketch used) → resolved to short
non-cloud-provider aliases, and `config-shape-proposal.yaml` amended to match. R4 (`freshness:`
had no provenance, units or resolution rule) → STORY-146 AC4/AC6 fix units (cycle counts) and
scoping (per-app, no global merge), and the block is added to the shape proposal.

**Judgement call flagged for the PO:** deferring STORY-147 and splitting STORY-148 are both
mine, not the verifier's decision to make. Neither changes total scope — 147 moves to the sprint
where it is consumed, and the split is the same work in two verifiable halves. Say the word and
either goes back.

---

## Second verifier pass (independent, fresh context, 2026-07-28)

A second `yt-plan-verifier` was dispatched over the revision — fresh rather than a continuation,
so it would not grade fixes written in its own vocabulary, and briefed to attack the **new**
claims the fixes introduced rather than confirm the old ones were addressed.

Verdict **GAPS**. It confirmed the mechanism at the heart of STORY-146 (the `mode="before"`
derive on a `frozen=True` model) actually works — including for the pre-built `ComponentConfig`
instances `load_config:348-351` passes, a case the plan never mentioned — and confirmed the
seven-field set, the units, the async protocol, the split boundary, and board/backlog/plan
agreement. It also found **three fix-introduced errors and one blocker both earlier passes
missed.**

### Closed in this revision

| # | Finding | Fix |
|---|---------|-----|
| **G2** | **Fix-introduced.** AC7 listed `config.py:183` as an untouched reader, but `:183` is `for sig in self.signals:` *inside* the `:182-189` block AC2 deletes. Merging "eight consumers" with "delete the validator" created a self-contradiction. A line-number check was unusable anyway — this story's own additions shift `:236` and `:360`. | STORY-146 AC7: **seven** surviving readers, checked semantically by grep, not line numbers |
| **G3** | **Fix-introduced.** The config-only publish guard covered the *loop's* config but not the *API's*. The API is a separate process reading its own `CONFIG_DIR`, which `settings.py:32` defaults to `config/apps` — whose `httpcheck.yaml:6` declares a real `statuspage_component_id`. With `asgi.py:36` loading the real `.env`, an API started per the documented recipe wires a **real `StatuspagePublisher`** on the approve trigger, and lifespan-seeds the real component into the demo table. | STORY-176 AC3 now requires `CONFIG_DIR` on **both** processes and asserts the API's *runtime* mapping is `{}` |
| **G5** | **Fix-introduced.** AC4's "6-digit fraction" is categorically wrong: `datetime.isoformat()` omits the fraction entirely when `microsecond == 0`, so the bound is **0- or 6-digit**. An implementer slicing six digits per the AC gets the STORY-051 stall the AC exists to prevent — and whole-second timestamps are the *likeliest* demo shape. | STORY-148 AC4: parse both sides, pin **three** precisions (0/6/9) |
| **G4** | `check_vendor_id_health` queries `from:now()-2h` at `run.py:196` before any loop exists. A player emitting from engine-start forward returns 0 for all ≥40 signals, failing AC6's "no dead monitor ids". | STORY-176 AC2(e): ≥2 h backfill relative to the request instant; cross-referenced in STORY-148 AC5 |
| **G6** | AC4 said freshness values are "validated as positive ints" while plan step 2 told the implementer to follow the `config.py:105-113` validator precedent — which makes AC5's named error unreachable (probed: conversion happens in **both** validator modes). | STORY-146 AC4: `FreshnessConfig` carries plain ints with **no** validator, stated as a constraint because copying the precedent is the natural instinct |
| **R1** | An unconditional `mode="before"` derive **silently discards** an explicit `signals=[…]` — worse than the invariant it replaced, and the ~9 `AppConfig(signals=…)` migrations would pass silently instead of failing loudly. | STORY-146 AC2: the derive validator **raises** `FlatSignalsRejectedError` on explicit non-empty `signals` |
| nits | Labels were still AWS region names after the aliases were renamed (defeating the point); roadmap still promised a stubbed publisher; board still said "7 consumers"; STORY-147's citation fix overran a 16-line file by one; "silent no-data" was wrong in three places (`pull_loop.py:200-207` logs at ERROR with a traceback — genuinely silent are only `grail_executor.py:97`, `_extract_count` → 0, and a window miss); `config-shape-proposal.yaml` still showed `group`/`description` with no sprint-63 marker. | all fixed |

### OPEN — needs a PO decision before lock

**BLOCKER: no demo scenario can produce a `DOWN` or `DEGRADED` observation.** Both earlier
passes and I reasoned past this. `map_synthetic_status` **raises** `UnknownVendorStatusError` on
any non-healthy code (`health_mapping.py:65-70`) — its own docstring states that inventing
failure codes is *"deliberately NOT done"*. `dispatch.py:80` is a bare list comprehension, so one
failure row destroys the whole batch including healthy rows. And the codebase's own test proves
monkeypatching is the only route (`test_pull_loop.py:139-145`: *"Production map_synthetic_status
is fail-loud on any non-healthy code … Mock the vendor-mapping edge so this wiring test can drive
a DOWN through run_cycle"*). A demo engine speaking HTTP over the wire cannot monkeypatch.

My STORY-148 AC8 framed emitted failure codes as *"assumptions"* — mapped but unverified. They
are not mapped at all. An assumed code does not make a row unverified; it makes the row
**unusable**.

What this costs, under the current no-`backend/src/`-changes rule:

- STORY-176 AC5 — 3 of 5 scenarios die (ladder-crossing degradation, minority-location failure,
  two-monitors-disagreeing). "Clean fleet" and "fully dark location" survive.
- STORY-176 AC7 and reality-gate item 4 — no proposal can open by any route.
- **STORY-149's reality gate is worse than unobtainable — it is a false pass.** Step 1 ("one
  location fails for one cycle → confirm no proposal appears") would PASS because nothing was
  ingested, not because anti-flap damped it. Step 2 would then fail, on the last story, after
  9 points are spent. This is exactly the tests-that-lie category the quality checklist exists
  for.

Options are recorded in "Open decisions" below. This is a PO call, not a wording fix.

**Sizing.** Independent re-estimate: STORY-146 is 3–5 (nine ACs, four models, three error
classes, two accessors, and a migration surface of **13 test files** — the plan named only
`test_config.py`, while `test_seed.py`, `test_topology_endpoint.py`, `test_dynamo_adapters.py`,
`test_availability_endpoint.py`, `fakes.py` and six more carry flat `signals:` or
`AppConfig(signals=…)`); STORY-176 is 4–5. Honest sprint total is **12–13, not 10** — the split
booked 6 points for work the first pass assessed at 7–8 while asserting it was "the same work in
two halves". That arithmetic did not close, and I should have caught it when I wrote it.

**Also actioned:** STORY-146's reality gate is the one loop run this sprint with a **live**
publisher wired (real `config/apps` mapping + real `.env` via `run.py:178`), and it runs *first*,
before STORY-176 AC3 exists. It is safe only circumstantially today (expired trial, `-inMemory`
Dynamo). Its gate now runs with `STATUSPAGE_API_KEY` unset, recorded in the evidence.

---

## STORY-146 — config authoring shape (5 pts)

### Verified contracts / constraints (cited)

- `ComponentConfig` (`backend/src/composition/config.py:57-73`) — `id`, `name`,
  `statuspage_component_id`. `SignalConfig` (`:76-113`) — `signal_key`, `native_id`, `name`,
  `component_id`, `interval_seconds` (+ positive-int validator at `:105`).
- `AppConfig` (`:116-144`) holds flat `components` (`:141-142`) + `signals` (`:143-144`); its
  `model_validator` (`:149-197`) enforces four invariants, including **referential integrity**
  `signal.component_id → declared component` at `:182-189`.
- **Eight consumers of `app.signals` that must not move:** `composition/config.py:174`, `:183`,
  `:236`, `:360`; `composition/run.py:136`; `seed_dynamo.py:56`;
  `composition/vendor_health.py:97`; `scripts/seed_topology.py:44`.
- **Test-side migration surface — 13 files, counted not estimated** (will change, and that is
  expected). 17 `AppConfig(` construction sites across `test_config.py`, `test_dynamo_seed.py`,
  `test_orchestrate.py`, `test_orchestration_integration.py`, `test_pull_loop.py`,
  `test_run_live_loop.py`, `test_vendor_health.py`; plus 10 flat `signals:` YAML blocks across
  `fakes.py`, `test_availability_endpoint.py`, `test_config.py`, `test_dynamo_adapters.py`,
  `test_seed.py`, `test_topology_endpoint.py`. An earlier draft said "~15 sites" and named only
  `test_config.py` — understating the *breadth*, which is what drives the estimate.
- **Probed, not inferred:** pydantic 2.13.4 converts a `ValueError` subclass raised in a
  `model_validator` to `ValidationError`; `ValidationError` *is* a `ValueError`, so
  `load_config`'s `except (TypeError, ValueError)` (`:355-357`) re-raises it as a bare
  `ValueError`. Named errors must therefore be raised outside that block.
- Real location values are opaque vendor entity ids —
  `"dt.entity.synthetic_location": "SYNTHETIC_LOCATION-000000000000005C"`
  (`backend/tests/fixtures/dynatrace/grail_synthetic_events.json:12`, real captured sample, from
  monitor `HTTP_CHECK-DB5792CB88D14CF4` — **not** the live `HTTP_CHECK-38B092E93932C002`, so
  even this one id is not re-derivable for the live monitor while the trial is expired).
- `Config` already exposes `component_for_signal`, `thresholds_for`, `statuspage_mapping()`
  (`config.py:242-299`) — the precedent AC6's `locations_for`/`freshness_for` follow, and the
  downstream values AC8 pins.
- `config/` sits outside `backend/` on purpose (dossier §4): editing it is a topology change,
  which is why `group`/`monitors` are config-authored rather than enum-coded.

### Steps

- [x] 1. Failing test: a nested-shape YAML fixture loads, and each monitor's resolved
      `component_id` equals its parent component's id (no `component_id` field authored).
- [x] 2. Add `MonitorConfig` (nested; `signal_key`/`native_id`/`name`/`interval_seconds`/
      optional `expected_locations`), nest it under `ComponentConfig`, keep the positive-int
      interval validator. Add the `model_validator(mode="before")` on `AppConfig` that
      synthesizes `signals` from `components[].monitors`, stamping the parent id — this is what
      keeps all eight consumers working (AC7).
- [x] 3. Delete the referential validator (`:182-189`) **and both its tests**
      (`test_config.py:112-121` model-level, `:244-262` loader-level). Add the compensating
      check: a raw top-level `signals:` key is rejected with `FlatSignalsRejectedError` (AC2) —
      without this, deleting the validator silently permits a bogus `component_id`.
- [x] 4. Add the `ConfigError(ValueError)` hierarchy (`UndeclaredLocationAliasError`,
      `FlatSignalsRejectedError`, `InvalidFreshnessError`) and a post-construction validation
      step in `load_config` **outside** the `try` at `:343-357`. Failing test asserts the
      specific class, not `ValueError`.
- [x] 5. Failing test: `locations:` map (alias → `native_id` + `label`); an `expected_locations`
      alias with no declaration raises `UndeclaredLocationAliasError` naming the monitor and the
      alias. Then implement.
- [x] 6. Failing test: `freshness:` block — defaults `stale_after_cycles: 3`, `reentry_cycles: 2`,
      zero/negative rejected, values held as **cycle counts** with no multiplication anywhere in
      this story. Then implement.
- [x] 7. Failing test: `locations`/`freshness` are per-app — two apps with different values
      resolve independently via `Config.locations_for(app_id)` / `freshness_for(app_id)`. No
      global merge exists to conflict. Then implement.
- [x] 8. Migrate the test-side surface to the nested shape: **13 files** — 17 `AppConfig(` sites
      and 10 flat `signals:` YAML blocks, enumerated in the contracts section above. AC2's
      raising derive-validator makes any missed site fail **loudly** rather than silently
      yielding `signals == []`, which is why that raise is required.
      Actual surface after mechanical grep verification (recorded in story History): 8 files touched
      `AppConfig(`/`ComponentConfig(`/`SignalConfig(` sites (`test_config.py`, `test_dynamo_seed.py`,
      `test_orchestration_integration.py`, `test_run_live_loop.py`, `test_orchestrate.py`,
      `test_pull_loop.py`, `test_vendor_health.py`) and 3 files with flat `signals:` YAML fixture
      blocks needing migration (`test_config.py`, `test_seed.py`, `test_topology_endpoint.py`);
      `fakes.py`, `test_dynamo_adapters.py`, and `test_availability_endpoint.py` were verified by
      grep to contain no `AppConfig(`/flat `signals:` construction (only incidental docstring/
      variable-name matches of the word "signals") and needed no change.
- [x] 9. Migrate `config/apps/httpcheck.yaml` — **nesting only**, no `locations:`, no
      `expected_locations` (AC8: unverifiable vendor ids must not enter live config). AC8 test:
      assert `signal_key`, `native_id`, `interval_seconds`, `component_for_signal`,
      `thresholds_for`, and `statuspage_mapping()` against **literals captured before the
      migration** — not recomputed from the new file.
- [x] 10. Verify the eight consumer lines are untouched in the story diff (`git diff` check,
      recorded in the story History). Verified: `git diff --name-only 282be8d..HEAD -- run.py
      seed_dynamo.py vendor_health.py scripts/seed_topology.py` is EMPTY — none of the four
      external files changed at all. Within `config.py`, `git diff 282be8d..HEAD` shows the
      referential-integrity loop's `for sig in self.signals:` (line 183 pre-story) as the only
      REMOVED `app.signals`/`self.signals` expression (deliberate, AC2); the other three
      `config.py`-internal expressions (`Config.__init__`, `load_config`'s global uniqueness
      check, the surviving duplicate-signal_key check) are unchanged context lines. Seven
      surviving readers total, all byte-identical expressions — recorded in the story History.
- [x] 11. Wiki blast radius: articles whose `code_refs` include `composition/config.py` or
      `seed_dynamo.py` — update or re-verify + bump `verified_sha`. **Note:** `run.py` is
      deliberately *excluded* from this predicate. It is a `code_ref` in four articles (the
      sweep flags it as an amplifier) and AC7 requires it untouched, so including it would
      over-quarantine four articles for a file this story does not change.

      **Outcome note (2026-07-28): this predicate was TOO NARROW.** The mechanical sweep flagged
      **six** articles, not one: five more carry migrated *test* files in their `code_refs`
      (`test_orchestrate.py`, `test_orchestration_integration.py`, `test_pull_loop.py`,
      `test_run_live_loop.py`, `test_vendor_health.py`, `test_dynamo_seed.py`). `config-layer.md`
      was rewritten (its Facts described the old four-key shape); the other five were
      **re-verified with a per-article stated reason** — their claims are about the *consumption*
      shape, which AC7/AC8 pin byte-identical, so only the tests' `AppConfig(...)` construction
      syntax moved. Retro material: test files as `code_refs` amplify staleness across unrelated
      articles, the same class of problem as the `run.py`/`pyproject.toml` amplifier notes the
      sweep already emits.

### Reality gate (146)

Run the real loop against the **existing** single real monitor with the migrated config
(`python -m src.composition.run`, DynamoDB Local) and confirm the topology seed writes the same
`COMPONENT#`/`SIGNAL#` items as before the migration — a byte-level before/after comparison of
the seeded items. **Verified executable today with no Dynatrace:** the seed runs at
`run.py:202`, before and independent of any observation arriving, and both
`check_vendor_id_health` (`vendor_health.py:99-110`) and `run_periodic` (`pull_loop.py:200`)
swallow the expired-trial errors, so the process starts, seeds, and stays up.

**Run it with `STATUSPAGE_API_KEY` unset, and record that in the evidence.** This is the only
loop run this sprint with a live publisher wired — it uses the **real** `config/apps` (mapping
non-empty, `httpcheck.yaml:6`) and the real `.env` (`run.py:178`), and it runs *before*
STORY-176 AC3's guard exists. Today it is safe only circumstantially (no observation can arrive,
so no verdict can form, and Dynamo is `-inMemory`); unsetting the key makes it safe by
construction instead.

---

## STORY-148 — the demo engine wire contract (3 pts)

### Verified contracts / constraints (cited)

- **The seam:** `Executor = Callable[[str], list[dict]]` (`adapters/inbound/dynatrace/query.py:32`),
  documented for injected fakes. Real one built by `make_grail_executor(env_url, api_token)`.
- **Ingest grammar — THREE clauses** (`query.py:85-97`):
  `dt.synthetic.monitor.id == "<native_id>"` AND `event.type == "http_monitor_execution"`, plus
  `timestamp >= toTimestamp("<iso>")` when a watermark exists; emitted as
  `fetch dt.synthetic.events | filter … | sort timestamp asc`. `toTimestamp()` is load-bearing —
  a bare string literal silently matches nothing (STORY-051, live-confirmed). The bound is
  `since.isoformat().replace("+00:00","Z")` → **6**-digit fraction, against **9**-digit rows.
- **Second grammar** (`composition/vendor_health.py:40-53`):
  `fetch dt.synthetic.events, from:now()-2h | filter dt.synthetic.monitor.id == "…" |
  summarize count()`, response a single row keyed literally `"count()"` (`_extract_count`,
  `:56-76`; `"count"` also accepted). Called at `run.py:192-196` for every signal, before the
  loops are built. Never raises — a probe error is logged, so a wrong response shows up as a
  false "monitor id is dead" warning, not a crash.
- **Required row fields — SEVEN.** Five from the assembler (`_assembly.py:86,108,111,114`):
  `timestamp`, `event.id`, `dt.synthetic.monitor.id`, `dt.entity.synthetic_location`, plus
  `event.type` for dispatch. **Two from the normalizer** (`http_normalizer.py:22-23`, both
  `require_field`): `result.status.code`, `result.status.message`.
- **Optional fields, with scale** (`_assembly.py:88-102`): `result.statistics.duration` — a
  **string of NANOSECONDS** (`"755000000"`, fixture:15), `//1_000_000` → `latency_ms`;
  `result.statistics.response_status_code` — a **string-typed number** (`"200"`).
- **HTTP protocol** (`grail_executor.py:43-97`): POST
  `{env_url}/platform/storage/query/v1/query:execute`, body `{"query": …}`, header
  `Authorization: Api-Token …`. Either 200 + `{"records": […]}` / `{"result":{"records":[…]}}`
  (sync fallback), or 202 + `requestToken` → GET `…/query:poll?request-token=…` until
  `state == "SUCCEEDED"`. At `:97`, **no `requestToken` and non-202 ⇒ `return []`, silently.**
- **One row = one location execution**; the normalizer never aggregates
  (`http_normalizer.py:4-7`); dispatch registry maps `event.type` → normalizer
  (`dispatch.py:44-46`) and raises `UnsupportedMonitorTypeError` otherwise.
- **Health mapping is deliberately partial:** `map_synthetic_status` maps only `"0"`/`"HEALTHY"`
  → `UP` and **raises** on anything else (`health_mapping.py:65-70`). Failure codes are
  unobserved; anything we emit is an assumption (AC8).
- `pyproject.toml:29` — `testpaths = ["backend/tests"]`. `pyproject.toml:111` — ruff excludes
  `.agents`, `.venv`, `frontend` — **not** `tools/`. Repo-root import precedent:
  `backend/tests/conftest.py:16-19`.
- Import-linter contracts cover `src.*`; `tools/` is outside all eight, so nothing to declare.

### Steps

- [x] 1. Failing test first (fidelity before features): a hand-built demo row is compared
      field-by-field against `grail_synthetic_events.json` — all **seven** required keys present,
      same value types, `response_status_code` a string. Then write the row builder.
- [x] 2. Failing test: a row intended as 755 ms assembles to `latency_ms == 755` (i.e. the
      builder emits nanoseconds as a string). Then implement. This is the AC2 scale check, kept
      separate from AC1's type check because type-equality cannot catch it.
- [x] 3. Failing test: ingest-grammar parsing honours all three clauses — monitor A's query never
      returns B's rows, a non-matching `event.type` returns nothing, the watermark bound excludes
      older rows; output sorted `timestamp asc`. Then implement.
- [x] 4. Failing test: the watermark bound is **parsed**, not string-compared — a row at
      `…746000000Z` against a bound of `…746000Z` is **included**. Then implement.
- [x] 5. Failing test: the second grammar (`summarize count()`) returns `[{"count()": N}]` for a
      known monitor and a 0-count for an unknown one. Then implement.
- [ ] 6. Wrap it in an HTTP server implementing the pinned protocol (POST `query:execute` → 202
      + `requestToken`, GET `query:poll` → `SUCCEEDED` + `records`), with the `Api-Token` header
      honoured.
- [ ] 7. Test through the **real** `make_grail_executor` against the local server, asserting
      assembled `SignalObservation`s (AC7 — this is what option (b) buys over option (a)).
- [ ] 8. AC8: collect every invented vendor code into ONE named constant with the
      unverified-assumption comment; README states plainly what "failure path tested" means.
- [ ] 9. AC9: `tools/demo_engine/` (underscore), tests under `backend/tests/`, verify the story
      diff touches no file under `backend/src/` (mechanical check over the commit range), and
      confirm `ruff check`/`ruff format` cover the new `tools/` code.

### Reality gate (148)

The AC1/AC2 field-and-scale comparison against the real captured fixture, **plus** the AC7 round
trip through the real `make_grail_executor` and the real HTTP client against the running server,
asserting assembled domain objects. Both are mechanical and executable today with no Dynatrace.
The story's core claim is fidelity, so it is proven by comparison, never by inspection.

**Honest limit to state in the evidence:** the *shape* is verified against a real captured
sample; the *failure codes* are assumed (AC8), because none has ever been observed.

---


## STORY-149 — anti-flap `DEGRADED` streak check (1 pt)

### Verified contracts / constraints (cited)

- The defect: `pipeline.py:226-227` proposes `degraded` for a `DEGRADED` streak of any length,
  with no threshold comparison — asymmetric with the `DOWN` ladder at `:215-224`, which checks
  `major` → `partial` → `degraded`, returns `_INTERNAL_WARNING` for `length == 1`, and
  `_NOTHING` otherwise (including length 0).
- **The docstring documents the defect** (`:210-211`): "always `degraded` — … so no length
  comparison is needed". It changes with the code (AC7).
- `_collapse_health` (`:84-97`): `DOWN` only when **every** location is down; **any** mix →
  `DEGRADED`. So the unguarded path is near-dead at 1 location and hot at 3+.
- `thresholds.degraded` already means "consecutive bad cycles before degraded"
  (`AntiFlapThresholds`, `:146-147`) — no new config.
- `AntiFlapOutcome` enforces the status↔warning coherence invariant at construction (`:171-187`),
  so the warning outcome cannot be conflated with a proposed status.
- **Two existing tests assert the current behaviour and are rewritten:**
  `backend/tests/test_anti_flap.py:185-190` (streak of 1 → `degraded`) and `:240-248` (streak of
  0 → `degraded`).
- **Verified to have no downstream effect:** `orchestrate.py:124-139` already returns NOOP when
  `proposed_status is None`; and `Health.DEGRADED` appears only in `test_anti_flap`,
  `test_pipeline`, `test_streak`, `test_availability`, `test_dynatrace_adapter` — no
  orchestration or e2e test drives a `DEGRADED` collapse. The fix cannot alter `decide`.
- **Out of scope:** Phase 2 (breadth ceiling, D1/D2) — STORY-150.

### Steps

- [ ] 1. Failing test: `DEGRADED` streak of 1 → internal warning (`proposed_status is None`,
      `internal_warning is True`), NOT a `degraded` proposal. Rewrites
      `test_anti_flap.py:185-190` (keeping its intent, renamed to state the new rule).
- [ ] 2. Failing test: `DEGRADED` streak above 1 but below `thresholds.degraded` → nothing
      proposed, no warning (use `thresholds.degraded > 2` to make the band reachable).
- [ ] 3. Failing test: `DEGRADED` streak of 0 → nothing, symmetric with `DOWN` at `:224`.
      Rewrites `test_anti_flap.py:240-248`.
- [ ] 4. Failing test: `DEGRADED` streak `>= thresholds.degraded` → proposes `degraded`
      (unchanged sustained behaviour).
- [ ] 5. Implement the symmetry in the `DEGRADED` branch **and update the `:210-211` docstring**
      in the same diff (AC7).
- [ ] 6. AC8: confirm every existing `DOWN`/`UP` anti-flap assertion passes **untouched** — both
      ladders byte-identical in the diff, nothing weakened or deleted.
- [ ] 7. Revert-check (AC4): revert the fix, confirm the streak-of-1 test fails, restore.
      Recorded as evidence that the test is load-bearing.

### Reality gate (149)

An **`orchestrate_signal`-level** test over a seeded observation stream, not a demo-engine run.
Construct multi-location `SignalObservation`s directly (`Health.UP` from two locations, `DOWN`
from a third) so `_collapse_health` returns `DEGRADED` from a genuine location disagreement —
the defect's real-world shape — then drive `orchestrate_signal` with a real `DecideService` over
DynamoDB Local and a recording publisher, and assert:

1. a **single** disagreeing cycle writes **no** proposal to the proposals table, and
   `GET /api/v1/approvals` returns empty over live HTTP;
2. extending the disagreement past `thresholds.degraded` **does** write one, and the endpoint
   returns it.

**Why not the demo engine** (changed by decision D-A): no demo scenario can produce a `DOWN`
observation at all — `map_synthetic_status` raises on any non-healthy code
(`health_mapping.py:65-70`) and `dispatch.py:80` loses the whole batch when it does. A
demo-engine gate would therefore have **passed step 1 for the wrong reason** — no proposal
because nothing was ingested, not because anti-flap damped it — and then failed step 2. Seeding
observations directly enters the pipeline *below* the vendor mapping, so it exercises the real
`collapse → streak → anti_flap → decide` chain and the real persistence and HTTP surface, with
no invented vendor codes anywhere.

**Honest limit:** this proves the fix against a *constructed* location disagreement. It does not
prove Dynatrace reports failures the way we assume — nothing can, until STORY-154/177. The
unit-level ACs remain the primary evidence; this gate is system-level corroboration.

---

## Decisions — RESOLVED by the PO 2026-07-28 ("i am ok with your recommendation")

**D-A → Option B.** The demo is scoped to `UP` + absence scenarios. STORY-176 AC5 lost its three
failure cases and gained three absence cases instead (dark monitor, staggered intervals, late
return — each exercising the freshness path, which the original set never touched). AC7 **inverted**
from "prove a proposal opens" to "prove none can, and state that plainly in the README", which also
retires the STORY-151 confound entirely. The provisional failure mapping became **STORY-177**, a
first-class story with its own review rather than a demo prerequisite smuggled into `backend/src/`.
STORY-149's reality gate is replaced with an `orchestrate_signal`-level test over a seeded
observation stream — see that story's gate below.

**D-B → move STORY-176 to sprint 63.** Sprint 62 is 9 pts across 3 stories
(146 at 5, 148 at 3, 149 at 1) and the goal is restated to "the shape and the wire are right".
STORY-176 opens sprint 63, where its fleet-scale data also feeds the frontend work.

The original decision text is kept below, unedited, because the reasoning is the record of *why*
the sprint has this shape — and because the rejected option A is the one a future sprint will
revisit under STORY-177.

### D-A · How do we get a `DOWN` observation into the demo? (blocker)

The demo engine cannot produce a failure observation through the real ingest path
(`health_mapping.py:65-70` raises; see "Second verifier pass"). Two ways forward:

**Option A — extend `health_mapping.py` with an explicitly-provisional failure mapping.**
Add a named, commented, unverified-pending-trial-renewal code set that maps to `DOWN`/`DEGRADED`.
Keeps all five scenarios, STORY-176 AC7, and STORY-149's end-to-end gate.
*Costs:* amends STORY-148 AC9 / STORY-176 AC8 (the no-`backend/src/` rule that makes both stories
low-risk), takes a slice of STORY-154, and runs against that file's **documented intent** —
`health_mapping.py:57-63` argues explicitly that inventing codes "would silently mis-map (or mask)
the real failure value during that verification, so it is deliberately NOT done". If the real code
later turns out to mean something else, we have baked in a wrong mapping.
*Variant A′:* gate the provisional mapping behind an env var so production behaviour stays
byte-identical and fail-loud unless explicitly enabled. Narrower risk, but still a production-code
change and a new config surface, and it partly re-invents `sample_mode` (which STORY-155 removes).

**Option B — scope the demo to `UP` + gap/dark scenarios this sprint.** Delete STORY-176 AC7, cut
AC5's three failure scenarios, and move all failure-path evidence to unit tests over hand-built
`Health.DOWN` observations. STORY-149's reality gate becomes an `orchestrate_signal`-level test
with a seeded observation stream rather than a demo-engine run.
*Keeps:* the no-`backend/src/` rule, and the fleet-scale claim (≥12 components / ≥40 signals /
≥4 locations of real ingest) which is most of STORY-176's value.
*Costs:* the demo cannot exercise the anti-flap ladder end to end this sprint — which is part of
what the PO asked the demo engine for ("we can test all the cases"). That capability moves to the
sprint that lands the real failure codes.

**Recommendation: Option B for this sprint**, with the failure-code mapping folded into STORY-154
as a first-class story rather than smuggled in as a demo prerequisite. Reasons: STORY-149's
*primary* evidence is its unit ACs, which are unaffected; the fleet claim survives intact; and
inventing vendor codes against the producing file's explicit written intent is the kind of
decision that should be a story with its own review, not a side effect. It also fits the PO's
pacing directive. If the PO wants the ladder demonstrable now, A′ is the safer form of A.

### D-B · Sizing — the sprint is 12–13 points, not 10

Honest re-estimate after the second pass: STORY-146 3→**5** (13-file migration surface),
STORY-176 3→**4–5**. With 148 (3) and 149 (1) that is 13, against a ~9–11 baseline and the PO's
explicit "no need to rush in single stretch".

Options: (i) **move STORY-176 to sprint 63**, leaving a 9-point foundations sprint
(146 + 148 + 149) whose goal restates to "the shape and the wire are right" — the fleet then opens
sprint 63 where it also feeds the frontend work real data; (ii) accept 13 and let the sprint run
long; (iii) trim STORY-176's fleet size, which weakens the one claim it exists to make.

**Recommendation: (i).** It keeps every story fully verified rather than three verified and one
rushed, and STORY-176 is the natural opener for 63. Note this interacts with D-A: under Option B
STORY-176 is smaller, so (ii) becomes more tenable if the PO prefers to keep the fleet in 62.

---

## Sprint close

- **Mid-sprint gates:** scoped `yt_gate.py --only` to what each story's diff can affect
  (backend-only sprint → `pytest`, import-linter, `ruff check`, `ruff format --check`;
  `cfn-lint` only if `infra/` is touched, which it should not be).
- **Final gate:** the FULL five-command backend gate on the final HEAD, clean tree — this is the
  evidence of record. No frontend gates apply (no `frontend/` diff this sprint).
- **Wiki compile pass** before review: fold in the config-shape change, the demo engine as a new
  article, the `sample_mode` supersession note, and the anti-flap correction; rehabilitate
  anything the sweep marks stale; lint links. Sweep was clean at planning (`8554c7b`).
- **Demo script:** the nested config reads as a hierarchy and the migrated real config seeds
  byte-identically (146) → demo rows proven field-and-scale identical to the real captured
  fixture, answered over real HTTP through the real `make_grail_executor`, both query grammars
  (148) → a single-cycle location disagreement proposes nothing while a sustained one does,
  end to end through `orchestrate_signal` and `GET /api/v1/approvals` (149).
- **What this sprint does NOT demo, stated plainly at review** so nobody mistakes the scope: no
  12-component fleet (STORY-176, sprint 63), and no failure-path ingest at all — the demo engine
  can serve rows but the vendor mapping raises on any non-healthy code, so the ladder is
  demonstrable only from seeded observations until STORY-177 lands a provisional mapping.
- **Not in this sprint, and stated at review so scope is unambiguous:** all frontend work
  (sprint 63+); STORY-147 (deferred to 63, where its consumer lands); STORY-176 (deferred to 63,
  decision D-B); STORY-177 (provisional failure mapping, created by decision D-A); STORY-150
  breadth model; STORY-151 per-component rollup; STORY-152 expected-locations completeness;
  STORY-153 rejection suppression; STORY-154 real failure codes (blocked on trial renewal);
  STORY-155 sample_mode removal; STORY-173 the leaked-container fixture fix.
