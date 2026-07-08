import { describe, expect, it } from 'vitest'
import type { ObservationDTO } from '../../api/types'
import { buildAvailabilitySegments, MAX_AVAILABILITY_SEGMENTS } from './segments'

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

describe('buildAvailabilitySegments', () => {
  it('maps observation health onto segment status, oldest first', () => {
    const observations: ObservationDTO[] = [
      makeObservation({ observed_at: '2026-07-03T13:29:00Z', health: 'up' }),
      makeObservation({ observed_at: '2026-07-03T13:28:00Z', health: 'degraded' }),
      makeObservation({ observed_at: '2026-07-03T13:27:00Z', health: 'down' }),
    ]

    const segments = buildAvailabilitySegments(observations)

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

    const [segment] = buildAvailabilitySegments(observations)
    expect(segment.title).toBe(
      'SYNTHETIC_LOCATION-0000000000000060 — up @ 2026-07-03T13:29:17.931000Z',
    )
  })

  it('maps an unrecognized health value to "unknown" via observationHealth', () => {
    const observations: ObservationDTO[] = [makeObservation({ health: 'weird' })]
    const [segment] = buildAvailabilitySegments(observations)
    expect(segment.status).toBe('unknown')
  })

  it('caps at MAX_AVAILABILITY_SEGMENTS, keeping the MOST RECENT observations', () => {
    const observations: ObservationDTO[] = Array.from({ length: 40 }, (_, index) =>
      makeObservation({
        observed_at: `2026-07-03T13:${String(39 - index).padStart(2, '0')}:00Z`,
        health: index === 0 ? 'down' : 'up',
      }),
    )

    const segments = buildAvailabilitySegments(observations)

    expect(segments).toHaveLength(MAX_AVAILABILITY_SEGMENTS)
    // The single "down" observation is the newest — it must survive the cap
    // and land last (rightmost, oldest-to-newest order).
    expect(segments[segments.length - 1].status).toBe('down')
  })

  it('returns an empty array for an empty observation list — never a fabricated bucket', () => {
    expect(buildAvailabilitySegments([])).toEqual([])
  })
})
