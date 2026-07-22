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
