import { describe, expect, it } from 'vitest'
import { formatLatency, formatPercent } from './format'

describe('formatPercent', () => {
  it('renders a 0-1 fraction as a percentage string with 2 decimals by default', () => {
    expect(formatPercent(1.0)).toBe('100.00')
    expect(formatPercent(0.9987)).toBe('99.87')
  })

  it('renders an em dash for a null (degenerate-window) percentage rather than a fabricated 0', () => {
    expect(formatPercent(null)).toBe('—')
  })

  it('supports a custom decimal count', () => {
    expect(formatPercent(0.14513888888, 1)).toBe('14.5')
  })
})

describe('formatLatency', () => {
  it('renders a millisecond value with thousands separators', () => {
    expect(formatLatency(428)).toBe('428')
    expect(formatLatency(1240)).toBe('1,240')
  })

  it('renders an em dash for a null latency rather than a fabricated 0', () => {
    expect(formatLatency(null)).toBe('—')
  })
})
