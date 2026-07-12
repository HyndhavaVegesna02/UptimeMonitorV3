---
id: STORY-064
title: Observation HTTP status code + check type on ObservationDTO
type: feature
---

## Context
Filed 2026-07-07 from the Sprint 38 redesign data-gap analysis. The mock's Check History grid has
"Type" and HTTP "Code" columns. `ObservationDTO` (`api/v1/history/models.py`) is
`{signal_key, observed_at, health, location, latency_ms?}` — neither exists. STORY-060 omits both
columns; this story adds them.

**Refinement probe (2026-07-12, live Grail + code inventory):**
- The canonical `http_monitor_execution` row carries `result.statistics.response_status_code`
  (string-typed number, e.g. `"200"`) on every sampled row (20/20, tenant monitor
  `HTTP_CHECK-38B092E93932C002`). `normalize_http_row` currently reads only `result.status.code`
  for the health verdict and DROPS the response status code — it is not on `SignalObservation`,
  not in the `observations` table, not on the DTO.
- There is NO dedicated check-type field in Grail; type derives from `event.type`
  (`http_monitor_execution`) — already mapped to `Provenance.native_kind == "http"` by the
  normalizer and PERSISTED in the `source` JSONB. The Type column therefore needs no new
  capture, only threading `source.native_kind` → DTO.
- Fixture source: probe sample records saved from the 2026-07-12 run (real wire values).

## Description
Capture `result.statistics.response_status_code` at normalization onto `SignalObservation`
(new nullable int field), persist it (new nullable `observations.response_status_code` column,
Alembic migration; Postgres repo + in-memory fake in parity), and serve it plus the check type
(from persisted provenance `native_kind`) on `ObservationDTO`. Frontend: add the Type and Code
columns to the Check History grid.

## Acceptance Criteria
- [ ] AC1 — Capture: `normalize_http_row` extracts `result.statistics.response_status_code` as
      `int` (missing/unparsable → `None`, never a crash) onto the observation via the shared
      assembly; tested with a fixture derived from the 2026-07-12 live probe sample.
- [ ] AC2 — Persist: an Alembic migration adds nullable integer
      `observations.response_status_code`; `alembic upgrade head` green on a fresh DB;
      `PostgresObservationRepository` and the in-memory fake both persist/return it, proven by
      the SAME contract test against both (fake/adapter parity).
- [ ] AC3 — Serve: `ObservationDTO` gains `response_status_code: int | None` and
      `check_type: str` (mapped from the persisted provenance `native_kind`); `/api/v1/history`
      returns both; existing validation (tz-aware 422 etc.) unchanged and still tested.
- [ ] AC4 — Render: the Check History grid gains Type and Code columns; Code renders "—" when
      null (pre-migration rows); MSW fixtures derive from a real wire sample; tests cover both
      the populated and null cases.
- [ ] AC5 — Reality gate: with the local stack ingesting live Dynatrace data, one rendered
      row's Type and Code match the raw `/api/v1/history` wire values for the same record.
- [ ] Six-gate DoD green; wiki blast radius resolved (mechanical sweep decides the articles).

## Open Questions
<!-- none — probe resolved the two filed questions (code IS on the canonical row; type derives
     from event.type/native_kind). Non-HTTP monitors: field stays nullable; only http exists. -->

## History
- 2026-07-07: filed from the redesign data-gap analysis. Status: draft (needs refinement + estimate).
- 2026-07-12: refined for pilot sprint 44 — live Grail probe (yt-plan-verifier discipline) +
  yt-scout code inventory answered both open questions; estimate 3; status ready under the PO's
  "run the pilot" directive (scope as recommended: 064 + wiki-coverage chore).
