# Sprint 58 — UI rewrite wave 4 (FINAL): maintenance + publications + polish + PO package

**Goal:** Complete the rewrite: maintenance (STORY-109), publications (STORY-110 part 1),
then the initiative-level polish matrix and the PO presentation package (STORY-110 part 2).
After this sprint the PO takes back the wheel for the merge review.

**Mode:** in-process. **Branch:** `sprint-58` off `ui-rewrite` (@533943d; sprint-57 8/8 gate).
**Delegation/retro rules:** unchanged (incl. 57-A1 atomic gate calls, 57-A2 existence-verified
salvage pointers). **Scope:** 2+3=5 pts.

**Skill guidance (ui-ux-pro-max forms domain — binding for 109):** visible labels (never
placeholder-only), inline validation on submit (error below field, aria-describedby,
focus-first-invalid), required indicators, success feedback (polite toast, no focus steal),
confirm destructive actions, semantic input types.

## Execution order & steps

### 1. STORY-109 — Maintenance (2 pts)
- [ ] Step 1: form on Tile language: Title/Reason/Component/Start/End, noValidate + validateMaintenanceForm salvage (EXISTENCE-VERIFIED: git cat-file confirms features/maintenance/fieldError.ts's validateMaintenanceForm on ui-redesign) — tests first
- [ ] Step 2: windows list: WYSIWYG local time + tz label (raw UTC tooltip; formatLocalRange EXISTENCE-VERIFIED on ui-redesign lib/formatTime.ts), Upcoming/Active chips, delete confirm, designed empty state
- [ ] Step 3: create/delete polite toasts (Toast contract salvage: components/Toast on ui-redesign); suite green
- [ ] Step 4: live gate: empty-submit error flow, probe create/delete round-trip w/ toasts (probe cleaned), 390, both themes
- [ ] Scoped gate (2-pointer)

### 2. STORY-110 — Publications + polish + package (3 pts)
- [ ] Step 1: publications page (timeline/list on Tile language, outcome + author when present, RelativeTime, count subtitle only when populated, designed empty state) — tests first
- [ ] Step 2: polish pass from the fold-forward list: <=480px brand sr-only; .text-label class defined or removed; low-tile-count grid balance; shared matchMedia stub adoption where trivial
- [ ] Step 3: suite green; scoped gate; reviews spec ∥ quality (3-pointer)
- [ ] Step 4 (orchestrator): FULL polish matrix — six tabs x {390,768,1024,1440} x {light,dark} scripted sweep, keyboard walkthrough, console/network audit, contrast spot checks
- [ ] Step 5 (orchestrator): journal wrap-up + PO presentation package (before/after screenshots, initiative summary)

**Sprint close:** full gate → wiki compile → review → merge to ui-rewrite → retro →
STOP: present the finished rewrite to the PO for the merge-to-main decision.
