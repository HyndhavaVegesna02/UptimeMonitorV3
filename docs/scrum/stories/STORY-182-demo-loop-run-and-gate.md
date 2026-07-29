---
id: STORY-182
title: Grail demo engine part 2b — the real loop run against the demo fleet, and its two-sided gate
type: chore
---

## Context

Split out of STORY-176 at sprint-63 planning (2026-07-29) after `yt-plan-verifier` re-estimated the
combined story at **6 points** and the PO chose to split rather than cram. STORY-176 keeps
**part 2a** — the scenario player, the demo fleet, the time base, and the publish-guard checks.
This story is **part 2b**: actually running the unmodified system against that fleet, and proving
the run means something.

The split is not arbitrary. STORY-176's publish-guard checks are precisely what must pass **before
any loop is ever started** (`decide` publishes recoveries with **no human gate**,
`decide.py:122-126`, published at `:171-172`). Putting the run in its own story makes that ordering
structural rather than a step order someone can reshuffle.

**Depends on:** STORY-176 (part 2a) — the player, the fleet config and the guard checks must exist
and pass first. Also STORY-148 (the wire contract) and STORY-146 (the nested config shape).

## Description

Run `python -m src.composition.run` — **unmodified** — with `DYNATRACE_ENV_URL` pointed at the demo
engine and `CONFIG_DIR` pointed at the demo config, and prove from **observation-derived** evidence
that the fleet ingested. Then prove the same evidence could have come back negative.

Four findings from the pre-lock verification shape this story, and each is an AC below rather than
a step someone might skip:

1. **`/components` and `/topology` are seed-derived** (`api/v1/topology/service.py:29` says so in
   its own docstring: *"sourced from the seeded topology"*; `components/service.py:22` reads
   `component_repo.list_components()`). Both return the full 12-component fleet **even if the demo
   engine returns `[]` for every query.** They are necessary but not sufficient evidence.
2. **The dedupe marker is permanent** (`dynamo_observation_repository.py:58-62`:
   `pk=EVT#<source_event_id>`, `sk=DEDUPE`). A repeat run against a reused table ingests **zero**
   rows while the table still holds the previous run's — a PASS indistinguishable from "nothing
   happened", which working agreement A1 (2026-07-29) exists to forbid.
3. **`DYNAMO_ENDPOINT_URL` is not in the repo-root `.env`** (verified: the file carries
   `DYNATRACE_*`, `STATUSPAGE_*`, and the retired `DATABASE_URL*` only). Unset, `make_dynamo_resource`
   (`composition/dynamo.py:19-27`) omits the dummy credentials and boto3 targets **real AWS
   us-east-1 with the operator's real credentials**. Today the default table names
   (`uptime-observations`/`uptime-control`, `settings.py:34-37`) differ from the live
   `uptime-monitor-*` names so it fails loudly — but this run is exactly where someone might export
   the live names.
4. **A leftover sample-mode flag rewrites reality.** `SampleModeIngest` forces **every** observation
   to `DOWN` while the persisted flag is ON (`composition/sample_mode.py:61-72`); the flag lives in
   the control table and is flippable over HTTP. On a reused table an ON flag turns the clean fleet
   into a fully-down fleet and opens degradation proposals — contradicting AC3 below.

## Acceptance Criteria

- [ ] **AC1 (preconditions, asserted and recorded — not assumed)** — Before the loop starts, all of
      these are asserted and their values recorded in the story evidence:
      (a) `CONFIG_DIR` → the demo config on **both** the loop and the API process (the API is a
      separate process that loads its own config, `app.py:137-138`, defaulting to `config/apps`,
      `settings.py:32`);
      (b) `DYNAMO_ENDPOINT_URL` → DynamoDB Local, and the table names are the demo ones, on **both**
      processes — never unset, never the live `uptime-monitor-*` names;
      (c) `GET /api/v1/sample-mode` → `{"enabled": false}`;
      (d) STORY-176's publish-guard checks re-run green at this story's HEAD (they are cheap;
      re-running them here means the guard is verified against the code that actually ran).
- [ ] **AC2 (a FRESH observations table, or an equivalent assertion)** — The run uses a
      newly-created observations table, **or** every ingest assertion additionally requires
      `observed_at >= run-start`. Which one was used is stated in the evidence. Rationale: the
      permanent `EVT#…/DEDUPE` marker makes a second run against a reused table ingest nothing while
      still passing a naive row-count check.
- [ ] **AC3 (the run ingests the fleet, proven from OBSERVATION-derived evidence)** — The unmodified
      `python -m src.composition.run` ingests observations for **≥12 components, ≥40 signals, ≥4
      locations**. Evidence must include at least one **observation-derived** endpoint, not only the
      seed-derived ones:
      `GET /api/v1/history?signal_key=…&since=…` and/or `GET /api/v1/availability?signal_key=…`
      (which carries `distinct_locations` and `completeness_pct`) and
      `/availability/component/{id}`.
      `GET /api/v1/components` and `/api/v1/topology` are recorded too, but explicitly labelled as
      **seed-derived — they pass with zero ingest** and are therefore not the proof.
- [ ] **AC4 (no dead monitor ids)** — The startup `check_vendor_id_health` probe (`run.py:196`)
      reports **no** dead ids for the ≥40 demo signals. This is the observable end-to-end proof of
      STORY-148 AC5's second (vendor-health) grammar.
- [ ] **AC5 (no proposal evidence is claimed, and the reason is recorded precisely)** — This story
      claims **nothing** about proposals appearing on `GET /api/v1/approvals`, because none can
      open: with only `UP` observations, and components seeded `OPERATIONAL`
      (`seed_dynamo.py:49`), `proposed_status == current_status`, so `decide` takes neither branch
      and `publish_change` stays `None` (`decide.py:119-126`). The endpoint is asserted to return a
      well-formed **empty** result.
      **State the consequence explicitly in the evidence:** because `publish` is never called at
      all, any "no Statuspage POST was attempted" log observation is **vacuous** — it proves
      nothing about the guard. The guard's evidence is STORY-176's publisher-type assertion, not
      this silence. Recorded as an AC so a future reader cannot mistake a quiet log for proof.
- [ ] **AC6 (production untouched)** — `git diff` for this story touches only `tools/`, the demo
      config directory, `docs/`, `CLAUDE.md`, and `backend/tests/`. No file under `backend/src/` is
      modified, verified mechanically from the commit range.
- [ ] **AC7** — All **eight** DoD gate commands exit 0 (five backend + three frontend; this story
      touches no frontend source, but the sprint-close full gate is the evidence of record).

## The reality gate (specified here because it is half the story's cost)

Working agreement A1 (2026-07-29) requires a recorded answer to "how could this have failed?".
Three sides:

1. **Positive** — the full run as AC3/AC4 describe, on a fresh table.
2. **Discriminating on the guard** — with a throwaway config that DOES declare a
   `statuspage_component_id` (a fake vendor id), the same runtime check must show a **non-empty**
   mapping and a real `StatuspagePublisher` selected. **Assert the selected publisher's TYPE; make
   no network call.** A guard whose check cannot come back "unsafe" is not evidence.
3. **Discriminating on backfill** — with an engine holding no history,
   `check_vendor_id_health` WARNs for every signal; with ≥2 h of coverage it is silent. Only the
   pair proves the vendor-health grammar works end to end.

## Open Questions

None.

## History

- 2026-07-29: split out of STORY-176 at sprint-63 planning. `yt-plan-verifier` re-estimated the
  combined story at 6 points against a 4-point entry — evidence: STORY-148 delivered the entire wire
  contract (rows, both grammars, store, HTTP server, 23 tests) for 3 points, while the combined
  STORY-176 additionally carried a YAML schema and player, a ≥12-component/≥40-signal/≥4-location
  config authoring task, five scenarios, a three-process live run under two known env-friction
  defects (STORY-179, STORY-178), three publish-guard checks, and a two-sided gate needing a second
  config and a second run. The PO chose to split rather than cram (standing pacing directive,
  2026-07-28). Four verifier findings are folded in as ACs here rather than left as steps: the
  seed-derived-endpoint false pass (AC3), the permanent dedupe marker (AC2), the missing
  `DYNAMO_ENDPOINT_URL` and its real-AWS consequence (AC1b), and the leftover sample-mode flag
  (AC1c). AC5 additionally records that the "no POST attempted" observation is *vacuous* under
  UP-only scope — `publish` is never called, so silence proves nothing.
