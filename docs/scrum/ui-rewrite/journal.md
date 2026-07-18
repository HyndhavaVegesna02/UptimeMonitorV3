# UI Rewrite Journal

PO directive 2026-07-18: full frontend rewrite, same backend, complete creative freedom;
`ui-rewrite` off main; per-sprint delegated verdicts; PO takes the final merge review.
Design authority: design-brief.md (binding) over the generated MASTER.md. The parked
`ui-redesign` initiative's journal (../ui-redesign/journal.md) holds the exploration
findings that still inform this rewrite's UX semantics.

## Sprint log

### Sprint 57 (2026-07-18) — wave 3: decision surfaces — 5/5 accepted
- Shipped: evidence-first approvals on the Tile language (per-location evidence, consequence
  confirm, live sample-mode round-trip verified) + dense check-history table (deep-link seed,
  aria-live summary matching API truth exactly, latency tint bands proven on real data,
  sticky header). Tests 508 -> 606.
- Lessons: a broken shell chain produced a commit whose message preceded its board edit —
  corrected next-commit; gate+board sequences now run as separate verified calls. Salvage
  pointers must be verified to exist before being named in briefs (initialHistoryFilters
  lived only in the never-green sprint-54 WIP).
- Next: sprint 58 — maintenance (109) + publications + polish matrix + PO package (110).

### Sprint 56 (2026-07-18) — wave 2: bento dashboard + availability — 5/5 accepted
- Shipped: bento mission-control dashboard (hero worst-of KPI, component tiles w/ uptime
  bar + inline-SVG latency spark, neutral-at-zero action tiles, recent-checks feed,
  MSW-real per-tile fault isolation) + availability on the Tile language (switcher,
  completeness phrasing, hatched legend, signal drill-down). Tests 461 -> 508.
- Notes: 2N dashboard history fetches = deliberate failure-domain isolation; grid balance
  at low tile counts + undefined .text-label class -> STORY-110 polish.
- Next: sprint 57 — approvals evidence cards (107) + dense check history (108).

### Sprint 55 (2026-07-18) — wave 1: foundation + shell — 6/6 accepted
- Shipped: Mission Teal tokens (dark-first, stored>dark precedence — corrected at the
  reality gate; 74 live-file WCAG contrast assertions), self-hosted Space Grotesk/Inter/
  JetBrains Mono, Tile/Button/StatusBadge/Icon/RelativeTime primitives, salvage ports,
  and the sidebar-less command-bar shell (worst-of status dot, 6 tabs, sample-mode
  cluster, focus-managed mobile sheet, 390px exact fit).
- Lessons: ui-sweep scripted Chromium = full-fidelity reality-gate fallback when the MCP
  is gone; design-authority corrections at the gate are cheap when caught same-story;
  skill domain-searches in briefs keep implementers on the rails.
- Next: sprint 56 — bento dashboard (STORY-105) + availability (STORY-106).
