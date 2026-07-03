import { describe, expect, it } from 'vitest'
import { formatPct } from './format'

describe('formatPct', () => {
  it('formats a percentage to two decimal places with a trailing %', () => {
    expect(formatPct(99.8654)).toBe('99.87%')
    expect(formatPct(100)).toBe('100.00%')
    expect(formatPct(0)).toBe('0.00%')
  })

  it('renders null as an explicit "no data" label — never 0% or NaN%', () => {
    expect(formatPct(null)).toBe('no data')
  })
})
