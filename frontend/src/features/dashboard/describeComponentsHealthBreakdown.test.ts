import { describe, expect, it } from 'vitest'
import type { ComponentDTO } from '../../api/types'
import { describeComponentsHealthBreakdown } from './describeComponentsHealthBreakdown'

describe('describeComponentsHealthBreakdown', () => {
  it('returns null when every component is up (nothing to call out)', () => {
    const components: ComponentDTO[] = [{ id: 'http-check', name: 'HTTP Check', status: 'operational' }]
    expect(describeComponentsHealthBreakdown(components)).toBeNull()
  })

  it('returns null for an empty component list', () => {
    expect(describeComponentsHealthBreakdown([])).toBeNull()
  })

  it('counts each non-up health status once, joined with middle dots', () => {
    const components: ComponentDTO[] = [
      { id: 'a', name: 'A', status: 'operational' },
      { id: 'b', name: 'B', status: 'degraded_performance' },
      { id: 'c', name: 'C', status: 'under_maintenance' },
      { id: 'd', name: 'D', status: 'under_maintenance' },
    ]
    expect(describeComponentsHealthBreakdown(components)).toBe('1 degraded · 2 in maintenance')
  })
})
