import { http, HttpResponse } from 'msw'
import type { PublicationDTO } from '../../api/types'

/**
 * Fixtures derived from the backend's own publications test fixtures — no
 * invented values (2026-07-04 agreement). `component_id`/`status`/
 * `proposal_id`/hour-of-day values mirror
 * `backend/tests/test_publications_endpoint.py::test_get_publications_most_recent_first`
 * (component_id "checkout", `ComponentStatus.DEGRADED`/`OPERATIONAL` at
 * `_utc(10)`/`_utc(12)` on 2026-06-29) and
 * `::test_get_publications_dto_shape` (component_id "login",
 * `ComponentStatus.MAJOR_OUTAGE` at `_utc(8)`, `proposal_id=5`,
 * `PublicationOutcome.FAILED` — STORY-072), plus
 * `backend/tests/test_publication_domain.py::test_publication_with_all_fields`
 * (`proposal_id=42`). Newest-first; covers a non-operational status
 * (`major_outage`, `degraded`), a `proposal_id: null` case (STORY-015g AC1),
 * and BOTH `outcome` values (STORY-072 AC4) — the `login` row is the one
 * `failed` attempt (mirrors the real 401 root cause), the rest `succeeded`.
 */
export const FIXTURE_PUBLICATIONS: PublicationDTO[] = [
  {
    id: 1,
    component_id: 'checkout',
    status: 'operational',
    published_at: '2026-06-29T12:00:00Z',
    proposal_id: null,
    outcome: 'succeeded',
  },
  {
    id: 2,
    component_id: 'login',
    status: 'major_outage',
    published_at: '2026-06-29T10:00:00Z',
    proposal_id: 5,
    outcome: 'failed',
  },
  {
    id: 3,
    component_id: 'checkout',
    status: 'degraded',
    published_at: '2026-06-29T08:00:00Z',
    proposal_id: 42,
    outcome: 'succeeded',
  },
]

/**
 * Publications feature's default success handler (STORY-015g AC1). The LIVE
 * endpoint currently returns `[]` (nothing published yet) — tests override
 * with `server.use(...)` for the empty/error scenarios; MSW is the only
 * mocked I/O edge.
 */
export const publicationsHandlers = [
  http.get('/api/v1/publications', () => {
    return HttpResponse.json(FIXTURE_PUBLICATIONS)
  }),
]
