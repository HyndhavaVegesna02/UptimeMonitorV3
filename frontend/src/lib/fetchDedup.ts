/**
 * In-house promise-coalescing cache (STORY-137). `useFetch` routes every
 * fetch through this so concurrent calls to the SAME stable fetcher — e.g.
 * the shell (`ShellLayout`) and the Dashboard page both calling the literal
 * module-level `getComponents` export at mount time — share ONE underlying
 * network request instead of each firing its own (the "2× components / 2×
 * approvals on a Dashboard mount" finding this story fixes).
 *
 * Deliberately NOT a cache of RESULTS — no stale-while-revalidate, no TTL,
 * no background refetch (AC2's explicit YAGNI). An entry lives in the map
 * ONLY while its request is in flight and is removed the instant it settles
 * (success OR failure). A later call — including a `retry` after an error —
 * always finds an empty slot for that fetcher and genuinely re-invokes it;
 * nothing is ever served from a stale success or a cached failure (AC3).
 *
 * Keyed by the fetcher's OWN identity, never a derived/guessed key: two
 * different function references are two different requests, full stop, so
 * this never wrongly coalesces genuinely distinct calls. A fetcher whose
 * request depends on arguments (e.g. `ComponentAvailabilityCard`'s
 * `getComponentAvailability(component.id, { since, until })`) is already a
 * fresh `useCallback` per distinct argument set (the existing stable-fetcher
 * discipline `useFetch` requires of every caller) — its identity changes
 * exactly when its arguments do, so keying on identity alone is correct
 * without this module needing to know anything about a fetcher's arguments.
 */
const inFlight = new Map<() => Promise<unknown>, Promise<unknown>>()

export function dedupedFetch<T>(fetcher: () => Promise<T>): Promise<T> {
  const existing = inFlight.get(fetcher)
  if (existing) {
    return existing as Promise<T>
  }

  const promise = fetcher().finally(() => {
    inFlight.delete(fetcher)
  })
  inFlight.set(fetcher, promise)
  return promise
}

/**
 * Evicts a fetcher's in-flight entry (if any) WITHOUT touching the promise
 * itself — a harmless no-op when nothing is in flight for it. Exists for
 * `useFetch`'s own client-side request timeout (STORY-136 AC3): a fetcher
 * that never settles would otherwise leave a permanent in-flight entry
 * behind (its `.finally` never runs), so a later `retry` would silently
 * rejoin the same still-hung promise instead of issuing a genuinely fresh
 * request. Calling this when the timeout fires clears the slot so the next
 * `dedupedFetch(fetcher)` call — the retry — always starts a real request.
 */
export function forgetFetch(fetcher: () => Promise<unknown>): void {
  inFlight.delete(fetcher)
}

/**
 * Wipes every in-flight entry, including a never-settling one whose own
 * `.finally` will never run to self-evict it. The module-level cache is a
 * process-wide singleton, so the test suite's own hygiene boundary (a test
 * that deliberately renders a component against a NEVER-resolving handler,
 * to assert its loading state, and returns without ever awaiting
 * settlement) must reset it between tests — `src/test/setup.ts` calls this
 * in the shared `afterEach`, the same place `server.resetHandlers()` lives
 * — otherwise that orphaned in-flight promise would silently poison every
 * later test in the process that shares the same fetcher reference (e.g.
 * `getApprovals`), which never actually calls the real (per-test) MSW
 * handler again. Production code never needs to call this.
 */
export function resetFetchDedupCache(): void {
  inFlight.clear()
}
