# Round 2 — design system derived from refimg.jpg (2026-07-19)

**PO directive (2026-07-19):** the 4-way exploration is stopped. PO likes the visual language
of `refimg.jpg` (a clean light-mode e-commerce SaaS admin dashboard). Analyze its visual
language, derive a cohesive design system, apply it to Uptime Monitor. Build ONE prototype
(code later). Skills to use: `web-design-guidelines`, `vercel-react-best-practices`,
`emil-design-eng` (all loaded this session).

## Reference read (what the image actually shows)

- **Theme:** light, calm, premium. The whole app sits in a large rounded frame (~24px) with
  a hairline border, floating on a cool light-gray backdrop. Left sidebar (white) + main
  content, divided by hairlines.
- **Palette:** near-white surfaces; cool light-gray canvas; near-black text; two greys for
  secondary/tertiary text; a single **sky-blue accent** (logo, links, the chart line);
  semantic **green** (positive deltas, sparkline) and **red** (negative). Extremely
  restrained — one accent, colour used sparingly.
- **Containers:** white cards, 1px very-light border, ~14–16px radius, generous padding,
  whisper-soft shadow. KPI cards = icon chip - label - big number - delta(arrow) + inline
  sparkline.
- **Typography:** humanist sans (Inter-like). Big bold KPI numerals; small medium-weight
  muted labels; clear hierarchy; tabular figures.
- **Density:** airy, comfortable, lots of whitespace.
- **Iconography:** thin line icons (Lucide-ish), small, muted, consistent stroke.
- **Signature bits:** outlined pill primary action + search in sidebar; grouped nav with tiny
  uppercase section labels ("Main / Operations / Favorites") and a count badge; big line chart
  with a range selector; dotted-world "Live Activity" map with pulse markers + segmented
  control; "Recent Orders" list; numbered "Top Products" ranking; trend arrows on deltas.

## Derived tokens (three-layer — design-system skill)

Primitives: cool-grey ramp (#FFFFFF → #17191E), sky accent #2E9FD6, green #16A34A,
red #EF4444, amber #F59E0B, violet #7C6BF5.

**Contrast-safe text tokens (emil + web-interface-guidelines, WCAG AA):** bright brand colours
are for *fills/strokes* only; text uses darkened variants — `--accent-text #10709E`,
`--pos-text #15803D`, `--neg-text #C42B22`, `--degraded-text #B45309`, `--maint-text #6D28D9`.
Body text #17191E; secondary #565C66; muted #6C727C (kept ≥12px). All verified ≥4.5:1 on white.

Semantic: canvas / app-frame / surface / surface-subtle / border / border-strong / text ×3 /
accent(+text+tint) / positive / negative / health{up,degraded,down,maintenance,unknown}.
Radius 16 (card) / 10 (control) / 999 (pill). Shadow: `0 1px 2px rgba(16,24,40,.04)` +
`0 1px 3px rgba(16,24,40,.06)` on hover-lift.

## IA mapping (product → reference layout, backed by real /api/v1 data)

- **Sidebar** grouped like the reference: MONITORING {Dashboard•, Availability, History} /
  OPERATIONS {Approvals [badge 1], Maintenance, Publications} / PINNED {Checkout Flow
  (degraded), Payment Gateway (maintenance)}. Top: "＋ Maintenance" pill (real operator
  action) + search (⌘K). Brand mark "Uptime Monitor".
- **Header:** "System overview" + calm greeting; overall status pill **Degraded** (worst-of,
  amber, dot+icon+label — never colour alone); last-updated; bell.
- **KPI row (4):** Overall availability 99.87% (+0.04%); Avg response 428 ms (−6.2%, good→green);
  Components healthy 4/6 (1 degraded · 1 maintenance); Pending approvals 1 (accent "attention").
  Sparklines on the two rate metrics.
- **Row: [Response-time chart 24h — 2/3] [Probe locations map + Upcoming maintenance — 1/3]**.
  Map echoes the reference dot-field with the 2 real synthetic locations (…0047, …0060) +
  segmented control (Latency / Availability / Errors).
- **Row: [Recent checks feed — recent-orders analog] [Components roster — top-products ranking]**.

Status vocab mapped: operational→up, degraded_performance→degraded,
under_maintenance→maintenance. Data + relative times from round-1-spec.md content model
(captured live from the running backend). Representative counts (checks/day) are illustrative;
no invented API fields.

## Build & QA

Single self-contained file `prototypes/refimg-dashboard.html` (first line `@dsCard`), Inter via
Google Fonts + system fallback, inline SVG icons/sparklines/chart, dot-field map. Motion per
emil: custom ease-out `cubic-bezier(.23,1,.32,1)`, ≤200ms, `:active` scale(.97),
`transform`/`opacity` only, `@starting-style` stagger, all guarded by `prefers-reduced-motion`.
QA: headless-Chromium screenshots 1440/768 + web-interface-guidelines self-review, then push to
Claude Design project "Uptime Monitor — UI Prototypes".
