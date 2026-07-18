import { describe, expect, it } from 'vitest'
import type { ComponentDTO } from '../../api/types'
import { deriveOverallStatus } from './deriveOverallStatus'

function component(id: string, status: string): ComponentDTO {
  return { id, name: id, status }
}

describe('deriveOverallStatus', () => {
  it('returns "unknown" for an empty component list — no signal to assess, never a fabricated "up" (explicit empty-input behavior)', () => {
    expect(deriveOverallStatus([])).toBe('unknown')
  })

  it('returns "up" when every component maps to up', () => {
    expect(
      deriveOverallStatus([component('a', 'operational'), component('b', 'operational')]),
    ).toBe('up')
  })

  it('picks the single worst status among a mix (down beats everything else)', () => {
    expect(
      deriveOverallStatus([
        component('a', 'operational'),
        component('b', 'degraded'),
        component('c', 'major_outage'),
      ]),
    ).toBe('down')
  })

  it('partial outranks degraded when there is no down', () => {
    expect(
      deriveOverallStatus([component('a', 'degraded'), component('b', 'partial_outage')]),
    ).toBe('partial')
  })

  it('degraded outranks unknown', () => {
    expect(
      deriveOverallStatus([component('a', 'some_future_status'), component('b', 'degraded')]),
    ).toBe('degraded')
  })

  it('an unrecognized status alone maps to unknown, worse than up', () => {
    expect(
      deriveOverallStatus([component('a', 'operational'), component('b', 'mystery')]),
    ).toBe('unknown')
  })

  it('is order-independent — the worst status wins regardless of array position', () => {
    expect(
      deriveOverallStatus([
        component('a', 'major_outage'),
        component('b', 'operational'),
        component('c', 'degraded'),
      ]),
    ).toBe('down')
    expect(
      deriveOverallStatus([
        component('a', 'operational'),
        component('b', 'degraded'),
        component('c', 'major_outage'),
      ]),
    ).toBe('down')
  })
})
