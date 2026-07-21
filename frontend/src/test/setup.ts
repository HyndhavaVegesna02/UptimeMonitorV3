import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from '../mocks/server'

// MSW is the ONLY mocked I/O edge in this suite (2026-06-29 assembly-test
// agreement, frontend edition) — no test patches the api client or a hook
// (STORY-121: re-established after STORY-120's greenfield clean-out).
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
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
