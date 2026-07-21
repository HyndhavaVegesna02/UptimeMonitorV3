import { http, HttpResponse } from 'msw'
import type { ProposalDTO } from '../../api/types'

/**
 * `GET /api/v1/approvals` fixture (STORY-121). Covers the null-`from_status`
 * case alongside an ordinary transition (a component's first-ever proposal
 * has no prior status).
 */
export const FIXTURE_PROPOSALS: ProposalDTO[] = [
  {
    id: 1,
    component_id: 'sockshop-checkout',
    from_status: 'operational',
    to_status: 'degraded_performance',
    state: 'open',
    proposed_at: '2026-07-21T12:00:00Z',
  },
]

/**
 * Default success handler (STORY-121 AC2 — the Approvals badge count is
 * this array's length). Tests override with `server.use(...)` for the
 * empty/error paths.
 */
export const approvalsHandlers = [
  http.get('/api/v1/approvals', () => {
    return HttpResponse.json(FIXTURE_PROPOSALS)
  }),
]
