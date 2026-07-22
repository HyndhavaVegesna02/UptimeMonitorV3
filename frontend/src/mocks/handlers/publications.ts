import { http, HttpResponse } from 'msw'
import type { PublicationDTO } from '../../api/types'

/**
 * `GET /api/v1/publications` fixture (STORY-133). The live list is currently
 * empty (`docs/scrum/sprints/2026-07-21-sprint-60/plan.md` appendix), so the
 * default handler returns `[]` — the populated shape below is the plan
 * appendix's illustrative `PublicationDTO` sample plus a second entry
 * exercising the null/`failed` edges, used by tests via `server.use(...)`.
 */
export const FIXTURE_PUBLICATIONS: PublicationDTO[] = []

/**
 * A populated, most-recent-first timeline (STORY-133 AC1/AC2). Entry 1 is
 * the plan appendix's exact sample. Entry 2 exercises the edge behaviors:
 * `proposal_id: null` (renders "—", never "0"), `author: null` (renders
 * "—"), and `outcome: 'failed'` paired with an ok-ish `status` — proving
 * `outcome` is never conflated with the health status.
 */
export const FIXTURE_PUBLICATIONS_TIMELINE: PublicationDTO[] = [
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
    component_id: 'http-check',
    status: 'operational',
    published_at: '2026-07-21T07:05:00Z',
    proposal_id: null,
    outcome: 'failed',
    author: null,
  },
]

/** Default success handler (STORY-133) — the live empty list. Tests override
 * with `server.use(...)` for the populated timeline. */
export const publicationsHandlers = [
  http.get('/api/v1/publications', () => {
    return HttpResponse.json(FIXTURE_PUBLICATIONS)
  }),
]
