import { describe, expect, it } from 'vitest'
import type { ObservationDTO } from '../../api/types'
import { buildUptimeSegments, MAX_UPTIME_SEGMENTS } from './uptimeSegments'

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

describe('buildUptimeSegments', () => {
  it('maps observation health onto segment status, oldest first', () => {
    const observations: ObservationDTO[] = [
      makeObservation({ observed_at: '2026-07-03T13:29:00Z', health: 'up' }),
      makeObservation({ observed_at: '2026-07-03T13:28:00Z', health: 'degraded' }),
      makeObservation({ observed_at: '2026-07-03T13:27:00Z', health: 'down' }),
    ]

    const segments = buildUptimeSegments(observations)

    // Newest-first input reverses to oldest (left) -> newest (right).
    expect(segments.map((s) => s.status)).toEqual(['down', 'degraded', 'up'])
  })

  it('carries a per-segment tooltip with location, health, and timestamp', () => {
    const observations: ObservationDTO[] = [
      makeObservation({
        location: 'SYNTHETIC_LOCATION-0000000000000060',
        health: 'up',
        observed_at: '2026-07-03T13:29:17.931000Z',
      }),
    ]

    const [segment] = buildUptimeSegments(observations)
    expect(segment.title).toBe(
      'SYNTHETIC_LOCATION-0000000000000060 — up @ 2026-07-03T13:29:17.931000Z',
    )
  })

  it('caps at MAX_UPTIME_SEGMENTS, keeping the MOST RECENT observations', () => {
    const observations: ObservationDTO[] = Array.from({ length: 40 }, (_, index) =>
      makeObservation({
        observed_at: `2026-07-03T13:${String(39 - index).padStart(2, '0')}:00Z`,
        health: index === 0 ? 'down' : 'up',
      }),
    )

    const segments = buildUptimeSegments(observations)

    expect(segments).toHaveLength(MAX_UPTIME_SEGMENTS)
    expect(segments[segments.length - 1].status).toBe('down')
  })

  it('returns an empty array for an empty observation list', () => {
    expect(buildUptimeSegments([])).toEqual([])
  })
})
