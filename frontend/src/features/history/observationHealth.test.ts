import { describe, expect, it } from 'vitest'
import { toObservationHealth } from './observationHealth'

describe('toObservationHealth', () => {
  it('maps the raw observation health vocabulary onto the shell health tokens', () => {
    expect(toObservationHealth('up')).toBe('up')
    expect(toObservationHealth('down')).toBe('down')
    expect(toObservationHealth('degraded')).toBe('degraded')
  })

  it('falls back to "unknown" for anything outside up/down/degraded', () => {
    expect(toObservationHealth('flaky')).toBe('unknown')
    expect(toObservationHealth('')).toBe('unknown')
  })

  it('is a DISTINCT mapping from the component vendor-status mapper — a raw "up" observation must stay "up", never fall through to "unknown" the way statusMapping.ts::toHealthStatus would', () => {
    // statusMapping.ts::toHealthStatus only recognizes the vendor vocabulary
    // (operational/degraded_performance/partial_outage/major_outage/
    // under_maintenance) — passing it a raw observation "up" mis-maps to
    // "unknown". This dedicated mapper must not repeat that mistake.
    expect(toObservationHealth('up')).not.toBe('unknown')
  })
})
