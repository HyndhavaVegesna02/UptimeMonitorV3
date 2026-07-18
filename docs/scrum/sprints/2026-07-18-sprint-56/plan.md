# Sprint 56 — UI rewrite wave 2: bento dashboard + availability

**Goal:** The two most-seen pages live on the new identity: the bento mission-control
dashboard (STORY-105) and the availability view (STORY-106).

**Mode:** in-process. **Branch:** `sprint-56` off `ui-rewrite` (@ee63f07, post-sprint-55
merge, 8/8 gate at a41d0a2). Merge back at review; main untouched.
**PO delegation / plan-verifier skip / retro rules:** unchanged (see sprint-55 plan).
**Scope:** 105 (3) + 106 (2) = 5 pts = velocity reference.

**Skill guidance (ui-ux-pro-max, chart domain — binding for 105):** data updates ~1/min →
periodic-refresh visuals, NOT streaming/ticker effects; the current overall state renders
as a large-text KPI (the hero tile); anomaly/status markers are shape+text, never color
alone; sparklines as inline SVG (volume is tiny — no chart library, no new deps);
reduced-motion respected on any pulse/refresh affordance.

## Execution order & steps

### 1. STORY-105 — Bento dashboard (3 pts)
- [x] Step 1: bento grid layout (asymmetric ≥1024px: hero 2x2-ish, tiles flow; stacks at 768/390) — tests first on composition
- [x] Step 2: hero system-status tile (worst-of via deriveOverallStatus, large KPI text + StatusBadge, "since"/context line)
- [x] Step 3: per-component tiles (status accent edge, uptime bar port/re-skin, latency inline-SVG spark from history, last-observed RelativeTime, drill-through link to check-history?signal=)
- [x] Step 4: action tiles (pending approvals / maintenance: neutral-at-zero, accent >0, whole-tile links — rewire orphaned useApprovalsBadge + useMaintenanceWindows) + recent-checks feed tile (latest N, RelativeTime + location labels)
- [x] Step 5: per-tile skeleton/error/empty states (reduced-motion guarded); suite green
- [x] Step 6: live gate (ui-sweep harness): tiles vs API truth, both themes, 390/768/1024/1440, zero console errors
- [x] Scoped DoD gate; reviews spec ∥ quality (3-pointer)

### 2. STORY-106 — Availability (2 pts)
- [ ] Step 1: page scaffold on new tokens (one h1, window switcher 24h/7d/30d in header)
- [ ] Step 2: per-component availability rows/tiles (% + bar) + completeness ("N% of expected checks received") + legend (down vs missing, hatched pattern not color-alone)
- [ ] Step 3: signal drill-down; suite green
- [ ] Step 4: live gate: switcher round-trip, labels, both themes, 390 fit
- [ ] Scoped DoD gate (2-pointer: no reviewer pair)

**Sprint close:** full gate → wiki → journal → delegated review → merge → retro →
sprint 57 (STORY-107 approvals + STORY-108 check history), then 58 (109 + 110 polish + PO package).
