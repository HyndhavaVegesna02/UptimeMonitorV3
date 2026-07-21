import { http, HttpResponse } from 'msw'
import type {
  AvailabilityDTO,
  ComponentAvailabilityDTO,
  ComponentTopologyDTO,
} from '../../api/types'

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

export const FIXTURE_COMPONENT_AVAILABILITY: Record<string, ComponentAvailabilityDTO> = {
  'http-check': {
    component_id: 'http-check',
    rollup: {
      availability_pct: 1.0,
      completeness_pct: 0.0930555,
      total_verdicts: 65,
      passing_verdicts: 65,
      maintenance_verdicts: 0,
      gap_verdicts: 655,
      distinct_locations: 0,
      window: '24h',
      computed_at: '2026-07-21T18:20:42Z',
    },
    signals: [
      {
        availability_pct: 1.0,
        completeness_pct: 0.0930555,
        total_verdicts: 65,
        passing_verdicts: 65,
        maintenance_verdicts: 0,
        gap_verdicts: 655,
        distinct_locations: 2,
        window: '24h',
        computed_at: '2026-07-21T18:20:42Z',
        signal_key: 'http-check',
      },
    ],
  },
}

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
  http.get('/api/v1/topology', () => {
    return HttpResponse.json(FIXTURE_TOPOLOGY)
  }),
  http.get('/api/v1/availability/component/:componentId', ({ params }) => {
    const componentId = String(params.componentId)
    const data = FIXTURE_COMPONENT_AVAILABILITY[componentId]
    if (!data) {
      return HttpResponse.json(
        { detail: `unknown component_id ${componentId}` },
        { status: 404 },
      )
    }
    return HttpResponse.json(data)
  }),
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

