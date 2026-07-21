import { describe, expect, it } from 'vitest'
import { toHealthStatus } from './statusMapping'

describe('toHealthStatus', () => {
  it.each([
    ['operational', 'up'],
    ['degraded_performance', 'degraded'],
    ['partial_outage', 'partial'],
    ['major_outage', 'down'],
    ['under_maintenance', 'maintenance'],
  ] as const)('maps vendor status %s -> health %s', (vendor, health) => {
    expect(toHealthStatus(vendor)).toBe(health)
  })

  it('falls back to unknown for an unrecognized vendor status', () => {
    expect(toHealthStatus('mystery_status')).toBe('unknown')
  })
})
