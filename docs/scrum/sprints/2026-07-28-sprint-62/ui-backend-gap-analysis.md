# New UI → existing backend: contract gap analysis

**Date:** 2026-07-28
**Design target:** `C:\Hyn\new ui\ops-pulse-react` (running on `localhost:5173`), a PO-built
clone of `https://ops-pulse-6.preview.emergentagent.com/`.
**Backend under analysis:** `backend/src/api/v1/*` at `main` (`517fc38`).
**Evidence:** all six routes screenshotted at 1440 (light + dark) and 390 —
`newui-0{1..8}-*.png` in this folder; every backend claim below cites `file:line`.

---

## 0. Three findings that reshape the request

### 0.1 The new UI is a static visual reference, not an app to wire up

The PO's brief was "adapt our backend to the new frontend". The new frontend cannot be
adapted to, because **it has no data layer to adapt**. It is scraped HTML mechanically
converted to JSX (the conversion scripts are still in the parent dir:
`fetch-html.mjs`, `extract-html.mjs`, `convert-html-to-jsx.mjs`).

Measured across all six pages (`src/pages/*.jsx`, 6565 lines):

| Page | `.map()` calls | `useState` | data arrays |
| ---- | -------------- | ---------- | ----------- |
| Dashboard.jsx (1547 ln) | **0** | 0 | 0 |
| Availability.jsx (2132 ln) | **0** | 2 | 0 |
| CheckHistory.jsx (1075 ln) | **0** | 0 | 0 |
| Publications.jsx (650 ln) | **0** | 0 | 0 |
| Approvals.jsx (592 ln) | **0** | 0 | 0 |
| Maintenance.jsx (569 ln) | **0** | 0 | 0 |

Zero loops, zero props, zero component decomposition, one shared `Layout.jsx`. Every one
of the 12 dashboard cards, 12 availability rows and 25 history rows is hand-spelled JSX
with literal values baked in. "Full mock data" is real in the sense that the *pixels* show
a fully-populated system — but it lives as text in the markup, not as data.

**Consequence:** the work is *not* "point this app at our API". It is:
1. treat this app as the **binding visual spec** (the role `refimg-dashboard.html` played
   for sprint-59, and `uptime-monitor-v3-design.html` plays for the backend), and
2. **rebuild it properly** as a decomposed, typed, tested React app in `frontend/`, and
3. **extend the backend** where the design demands data we do not expose (§2).

This is good news for fidelity — a static reference is an unambiguous pixel target — and it
means the 8016 lines are a spec to read, not code to port.

### 0.2 The design depicts a 12-component / 50-signal / 7-region fleet. We monitor one HTTP check.

`config/apps/httpcheck.yaml` is the entire production topology:

```yaml
components: [ { id: http-check, name: HTTP Check } ]
signals:    [ { signal_key: http-check, interval_seconds: 120 } ]
```

One component. One signal. One location. The design's density — a 4×3 card grid, a
12-row availability table, "50 signals across 7 regions", "97 observations · page 1 of 4"
— is entirely fictional. Rendered against the real system, the dashboard grid is **one
card in a 4-column grid** and the availability table is **one row**.

This is the single biggest risk to a fourth rejection: the layouts were designed for
density we do not have, and a design that looks superb at 12 cards can look broken at 1.
**PO decision required** (§4, Q1).

### 0.3 The reference has real defects — we should not port them

Found live, not inferred:

| Defect | Evidence |
| ------ | -------- |
| **No responsive handling at all.** At 390px the fixed 250px sidebar stays at desktop width and the body scrolls horizontally. | `newui-08-dashboard-390.png` — a horizontal scrollbar and the content clipped mid-card |
| Component names truncate to ellipsis even at 1440 (`API Gate…`, `User Authe…`, `Transactio…`, `Recommen…`) | `newui-01-dashboard-1440.png` |
| Availability/Completeness meter bars render full-width in red/amber regardless of value — 96.075% and 99.875% draw identically | `newui-02-availability-1440.png` |
| Column header says `UPTIME BLOCKS · 30D` while the active range tab is `24 hours` | `newui-02-availability-1440.png` |
| Approvals sidebar badge becomes an unreadable solid white circle in dark mode (`.badge` sets `color: white` over `background: var(--text-main)`, which inverts) | `newui-07-dashboard-dark-1440.png`; `index.css:220-228` |
| React error: `Invalid DOM property 'fill-opacity'. Did you mean 'fillOpacity'?` | console, dashboard load |
| React error: controlled `value` with no `onChange` → read-only field | console, `/history` load |
| Two different greens for one meaning: status dots use `--color-green: rgb(34,197,94)` (emerald) while badges use Tailwind `teal-500` | `index.css:12` vs `Dashboard.jsx:31` |
| `favicon.ico` 404 | console |
| "Trigger test failure" is `onClick={() => alert('Test failure triggered!')}` | `Layout.jsx:113` |

Our rebuild fixes all of these. Notably #1 is a *regression risk*: the rejected sprint-61
build did handle 390px correctly (verified live). Fidelity to the reference must mean
fidelity to its **visual language**, not to its bugs.

---

## 1. What the design system actually is

Two layers, both worth porting deliberately rather than copying:

**Layer 1 — `src/index.css` custom properties** (the shell: sidebar, header, layout):

| Token | Value |
| ----- | ----- |
| `--bg-main` | `rgb(243, 244, 247)` — cool grey canvas |
| `--text-main` | `rgb(15, 23, 41)` |
| `--text-muted` | `rgb(100, 110, 130)` |
| `--glass-bg` | `rgba(255, 255, 255, 0.66)` + `backdrop-filter: blur(12px)` |
| `--glass-border` | `rgba(255, 255, 255, 0.8)` |
| `--shadow-soft` | `0 4px 24px rgba(0,0,0,.04), 0 1px 2px rgba(0,0,0,.02)` |
| `--radius-lg / md / sm` | `1.5rem / 1rem / 0.5rem` |
| `--font-sans` | Manrope → Inter → system-ui |
| `--font-mono` | JetBrains Mono |
| status | `--color-green rgb(34,197,94)`, `--color-orange rgb(249,115,22)`, `--color-red rgb(239,68,68)` |

**Layer 2 — Tailwind v4 utilities inline in the pages** (the content area): a 4-step
status palette `teal → amber → orange → rose` (Operational / Degraded / Partial Outage /
Major Outage), each rendered as a pill with `bg-{c}-500/10 border-{c}-500/25
text-{c}-700` and a `dark:` counterpart. Dark mode is a plain `.dark` class on
`<html>` (`Layout.jsx:114`) plus a shadcn-style HSL block at `index.css:655`.

**Signature visual moves** (these are what makes it feel different from the rejected
builds, and what fidelity means here):
1. **Dark inset sidebar** — a near-black rounded panel floating on the light canvas with
   its own margin, not a full-bleed edge-to-edge rail.
2. **Glassmorphism** — translucent white surfaces with backdrop blur over a cool grey
   canvas, very soft diffuse shadows, generous `1.5rem` radii.
3. **Mono for all data** — every number, id, timestamp and label uses JetBrains Mono with
   wide uppercase tracking; Manrope only for prose and headings.
4. **Teal as the single accent** — teal for brand/active/primary-action, with the
   amber/orange/rose ramp reserved strictly for health.

**Palette conflict to resolve:** this is a **teal/emerald** system. Sprint-59's
(PO-approved, then rejected) system was **single-sky-blue** with a 7-status palette. The
7 statuses also don't map onto the reference's 4. See §4 Q3.

---

## 2. The gap: what the design needs vs what the API serves

Backend surface today — 13 endpoints, verified at `main`:

| # | Endpoint | Shape |
| - | -------- | ----- |
| 1 | `GET /health` | `{status}` — `health/controller.py:13` |
| 2 | `GET /components` | `[{id, name, status}]` — `components/models.py:12` |
| 3 | `GET /topology` | `[{id, name, signals[{signal_key, name, interval_seconds, component_id}]}]` — `topology/models.py:14` |
| 4 | `GET /availability?signal_key&since&until&interval_seconds` | `AvailabilityDTO` — `availability/controller.py:26` |
| 5 | `GET /availability/component/{id}?since&until` | `{component_id, rollup, signals[]}` — `availability/controller.py:69` |
| 6 | `GET /history?signal_key&since&until&limit` | `[{signal_key, observed_at, health, location, latency_ms, response_status_code, check_type}]` — `history/controller.py:20` |
| 7 | `GET /approvals` | `[{id, component_id, from_status, to_status, state, proposed_at}]` — `approvals/models.py:12` |
| 8 | `POST /decisions/{proposal_id}` | `{action, actor, notes}` → `{proposal_id, state, resolved_at}` — `decisions/controller.py:15` |
| 9 | `GET /maintenance` | `[{id, component_id, starts_at, ends_at, reason, title}]` — `maintenance/models.py:11` |
| 10 | `POST /maintenance` | 201 |
| 11 | `DELETE /maintenance/{window_id}` | 204 |
| 12 | `GET /publications` | `[{id, component_id, status, published_at, proposal_id, outcome, author}]` — `publications/models.py:12` |
| 13 | `GET|PUT /sample-mode` | `{enabled}` |

`AvailabilityDTO` (`availability/models.py:14`) is richer than the design uses:
`availability_pct`, `completeness_pct`, `total_verdicts`, `passing_verdicts`,
`maintenance_verdicts`, `gap_verdicts`, `distinct_locations`, `window`, `computed_at`.
Note **`completeness_pct` already exists** — the design's "Completeness" column is free,
and `distinct_locations` gives the sidebar's "across N regions" honestly.

### 2.1 Dashboard

| UI element | Backed by | Verdict |
| ---------- | --------- | ------- |
| Status-bucket counts (Operational 10 / Degraded 0 / Partial 2 / Major 0) | group `/components[].status` | ✅ free |
| Hero verdict "Partial outage detected" | worst-of `/components[].status` | ✅ free |
| KPI "Active incidents 2" | count non-operational components | ✅ free |
| KPI "Pending approvals 5" | `/approvals`.length | ✅ free |
| KPI "Maintenance 3 · 1 in progress" | `/maintenance` + now-vs-window | ✅ free |
| Component card: name, status | `/components` | ✅ free |
| Hero "48 of 50 signals healthy" | — | ❌ **no latest-health-per-signal endpoint** |
| Hero "last check just now" | — | ❌ same gap (needs max `observed_at`) |
| KPI "Fleet uptime · 24h 97.66%" | — | ❌ **no fleet-level rollup**; only per-signal (#4) / per-component (#5) |
| Card: 24h uptime % | #5 per component | ⚠️ **N+1** — one call per component |
| Card: category chip (`COMMERCE`/`PLATFORM`/`DATA`/`DISCOVERY`/`MESSAGING`) | — | ❌ **no `group` field** on component |
| Card: description ("Cart, payments and order placement") | — | ❌ **no `description` field** |
| Card: sparkline series | — | ❌ **no bucketed time-series endpoint** |
| Card: signal health counts (`4 · 0 · 0 · 4 signals`) | — | ❌ needs latest-health-per-signal |
| 14-day fleet strip | — | ❌ needs daily buckets |

### 2.2 Availability

| UI element | Backed by | Verdict |
| ---------- | --------- | ------- |
| Range tabs 24h / 7d / 30d | `since`/`until` on #5 | ✅ free |
| "Sort by lowest availability" | client-side | ✅ free |
| Availability % per component | #5 `rollup.availability_pct` | ⚠️ N+1 |
| Completeness % per component | #5 `rollup.completeness_pct` | ✅ already in DTO |
| Footer "Below SLO 12" | client-derived | ✅ free |
| Status per row | `/components` | ✅ free |
| Category sub-label | — | ❌ same `group` gap |
| **30 uptime blocks per row** | — | ❌ **no bucketed series** |
| Footer "Fleet availability 24h" / "Data completeness 24h" | — | ❌ **no fleet rollup** |

### 2.3 Approvals

| UI element | Backed by | Verdict |
| ---------- | --------- | ------- |
| from → to status transition | `/approvals` | ✅ free |
| Age ("43m ago") | `proposed_at` | ✅ free |
| Approve & publish / Reject | `POST /decisions/{id}` | ✅ free |
| Component display name | join `/components` | ✅ free |
| **Reasoning** ("3 of 5 signals failing in eu-west-1 + us-east-1") | — | ❌ **not on `ProposalDTO`** |
| **Confidence %** ("91% confidence") | — | ❌ **not on DTO — and may not exist in the domain at all** |
| **Evidence signal count** ("4 evidence signals") | — | ❌ not on DTO |
| **Proposed by** ("auto-detector") | — | ❌ not on DTO |
| Proposal id rendered `ap-0-c-checkout` | ours is `int` | ⚠️ cosmetic |
| `actor` for the decision call | UI hardcodes "Nadia M." | ❌ **no auth/users in the backend** |

### 2.4 Check History — the largest single gap

| UI element | Backed by | Verdict |
| ---------- | --------- | ------- |
| Timestamp, latency, HTTP status | `/history` | ✅ free |
| Range 1h / 24h / 7d / 30d | `since`/`until` | ✅ free |
| **A fleet-wide feed across all components** | — | ❌ **`/history` *requires* `signal_key`** (`history/controller.py:22`) — the design's core view is impossible in one call |
| **Pagination "97 observations · page 1 of 4"** | `limit` only | ❌ **no offset/cursor, no total count** |
| Component filter dropdown | — | ❌ no component param on `/history` |
| Location filter dropdown | — | ❌ no location param; no locations endpoint |
| Result tabs **Success 88 / Slow 3 / Timeout 4 / Failure 2** | ours is `up`/`down`/`degraded` | ❌ **different taxonomy** — "Slow" and "Timeout" are not domain verdicts |
| Location display name "US East (Virginia)" | raw `location` string | ❌ no region metadata |
| Check column "HTTP GET" / "HTTP POST" / "DNS" / "TCP" | `check_type` is e.g. `"http"` | ❌ no method granularity |

### 2.5 Maintenance

| UI element | Backed by | Verdict |
| ---------- | --------- | ------- |
| Title, description, window | `/maintenance` (`title`, `reason`, `starts_at`, `ends_at`) | ✅ free |
| Status tabs Scheduled / In progress / Completed | derive from window vs now | ✅ free |
| New-maintenance form | `POST /maintenance` | ✅ free |
| **Multiple affected-component chips** (`Database — Primary` + `Database — Replica` on `m-1`) | `component_id` is **singular** | ❌ **multi-component windows unsupported** |

### 2.6 Publications

| UI element | Backed by | Verdict |
| ---------- | --------- | ------- |
| Status pill, relative + absolute time | `/publications` | ✅ free |
| "Published by ops-nadia" | `author` | ✅ free |
| **Headline** ("Investigating elevated error rates on Checkout") | — | ❌ **not on DTO** |
| **Body prose** ("We are investigating elevated 5xx responses…") | — | ❌ not on DTO |
| Multiple affected components | singular `component_id` | ❌ same as maintenance |
| — | `outcome` (`succeeded`/`failed`) **exists but the design drops it** | ⚠️ we should keep it; a failed publish must stay visible |

### 2.7 Shell

| UI element | Backed by | Verdict |
| ---------- | --------- | ------- |
| Approvals / Maintenance nav badges | `/approvals`, `/maintenance` | ✅ free |
| "PRODUCTION" env badge | build-time constant | ✅ free |
| "50 signals across 7 regions" | `/topology` count + `distinct_locations` | ✅ free |
| "Trigger test failure" | maps cleanly onto **`PUT /sample-mode`** | ✅ free — a real feature behind that button |
| ⌘K search over components/signals/locations | — | ❌ no search endpoint (client-side over `/topology` is viable) |
| User avatar "Nadia M." | — | ❌ no users/auth |

---

## 3. Consolidated backend work

Ordered by how much of the design each unblocks. Every item is additive — no existing
contract breaks, so the current frontend keeps working throughout.

| # | Change | Unblocks | Zone | Est |
| - | ------ | -------- | ---- | --- |
| **B1** | **Fleet summary endpoint** `GET /summary` — worst-of status, per-bucket counts, fleet availability + completeness, signals-healthy/total, last-check instant, open-approval + active-maintenance counts. One call for the hero + all four KPIs. | Dashboard hero + 4 KPIs; Availability footer | core service + api | 5 |
| **B2** | **Fleet history** — make `signal_key` optional on `/history`; add `component_id`, `location`, `health` filters, `offset`, and a total count (envelope `{items, total, offset, limit}`). | The entire Check History page | api + persistence | 5 |
| **B3** | **Bucketed availability series** `GET /availability/series?component_id&since&until&buckets=N` → N per-bucket verdicts. | Sparklines, 30-block bars, 14-day strip | core query + api | 5 |
| **B4** | **Component metadata** — add `group` + `description` to `config/apps` and `ComponentDTO`. | Category chips + card descriptions everywhere | config + api | 2 |
| **B5** | **Latest health per signal** — either fold into B1/`/topology`, or `GET /signals/latest`. | Hero "48 of 50", per-card signal counts | core + api | 3 |
| **B6** | **Batch component availability** — `GET /availability/components?ids=…` to kill the N+1. | Dashboard + Availability page load cost | api | 3 |
| **B7** | **Location/region metadata** — display names for probe locations. | "US East (Virginia)", region filter | config + api | 2 |
| **B8** | **Proposal evidence** — `reasoning`, `evidence_signal_count`, `proposed_by` on `ProposalDTO`. Requires confirming the anti-flap engine can supply them. | Approvals detail pane | core + api | 3 |
| **B9** | **Publication headline + body** | Publications timeline | domain + api | 3 |
| **B10** | **Multi-component maintenance / publications** | Multi-chip cards | domain + persistence + api | 5 |

**Not recommended without a product decision:** proposal *confidence %* (§4 Q2), users/auth,
and the Slow/Timeout/Failure taxonomy (§4 Q4).

B1–B4 alone unblock roughly 80% of the design. B8–B10 are the expensive tail and buy the
least.

---

## 4. PO decisions needed before a sprint can lock

**Q1 — Topology density (blocking).** The design assumes 12 components / 50 signals /
7 regions; we monitor 1 / 1 / 1. Do we (a) expand `config/apps` + Dynatrace to a realistic
fleet, (b) design honestly for a small fleet and let the layouts breathe at n=1, or
(c) build to the dense design and accept that it looks sparse until the fleet grows?
Getting this wrong is the most likely cause of a fourth rejection.

**Q2 — Invented data.** Confidence %, publication headlines/bodies, and component
descriptions are visible in the design but have no source in our domain. Invent them
(new fields operators fill in), derive weak substitutes, or drop those visuals?

**Q3 — Palette.** This reference is teal/emerald with a 4-status ramp. Sprint-59's system
was sky-blue with 7 statuses (`up`/`degraded`/`partial`/`down`/`maintenance`/`unknown`/
`missing`). Adopt teal + 4 and map the other 3 statuses into it, or keep 7 statuses in the
teal language? The reference has no visual for `maintenance`, `unknown`, or `missing` —
and `unknown`/`missing` are load-bearing in this system.

**Q4 — Result taxonomy.** The design's `Success / Slow / Timeout / Failure` is not our
`up / down / degraded`. Relabel the design to our verdicts, or add a latency-threshold
"slow" and a timeout distinction to the domain?

**Q5 — Rebuild base.** Branch sprint-62 from `main` (frontend = the old sprint-38 build)
or from the `sprint-61` tip (the rejected-look build, but with 745 green tests and a
verified data layer: `useFetch` with timeout + in-flight dedup, the typed API client, DTO
types, MSW harness)? **Recommendation:** branch from `main`, then cherry-pick sprint-61's
*design-neutral infrastructure* only. Rejecting a look is not a reason to throw away a
verified fetch layer, and rebuilding it would burn a third of the sprint re-earning tests
we already have.

---

## 5. Recommended shape

A three-sprint program, not one sprint:

- **Sprint 62 — foundation + one page proven end-to-end.** Design system ported from the
  reference (tokens, glass surfaces, dark inset sidebar, Manrope/JetBrains Mono, teal
  accent), the app shell, B1 + B4, and the **Dashboard** rendering real data. Ends with a
  PO look-and-feel checkpoint on a real page before more pages get built on the language.
- **Sprint 63 — the data-heavy pages.** B2 + B3 + B6, then Availability and Check History.
- **Sprint 64 — the workflow pages + the expensive tail.** Approvals, Maintenance,
  Publications; B8–B10 as far as Q2 allows.

**Process note for the retro.** Three UI directions have now been rejected *after* being
built, and each passed its own AC, DoD gate and reality gate. The mechanical floor worked
perfectly and still produced three rejections, because the gates verify conformance to the
AC we wrote — nothing in the loop verified *the PO wants this look* before a sprint of work
existed. Sprint 62's checkpoint above is the pilot fix: a PO look-and-feel sign-off on one
real page, mid-sprint, before the language is replicated across six.
