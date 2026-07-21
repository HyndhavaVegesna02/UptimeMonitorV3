import { describe, expect, it } from 'vitest'
import type { ComponentDTO } from '../../api/types'
import type { SignalsMap } from './types'
import { deriveRoster } from './deriveRoster'

const COMPONENTS: ComponentDTO[] = [
  { id: 'http-check', name: 'HTTP Check', status: 'operational' },
  { id: 'no-data-yet', name: 'No Data Yet', status: 'operational' },
]

const SIGNALS: SignalsMap = {
  'http-check': {
    availability: {
      availability_pct: 1,
      completeness_pct: 0.145,
      total_verdicts: 102,
      passing_verdicts: 102,
      maintenance_verdicts: 0,
      gap_verdicts: 618,
      distinct_locations: 2,
      window: '24h',
      computed_at: '2026-07-21T08:00:01Z',
    },
    history: [
      { signal_key: 'http-check', observed_at: '2026-07-21T07:58:41Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000060', latency_ms: 588, response_status_code: 200, check_type: 'http' },
      { signal_key: 'http-check', observed_at: '2026-07-21T07:57:41Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: 951, response_status_code: 200, check_type: 'http' },
    ],
  },
}

describe('deriveRoster', () => {
  it('produces one row per component with its health, uptime, latest latency, and trend', () => {
    const rows = deriveRoster(COMPONENTS, SIGNALS)
    const httpCheck = rows.find((row) => row.component.id === 'http-check')!
    expect(httpCheck.health).toBe('up')
    expect(httpCheck.uptimePct).toBe(1)
    expect(httpCheck.latestLatencyMs).toBe(588)
    expect(httpCheck.latencyTrend).toEqual([951, 588])
  })

  it("renders a component with no fetched signal data gracefully (nulls, not a crash)", () => {
    const rows = deriveRoster(COMPONENTS, SIGNALS)
    const noData = rows.find((row) => row.component.id === 'no-data-yet')!
    expect(noData.uptimePct).toBeNull()
    expect(noData.latestLatencyMs).toBeNull()
    expect(noData.latencyTrend).toEqual([])
  })

  it('preserves the original component order', () => {
    const rows = deriveRoster(COMPONENTS, SIGNALS)
    expect(rows.map((row) => row.component.id)).toEqual(['http-check', 'no-data-yet'])
  })

  it('returns an empty array for no components', () => {
    expect(deriveRoster([], {})).toEqual([])
  })
})
