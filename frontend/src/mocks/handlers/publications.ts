import { http, HttpResponse } from 'msw'
import type { PublicationDTO } from '../../api/types'

/**
 * `GET /api/v1/publications` fixture (STORY-133).
 */
export const FIXTURE_PUBLICATIONS: PublicationDTO[] = [
  {
    id: 1,
    component_id: 'http-check',
    status: 'operational',
    published_at: '2026-07-21T08:05:00Z',
    proposal_id: 1,
    outcome: 'succeeded',
    author: 'dashboard-operator',
  },
  {
    id: 2,
    component_id: 'sockshop-checkout',
    status: 'degraded_performance',
    published_at: '2026-07-21T09:12:00Z',
    proposal_id: null,
    outcome: 'failed',
    author: 'auto-publisher',
  },
]

export const publicationsHandlers = [
  http.get('/api/v1/publications', () => {
    return HttpResponse.json(FIXTURE_PUBLICATIONS)
  }),
]
