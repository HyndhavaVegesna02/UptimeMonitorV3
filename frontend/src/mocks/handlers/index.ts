import { componentsHandlers, FIXTURE_COMPONENTS } from './components'

/**
 * Composes each feature's MSW handler module into the single array the
 * Node server registers (STORY-041 AC3). A future tab story adds
 * `mocks/handlers/<feature>.ts` + spreads it in here, touching no other
 * feature's handlers or fixtures.
 */
export const handlers = [...componentsHandlers]

// Re-exported so existing call sites (`import { FIXTURE_COMPONENTS } from
// '../mocks/handlers'`) keep working unchanged.
export { FIXTURE_COMPONENTS }
