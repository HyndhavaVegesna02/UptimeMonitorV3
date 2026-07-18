import { describe, expect, it } from 'vitest'
import type { ObservationDTO } from '../../api/types'
import { buildLatencyPoints, MAX_LATENCY_POINTS } from './latencyPoints'

function observation(overrides: Partial<ObservationDTO> = {}): ObservationDTO {
  return {
    signal_key: 'frontend-http',
    observed_at: '2026-07-03T13:29:17.931000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: 571,
    response_status_code: 200,
    check_type: 'http',
    ...overrides,
  }
}

describe('buildLatencyPoints', () => {
  it('produces no points for an empty history — never a fabricated spark', () => {
    expect(buildLatencyPoints([])).toEqual([])
  })

  it('reverses newest-first observations into oldest -> newest values', () => {
    const observations = [
      observation({ observed_at: '2026-07-03T13:29:17Z', latency_ms: 300 }),
      observation({ observed_at: '2026-07-03T13:28:17Z', latency_ms: 200 }),
      observation({ observed_at: '2026-07-03T13:27:17Z', latency_ms: 100 }),
    ]
    expect(buildLatencyPoints(observations)).toEqual([100, 200, 300])
  })

  it('filters out null-latency observations (no measurement, never rendered as 0)', () => {
    const observations = [
      observation({ observed_at: '2026-07-03T13:29:17Z', latency_ms: 300 }),
      observation({ observed_at: '2026-07-03T13:28:17Z', latency_ms: null }),
      observation({ observed_at: '2026-07-03T13:27:17Z', latency_ms: 100 }),
    ]
    expect(buildLatencyPoints(observations)).toEqual([100, 300])
  })

  it('caps at MAX_LATENCY_POINTS, keeping the MOST RECENT observations', () => {
    const many = Array.from({ length: 45 }, (_, i) =>
      observation({ observed_at: `2026-07-03T13:${String(29 - (i % 29)).padStart(2, '0')}:00Z`, latency_ms: i }),
    )
    const points = buildLatencyPoints(many)
    expect(points).toHaveLength(MAX_LATENCY_POINTS)
    // The 20 most recent (indices 0..19 of the newest-first input) survive,
    // reversed so index 19 ends up first, index 0 (the very newest) last.
    expect(points[points.length - 1]).toBe(0)
  })
})
