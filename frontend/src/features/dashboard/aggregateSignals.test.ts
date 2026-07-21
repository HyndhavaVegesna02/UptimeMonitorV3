import { describe, expect, it } from 'vitest'
import type { SignalsMap } from './types'
import { deriveOverallAvailability, flattenHistory } from './aggregateSignals'

const SIGNALS: SignalsMap = {
  'http-check': {
    availability: {
      availability_pct: 1,
      completeness_pct: 0.14,
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

describe('deriveOverallAvailability', () => {
  it("with one signal, returns THAT signal's availability_pct directly", () => {
    expect(deriveOverallAvailability(SIGNALS)).toBe(1)
  })

  it('averages across multiple signals when there is more than one', () => {
    const twoSignals: SignalsMap = {
      ...SIGNALS,
      other: { ...SIGNALS['http-check'], availability: { ...SIGNALS['http-check'].availability, availability_pct: 0.5 } },
    }
    expect(deriveOverallAvailability(twoSignals)).toBeCloseTo(0.75)
  })

  it('ignores null availability_pct values rather than treating them as 0', () => {
    const withNull: SignalsMap = {
      ...SIGNALS,
      other: { ...SIGNALS['http-check'], availability: { ...SIGNALS['http-check'].availability, availability_pct: null } },
    }
    expect(deriveOverallAvailability(withNull)).toBe(1)
  })

  it('returns null when there are no signals or every value is null', () => {
    expect(deriveOverallAvailability({})).toBeNull()
  })
})

describe('flattenHistory', () => {
  it('combines every signal\'s observations, sorted most-recent-first', () => {
    const combined = flattenHistory(SIGNALS)
    expect(combined).toHaveLength(2)
    expect(combined[0].latency_ms).toBe(588)
    expect(combined[1].latency_ms).toBe(951)
  })

  it('merges and re-sorts across multiple signals (not just concatenates)', () => {
    const twoSignals: SignalsMap = {
      a: {
        availability: SIGNALS['http-check'].availability,
        history: [
          { signal_key: 'a', observed_at: '2026-07-21T07:50:00Z', health: 'up', location: 'loc1', latency_ms: 100, response_status_code: 200, check_type: 'http' },
        ],
      },
      b: {
        availability: SIGNALS['http-check'].availability,
        history: [
          { signal_key: 'b', observed_at: '2026-07-21T07:59:00Z', health: 'up', location: 'loc2', latency_ms: 200, response_status_code: 200, check_type: 'http' },
        ],
      },
    }
    const combined = flattenHistory(twoSignals)
    expect(combined[0].latency_ms).toBe(200)
    expect(combined[1].latency_ms).toBe(100)
  })

  it('returns an empty array for no signals', () => {
    expect(flattenHistory({})).toEqual([])
  })
})
