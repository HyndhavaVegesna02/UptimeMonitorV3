import { http, HttpResponse } from 'msw'
import type { AvailabilityDTO } from '../../api/types'

/**
 * `GET /api/v1/availability?signal_key=...` fixture (STORY-122) — the EXACT
 * real response captured from the running local stack (checklist: fixtures
 * derive from a real captured sample), see
 * `docs/scrum/sprints/2026-07-21-sprint-59/live-api-samples.md`. Keyed by
 * `signal_key`, same reasoning as `history.ts`.
 */
export const FIXTURE_AVAILABILITY: Record<string, AvailabilityDTO> = {
  'http-check': {
    availability_pct: 1.0,
    completeness_pct: 0.1451388888888889,
    total_verdicts: 102,
    passing_verdicts: 102,
    maintenance_verdicts: 0,
    gap_verdicts: 618,
    distinct_locations: 2,
    window: '24h',
    computed_at: '2026-07-21T08:00:01.306758Z',
  },
}

/**
 * Default success handler (STORY-122). An unfixtured signal_key resolves to
 * 404, mirroring the real backend's unknown-signal behavior
 * (`availability/controller.py`) rather than fabricating a result.
 */
export const availabilityHandlers = [
  http.get('/api/v1/availability', ({ request }) => {
    const url = new URL(request.url)
    const signalKey = url.searchParams.get('signal_key') ?? ''
    const data = FIXTURE_AVAILABILITY[signalKey]
    if (!data) {
      return HttpResponse.json({ detail: `unknown signal_key ${signalKey}` }, { status: 404 })
    }
    return HttpResponse.json(data)
  }),
]
