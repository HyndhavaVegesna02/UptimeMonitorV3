---
id: STORY-041
title: Frontend pattern hardening — client error-wrapping, shared cx(), modular MSW handlers, catch-all route
type: chore
---

## Context
From the STORY-015a (sprint-25) quality review — six non-blocking MINOR findings, none of which
blocked the shell, but several of which harden the template at its highest-leverage point BEFORE
the six per-tab stories (015b–015g) copy the shell's client/primitives/handlers. Best landed
with or just before the second tab so the seams are tightened before they proliferate. All work
is inside `frontend/`; no backend impact.

## Description / Acceptance Criteria
- [ ] AC1: `frontend/src/api/client.ts::getJson` wraps a malformed-body `SyntaxError` (from
      `response.json()` on a 2xx) into the typed `ApiError`, so the client's contract ("produce a
      typed ApiError on any failure") holds on every realistic path. Test drives a 2xx + invalid
      JSON via MSW and asserts a typed `ApiError` (not a raw `SyntaxError`).
- [ ] AC2: The duplicated `[...].filter(Boolean).join(' ')` classnames idiom in `Button.tsx` /
      `Panel.tsx` (and any other primitive) is factored into a single shared `cx()` helper; the
      primitives use it. (Parallel-shape / shared-assembly agreement, 2026-06-25.)
- [ ] AC3: `frontend/src/mocks/handlers.ts` is modularized so a tab story adds its handlers +
      fixtures in its own module composed into the server, rather than appending to one shared flat
      array — keeping a per-tab story inside its own files.
- [ ] AC4: `frontend/src/AppShell.tsx` renders a catch-all (`*`) route for unknown paths (a simple
      "not found" / redirect-to-Dashboard), tested.
- [ ] AC5: All three frontend DoD gates stay green (`npm test`, `npm run build`, `npm run lint`).

## Open Questions
None.

## History
- 2026-06-29: first raised as STORY-041 in the reverted sprint-24 review; erased by `521764c`.
- 2026-07-02: re-created from the STORY-015a (sprint-25) quality-review minors, re-scoped to the
  Linear-guided shell's actual files. Status: ready. Estimate 2.
