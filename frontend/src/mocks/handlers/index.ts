import { approvalsHandlers, FIXTURE_PROPOSALS } from './approvals'
import { componentsHandlers, FIXTURE_COMPONENTS } from './components'

/**
 * Composes each feature's MSW handler module into the single array the Node
 * server registers (STORY-121). A future story adds
 * `mocks/handlers/<feature>.ts` + spreads it in here, touching no other
 * feature's handlers or fixtures.
 */
export const handlers = [...componentsHandlers, ...approvalsHandlers]

export { FIXTURE_COMPONENTS, FIXTURE_PROPOSALS }
