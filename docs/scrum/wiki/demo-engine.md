---
title: The Grail demo engine — a local stand-in for the expired Dynatrace trial (tools/demo_engine/)
code_refs: [tools/demo_engine/__init__.py, tools/demo_engine/rows.py, tools/demo_engine/query_grammar.py, tools/demo_engine/store.py, tools/demo_engine/server.py, tools/demo_engine/scenario.py, tools/demo_engine/assumed_failure_codes.py, backend/tests/demo_engine/test_rows.py, backend/tests/demo_engine/test_query_grammar.py, backend/tests/demo_engine/test_watermark_precision.py, backend/tests/demo_engine/test_vendor_health_query.py, backend/tests/demo_engine/test_server.py, backend/tests/demo_engine/test_via_grail_executor.py, backend/tests/demo_engine/test_assumed_failure_codes.py, backend/tests/demo_engine/test_scenario.py, backend/tests/demo_engine/test_scenario_coverage.py, backend/tests/test_demo_fleet_config.py, backend/tests/fixtures/dynatrace/grail_synthetic_events.json, backend/tests/conftest.py, config/demo/fleet-core.yaml, config/demo/fleet-platform.yaml, config/demo/fleet-edge.yaml, config/demo/scenarios/clean-fleet.yaml, config/demo/scenarios/dark-location.yaml, config/demo/scenarios/dark-monitor.yaml, config/demo/scenarios/staggered-intervals.yaml, config/demo/scenarios/late-return.yaml]
verified_sha: d530238
verified_sprint: sprint-63
status: verified          # verified | stale | archived
---

## Facts (verified against code)

A local HTTP server that speaks the Dynatrace Grail `query:execute` API faithfully enough that the
**real, unmodified** `make_grail_executor` can talk to it and the real ingest path assembles correct
`SignalObservation`s from its rows (`tools/demo_engine/__init__.py:1-15`). It exists because the
Dynatrace trial expired before a live failure signal could ever be captured (memory:
`dynatrace-trial-expired`); the PO approved it as the substitute for live metrics. Built by
STORY-148 as **part 1 of 2 — the wire contract only**. **Part 2a (the scenario player, the demo
fleet config, and the publish guard) landed in STORY-176 (sprint 63) — see the dedicated section
below.** The end-to-end loop run itself, and its own two-sided reality gate, is **part 2b,
STORY-182 (sprint 64)** — no demo loop has been started by any story to date.

### Where it lives, and why that is not `backend/src/`
- The package is `tools/demo_engine/`, outside `backend/src/` **on purpose** (dossier §4,
  `__init__.py:12-14`): it can never enter the production image, and every module here is free to
  import `src.*` while nothing under `backend/src/` ever imports this package. That direction is
  what keeps it a test double rather than a second production path.
- Importability is a `sys.path` insertion in the ONE shared `backend/tests/conftest.py`
  (repo-root `tools/`, alongside the pre-existing `scripts/` insertion). A package-local
  `backend/tests/demo_engine/conftest.py` was tried and **deleted**: a bare `__init__.py`-less
  `conftest.py` collides on `sys.modules['conftest']` and silently broke `test_dynamo_local.py`.
  See [[dev-setup-and-dod]] and [[persistence-adapters]]. **STORY-180 AC6/minor 8** reviewed the
  insertion position explicitly and kept it at the FRONT (`insert(0, ...)`, matching the
  `scripts/` precedent), with the reason recorded in `conftest.py` itself: `tools/` today holds
  only `demo_engine/` (importable) and the hyphenated, unimportable `ui-sweep/`, so there is zero
  real collision risk. Append is the fallback if `tools/` ever gains a second, generically-named
  importable package.
- STORY-148 changed **no** file under `backend/src/` (its AC9). The engine adapts to production, not
  the reverse.

### The row shape (`rows.py`)
- `build_row(...)` (`rows.py:47`) emits the seven fields the real ingest path actually reads:
  `timestamp`, `event.id`, `event.type`, `dt.synthetic.monitor.id`,
  `dt.entity.synthetic_location`, `result.status.code`, `result.status.message`, plus the two
  OPTIONAL statistics fields (`rows.py:84-87`). Cosmetic fixture fields (`event.kind`,
  `result.state`, `dt.entity.http_check`, `monitor.name`, …) are deliberately **omitted**
  (`rows.py:12-15`) — no production code reads them, and including them would imply they are part
  of the wire contract.
- **The units trap is closed by the signature, not by a comment.** `duration_ms` and
  `response_status_code` are taken in NATURAL units and converted to the wire's string/nanosecond
  shape inside the builder — `str(duration_ms * 1_000_000)` (`rows.py:85`). There is no
  string-typed `duration` parameter a caller could hand `"755"` (ms) where the wire means
  `"755000000"` (ns).
- `format_ns_timestamp` (`rows.py:32`) always emits exactly **9** fractional digits —
  `f"{base}.{dt.microsecond:06d}000Z"` (`rows.py:44`). Real Grail rows carry nanosecond precision;
  Python has no sub-microsecond precision, so the trailing three digits are always `000`, which
  matches the real captured sample's own shape. It rejects a naive or non-UTC datetime
  (`rows.py:41-42`).
- Field-and-type fidelity is asserted against the **real captured sample**
  `backend/tests/fixtures/dynatrace/grail_synthetic_events.json` — read off disk, not restated
  inline (`backend/tests/demo_engine/test_rows.py`). The fixture predates this story (committed
  `fc65483` under STORY-016b), so the test cannot be circular.
- `STATUS_CODE_HEALTHY`/`STATUS_MESSAGE_HEALTHY` (`rows.py:26-27`) previously documented themselves
  as "the ONLY (code, message) pair `map_synthetic_status` accepts" — false, and corrected by
  STORY-180 AC1/minor 6: `health_mapping.py:65` tests `code == "0" or message == "HEALTHY"`, an
  `or`, so either half alone is sufficient; the two constants are still emitted together by default
  only because that mirrors the real captured sample's own shape.

### The two query grammars (`query_grammar.py`, `store.py`)
- `parse_query` (`query_grammar.py:69`) recognizes exactly the two DQL shapes production emits: the
  ingest grammar from `build_dql_query` (`adapters/inbound/dynatrace/query.py:85-97`) and the
  vendor-health `summarize count()` probe from `build_vendor_health_query`
  (`composition/vendor_health.py:40-53`).
- Anything else raises `UnrecognizedDqlQueryError` (`query_grammar.py:34`, raised at `:78` and
  `:86`), which `server.py:99-101` turns into an HTTP **400**. This fail-loud path is not
  decoration: `grail_executor.py:97` returns `[]` on an unexpected envelope, so a regression from
  loud to silent would be indistinguishable from "no data" — the exact shape of the STORY-051
  ingest stall. STORY-176 adds a third grammar, which is what this guard is for.
- **The watermark bound is parsed by the REAL production parser** — `parse_watermark_bound`
  delegates to `_assembly.py::parse_ns_timestamp` (`query_grammar.py:26,66`), imported, never
  reimplemented. Bound and row timestamps are therefore compared as `datetime`s, never as strings:
  a 6-digit-fraction bound sorts lexicographically BEFORE a 9-digit row at the same instant, which
  reproduces the STORY-051 stall inside the engine if this is skipped (`query_grammar.py:54-64`).
- Ingest filtering is three-clause — monitor id AND `event.type` AND the watermark lower bound —
  and results are sorted by parsed timestamp (`store.py:56-68`).
- The vendor-health answer is `[{"count()": count}]` (`store.py:80`), counted inside
  `request_instant - VENDOR_HEALTH_WINDOW` (`store.py:73-79`). `VENDOR_HEALTH_WINDOW` is a
  2-hour literal (`store.py:22`) that mirrors `_HEALTH_CHECK_WINDOW` (`vendor_health.py:37`) but is
  deliberately NOT imported — the window is part of the wire contract the engine answers, not an
  implementation detail borrowed from composition. **STORY-180 AC2** closed the divergence risk
  this created: `test_vendor_health_window_matches_the_composition_health_check_window`
  (`test_vendor_health_query.py`) asserts the two are numerically equal (parsing
  `_HEALTH_CHECK_WINDOW`'s `"<N>h"` shape in the TEST only) and fails if a future change to the
  composition constant is not mirrored here — the route decided at planning was this equality
  test, not teaching the engine to parse the DQL `from:` clause (`parse_query` never reads it at
  all: no `from:` regex exists, `query_grammar.py:28-31`, and `VendorHealthQuery` has no window
  field). `request_instant` defaults to the wall clock, but ONLY the vendor-health branch reads it
  — an ingest query never touches it at all (`store.py::handle_query`; pinned by
  `test_ingest_query_never_reads_the_wall_clock`, `test_query_grammar.py`, STORY-180 AC5/minor 7,
  which made the clock read fresh-per-vendor-health-call-only rather than unconditional on every
  call).

### The wire protocol (`server.py`)
- Serves the **async** branch of what `make_grail_executor` speaks
  (`grail_executor.py:43-97`): POST `…/query:execute` → `202` + a JSON body carrying
  `requestToken` (`server.py:103-105`), then GET `…/query:poll?request-token=…` →
  `{"state": "SUCCEEDED", "records": …}` on the first poll (`server.py:122`). The async branch is
  chosen deliberately — a sync-only server would exercise only the executor's fallback branch
  (`server.py:4-12`). Every query resolves synchronously server-side; only the protocol is async.
- Three obligations of `grail_executor.py` are pinned by tests (`server.py:14-20`): the `202` body
  is JSON (`grail_executor.py:73` parses it unconditionally); every poll response carries `state`
  (a bare `{"records": …}` raises "unknown state: None", `grail_executor.py:136-137`); and the
  `Authorization: Api-Token …` header is required.
- **Auth is a scheme-prefix check only** (`server.py:65-72`): the header must start with
  `"Api-Token "`. A wrong scheme and an absent header both 401; an arbitrary junk token returns
  202. That is a sound demo simplification — the engine has no notion of a valid Dynatrace token —
  and it satisfies AC6, which pins the header's PRESENCE. It is **not** token validation and must
  never be reported as such.
- `do_POST` drains the request body **before** any early return (`server.py:81-82`). This is a
  root-cause fix, not a retry band-aid: closing the connection with unread bytes in the socket's
  receive buffer can make the OS send a TCP RST instead of a clean close, surfacing to the client
  as an intermittent `ConnectionResetError`/`httpx.ReadError` — reproduced live on Windows against
  the 401 branch.
- A malformed JSON body returns a **400** with a message rather than a stdlib traceback
  (`server.py:90-94`).
- `DemoEngineServer` binds port 0 and reads the ACTUALLY bound port back off the live socket via
  `base_url` → `self._httpd.server_address` (`server.py:140-143`) — never a port computed and handed
  off around the bind, which is precisely the defect class STORY-179 hit in this repo's own
  DynamoDB-Local fixture (`server.py:128-131`).
- `_DemoHTTPServer.results` (`server.py:48`) is a per-token result cache that is now bounded:
  `do_GET` **pops** (not merely reads) a token's entry on its first poll (`server.py::do_GET`),
  since every query here resolves synchronously server-side and there is no "still RUNNING, poll
  again" state to preserve an entry for. Before STORY-180 AC4/minor 5 it only grew, one entry per
  query, for the process lifetime — harmless for a test-scoped engine, a slow leak once STORY-176
  makes it long-running. Pinned by `test_results_cache_is_evicted_after_being_polled`
  (`test_server.py`).

### Scope honesty: this engine emits UP and absence, nothing else
- `map_synthetic_status` (`health_mapping.py:54-70`) maps ONLY `code == "0"` /
  `message == "HEALTHY"` to `Health.UP` and RAISES on every other value. A real failure code has
  never been observed, and that module's own docstring says inventing one "would silently mis-map
  (or mask) the real failure value".
- So every non-healthy pair this engine can build is an **assumption**, collected in one named place
  (`assumed_failure_codes.py:33-34`: `"1"`/`"UNHEALTHY"`, marked UNVERIFIED pending trial renewal,
  STORY-154) so nobody mistakes a demo failure row for a confirmed vendor contract.
- STORY-148's reality gate **executed** this: the assumed row reached the real, unmodified
  `map_synthetic_status`, raised `UnknownVendorStatusError`, and took the whole batch with it
  (`dispatch.py:80`'s bare comprehension). The failure path is proven **rejected** — the opposite of
  "tested". Adding a real failure mapping to `backend/src/` is STORY-177, a first-class reviewed
  decision, never a side effect of a demo fixture (`assumed_failure_codes.py:16-22`).
- Consequence for anything downstream: **no demo scenario can drive a `DOWN` or `DEGRADED`
  proposal.** PO decision D-A re-pointed STORY-149's reality gate away from the demo engine for
  exactly this reason — a demo-based gate would have false-passed "no proposal appeared" because
  nothing was ingested, not because anti-flap damped it. See
  [[core-pipeline-and-availability]].

### The scenario player, the demo fleet, and the publish guard (STORY-176, part 2a)
- **The player is a scripted expander, not a random generator.** `SignalScenario`
  (`scenario.py::SignalScenario`) declares an ORDERED list of cycles per signal; each cycle names
  which locations report `UP` that cycle — a location's absence from a cycle's list is the only
  other outcome this `UP`-and-absence-only engine can express (see "Scope honesty" above).
  `load_scenario_file` (`scenario.py::load_scenario_file`) parses a scenario YAML into a list of
  these, raising `InvalidScenarioError` on a non-mapping top level, a signal block missing
  `monitor_id`/`interval_seconds`/`cycles`, a field of the wrong TYPE (`cycles` null/non-list, a
  non-list cycle entry, a non-int `interval_seconds`, a non-string `monitor_id`), or a non-positive
  `interval_seconds` — every message names both the file and the signal key, never a bare stdlib
  exception (sprint-63 fix round, quality finding M2: this guard did not exist at first ship, so
  `cycles:` with no value leaked a bare `TypeError`, and `interval_seconds: -30` was silently
  accepted and emitted rows in the future). Pinned by
  `backend/tests/demo_engine/test_scenario.py::test_load_scenario_file_rejects_non_mapping_top_level`,
  `::test_load_scenario_file_missing_required_field_raises`, and the
  `test_load_scenario_file_*_rejected*` family (one test per rejected shape).
- **Expansion is PAST-ANCHORED, decided at sprint-63 planning** (`scenario.py::expand_scenario`):
  the scenario's LAST cycle lands at the caller's `end_time` (typically `clock.now()`); each earlier
  cycle lands successively further back at the monitor's own `interval_seconds`. This is what keeps
  the whole declared ladder inside `orchestrate.py:94-98`'s rolling 7-cycle window on the very first
  query and every row at or before `end_time` — a forward player (t0 → now) would instead have every
  cycle beyond `end_time + 5min` silently quarantined by `ingest_service.py`'s `FUTURE_TOLERANCE`
  until wall-clock time caught up. **This "at or before `end_time`" guarantee holds provided
  `interval_seconds` is positive** — a negative value would walk the ladder FORWARD, not back
  (reproduced live pre-fix: `interval_seconds: -30` emitted `12:01:00, 12:00:30` for
  `end_time=12:00:00`); `load_scenario_file` now rejects a non-positive `interval_seconds` at load
  time (`InvalidScenarioError`, sprint-63 fix round, quality finding M2), so every scenario that
  survives loading satisfies it. Pinned by
  `test_scenario.py::test_expand_scenario_ladder_fits_inside_orchestrates_rolling_window`,
  `::test_expand_scenario_no_row_lands_after_end_time`,
  `::test_expand_scenario_last_row_is_within_the_vendor_health_window` (the last one ties past-anchoring
  directly to `store.py`'s `VENDOR_HEALTH_WINDOW`), and
  `::test_load_scenario_file_interval_seconds_negative_rejected_with_named_error`.
- **The demo fleet** (`config/demo/`, repo root — never `config/apps/`) is three files in STORY-146's
  nested shape (`fleet-core.yaml`, `fleet-platform.yaml`, `fleet-edge.yaml`), each a DISTINCT `app.id`:
  13 components, 41 signals, 4 declared locations (`loc-a`..`loc-d`), a `freshness:` block per file,
  every monitor at `interval_seconds <= 60`. Pinned by
  `backend/tests/test_demo_fleet_config.py::test_demo_fleet_scale_meets_ac4_minimums`,
  `::test_demo_fleet_every_files_locations_and_freshness_survive_loading`, and
  `::test_demo_fleet_monitors_use_short_intervals`. STORY-146's own F4 fix (`config.py:715-721`)
  already turns a duplicate `app.id` into a raised `DuplicateAppIdError` rather than the silent
  `locations`/`freshness` discard STORY-176's citation describes — the three files simply declare
  distinct ids, so this test proves the POSITIVE (survival) case, not a trap.
- **The publish guard is config-only and needs `CONFIG_DIR` on BOTH composition roots that could
  build a live publisher — not just the loop.** `config/demo/` declares NO
  `statuspage_component_id` on any component, so `Config.statuspage_mapping()` is `{}` and
  `build_publisher` (`publish_helper.py:211`) falls through to a `LoggingPublisher` delegate **even
  with real Statuspage credentials present** (the repo-root `.env`, loaded by `run.py:178`'s
  `load_dotenv()`, which walks up from the source file, not CWD). The two roots — the loop
  (`run.py::main` → `build_live_loop`) and the API's approve trigger (`app.py::create_app`, which
  takes no `config_dir` argument in the documented recipe, so `CONFIG_DIR` alone governs it) — are
  BOTH asserted in-process (`create_app()` called directly, no HTTP: no v1 route exposes the
  mapping/publisher/config, verified by enumerating all 14 routes at sprint-63 planning), pinned by
  `test_demo_fleet_config.py::test_create_app_with_demo_config_dir_yields_empty_mapping_and_logging_delegate`.
  The SAME assertion pointed at `config/apps` (which DOES declare a `statuspage_component_id`,
  `config/apps/httpcheck.yaml:8`) selects a real `StatuspagePublisher` TYPE with no network call —
  the two-sided proof that the guard is a property of the config, not a promise about wiring
  (`::test_create_app_with_live_config_dir_and_real_looking_creds_selects_real_publisher_type`).
  Demo component ids are additionally DISJOINT from `config/apps`'s ids (a real set intersection,
  `::test_demo_component_ids_are_disjoint_from_config_apps_component_ids`) because
  `StatuspagePublisher` keys on the canonical component id (`statuspage/__init__.py:41-46`), so a
  collision would PATCH the real page even with `CONFIG_DIR` set correctly everywhere — proven
  catchable, not just asserted absent, by
  `::test_disjointness_check_actually_catches_a_collision`.
- **Scenario coverage is `UP` and absence only** (`config/demo/scenarios/`): a clean fleet
  (`clean-fleet.yaml`), a fully dark location (`dark-location.yaml` — lowers `distinct_locations`,
  does NOT touch a freshness/completeness path, since `expected_locations` has zero consumers
  outside `config.py`), a fully dark monitor (`dark-monitor.yaml` — empty window → `streak` returns
  `None` → `orchestrate_signal` NOOPs, `orchestrate.py:113-121`), staggered intervals on one
  component (`staggered-intervals.yaml` — two monitors at different `interval_seconds` (30/45); their
  ingested `observed_at` spacing matches each monitor's OWN interval, pinned by
  `test_scenario_coverage.py::test_staggered_intervals_scenario_observed_at_spacing_matches_each_monitors_own_interval`.
  **Correction (sprint-63 fix round, quality finding M1):** an earlier version of this bullet and its
  cited test claimed the two monitors' `bucket_into_cycles` results "share no cycle boundary" — false:
  because expansion is past-anchored, both monitors' LAST cycle lands at the same `end_time`, so they
  share exactly that one boundary; the prior test only asserted set INEQUALITY of bucket keys, built
  from the `since`/`interval` the test itself supplied rather than the rows, so it never actually
  pinned per-monitor spacing and could not have caught the false claim), and a late-returning monitor
  (`late-return.yaml` — ingest simply resumes after a gap; `reentry_cycles` has no consumer, so no
  re-entry POLICY is asserted). All five are driven through the real `normalize_rows` →
  `IngestService` chain with in-memory fakes, pinned by
  `backend/tests/demo_engine/test_scenario_coverage.py`.

### Test surface
- 29 tests in `backend/tests/demo_engine/` across seven files (STORY-180 net +2 over STORY-148's
  27: AC2 and AC4 each added one test, AC5/minor 3 folded a stdlib-only test into a docstring
  (-1), and AC5/minor 7 added one — a rename, AC5/minor 4, does not change the count):
  `test_rows.py` (fixture fidelity), `test_query_grammar.py` (both grammars + the fail-loud error
  + the wall-clock-not-read-for-ingest guard), `test_watermark_precision.py` (the 0/6/9-digit
  bound, the 0- and 6-digit cases now routed through the real `build_dql_query`), the vendor-health
  window equality guard (`test_vendor_health_query.py`), `test_server.py` (the HTTP protocol, auth,
  the 400s, and the token-cache eviction), `test_via_grail_executor.py` (the real executor
  end-to-end), `test_assumed_failure_codes.py` (the assumption is labeled and rejected).
- None of them needs Dynamo: neither `dynamo_local` (session-scoped) nor `clean_dynamo_tables` is
  `autouse`, so this subset runs standalone.
- STORY-176 part 2a adds **20 more** tests in `backend/tests/demo_engine/` (now nine files, 49
  total): `test_scenario.py` (15 — AC1 row-count-per-cycle, AC2's format/monotonicity/window/
  backfill/not-in-future, and the scenario-file load path, including its own malformed-input
  behaviour) and `test_scenario_coverage.py` (5 — one per AC5 case, each driven through the real
  ingest chain). A further **10 tests** in `backend/tests/test_demo_fleet_config.py` (composition
  zone, not `demo_engine/` proper — it tests `Config`/`create_app` against `config/demo/`, not the
  engine package) pin the publish guard and the fleet's scale/multi-file survival; TWO of those
  (`test_create_app_with_demo_config_dir_...`, `test_create_app_with_live_config_dir_...`) need
  `dynamo_local` (a real `create_app()` call wires real Dynamo-backed repos, though no I/O actually
  occurs before assertion — `boto3.resource(...).Table(...)` is lazy). Grand total: 604 tests
  repo-wide (572 at the sprint-63 branch point `e107811`; STORY-180 brought it to 574 first; this
  story's +30 brings it to 604).

## Inference (not verified — reasoning, not fact)

- The engine's fidelity claim is bounded by what the captured sample contains. It proves the fields
  the ingest path READS are right in shape, type and scale; it cannot prove Grail never sends
  something else, and it says nothing about failure-row shape (see the scope-honesty section).
- STORY-180 closed the two items this section used to flag as future risk for STORY-176's
  long-running engine: `server.results` is now evicted per poll (Facts, above) and the
  vendor-health window has an equality guard against silent divergence (Facts, above). Neither was
  ever a correctness bug in the STORY-148 test-scoped lifetime; STORY-180 made both hold under a
  long-running process too.

## History

- sprint-63 (STORY-176, part 2a): the scenario player (`scenario.py`), the demo fleet
  (`config/demo/`, 13 components / 41 signals / 4 locations across three distinct-`app.id` files),
  the five UP-and-absence scenarios (`config/demo/scenarios/`), and the config-only publish guard
  (proven in-process, both sides — an empty demo mapping selecting `LoggingPublisher` AND the live
  `config/apps` mapping selecting a real `StatuspagePublisher` TYPE, plus a proven-catchable
  component-id disjointness check) all land. AC6/AC7 (the actual loop run) are explicitly OUT of
  this story — split to STORY-182 (sprint 64) at sprint-63 planning after a re-estimate put the
  combined story at 6 points. Zero files under `backend/src/` changed (AC8, mechanically verified:
  `git diff --name-only 1aadf95..HEAD -- backend/src/` is empty). Net test count: 574 → 604 (+30).
  DoD gate 5/5 backend (no frontend files touched). verified_sha -> d530238.
- sprint-63 (STORY-180): all eight deferred STORY-148 quality-review minors closed. AC1/minor 6:
  `rows.py:26-27`'s docstring corrected — `map_synthetic_status` accepts either half of the pair,
  not only the pair together. AC2/minor 1: an equality test now fails if `store.py`'s
  `VENDOR_HEALTH_WINDOW` diverges from `vendor_health.py`'s `_HEALTH_CHECK_WINDOW` (the route
  decided at planning; parsing the DQL `from:` clause remains unimplemented and is a legitimate
  future improvement, not a defect). AC3/minor 2: the watermark-precision test's 0- and 6-digit
  cases now build their query through the real `build_dql_query` (with `overlap=timedelta(0)`,
  load-bearing — the STORY-051 discrimination the test exists to prove would silently stop
  working at the 5-minute default); the 9-digit case keeps its literal (the real builder cannot
  emit one). AC4/minor 5: `server.results` is popped, not merely read, on first poll, bounding a
  cache that previously grew one entry per query for the process lifetime. AC5/minors 3,4,7: the
  stdlib-only string-ordering test folded into a docstring (test count -1), the overstated test
  name corrected, and `store.py::handle_query` stopped reading the wall clock on the ingest path
  (it is never used there). AC6/minor 8: the `tools/` `sys.path` front-insertion in
  `backend/tests/conftest.py` is now an explicit, reasoned decision, not a silent default. Net
  test count: 27 -> 29. Zero files under `backend/src/` changed (AC8). DoD gate 8/8. verified_sha
  -> 701bfab.
- sprint-62 (STORY-148): created at the sprint-end compile pass, after the story shipped and was
  reality-gated. Deliberately deferred out of the story itself: the engine's Facts are only worth
  writing down once its wire shape survived a live probe, and the probe changed what was worth
  saying (the auth check is a scheme prefix, not validation; the assumed failure code is REJECTED
  end-to-end and takes its whole batch with it). Spec review PASS 10/10; quality review
  FIX_REQUIRED → 2 majors fixed (a README recipe that documented the very conftest file the story
  had deleted; the fail-loud contract shipping with zero test coverage) and 8 minors routed to
  STORY-180. DoD gate 8/8 at `29430ff`, reality gate 19/19. verified_sha -> 64f680b (the last
  commit touching the engine or its tests).
