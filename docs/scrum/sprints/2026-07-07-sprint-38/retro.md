# Sprint 38 Retro — Operator Dashboard redesign

**Outcome:** 8/8 stories accepted, **31/31 points** (velocity recorded), single session. No story
blocked; all estimates held; no effort-cap trips. Merged to `main` @ `827cf69`.

## What went well
- **Commit-after-green crash-recovery generalized to a new failure mode.** The account **session
  limit killed two implementer agents mid-run** (056, 057). Zero work lost: 056 had committed
  nothing → clean fresh redo; 057's committed hook steps were recovered by merging its branch and a
  fresh agent finished the page. The crash-recovery agreement (written for connection drops) held
  perfectly under session-limit deaths.
- **Wave-based parallel multi-agent execution** delivered the whole redesign in one session: Wave 0
  (foundation) → Wave 1 (shell) → Wave 2 (six pages in two parallel worktree batches), integrated
  serially with per-story Opus spec+quality reviews and serial gates. Disjoint file-scoping held —
  no integration conflicts.
- **Adapt-to-real-data discipline** — no fabricated data anywhere; five backend gaps filed
  (063–067) instead of faked.
- **The review live walkthrough earned its keep again** (cf. Sprint 32) — it surfaced a live
  operational bug (stale monitor id) wholly unrelated to the sprint.

## What dragged / incidents
- **1 reviewer rejection loop:** STORY-060 quality CHANGES REQUESTED — a missing
  `prefers-reduced-motion` guard its sibling Availability page already had, and the render cap
  silently lowered 1000→200. Both fixed in one loop (cap restored via an injectable prop so the
  flake fix didn't cost product behavior).
- **1 hotfix:** stale Dynatrace `native_id` (`config/apps/httpcheck.yaml`). Root cause: nothing
  verified a configured vendor id resolves to live data, so the loop ingested nothing silently. NOT
  introduced by any sprint-38 story (empty backend diff) — pre-existing config drift. Fixed on
  `main` @ `79bfbb3`.
- **New flaky test:** STORY-058's `useAvailability.test.tsx` false-reds under CPU parallelism (→
  STORY-068). Same class as STORY-054, which this sprint fixed — a recurring jsdom-under-contention
  theme.
- **Worktree footgun:** agent worktrees were cut from `sprint-38-start` (branch base), not the tip,
  so each Wave-2 agent had to `git merge sprint-38` to get the foundation. Batch-1 agents
  self-corrected; an explicit sync STEP 0 was added to batch-2 briefs mid-sprint.

## Wiki drift
Only `frontend-zone.md` went stale (the six page rebuilds) — recompiled at sprint close. Nothing
stale ≥3 sprints; the other 12 articles stayed current (empty backend diff).

## Amendments adopted (PO-approved 2026-07-08 — see working-agreements.md)
1. **Parallel implementer subagents in isolated worktrees sync the integration branch first**
   (`git merge <sprint-branch>` before work) — worktrees are cut from the branch base, not tip.
2. **Config referencing a live vendor resource id carries a drift check** — probe it resolves to
   live data when added/changed + at the review spot-check; standing health signal filed as
   **STORY-070**.

## Tooling friction (noted, no amendment)
- `lint-imports` crashes on Windows cp1252 console output (cosmetic; `PYTHONIOENCODING=utf-8`
  works around it). Flag if it recurs.

## Follow-ups filed this sprint
- **063–067** backend data gaps (proposal enrichment, observation code/type, maintenance
  title+delete, publication metadata, component grouping + uptime buckets).
- **068** `useAvailability` parallelism flake · **069** redesign consolidation minors ·
  **070** live vendor-id drift health check (from amendment ②).

## Notes
- Sprint 35 (STORY-017 deployment) remains parked/unmerged, unaffected.
- PO accepted the redesign as-is: page `h1`s stay "Dashboard"/"Maintenance" (nav-label invariant);
  Check History cap stays 1000.
