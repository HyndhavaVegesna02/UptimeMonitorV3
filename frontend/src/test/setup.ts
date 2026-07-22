import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { resetFetchDedupCache } from '../lib/fetchDedup'
import { server } from '../mocks/server'

// MSW is the ONLY mocked I/O edge in this suite (2026-06-29 assembly-test
// agreement, frontend edition) — no test patches the api client or a hook
// (STORY-121: re-established after STORY-120's greenfield clean-out).
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  server.resetHandlers()
  // STORY-137's dedupedFetch cache is a process-wide singleton keyed on
  // fetcher identity (e.g. the module-level `getApprovals`/`getComponents`
  // exports) — reset it alongside the MSW handlers so a test that
  // deliberately never resolves a fetch (to assert the loading state)
  // cannot leave an orphaned in-flight entry that silently starves every
  // LATER test sharing that same reference.
  resetFetchDedupCache()
})
afterAll(() => server.close())

// jsdom does not implement `window.matchMedia` (STORY-121's
// `useMediaQuery` — desktop-rail vs mobile-sheet breakpoint detection —
// needs it). Defaults every query to non-matching ("mobile"); individual
// tests that need the desktop breakpoint stub `window.matchMedia`
// themselves via `vi.stubGlobal`.
if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    }) as MediaQueryList
}
