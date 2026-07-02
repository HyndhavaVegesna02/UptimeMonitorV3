import { http, HttpResponse } from 'msw'
import type { ComponentDTO } from '../../api/types'

export const FIXTURE_COMPONENTS: ComponentDTO[] = [
  { id: 'sockshop-frontend', name: 'Sock Shop — frontend', status: 'operational' },
  { id: 'sockshop-catalogue', name: 'Sock Shop — catalogue', status: 'degraded' },
]

/**
 * Covers every backend `ComponentStatus` value plus one unrecognized string,
 * for the Dashboard tab's status->badge mapping test (STORY-015b AC3): the
 * `toHealthStatus` `?? 'unknown'` guard must render a neutral badge instead
 * of crashing on a status the frontend doesn't recognize.
 */
export const FIXTURE_COMPONENTS_ALL_STATUSES: ComponentDTO[] = [
  { id: 'status-operational', name: 'Operational Component', status: 'operational' },
  { id: 'status-degraded', name: 'Degraded Component', status: 'degraded' },
  {
    id: 'status-partial-outage',
    name: 'Partial Outage Component',
    status: 'partial_outage',
  },
  { id: 'status-major-outage', name: 'Major Outage Component', status: 'major_outage' },
  { id: 'status-mystery', name: 'Mystery Component', status: 'mystery_status' },
]

/**
 * Dashboard/components feature's default success handler (STORY-015a AC3).
 * Tests override with `server.use(...)` for the error/retry paths — MSW is
 * the only mocked I/O edge; nothing mocks the api client or the hook itself.
 */
export const componentsHandlers = [
  http.get('/api/v1/components', () => {
    return HttpResponse.json(FIXTURE_COMPONENTS)
  }),
]
