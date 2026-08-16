---
title: Sample mode — the on-demand outage simulator (REMOVED, STORY-155a/155b)
tier: reference
status: archived
archived_sprint: sprint-73
archived_reason: >-
  Declared TEMPORARY by PO directive at the sprint-31 lock (2026-07-03, STORY-048 AC7):
  removability was a first-class acceptance criterion from the day this feature was built.
  It existed to solve one problem — the real Dynatrace monitor stayed healthy, so the
  Approvals/Publications tabs were always empty and the degrade→approve→publish→recover loop
  could only be exercised against fakes — by forcing every incoming observation to
  `Health.DOWN` while a persisted flag was ON. STORY-148's Grail demo engine
  (`tools/demo_engine/`, see [[demo-engine]]) reached the same demonstration goal without a
  bespoke, always-armed decorator sitting over the live ingest front door: a real HTTP server
  the unmodified `make_grail_executor` talks to, driven by an authored scenario player,
  producing HEALTHY rows and absence (never a fabricated DOWN). Once the demo engine existed
  and was proven end-to-end (STORY-182), sample mode had no remaining reason to exist —
  STORY-155a removed the frontend consumer (2026-08-15/16) and STORY-155b (this story) removed
  the backend producer, deleted the DynamoDB flag repository/port/adapter, the
  `SampleModeIngest` composition-layer decorator, and the `GET`/`PUT /api/v1/sample-mode`
  API feature, then archived this article — consumer-first, so it staled only once instead of
  being updated and then archived. Full removal accounting: STORY-155b's own History section
  and its story file.
verified_sprint: sprint-69
# Archived 2026-08-16 (STORY-155b). Converted from tier: map / status: stale (STORY-155a's
# 2026-08-16 demotion, once the frontend half went out from under it) to tier: reference /
# status: archived. code_refs and the "## Facts" heading are dropped per the reference tier's
# integrity rule (yt_wiki.py::check_integrity) -- a tombstone asserts nothing about live code,
# so it is never swept (docs/scrum/wiki/*.md is a non-recursive, top-level-only glob;
# docs/scrum/wiki/archive/ is explicitly out of its scope, per test_citation_gate.py's own
# comment). The body below is preserved as HISTORY of what was built and why -- not a current
# claim about any file it names, all of which are deleted as of this same story.
---

## What sample mode was (historical — not a claim about current code; every file it names
below is deleted as of STORY-155b)

### The problem it solved (dossier §6, §8, §17)
The real Dynatrace monitor was healthy, so the Approvals and Publications tabs were always
empty and the approve→publish→recover loop could only be exercised with fakes. Sample mode was
a global, persisted, process-crossing boolean flag: while ON, the live loop recorded EVERY
incoming observation with `health=DOWN` (simulating an outage), so the real pipeline
(streak → anti-flap → decide) opened a real degradation proposal that could be approved,
published, and — after flipping the switch OFF — recovered from. Default OFF (PO answer,
2026-07-03).

The two-process constraint (why this was DB-persisted, not an in-memory bool): the API server
and the live loop shared only the database, so the flag had to be readable from both
processes. Hexagonal constraint: the forced-DOWN override was a composition-layer concern,
applied at the ingest edge — `core/domain/*` and `core/services/*` were never touched.

### Shape (D1–D7, STORY-048)
- **Storage**: one row in the control table, `pk="CONFIG", sk="SAMPLE_MODE"` (a
  process-crossing single boolean; absent row meant OFF).
- **Port**: `SampleModeRepository` (ABC) — `is_enabled() -> bool` (never raises, `False` when
  never set) and `set_enabled(enabled: bool) -> None` (idempotent upsert).
- **API**: a five-file `api/v1/sample_mode/` feature — `GET /sample-mode` →
  `{"enabled": bool}`; `PUT /sample-mode {"enabled": bool}` → applies the flag, returns the new
  state, idempotent.
- **The override**, `SampleModeIngest` — a composition-layer decorator over `SignalIngestPort`,
  wrapping the real `IngestService` in `composition/run.py::build_live_loop`. Read the flag
  EXACTLY ONCE per `ingest_observations` call (no caching), matching one read per
  `run_periodic` cycle. OFF: passthrough, the SAME observation instances (no copy, byte-
  identical to today's behavior — this invariant is what STORY-155b's AC1 re-proved one layer
  up, through `run_periodic`, right before the decorator was deleted). ON: every observation
  replaced by a copy with `health=Health.DOWN` and `raw_ref="sample-mode:forced-down"` (the
  sentinel marker, D5) — every other field (`signal_key`, `observed_at`, `source_event_id`,
  `source`, `location`, `latency_ms`) unchanged, so dedup/watermark behavior never depended on
  the flag.
- **The frontend consumer** (STORY-049, relocated STORY-056): a shell-level top-bar trigger
  (`TopBar.tsx`) plus a dismissible warning banner (`SampleModeBanner.tsx`), both driven by one
  `useSampleMode()` hook called once in `AppShell.tsx` and threaded down as a prop — removed by
  STORY-155a.

### Operational gotchas (live-verified 2026-07-06 debug sprint;
`docs/scrum/sprints/2026-07-06-debug-sample-mode/report.md`)
The flip was NOT retroactive — forced copies kept `source_event_id` unchanged, so any
observation already persisted as `up` before a flip stayed `up` forever; DOWN applied only to
events ingested in cycles AFTER the flip. The flag row lived per DB instance, so recreating a
throwaway dev database reset it to OFF while a client-side hook could keep showing ON from its
last successful PUT (no re-poll) — a genuine UI/DB disagreement, not a defect, once understood.

### Why it was safe to build knowing it would be deleted
Every design decision favored removability over integration: dedicated new files wherever
possible, existing files touched only at minimal, comment-marked seam points
(`# STORY-048 sample-mode seam`), zero changes to canonical domain types or existing tables,
and flag-OFF byte-identical to pre-feature behavior. That is exactly what let STORY-155b remove
it in one story: delete the dedicated files, revert the marked seam lines, done — the mechanical
deletion recipe this article originally carried (STORY-048 AC7c) matched reality closely enough
to be followed, once three drifted spots were corrected at STORY-155b's pre-lock verification
(a wrong adapter filename, a "Postgres" label the DynamoDB migration had left stale, and the
DynamoDB key shape — sort key, not partition key).

## History
- 2026-08-16 (STORY-155b): **ARCHIVED.** The backend half of the feature (port, DynamoDB
  adapter, `SampleModeIngest` decorator, the `api/v1/sample_mode` five-file feature, and every
  wiring seam) was deleted; this article converted from `tier: map` / `status: stale` (STORY-155a's
  demotion) to `tier: reference` / `status: archived`, moved into `docs/scrum/wiki/archive/`, and
  had its `code_refs` and `## Facts` heading dropped per the reference tier's integrity rule. The
  body above is a condensed historical record; the full original Facts (implementation detail,
  file-by-file) and this article's complete verification trail across 30+ sprints remain readable
  in git history at any commit before this one.
- sprint-69 and earlier: see git history for this file's full verification trail
  (`git log -- docs/scrum/wiki/sample-mode.md`, or any earlier commit's copy of this article) —
  not reproduced here; the condensed record above is what a reader needs going forward.
