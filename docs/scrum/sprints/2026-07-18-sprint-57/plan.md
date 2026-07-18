# Sprint 57 — UI rewrite wave 3: decision surfaces

**Goal:** The operator's decision pages live on the new identity: evidence-first approvals
(STORY-107) and the dense check-history table (STORY-108).

**Mode:** in-process. **Branch:** `sprint-57` off `ui-rewrite` (@0f0dd49; sprint-56 8/8 gate
at 67631c7). **Delegation/plan-verifier-skip/retro rules:** unchanged. **Scope:** 3+2=5 pts.

**Skill guidance (ui-ux-pro-max, ux domain — binding):** forms/feedback rules for confirms
(explicit consequence copy, error recovery paths); table rules (sortable/aria-sort optional,
sticky header, tabular numerals, aria-live result summaries); status never color-alone.

## Execution order & steps

### 1. STORY-107 — Approvals evidence queue (3 pts)
- [ ] Step 1: evidence hook port (per-location latest results via existing history endpoint w/ limit; salvage useProposalEvidence semantics from ui-redesign) — MSW tests first
- [ ] Step 2: evidence-first card on Tile language (friendly name + slug secondary, transition StatusBadges, Proposed RelativeTime, per-location rows, skeleton/degrade-gracefully-still-actionable)
- [ ] Step 3: "View checks" deep link ?signal= (Check History accepts it in 108 — land the param contract here behind the existing page placeholder if 108 not yet merged: link renders, target seeds when page exists)
- [ ] Step 4: approve confirm consequence copy ("Publishes '<component>: <status>' to the public status page."), reject unchanged; designed Queue-clear empty state
- [ ] Step 5: suite green; scoped gate; reviews spec ∥ quality
- [ ] Step 6: live gate: sample-mode proposal round-trip (evidence rows vs API, confirm copy, reject, off)

### 2. STORY-108 — Check history table (2 pts)
- [ ] Step 1: filters (search/result/location/window) + ?signal= URL seed — tests first
- [ ] Step 2: dense mono table (RelativeTime, location labels, latency threshold tint via tokens, sticky header, aria-live summary "N checks · M down")
- [ ] Step 3: designed zero-result + unfiltered empty states; suite green
- [ ] Step 4: live gate: filters + URL seed, computed-style tint thresholds, sticky header, 390 in-container scroll only
- [ ] Scoped DoD gate (2-pointer)

**Sprint close:** full gate → wiki → journal → review → merge → retro → sprint 58
(STORY-109 maintenance + STORY-110 publications/polish/PO package).
