# Sprint 32 — Review

**Goal:** the two-grain Availability tab (STORY-015d) + the Dashboard sample-switch toggle (STORY-049).
**Branch:** `sprint-32` (from main @ `3785f12`). Committed 5 pts; both stories Done.
**DoD surface:** three frontend gates (`npm test` / `npm run build` / `npm run lint`); backend
untouched all sprint (empty diff over backend paths from the sprint-31 gate-green state `61d786a`,
re-checked per story), so the six-gate backend evidence holds by baseline.
**Wiki compile pass:** 13/13 articles CURRENT at review HEAD, 0 broken links (mechanical sweep).

## STORY-015d — Availability tab (3 pts) — recommend ACCEPT

What was built: `pages/AvailabilityPage.tsx` + `features/availability/` (useAvailability hook on
the shared `useFetch`, `windowToRange` tz-seam, `format.ts`), `mocks/handlers/availability.ts`,
topology/availability DTOs + client fns. Commits `8de1e1b..c2e865c` (T1–T5), wiki `7e4fc68`,
gates `400331f`, then fix loop `b827210..ae53070`.

AC evidence:
- **AC1 (two grains: rollup + per-signal drill-down):** component rows show rollup availability%,
  completeness%, verdict counts; row expands (real button, `aria-expanded`) to per-signal children
  (name + signal_key + per-signal values). Spec reviewer RAN the tests and traced them to the AC.
  LIVE: expanding "HTTP Check" reveals its child signal with real data.
- **AC2 (window selector drives tz-aware refetches, MSW asserts actual params):** 24h/7d/30d
  segmented control; test captures the actual `since`/`until` MSW received (trailing-Z tz-aware,
  span matches the preset, values genuinely change on selection).
- **AC3 (degenerate windows render honestly):** null pct → "no data" (never 0%/NaN, empty bar);
  tested at both grains; zero-signal component renders its all-None rollup with no dead-end
  expand control.
- **AC4 (states + per-tab pattern + bars never sole carrier):** shell Loading/Empty/Error+retry;
  built on shared `useFetch` + per-feature MSW module; bar `aria-hidden`, value always text.

Pipeline: spec PASS + quality APPROVE first-pass (reviewer traced the refetch-identity chain and
the stale-response guard). Then the orchestrator found a **percent-scale defect at review prep**
(demoing live): the wire values are 0–1 fractions but display + fixtures assumed percent-scale —
146 green tests validated the wrong scale ("1.00%" for fully-up). Fix loop (attempt 2): ×100 at
the two display seams, fixtures converted to true wire scale, assertions rewritten (none deleted),
plan contract annotated. Focused Opus second-pass: PASS (independent grep, backend ground-truth
check, no remaining scale assumption). Root cause was a planning-precision miss (contract pinned
types but not units/scale) — carried to retro.

Gate: `npm test` 146/146, build, lint — exit 0 at clean HEAD `ae53070` (and previously `400331f`).
**Live demo (verified via Playwright on the running stack):** Availability tab renders
**100.00% / 8.33%** matching the real API fractions `1.0 / 0.0833`; drill-down works.

Open minors (non-blocking): degenerate rollup shows literal zero counts next to "no data"
(taste); backlog candidates flagged: no live-clock window re-slide; bar color not
threshold-mapped (accent only).

## STORY-049 — Dashboard sample-switch toggle (2 pts) — recommend ACCEPT

What was built: `SampleModeDTO` + `getSampleMode`/`putSampleMode` (new typed `putJson` helper),
`mocks/handlers/sampleMode.ts`, `features/dashboard/useSampleMode.ts`, Dashboard switch + warning.
Commits `e332e2b` (T1), `63886bc` (T2), `4e591dd`/`a06a85d`/`1b9ef7d` (T3 wiki + gates).

AC evidence:
- **AC1 (switch reflects API state on load; accessible):** real `role="switch"` +
  `aria-checked`, text-labeled, keyboard-operable; load off/on/loading cases MSW-tested.
  LIVE: the switch renders on the Dashboard (off, matching `GET /sample-mode` → `enabled:false`).
- **AC2 (toggle PUTs; success reflects response, failure never flips):** no optimistic flip
  (response-derived state; an effect-synced version was rejected for a real one-frame race);
  PUT body asserted via MSW; failure test pins `aria-checked` unchanged + error affordance.
- **AC3 (visible ON-warning):** "sample mode — signals recorded as DOWN", `role="status"`,
  health-degraded (amber) token + icon + ink text — never color-alone; red deliberately reserved
  for real down-status.
- **AC4 (DTO check at planning):** done at planning — `{enabled: bool}` verified against
  `sample_mode/models.py`.
- **AC5 (gates):** `npm test` 146/146 (+21 new), build, lint — exit 0 at clean HEAD `1b9ef7d`.

Pipeline: 2 pts → gate-only (no reviewers, per the default pipeline). TEMPORARY-feature duty
honored: `sample-mode.md`'s REMOVAL inventory now lists every frontend file/seam this story added
(including the shared `putJson` caveat), so the removal recipe stays complete.

## Demo steps (stack is running)

1. http://localhost:5173/availability — two-grain tab against the real backend; click the
   component row to drill down; switch 24h/7d/30d.
2. http://localhost:5173/ — flip "Sample mode" ON: warning appears; the live loop then records
   incoming observations as DOWN (identifiably simulated) → within ~2 min the degrade proposal
   appears on the Approvals tab → approve → Statuspage publish → flip OFF to recover. (The full
   STORY-048 demo loop, now drivable from the UI.)
3. `curl http://localhost:8000/api/v1/availability/component/http-check` — raw fractions on the
   wire; the tab shows them ×100.

## Incidents (retro input)

1. **Scale defect passed both reviewers + 146 tests** — fixtures encoded the same wrong assumption
   the plan implied; caught only by demoing against live data. Planning's DTO check needs
   units/scale, and consumer stories likely need a live-smoke step now that a stack exists.
2. **Opus session limit killed a reviewer mid-run again** (2nd sprint running); fresh re-dispatch
   after reset passed.
3. **Live loop crashed on a transient Grail SSL timeout** during the PO-requested stack run →
   STORY-050 (draft defect) filed.
4. Both implementer dispatches clean, no watchdog stalls — first sprint since 29 without a
   tail-recovery; the article-by-article wiki-commit agreement held.

## Verdicts (PO)

- STORY-015d (3 pts): _pending_
- STORY-049 (2 pts): _pending_
