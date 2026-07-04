import { http, HttpResponse } from 'msw'
import type { ObservationDTO } from '../../api/types'

/**
 * Factory for one observation row, defaulted to the LIVE wire sample pinned
 * in the sprint-33 plan (2026-07-04 agreement — fixtures MUST derive from
 * this shape/scale, never invented values):
 * `{"signal_key":"http-check","observed_at":"2026-07-03T13:29:17.931000Z",
 * "health":"up","location":"SYNTHETIC_LOCATION-0000000000000060",
 * "latency_ms":571}` — fractional-second ISO UTC timestamp, integer-ms
 * latency, raw vendor location id string.
 */
function makeObservation(overrides: Partial<ObservationDTO> = {}): ObservationDTO {
  return {
    signal_key: 'frontend-http',
    observed_at: '2026-07-03T13:29:17.931000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: 571,
    ...overrides,
  }
}

/**
 * `frontend-http` fixture (STORY-015e AC1, AC3, AC4) — the default signal
 * the tab selects first (matches `FIXTURE_TOPOLOGY`'s first component's
 * first signal in `availability.ts`). Newest-first; covers all three
 * observation-health values plus a `latency_ms: null` row (no measurement,
 * distinct from a real `0`).
 */
export const FIXTURE_HISTORY_FRONTEND_HTTP: ObservationDTO[] = [
  makeObservation({
    observed_at: '2026-07-03T13:29:17.931000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: 571,
  }),
  makeObservation({
    observed_at: '2026-07-03T13:28:17.812000Z',
    health: 'degraded',
    location: 'SYNTHETIC_LOCATION-0000000000000061',
    latency_ms: 2140,
  }),
  makeObservation({
    observed_at: '2026-07-03T13:27:17.699000Z',
    health: 'down',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: null,
  }),
  makeObservation({
    observed_at: '2026-07-03T13:26:17.544000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000062',
    latency_ms: 498,
  }),
]

/**
 * `frontend-tls` fixture — a second signal's history, distinct from
 * `frontend-http`'s, so a selector-driven refetch is observably a real
 * change (STORY-015e AC2), not the same data re-rendered.
 */
export const FIXTURE_HISTORY_FRONTEND_TLS: ObservationDTO[] = [
  makeObservation({
    signal_key: 'frontend-tls',
    observed_at: '2026-07-03T13:25:02.101000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000063',
    latency_ms: 812,
  }),
  makeObservation({
    signal_key: 'frontend-tls',
    observed_at: '2026-07-03T13:20:02.045000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000063',
    latency_ms: 799,
  }),
]

/** Keyed by `signal_key` (STORY-015e AC1, AC2) — the handler below looks up
 * the requested `signal_key` query param here; an unrecognized/unfixtured
 * key (e.g. the zero-signal component's absent case) returns `[]`, the real
 * empty-window shape rather than a 404. */
export const FIXTURE_HISTORY_BY_SIGNAL: Record<string, ObservationDTO[]> = {
  'frontend-http': FIXTURE_HISTORY_FRONTEND_HTTP,
  'frontend-tls': FIXTURE_HISTORY_FRONTEND_TLS,
}

/**
 * History feature's default success handler (STORY-015e AC1, AC2). Requires
 * `signal_key` like the real endpoint; tests override with `server.use(...)`
 * for error/volume-cap scenarios — MSW is the only mocked I/O edge.
 */
export const historyHandlers = [
  http.get('/api/v1/history', ({ request }) => {
    const url = new URL(request.url)
    const signalKey = url.searchParams.get('signal_key') ?? ''
    return HttpResponse.json(FIXTURE_HISTORY_BY_SIGNAL[signalKey] ?? [])
  }),
]
