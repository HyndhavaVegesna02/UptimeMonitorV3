---
id: STORY-176
title: Grail-shaped demo engine, part 2 — scenario player, demo fleet, and the real loop run
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
- [ ] **AC3 (publish safety — non-negotiable, and config-only)** — No demo run can POST to a
      real Statuspage, **even with real credentials in the repo-root `.env`**. The demo config
      declares no `statuspage_component_id` on any component, so `statuspage_mapping() == {}`
      and both composition roots fall through to `LoggingPublisher`. Two tests: one asserts
      `statuspage_mapping() == {}` for the loaded demo config; one asserts `build_publisher`
      with an empty mapping and non-empty credentials returns a chain whose delegate is a
      `LoggingPublisher`, not a `StatuspagePublisher`. The demo README states the guard and names
      both routes (`run.py:121`, `app.py:160-182`). **No demo loop is started before this AC
      passes** — `decide` publishes recoveries with no human gate
      (`core/services/decide.py:122-126`), so fake recoveries would otherwise reach the live
      public page.
- [ ] **AC4 (the demo fleet)** — A demo config directory (never `config/apps/`) declaring
      **≥12 components, ≥40 signals, ≥4 locations**, authored in STORY-146's nested shape with
      declared `locations:` and a `freshness:` block. Location aliases are short non-cloud-provider
      strings per STORY-146. Fabricated `SYNTHETIC_LOCATION-*` ids are acceptable **here** —
      this is demo config, explicitly not live config.
- [ ] **AC5 (scenario coverage)** — Scenarios cover the cases the planning discussion
      identified: a clean fleet; a degradation crossing the anti-flap ladder to an open
      proposal; a minority-location failure; a fully dark location; and two monitors on one
      component disagreeing (the STORY-151 bug, reproducible on demand rather than by accident).
- [ ] **AC6 (real loop, real fleet)** — Running the **unmodified**
      `python -m src.composition.run` with `DYNATRACE_ENV_URL` → the demo engine and
      `CONFIG_DIR` → the demo config ingests observations into DynamoDB for ≥12 components,
      ≥40 signals, ≥4 locations. Verified by querying the observations table and by
      `GET /api/v1/components` and `/api/v1/topology` returning that fleet over live HTTP.
      The startup `check_vendor_id_health` probe reports **no** dead monitor ids (this is the
      observable proof that STORY-148 AC5's second grammar works end to end).
- [ ] **AC7 (proposal evidence must not be spoofable)** — The scenario used to demonstrate a
      real open proposal on `GET /api/v1/approvals` targets a **single-monitor** component.
      Reason: at ≥12 components / ≥40 signals the fleet averages ~3 monitors per component, and
      `orchestrate.py:88,153` + `decide.py:157-169` mean every healthy sibling resolves an open
      proposal to `OBSOLETED` and publishes a recovery (STORY-151, deliberately unfixed). On a
      multi-monitor component the evidence is racy in both directions. The multi-monitor "fight"
      scenario from AC5 is exercised **separately and deliberately**, as a demonstration of the
      known defect rather than as proposal evidence.
- [ ] **AC8 (production untouched)** — `git diff` touches only `tools/`, the demo config
      directory, `docs/`, `CLAUDE.md`, and tests under `backend/tests/`. No file under
      `backend/src/` is modified, verified mechanically from the commit range.
- [ ] **AC9** — All five backend DoD gate commands exit 0.

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
  (7-cycle window, timestamp format, monotonicity, short intervals) each cause **silent** no-data
  if violated; (3) the "real open proposal" evidence was confounded by the known STORY-151
  sibling-OBSOLETE path and is now pinned to a single-monitor component.
</content>
