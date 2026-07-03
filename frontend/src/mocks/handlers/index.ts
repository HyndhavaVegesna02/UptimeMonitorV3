import {
  componentsHandlers,
  FIXTURE_COMPONENTS,
  FIXTURE_COMPONENTS_ALL_STATUSES,
} from './components'
import { approvalsHandlers, FIXTURE_PROPOSALS } from './approvals'
import {
  availabilityHandlers,
  FIXTURE_AVAILABILITY_BY_COMPONENT,
  FIXTURE_TOPOLOGY,
} from './availability'

/**
 * Composes each feature's MSW handler module into the single array the
 * Node server registers (STORY-041 AC3). A future tab story adds
 * `mocks/handlers/<feature>.ts` + spreads it in here, touching no other
 * feature's handlers or fixtures.
 */
export const handlers = [
  ...componentsHandlers,
  ...approvalsHandlers,
  ...availabilityHandlers,
]

// Re-exported so existing call sites (`import { FIXTURE_COMPONENTS } from
// '../mocks/handlers'`) keep working unchanged.
export {
  FIXTURE_COMPONENTS,
  FIXTURE_COMPONENTS_ALL_STATUSES,
  FIXTURE_PROPOSALS,
  FIXTURE_AVAILABILITY_BY_COMPONENT,
  FIXTURE_TOPOLOGY,
}
