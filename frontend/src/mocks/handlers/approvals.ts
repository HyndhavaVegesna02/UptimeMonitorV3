import { http, HttpResponse } from 'msw'
import type { DecisionResponse, ProposalDTO } from '../../api/types'

/**
 * `GET /api/v1/approvals` fixture (STORY-121, extended STORY-131). Covers
 * the null-`from_status` case ("New" — a component's first-ever proposal
 * has no prior status) alongside an ordinary transition.
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
  {
    id: 2,
    component_id: 'sockshop-catalogue',
    from_status: null,
    to_status: 'operational',
    state: 'open',
    proposed_at: '2026-07-21T12:05:00Z',
  },
]

/**
 * `POST /api/v1/decisions/{proposal_id}` fixture (STORY-131 — the sprint's
 * first mutating page). Success shape from the plan appendix's illustrative
 * `DecisionResponse` sample. Tests override with `server.use(...)` for the
 * 409/404/other-error paths (a forced 409 and 404 are AC8-required).
 */
export const FIXTURE_DECISION_RESPONSE: DecisionResponse = {
  proposal_id: 1,
  state: 'approved',
  resolved_at: '2026-07-21T12:06:00Z',
}

/**
 * Default success handlers (STORY-121 AC2 — the Approvals badge count is
 * `FIXTURE_PROPOSALS.length`; STORY-131 adds the decision POST). Tests
 * override with `server.use(...)` for the empty/error paths.
 */
export const approvalsHandlers = [
  http.get('/api/v1/approvals', () => {
    return HttpResponse.json(FIXTURE_PROPOSALS)
  }),
  http.post('/api/v1/decisions/:proposalId', () => {
    return HttpResponse.json(FIXTURE_DECISION_RESPONSE)
  }),
]
