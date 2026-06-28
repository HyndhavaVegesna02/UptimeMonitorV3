---
id: STORY-016
title: First end-to-end thread
type: feature
---

## Context
Spec: dossier §17 (demo path). Integration. The deliberate first DEMOABLE thread — by
design, the first visible end-to-end behavior (earlier zones demo proven layers).

**Split (Sprint 15 planning, 2026-06-28).** The orchestration *logic* (run the pipeline per cycle →
produce proposals → publish-on-approve), which is fake-testable backend, moved to **STORY-016a**
(itself blocked on the §7/§17 config layer, STORY-040). THIS story is now just the **live e2e demo**:
point the (already-built + fake-tested) orchestration at real Dynatrace + Statuspage and observe the
thread end to end. Gated on live credentials.

## Description
With STORY-016a's orchestration in place, wire one real thread LIVE: one Dynatrace monitor → pull
loop → canonical observation → pipeline → proposal → human approval → Statuspage publish. A forced
failure via the shim produces a proposal that, once approved, publishes — observed end to end against
real services.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: A forced failure (via the shim) produces a degradation proposal visible on
      the dashboard.
- [ ] AC2: Approving that proposal publishes the status change to the real Statuspage —
      observed end to end.
- [ ] AC3: The thread runs against deployed/integrated components (not just unit mocks).

## Credentials & setup (captured 2026-06-28 — PO has Dynatrace ready)
The PO has a Dynatrace tenant with **one synthetic monitor** set up. Prerequisite (likely a small
sub-story, "real Dynatrace Executor"): the production `Executor` is NOT built yet — today
`adapters/inbound/dynatrace/query.py::Executor` is just a `Callable[[str], list[dict]]` seam injected
with a fake in every test ("production wiring will inject a real HTTP-backed implementation"). The
backend reads ZERO Dynatrace credentials today; `composition/settings.py` only knows `DATABASE_URL`.
When the real Executor is built it needs:
- **`DYNATRACE_ENV_URL`** (secret, env) — the tenant base URL (e.g. `https://<id>.apps.dynatrace.com`);
  the Grail DQL execute endpoint lives under `…/platform/storage/query/v1/query:execute`.
- **`DYNATRACE_API_TOKEN`** (secret, env) — a platform token with the Grail **synthetic-read** scope
  (confirm the exact current scope name against Dynatrace docs before minting; do not over-scope).
- The **monitor id** is CONFIG, not a secret — it goes in `config/apps/<app>.yaml` as the signal's
  `native_id` (dossier §7: config holds the mapping, env holds secrets; config references env var
  NAMES never values). Statuspage publish creds are the analogous pair for the publish side.
Secrets go in the environment / a gitignored `.env`, never committed and never pasted into the
transcript. Env-var names are finalized when the Executor + `settings.py` entry are written.

## Open Questions
- Confirm which monitor/route is the headline thread and the live-credential plan at
  refinement (this is the first story needing live Dynatrace + Statuspage).
- Build the "real Dynatrace Executor" (HTTP DQL client + settings + recorded-fixture test) as a
  sub-story before/within this one? (It is the concrete piece the live thread needs.)
- **Wire the orchestration's `DecideService` with `composition/publish_helper.py::BestEffortPublisher`**
  (STORY-016a left this as a documented injection contract — no live composition root wires it yet).
  The live driver (`run_periodic` threading the orchestration extras) MUST inject the real Statuspage
  publisher wrapped in `BestEffortPublisher`, or a recovery-publish failure crashes the pull cycle
  (STORY-016a AC3 / T1.1). Flagged by both Opus reviewers at the Sprint 17 review.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §17. Status: draft — refine before its sprint.
