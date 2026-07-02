import { http, HttpResponse } from 'msw'
import type { ComponentDTO } from '../../api/types'

export const FIXTURE_COMPONENTS: ComponentDTO[] = [
  { id: 'sockshop-frontend', name: 'Sock Shop — frontend', status: 'operational' },
  { id: 'sockshop-catalogue', name: 'Sock Shop — catalogue', status: 'degraded' },
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
