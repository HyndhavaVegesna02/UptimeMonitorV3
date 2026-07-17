import { vi } from 'vitest'

type ChangeListener = (event: MediaQueryListEvent) => void

interface MockMediaQueryList {
  matches: boolean
  media: string
  addEventListener: (type: 'change', listener: ChangeListener) => void
  removeEventListener: (type: 'change', listener: ChangeListener) => void
}

/**
 * Shared jsdom `window.matchMedia` stub (ported from `ui-redesign`
 * STORY-096 — salvage list). jsdom does not implement `matchMedia` itself,
 * so every consumer of it needs a stub. This helper is for any test that
 * needs to simulate a media query CHANGING live (the `useMediaQuery` hook's
 * whole reason to exist) — a one-query static-`matches` no-op-listener
 * inline stub is still fine for a test that only needs an initial value.
 */
export function stubMatchMedia(initialMatches: Record<string, boolean> = {}) {
  const lists = new Map<string, { mql: MockMediaQueryList; listeners: Set<ChangeListener> }>()

  function getList(query: string) {
    let entry = lists.get(query)
    if (!entry) {
      const listeners = new Set<ChangeListener>()
      const mql: MockMediaQueryList = {
        matches: initialMatches[query] ?? false,
        media: query,
        addEventListener: (_type, listener) => listeners.add(listener),
        removeEventListener: (_type, listener) => listeners.delete(listener),
      }
      entry = { mql, listeners }
      lists.set(query, entry)
    }
    return entry
  }

  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => getList(query).mql),
  )

  return {
    /** Update a query's `matches` value and notify every listener
     * registered via `addEventListener('change', …)` — mirrors a real
     * viewport resize crossing the query's breakpoint. */
    setMatches(query: string, matches: boolean) {
      const entry = getList(query)
      entry.mql.matches = matches
      const event = { matches, media: query } as MediaQueryListEvent
      for (const listener of entry.listeners) {
        listener(event)
      }
    },
  }
}
