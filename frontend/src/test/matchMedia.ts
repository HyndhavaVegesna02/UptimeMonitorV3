import { vi } from 'vitest'

type ChangeListener = (event: MediaQueryListEvent) => void

interface MockMediaQueryList {
  matches: boolean
  media: string
  addEventListener: (type: 'change', listener: ChangeListener) => void
  removeEventListener: (type: 'change', listener: ChangeListener) => void
}

/**
 * Shared jsdom `window.matchMedia` stub (STORY-096) — jsdom does not
 * implement `matchMedia` itself, so every consumer of it needs a stub. Five
 * call sites (`App.test.tsx`, `AppShell.test.tsx`, `ThemeContext.test.tsx`,
 * `resolveTheme.test.ts`, `TopBar.test.tsx`) already hand-roll a one-query,
 * static-`matches`, no-op-listener version inline; this helper is the
 * shared replacement for any NEW test that also needs to simulate a media
 * query CHANGING live (the `useMediaQuery` hook's whole reason to exist) —
 * see that hook's test file for the intended usage. Rewriting the five
 * existing ad-hoc copies is deliberately out of this story's scope (no
 * behavior of theirs needs the live-change capability).
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
