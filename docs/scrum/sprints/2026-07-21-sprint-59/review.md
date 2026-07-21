# Sprint 59 — Review

**Goal:** Stand up the new greenfield frontend on the approved *refimg*-derived visual language —
a documented design system + Phosphor icons (STORY-120), the re-skinned collapsible app shell
(STORY-121), and the full Dashboard live on real backend data (STORY-122). One complete, demoable
vertical slice = the approved prototype, running on real data.

**Outcome:** All three stories **Done**. Full 8-command DoD gate **green** on final HEAD
`1760067`. Branch `sprint-59` is **NOT merged to main** — per the PO's greenfield-then-swap
decision, acceptance at this review *is* the swap.

**Mode:** in-process. **Branch:** `sprint-59` (off the `ui-prototype` line @280cac2).
**Reference:** the approved prototype `docs/scrum/sprints/2026-07-18-ui-prototyping/prototypes/refimg-dashboard.html`.

---

## How to demo
Local stack (DynamoDB Local :8001 + API :8000 + pull-loop + Vite :5173) — open
**http://localhost:5173**. `/dashboard` (real data), the collapsible sidebar (persists across
reload), the mobile sheet (<860px), and `/styleguide` (every primitive × state). NOTE: the
Dashboard's availability-dependent regions take ~20s to first-paint locally — a DynamoDB-Local
perf artifact, see STORY-127 below (values render exactly correct once loaded).

---

## STORY-120 — Design-system foundation + Phosphor (3 pts) — DONE
Fresh three-layer token system (`tokens.css`), Phosphor `Icon` wrapper (decorative-or-labelled
prop-enforced), core primitives (Button/Panel/StatusBadge/SummaryCard/Sparkline/Loading/Error/
Empty), a `/styleguide` gallery, and the `frontend-design-system.md` wiki article. WCAG-AA contrast
enforced by a token test computing real luminance; a no-raw-hex test scans component files.
- **Reviews:** spec FAIL→fixed (AC5 Sparkline animated `stroke-dashoffset`, not transform/opacity —
  the test enshrined the breach; fixed + story History deletion-rationale added). quality
  FIX_REQUIRED→fixed (CLAUDE.md frontend section was stale — Geist→Inter, deleted trees — corrected;
  + two three-layer-token-integrity minors).
- **Scoped DoD:** green (`024d0e4`). **Reality gate:** live `/styleguide` render, 0 console errors,
  matches the approved visual language.

## STORY-121 — App shell: collapsible sidebar + topbar, responsive, first-class motion (3 pts) — DONE
Grouped sidebar (Monitoring/Operations/Pinned) with Phosphor icons + `aria-current`; a minimal typed
API client (`/components`, `/approvals`) + MSW harness; worst-of overall-status pill (dot+icon+text);
collapsible desktop rail (localStorage-persisted, no-flash pre-paint) with delayed tooltips;
off-canvas mobile sheet (Escape/backdrop dismiss + focus-return); first-class motion (transform/
opacity only, ≤250ms, reduced-motion guarded).
- **Crash recovery:** the first implementer session hit a usage limit mid-story; the commit-per-green-step
  cadence contained it — 4 green commits + coherent uncommitted work preserved, one orphan scrap
  discarded, resume point checkpointed, resumed cleanly.
- **Reviews:** spec PASS (all 9 ACs). quality FIX_REQUIRED→fixed — **CRITICAL:** the pre-paint
  collapse class outlived hydration (higher CSS specificity pinned the sidebar at the 64px rail after
  a collapsed-reload+expand — a real bug the jsdom tests couldn't catch); **MAJOR:** the Approvals
  count was `aria-hidden` with no screen-reader conveyance. Both fixed (+ last-updated-at-fetch and
  `:active` press feedback).
- **Scoped DoD:** green (`617d362`). **Reality gate (live, scripted Chromium):** renders TRUTHFULLY
  to live API (badge=0→none, pill=Up=worst-of live components, PINNED=real "HTTP Check" — not the
  prototype's mock); CRITICAL fix verified (load-collapsed→expand → full 240px, no clipping); AC5
  persistence bidirectional; mobile sheet + Escape/focus-return; no h-scroll @ 375/768/1024/1440;
  motion 0.22s under no-preference → 0s under emulated reduce; 0 console errors.

## STORY-122 — Dashboard page on real data (3 pts) — DONE
KPI row (availability 24h, avg latency, components healthy n/total, pending approvals — with inline
SVG sparklines, deltas OMITTED not fabricated), response-time chart (inline SVG, real spike callout,
`role="img"`+aria-label), probe-locations panel (segmented control, `aria-pressed`), upcoming-
maintenance, recent-checks feed, components roster. API client extended (`/history`, `/availability`,
`/maintenance`) typed from the live contracts; fixtures from real captured responses.
- **Reviews:** spec PASS (all 7 ACs; deltas omitted; exactly-one-h1 verified end-to-end). quality
  FIX_REQUIRED→fixed — **MAJOR:** the chart legend labeled the raw per-check series "Median response"
  (no median computed — a false statistic contradicting its own aria-label); relabeled to "Response
  time" + regression test. Truthful-rendering check otherwise excellent.
- **Scoped DoD:** green (`93a97c7`). **Reality gate (live):** every rendered number EXACT vs live
  `/api/v1` — availability 100.00% (avail_pct 1.0), avg 439ms + spike 865ms@…0060 (computed from
  history, exact), 1/1 healthy, 0 approvals, 2 probe locations, empty maintenance→empty state. Chart
  relabel confirmed live. 0 console errors; no h-scroll @ 390 + 1440.

---

## Findings filed to backlog (not blocking; from reviews + reality gates)
- **STORY-123** — control/button height 36px < 44px touch target (matches the prototype; desktop-first).
- **STORY-124** — extend contrast test to muted/secondary text on the canvas backdrop.
- **STORY-125** — mobile-sheet full keyboard focus-trap + `role="dialog"`/`aria-modal`.
- **STORY-126** — skip-to-content link in the shell.
- **STORY-127** *(defect)* — `/api/v1/availability` is slow (~20–120s) against DynamoDB-Local
  (single-threaded, serializes queries behind the 24h scan) → the Dashboard first-paint stalls. Likely
  a local-stack artifact; VERIFY on real DynamoDB before optimizing. Backend (frozen this sprint).
- **STORY-128** — Dashboard: lazy-load the availability-dependent KPI so fast regions paint first; +
  dedupe the components/approvals double-fetch (shell + page).

## DoD evidence of record — full 8-command gate, final HEAD `1760067`
pytest 529 passed · import-linter 8/8 kept · ruff check · ruff format · cfn-lint · npm test 403
passed (53 files) · npm build · npm lint — all exit 0. Wiki compile pass CLEAN (sweep/facts/links/
integrity); `frontend-zone.md` archived+rewritten, `sample-mode.md` frontend section rehabbed.

## Not done / out of scope (as planned)
The five non-Dashboard tabs (Availability/History/Approvals/Maintenance/Publications) are intentional
placeholders — sprints 60–61. No sample-mode UI in the new frontend (backend feature intact).

## PO decision
Accept → merge `sprint-59` to `ui-prototype` (the swap). Reject → back to backlog with feedback,
commits stay off the branch tip. Per-story accept/reject also available.
