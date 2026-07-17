# Sprint 54 — UI redesign wave 3: decision support

**Goal:** Close the last two exploration findings: the operator can approve a status change
with real evidence in front of them (STORY-100, journal #4 + #14), and Check History reads
as an operator tool instead of a raw log dump (STORY-101, journal #13).

**Mode:** in-process. **Branch:** `sprint-54` (off `ui-redesign`; merge back at review; main
untouched). **PO delegation:** unchanged; this is the last planned sprint before the
initiative-level polish pass + final PO presentation.

**Plan-verifier: SKIPPED** (token economy, PO-approved 2026-07-15) — frontend display-layer
against existing, already-consumed endpoints (components, history, approvals); STORY-100
consumes the history endpoint from a new page but with the SAME DTO/params the Check History
page already exercises (incl. the STORY-094 limit param); in-process mode.

**Baseline:** ui-redesign @ 1a54f25 (sprint-53 8/8 gate at 71e28ad + merges). Scoped gates
per story; full gate at close (DYNAMO unset, retro-52 A1).

**Verification:** live Playwright per story (retro-52 A2 protocols in force). STORY-100's
populated queue is exercised via sample mode (proposal in → verify → reject → off).

**Scope:** 100 (3 pts) + 101 (2 pts) = 5 = velocity reference. 100 first: higher risk
(cross-page deep link, per-location evidence assembly), and its "View checks" deep link
lands on the page 101 then restyles — the seam (URL params) is agreed in 100.

**Dossier/spec anchors:** dossier §17; journal findings #4, #13, #14, decision D5;
review-52's accepted-with-notes items (fold: Check History unfiltered empty-state icon into
101; Approvals Panel wrap into 100).

## Execution order & steps

### 1. STORY-100 — Approvals decision support (3 pts) — order 1
- [ ] Step 1: evidence assembly hook (per-location latest result for the proposal's signal from the existing history endpoint w/ limit param) — tests first (MSW)
- [ ] Step 2: evidence-first ApprovalCard: friendly component name (slug secondary), transition, RelativeTime "Proposed", per-location rows (status badge + latency + relative time), graceful degradation when history fetch fails (card stays actionable)
- [ ] Step 3: "View checks" deep link → /check-history?signal=…&location=… (URL params drive the existing filters; make them URL-driven if not already — display-layer)
- [ ] Step 4: consequence copy on confirm ("Publishes '<component>: <to-status>' to the public status page."); Approvals Panel wrap (review-52 note)
- [ ] Step 5: full suite green
- [ ] Step 6: reality gate: sample mode on → live proposal card shows evidence + deep link lands filtered → reject, off; MSW-level multi-proposal render covered by tests
- [ ] Scoped DoD gate + evidence merge; spec + quality reviews (3-pointer)

### 2. STORY-101 — Check History readability (2 pts) — order 2
- [ ] Step 1: drop standalone Type column (merge into Component secondary text) — tests first
- [ ] Step 2: latency threshold tint via named tokens (muted <500ms / warn 500–1000 / high >1000)
- [ ] Step 3: sticky header within the table scroll container
- [ ] Step 4: results summary line ("N checks · M down" + filter echo, aria-live=polite) above the table; unfiltered empty state gets the designed EmptyState icon (review-52 note)
- [ ] Step 5: full suite green
- [ ] Step 6: reality gate: live table (thresholds via computed styles vs real latencies), sticky header on scroll, summary counts vs API truth, 390px in-container scroll only
- [ ] Scoped DoD gate + evidence merge

**Sprint close:** full gate → wiki compile → journal → delegated review → merge →
retro → then the initiative-level final polish pass: full six-tab × {390,768,1024,1440} ×
{light,dark} Playwright sweep + a11y audit on ui-redesign HEAD, journal wrap-up, and the
PO presentation package (this is where the PO takes back the wheel).

**Tooling (frozen):** unchanged.
