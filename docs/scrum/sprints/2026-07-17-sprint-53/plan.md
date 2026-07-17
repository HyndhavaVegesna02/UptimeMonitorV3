# Sprint 53 — UI redesign wave 2: operator signal quality

**Goal:** Make what the operator reads trustworthy and human: relative local times instead
of raw ISO-UTC, friendly identities instead of vendor IDs, calm zero-states instead of
false urgency, cross-tab awareness on the dashboard, and honest mode/nav affordances.

**Mode:** in-process. **Branch:** `sprint-53` (off `ui-redesign`; merges back into
`ui-redesign` at review; main untouched — initiative rules, PO directive 2026-07-17).
**PO delegation:** unchanged (plans + per-sprint verdicts pre-approved; final merge is PO's).

**Plan-verifier: SKIPPED** (token economy, PO-approved 2026-07-15) — same rationale as
sprint 52: frontend display-layer only, existing already-consumed DTOs, no new endpoint/param
consumption, in-process mode. Recorded here for PO visibility.

**Baseline:** ui-redesign @ 30895b8 carries sprint-52's full 8/8 gate (45c6086) + a no-ff
merge; treated green. Scoped gates per story; full 8-command gate at sprint close
(DYNAMO_ENDPOINT_URL UNSET per retro-52 A1).

**Verification:** live Playwright reality gate per story (stack already running); element
screenshots / computed styles for any color claim; hard reload before trusting console
errors after HMR (retro-52 A2).

**Scope:** STORY-098 (2) + STORY-099 (2) + STORY-102 (2) = 6 pts vs velocity 5 — accepted
deliberately: all three are small, independent, display-layer stories and wave 1 landed
without rework; if the third story slips it returns to the backlog at review, not mid-sprint.

**Dossier/spec anchors:** dossier §17; sprint-38 design brief tokens; journal findings
#5–#9, #12, #15–#16 and decisions D3–D4; wiki frontend-zone.md (fresh at ff0779e/0f93a79).

## Execution order & steps

### 1. STORY-098 — Human time & identity (2 pts) — order 1: 099's "updated Xs ago" and later stories consume its formatters
- [x] Step 1: `lib/formatTime.ts` (relative + absolute-local + ISO tooltip contract) — tests first (boundaries: <1m, minutes, hours, days, future, invalid)
- [x] Step 2: `lib/formatLocation.ts` (short display form + raw tooltip) — tests first
- [x] Step 3: adopt in Check History, dashboard signals drill-down, Approvals "Proposed", Publications; `<time dateTime>` + title everywhere; minute-tick re-render
- [x] Step 4: Maintenance windows render local time + tz label (raw UTC in tooltip)
- [x] Step 5: full frontend suite green
- [x] Step 6: Playwright reality gate: no bare ISO/microseconds visible on any tab; tooltips carry raw; maintenance round-trip shows local tz
- [x] Scoped DoD gate + evidence merge

### 2. STORY-099 — Signal quality: dashboard + availability (2 pts) — order 2: consumes 098's formatter
- [ ] Step 1: SummaryCard neutral-at-zero logic (color only when >0) — tests first
- [ ] Step 2: replace "Components" card with "Pending approvals" + "Maintenance" action cards (live counts, whole-card link, keyboard-focusable)
- [ ] Step 3: "Updated Xs ago" indicator in Dashboard PageHeader actions (poll-cycle driven, via formatTime)
- [ ] Step 4: Availability completeness relabel ("N% of expected checks received")
- [ ] Step 5: full frontend suite green
- [ ] Step 6: Playwright reality gate: computed-style proof of neutral zeros (healthy state) + colored non-zeros (sample mode ON briefly, reversed); card navigation; label copy
- [ ] Scoped DoD gate + evidence merge

### 3. STORY-102 — Mode & nav affordances (2 pts) — order 3: independent; touches TopBar/rail/maintenance form
- [ ] Step 1: sample-mode control relabel (visible text ≥768px, warning accent when ON, never red) — tests first
- [ ] Step 2: persistent "SAMPLE" chip when ON + banner dismissed (click restores banner)
- [ ] Step 3: collapsed-rail tooltips (hover AND focus) + badge aria-label with count
- [ ] Step 4: maintenance form inline validation (styled errors, aria-describedby, focus-first-invalid, Title required) + success/delete toast (aria-live polite)
- [ ] Step 5: full frontend suite green
- [ ] Step 6: Playwright reality gate: toggle state colors (computed), chip persistence across tabs, tooltip on keyboard focus, form error flow + toast (probe window created + deleted)
- [ ] Scoped DoD gate + evidence merge

**Sprint close:** full 8-command gate (isolated DB) → wiki compile pass → journal sprint log
→ delegated review → merge `sprint-53` → `ui-redesign` → retro → sprint 54 planning
(STORY-100 approvals evidence + STORY-101 check-history readability, 5 pts).

**Tooling (frozen):** unchanged from sprint 52.
