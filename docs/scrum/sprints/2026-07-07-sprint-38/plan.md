# Sprint 38 — Operator Dashboard redesign — Plan & Design Brief

**Goal:** Re-skin the six-tab operator SPA (`frontend/`) to the imported *Operator Dashboard*
design, binding every element to REAL API data (no fakes), preserving all functionality,
routing, business logic, and the theme system. Backend data gaps → follow-up stories 063-067.

**Visual source of truth:** `reference-operator-dashboard.dc.html` (in this folder; a
design-compiler mock — `{{ … }}` are data bindings, `sc-if`/`sc-for` are conditionals/loops,
NOT literal markup). It is dark-first with a light theme; our app already ships both.

**PO decisions (2026-07-07):** adapt to real data / no fakes / gaps → follow-up stories · fonts
as in the mock (self-hosted Geist) · single-sprint finish · relocate the sample-mode toggle to
the top-bar trigger.

---

## Parallel execution model (PO-directed multi-agent)

Wave-based — the eight stories are not all independent:

- **Wave 0 (solo, blocking): STORY-055** design-system foundation + shared primitives. Everything
  inherits it. Gate-green + committed on `sprint-38` before anything else.
- **Wave 1 (solo, blocking): STORY-056** shell. Wraps every page; relocates the sample-mode toggle
  out of `DashboardPage` before 057 rebuilds it.
- **Wave 2 (parallel, worktree-isolated): STORY-057–062** fan out as up to 6 concurrent
  Sonnet-5/HIGH implementers, each in its own git worktree on disjoint files. Integrate SERIALLY;
  Opus reviews (057-061) + DoD gate run serially (never concurrent `npm test`/`build`).

Pipeline: 055-061 (3+ pts) = implementer(Sonnet5/HIGH) + spec(Opus) + quality(Opus) + gate; 062
(2 pts) = gate-only. Implementer model rule 2026-06-24/2026-07-02.

---

## Design system spec (STORY-055 owns this; everyone else consumes it)

**Keep the existing token NAMES** (`--color-*`, `--fs-*`, `--space-*`, `--radius-*`, …) so
downstream components/pages that already read `var(--…)` need no rewrite — **retune the VALUES**
to the reference, and ADD the new tokens. Keep the `:root[data-theme='dark'|'light']` scoping and
the `index.html` pre-paint script mechanism unchanged.

### Color token remap (current name → dark / light)
| Token | Dark | Light |
|---|---|---|
| `--color-canvas` | `#0b0d10` | `#f6f7f9` |
| `--color-surface-1` | `#111419` | `#ffffff` |
| `--color-surface-2` | `#171b21` | `#f0f2f5` |
| `--color-surface-3` (hover) | `#1b2027` | `#eaedf1` |
| `--color-surface-4` | `#1b2027` | `#eaedf1` (alias surface-3; ladder is 3-deep + hover in the ref) |
| `--color-hairline` | `#22272e` | `#e4e7eb` |
| `--color-hairline-strong` | `#2d333b` | `#d3d8de` |
| `--color-ink` | `#e6e9ee` | `#161a1e` |
| `--color-ink-muted` | `#98a1ac` | `#59626c` |
| `--color-ink-subtle` | `#69727d` | `#8a929b` |
| `--color-ink-tertiary` | `#69727d` (alias subtle) | `#8a929b` |
| `--color-accent` | `#7c85f0` | `#5b60d6` |
| `--color-accent-hover` | `#939bf5` (brighten) | `#4a4fc0` (darken) |
| `--color-accent-focus` | `#7c85f0` | `#5b60d6` |
| `--color-accent-bg` (NEW) | `rgba(124,133,240,.14)` | `rgba(91,96,214,.10)` |
| `--color-on-accent` | `#ffffff` | `#ffffff` |
| `--color-overlay` | `rgba(0,0,0,.6)` | `rgba(13,14,16,.4)` |

### Health / status palette — extend 5 → 7 (each with a `-subtle`/`-bg` companion)
| HealthStatus | Dark | Light | Notes |
|---|---|---|---|
| `up` (ok) | `#3fb950` | `#1a7f37` | |
| `degraded` | `#d6a419` | `#9a6700` | |
| `partial` **(NEW)** | `#e8843b` | `#bc4c00` | maps `partial_outage` (see below) |
| `down` (major) | `#f85149` | `#cf222e` | |
| `maintenance` | `#3b9eff` | `#0b68cb` | KEEP current blue (maintenance windows) |
| `unknown` | `#8b96a5` | `#57606a` | |
| `missing` **(NEW)** | `#4f7bd0` | `#0969da` | Availability *completeness* only, not component health |
`-bg` alpha: dark ≈ `.13–.16`, light ≈ `.10–.12` (mirror the ref `--*-bg` values).

**`statusMapping.ts` change:** map `partial_outage → 'partial'` (was `→ 'degraded'`). Extend the
`HealthStatus` union with `'partial'` and `'missing'`; extend `StatusBadge` `DEFAULT_LABELS`
(`partial` → "Partial outage", `missing` → "Missing data"). Update the affected StatusBadge /
statusMapping tests. **Accessibility invariant unchanged:** every badge is dot **+ text label**,
never color-only.

### Type, spacing, radii, shadow, fonts
- **Fonts:** add `@fontsource/geist` (400;500;600;700) + `@fontsource/geist-mono` (400;500;600);
  import weights in `main.tsx` (mirror the current `@fontsource/inter` imports). Set
  `--font-sans: 'Geist', …` and `--font-mono: 'Geist Mono', …`. Remove the Inter/JetBrains imports
  and deps. **No Google-CDN `<link>`** (offline/CSP). Update the CLAUDE.md/README font line +
  `frontend/package.json` in the same commit.
- **Base size:** body 13px, line-height 1.45; keep the utility `.text-*` classes but retune to the
  ref (h1 17px/650/-.01em; section labels 11px/600/uppercase/.05–.06em; mono 11.5–12.5px). Add
  `font-variant-numeric: tabular-nums` globally (on `body`).
- **Radii:** control ~7px, card 8px, chip 4–5px, pill 9999px.
- **Shadow (NEW token `--shadow`):** dark `none`; light `0 1px 3px rgba(18,24,38,.06),0 1px 2px rgba(18,24,38,.04)`.
- Keep `--focus-ring`, `--target-min` (40px). Sidebar width tokens: `--nav-width` (expanded ~212px)
  / collapsed ~52px; header height 52px.

### Shared primitives STORY-055 must build (Wave-2 pages consume them)
- **`Table`/`DataGrid`** — extract the table `th/td`/hairline/uppercase-caption styling currently
  copy-pasted across 6 page CSS files into ONE primitive (kills that duplication). Must keep
  `role="table"`, `<th scope="col">` semantics so page tests stay role-based.
- **`UptimeBar`** — the segment sparkline (N equal segments, each colored by a status; `title`
  tooltip per segment; "no data" rendering). Used by Dashboard + Availability.
- **`SummaryCard`** — the labeled stat card (dot + uppercase label + big mono value + sub). Dashboard.
- **`Timeline`** — the vertical line + dot list primitive. Publications.
Each ships co-located CSS + its own Vitest test (render + a11y name), token-only colors.

---

## Per-surface layout specs (distilled from the mock)

**Shell (056):** left sidebar (logo+collapse header 52px; icon+label nav buttons; active = accent
bg/weight; Approvals badge dot/number; collapse toggles to icons-only). Top bar 52px right-aligned:
⚡ failure trigger (→ sample-mode) + theme toggle. Dismissible banner under the bar (→ sample-mode
warning). Content column scrolls; page container `padding:18px 20px; max-width:1400px; margin:auto`.

**Dashboard (057):** header (title + "Live status across N components · updated … · click a row…");
row of `SummaryCard`s (counts by status from `getComponents`); component rows — chevron + status dot
(reduced-motion-guarded pulse only if you add one) + mono name + `UptimeBar` + uptime % + status
pill; expand → signals table (`getTopology`+`getHistory`: location/label/status/latency/last). ONE
group (no `group` field → STORY-067). Keep the active-maintenance badge (STORY-046). Uptime segments
derived from real availability/history; **omit the bar gracefully where no data** (no fabricated
segments).

**Availability (058):** header + legend (down / missing-data) + 24h/7d/30d toggle (reuse
`windowRange`). Grid rows: component (name+group) | Availability (big mono % + down label +
`UptimeBar`) | Data completeness (big mono % + "missing data" chip + split bar: `--ok` width =
completeness, remainder hatched `missing`). `availability_pct`/`completeness_pct` are **0-1
fractions** — reuse `formatPct`. Keep per-signal drill-down.

**Approvals (059):** cards (severity accent stripe left; **severity derived from `to_status`**:
major_outage→major, partial_outage→partial, degraded→degraded, else unknown), component + from→to
status pills (New when `from_status` null), Approve/Reject with confirm state (keep 409/404 notice),
"Queue clear" empty state. **Omit** reason/source/detected-ago/checks/triggering-signals (not on
`ProposalDTO`) → STORY-063.

**Check History (060):** filter toolbar — search input (client-side filter over
component/location/signal_key) + result-filter `<select>` + location-filter `<select>` + window
toggle. Dense mono grid: Timestamp/Component/Location/Result(dot+label)/Latency. **Omit** "Type" +
HTTP "Code" columns (not on `ObservationDTO`) → STORY-064. Resolve STORY-054: the rebuilt table must
not false-red under parallelism (cap/virtualize or bound fixture; keep the 1000-cap caption).

**Maintenance (061):** two columns — form card (Title→maps to `reason`; Component `<select>`; Start/End
`datetime-local`; "Schedule window" submit) + windows list (title + state badge via
`deriveWindowState` + `component · range`). Keep inline 422 field mapping (`fieldError`). **Omit**
delete button (no DELETE endpoint) → STORY-065.

**Publications (062):** vertical `Timeline` — dot + connector per row; scope (component) → status +
outcome chip; `published_at · proposal_id`. **Omit** author/outcome/incident (not on `PublicationDTO`;
show `proposal_id` + real fields) → STORY-066. Keep the "latest 50" caption.

---

## Verified API contracts (pinned at planning — do NOT re-infer)
`ComponentDTO{id,name,status}` (status raw enum operational/degraded/partial_outage/major_outage) ·
`ProposalDTO{id,component_id,from_status?,to_status,state,proposed_at}` ·
`AvailabilityDTO{availability_pct 0-1|null, completeness_pct 0-1|null, total/passing/maintenance/gap_verdicts, distinct_locations, window, computed_at}` →
`ComponentAvailabilityDTO{component_id, rollup, signals[SignalAvailabilityDTO{+signal_key}]}` ·
`ComponentTopologyDTO{id,name,signals[TopologySignalDTO{signal_key,name,interval_seconds?,component_id}]}` ·
`ObservationDTO{signal_key,observed_at,health(up/down/degraded),location,latency_ms?}` ·
`PublicationDTO{id,component_id,status,published_at,proposal_id?}` ·
`MaintenanceWindowDTO{id,component_id,starts_at,ends_at,reason?}` (no state; derived) ·
`SampleModeDTO{enabled}` · endpoints unchanged (`api/client.ts`). MSW fixtures for redesigned pages
derive from the EXISTING `mocks/handlers/*` fixtures (already real-shape), never re-invented.

## Conventions checklist (held at quality review, every story)
- **Token discipline:** components read `var(--…)` only; raw hex appears ONLY in `tokens.css`.
- **Accessibility invariants (preserve — the current app is meticulous):** status = dot **+ text**,
  never color-only; interactive rows/toggles are keyboard-operable with correct roles
  (`role="switch"`+`aria-checked`, buttons `aria-pressed`, expanders `aria-expanded`,
  `role="status"`/`alert` on live regions); skip-link kept; 40px min targets; any animation
  `prefers-reduced-motion`-guarded.
- **Tests by role/name/text**, not class/DOM; a contract change REWRITES its tests (never deletes to
  a gap); MSW is the only mocked edge (`onUnhandledRequest:'error'`).
- **Scoped staging** (never `git add -A`); clean committed tree at gate; **empty backend diff**
  (`git diff sprint-38-start..HEAD -- backend/ scripts/ config/ migrations/ pyproject.toml alembic.ini`).
- **Wiki:** run the mechanical staleness sweep at DoD; the `frontend-zone` article's `code_refs`
  cover the shell/tokens — update/re-verify per the 2026-06-28 sweep agreement.
- **CLAUDE.md/README** updated in the same commit if the frontend stack/commands/fonts line changes
  (2026-06-23 command-sync).
- If the mock's markup lowers accessibility (`onClick` on `<div>`, color-only dots, unguarded
  `statusPulse`), KEEP our stricter version — visual fidelity never trades away a11y.
