# STORY-137 — Shared fetch dedup/cache

- **Status:** ready
- **Points:** 3
- **Sprint:** 61
- **Type:** defect
- **Scope:** frontend only

## Context
From the 2026-07-22 design-QA review, verified: the shell and the Dashboard page each
fetch `/components` and `/approvals` independently (2× each on a Dashboard mount; 1×
`/maintenance`), and there is no cache/dedup layer. The review's "3–4× / header+sidebar+
cards" was overstated/mis-attributed (shell passes results to sidebar+topbar via props),
but the underlying duplication + missing dedup is real.

## Acceptance criteria
- **AC1** — On a Dashboard mount, each distinct endpoint (`/components`, `/approvals`,
  `/maintenance`) fires **exactly once**, not once per consuming component. Proven by an MSW
  request-count assertion (handler call count == 1 per endpoint across shell + page).
- **AC2** — The dedup layer is **in-house and minimal** — a small shared request cache /
  promise-coalescing keyed on fetch identity. NO new heavy dependency (no React Query/SWR).
  Stale-while-revalidate / background refetch is out of scope (YAGNI).
- **AC3** — No refetch loop; stable-fetcher discipline preserved; a fetch error still
  surfaces `ErrorState`; retry re-issues a **real** request (not a cached failure).
- **AC4** — No behavioral regression on any fetching page (Availability/History/Approvals/
  Maintenance/Publications). Gates green.

## Design / skills
Honor the mandated skills. Keep the abstraction small and local to `lib/` — do not
introduce a global state library. Coordinate with STORY-136 AC3 (both touch `useFetch`);
136 lands first.
