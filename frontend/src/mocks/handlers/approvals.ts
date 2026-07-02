import { http, HttpResponse } from 'msw'
import type { DecisionResponse, ProposalDTO } from '../../api/types'

/**
 * Covers the null-`from_status` case (a component's first-ever proposal has
 * no prior status — STORY-015c AC1) alongside an ordinary transition.
 */
export const FIXTURE_PROPOSALS: ProposalDTO[] = [
  {
    id: 1,
    component_id: 'sockshop-frontend',
    from_status: 'operational',
    to_status: 'degraded',
    state: 'open',
    proposed_at: '2026-07-01T12:00:00Z',
  },
  {
    id: 2,
    component_id: 'sockshop-catalogue',
    from_status: null,
    to_status: 'major_outage',
    state: 'open',
    proposed_at: '2026-07-02T08:30:00Z',
  },
]

/**
 * Approvals/decisions feature's default success handlers (STORY-015c AC1/
 * AC2). Tests override with `server.use(...)` for the empty/error/409/404
 * paths — MSW is the only mocked I/O edge; nothing mocks the api client or
 * the hook/page itself.
 */
export const approvalsHandlers = [
  http.get('/api/v1/approvals', () => {
    return HttpResponse.json(FIXTURE_PROPOSALS)
  }),
  http.post('/api/v1/decisions/:proposalId', async ({ params }) => {
    const response: DecisionResponse = {
      proposal_id: Number(params.proposalId),
      state: 'resolved',
      resolved_at: '2026-07-02T09:00:00Z',
    }
    return HttpResponse.json(response)
  }),
]
