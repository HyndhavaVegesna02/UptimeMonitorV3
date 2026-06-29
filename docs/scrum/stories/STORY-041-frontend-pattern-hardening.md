---
id: STORY-041
title: Frontend pattern hardening — shared tab components + token/grid cleanups
type: chore
---

## Context
From the Sprint 24 review (STORY-015b, the first tab + per-tab template). Both Opus reviewers approved the
Dashboard but flagged non-blocking items that would multiply as the next five tabs (015c–015g) copy the
pattern. Land this with or before the 2nd tab (STORY-015c) to avoid 6× copy-paste drift.

## Acceptance Criteria
- [ ] AC1: Extract the generic tab pieces into a shared `frontend/src/components/` layer — at least
      `StatusBadge`, `LoadingSkeleton`, `ErrorPanel` — and have the Dashboard consume them (no behavior
      change; tests stay green). These are what every tab needs.
- [ ] AC2: Data-drive `getStatusBadge` — replace the ~5 near-duplicate SVG/markup branches with a
      `status → { label, glyph }` map (the unknown-status defensive branch preserved). Keep the icon+label,
      ink text, icon-colored-by-health-token behavior.
- [ ] AC3: Tokenize the shell's `.health-badge--up/down/degraded/maintenance` border/background `rgba(...)`
      literals into named CSS vars (the badge label-text contrast fix from 015b stays; only the
      border/bg literals move into the token layer).
- [ ] AC4: Fix off-grid spacing literals on the buttons (`padding: 10px 16px/18px`, `fontSize: 14px`) — use
      a shared `.btn` size class on the 4px grid + the design's button type, replacing per-call inline px.
- [ ] AC5: Frontend DoD gate green (typecheck/lint/test/build); all existing tests pass; no visual
      regression to the Dashboard. Backend untouched (Python gate stays green).

## Out of scope
- New tab bodies (those are 015c–015g). Self-hosting Inter (separate follow-up). A routing library.

## History
- 2026-06-29: created from the Sprint 24 review (STORY-015b) non-blocking findings. 2 pts. Status: ready.
