---
title: The Grail demo engine — a local stand-in for the expired Dynatrace trial (tools/demo_engine/)
code_refs: [tools/demo_engine/__init__.py, tools/demo_engine/rows.py, tools/demo_engine/query_grammar.py, tools/demo_engine/store.py, tools/demo_engine/server.py, tools/demo_engine/scenario.py, tools/demo_engine/assumed_failure_codes.py, backend/tests/demo_engine/test_rows.py, backend/tests/demo_engine/test_query_grammar.py, backend/tests/demo_engine/test_watermark_precision.py, backend/tests/demo_engine/test_vendor_health_query.py, backend/tests/demo_engine/test_server.py, backend/tests/demo_engine/test_via_grail_executor.py, backend/tests/demo_engine/test_assumed_failure_codes.py, backend/tests/demo_engine/test_scenario.py, backend/tests/demo_engine/test_scenario_coverage.py, backend/tests/test_demo_fleet_config.py, backend/tests/fixtures/dynatrace/grail_synthetic_events.json, backend/tests/conftest.py, config/demo/fleet-core.yaml, config/demo/fleet-platform.yaml, config/demo/fleet-edge.yaml, config/demo/scenarios/clean-fleet.yaml, config/demo/scenarios/dark-location.yaml, config/demo/scenarios/dark-monitor.yaml, config/demo/scenarios/staggered-intervals.yaml, config/demo/scenarios/late-return.yaml, config/demo/scenarios/down-ladder.yaml, config/demo/scenarios/partial-breadth.yaml, config/demo/scenarios/degraded-ladder.yaml, config/demo/scenarios/poison-row.yaml, tools/demo_loop_gate/__init__.py, tools/demo_loop_gate/harness.py, tools/demo_loop_gate/env_matrix.py, tools/demo_loop_gate/fleet_coverage.py, tools/demo_loop_gate/guard_reality_gate.py, tools/demo_loop_gate/backfill_reality_gate.py, tools/demo_loop_gate/failure_path_reality_gate.py, tools/demo_loop_gate/publisher_chain.py, tools/demo_loop_gate/evidence.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, backend/src/adapters/inbound/dynatrace/dispatch.py]
verified_sha: c2fd3d2
verified_sprint: sprint-68
status: verified          # verified | stale | archived
# Re-verified 2026-07-30 (sprint-64, STORY-183) by the orchestrator. Changed paths in the range
# c2c3345..638853a: tools/demo_engine/server.py + backend/tests/demo_engine/test_server.py (both
# STORY-183's retention bound), and tools/import_provenance.py's arrival (STORY-187, NOT a code_ref
# of this article — it is not part of the demo engine). The cache Facts were REWRITTEN, not merely
# re-stamped: STORY-180's consume-on-first-poll description was made false by STORY-183 and is now
# carried as an explicit superseded note. Every new behavioural Fact cites its pinning test (A2).
# Re-verified again 2026-07-30 (STORY-184): tools/demo_engine/scenario.py +
# backend/tests/demo_engine/test_scenario.py. The past-anchoring Fact was REWRITTEN, not
# re-stamped: it said the at-or-before-end_time guarantee 'holds provided interval_seconds is
# positive' and credited the LOADER for enforcing it -- true in sprint 63, made obsolete by
# STORY-184 moving the invariant onto the type, which makes the guarantee UNCONDITIONAL. The old
# loader-only state is kept as a superseded note with its live reproduction.
#
# Re-verified 2026-07-30 (sprint-65, STORY-191 fix round) by the orchestrator, and the Facts were
# REWRITTEN rather than re-stamped -- three of them had become FALSE:
#   1. "no demo loop has been started by any story to date" -- falsified by STORY-182 in sprint 64
#      and never corrected (the sprint-64 follow-up STORY-189 filed it; this closes it).
#   2. "this engine emits UP and absence, nothing else" -- falsified by STORY-177's provisional
#      mapping. The old state is kept as an explicit SUPERSEDED note because its reasoning still
#      governs how far these codes may be trusted (they remain ASSUMPTIONS).
#   3. "the five UP-and-absence scenarios" -- there are now nine.
# code_refs GAINED the whole tools/demo_loop_gate/ package (8 modules). Its absence was a real
# blind spot, not a formality: staleness is `git diff verified_sha..HEAD -- <code_refs>`, so
# changes to the very harness this article describes could NEVER mark it stale. Also added the
# four new scenario files and the two backend modules the failure path now depends on.
# Re-stamped 2026-07-30 (sprint-65 quality-review round). Facts re-read; the scenario
# vocabulary is now validated at LOAD time with file/signal/cycle context, and the closed
# outcome set is unchanged. No Fact here became false.
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
STORY-182 (sprint 64)**, which RAN IT: 13 components / 41 signals / 4 locations ingested by the
real unmodified `python -m src.composition.run`. **Sprint 65 then closed the failure half** —
STORY-190 (a bad row is quarantined instead of stalling its signal), STORY-177 (a provisional
failure mapping) and STORY-191 (a real `DOWN`, a real `DEGRADED`, a quarantined poison row and a
real recovery PUBLISH, all driven through the same harness and asserted from persisted state).

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
- `parse_query` (`query_grammar.py:71`) recognizes exactly the two DQL shapes production emits: the
  ingest grammar from `build_dql_query` (`adapters/inbound/dynatrace/query.py:83-125`) and the
  vendor-health `summarize count()` probe from `build_vendor_health_dql`
  (`adapters/inbound/dynatrace/query.py:139-158`; relocated there from
  `composition/vendor_health.py:40-53` at STORY-204, ZR-8 finding 2 — query-construction logic
  lives in exactly one adapter).
- Anything else raises `UnrecognizedDqlQueryError` (`query_grammar.py:36`, raised at `:80` and
  `:88`), which `server.py:99-101` turns into an HTTP **400**. This fail-loud path is not
  decoration: `grail_executor.py:97` returns `[]` on an unexpected envelope, so a regression from
  loud to silent would be indistinguishable from "no data" — the exact shape of the STORY-051
  ingest stall. STORY-176 adds a third grammar, which is what this guard is for.
- **The watermark bound is parsed by the REAL production parser** — `parse_watermark_bound`
  delegates to `_assembly.py::parse_ns_timestamp` (`query_grammar.py:28,68`), imported, never
  reimplemented. Bound and row timestamps are therefore compared as `datetime`s, never as strings:
  a 6-digit-fraction bound sorts lexicographically BEFORE a 9-digit row at the same instant, which
  reproduces the STORY-051 stall inside the engine if this is skipped (`query_grammar.py:56-66`).
- Ingest filtering is three-clause — monitor id AND `event.type` AND the watermark lower bound —
  and results are sorted by parsed timestamp (`store.py:61-73`).
- The vendor-health answer is `[{"count()": count}]` (`store.py:85`), counted inside
  `request_instant - VENDOR_HEALTH_WINDOW` (`store.py:75-84`). `VENDOR_HEALTH_WINDOW` is a
  2-hour literal (`store.py:24`) that mirrors `HEALTH_CHECK_WINDOW`
  (`adapters/inbound/dynatrace/query.py:136`; relocated there from
  `composition/vendor_health.py:37` at STORY-204, made public in the STORY-204 fix round — the
  only private-**name** import across a module AND zone boundary in `backend/src`, under a
  leading-underscore-*symbol* reading; `composition/app.py:224` imports the private *package*
  `src.api.v1._shared.errors` across a zone boundary too, which is a private PACKAGE, not a
  private name) but is deliberately NOT
  imported — the window is part of the wire contract the engine answers, not an implementation
  detail borrowed from the adapter that builds the query. **STORY-180 AC2** closed the divergence
  risk this created: `test_vendor_health_window_matches_the_composition_health_check_window`
  (`test_vendor_health_query.py`) asserts the two are numerically equal (parsing
  `HEALTH_CHECK_WINDOW`'s `"<N>h"` shape in the TEST only) and fails if a future change to the
  adapter constant is not mirrored here — the route decided at planning was this equality
  test, not teaching the engine to parse the DQL `from:` clause (`parse_query` never reads it at
  all: no `from:` regex exists, `query_grammar.py:30-33`, and `VendorHealthQuery` has no window
  field). `request_instant` defaults to the wall clock, but ONLY the vendor-health branch reads it
  — an ingest query never touches it at all (`store.py::handle_query`; pinned by
  `test_ingest_query_never_reads_the_wall_clock`, `test_query_grammar.py`, STORY-180 AC5/minor 7,
  which made the clock read fresh-per-vendor-health-call-only rather than unconditional on every
  call).

### The wire protocol (`server.py`)
- Serves the **async** branch of what `make_grail_executor` speaks
  (`grail_executor.py:43-97`): POST `…/query:execute` → `202` + a JSON body carrying
  `requestToken` (`server.py:103-105`), then GET `…/query:poll?request-token=…` →
  `{"state": "SUCCEEDED", "records": …}` on **every** poll inside the retention window
  (`server.py:207`; STORY-183 — it was first-poll-only until then). The async branch is
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
- `_DemoHTTPServer.results` (`server.py:97`) is a per-token result cache bounded by **RETENTION**:
  each entry stores its insertion instant alongside the records, and `_evict_expired`
  (`server.py:100-118`) removes anything older than the instance's `retention` — swept on **both**
  `do_POST` and `do_GET`, so an entry is collected even if nothing ever polls again. Default
  `_DEFAULT_RETENTION = 5 minutes`, declared once with its reason at the literal
  (`server.py:50-60`, the literal at `:60`). Pinned by `test_entry_never_polled_is_evicted_once_past_retention`
  (`test_server.py:150`) and, for the bound itself,
  `test_cache_length_stays_bounded_when_nothing_is_polled` (`test_server.py:191`) — which advances an
  injected clock past retention between executes and asserts the length stays at 1, so the assertion
  cannot pass while the leak is intact.
- **A repeat poll of the same `request-token` inside the retention window is SERVED, not 404'd**
  (`server.py:200-207`) — `do_GET` reads, it does not pop. This is vendor fidelity: real Grail
  retains a completed result and re-serves it within a window. Pinned by
  `test_repeat_poll_inside_retention_returns_the_same_records_twice` (`test_server.py:91`).
  A poll of a token already evicted by retention still returns the unchanged
  `404 {"error": "unknown request token"}` (`test_poll_after_retention_eviction_still_404s`,
  `test_server.py:172`).
- `retention` and `clock` are **genuinely per-instance** constructor arguments, assigned directly and
  never copied from the module constant at construction (`server.py:88-98`, passed through from
  `DemoEngineServer`, `server.py:230-239`). A caller reads the EFFECTIVE value back via
  `server._httpd.retention`. This shape is load-bearing for proofs: a server that copied a module
  constant would not observe a monkeypatch of it, so a two-sided proof varying retention would run
  **identically on both sides** — the false-pass class that cost sprint 63 two proofs.
- The eviction sweep holds `_results_lock` across the whole read-then-delete (`server.py:111-118`).
  `_DemoHTTPServer` extends `ThreadingHTTPServer` over a bare dict, so an unguarded sweep racing a
  handler thread's insert would raise `RuntimeError: dictionary changed size during iteration` —
  reachable once STORY-182 drives 41 concurrent signal loops through this server (measured: all 41
  fire their first cycle within ~2s).
- **Auth precedes any cache touch** (`server.py:188` `_require_auth()` returns early, before the
  clock read and eviction at `:198-199` and the cache read at `:200-201`), so an unauthenticated poll can never affect cache state.
  Pinned by `test_unauthenticated_poll_does_not_touch_the_cache` (`test_server.py:216`).
- Superseded, kept so it is not re-litigated: STORY-180 AC4/minor 5 bounded this cache by
  **consume-on-first-poll** (`results.pop`), pinned by
  `test_results_cache_is_evicted_after_being_polled`. That bound was **partial** — a token executed
  but never successfully polled (a failed poll leg, `grail_executor.py:111`; the pull loop swallowing
  a faulted cycle, `pull_loop.py:200-207`) leaked for the process lifetime — and it narrowed the wire
  protocol by 404-ing a repeat poll. STORY-183 replaced both with retention, which is strictly better
  on both axes; that test was removed as a **contract correction, not a weakening** (its own docstring
  attributed it to STORY-180, not to STORY-148's wire contract).

### Scope honesty: what this engine can emit (REWRITTEN — sprint 65)

**This section previously read "this engine emits UP and absence, nothing else". That is no longer
true.** STORY-177 (sprint 65) landed a provisional failure mapping in `backend/src/`, and STORY-191
drove it through a real loop run. The superseded state is kept below because the *reasoning* still
governs how much these codes may be trusted.

- `map_synthetic_status` (`health_mapping.py`) now resolves in three steps: the healthy OR-rule
  (`code == "0"` or `message == "HEALTHY"` → `Health.UP`) **first and unchanged**; then an exact
  `(code, message)` tuple lookup in `PROVISIONAL_STATUS_MAPPING`; then a raise. Every provisional hit
  logs at WARNING naming the code, the message and its unverified status.
- The mapping holds exactly two entries — `("1", "UNHEALTHY") → Health.DOWN` and
  `("2", "DEGRADED") → Health.DEGRADED`. **Both remain ASSUMPTIONS.** A real Dynatrace failure code
  has still never been observed; the trial expired 2026-07-28 before one could be captured. STORY-154
  replaces the *contents* of that one constant when a tenant exists.
- The codes live in `health_mapping.py` and are **derived** in
  `tools/demo_engine/assumed_failure_codes.py`, never redeclared — `tools/` may import `src.*`, never
  the reverse. `scenario.py`'s outcome vocabulary is likewise derived, and is deliberately **closed**
  (`up` / `down` / `degraded` / `poison`) with no free-form `"code:message"` escape hatch, so a
  fixture can never introduce a vendor literal that reads as a contract.
- **SUPERSEDED, kept for its reasoning (STORY-148, sprint 62–63):** the engine could emit `UP` and
  absence only, because `map_synthetic_status` raised on every non-healthy value and
  `dispatch.py:80`'s bare comprehension then discarded the whole batch. STORY-148's reality gate
  executed exactly that: the assumed row raised `UnknownVendorStatusError` and took the batch with
  it — the failure path proven **rejected**, the opposite of "tested". Consequently no demo scenario
  could drive a `DOWN` or `DEGRADED` proposal, which is why PO decision D-A re-pointed STORY-149's
  reality gate away from the demo engine. Both halves of that are now closed: STORY-190 made a bad
  row survivable (quarantined, batch preserved, watermark advances) and STORY-177 added the mapping.
- **What "the failure path is tested" means here, precisely:** tested against an ASSUMED code,
  through the real unmodified ingest path, in a real loop run — never against anything Dynatrace has
  confirmed.
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
  `interval_seconds` — the last two now **delegated to `SignalScenario.__post_init__`** and re-raised
  with the file/key prefix (STORY-184; see the past-anchoring bullet). Every message names both the
  file and the signal key, never a bare stdlib
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
  until wall-clock time caught up. **The "at or before `end_time`" guarantee is now UNCONDITIONAL,
  because the invariant lives on the TYPE** (STORY-184, sprint 64): `SignalScenario.__post_init__`
  (`scenario.py:56-80`) rejects any `interval_seconds` that is not a positive `int`, so **no
  construction path — direct or via the loader — can produce a scenario that walks the ladder
  forward.** It uses `type(x) is not int`, not `isinstance`, deliberately: `bool` is an `int`
  subclass, so `isinstance(True, int)` is `True` and would let `interval_seconds: true` through.
  `load_scenario_file` now catches the type's bare `ValueError` and re-raises it as
  `InvalidScenarioError` prefixed with the file path and signal key (`scenario.py:159-171`) — context
  the type itself cannot have.
  The remaining caveat is caller-side and is stated in the function's own docstring: the guarantee is
  "at or before `end_time`", **not** "at or before now" — a caller passing a future `end_time` still
  gets a ladder anchored to it. Production passes `clock.now()`, which is what makes "never in the
  future" hold in practice.
  Superseded, kept so it is not re-litigated: sprint-63's fix round (quality finding M2) put this
  check in `load_scenario_file` ONLY, which left direct construction unguarded — reproduced live at
  that commit, `SignalScenario(interval_seconds=-30, cycles=[['L1'],['L1']])` expanded to
  `12:00:30, 12:00:00` for `end_time=12:00:00`, i.e. a row in the future, landing in
  `ingest_service.py`'s silent `FUTURE_TOLERANCE` quarantine whose rejected count `run.py` discards.
  That gap is what STORY-184 closed. Pinned by
  `test_scenario.py::test_signal_scenario_rejects_non_positive_interval_seconds` (`-30` and `0`),
  `::test_signal_scenario_rejects_non_int_interval_seconds` (`"30"`, `30.5`, `True`),
  `::test_signal_scenario_accepts_a_valid_positive_interval_seconds` (the valid shape too),
  `::test_signal_scenario_negative_interval_can_no_longer_expand_into_the_future` (the exact
  pre-fix construction, now raising), plus
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
- **Scenario coverage (updated sprint 65).** `config/demo/scenarios/` now holds NINE files. The
  original five are `UP`-and-absence only: a clean fleet
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
- STORY-176 part 2a adds tests in `backend/tests/demo_engine/` (now nine files, **59 total** after
  the sprint-63 fix round below): `test_scenario.py` (**24** — AC1 row-count-per-cycle, AC2's
  format/monotonicity/interval-spacing/window/backfill/not-in-future, the scenario-file load path
  including its malformed-input AND type/sign-validation behaviour) and `test_scenario_coverage.py`
  (**6** — one per AC5 case plus the scenario<->fleet coherence check). A further **10 tests** in
  `backend/tests/test_demo_fleet_config.py` (composition zone, not `demo_engine/` proper — it tests
  `Config`/`create_app` against `config/demo/`, not the engine package) pin the publish guard and the
  fleet's scale/multi-file survival; ONE of those (`test_create_app_with_live_config_dir_...`) still
  needs `dynamo_local` (a real `create_app()` call wires real Dynamo-backed repos, though no I/O
  actually occurs before assertion — `boto3.resource(...).Table(...)` is lazy); the OTHER
  (`test_create_app_with_demo_config_dir_...`, the CONFIG_DIR-governs-`create_app` half of the
  publish-safety proof) was un-gated from Docker in the sprint-63 fix round (quality finding S2) —
  it now sets a literal, deliberately-unreachable `DYNAMO_ENDPOINT_URL` instead of requesting
  `dynamo_local`, so it can never silently SKIP on a Docker-less machine; proven by running it with
  `docker` removed from `PATH` and no `DYNAMO_ENDPOINT_URL` set. Grand total: **614 tests**
  repo-wide (572 at the sprint-63 branch point `e107811`; STORY-180 brought it to 574 first; the
  story's initial +30 brought it to 604; the sprint-63 fix round's +10 — 9 in `test_scenario.py`, 1
  in `test_scenario_coverage.py` — brings it to 614).

## Inference (not verified — reasoning, not fact)

- The engine's fidelity claim is bounded by what the captured sample contains. It proves the fields
  the ingest path READS are right in shape, type and scale; it cannot prove Grail never sends
  something else, and it says nothing about failure-row shape (see the scope-honesty section).
- STORY-180 closed the two items this section used to flag as future risk for STORY-176's
  long-running engine: the token cache gained a bound and the vendor-health window gained an equality
  guard against silent divergence (Facts, above). Neither was ever a correctness bug in the STORY-148
  test-scoped lifetime. **STORY-183 (sprint 64) then replaced STORY-180's consume-on-first-poll bound
  with a RETENTION bound**, because consume-on-read left the abandoned-token path unbounded and cost
  repeat-poll fidelity — see the cache Facts above for the current behaviour and the superseded note.

## History

- sprint-68 (STORY-204 third fix round): the second fix round's sweep was still incomplete —
  fixed four kinds of stale/overstated citation this round, all found by re-deriving every
  `query.py` citation in the repo against the real file rather than trusting a named list: (1) the
  `query.py:133,152` citation, which round two never touched at all in two of this article's own
  `code_refs` (`tools/demo_loop_gate/backfill_reality_gate.py:9`,
  `tools/demo_loop_gate/fleet_coverage.py:25`) plus two non-`code_ref` siblings — HEAD-derived to
  `:136,155`; (2) a DIFFERENT stale pattern round two's fix never addressed: the whole-FUNCTION
  citation for `build_vendor_health_dql` (`query.py:136-155`, its span BEFORE the fix round's
  3-line "PUBLIC" comment insertion) needed the same +3 shift, to `:139-158` — found here (the
  two-grammars section, above) and in this article's own `code_refs`
  `tools/demo_engine/query_grammar.py:11` and
  `backend/tests/demo_engine/test_vendor_health_query.py:4`; (3)
  `backend/tests/demo_engine/test_watermark_precision.py:3` (a `code_ref`) cited `query.py:96`
  (inside an unrelated docstring paragraph) for `since.isoformat().replace("+00:00", "Z")`, which
  actually lives at `query.py:121` — pre-existing, unrelated to this story's line-shifting edit,
  caught only by the exhaustive sweep; (4) `tools/demo_engine/rows.py:22` (also a `code_ref`) had a
  third, unrelated pre-existing error of the same kind: it cited `query.py:87` (a blank docstring
  line) for the `http_monitor_execution` event-type literal, which is actually at `query.py:112`.
  Also narrowed the one remaining overstated "only private-name import" occurrence this article's
  own second-fix-round entry had declined as out of scope: `test_vendor_health_query.py`'s
  docstring, same wording as the wiki fix below. Citation/wording only, no behaviour change.
  verified_sha -> c2fd3d2 (this article's content commit is the direct child of that sha).
- sprint-68 (STORY-204): `build_vendor_health_query` relocated from `composition/vendor_health.py`
  into `adapters/inbound/dynatrace/query.py` as `build_vendor_health_dql` (ZR-8 finding 2 — see
  [[zone-rules]]), sharing a new `_reject_dql_breaking_native_id` validation helper with
  `build_dql_query`. This engine's own behaviour and every Fact about IT are unchanged — it still
  parses the identical DQL string shape the relocated builder emits (proven by the existing,
  unmodified assertions in `test_vendor_health_query.py` and `test_server.py`, only their imports
  repointed) — but the relocation moved several cited `file:line`s this article pins: the two query
  grammars section (`query_grammar.py`'s citations for both grammars, `store.py:18-24`'s
  `VENDOR_HEALTH_WINDOW` mirror comment, whose own line moved 22→24 because its comment grew by two
  lines), and `test_scenario.py`'s trailing-window comment. `tools/demo_loop_gate/fleet_coverage.py`
  and `backfill_reality_gate.py` (both `code_refs`) had their own trailing-2h-window citations
  repointed the same way; `composition/vendor_health.py`'s own body shifted (its docstring grew),
  so the "healthy branch logs one INFO line" / "contradicts its docstring" citations moved too
  (`:126-133`→`:124-132`, `:86`→`:77`). All repointed to the new file, verified against the real
  code, not guessed. verified_sha -> c815ebe (this article's content commit is the direct child of
  that sha; see the self-reference note elsewhere in this History for why the child's own sha
  cannot be recorded here).
- sprint-68 (STORY-204 fix round): `_HEALTH_CHECK_WINDOW` made public
  (`HEALTH_CHECK_WINDOW`) at its one declaration (`query.py`) — the only private-**name**
  import across a module AND zone boundary in `backend/src`, under a
  leading-underscore-*symbol* reading. Repointed the two Facts
  above that named the old private form (the `VENDOR_HEALTH_WINDOW` mirror comment,
  the equality test's docstring/parse citation) and `tools/demo_engine/store.py`'s own
  comment (line count unchanged, so `store.py:24`'s `VENDOR_HEALTH_WINDOW` line — and
  the ZR-3 ledger's `(store.py, 24)` key — is unaffected). This article's own History
  entries above stay in their original historical wording (they narrate what STORY-204
  did at the time, which used the private name). verified_sha -> bfa5f77.
- sprint-68 (STORY-204 second fix round): fixed a stale line ref
  (`adapters/inbound/dynatrace/query.py:133` -> `:136`, moved by bfa5f77's added comment
  lines) in the `VENDOR_HEALTH_WINDOW`-mirror Fact above, and narrowed both "the only
  private-name import" occurrences in this article to the leading-underscore-*symbol*
  reading they actually hold under — `composition/app.py:224` imports the private
  *package* `src.api.v1._shared.errors` across the same kind of zone boundary, which is
  a private PACKAGE, not a private name. `tools/demo_engine/store.py`'s own comment (a
  `code_ref`) got the same `query.py:133` -> `:136` line-ref fix, and
  `backend/tests/demo_engine/test_scenario.py`'s (also a `code_ref`) `AC2(e)` docstring
  had its stale `_HEALTH_CHECK_WINDOW` reference corrected to the current public
  `HEALTH_CHECK_WINDOW` — both citation/wording only, no behaviour change, so no other
  Fact in this article is affected. verified_sha -> 482d279.
- sprint-68 (STORY-205): RE-VERIFIED, no content change. `tools/demo_loop_gate/
  failure_path_reality_gate.py` (a `code_ref`) had its `_component_repo` docstring's
  key-schema citation repointed from `dynamo_component_repository.py:36-41` (already
  stale — STORY-199's pagination loops had displaced it) to
  `adapters/persistence/topology_keys.py::component_item_key`, the ZR-8 Finding 1 fix
  (see [[zone-rules]]). The gate's behaviour, code path and every Fact in this article
  are unchanged — only a comment naming where the schema now lives. verified_sha ->
  96f9048.
- sprint-67 (STORY-202 fix round): **the AC6 empirical claim below was actually EXECUTED
  in this fix round, with captured output** — the orchestrator had reverted this
  article's `verified_sha` stamp because no evidence existed that the prior claim had
  run; that gap is now closed. `tools/demo_loop_gate/harness.py` and
  `tools/demo_loop_gate/env_matrix.py` changed, but import DIFFERENT SUBSETS of the
  seven names, not both all seven — corrected here to match the correction made in
  [[zone-rules]] ZR-3's own Facts (an earlier draft of both articles said "both
  files import all seven"): `env_matrix.py` imports all seven (`CONFIG_DIR_VAR`,
  `AWS_REGION_VAR`, `DYNAMO_OBSERVATIONS_TABLE_VAR`, `DYNAMO_CONTROL_TABLE_VAR`,
  `DYNAMO_ENDPOINT_URL_VAR`, `STATUSPAGE_PAGE_ID_VAR`, `STATUSPAGE_API_KEY_VAR`, since
  it sets all seven as child-env dict keys); `harness.py` imports only the four it
  actually re-types as a dict key at its six AC8 sites (`CONFIG_DIR_VAR`,
  `DYNAMO_CONTROL_TABLE_VAR`, `DYNAMO_ENDPOINT_URL_VAR`,
  `DYNAMO_OBSERVATIONS_TABLE_VAR`) — it never re-types `AWS_REGION`/
  `STATUSPAGE_PAGE_ID`/`STATUSPAGE_API_KEY` as a literal dict key anywhere. Both
  import from `backend/src/composition/settings.py` instead of re-declaring the
  env-var key NAMES — see [[zone-rules]] ZR-3. The publish guard MECHANISM this
  article documents (`Config.statuspage_mapping()` empty for `config/demo`,
  `build_publisher` falling through to `LoggingPublisher`, `publish_helper.py:211`)
  is behaviour-identical: re-verified empirically (not just reasoned), executed
  directly against the production interfaces —
  `load_config("config/demo").statuspage_mapping()` printed `{}`, and
  `build_publisher(...)` called with real-looking Statuspage credentials
  (`statuspage_page_id="REAL-LOOKING-PAGE-ID"`, `statuspage_api_token=
  "REAL-LOOKING-API-TOKEN"`) present returned a `StatusWritebackPublisher` whose
  `._delegate` printed as `LoggingPublisher` (`isinstance(..., LoggingPublisher)`
  → `True`). `test_create_app_with_demo_config_dir_yields_empty_mapping_and_logging_delegate`
  and the disjointness tests cited above still pass unchanged. Also confirmed via
  the two-sided AC4 mutation proof — a KEY-NAME mismatch (which env-var NAME is
  used as the `os.environ`/child-env dict key), never a stored config VALUE
  mismatch: at the pre-STORY-202 commit `6f872c3`, `CONFIG_DIR_VAR` did not yet
  exist as a constant — the literal `"CONFIG_DIR"` lived directly inside
  `load_settings()`'s function body, and THAT literal is what was renamed there
  (to `"CONFIG_DIR_X"`), leaving `env_matrix.py`'s own, separately-hardcoded
  `"CONFIG_DIR"` literal untouched; at HEAD, the same rename is applied once, to
  the now-existing `CONFIG_DIR_VAR` constant's value, and both `env_matrix.py`
  and `settings.py` follow it because they read the one shared symbol. Result:
  pre-fix, the harness and `settings.py` DISAGREE on the injected key name — the
  harness's fixed `config/demo` value silently fails to reach `load_settings()`,
  which falls back to the `config/apps` default (the live-page-selecting
  default) — while at HEAD, after the identical mutation, they agree.
  verified_sha -> `3c0cdeb`.
- sprint-63 (STORY-176, part 2a): the scenario player (`scenario.py`), the demo fleet
  (`config/demo/`, 13 components / 41 signals / 4 locations across three distinct-`app.id` files),
  the scenarios (`config/demo/scenarios/`), and the config-only publish guard
  (proven in-process, both sides — an empty demo mapping selecting `LoggingPublisher` AND the live
  `config/apps` mapping selecting a real `StatuspagePublisher` TYPE, plus a proven-catchable
  component-id disjointness check) all land. AC6/AC7 (the actual loop run) are explicitly OUT of
  this story — split to STORY-182 (sprint 64) at sprint-63 planning after a re-estimate put the
  combined story at 6 points. Zero files under `backend/src/` changed (AC8, mechanically verified:
  `git diff --name-only 1aadf95..HEAD -- backend/src/` is empty). Net test count: 574 → 604 (+30).
  DoD gate 5/5 backend (no frontend files touched). verified_sha -> d530238.
- sprint-63 (STORY-176, fix round after quality FIX_REQUIRED): C1 (critical) — the per-monitor
  interval math in `expand_scenario` was pinned by nothing (a mutant hardcoding 30s passed all 30
  original tests); added a parametrized (30s/45s) test asserting consecutive expanded cycles are
  spaced by exactly `scenario.interval_seconds`, and reworked the staggered-intervals test to assert
  each monitor's own `observed_at` spacing from the ingested rows, not a `bucket_into_cycles` set
  built from the test's own `since`/`interval` args. Both discrimination-proofed against the same
  hardcoded-interval mutant (RED confirmed, then reverted with an empty `git diff`). M1 — corrected
  the false "share no cycle boundary" claim (both Facts, above, and the test docstring): the two
  staggered monitors' LAST cycles land on the same instant (`end_time`), so they share exactly one
  boundary. M2 — `load_scenario_file` now validates field TYPES and `interval_seconds`'s SIGN (a
  null/wrong-type `cycles`, a non-int or non-positive `interval_seconds`), raising a named
  `InvalidScenarioError` with the file and signal key instead of leaking a bare stdlib `TypeError`;
  closes the (previously silently-accepted) negative-`interval_seconds` case that would have emitted
  rows in the future, falsifying AC2f — CLAUDE.md and this file's own "never in the future" claims
  now state that precondition explicitly. M3 — added a test looping every
  `config/demo/scenarios/*.yaml` against `load_config(config/demo)`, asserting each scenario's
  `monitor_id`/`interval_seconds` agree with the fleet's `native_id`/`interval_seconds` for that
  `signal_key` (previously unpinned: `_ingest_scenario` passes `signal_key=` explicitly, so a row's
  own `dt.synthetic.monitor.id` was never read by any test). M4 — deleted the dead
  `event_id_prefix` parameter (no caller, no test). S1 — `_FakeRejectedRepo` now subclasses
  `RejectedObservationRepository`, matching the peer fakes. S2 —
  `test_create_app_with_demo_config_dir_...` (the CONFIG_DIR-governs-`create_app` safety proof) no
  longer needs `dynamo_local`/Docker: it sets a literal, deliberately-unreachable
  `DYNAMO_ENDPOINT_URL` (no I/O occurs before its assertions), proven by running it with `docker`
  removed from `PATH`. Zero files under `backend/src/` changed throughout (mechanically verified per
  finding). Net test count: 604 → 614 (+10: +9 `test_scenario.py`, +1
  `test_scenario_coverage.py`). DoD gate 5/5 backend. verified_sha -> c2c3345.
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
  cache that previously grew one entry per query for the process lifetime — **superseded by
  STORY-183's retention bound in sprint 64; see the cache Facts**. AC5/minors 3,4,7: the
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
