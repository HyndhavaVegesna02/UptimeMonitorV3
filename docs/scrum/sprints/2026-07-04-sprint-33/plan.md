# Sprint 33 — Plan

**Dates:** starts 2026-07-04.
**Goal:** the Check History tab (STORY-015e) + the Publications tab (STORY-015g) — the two
read-only audit surfaces, completing five of the six tabs.
**Branch:** `sprint-33` (tag `sprint-33-start` @ `350e928`). Committed: 5 pts (velocity mean 5.0).
**Mode:** in-process — Sonnet 5 implementer at high effort; STORY-015e (3 pts → Opus spec +
quality reviewers); STORY-015g (2 pts → implementer + DoD gate).
**Execution order:** 015e first (risk: two selectors, volume handling, NEW observation-health
badge mapping), then 015g (clean closer on the established read-tab pattern).
**Operational note:** the local stack (DB :55432 + uvicorn :8000 + live loop + Vite :5173) runs
detached alongside implementation per PO standing request — do not manage or depend on those
processes; MSW is the only test I/O edge.

All work is inside `frontend/`. **No backend source change.** Three frontend gates (`npm test` /
`npm run build` / `npm run lint` from `frontend/`) exit 0 on a clean committed tree; six backend
gates hold by the empty-diff baseline. Tokens + shell primitives only; no raw hex. Mirror the
per-tab pattern (015b read / 015d parameterized-fetch): page in `pages/`, feature hook on the
shared `src/lib/useFetch.ts` (STABLE fetcher identity — module-scoped fn, or `useCallback` over a
`useMemo`'d param object, the 015d-sanctioned pattern), per-feature MSW module composed into
`mocks/handlers/index.ts`.

TDD cadence: failing test → watch it fail → minimal code → green → **commit after every green
step**, staging only touched files (never `git add -A`), branch verified `sprint-33` first.

## Verified API contracts (pinned at planning against producing code + LIVE wire samples —
## do not assume beyond these; fixtures MUST derive from the samples below, 2026-07-04 agreement)

- `GET /api/v1/history?signal_key=<key>&since&until` → `list[ObservationDTO]`
  (`backend/src/api/v1/history/models.py`), **newest-first**, NO pagination. Exactly ONE
  `signal_key` REQUIRED; `since`/`until` optional ISO-8601, tz-aware only (naive → 422; default
  window last 24h). Fields: `{ signal_key: string, observed_at: string (ISO UTC),
  health: string, location: string, latency_ms: number | null }`.
  **UNITS/ENUMS (verified at code, not names):** `latency_ms` = INTEGER MILLISECONDS or null
  (`core/domain/signal.py::SignalObservation.latency_ms`); `health` = the OBSERVATION vocabulary
  `"up" | "down" | "degraded"` (`signal.py::Health`, serialized via `.value` in
  `history/service.py`) — **NOT** ComponentStatus: `api/statusMapping.ts::toHealthStatus` does
  NOT apply (it would map "up" → unknown). `location` is a raw vendor id string (live:
  `"SYNTHETIC_LOCATION-0000000000000060"`) — render as-is, mono.
  LIVE SAMPLE (2026-07-04, fixtures derive from this shape/scale):
  `{"signal_key":"http-check","observed_at":"2026-07-03T13:29:17.931000Z","health":"up",
  "location":"SYNTHETIC_LOCATION-0000000000000060","latency_ms":571}` (120 rows, newest-first
  confirmed).
- Signal enumeration for the selector: `GET /api/v1/topology` → `list[ComponentTopologyDTO]`
  (already typed in `api/types.ts` + `getTopology()` from 015d — REUSE, do not re-add).
- `GET /api/v1/publications` → `list[PublicationDTO]`
  (`backend/src/api/v1/publications/models.py`), **newest-first, at most 50** (`list_recent`
  cap — the cap must be VISIBLE in the UI, not silent). Fields: `{ id: number,
  component_id: string, status: string, published_at: string (ISO UTC),
  proposal_id: number | null }`.
  **ENUMS:** `status` = ComponentStatus vocabulary (`"operational" | "degraded" |
  "partial_outage" | "major_outage"`, via `.value`) → the existing `toHealthStatus` DOES apply.
  `proposal_id` null → render honestly (em-dash), never a sentinel. LIVE endpoint currently
  returns `[]` (nothing published yet) — the empty state is the REAL initial state; fixture
  values derive from the backend's own publications test fixtures
  (`backend/tests/` — read them) per the real-sample agreement.
- No other endpoints. No pagination params exist on either endpoint.

## STORY-015e — Check History tab (3 pts) — AC1–AC4

- [x] **T1 — Types + client + MSW module (AC1 plumbing).** Add `ObservationDTO` to
      `api/types.ts` (exact shape incl. `latency_ms: number | null`). Add
      `getHistory(params: { signal_key: string; since: string; until: string }):
      Promise<ObservationDTO[]>` to `api/client.ts` (query-string encode all three; reuse
      `getJson`/`ApiError`). Add `mocks/handlers/history.ts` — fixtures DERIVED from the live
      sample above (fractional-second ISO UTC timestamps, integer-ms latencies, raw vendor
      location strings, health values from the observation vocabulary incl. at least one
      `"down"`, one `"degraded"`, and one `latency_ms: null`), newest-first; compose into
      `handlers/index.ts`. Client unit tests assert URL + exact query params via MSW.
- [x] **T2 — Observation-health badge mapping (AC3).** A small mapper (e.g.
      `features/history/observationHealth.ts`) from `"up" | "down" | "degraded"` (else →
      unknown) onto the SAME health-token statuses `StatusBadge` consumes — deliberately
      SEPARATE from `toHealthStatus` (different producing vocabulary; a doc-comment states
      why both exist). Unit-test all four branches. Do NOT modify `statusMapping.ts` (its
      contract change would ripple into Dashboard/Publications).
- [x] **T3 — `useHistory` hook (AC1, AC2).** `features/history/useHistory.ts`: for
      `{ signalKey, range }`, fetch `getHistory(...)` through the shared `useFetch` with the
      015d identity pattern (`useCallback([signalKey, range])`; consumers `useMemo` the range
      from the preset). Signal list comes from `getTopology()` (flatten components → signals;
      reuse the existing typed client fn). Default signal = first in the enumeration; default
      window = 24h. MSW tests: success; signal change → refetch with the NEW `signal_key`
      asserted; window change → refetch with NEW tz-aware `since`/`until` asserted; error.
- [x] **T4 — Page render (AC1, AC3).** `pages/CheckHistoryPage.tsx` (+ CSS mirroring the
      established page conventions): dense hairline-separated chronological rows —
      `observed_at` (mono), `StatusBadge` via the T2 mapping, `latency_ms` (mono, rendered
      `571 ms`; null → em-dash, NEVER `0 ms` or `null ms`), `location` (mono, as-is). Signal
      selector (accessible native `<select>` or listbox semantics, labeled) + window selector
      (24h/7d/30d, mirror 015d's segmented control). Rows render newest-first exactly as the
      API returns them (do NOT re-sort — the ORDER is the contract). MSW tests: rows render
      with mapped badges (up/down/degraded), null-latency em-dash, order preserved.
- [ ] **T5 — Volume cap + states (AC4).** Render at most the latest 1,000 rows; when the
      response exceeds that, a visible note "showing latest 1,000 of N observations" (tested
      with a >1,000-row generated fixture). Loading (`LoadingState`), empty ("no observations
      in this window", `EmptyState`), error+retry (`ErrorState`); Panel `headingLevel="h1"`.
      Tests for each state.
- [ ] **T6 — Gates + blast radius (015e).** Three frontend gates exit 0 on a clean committed
      tree. Mechanical wiki staleness sweep; update every flagged article (expect at least
      `frontend-zone.md`), **committing article-by-article**.

## STORY-015g — Publications tab (2 pts) — AC1–AC3

- [ ] **T1 — Types + client + MSW (AC1 plumbing).** `PublicationDTO` in `api/types.ts`;
      `getPublications(): Promise<PublicationDTO[]>` in `api/client.ts`;
      `mocks/handlers/publications.ts` with fixtures derived from the backend's publications
      test fixtures (ComponentStatus values incl. a non-operational one; a `proposal_id: null`
      case), newest-first, composed into `index.ts`. Client unit test via MSW.
- [ ] **T2 — Hook + page (AC1, AC2, AC3).** `features/publications/usePublications.ts` =
      `useFetch(getPublications)` (module-scoped fetcher — plain read tab, no params).
      `pages/PublicationsPage.tsx`: changelog rows newest-first — `published_at` (mono),
      `component_id`, single `StatusBadge` via the EXISTING `toHealthStatus`, `proposal_id`
      (mono; null → em-dash). The 50-item cap visible in the header/copy (e.g. "latest 50
      publications"). Loading / empty ("nothing published yet") / error+retry via shell
      primitives; Panel `headingLevel="h1"`. MSW tests: render (incl. null-proposal and
      non-operational status), empty, error+retry; assert the cap copy is present.
- [ ] **T3 — Gates + blast radius (015g).** Three gates exit 0 on a clean committed tree.
      Mechanical sweep; update flagged articles (expect `frontend-zone.md`),
      article-by-article commits.

## Conventions checklist (held at quality review)
- Tokens, not hex; status never color-alone (badge dot + ink label); machine values (timestamps,
  latency, ids) in the mono token; ink ≥4.5:1 both themes.
- MSW is the ONLY mock; tests assert accessible roles/text + the ACTUAL requests MSW received
  (exact `signal_key`/`since`/`until`). Tests that lie = blocking.
- **Fixtures derive from real samples (2026-07-04):** history fixtures from the live sample in
  this plan; publications fixtures from the backend's own test fixtures. Invented
  plausible-looking values are a review finding.
- Null handling explicit and tested: `latency_ms: null` → em-dash (never `0 ms`);
  `proposal_id: null` → em-dash (no sentinel — 2026-06-28 agreement kin).
- Every list surface has a tested empty state; 015e additionally tests the >cap volume note.
- A contract change rewrites tests, never deletes coverage (2026-06-29).
- Stable fetcher identity (015d pattern); double-test convention — the fetch machine is tested
  at `useFetch` level, tabs test their own behavior only.
- tz-discipline: reuse `windowToRange` from 015d for since/until (do NOT duplicate it — the
  parallel-shape agreement); its tests already pin tz-awareness.
- Scoped staging; commit-after-green; TS strict; no `eslint-disable`; doc-comment new public
  hooks/modules (esp. WHY `observationHealth` is separate from `toHealthStatus`).

## Guardrails (implementer)
- Build to THIS plan + the story files (`STORY-015e-check-history-tab.md`,
  `STORY-015g-dashboard...` — see backlog paths) + dossier §17 — never chat history. No backend
  changes; no `.scrum/` writes; no reviewers/merge; don't touch the running local processes.
- Genuine ambiguity → STOP with the exact question. Effort > 3× estimate → STOP.
- Report per story: steps + commit SHA each; gates + exits + tails; wiki articles updated;
  design decisions; candidates noticed-but-not-done.

## Sequencing rationale
015e first per risk-early: it carries the new mapping, two coupled selectors, and the volume
decision; 015g is a minimal read tab whose only nuance (cap visibility, null proposal_id) is
already pinned. Within 015e: plumbing → mapping (pure, cheap) → hook (highest uncertainty —
coupled selector refetches) → render → volume/states → gates+wiki. The orchestrator runs the
live render-vs-wire spot check (2026-07-04 agreement) at review prep for BOTH stories.
