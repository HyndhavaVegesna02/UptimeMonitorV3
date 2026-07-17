import { describe, expect, it } from 'vitest'
import type { ComponentDTO } from '../../api/types'
import { summarizeComponents } from './summary'

function component(id: string, status: string): ComponentDTO {
  return { id, name: id, status }
}

describe('summarizeComponents', () => {
  it('counts every recognized status bucket, reconciling with the input length — no redundant "Components" total card (STORY-099 AC1)', () => {
    const components = [
      component('a', 'operational'),
      component('b', 'operational'),
      component('c', 'degraded'),
      component('d', 'partial_outage'),
      component('e', 'major_outage'),
    ]

    const cards = summarizeComponents(components)
    const byKey = new Map(cards.map((card) => [card.key, card]))

    // The redundant total card (duplicating "Operational N of N") is gone.
    expect(byKey.has('total')).toBe(false)
    expect(byKey.get('up')?.value).toBe(2)
    expect(byKey.get('degraded')?.value).toBe(1)
    expect(byKey.get('partial')?.value).toBe(1)
    expect(byKey.get('down')?.value).toBe(1)
    // No unrecognized statuses in this fixture -> no "Unknown" card at all.
    expect(byKey.has('unknown')).toBe(false)
  })

  it('adds an Unknown card only when an unrecognized status actually occurs', () => {
    const cards = summarizeComponents([component('mystery', 'some_future_status')])
    const byKey = new Map(cards.map((card) => [card.key, card]))

    expect(byKey.get('up')?.value).toBe(0)
    expect(byKey.get('unknown')?.value).toBe(1)
  })

  it('renders every card with a real, non-fabricated count on an empty component list', () => {
    const cards = summarizeComponents([])
    const byKey = new Map(cards.map((card) => [card.key, card]))

    expect(byKey.get('up')?.value).toBe(0)
    expect(byKey.has('unknown')).toBe(false)
  })

  it('assigns the SummaryCard tone vocabulary matching each health bucket', () => {
    const cards = summarizeComponents([component('a', 'operational')])
    const byKey = new Map(cards.map((card) => [card.key, card]))

    expect(byKey.get('up')?.tone).toBe('up')
    expect(byKey.get('degraded')?.tone).toBe('degraded')
    expect(byKey.get('partial')?.tone).toBe('partial')
    expect(byKey.get('down')?.tone).toBe('down')
  })

  it('marks the "bad state" cards (degraded/partial/down) neutral-at-zero, but never Operational (STORY-099 AC1, journal D4)', () => {
    const cards = summarizeComponents([component('a', 'operational')])
    const byKey = new Map(cards.map((card) => [card.key, card]))

    expect(byKey.get('up')?.neutralAtZero).toBe(false)
    expect(byKey.get('degraded')?.neutralAtZero).toBe(true)
    expect(byKey.get('partial')?.neutralAtZero).toBe(true)
    expect(byKey.get('down')?.neutralAtZero).toBe(true)
  })
})
