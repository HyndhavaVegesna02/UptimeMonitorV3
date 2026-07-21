import { describe, expect, it } from 'vitest'
import { FIXTURE_COMPONENT_AVAILABILITY } from '../../mocks/handlers/availability'
import {
  availabilityBand,
  deriveDownCount,
  formatAvailabilityPercent,
  isLowCompleteness,
  LOW_COMPLETENESS_THRESHOLD,
} from './format'

describe('formatAvailabilityPercent', () => {
  it('scales a 0-1 fraction to a 2-decimal percent numeric string (unit rendered by the caller)', () => {
    // Real captured sample: rollup.availability_pct 1.0 -> "100.00".
    expect(formatAvailabilityPercent(1.0)).toBe('100.00')
    // Real captured sample: rollup.completeness_pct 0.0930555 -> "9.31".
    expect(formatAvailabilityPercent(0.0930555)).toBe('9.31')
  })

  it('renders "No data" for a null percentage, NEVER a fabricated 0%', () => {
    expect(formatAvailabilityPercent(null)).toBe('No data')
  })

  it('renders "0.00" (not "No data") for a genuine zero fraction', () => {
    expect(formatAvailabilityPercent(0)).toBe('0.00')
  })
})

describe('isLowCompleteness', () => {
  it('flags a completeness fraction below the threshold', () => {
    expect(isLowCompleteness(0.0930555)).toBe(true)
    expect(isLowCompleteness(LOW_COMPLETENESS_THRESHOLD - 0.001)).toBe(true)
  })

  it('does not flag a completeness fraction at or above the threshold', () => {
    expect(isLowCompleteness(LOW_COMPLETENESS_THRESHOLD)).toBe(false)
    expect(isLowCompleteness(1.0)).toBe(false)
  })

  it('never treats null as low completeness', () => {
    expect(isLowCompleteness(null)).toBe(false)
  })
})

describe('availabilityBand', () => {
  it('bands a null percentage as "missing" (no data), not "down"', () => {
    expect(availabilityBand(null)).toBe('missing')
  })

  it('bands >=99.9% as "up"', () => {
    expect(availabilityBand(1.0)).toBe('up')
    expect(availabilityBand(0.999)).toBe('up')
  })

  it('bands below 99.9% as "down"', () => {
    expect(availabilityBand(0.9989)).toBe('down')
    expect(availabilityBand(0)).toBe('down')
  })
})

describe('deriveDownCount', () => {
  it('derives down = total - passing - maintenance from the real captured rollup', () => {
    expect(deriveDownCount(FIXTURE_COMPONENT_AVAILABILITY['http-check'].rollup)).toBe(0)
  })

  it('derives a non-zero down count when passing+maintenance falls short of total', () => {
    expect(
      deriveDownCount({
        availability_pct: 0.5,
        completeness_pct: 0.5,
        total_verdicts: 10,
        passing_verdicts: 6,
        maintenance_verdicts: 1,
        gap_verdicts: 0,
        distinct_locations: 1,
        window: '24h',
        computed_at: '2026-07-21T00:00:00Z',
      }),
    ).toBe(3)
  })
})
