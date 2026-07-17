# UI Redesign Journal

PO directive (2026-07-17): significantly improve UI/UX; backend completely unchanged;
feature branches only (integration branch `ui-redesign`, never merged to main without PO
review); every change Playwright-verified against the local stack. This journal records
only what isn't captured in stories/plans/retros: exploration findings, design decisions
and their reasoning, and lessons learned.

## Method

- Live local stack (DynamoDB Local :8001, API :8000, live loop w/ real Dynatrace, Vite :5173).
- Playwright MCP walk of all six tabs, light+dark, 1536/1440/390 viewports, collapsed sidebar,
  keyboard focus, sample-mode round-trip (on → proposal appeared → rejected → off), maintenance
  create/delete round-trip, approve-confirm (canceled before submit — never published).
- Audit lens: ui-ux-pro-max skill (design-system baseline + priority rules 1–10) with
  observability-dashboard practice cross-checked against
  [Grafana best practices](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/best-practices/),
  [logz.io top-10 dashboard mistakes](https://logz.io/blog/top-10-mistakes-building-observability-dashboards/),
  [UXPin dashboard principles](https://www.uxpin.com/studio/blog/dashboard-design-principles/).
- Evidence: `exploration/explore-01..19.png` (in this folder). Zero console errors/warnings,
  all `/api/*` 200 across the whole exploration session.

## Findings (verified 2026-07-17, all via Playwright against the live local stack)

### Critical — responsive shell (evidence: explore-17, explore-18)
1. At 390×844 the sidebar keeps its 211px desktop width; content gets ~180px; horizontal
   scrollbar appears (worse than STORY-096 described — it's every page, not just the sidebar).
2. Check History at 390px: filters clipped, only the (wrapped) timestamp column visible.
3. Sample-mode banner wraps into a tall 5-line column on mobile.

### Operator workflow / IA
4. Approval cards give zero decision evidence (explore-13): raw signal slug (`http-check`),
   no friendly component name, no affected locations, no "degraded since" duration, no link
   to the failing checks. The operator is asked to publish blind. (Violates
   "metrics need context" — the #1 observability-dashboard mistake per logz.io.)
5. Raw ISO-8601 UTC timestamps everywhere, microseconds included (`2026-07-17T10:25:03.101501Z`);
   no relative times. Maintenance form takes LOCAL time input but displays the window as raw
   UTC after creation (explore-16) — operator-hostile round-trip.
6. Raw vendor location IDs (`SYNTHETIC_LOCATION-0000000000000047`) dominate dashboard
   drill-down and Check History columns (explore-02, explore-06).
7. Zero-value stat cards keep their alert colors (amber/orange/red "0" — explore-01):
   false urgency when everything is healthy. "Components" card is redundant with
   "Operational N of N".
8. No cross-tab awareness on the dashboard (pending approvals / active maintenance live only
   in the nav badge); no last-updated indicator anywhere despite background polling.
9. Availability tab: "8.33% • missing data" (explore-03) — the number is *completeness*,
   the label reads as *missing*. Genuinely ambiguous.
10. Empty states are inconsistent: Approvals has a designed one (icon + title + body),
    Maintenance/Publications are bare text; Publications shows "Showing the latest 50
    publications" above "Nothing published yet" (explore-08).
11. Page scaffold is inconsistent: Dashboard/Approvals/Maintenance render h1 outside the
    card; Check History/Publications render the title inside it; container widths differ
    per tab (Approvals ~960px centered vs Dashboard full-width).

### Visual / affordance
12. Sample-mode toggle is an icon-only lightning button styled red (explore-01) — reads as
    an alert/destructive control, not an environment switch; when its banner is dismissed the
    red icon is the only remaining indicator.
13. Check History table: Type and Component columns are identical on every row; timestamp
    column is ~2× wider than needed; latency has no visual encoding; "Down" rows show
    code 200 (sample-mode artifact, but unexplained to the operator).
14. Approve/Reject inline confirms exist (good) but "Confirm approve" carries no consequence
    copy ("this updates the public status page") and uses the same primary styling as any button.
15. Maintenance form uses native browser validation bubbles (transient, unstyled,
    explore-15); Title is not required; no success feedback after creating a window.
16. Collapsed sidebar rail is icon-only with no tooltips (explore-19); pending badge
    degrades to an unexplained red dot.

### Foundations verified good (preserve, don't regress)
- `:focus-visible` two-tone focus ring (verified via real Tab keypress); skip link;
  aria-labels ("Approvals, 1 pending"; switch role on sample mode); semantic tables.
- 7-status token palette + light/dark theming (token-driven, `data-theme` on root).
- Zero console errors; typed API client; MSW test seam.
- Note: full-viewport headless screenshots showed a "white sidebar" in dark mode
  (explore-10/11) — verified false alarm: computed styles + element screenshot (explore-12)
  + sprint-51's live sweep all show it dark. Headless sticky-layer compositing artifact;
  re-verify anything similar with element screenshots before filing.

## Design decisions

- D1 (2026-07-17): Evolve the existing sprint-38 Geist/Linear-derived token system; do NOT
  re-theme (the ui-ux-pro-max generator suggested Fira/OLED-dark-only — rejected: the
  project has a deliberate, tested light+dark system; the binding parts of the skill are
  its accessibility/density/consistency rules, not the palette suggestion).
- D2: Mobile strategy = collapse-to-rail at ≤1024px, overlay drawer at ≤768px (Material
  adaptive-navigation rule), because operators genuinely use phones during incidents.
- D3: Time display = relative ("4m ago") with absolute local time + UTC in a tooltip/title,
  monospace tabular figures; one shared formatter, no per-page variants.
- D4: Color carries state only when state is non-nominal — zero-value cards go neutral
  (Grafana "meaningful color" rule).
- D5: Approval cards become evidence-first: component name, transition, duration,
  affected locations w/ latest results, link to pre-filtered Check History. Consequence
  copy on the confirm step.

## Sprint log

### Sprint 52 (2026-07-17) — wave 1: responsive shell + consistent scaffold — 5/5 accepted
- Shipped: adaptive sidebar (auto-rail ≤1024px, focus-managed overlay drawer ≤768px, drawer
  closes on nav — a live-gate catch), 390px-safe layouts everywhere (scrollWidth==390 on all
  six tabs), table-scoped horizontal scrolling, shared PageHeader (one h1/page, outside cards),
  single container-width policy (960px token + explicit wide opt-in), designed EmptyStates on
  all tabs, Publications empty-copy contradiction fixed, Availability controls into the header
  actions slot. Tests 363 → 417. Findings #1–#3, #10–#11 CLOSED.
- Lessons (details in sprint retro): L1 — never point a gate's pytest at the live dev DB
  (fixture wipe incident); L2 — after HMR hot patches, hard-reload before trusting console
  errors; full-viewport headless screenshots lie about sticky-element colors (use element
  shots / computed styles); L3 — the live reality gate catches what jsdom can't (drawer-
  covers-page); L4 — wiki ownership follows the agent definition, briefs must not improvise.
- Remaining findings → sprint 53+: #4–#9, #12–#16 (time/identity, dashboard signal quality,
  approvals evidence, check-history readability, mode/nav affordances).
