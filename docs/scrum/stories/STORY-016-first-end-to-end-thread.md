---
id: STORY-016
title: First end-to-end thread (live demo)
type: feature
---

## Context
Spec: dossier §8 (pull loop), §12/§14 T1.1 (commit-first / best-effort publish), §17 (demo path).
Integration / composition. The deliberate first DEMOABLE thread — point the already-built, fake-tested
orchestration (STORY-016a) at the PO's REAL Dynatrace monitor and REAL Statuspage component and watch
one signal flow end to end.

**Split history.** The orchestration *logic* (run the pipeline per cycle → produce proposals →
publish-on-approve) moved to **STORY-016a** (done, Sprint 17). THIS story is the live wiring: the two
real HTTP **Executors** (Dynatrace DQL + Statuspage PATCH) that were left as injected seams, the
`settings.py` entries for their credentials, the config field carrying the Statuspage component
mapping, threading orchestration through `run_periodic`, and the composition entrypoint that assembles
`BestEffortPublisher(RecordingPublisher(StatuspagePublisher))` and runs the live loop.

**Scope decision (Sprint 20 planning, 2026-06-29 — PO has BOTH Dynatrace and Statuspage creds).**
Build BOTH real Executors this sprint. Everything is gate-green via **recorded fixtures** (no live call
in any test — the pure-core/mockable-edges agreement holds). The single thing the DoD gate cannot prove
is the *live observation* against the real SaaS — that is an explicit **manual post-merge smoke** the PO
runs (runbook in `plan.md` T5), not a gated AC.

## Live topology (committed at sprint-20 prep, 58b4072)
- App `httpcheck` → component `http-check` → signal `http-check`.
- Dynatrace monitor (signal `native_id`): `HTTP_CHECK-DB5792CB88D14CF4`, 120 s cadence.
- Statuspage component (`statuspage_component_id`): `xdnywbx77npw`.

## Acceptance Criteria
- [ ] **AC1 — Real Dynatrace Executor.** A `httpx`-backed `Executor` (the seam in
      `adapters/inbound/dynatrace/query.py::Executor`) POSTs `build_dql_query(...)`'s DQL to the Grail
      execute endpoint (`{DYNATRACE_ENV_URL}/platform/storage/query/v1/query:execute`) with the platform
      token, and maps the Grail response records to the flat row-dict shape the normalizers consume
      (`timestamp`, `event.id`, `synthetic_test.id`, `synthetic_test.type`, `synthetic_location.name`,
      `execution.outcome`, `request.response_time_ms`). Driven by a **recorded fixture** (mocked
      transport) — asserts the request (endpoint, auth header, JSON body carries the query) AND that a
      recorded Grail response normalizes to `SignalObservation`s. No live call in the test.
- [ ] **AC2 — Real Statuspage Executor.** A `httpx`-backed executor for the Statuspage seam
      (`adapters/outbound/statuspage::Executor`) performs the real `PATCH .../components/{id}` and returns
      the parsed JSON. Recorded-fixture test asserts method/url/headers/body and that a non-2xx response
      raises (so `BestEffortPublisher` can swallow it). No live call in the test.
- [ ] **AC3 — Settings + config mapping.** `settings.py::Settings` carries `dynatrace_env_url`,
      `dynatrace_api_token`, `statuspage_page_id`, `statuspage_api_token`; `load_settings()` reads
      `DYNATRACE_ENV_URL` / `DYNATRACE_API_TOKEN` / `STATUSPAGE_PAGE_ID` / `STATUSPAGE_API_KEY`.
      `ComponentConfig` gains an optional `statuspage_component_id: str | None`; `Config` exposes the
      `{component_id: statuspage_component_id}` mapping. Tests: present/absent env, mapping built from
      config (skips components without an id).
- [ ] **AC4 — Live driver wires the full chain, orchestration threaded.** `run_periodic` is extended to
      thread the six orchestration extras through to `run_cycle` (today it runs ingest-only). A new
      composition entrypoint (`composition/run.py` + `python -m`) loads settings + config, seeds topology,
      mirrors `create_app`'s repo wiring, builds the Dynatrace executor and the publisher chain
      `BestEffortPublisher(RecordingPublisher(StatuspagePublisher(statuspage_executor)))`, constructs
      `DecideService(proposal_repo, publisher=best_effort)`, and runs `run_periodic` per signal. A
      fake-backed assembly test proves the chain (BestEffort wraps Recording wraps Statuspage) and that
      orchestration extras reach `run_cycle`. CLAUDE.md gains the run command (command-sync agreement).
- [ ] **AC5 — Manual live smoke (post-merge, NOT gated).** Runbook in `plan.md`: with `.env` set, run the
      loop against a throwaway/Neon Postgres; force a failure on the Dynatrace monitor → a degradation
      proposal appears via `GET /api/v1/approvals`; approve it → the `xdnywbx77npw` Statuspage component
      flips, and a row lands in `publications`. PO-observed; recorded in the retro, not the DoD gate.

## Credentials & setup (all present as of 2026-06-29)
Secrets live in the gitignored `.env`, never committed, never pasted in chat. Config references env-var
NAMES, never values; the monitor id and Statuspage component id are non-secret topology (in
`config/apps/httpcheck.yaml`).
- **`DYNATRACE_ENV_URL`** — tenant base URL `https://bqm75769.apps.dynatrace.com` (Grail DQL execute
  endpoint under `…/platform/storage/query/v1/query:execute`).
- **`DYNATRACE_API_TOKEN`** — platform token, scopes `storage:buckets:read storage:events:read`.
- **`STATUSPAGE_API_KEY`** — Statuspage API token (`Authorization: OAuth <key>`).
- **`STATUSPAGE_PAGE_ID`** — the page id.
- The **monitor id** and **Statuspage component id** are config (above), not secrets.

## Open Questions (resolve in the live smoke, not the gate)
- The exact Grail response field names + the platform-token auth header form
  (`Authorization: Api-Token …`) are the integration unknowns — the recorded-fixture tests pin the shape
  we BUILD to; the PO's live smoke confirms the real tenant matches (adjust the executor's response
  mapping if the field names differ).
- `httpx` moves from a dev-only extra into runtime `dependencies` (the executors need it at runtime).

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §17. Status: draft.
- 2026-06-28: split — orchestration logic to STORY-016a; this story became the live e2e, gated on creds.
- 2026-06-29: refined + scoped for Sprint 20. PO confirmed both Dynatrace + Statuspage creds; chose to
  build both Executors now. AC rewritten to 5 gate-verifiable-or-manual criteria. Points 3 → 5.
