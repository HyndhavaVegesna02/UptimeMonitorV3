# Sprint 41 — Quick cleanup (068 + 069 + 070)

## STORY-068 (defect, 2pt, gate-only) — deterministic frontend gate
`frontend/src/features/availability/useAvailability.test.tsx` throws ~18 uncaught exceptions under
`npm test` file-parallelism (clean serialized). Diagnose: real unhandled-rejection / act()-leak /
state-update-after-unmount in the hook or test, vs a pure contention timeout. `useAvailability` fans
out `getComponentAvailability` per component + per-component segment `getHistory`. Fix accordingly
(await settle, cancellation guard, proper cleanup). AC: `npm test` (default parallelism) passes
deterministically across repeated runs incl. under load; if a real hook leak, add a regression test.
Frontend-only.

## STORY-069 (chore, 3pt, full pipeline) — redesign consolidation minors
- **Extract `frontend/src/features/history/uptimeSegments.ts`** (`buildUptimeSegments` +
  `MAX_UPTIME_SEGMENTS`) and consume from BOTH `dashboard/useComponentUptime.ts` and
  `availability/segments.ts` (currently byte-identical copies — worktree-isolation duplication).
- **Fix stale docstrings** in `dashboard/useTopology.ts` + `dashboard/useComponentSignals.ts` that
  reference the removed `useSignalOptions.ts`/`useHistory.ts`.
- **Token/a11y nits:** add a `--fs-stat` token for the big stat number (SummaryCard/Availability);
  tokenize `ApprovalCard` chip font-size + the Approvals badge radius; add `aria-controls` on the
  Dashboard/Availability row expanders. Token-only colors; keep tests green.
AC: dups removed (single shared module, both consumers use it), docstrings correct, nits applied;
frontend three-gate green. Frontend-only.

## STORY-070 (feature, 3pt, full pipeline) — vendor-id drift health check
**Mechanism (decided): loud WARNING at live-loop startup, NOT fail-fast.** At loop start, for each
configured monitor `native_id`, run a bounded DQL count over a recent window; if 0 rows, log a
prominent WARNING naming the monitor. Must stay pure-core / mockable-edge (probe is an adapter/
composition concern; core stays vendor-free). AC: a 0-rows id → a loud, testable signal; a healthy
id → none; covered with a FAKED executor (no live Dynatrace call); wired into the loop startup path.
Backend six-gate. Do NOT block startup on a dead monitor.

## Conventions / execution
- 070 backend: DB-gated tests use `migrated_db`; the live writers are PAUSED so a SINGLE pytest
  invocation reuses `DATABASE_URL` (55432; `+psycopg` DIRECT for alembic). No second DB.
- Frontend (068/069): token-only colors; a11y (dot+text, reduced-motion); tests by role/name; MSW
  only edge.
- Backend six-gate / frontend three-gate DoD. Commit per green step; scoped staging. Do NOT edit
  `.scrum/`. Wiki sweep at DoD (frontend-zone for 069; an ingest/loop article for 070 if code_refs hit).
