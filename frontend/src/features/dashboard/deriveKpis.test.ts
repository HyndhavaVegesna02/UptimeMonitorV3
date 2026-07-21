import { describe, expect, it } from 'vitest'
import type { ComponentDTO, ObservationDTO } from '../../api/types'
import { averageLatencyMs, healthSeries, latencySeries, summarizeComponentsHealth } from './deriveKpis'

const COMPONENTS: ComponentDTO[] = [
  { id: 'http-check', name: 'HTTP Check', status: 'operational' },
]

// Real-shaped sample (live-api-samples.md), most-recent first — matches the
// backend's `ObservationDTO` history ordering.
const OBSERVATIONS: ObservationDTO[] = [
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
    health: 'down',
    location: 'SYNTHETIC_LOCATION-0000000000000047',
    latency_ms: null,
    response_status_code: null,
    check_type: 'http',
  },
]

describe('summarizeComponentsHealth', () => {
  it('counts how many components map to the "up" health status, out of the total', () => {
    expect(summarizeComponentsHealth(COMPONENTS)).toEqual({ healthy: 1, total: 1 })
  })

  it('counts a mix of healthy/unhealthy components', () => {
    const mixed: ComponentDTO[] = [
      { id: 'a', name: 'A', status: 'operational' },
      { id: 'b', name: 'B', status: 'degraded_performance' },
      { id: 'c', name: 'C', status: 'operational' },
    ]
    expect(summarizeComponentsHealth(mixed)).toEqual({ healthy: 2, total: 3 })
  })

  it('returns zero/zero for an empty component list rather than a leaked stdlib error', () => {
    expect(summarizeComponentsHealth([])).toEqual({ healthy: 0, total: 0 })
  })
})

describe('averageLatencyMs', () => {
  it('averages the non-null latencies, rounded to the nearest ms', () => {
    // (588 + 951) / 2 = 769.5 -> rounds to 770
    expect(averageLatencyMs(OBSERVATIONS)).toBe(770)
  })

  it('returns null for an empty observation list rather than NaN', () => {
    expect(averageLatencyMs([])).toBeNull()
  })

  it('returns null when every observation has a null latency', () => {
    expect(
      averageLatencyMs([
        { ...OBSERVATIONS[2] },
        { ...OBSERVATIONS[2], observed_at: '2026-07-21T07:55:00Z' },
      ]),
    ).toBeNull()
  })
})

describe('latencySeries', () => {
  it('reverses history (most-recent-first) to oldest-first for the sparkline, dropping nulls', () => {
    expect(latencySeries(OBSERVATIONS)).toEqual([951, 588])
  })
})

describe('healthSeries', () => {
  it('maps each observation to 1 (up) or 0 (not up), oldest-first', () => {
    expect(healthSeries(OBSERVATIONS)).toEqual([0, 1, 1])
  })
})
