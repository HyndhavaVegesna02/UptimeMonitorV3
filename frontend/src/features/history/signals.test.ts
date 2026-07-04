import { describe, expect, it } from 'vitest'
import { FIXTURE_TOPOLOGY } from '../../mocks/handlers'
import { flattenSignals } from './signals'

describe('flattenSignals', () => {
  it('flattens every component\'s signals into one list, tagged with the owning component name', () => {
    const flattened = flattenSignals(FIXTURE_TOPOLOGY)

    const totalSignals = FIXTURE_TOPOLOGY.reduce(
      (sum, component) => sum + component.signals.length,
      0,
    )
    expect(flattened).toHaveLength(totalSignals)

    const multiSignalComponent = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-frontend')!
    const [firstSignal] = multiSignalComponent.signals
    const flattenedFirst = flattened.find((s) => s.signal_key === firstSignal.signal_key)
    expect(flattenedFirst).toMatchObject({
      ...firstSignal,
      componentName: multiSignalComponent.name,
    })
  })

  it('preserves component and signal order (the first entry is the default selection)', () => {
    const flattened = flattenSignals(FIXTURE_TOPOLOGY)
    const firstComponentWithSignals = FIXTURE_TOPOLOGY.find((c) => c.signals.length > 0)!
    expect(flattened[0].signal_key).toBe(firstComponentWithSignals.signals[0].signal_key)
  })

  it('returns an empty list for a zero-signal-everywhere topology', () => {
    const noSignals = FIXTURE_TOPOLOGY.map((component) => ({ ...component, signals: [] }))
    expect(flattenSignals(noSignals)).toEqual([])
  })

  it('returns an empty list for an empty topology', () => {
    expect(flattenSignals([])).toEqual([])
  })
})
