---
id: STORY-070
title: Live vendor-id drift health check — surface a configured-but-empty Dynatrace monitor id loudly
type: feature
---

## Context
From the Sprint 38 retro (2026-07-08 working agreement). During the Sprint 38 review browser
walkthrough, History/Availability were empty; a direct Grail probe found the configured
`config/apps/httpcheck.yaml` `native_id` (`HTTP_CHECK-DB5792CB88D14CF4`) had produced ZERO
executions in 30 days — the demo monitor had been recreated with a new id
(`HTTP_CHECK-38B092E93932C002`, 2,882 runs/24h). The pull loop polled Dynatrace correctly every
cycle (async execute+poll, HTTP 200) but the stale id matched no rows, so it ingested nothing
**silently** — a "trusted-and-wrong" no-data pipeline. Fixed by hotfix `79bfbb3`; this story adds
detection so the drift can never again go unnoticed.

## Description (to refine)
Add a health signal that each configured monitor `native_id` resolves to live executions — e.g. a
boot-time check and/or a periodic probe that runs a bounded DQL count for each configured monitor
over a recent window and surfaces "configured monitor X returned 0 rows over N" loudly (log
ERROR/warning, health endpoint, or metric) rather than letting the loop ingest nothing quietly.
Must stay within the pure-core / mockable-edge architecture (the probe is an adapter concern; core
stays vendor-free). No live Dynatrace call in tests (fake the executor).

## Acceptance Criteria (to refine)
- [ ] A configured `native_id` that returns 0 rows over the check window produces a LOUD, testable
      signal (not a silent no-op); a healthy id does not.
- [ ] Covered by tests with a faked executor (no live vendor call); the check is wired into the
      boot/loop path per the chosen mechanism.
- [ ] Backend six-gate DoD green.

## Decided (sprint-41 planning, PO 2026-07-08)
- **Mechanism = loud WARNING at live-loop startup** (NOT fail-fast — must not block startup). At
  loop start, run a bounded DQL count per configured `native_id` over a recent window; 0 rows → log
  a prominent WARNING naming the monitor. Testable with a faked executor (no live Dynatrace call).
- Window/threshold: a recent bounded window (e.g. last ~2h or a small multiple of the interval); a
  single startup probe returning 0 rows is enough to warn.

## Open Questions
None — mechanism decided above.

## Review outcome (sprint-41, 2026-07-09)
- **Spec (Opus): PASS.** AC1 MET (0-rows → loud WARNING naming the monitor; healthy id logs no
  warning; driven+asserted in `test_vendor_health.py`). AC2 MET (faked executor; probe wired into
  `run.py::main` before `build_live_loop`; the wiring test does NOT patch away the wiring; non-fail-fast
  behavior tested). AC3 (six-gate) MET after a trivial ruff gate fix.
- **Quality (Opus): APPROVE** (0 critical / 0 major). Non-blocking MINORS captured as candidate nits
  (not fixed — no follow-up story unless the PO wants one):
  1. `build_vendor_health_query` interpolates `native_id` without the `InvalidNativeIdError` guard its
     sibling `adapters/inbound/dynatrace/query.py::build_dql_query` uses. Safe: `native_id` is trusted
     config and any malformed-query error is caught by the probe's broad `except` → logged WARNING,
     never a crash. Divergence noted for consistency only.
  2. The probe counts all `dt.synthetic.events` for the id rather than scoping to
     `event.type == "http_monitor_execution"` like the ingest query — deliberate lenient existence
     probe, documented in the docstring.
- **Gate note:** the canonical `pytest` false-red on the sprint-untouched, Docker-contention-flaky
  DB-lifecycle tests (`test_dev_db_cli.py` + `test_dev_db_fixture.py`); proven contention and handled
  per the 2026-07-06 agreement; filed as defect **STORY-073**. STORY-070's own 17 tests + 523 others
  green; gates 2–6 green. Integrated to sprint-41 @ `4d3fd7a`; wiki resolved @ `d223b3d`.

## History
- 2026-07-08: filed from the Sprint 38 retro (working agreement on live vendor-id drift).
  Status: draft (needs refinement + estimate).
- 2026-07-09: implemented (Sonnet worktree), reviewed (spec PASS / quality APPROVE), six-gate green
  (pytest via the resource-isolated valid signal), board → done. Awaiting PO acceptance at review.
