---
id: STORY-054
title: Flaky frontend DoD gate — CheckHistoryPage 1000-cap test times out under npm test parallelism
type: defect
---

## Context (found during sprint-37 STORY-046 gate verification, 2026-07-06)
The canonical frontend DoD command `npm test` (Vitest with default file parallelism)
INTERMITTENTLY fails with exit 1 because a single PRE-EXISTING test —
`frontend/src/pages/CheckHistoryPage.test.tsx::"caps rendering at the latest 1,000
observations with a visible cap notice"` (line ~200, `TOTAL = 1500`) — times out at
Vitest's default `5000ms` when the machine's CPUs are saturated by parallel test files.

Proven a resource-contention false-red, NOT a code regression:
- The test is UNTOUCHED by sprint 37: `git diff sprint-37-start..HEAD -- frontend/src/pages/CheckHistoryPage.*` is empty.
- In ISOLATION it passes in ~3.6s (11 passed): `npx vitest run src/pages/CheckHistoryPage.test.tsx` → exit 0.
- The FULL suite single-threaded passes clean: `npx vitest run --no-file-parallelism` → 34 files / 230 passed, exit 0.
- It is INTERMITTENT: the same `npm test` command passed green during STORY-052's gate
  run earlier the same day (225 passed) and failed during STORY-046's run (1 failed /
  229 passed) — pure CPU-contention timing, machine-dependent.

This is the frontend analogue of the 2026-07-02 DB-concurrency false-red agreement
(a contention-induced red is invalid; re-run cleanly). But a DoD gate that flakes on
adequate hardware undermines the mechanical-floor principle — the gate must be
trustworthy. STORY-046's real signal was taken from the clean single-threaded run and
recorded as such, with this defect filed so `npm test` itself becomes reliable.

## Description
Make the frontend DoD gate deterministic on a contended machine. Candidate fixes (decide
at refinement): (a) raise the `testTimeout` for the 1000-cap render test specifically (it
mounts 1500 rows — a legitimately heavy render); (b) reduce the fixture size / assert the
cap without rendering the full 1500; (c) pin Vitest's `poolOptions`/`maxWorkers` (or
`fileParallelism`) in `vite.config.ts` so the suite doesn't starve itself of CPU; or a
combination. Preserve what the test proves (the latest-1000 cap + the visible cap notice).

## Acceptance Criteria (draft — refine before scheduling)
- [ ] AC1: `npm test` (the canonical DoD command, unchanged) passes with exit 0
      DETERMINISTICALLY — run it N consecutive times (e.g. 5) with no failure — on this
      machine, without `--no-file-parallelism`.
- [ ] AC2: the CheckHistoryPage cap behavior is still asserted (latest-1000 cap + visible
      cap notice) — no coverage lost.
- [ ] AC3: three-gate frontend DoD green; backend untouched (empty backend diff).

## Open Questions
- Which fix (timeout bump vs fixture-size reduction vs parallelism pin vs combo) — decide
  at refinement, informed by whether other tests also flirt with the 5000ms ceiling.

## History
- 2026-07-06: filed as a defect during sprint-37 STORY-046 gate verification. The flake
  produced a false-red on `npm test`; the valid green signal was taken from the clean
  single-threaded run per the 2026-07-02 contention precedent. Retro input for sprint 37.
