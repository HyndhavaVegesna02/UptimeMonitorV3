# Sprint 61 — Plan

**Goal:** Harden and refine the operator cockpit delivered in sprints 59–60. Fix the
confirmed correctness and design defects surfaced by the 2026-07-22 design-QA review —
on the real `/api/v1` backend, keeping the sprint-59 design system. Frontend only; no
placeholders regress.

**Mode:** in-process (PO decision 2026-07-22 — the `/yourteam` arg said "external", but
the PO's standing directive after the sprint-60 external rejection is "you only
implement"; PO reaffirmed in-process at planning). Orchestrator dispatches
`yt-implementer` per story (TDD, commit per green step); 3+ pt stories get `yt-spec-reviewer`
∥ `yt-quality-reviewer`; all stories get the DoD gate + reality gate.

**Branch:** `sprint-61`, cut from the sprint-60 tip `a1c9b12` (the unmerged
`ui-prototype` / new-frontend line). `main` untouched. Start tag `sprint-61-start`.

**Provenance:** every story below traces to a finding in the 2026-07-22 design-QA review
that was **verified against code + the live app** before entering scope. False /
already-done / external findings from that review were triaged OUT (see "Triaged out"
at the bottom) and are NOT in this sprint.

**Plan-verifier: SKIPPED (token economy, PO-approved 2026-07-15).** This is a purely
internal frontend sprint — UI refinement against the **existing, already-verified**
`/api/v1` DTOs the cockpit already consumes (no new contract, no adapter/vendor path, no
units/scale logic, not external mode). Per the rule, purely-internal-UI sprints skip the
adversarial pre-lock dispatch. The one story that adds a route (STORY-143) consumes the
already-live `GET /availability/component/{id}` contract that STORY-129 verified this
sprint-line; no new backend contract is introduced.

**NON-NEGOTIABLE:** frontend only. No backend / config / infra / API / DynamoDB /
pipeline edits, no new Docker resources. Design FRESH against the sprint-59 design system
with the mandated skills — do NOT reuse the rejected external work
(tag `scrap/sprint-60-external-rejected`).

**Mandatory skills** in every implementer + reviewer brief: `ui-ux-pro-max` (live copy at
`.agents/skills/ui-ux-pro-max`), `web-design-guidelines`, `vercel-react-best-practices`,
`emil-design-eng`, `design-system`.

**Gates:** mid-sprint scoped `yt_gate.py --only npm`; sprint close = full 8-command gate
on the final HEAD (per the sprint-60 A1 DoD amendment: `python -m pytest` and the
`cfnlint.runner:main` callable form — the backend gates stay green because no backend
file changes). Reality gate per story against the live stack (DynamoDB :8001 + API :8000
+ Vite :5173).

**Live-data caveat (carried from planning):** the local DynamoDB is empty and cannot be
repopulated (Dynatrace deactivated; the loop can't pull; sample mode only forces data
through the running loop). Data-dependent visuals are therefore verified at the reality
gate by (a) the empty/loading/error states live, and (b) code-level correctness +
component tests over the plan's captured fixture shapes — the same split STORY-133 used.
Any story whose reality gate genuinely requires populated data states that explicitly.

---

## Execution order

Correctness + shared infra first (low-risk, foundational, both touch `useFetch`), then the
headline layout, then polish, then the one additive new route last.

| Order | Story | Pts | Ceremony |
| ----- | ----- | --- | -------- |
| 1 | STORY-136 Dashboard/shell correctness hardening | 3 | 3-pointer |
| 2 | STORY-137 Shared fetch dedup/cache | 3 | 3-pointer |
| 3 | STORY-138 Dashboard layout coherence | 5 | 3-pointer |
| 4 | STORY-139 Response-time chart axis | 3 | 3-pointer |
| 5 | STORY-140 Empty-state & data-formatting polish | 3 | 3-pointer |
| 6 | STORY-141 Shell interaction polish | 3 | 3-pointer |
| 7 | STORY-142 Maintenance schedule date fields | 3 | 3-pointer |
| 8 | STORY-143 Component-scoped availability view | 5 | 3-pointer |

**Total: 28 pts** (the full confirmed set — PO chose "everything confirmed" at planning;
above the ~9 baseline velocity, owned by the PO; STORY-143 is the natural carryover if the
review tail runs long).

---

## Story specs

### STORY-136 — Dashboard/shell correctness hardening (3 pts)
*Findings: P0 duplicate React key (dashboard), P0 `unknown` status during load, P0 no fetch timeout.*

- **AC1** — The Dashboard "Recent checks" feed no longer keys rows by the colliding
  `signalKey-observed_at-location` triple (`deriveRecentChecks.ts:46`). Rows are keyed by a
  guaranteed-unique discriminator (final sorted position, matching the STORY-130 History
  fix). A regression test constructs a batch with a **duplicate `(signal_key, observed_at,
  location)` triple** and asserts no React duplicate-key warning and correct row count/order.
- **AC2** — While the components fetch is in flight, the topbar overall-status shows a
  **neutral loading treatment** (skeleton or "Updating…"), never the `unknown` health token.
  The `unknown` token renders only when the fetch has succeeded and the status is genuinely
  unknown. Test: assert loading-phase render is not the `unknown` StatusBadge; success-with-data
  render is the real status.
- **AC3** — `useFetch` gains a **request timeout**; a request that never settles transitions to
  the error phase (surfacing the existing `ErrorState` + retry), not an infinite spinner. Test
  with a never-resolving fetcher + fake timers asserts the error phase + working retry. Existing
  error-state/retry behavior (already wired) is preserved.
- **AC4** — No regression: all six routes still render; `npm test`/`build`/`lint` green.

### STORY-137 — Shared fetch dedup/cache (3 pts)
*Finding: P1 redundant parallel API calls (2× components + 2× approvals on a Dashboard mount; no cache layer). Verified overstated ("3–4×"/"header/sidebar" was wrong) but real: shell-vs-page duplication.*

- **AC1** — Concurrent identical fetches are **deduped**: on a Dashboard mount, each distinct
  endpoint (`/components`, `/approvals`, `/maintenance`) fires **exactly once**, not once per
  consuming component. Proven by an MSW request-count assertion (handler call count == 1 per
  endpoint across shell + page).
- **AC2** — The dedup layer is **in-house and minimal** (a small shared request cache / promise-
  coalescing keyed on the fetch identity — NO new heavy dependency like React Query; YAGNI on
  features not needed). Stale-while-revalidate / background refetch is out of scope.
- **AC3** — No refetch loop; the stable-fetcher discipline is preserved; a fetch error still
  surfaces `ErrorState`; retry re-issues a real request (not a cached failure).
- **AC4** — No behavioral regression on any page that fetches (Availability/History/Approvals/
  Maintenance/Publications); gates green.

### STORY-138 — Dashboard layout coherence (5 pts)
*Findings: P1 jagged center gutter (headline), P3 bottom-right void, P2 uneven KPI card padding, P2 inconsistent KPI accent bar.*

- **AC1** — The two Dashboard content rows share **one 2-column grid** with a single, consistent
  gutter x-position across both rows (no ~145px jump). Verified at the reality gate by measuring
  the left/right card edges of both rows (the divider x matches within a small tolerance).
- **AC2** — Column heights are balanced so there is **no large bottom-right empty void** — either
  equal-height columns or a content rebalance that fills the region (a fresh design decision, not
  a stretch hack that leaves whitespace).
- **AC3** — All four KPI cards have a **consistent content footprint** — cards without a sparkline
  no longer leave a visibly empty band relative to cards with one (equal, deliberate composition).
- **AC4** — The KPI accent treatment is **consistent by rule** (the green-vs-blue-vs-none bar
  inconsistency is resolved deliberately — e.g. a bar per card tied to meaning, or none — not an
  accidental mix).
- **AC5** — Responsive: the shared grid collapses cleanly at mobile (390) with no horizontal body
  scroll; reality-gate visual @390 + @1440.

### STORY-139 — Response-time chart axis (3 pts)
*Finding: P2 Y-axis labels collide with gridlines; baseline not 0; data-derived ticks.*

- **AC1** — The response-time chart Y-axis uses a **0 baseline** (bottom tick = 0), not the data
  minimum.
- **AC2** — Ticks are **rounded "nice" numbers** (e.g. 0/250/500/750/1000-style), not raw
  data-derived values (1082/809/536/262).
- **AC3** — A **reserved axis gutter** offsets the plot so labels do not overlap the gridlines or
  the plotted line at real data. Test asserts label positions sit in the gutter, not over the plot.
- **AC4** — The empty/no-data state is unchanged ("No response-time data available"); the a11y
  treatment (chart labelling) is preserved.

### STORY-140 — Empty-state & data-formatting polish (3 pts)
*Findings: P3 bare-dash KPI empty state, P2 History timestamps lack tz label, P2 cryptic location labels (frontend-scope portion).*

- **AC1** — When a KPI has no data, it renders a **clean "No data yet" treatment**, not a bare
  "— %" / "— ms" + "Across 0 probe locations". (Fresh design; consistent across the availability
  and response-time KPIs.) Verified live in the current empty stack.
- **AC2** — History-row timestamps carry an explicit **timezone indicator** consistent with the
  Maintenance card (which already appends "UTC"). Test asserts the tz label is present in the
  rendered string.
- **AC3** — Location labels get a **cleaner frontend-scope treatment** than "…0047" (e.g. a
  readable short-id presentation). **A doc-comment + the story History record that true
  human-readable names are blocked on a backend field** (`location_name` does not exist in the
  API) — filed as STORY-144. This story does NOT invent names client-side.
- **AC4** — Gates green; no regression.

### STORY-141 — Shell interaction polish (3 pts)
*Findings: P1 dead notifications bell, P3 mobile drawer (no close button / no brand header), P3 styleguide states center-aligned.*

- **AC1** — The notifications **bell is no longer a dead control**: it opens a real popover/panel
  with a proper empty state ("No notifications") and correct a11y (`aria-expanded`/`aria-controls`,
  focus management, Escape-to-close, click-outside). A fresh, minimal, extensible design — not a
  stub. (If, at review, the PO would rather hide it than build it, that's a review call; the
  default here is to implement.)
- **AC2** — The mobile navigation drawer has an **in-drawer brand/title header AND an explicit
  close (X) button** (in addition to the existing backdrop/Escape dismissal). Verified live @390.
- **AC3** — The Styleguide Loading/Error/Empty examples are **left-aligned to match the sibling
  gallery sections** (the state primitives keep their own internal centering; the gallery cell
  presents them consistently).
- **AC4** — Gates green; reality-gate the bell (open/empty/close) + mobile drawer (open/close/
  header) live.

### STORY-142 — Maintenance schedule date fields (3 pts)
*Finding: P3 raw native `datetime-local` inputs (style clash, OS-locale, native pickers).*

- **AC1** — The schedule form's Start/End fields are **styled to match the form system** (a
  consistent, legible date-time control) instead of bare native `datetime-local`. Whether via a
  styled wrapper or a custom field is the builder's craft call.
- **AC2** — The existing **UTC conversion behavior is preserved byte-for-byte** — local input →
  `…Z` stored (the STORY-132 datetime-local→UTC-Z contract), proven by the existing conversion
  tests still passing (rewrite, don't delete, if the input mechanism changes).
- **AC3** — The **422 field-mapping** (server "ends_at must be strictly greater than starts_at" →
  `ends_at` aria-invalid) and the client-side end-before-start guard are preserved with their
  order-sensitive tests.
- **AC4** — A11y: real `<label>` per field, `aria-invalid`/`aria-describedby`/`role=alert` on
  errors, retained. Gates green.

### STORY-143 — Component-scoped availability view (5 pts)
*Finding: P1 pinned "HTTP Check" links to the generic `/availability` list, not a component-scoped view; no such route exists.*

- **AC1** — A **component-scoped availability route** exists (e.g. `/availability/:componentId`)
  rendering that one component's availability (rollup + per-signal drill-down) on the real
  `GET /availability/component/{id}` data.
- **AC2** — The pinned nav item ("HTTP Check") **routes to that component-scoped view**, not the
  generic list. Test asserts the pinned item's target.
- **AC3** — The view handles **loading / error+retry / empty / unknown-component** states (a bad
  id → a clean not-found treatment, not a crash or infinite spinner).
- **AC4** — Back-navigation to the generic Availability list works; the generic list is unchanged.
- **AC5** — Reality gate: navigate via the pinned item to the scoped view on the live stack;
  exactly one h1; no horizontal body scroll @390 + @1440; zero console errors.

---

## Triaged OUT of this sprint (verified false / already-done / not frontend)

Recorded so a future reader does not re-chase them (full evidence in the planning transcript):

- **"LOCATIONS shows 0 vs distinct_locations:2"** — FALSE. Correctly bound to
  `rollup.distinct_locations`, genuinely 0 at rollup grain (known quirk); per-signal shows 2.
- **"History unbounded ~5000px"** — ALREADY-DONE. `capRows` defaults to 1000 in production +
  1000/signal server limit.
- **"Availability numeric alignment mixed" / "numeric header-vs-cell mismatch"** — ALREADY-FIXED
  (26ad735; all numeric columns + headers right-aligned).
- **"History RESULT over-wide" / "CHECK-TYPE accent-blue not clickable"** — FALSE (plain `<td>`,
  no width defs, no accent/link token).
- **"No error state / no retry on widgets"** — FALSE (`ErrorState` + `onRetry` are wired; only the
  *timeout* gap is real → folded into STORY-136 AC3).
- **"Collapsed sidebar icons have no tooltips"** — FALSE (`role="tooltip"` + `aria-describedby`
  wired).
- **"Maintenance lacks a tz label"** — the *card* already shows "UTC"; only History rows lacked
  one → folded into STORY-140 AC2.
- **"node_modules stale / package-lock"** — NOT a repo defect (lock committed, deps correct, no
  Geist; it was a stale local install). Real gap = no CI runs `npm ci` → filed as STORY-145 (infra).

## Filed as follow-ups (out of frontend scope — not in this sprint)

- **STORY-144 (backend):** expose a human-readable location name in the observation/availability
  API so the cockpit can show real names (unblocks the true fix behind STORY-140 AC3).
- **STORY-145 (infra/CI):** add a CI job running `npm ci && npm run build && npm test && npm run
  lint` so lockfile drift / stale installs are caught mechanically (the real gap behind the
  false "stale node_modules" finding).
