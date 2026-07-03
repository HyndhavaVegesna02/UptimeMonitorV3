---
id: STORY-049
title: Sample switch (frontend) — Dashboard toggle wired to the sample-mode API
type: feature
---

## Context
Frontend half of the PO's sample-switch idea (2026-07-03); backend substrate is STORY-048
(HARD dependency — the flag API must exist). All work inside `frontend/`; the three frontend
DoD gates apply; backend untouched.

## Description
A switch control on the Dashboard tab showing the current sample-mode state and toggling it via
the STORY-048 API. While ON, the operator is unmistakably warned that incoming signals are being
recorded as DOWN (simulated outage).

## Acceptance Criteria
- [ ] AC1: the Dashboard tab renders a sample-switch control reflecting the current state from
      the API on load (accessible: real switch semantics, labeled; keyboard-operable).
- [ ] AC2: toggling calls the mutate endpoint and reflects the new state on success; a failed
      mutate surfaces the shell's error affordance and does NOT show the flipped state. Tested
      via MSW (success, failure, and load-state cases — MSW is the only mocked edge).
- [ ] AC3: while ON, the Dashboard shows a clearly visible "sample mode — signals recorded as
      DOWN" warning (tokens, not raw hex; health palette discipline per the shell conventions).
- [ ] AC4: DTO fields rendered are verified against the real STORY-048 `models.py` at planning
      (2026-07-02 consumer-tab agreement).
- [ ] AC5: `npm test`, `npm run build`, `npm run lint` all exit 0 on a clean committed tree.

## Open Questions
None — visual shape follows the existing shell primitives; exact copy is implementer's choice
within AC3's wording.

## History
- 2026-07-03: drafted alongside STORY-048 (backend). Estimate 2. Depends on STORY-048.
