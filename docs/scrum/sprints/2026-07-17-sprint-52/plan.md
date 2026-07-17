# Sprint 52 — UI redesign wave 1: responsive shell + consistent scaffold

**Goal:** Make the operator dashboard structurally sound as a UI: usable at every
viewport (390 → 1440) and consistent in its page anatomy — the foundation the rest of
the ui-redesign initiative builds on.

**Mode:** in-process. **Branch:** `sprint-52` (off `ui-redesign` — NOT off main; merges
back into `ui-redesign` at review per the PO's 2026-07-17 initiative directive; main is
untouched until the PO's final review of the whole initiative).

**PO delegation note (2026-07-17):** the PO pre-approved sprint plans and per-sprint
review verdicts for this initiative; the final merge decision into main stays with the PO.

**Plan-verifier: SKIPPED** (token economy, PO-approved 2026-07-15) — not contract-
sensitive: both stories are frontend display-layer work against existing, already-consumed
DTOs; no new endpoint/param consumption, no adapter/vendor path, no units/scale logic,
mode is in-process. Skip + reason recorded here for PO visibility.

**Baseline:** full 8-command gate re-run at lock on `sprint-52` HEAD (evidence in
`sprint-current.yaml` `baseline_gate`), since the sprint-51 final gate ran pre-merge.

**Verification strategy (PO directive):** every story's reality gate is a live Playwright
pass against the running local stack (DynamoDB Local :8001 + API :8000 + loop + Vite
:5173, already up), at 390/768/1024/1440, light + dark. Full-viewport headless screenshots
of the sticky sidebar can false-report theme colors (journal, "foundations" note) — use
element screenshots / computed styles for any color claim.

**Dossier/spec anchors:** dossier §17 (two surfaces; operator cockpit), sprint-38 design
brief (`docs/scrum/sprints/2026-07-07-sprint-38/`), `DESIGN-linear.app.md` (adapt, don't
copy), ui-redesign journal (`docs/scrum/ui-redesign/journal.md`) findings #1–#3, #10–#11
and decisions D1–D2.

## Execution order & steps

### 1. STORY-096 — Responsive shell (3 pts) — order 1: highest blast radius (touches the shell every page sits in)
- [ ] Step 1: breakpoint tokens in `tokens.css` (+ a `useMediaQuery`/matchMedia hook) — tests first
- [ ] Step 2: ≤1024px auto-collapse to the existing icon rail (expand still possible; user pref respected on re-widen)
- [ ] Step 3: ≤768px drawer: closed by default, hamburger trigger in top bar, scrim, Escape + scrim-click close, focus trap in/return
- [ ] Step 4: banner + page containers + filter rows fit 390px; tables scroll inside their own container only
- [ ] Step 5: Vitest for hook + drawer behavior; full frontend suite green
- [ ] Step 6: Playwright reality gate: all six tabs × {390, 768, 1024, 1440} × {light, dark}; `scrollWidth <= viewport` assertion per tab; drawer keyboard flow
- [ ] Scoped DoD gate (`--only` npm test / npm build / npm lint) + evidence merge

### 2. STORY-097 — Consistent page scaffold (2 pts) — order 2: builds on the settled shell
- [ ] Step 1: `PageHeader` component (title/subtitle/actions slot) — tests first
- [ ] Step 2: adopt on all six pages; one container-width policy (explicit wide-opt-in prop)
- [ ] Step 3: EmptyState adoption (Maintenance list, Publications, Check History zero-result); Publications empty-copy fix
- [ ] Step 4: Availability legend + range switcher into the header actions slot
- [ ] Step 5: Vitest updates; full frontend suite green
- [ ] Step 6: Playwright reality gate: six tabs, empty + populated states (sample mode for populated approvals; reversed after), heading audit (one h1/page)
- [ ] Scoped DoD gate + evidence merge

**Sprint close:** full 8-command gate on final HEAD (evidence of record) → wiki compile
pass (frontend-zone.md at minimum; blast-radius check on all touched `code_refs`) →
journal sprint-log entry → review (delegated verdict) → merge `sprint-52` → `ui-redesign`
→ retro → next planning.

**Tooling (frozen for the sprint):** Playwright MCP (session-loaded), ui-ux-pro-max skill,
existing local stack. No new Docker resources (PO constraint).
