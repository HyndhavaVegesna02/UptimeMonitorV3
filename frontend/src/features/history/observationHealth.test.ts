import { describe, expect, it } from 'vitest'
import { observationHealth } from './observationHealth'

describe('observationHealth', () => {
  it('maps "up" to the "up" health token', () => {
    expect(observationHealth('up')).toBe('up')
  })

  it('maps "down" to the "down" health token', () => {
    expect(observationHealth('down')).toBe('down')
  })

  it('maps "degraded" to the "degraded" health token', () => {
    expect(observationHealth('degraded')).toBe('degraded')
  })

  it('maps any unrecognized value to "unknown" (e.g. a ComponentStatus value, which does NOT apply here)', () => {
    expect(observationHealth('operational')).toBe('unknown')
    expect(observationHealth('major_outage')).toBe('unknown')
    expect(observationHealth('')).toBe('unknown')
  })
})
