import { http, HttpResponse } from 'msw'
import type { ComponentTopologyDTO } from '../../api/types'

/**
 * `GET /api/v1/topology` fixture (STORY-129) — the EXACT real response
 * captured from the running local stack (checklist: fixtures derive from a
 * real captured sample), see `docs/scrum/sprints/2026-07-21-sprint-60/plan.md`
 * §Appendix.
 */
export const FIXTURE_TOPOLOGY: ComponentTopologyDTO[] = [
  {
    id: 'http-check',
    name: 'HTTP Check',
    signals: [
      {
        signal_key: 'http-check',
        name: 'HTTP Check',
        interval_seconds: 120,
        component_id: 'http-check',
      },
    ],
  },
]

/**
 * Default success handler (STORY-129). Tests override with `server.use(...)`
 * for the empty/error paths and for multi-component scenarios.
 */
export const topologyHandlers = [
  http.get('/api/v1/topology', () => {
    return HttpResponse.json(FIXTURE_TOPOLOGY)
  }),
]
