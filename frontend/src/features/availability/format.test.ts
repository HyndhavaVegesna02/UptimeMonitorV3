import { describe, expect, it } from 'vitest'
import {
  availabilityBand,
  formatDownLabel,
  formatPct,
  isCompletenessLow,
} from './format'

describe('formatPct', () => {
  it('scales a 0-1 wire fraction to a percentage with two decimal places (STORY-015d fix)', () => {
    expect(formatPct(0.998654)).toBe('99.87%')
    expect(formatPct(1)).toBe('100.00%')
    expect(formatPct(0)).toBe('0.00%')
  })

  it('renders null as an explicit "no data" label — never 0% or NaN%', () => {
    expect(formatPct(null)).toBe('no data')
  })
})

describe('formatDownLabel', () => {
  it('renders "no downtime" when every non-maintenance verdict passed (STORY-058 AC1)', () => {
    expect(
      formatDownLabel({
        availability_pct: 1,
        total_verdicts: 96,
        passing_verdicts: 95,
        maintenance_verdicts: 1,
      }),
    ).toBe('no downtime')
  })

  it('singularizes exactly one down verdict', () => {
    expect(
      formatDownLabel({
        availability_pct: 0.9,
        total_verdicts: 10,
        passing_verdicts: 9,
        maintenance_verdicts: 0,
      }),
    ).toBe('1 period down')
  })

  it('pluralizes more than one down verdict, derived from REAL verdict counts', () => {
    expect(
      formatDownLabel({
        availability_pct: 0.8,
        total_verdicts: 10,
        passing_verdicts: 8,
        maintenance_verdicts: 0,
      }),
    ).toBe('2 periods down')
  })

  it('renders "no data" (never "no downtime") when availability_pct is null — a degenerate window has no verdicts to count', () => {
    expect(
      formatDownLabel({
        availability_pct: null,
        total_verdicts: 0,
        passing_verdicts: 0,
        maintenance_verdicts: 0,
      }),
    ).toBe('no data')
  })
})

describe('isCompletenessLow', () => {
  it('is false at and above the 98% threshold', () => {
    expect(isCompletenessLow(0.98)).toBe(false)
    expect(isCompletenessLow(1)).toBe(false)
  })

  it('is true below the 98% threshold', () => {
    expect(isCompletenessLow(0.975)).toBe(true)
    expect(isCompletenessLow(0)).toBe(true)
  })

  it('is false for null — "no data" is a distinct condition from "low completeness"', () => {
    expect(isCompletenessLow(null)).toBe(false)
  })
})

describe('availabilityBand', () => {
  it('bands >=99.9% as up', () => {
    expect(availabilityBand(0.999)).toBe('up')
    expect(availabilityBand(1)).toBe('up')
  })

  it('bands >=99% and <99.9% as degraded', () => {
    expect(availabilityBand(0.99)).toBe('degraded')
    expect(availabilityBand(0.995)).toBe('degraded')
  })

  it('bands >=95% and <99% as partial', () => {
    expect(availabilityBand(0.95)).toBe('partial')
    expect(availabilityBand(0.97)).toBe('partial')
  })

  it('bands below 95% as down', () => {
    expect(availabilityBand(0.94)).toBe('down')
    expect(availabilityBand(0)).toBe('down')
  })

  it('bands null as null — no data has no health verdict to render', () => {
    expect(availabilityBand(null)).toBeNull()
  })
})
