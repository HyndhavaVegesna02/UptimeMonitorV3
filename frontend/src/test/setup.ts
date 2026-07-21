import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from '../mocks/server'

// MSW is the ONLY mocked I/O edge in this suite (2026-06-29 assembly-test
// agreement, frontend edition) — no test patches the api client or a hook
// (STORY-121: re-established after STORY-120's greenfield clean-out).
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
