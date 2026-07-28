# Carried forward to sprint 63 — STORY-176 plan section

Excised from sprint 62's `plan.md` when the PO moved STORY-176 to sprint 63 (decision D-B,
2026-07-28). Kept verbatim so sprint 63's planning starts from the verified contracts and
steps rather than re-deriving them — **but re-verify before use**: these citations were
confirmed at `57aa523`, and STORY-146 changes `composition/config.py` beneath them.

`docs/scrum/stories/STORY-176-demo-fleet-scenarios-and-loop-run.md` is the AUTHORITY on
scope and is already rescoped for decision D-A (UP + absence only, no failure scenarios,
AC7 inverted to prove no proposal can open). The steps and reality gate below still
reference the pre-D-A failure scenarios in places — reconcile against the story, not this.

---

## STORY-176 — demo engine part 2: scenario player, demo fleet, real loop run (3 pts)

### Verified contracts / constraints (cited)

- **Publish exposure, both routes.** `run.py:178 load_dotenv()` walks up from the source file,
  not CWD, so the existing repo-root `.env` supplies `STATUSPAGE_PAGE_ID`/`STATUSPAGE_API_KEY`
  from any launch directory. Route 1: `run.py:121-128` → `build_publisher`. Route 2 (the API's
  approve trigger, and the reality gate runs the API): `composition/app.py:160-182` →
  `load_statuspage_secrets()` + `seed_config.statuspage_mapping()` → the same `build_publisher`.
- **The single gate both routes pass through** (`publish_helper.py:211`):
  `if statuspage_page_id and statuspage_api_token and component_mapping:` — so an **empty
  mapping** forces `StatusWritebackPublisher(LoggingPublisher(), …)` even with real credentials.
  `statuspage_mapping()` includes only components declaring a non-None
  `statuspage_component_id` (`config.py:292-299`). Neither root has a publisher injection point,
  which is why the guard is config-only.
- **Ingest window:** `orchestrate.py:94-98` — `since = until - (max_threshold + 2) * interval`,
  a rolling **7-cycle** window (§10 defaults) ending at `clock.now()`. Rows outside it never
  become verdicts.
- **Timestamp strictness:** `parse_ns_timestamp` feeds `SignalObservation`, which rejects naive
  or non-UTC datetimes (`signal.py:81-91`: "observed_at must be a tz-aware UTC datetime"). A
  raise kills the cycle while `run_periodic` survives — i.e. silent no-data, not a crash.
- **The sibling-OBSOLETE path (known, deliberately unfixed):** `orchestrate.py:88,153` resolves
  the component per signal, and `decide.py:157-169` OBSOLETEs an open proposal when a sibling
  reports healthy — publishing a recovery. This is STORY-151; at ~3 monitors/component it makes
  proposal evidence racy in both directions.
- **Recovery is ungated:** `decide.py:122-126` publishes recoveries with no human approval.
- STORY-146's nested shape and per-app `locations:`/`freshness:`; STORY-148's engine.

### Steps

- [ ] 1. Failing test: scenario file → per-signal, per-cycle, per-location outcome sequence; the
      player expands it into rows at each monitor's `interval_seconds`, asserting exact row
      counts per location per cycle. Then implement.
- [ ] 2. Failing tests for each of AC2's four time-base constraints: rows land inside the
      7-cycle window; timestamps are `Z`-suffixed 9-digit UTC matching the fixture **format**;
      emission is monotonic across successive queries; demo intervals ≤ 60 s. Each violated
      constraint yields silent no-data, so each is asserted rather than assumed.
- [ ] 3. **AC3 before any loop run** — author the demo config with **no**
      `statuspage_component_id` anywhere; two tests: `statuspage_mapping() == {}` for the loaded
      demo config, and `build_publisher` with an empty mapping + non-empty credentials returns a
      chain whose delegate is a `LoggingPublisher`. Document the guard and both routes in the
      demo README.
- [ ] 4. Author the demo config directory (≥12 components, ≥40 signals, ≥4 locations) in
      STORY-146's nested shape, with declared `locations:` (short non-cloud-provider aliases) and
      a `freshness:` block. Fabricated `SYNTHETIC_LOCATION-*` ids are fine here — demo config,
      never `config/apps/`.
- [ ] 5. Scenario set per AC5: a clean fleet; a degradation crossing the anti-flap ladder to an
      open proposal (on a **single-monitor** component, AC7); a minority-location failure; a
      fully dark location; two monitors on one component disagreeing.
- [ ] 6. Run the **unmodified** `python -m src.composition.run` against the engine + demo config;
      verify observations for ≥12 components / ≥40 signals / ≥4 locations, and that
      `check_vendor_id_health` reports **no** dead monitor ids (the end-to-end proof of
      STORY-148 AC5).
- [ ] 7. AC7: capture the open-proposal evidence from the single-monitor component; exercise the
      multi-monitor "fight" scenario separately as a demonstration of the known STORY-151 defect.
- [ ] 8. AC8: verify the story diff touches no file under `backend/src/`.
- [ ] 9. Document the demo recipe in `CLAUDE.md` (append-only) — the two env vars and the
      publisher guard.
- [ ] 10. Wiki: add the demo engine as a new article (`code_refs` → `tools/demo_engine/`), and
      record in `sample-mode.md` that this supersedes `sample_mode` (removal is STORY-155).

### Reality gate (176)

Start DynamoDB Local, point `DYNATRACE_ENV_URL` at the demo engine and `CONFIG_DIR` at the demo
config, run the **unmodified** `python -m src.composition.run`, and show:

1. observations landing for ≥12 components / ≥40 signals / ≥4 locations;
2. `GET /api/v1/components` + `/api/v1/topology` returning that fleet over live HTTP;
3. `check_vendor_id_health` reporting no dead monitor ids at startup;
4. a scripted degradation opening a real proposal on `GET /api/v1/approvals` — from a
   **single-monitor** component, so no healthy sibling can OBSOLETE it (AC7);
5. the log/recording proving no Statuspage call was attempted, with `statuspage_mapping() == {}`
   as the mechanism.

**Honest limits to state in the evidence:** every failure-state row rests on assumed vendor
codes (STORY-148 AC8) — the pipeline's handling of them is verified, the codes themselves are
not; and the fleet is fictional, so this proves the *system* handles a fleet, not that any
particular real monitor behaves this way.

---
