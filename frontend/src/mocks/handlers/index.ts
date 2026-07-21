import { approvalsHandlers, FIXTURE_PROPOSALS } from './approvals'
import {
  availabilityHandlers,
  FIXTURE_AVAILABILITY,
  FIXTURE_COMPONENT_AVAILABILITY,
  FIXTURE_TOPOLOGY,
} from './availability'
import { componentsHandlers, FIXTURE_COMPONENTS } from './components'
import { FIXTURE_HISTORY, historyHandlers } from './history'
import { FIXTURE_MAINTENANCE, maintenanceHandlers } from './maintenance'
import { FIXTURE_PUBLICATIONS, publicationsHandlers } from './publications'

/**
 * Composes each feature's MSW handler module into the single array the Node
 * server registers (STORY-121, extended STORY-122). A future story adds
 * `mocks/handlers/<feature>.ts` + spreads it in here, touching no other
 * feature's handlers or fixtures.
 */
export const handlers = [
  ...componentsHandlers,
  ...approvalsHandlers,
  ...historyHandlers,
  ...availabilityHandlers,
  ...maintenanceHandlers,
  ...publicationsHandlers,
]

export {
  FIXTURE_AVAILABILITY,
  FIXTURE_COMPONENT_AVAILABILITY,
  FIXTURE_COMPONENTS,
  FIXTURE_HISTORY,
  FIXTURE_MAINTENANCE,
  FIXTURE_PROPOSALS,
  FIXTURE_PUBLICATIONS,
  FIXTURE_TOPOLOGY,
}


