# Sprint 24 — Retro

**Date:** 2026-06-29
**Sprint:** STORY-015b (3 pts committed / 3 accepted). The first real frontend tab — the Dashboard.

## What went well
- **Cleanest frontend sprint yet:** both Opus reviewers approved first-pass with ZERO blocking findings.
  The external implementer delivered a sound, well-structured tab — the `useComponents` hook removed the
  shell's `eslint-disable set-state-in-effect` (not relocated it), sub-components are module-scope, the
  table is real (`<th scope>`), and the 14 tests genuinely drive behavior (status→badge via accessible
  text, real 500→retry, unknown-status guard).
- **The per-tab pattern is established** (page in `tabs/` + hook in `hooks/`) for 015c–015g to copy, and
  the reviewer's "lift the generic pieces into a shared `components/` layer by tab 2–3" note was captured as
  a tracked chore (STORY-041) rather than lost.
- **Inline-fixing the propagating items paid off:** the two real a11y issues (degraded contrast, role=status
  live-region spam) were fixed in the template before they could be copied into five more tabs.

## What we learned
- **A semantic color token leaked into label TEXT and silently failed contrast.** The degraded badge's
  "Degraded" label was mustard `#d9a441` ≈ 2.2:1 — inherited from the STORY-015a shell, about to propagate.
  This is the kind of a11y defect that hides in "approved" code because the gate doesn't measure contrast.
- **External single-commit cadence, again.** The whole story landed in one commit despite the
  commit-after-green brief. Inherent to external implementation; noted, not amended (third time — accepted
  as a property of the handoff workflow).

## Amendments
- **ADOPTED (PO-approved 2026-06-29):** *Semantic/health color is for non-text cues only (icons/dots/
  borders/backgrounds); label text uses ink and must meet WCAG 4.5:1 — a colored token used as text is a
  review finding.* Written into `.scrum/working-agreements.md` with the motivating incident. The quality
  reviewer enforces it per tab (check the lightest/most-saturated values first).

## Carry-forward (tracked, not amendments)
- **STORY-041 — Frontend pattern hardening** (2 pts, ready): shared `StatusBadge`/`LoadingSkeleton`/
  `ErrorPanel`; data-driven `getStatusBadge`; tokenize the shell `.health-badge--*` `rgba()`; fix off-grid
  `10px` button paddings. Land with/before STORY-015c (the 2nd tab).
- Self-host Inter (shell-level Google Fonts `@import`) — a separate small follow-up.

## Process metrics
- Reviewer rejections: 0 (both first-pass APPROVE/PASS). Inline fix-rounds: 1 (non-blocking polish).
  Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 3 pts, single story, no overrun. Velocity: 3/3. Last-4 (21,22,23,24) = 5,3,5,3.
