import { http, HttpResponse } from 'msw'
import type { ObservationDTO } from '../../api/types'

/**
 * `GET /api/v1/history?signal_key=...` fixture (STORY-122) — the EXACT real
 * response captured from the running local stack (checklist: fixtures
 * derive from a real captured sample), see
 * `docs/scrum/sprints/2026-07-21-sprint-59/live-api-samples.md`. Keyed by
 * `signal_key` so the handler below can serve per-signal data without
 * hardcoding a single key — an unknown signal_key resolves to `[]` rather
 * than a fabricated shape.
 */
export const FIXTURE_HISTORY: Record<string, ObservationDTO[]> = {
  'http-check': [
    {
      signal_key: 'http-check',
      observed_at: '2026-07-21T07:58:41.133000Z',
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000060',
      latency_ms: 588,
      response_status_code: 200,
      check_type: 'http',
    },
    {
      signal_key: 'http-check',
      observed_at: '2026-07-21T07:57:41.375000Z',
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000047',
      latency_ms: 951,
      response_status_code: 200,
      check_type: 'http',
    },
    {
      signal_key: 'http-check',
      observed_at: '2026-07-21T07:56:41.164000Z',
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000047',
      latency_ms: 293,
      response_status_code: 200,
      check_type: 'http',
    },
    {
      signal_key: 'http-check',
      observed_at: '2026-07-21T07:56:41.164000Z',
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000060',
      latency_ms: 561,
      response_status_code: 200,
      check_type: 'http',
    },
    {
      signal_key: 'http-check',
      observed_at: '2026-07-21T07:54:41.274000Z',
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000060',
      latency_ms: 570,
      response_status_code: 200,
      check_type: 'http',
    },
    {
      signal_key: 'http-check',
      observed_at: '2026-07-21T07:53:41.570000Z',
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000047',
      latency_ms: 331,
      response_status_code: 200,
      check_type: 'http',
    },
    {
      signal_key: 'http-check',
      observed_at: '2026-07-21T07:52:41.508000Z',
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000060',
      latency_ms: 904,
      response_status_code: 200,
      check_type: 'http',
    },
    {
      signal_key: 'http-check',
      observed_at: '2026-07-21T07:51:41.147000Z',
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000047',
      latency_ms: 356,
      response_status_code: 200,
      check_type: 'http',
    },
  ],
}

/**
 * Default success handler (STORY-122). Reads `signal_key` off the request
 * URL so a caller for an unfixtured key gets `[]` (an honest empty window)
 * rather than silently returning another signal's data. Tests override with
 * `server.use(...)` for the error path.
 */
export const historyHandlers = [
  http.get('/api/v1/history', ({ request }) => {
    const url = new URL(request.url)
    const signalKey = url.searchParams.get('signal_key') ?? ''
    return HttpResponse.json(FIXTURE_HISTORY[signalKey] ?? [])
  }),
]
