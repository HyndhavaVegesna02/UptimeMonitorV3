# Debug sprint — sample mode ON but Check History shows "up" (2026-07-06)

A short, PO-directed debug sprint (single session, no story points, no velocity entry).
Recorded per PO instruction as a sprint-style record; there was no planning/review cycle —
this file is plan, review, and retro in one.

- **Trigger (PO, 2026-07-06):** "even when sample mode is on, i can see in check history as
  up. and dynatrace monitor is running no problem that side. debug this in a new branch."
  Same symptom family as the 2026-07-04 report that produced STORY-051.
- **Branch:** `debug/sample-mode-forced-down-not-applied`, cut from
  `debug/ingest-stall-sample-mode` — so it carries the (still unmerged) STORY-051 commits
  `c1839e4` / `2d999f2` / `1257cc9`. STORY-051's own DoD gate (AC3) remains pending its
  sprint; this debug sprint changed no production code.
- **Method:** systematic-debugging protocol — evidence at every component boundary before
  any hypothesis; then a live end-to-end reproduction as the decisive experiment.

## Goal

Determine whether the sample-mode force (`STORY-048` D4 decorator) fails to apply on the
live path — i.e. whether there is a code defect between the Dashboard toggle and the
Check History tab — or whether the symptom is environmental.

## Evidence (live probes, 2026-07-06, times UTC)

**State found at session start** (dev Postgres `uptime_pg_pytest`, port 55432):

| Layer | Probe | Result |
| --- | --- | --- |
| Flag storage | `select * from sample_mode` | **0 rows** — never-set, which the port defines as OFF |
| Observations | `select count(*) from observations` | **0 rows** — this DB instance has never been ingested into |
| Watermarks | `select * from watermarks` | **0 rows** — the loop never ran against this DB |
| Stack | ports 8000 / 5173 / 55432 | nothing listening — API, loop, and frontend all down |

Conclusion from state alone: the DB instance was fresh (recreated since the PO's
observation). The "up" rows the PO saw came from an earlier stack run whose DB no longer
exists; the flag the PO switched ON was a row in that earlier DB.

**Code audit** (no defect found):

- `backend/src/composition/run.py` step 2 wires `SampleModeIngest` around the real
  `IngestService` on the same engine as every other repository — correct.
- `backend/src/composition/pull_loop.py::run_cycle` persists observations **only** through
  `ingest_port`; the `observation_repo` it also receives is read-only input to
  `orchestrate_signal` — no bypass path exists.
- `frontend/src/main.tsx` has no MSW — the dev frontend talks to the real API via the Vite
  proxy; fixture data cannot explain the symptom.
- `frontend/src/features/dashboard/useSampleMode.ts` is non-optimistic (AC2) but holds the
  last successful PUT's value in client state and **never re-polls** — after a DB recreate
  the toggle keeps showing ON against a DB whose flag is OFF.

**Live end-to-end reproduction** (this branch, real Dynatrace, real Grail):

1. `PUT /api/v1/sample-mode {"enabled": true}` → row persisted
   (`t | t | 2026-07-06 06:14:21+00`).
2. Live loop cycle 1: 120 real Grail observations ingested — **all `health=down`,
   `raw_ref='sample-mode:forced-down'`**; watermark written `06:13:54`.
3. Cycle 2 (~2 min later): watermark advanced to `06:15:54`, +2 more forced-down rows —
   the STORY-051 `toTimestamp()` fix re-confirmed live (second independent confirmation
   of its AC2).
4. `GET /api/v1/history` (the exact endpoint Check History renders) returned those rows
   as `"health":"down"`.
5. `PUT {"enabled": false}` → next cycle's 2 rows persisted as genuine `up`,
   `raw_ref NULL` — byte-identical passthrough confirmed both ways.

## Verdict

**No code defect.** The whole chain — toggle → PUT → `sample_mode` row → per-cycle flag
read → forced-DOWN ingest → Check History — works on this branch. The reported symptom is
fully explained by three compounding environmental facts:

1. **Pre-fix ingestion stall (STORY-051, fixed on this branch, unmerged).** Before
   `c1839e4`, the loop ingested only its first-cycle ~2h backfill (as `up`, flag OFF at
   the time) and then never ingested again — so a later flag flip could never produce a
   DOWN row. This was the dominant cause of the original observation.
2. **The flag row lives per DB instance.** `sample_mode` is a table in the throwaway dev
   Postgres; every `dev_db.py up` / fixture recreate resets it to empty (= OFF). The
   Dashboard toggle meanwhile keeps showing ON from client-side state — the UI can
   honestly report a PUT that succeeded against a database that no longer exists.
3. **The flip is not retroactive — by design.** Dedup keys on `source_event_id`
   (wiki: "dedup and watermark behavior is identical regardless of the flag"), so rows
   ingested before the flip stay `up` forever; DOWN applies only to events ingested in
   cycles after the flip. With a ~2h up-backfill and one event/min arriving, Check History
   reads as overwhelmingly "up" for a long time after flipping ON. For an all-down demo:
   flip ON **before** starting the loop against a fresh DB.

## Outcome

- Production code changed: **none.** This debug sprint's only commits are this record and
  a wiki update.
- Wiki: `docs/scrum/wiki/sample-mode.md` gained the operational-gotchas facts above
  (live-verified this session).
- STORY-051 gains a second live confirmation; its merge/DoD path is unchanged (pending a
  planned sprint).

## Follow-up candidates (for refinement — deliberately NOT filed as ready stories)

- Dashboard sample-mode toggle re-polls (`GET` on tab focus / interval) instead of
  trusting client-state override indefinitely — would have exposed cause 2 immediately.
  (Note: the feature is PO-flagged TEMPORARY; weigh against its planned deletion.)
- Per-cycle loop telemetry (fetched/accepted/rejected counts) — already recorded as a
  STORY-051 out-of-scope observation; this session independently re-motivated it.
- A loop-liveness surface in the dashboard (last-cycle timestamp) — causes 1 and 2 were
  both invisible because nothing in the UI distinguishes "healthy and quiet" from "dead".
