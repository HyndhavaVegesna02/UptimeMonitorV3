import { describe, expect, it } from 'vitest'
import type { ComponentDTO } from '../api/types'
import { deriveOverallStatus } from './overallStatus'

function component(status: string): ComponentDTO {
  return { id: status, name: status, status }
}

describe('deriveOverallStatus (STORY-121 AC4)', () => {
  it('returns unknown for an empty component list', () => {
    expect(deriveOverallStatus([])).toBe('unknown')
  })

  it('returns up when every component is operational', () => {
    expect(deriveOverallStatus([component('operational'), component('operational')])).toBe('up')
  })

  it('picks the worst status across a non-trivial mix: down > partial > degraded > maintenance > unknown > up', () => {
    const mixed: ComponentDTO[] = [
      component('operational'),
      component('degraded_performance'),
      component('under_maintenance'),
      component('major_outage'),
      component('partial_outage'),
      component('mystery_status'),
    ]

    expect(deriveOverallStatus(mixed)).toBe('down')
  })

  it('prefers partial over degraded/maintenance/unknown when there is no down component', () => {
    const mixed: ComponentDTO[] = [
      component('operational'),
      component('degraded_performance'),
      component('under_maintenance'),
      component('mystery_status'),
      component('partial_outage'),
    ]

    expect(deriveOverallStatus(mixed)).toBe('partial')
  })

  it('prefers degraded over maintenance/unknown when there is no down/partial component', () => {
    const mixed: ComponentDTO[] = [
      component('operational'),
      component('mystery_status'),
      component('under_maintenance'),
      component('degraded_performance'),
    ]

    expect(deriveOverallStatus(mixed)).toBe('degraded')
  })

  it('prefers maintenance over unknown when there is no down/partial/degraded component', () => {
    const mixed: ComponentDTO[] = [
      component('operational'),
      component('mystery_status'),
      component('under_maintenance'),
    ]

    expect(deriveOverallStatus(mixed)).toBe('maintenance')
  })
})
