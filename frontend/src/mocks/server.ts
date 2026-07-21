import { setupServer } from 'msw/node'
import { handlers } from './handlers'

/** Node MSW server for tests (src/test/setup.ts wires its lifecycle). */
export const server = setupServer(...handlers)
