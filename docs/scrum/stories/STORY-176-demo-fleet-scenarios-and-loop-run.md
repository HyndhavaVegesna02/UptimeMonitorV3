---
id: STORY-176
title: Grail-shaped demo engine, part 2a — scenario player, demo fleet, time base, and the publish guard
type: chore
---

## Context

STORY-148 builds the demo engine's **wire contract**: rows indistinguishable from real Grail
rows, both DQL grammars the production code emits, and the async HTTP protocol
`make_grail_executor` speaks. That is a faithful vendor stand-in with nothing to say.

This story gives it something to say, and then runs the real system against it: a scripted
scenario player, a fictional fleet authored in STORY-146's nested config shape, and an
end-to-end run of the **unmodified** `python -m src.composition.run` producing observations,
verdicts and a real open proposal for a fleet that does not exist.

It is a **scenario player, not a random generator**. Random noise will not reliably produce the
cases that matter (anti-flap ladders, breadth, staleness, the two-monitors-fight bug), so
scenarios declare per-signal, per-cycle, per-location outcomes:

```yaml
api-gateway-health:   [up ×5, "down from 2 of 3 locations" ×4, up ×3]
api-gateway-graphql:  [up ×20]
```

## Description

Three pieces on top of STORY-148's engine, plus the run that proves them.

**The player** expands a scenario file into timestamped rows. **The fleet** is a demo config
directory (never `config/apps/`) authored in the nested shape. **The publish guard** is what
makes running any of this safe.

**Why the publish guard is config-only, not a wired stub.** The original draft said "the demo
composition wires a no-op publisher". That is not implementable: `run.py:121-128` builds the
publisher *inside* `build_live_loop` from `secrets`, with no injection point, and this story may
not modify `backend/src/`. The real exposure is also different and larger than the draft
described — `run.py:178` `load_dotenv()` walks up from the source file (not CWD), so the
existing repo-root `.env` supplies `STATUSPAGE_PAGE_ID` and `STATUSPAGE_API_KEY` no matter where
the demo is launched from, and there are **two** composition roots that build a live publisher
from them: `publish_helper.py:211` via `run.py:121`, and the API's approve trigger at
`composition/app.py:160-182` via `load_statuspage_secrets()` — which matters because the reality
gate runs the API.

Both routes pass through the same gate:

```python
# backend/src/composition/publish_helper.py:211
if statuspage_page_id and statuspage_api_token and component_mapping:
```

`component_mapping` comes from `statuspage_mapping()`, which includes only components declaring
a non-None `statuspage_component_id` (`config.py:292-299`). So a demo config that declares
**no** `statuspage_component_id` on any component yields `{}`, and both roots fall through to
`StatusWritebackPublisher(LoggingPublisher(), …)` — with real credentials present. That is the
guard: a property of the config, not a promise about wiring.

## Acceptance Criteria

- [ ] **AC1 (scenario expansion)** — A scenario file declares per-signal, per-cycle,
      per-location outcomes and the player expands it into rows at each monitor's own
      `interval_seconds`. A test asserts a declared sequence produces exactly the expected row
      count per location per cycle.
- [ ] **AC2 (the time base, stated — four constraints)** — Rows are only ingestible if all four
      hold, so each is asserted:
      (a) **Window** — `orchestrate.py:94-98` computes `since = until - (max_threshold + 2) *
      interval`, a rolling **7-cycle** window (with §10 defaults) ending at `clock.now()`. Rows
      outside it never become verdicts, so scenario time is anchored to now, not to a fixed
      epoch.
      (b) **Format** — timestamps are `Z`-suffixed 9-digit-fraction UTC strings, identical in
      **format** to the fixture (`…746000000Z`), because `parse_ns_timestamp` feeds
      `SignalObservation`, which rejects naive or non-UTC datetimes (`signal.py:81-91`) — and a
      raise kills the cycle while `run_periodic` survives it, i.e. silent no-data.
      (c) **Monotonicity** — emitted timestamps advance across successive queries, or the
      watermark bound excludes cycle 2 onward.
      (d) **Interval** — demo monitors use short intervals (≤ 60 s) so a 5-cycle anti-flap
      ladder completes in minutes rather than ~25.
      (e) **Backfill ≥ 2 hours** — the engine serves history relative to each *request* instant,
      covering at least the last 2 hours, not history beginning at engine start.
      `check_vendor_id_health` runs at `run.py:196` **before any loop is built**, querying
      `from:now()-2h` per signal, and WARNs when the count is 0 (`vendor_health.py:113-124`). An
      engine that starts emitting at t₀ returns 0 for every one of the ≥40 signals at that
      moment, failing AC6's "no dead monitor ids" — which is the observable proof STORY-148 AC5
      exists to produce.

      (f) **NOT in the future by more than 5 minutes.** `ingest_service.py:37` sets
      `FUTURE_TOLERANCE = timedelta(minutes=5)` and `:119-125` **quarantines** any observation with
      `observed_at > now + 5min` into the rejected repository. `run.py` passes no `on_cycle`, so the
      `IngestResult`'s rejected count is **discarded — nothing logs it.** This is the failure a
      scenario player is most likely to hit and it is entirely silent. Added 2026-07-29 by
      `yt-plan-verifier`; it also means the note below ("only three" silent failures) undercounts —
      there are **four**.

      **The timeline direction is PAST-ANCHORED (decided at planning, 2026-07-29).** The player
      expands a scenario **backwards from `clock.now()`**, not forwards from t₀. Both readings
      satisfied AC1 + AC2(a) as originally written, and they are different implementations with
      different costs: forward playback quarantines every cycle beyond t₀+5min under (f) until
      wall-clock catches up, and the run would have to last `cycles × interval`. Past-anchored means
      the whole ladder is present in the first query.

      Note on diagnosing (a)–(d) during implementation: violations of (b) in particular are
      **logged, not silent** — `pull_loop.py:200-207` catches and `logger.exception`s at ERROR
      with a full traceback. The loop's ERROR log is the fastest route to a timestamp, mapping, or
      malformed-row problem. Genuinely silent failures are only three: `grail_executor.py:97`'s
      `return []`, `_extract_count` → 0, and a window/watermark miss.
- [ ] **AC3 (publish safety — non-negotiable; config-only AND `CONFIG_DIR` on BOTH processes)** —
      No demo run can POST to a real Statuspage, **even with real credentials in the repo-root
      `.env`**. Two things are required together, and the second was missed in the first draft of
      this AC:

      **(a) The demo config declares no `statuspage_component_id` on any component**, so
      `statuspage_mapping() == {}` and `publish_helper.py:211` falls through to
      `StatusWritebackPublisher(LoggingPublisher(), …)`. Verified: that line is the **only**
      construction of `StatuspagePublisher`/`make_statuspage_executor` anywhere in `backend/src/`;
      `StatusWritebackPublisher.publish` (`publish_helper.py:172-180`) makes no external call
      (a DynamoDB `set_status`, then the delegate); `app.py:184-196`'s other branches reach only
      `LoggingPublisher`; and no approve/reject endpoint builds its own publisher —
      `ApprovalService` takes the injected one (`app.py:201-203`).

      **(b) `CONFIG_DIR` must point at the demo config on the API process too, not just the
      loop.** The API is a **separate process that loads its own config**:
      `app.py:171-175` takes the mapping from `app.state.seed_config.statuspage_mapping()`,
      `app.py:137-138` resolves `config_dir or settings.config_dir`, and `settings.py:32`
      defaults `CONFIG_DIR` to **`config/apps`** — whose `httpcheck.yaml:6` declares
      `statuspage_component_id: xdnywbx77npw`. With `asgi.py:36`'s `load_dotenv()` supplying real
      credentials, an API started per the documented recipe (CLAUDE.md "Run the app locally"
      step 4, no `CONFIG_DIR`) while the loop runs on demo config wires a **real
      `StatuspagePublisher`** on the approve trigger — and its lifespan seed additionally writes
      the real `http-check` component into the demo table. Guard (a) alone does not close this,
      because (a) is a property of the *demo* config and the API never reads it.

      **(c) Demo component ids MUST be disjoint from `config/apps` component ids.** Added
      2026-07-29 after `yt-plan-verifier` found a bypass that (a) and (b) together do not close:
      `StatuspagePublisher.publish` keys on the **canonical component id**
      (`adapters/outbound/statuspage/__init__.py:41-46`). A demo component reusing a live id (e.g.
      `http-check`, `config/apps/httpcheck.yaml:8`) on an API process running the DEFAULT
      `CONFIG_DIR` — which is exactly what CLAUDE.md "Run the app locally" step 4 does, passing no
      `CONFIG_DIR` — resolves to `{http-check: xdnywbx77npw}` and PATCHes the **real** page on
      approve. Guard (b) is a human-set env var; this check is mechanical and cannot be forgotten.
      The one **automatic** layer, which neither the original AC nor the plan named, is
      `UnmappedComponentIdError` (`statuspage/__init__.py:43`) swallowed by `BestEffortPublisher`
      (`publish_helper.py:59-66`) — it saves a NON-colliding id and nothing else. That is why (c)
      exists.

      **Four tests / checks:** `statuspage_mapping() == {}` for the loaded demo config;
      `build_publisher` with an empty mapping and non-empty credentials returns a chain whose
      delegate is a `LoggingPublisher`; `set(demo component ids) & set(load_config("config/apps")
      component ids) == set()`; and the API's runtime mapping is `{}` — asserted **in-process**
      (`CONFIG_DIR=<demo> python -c "from src.composition.app import create_app; ..."` then
      `app.state.seed_config.statuspage_mapping() == {}` and the delegate's type), because
      `yt-plan-verifier` enumerated all 14 v1 routes and **none** exposes the mapping, the
      publisher, or the loaded config — so "asserted against the live process over HTTP" was
      unsatisfiable without a `backend/src` change that AC8 forbids. `asgi.py` calls `create_app()`
      with no `config_dir`, so `CONFIG_DIR` governs it (`settings.py:32`) and the in-process
      assertion exercises the same resolution path the server does. The demo README and the
      recipe state `CONFIG_DIR` as required on **both** processes and name both routes.
      **No demo loop is started before this AC passes** — `decide` publishes recoveries with no
      human gate (`core/services/decide.py:122-126`), so fake recoveries would otherwise reach
      the live public page.
- [ ] **AC4 (the demo fleet)** — A demo config directory (never `config/apps/`) declaring
      **≥12 components, ≥40 signals, ≥4 locations**, authored in STORY-146's nested shape with
      declared `locations:` and a `freshness:` block. Location aliases are short non-cloud-provider
      strings per STORY-146. Fabricated `SYNTHETIC_LOCATION-*` ids are acceptable **here** —
      this is demo config, explicitly not live config.
- [ ] **AC5 (scenario coverage — `UP` and absence only; see the scope note)** — Scenarios cover
      every case reachable without a failure-code mapping:
      (a) a clean fleet across all locations;
      (b) a **fully dark location** — a declared location that stops reporting entirely.
      **Reworded 2026-07-29 (PO decision).** It does NOT exercise "the `expected_locations` gap and
      the completeness denominator": `expected_locations`, `locations_for`, `freshness_for`,
      `stale_after_cycles` and `reentry_cycles` have **zero consumers** anywhere under
      `backend/src` outside `composition/config.py` (verified by grep; `config.py:261` says so
      itself — "STORY-151/152 consume this"), and `availability.py:265` computes
      `completeness_denominator = expected_cycles * distinct_locations` where `distinct_locations`
      is the count of locations **observed** (`:74`) — so a dark location shrinks numerator and
      denominator together and completeness barely moves. What it DOES produce, and what the test
      asserts: a lower `distinct_locations` on `/availability`, and `collapse` seeing `{UP}` from
      the surviving locations (`pipeline.py:40-97` has no location-count awareness at all). The
      scenario's real value is as a **fixture the consumer stories will need**;
      (c) a **fully dark monitor** — every location silent. Likewise reworded: no freshness path is
      consulted because none is wired. What it produces is an empty window → `streak` returns
      `None` → `orchestrate_signal` NOOPs (`orchestrate.py:113-121`), asserted as such;
      (d) **staggered intervals** — monitors at different `interval_seconds` on one component, so
      cycle boundaries do not line up;
      (e) a **late-returning monitor** — dark, then reporting again. Reworded: `reentry_cycles`
      has no consumer, so what this asserts is that **ingest resumes** after a gap (rows land, the
      watermark advances) — not that any re-entry policy ran.
      **Deliberately NOT in this story:** any scenario requiring a `DOWN` or `DEGRADED`
      observation (a ladder-crossing degradation, a minority-location failure, two monitors
      disagreeing). Those are unreachable through the real ingest path — see the scope note below
      — and arrive with STORY-177.
- [ ] ~~**AC6 (real loop, real fleet)**~~ — **MOVED to STORY-182** (part 2b) at sprint-63
      planning. The run, its evidence, and the `check_vendor_id_health` dead-id check are that
      story's AC3/AC4. This story ships the player, the fleet and the guard that make the run
      *safe to attempt*; it deliberately does not run it.
- [ ] ~~**AC7 (no proposal evidence is claimed)**~~ — **MOVED to STORY-182** (its AC5), together
      with the sharper reason: `publish` is never called at all under UP-only scope, so a quiet
      publish log is vacuous evidence.
- [ ] **AC8 (production untouched)** — `git diff` touches only `tools/`, **`config/demo/`** (the
      demo config directory — named here so the check is a concrete allowlist, not a description),
      `docs/`, `CLAUDE.md`, and tests under `backend/tests/`. No file under `backend/src/` is
      modified, verified mechanically from the commit range.
      **Multi-file trap:** a ≥12-component fleet will span several YAML files, and
      `config.py:585-587` silently discards a duplicate `app.id`'s `locations`/`freshness`. Each
      demo YAML declares a DISTINCT `app.id`, with a test asserting every declared location and
      freshness block survives loading.
- [ ] **AC9** — All **eight** DoD gate commands exit 0 (five backend + three frontend).

## Scope note — why there are no failure scenarios (PO decision, 2026-07-28)

A demo engine speaking HTTP **cannot** produce a `DOWN` or `DEGRADED` observation, because the
failure path does not exist in the ingest code yet:

- `map_synthetic_status` maps only `"0"`/`"HEALTHY"` → `UP` and **raises**
  `UnknownVendorStatusError` on everything else (`health_mapping.py:65-70`). Its docstring states
  the omission is deliberate: *"Inventing failure codes here would silently mis-map (or mask) the
  real failure value during that verification, so it is deliberately NOT done."*
- `dispatch.py:80` normalizes rows in a bare list comprehension, so a single failure-coded row
  raises and **the whole batch for that signal in that cycle is lost**, healthy rows included.
- The codebase's own wiring test proves monkeypatching is the only route
  (`backend/tests/test_pull_loop.py:139-145`) — unavailable to a process talking over a socket.

Found by the second `yt-plan-verifier` pass. An earlier draft of this story framed emitted failure
codes as "assumptions", which was wrong: an assumed code is not an *unverified* row, it is an
*unusable* one. The PO chose to scope the demo to `UP` + absence rather than add a provisional
mapping to `backend/src/` as a demo prerequisite — so the provisional mapping is now STORY-177,
a first-class story with its own review, and the failure-path scenarios land with it.

## Open Questions

None.

## History

- 2026-07-28: created by splitting STORY-148 after `yt-plan-verifier` assessed the original
  single 5-pt story at 7–8 pts. This is part 2 (scenario player, demo fleet, loop run);
  STORY-148 keeps part 1 (the wire contract). Three verifier findings are folded in here
  specifically: (1) the publish guard as originally written was **unsatisfiable** — no injection
  point in `run.py:121-128` under a no-`backend/src`-changes constraint — and the actual exposure
  runs through `load_dotenv()` picking up the existing `.env` plus a second, unmentioned route
  via the API's approve trigger; it is now a config-only guard that holds even with real
  credentials present; (2) the scenario time base was unspecified, and four separate constraints
  (7-cycle window, timestamp format, monotonicity, short intervals) each cause no-data
  if violated; (3) the "real open proposal" evidence was confounded by the known STORY-151
  sibling-OBSOLETE path and was pinned to a single-monitor component.
- 2026-07-28: **second verifier pass + PO decision — rescoped to `UP` + absence, and DEFERRED to
  sprint 63.** The failure-path scenarios were unreachable (see the Scope note): AC5 lost its
  three failure cases and gained three absence cases instead (dark monitor, staggered intervals,
  late return — each exercising freshness, which the original set never touched); AC7 inverted
  from "prove a proposal opens" to "prove none can, and say so", which also retires the STORY-151
  confound; the provisional failure mapping became STORY-177. AC3 grew the
  `CONFIG_DIR`-on-both-processes requirement after the verifier found the API reaches a live
  `StatuspagePublisher` through its own config; AC2 gained the ≥2 h backfill constraint.
  Deferred to sprint 63 per the PO's pacing directive: the honest re-estimate put sprint 62 at
  12–13 pts against a ~9–11 baseline, and this story opens 63 where its fleet-scale data also
  feeds the frontend work.
- 2026-07-29: **SPLIT at sprint-63 planning, and four AC defects fixed pre-lock.** `yt-plan-verifier`
  re-estimated the combined story at 6 pts (STORY-148 delivered the whole wire contract for 3), and
  the PO chose to split: this is now **part 2a** (player, fleet, time base, publish guard) at 3 pts;
  **STORY-182** takes the run and its two-sided gate (AC6/AC7 moved there). The four fixes matter
  more than the split:
  (1) **The publish guard had a bypass.** `StatuspagePublisher` keys on the canonical component id,
  so a demo id colliding with a live one, on an API running the DEFAULT `CONFIG_DIR` (what the
  documented recipe does), PATCHes the real page. AC3 gained a mechanical id-disjointness check and
  now names `UnmappedComponentIdError`/`BestEffortPublisher` as the only automatic layer.
  (2) **AC3(b) was unsatisfiable** — the same shape as the original publish AC recorded above. No
  v1 route exposes the runtime mapping, so "asserted against the live process" needed a forbidden
  `backend/src` change; it is now an in-process `create_app()` assertion.
  (3) **AC2 was missing a sixth, silent constraint** — `FUTURE_TOLERANCE = 5min` quarantines
  future-dated rows and `run.py` discards the rejected count, so AC2's own "only three silent
  failures" note undercounted. The timeline direction (past-anchored) is now decided rather than
  left to the implementer.
  (4) **AC5(b)(c)(e) claimed to exercise code with zero consumers.** `expected_locations`,
  `freshness_for`, `stale_after_cycles` and `reentry_cycles` have none outside `config.py`, and the
  completeness denominator uses OBSERVED locations, so a dark location barely moves it. The PO chose
  to reword to the real observable effects rather than defer the scenarios, keeping them as fixtures
  the consumer stories (STORY-151/152) will need.
