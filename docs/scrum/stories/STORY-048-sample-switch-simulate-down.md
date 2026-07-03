---
id: STORY-048
title: Sample switch (backend) — persisted flag + toggle API + incoming signals recorded as DOWN while ON
type: feature
---

## Context
PO idea (2026-07-03, right after the sprint-30 live demo): the real monitor is healthy, so the
Approvals and Publications tabs are always empty and the core approve→publish loop can only be
exercised with fakes. A **sample switch** fixes that: while it is ON, every incoming Dynatrace
observation is recorded with health **DOWN** (simulating an outage), so the real pipeline
(streak → anti-flap → decide) opens a real degradation proposal that can be approved, published,
and — after flipping the switch OFF — recovered from. Default OFF (PO answer, 2026-07-03).

Architectural constraint (why this is not just an in-memory bool): the Dashboard/API server and
the live pull-loop are two separate processes sharing only the database. The switch state must
be DB-persisted, mutated through the API, and re-read by the loop every cycle.

Hexagonal constraint: the core stays pure — the forced-DOWN override is a composition-layer
concern applied at the ingest edge, never inside `core/services/`.

## Description
Backend only (the Dashboard toggle UI is STORY-049):
1. A persisted global **sample-mode flag** (single boolean, default OFF): migration + core port +
   Postgres adapter + fake (parity).
2. A five-file API feature exposing the flag: read current state + set it.
3. Live-loop wiring: each cycle reads the flag; while ON, observations are recorded with
   health=DOWN (all signals); while OFF, behavior is byte-identical to today. A flip takes
   effect from the next cycle — no process restart.
4. Simulated rows are identifiable as simulated (marker decided in the plan, e.g. via the
   observation's provenance), so real history can be distinguished/cleaned later.

## Acceptance Criteria
- [ ] AC1: the flag is persisted and process-crossing: migration adds its storage (default OFF);
      a core port exposes get/set in domain vocabulary; Postgres adapter + in-memory fake agree
      via ONE parity contract test (2026-06-26 agreement), incl. the never-set → OFF default.
- [ ] AC2: API endpoints expose the flag (five-file module + shape test): GET returns the current
      state; a mutate endpoint sets ON/OFF (idempotent; invalid body → 422). Tested through
      `create_app` with fakes + one DB-gated round-trip.
- [ ] AC3: with the flag ON, the live loop records every incoming observation with health=DOWN
      regardless of vendor-reported health; with it OFF, recorded observations are unchanged
      (regression: existing ingest tests stay green). Override lives in the composition layer;
      core imports stay pure. Tested with fakes driving both switch states.
- [ ] AC4: the flag is read per cycle: a flip between cycles changes the next cycle's recording
      with no loop restart. Tested (two-cycle fake-driven test, OFF→ON and ON→OFF).
- [ ] AC5: simulated observations are identifiable as simulated in what is persisted; the test
      proves a simulated row is distinguishable from a genuine DOWN.
- [ ] AC6: all six backend gates green; wiki blast radius resolved.
- [ ] AC7 (PO directive at lock, 2026-07-03 — this is a TEMPORARY feature): removability is
      designed in. (a) All sample-mode logic lives in dedicated new modules (domain, port,
      adapter, API feature, composition seam); existing files are touched only at minimal,
      clearly-marked seam points. (b) With the switch OFF, runtime behavior is byte-identical to
      before this story (regression: the pre-existing ingest/loop BEHAVIOR tests pass
      unmodified; the run.py assembly-shape test alone is updated for the marked seam — it
      asserts composition shape, which deliberately changes there).
      (c) A REMOVAL inventory is written (in the story's wiki article) listing exactly what to
      delete/revert — files, seam lines, the drop-migration — so a future removal story is
      mechanical and cannot break the system.

## Open Questions
None at draft time — switch meaning ("record incoming as DOWN") and default (OFF) are PO answers
(2026-07-03). Storage shape / marker mechanism / endpoint naming are plan-level decisions.

## History
- 2026-07-03: drafted from the PO's post-sprint-30-demo idea + clarification ("incoming dynatrace
  logs from monitor should be recorded as down", default OFF). Estimate 5. Frontend toggle split
  out as STORY-049 (frontend zone isolation).
- 2026-07-03: PO approved; at the sprint-31 lock the PO added the temporary-feature/removability
  directive → AC7. Estimate unchanged (removability is a design constraint, not extra surface).
