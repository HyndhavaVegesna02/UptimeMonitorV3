---
id: STORY-148
title: Local Grail-shaped demo engine — scripted scenarios, no Dynatrace
type: chore
---

## Context

The PO's Dynatrace trial expired 2026-07-28. No observations arrive, so local DynamoDB stays
empty, nothing data-dependent can be reality-gated, and the multi-monitor / multi-location
correctness work agreed this sprint-line (breadth ceiling, per-component rollup, freshness)
cannot be exercised against realistic scenarios **at any price**.

The existing `sample_mode` feature does not help: `SampleModeIngest` decorates
`SignalIngestPort` and flips **already-normalized** observations to `DOWN`
(`backend/src/composition/sample_mode.py:66-72`), so it needs real data to have anything to
flip.

The seam for a substitute already exists and is documented for exactly this purpose:

```python
# backend/src/adapters/inbound/dynatrace/query.py:32
Executor = Callable[[str], list[dict]]
#: Production wiring (composition root) will inject a real HTTP-backed
#: implementation; every test in this package injects a fake instead.
```

PO approved option (b) — a local HTTP server speaking the Grail `execute query` API — over a
fake `Executor` callable, because it needs **zero production-code changes** (one env var) *and*
is more faithful, additionally exercising `make_grail_executor`, the real HTTP client, auth
headers and response parsing. Decision recorded as D4 in
`docs/scrum/sprints/2026-07-28-sprint-62/decisions-and-future-work.md`.

## Description

A small HTTP server under `tools/demo-engine/` that answers the same request
`make_grail_executor` issues, returning DQL rows shaped exactly like real Grail rows, driven by
**scripted scenario files**. Point `DYNATRACE_ENV_URL` at it and `CONFIG_DIR` at a demo config
directory, and the real loop runs against a fictional fleet.

It is a **scenario player, not a random generator**. Random noise will not reliably produce the
cases that matter (anti-flap ladders, breadth, staleness, the two-monitors-fight bug), so
scenarios declare per-signal, per-cycle, per-location outcomes:

```yaml
api-gateway-health:   [up ×5, "down from 2 of 3 locations" ×4, up ×3]
api-gateway-graphql:  [up ×20]
```

It lives in `tools/` at the repo root, **outside `backend/src/`**, so it can never enter the
production image and import-linter contracts are untouched.

## Acceptance Criteria

- [ ] **AC1 (wire fidelity — the whole value of the story)** — The demo response is
      shape-identical to the real captured sample
      `backend/tests/fixtures/dynatrace/grail_synthetic_events.json`. A test asserts that for
      every field the assembler subscripts directly
      (`timestamp`, `event.id`, `dt.synthetic.monitor.id`, `event.type`,
      `dt.entity.synthetic_location` — `_assembly.py:24`) plus the optional
      `result.statistics.duration` and `result.statistics.response_status_code`
      (`_assembly.py:80-84`), the demo row carries the same key **and the same value type**
      (note `response_status_code` is a STRING-typed number on the real wire, e.g. `"200"`).
      Asserted field-by-field against the fixture, not by eyeballing.
- [ ] **AC2 (query honoured)** — The engine parses the query it is sent and honours **both**
      clauses `build_dql_query` emits (`query.py:85-97`): the
      `dt.synthetic.monitor.id == "<native_id>"` scope filter, and the
      `timestamp >= toTimestamp("…")` lower bound when a watermark exists. Rows are returned in
      `timestamp asc` order. A test proves a query for monitor A never returns monitor B's rows,
      and that a watermark bound excludes older rows.
- [ ] **AC3 (real loop, real fleet)** — Running the unmodified loop
      (`python -m src.composition.run`) with `DYNATRACE_ENV_URL` → the demo engine and
      `CONFIG_DIR` → the demo config ingests observations into DynamoDB for **≥12 components,
      ≥40 signals, ≥4 locations**. Verified by querying the observations table and by
      `GET /api/v1/components` and `/api/v1/topology` returning that fleet.
- [ ] **AC4 (publish safety — non-negotiable)** — No demo run can POST to a real Statuspage.
      `decide` publishes recoveries with **no human gate**
      (`backend/src/core/services/decide.py:122-126`), so fake recoveries would otherwise reach
      the live public page. The demo composition wires a no-op/recording publisher; a test
      asserts the demo wiring's publisher is not the real HTTP one, and the documented recipe
      states the guard.
- [ ] **AC5 (assumptions labelled, not buried)** — `map_synthetic_status` maps only
      `"0"`/`"HEALTHY"` and raises on everything else
      (`adapters/inbound/dynatrace/health_mapping.py:65-70`), because a real failure code has
      never been observed. Any failure code the demo engine emits is therefore an
      **assumption**. All such codes live in ONE named constant with a comment marking them
      unverified pending trial renewal, and the demo README states plainly that "the failure
      path is tested" means "with assumed codes".
- [ ] **AC6 (production untouched)** — `git diff` for this story touches only `tools/`, the
      demo config directory, `docs/`, and test files. **No file under `backend/src/` is
      modified.** Verified mechanically from the story's commit range.
- [ ] **AC7** — All five backend DoD gate commands exit 0.

## Open Questions

None.

## History

- 2026-07-28: drafted. PO chose option (b) (local Grail-shaped HTTP server + scenario files)
  over option (a) (fake `Executor`) and option (c) (also driving CI fixtures — deferred, may
  grow out of this). Recorded as D4. Removal of the superseded `sample_mode` feature is
  deliberately NOT folded in — it has its own removal inventory
  (`docs/scrum/wiki/sample-mode.md`) spanning port/adapter/fake/API, and belongs in its own
  story.
