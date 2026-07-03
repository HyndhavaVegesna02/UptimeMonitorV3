# Sprint 32 — Plan

**Dates:** starts 2026-07-03.
**Goal:** the two-grain Availability tab (STORY-015d) + the Dashboard sample-switch toggle (STORY-049).
**Branch:** `sprint-32` (tag `sprint-32-start` @ `3785f12`). Committed: 5 pts (velocity mean 5.0).
**Mode:** in-process — Sonnet 5 implementer at high effort; STORY-015d (3 pts → Opus spec + quality
reviewers, full pipeline); STORY-049 (2 pts → implementer + DoD gate).
**Execution order:** STORY-015d first (highest risk: new two-grain drill-down pattern, window
selector, degenerate-window handling), then STORY-049 (small closer).
**Operational note:** the STORY-042 local stack (throwaway DB + uvicorn :8000 + live loop + Vite
dev server) runs alongside implementation per PO request — the implementer does NOT manage those
processes and must not depend on them in tests (MSW is the only test I/O edge).

All work is inside `frontend/`. **No backend source change.** Six backend DoD commands stay green
untouched (empty-diff baseline); the three frontend commands (`npm test` / `npm run build` /
`npm run lint`, from `frontend/`) exit 0 on a clean committed tree. Reuse the shell's tokens +
primitives; no new raw hex. Design reference: `DESIGN-linear.app.md` (guide, not copy). Mirror the
per-tab pattern set by 015b/015c: page in `pages/`, feature hook in `features/<tab>/` on the shared
`src/lib/useFetch.ts`, per-feature MSW module in `mocks/handlers/` composed into
`mocks/handlers/index.ts`.

TDD cadence: failing test → see it fail → minimal code → green → **commit after every green step**,
staging only touched files (never `git add -A`), branch verified `sprint-32` before each commit.

## Verified API contracts (verified at planning against backend source — do not assume beyond these)

- `GET /api/v1/topology` → `list[ComponentTopologyDTO]`
  (`backend/src/api/v1/topology/models.py`): `{ id: string, name: string, signals:
  [{ signal_key: string, name: string, interval_seconds: number | null, component_id: string }] }`.
  Signals sorted server-side; a component can have zero signals.
- `GET /api/v1/availability/component/{component_id}?since&until` → `ComponentAvailabilityDTO`
  (`backend/src/api/v1/availability/models.py`): `{ component_id: string, rollup: AvailabilityDTO,
  signals: SignalAvailabilityDTO[] }`.
  `AvailabilityDTO`: `{ availability_pct: number | null, completeness_pct: number | null,
  total_verdicts: number, passing_verdicts: number, maintenance_verdicts: number,
  gap_verdicts: number, distinct_locations: number, window: string, computed_at: string (ISO) }`.
  `SignalAvailabilityDTO` = `AvailabilityDTO` + `{ signal_key: string }`. Children sorted by
  `signal_key`; zero-signal component → `signals: []` + all-None/zero rollup (NOT a 500).
  `since`/`until` are optional ISO-8601 strings (default: last 24h ending now); **naive datetimes
  are rejected 422** — always send tz-aware ISO (trailing `Z`). Status: **200** ok · **422**
  malformed/naive `since`/`until` · **404** unknown `component_id` · **409**
  `SignalIntervalUnconfiguredError` (unreachable once seeded — treat as a generic error).
- `GET /api/v1/sample-mode` → `SampleModeDTO { enabled: boolean }` (`enabled: false` when never
  set). `PUT /api/v1/sample-mode` body `{ enabled: boolean }` → `SampleModeDTO` (idempotent;
  returns the new state). No 4xx beyond FastAPI's own 422 on a malformed body.

## STORY-015d — Availability tab (3 pts) — AC1–AC4

- [ ] **T1 — Types + client + MSW module (AC1 plumbing).** Add `TopologySignalDTO`,
      `ComponentTopologyDTO`, `AvailabilityDTO`, `SignalAvailabilityDTO`, `ComponentAvailabilityDTO`
      to `frontend/src/api/types.ts` (mirror the verified shapes EXACTLY, incl. `| null` fields).
      Add to `frontend/src/api/client.ts`: `getTopology(): Promise<ComponentTopologyDTO[]>` and
      `getComponentAvailability(componentId: string, range: { since: string; until: string }):
      Promise<ComponentAvailabilityDTO>` (query-string encode `since`/`until`; reuse the existing
      `getJson`/`ApiError` wrapper — status must stay readable). Add `mocks/handlers/availability.ts`
      (handlers for BOTH endpoints + fixtures: a multi-signal component, a single-signal component,
      a zero-signal component with the all-None rollup, and a null-pct no-data window case), composed
      into `mocks/handlers/index.ts`. Unit tests: client functions hit the right URL + query params
      via MSW.
- [ ] **T2 — Window range helper (AC2).** Pure helper (e.g.
      `features/availability/windowRange.ts`): `windowToRange(preset: '24h' | '7d' | '30d',
      now?: Date): { since: string; until: string }` returning tz-aware UTC ISO strings (trailing
      `Z`), `until` = now, `since` = now − preset. Unit-test all three presets + that output parses
      tz-aware (this is the tz-discipline seam — a naive string here becomes a backend 422).
- [ ] **T3 — `useAvailability` hook (AC1, AC2).** `features/availability/useAvailability.ts`:
      for a given range, fetch `getTopology()` then `Promise.all` of
      `getComponentAvailability(c.id, range)` per component; return the merged
      `{ topology, availabilityByComponent }` through the shared `useFetch` state machine
      (loading | error | success, `retry`). The hook must REFETCH when the range changes — if
      `useFetch` does not re-run on a changed fetcher, extend it minimally (deps/key param) and
      REWRITE its tests for the new contract (never delete; 2026-06-29 agreement) — or key the
      consumer remount; choose the cleaner and say why in the report. MSW tests: success (merged
      shape), one-component-fetch failure → error state (Promise.all rejects — that is acceptable
      whole-tab error behavior), and range-change → refetch with the NEW query params asserted.
- [ ] **T4 — Page render: two-grain rows (AC1).** `pages/AvailabilityPage.tsx` (+ CSS module
      mirroring `DashboardPage.css` conventions): per component a headline row — name,
      rollup `availability_pct` as the headline (mono, consistent precision, e.g. `99.87%`),
      `completeness_pct`, verdict counts (total/passing/maintenance/gap) as auditability detail,
      and a tokens-styled horizontal bar (width = availability%, `var(--…)` tokens only; the
      numeric value is ALWAYS present as text — the bar is never the sole carrier). Row expands
      (real `<button>`, `aria-expanded`, keyboard-operable, visible accent focus) to per-signal
      child rows: signal `name` + `signal_key`, its own availability% / completeness% / counts /
      bar. Zero-signal component renders its (all-None) rollup honestly with no expandable children.
      MSW tests: multi-signal expand shows children with per-signal values; zero-signal case.
- [ ] **T5 — Window selector + degenerate windows + states (AC2, AC3, AC4).** Window selector
      (segmented control / button group; ≥40px targets; `aria-pressed` or radio semantics;
      keyboard-operable) with 24h / 7d / 30d presets driving the hook's range. Null
      `availability_pct`/`completeness_pct` renders an explicit "no data" treatment (muted ink
      token + em-dash or "no data" label — NEVER `0%`, never `NaN`, no crash; bar renders empty).
      Loading (`LoadingState`), empty topology ("no components", `EmptyState`), error+retry
      (`ErrorState`) via shell primitives; Panel `headingLevel="h1"`. MSW tests: selector change
      asserts the actual `since`/`until` query params sent (AC2's named assertion); null-pct row
      shows "no data" not 0%; loading/empty/error+retry each driven and asserted.
- [ ] **T6 — Gates + blast radius (015d).** All three frontend gates exit 0 on a clean committed
      tree. No CLAUDE.md/DoD change (no new command). Run the mechanical wiki staleness sweep;
      update every article it flags (expect at least `frontend-zone.md` — client/types/handlers/new
      feature dir), **committing article-by-article** (2026-07-03 agreement).

## STORY-049 — Dashboard sample-switch toggle (2 pts) — AC1–AC5

- [ ] **T1 — Types + client + MSW (AC4 plumbing).** Add `SampleModeDTO` to `types.ts`. Client:
      `getSampleMode(): Promise<SampleModeDTO>` and `putSampleMode(enabled: boolean):
      Promise<SampleModeDTO>` — add a typed PUT helper mirroring the existing POST wrapper
      (network/non-2xx/malformed-body → `ApiError`). `mocks/handlers/sampleMode.ts` (GET + PUT
      handlers, mutable fixture state) composed into `index.ts`. Client unit tests via MSW
      (incl. PUT body assertion).
- [ ] **T2 — Toggle + warning on the Dashboard (AC1, AC2, AC3).** `features/dashboard/useSampleMode.ts`
      (load via `useFetch(getSampleMode)`; expose a `setEnabled` that PUTs and reflects the
      RESPONSE state on success — no optimistic flip). On `DashboardPage`: a real switch
      (`role="switch"` + `aria-checked`, or a native checkbox styled as one), text-labeled
      ("Sample mode"), keyboard-operable, ≥40px target, visible accent focus; disabled while the
      PUT is in flight. While ON: a clearly visible warning — "sample mode — signals recorded as
      DOWN" (or equivalent wording) — styled with health/warning TOKENS (dot/icon + ink label;
      never color-alone, no raw hex). A failed PUT surfaces the shell's error affordance
      (inline error near the switch is fine) and the switch does NOT show the flipped state.
      MSW tests: initial state rendered from GET (both off and on); toggle success (assert the
      actual PUT body `{enabled: true}` MSW received + warning appears); toggle-off success
      (warning disappears); PUT failure (error shown, `aria-checked` unchanged); load-state case.
- [ ] **T3 — Gates + blast radius (049).** Three frontend gates exit 0 on a clean committed tree.
      Run the mechanical sweep; expect at least `frontend-zone.md` AND `sample-mode.md` — the
      REMOVAL inventory in `sample-mode.md` MUST gain every frontend file/seam this story adds
      (it is a TEMPORARY feature; the inventory is its removal recipe). Commit article-by-article.

## Conventions checklist (held at quality review)
- **Tokens, not hex;** status/warning is dot/icon + ink label, never color-alone; health color never
  as text color; ≥4.5:1 ink both themes; bars/switches carry no meaning that text doesn't also carry.
- **Tests drive real behavior:** MSW at the network boundary is the ONLY mock — never mock
  `useFetch`/feature hooks/pages under assertion; assert via accessible roles/text and the actual
  requests (query params, PUT body) MSW received. Tests that lie / assert nothing = blocking.
- **A contract change rewrites its tests, never deletes coverage** (2026-06-29) — applies
  especially to any `useFetch` extension in 015d/T3.
- **Every list surface has a tested empty state** (2026-06-25): empty topology; zero-signal
  component; "no data" null-pct treatment (the frontend twin of the empty-input agreement).
- **Numbers:** mono for figures, consistent precision, explicit null treatment — never `NaN%`,
  never `0%` standing in for "no data".
- **tz-discipline:** every `since`/`until` sent is tz-aware ISO (the backend 422s naive input);
  `windowToRange` is the single seam and is tested for it.
- **Double-test convention (Sprint-26 carry-forward):** the fetch state machine is tested at the
  `useFetch` level; tab tests assert the tab's own behavior — do NOT re-assert the generic machine.
- Scoped staging; commit-after-green; TS strict; no `eslint-disable`; doc-comment new public
  hooks/modules mirroring the shell's style; follow existing import/naming/structure patterns.

## Guardrails (implementer)
- Build to THIS plan + `docs/scrum/stories/STORY-015d-availability-tab.md` +
  `docs/scrum/stories/STORY-049-dashboard-sample-switch-toggle.md` + dossier §17/§11 — never chat
  history. Do NOT change backend source (six backend gates stay green by baseline). Do NOT write
  `.scrum/` board state; do NOT run reviewers or merge — the orchestrator owns the back half.
- Do NOT touch the running local-stack processes (DB container, uvicorn, live loop, Vite dev
  server); tests must pass with none of them running (MSW only).
- Genuine ambiguity → STOP and report the exact question. Effort > 3× estimate → STOP.
- Report: steps done + commit SHA each; every gate command + exit + tail; design decisions
  (esp. the T3 refetch approach); anything noticed-but-not-done; or the blocking question.

## Sequencing rationale
015d first per the risk-early rule — it introduces the two-grain drill-down pattern, a window
selector driving refetches, and degenerate-data rendering; a blocker there leaves runway. Within
015d: plumbing (T1) → the pure range seam (T2) → the composite hook (T3, the highest-uncertainty
piece — topology + N availability calls + refetch-on-range-change) → render (T4) → selector/states
(T5) → gates+wiki (T6). 049 is a self-contained 2-point closer reusing the exact plumbing shape
just exercised, with its own gates+wiki tail (T3) so each story is independently Done.
