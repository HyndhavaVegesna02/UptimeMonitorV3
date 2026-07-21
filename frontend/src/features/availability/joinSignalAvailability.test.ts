import { describe, expect, it } from 'vitest'
import { FIXTURE_COMPONENT_AVAILABILITY } from '../../mocks/handlers/availability'
import { FIXTURE_TOPOLOGY } from '../../mocks/handlers/topology'
import { joinSignalAvailability } from './joinSignalAvailability'

describe('joinSignalAvailability', () => {
  it('joins the real captured http-check signal availability onto its topology name/interval', () => {
    const topologySignals = FIXTURE_TOPOLOGY[0].signals
    const availabilitySignals = FIXTURE_COMPONENT_AVAILABILITY['http-check'].signals

    const joined = joinSignalAvailability(topologySignals, availabilitySignals)

    expect(joined).toEqual([
      {
        ...availabilitySignals[0],
        name: 'HTTP Check',
        intervalSeconds: 120,
      },
    ])
  })

  it('resolves an empty array for a zero-signal component (no crash, no drill-down affordance)', () => {
    expect(joinSignalAvailability([], [])).toEqual([])
  })

  it('falls back to the signal_key as the display name when topology has no matching signal', () => {
    const joined = joinSignalAvailability([], [
      {
        signal_key: 'orphan-signal',
        availability_pct: null,
        completeness_pct: null,
        total_verdicts: 0,
        passing_verdicts: 0,
        maintenance_verdicts: 0,
        gap_verdicts: 0,
        distinct_locations: 0,
        window: '24h',
        computed_at: '2026-07-21T00:00:00Z',
      },
    ])

    expect(joined[0].name).toBe('orphan-signal')
    expect(joined[0].intervalSeconds).toBeNull()
  })

  it('guards a null topology interval_seconds (predates the interval backfill)', () => {
    const joined = joinSignalAvailability(
      [{ signal_key: 'legacy-signal', name: 'Legacy Signal', interval_seconds: null, component_id: 'c1' }],
      [
        {
          signal_key: 'legacy-signal',
          availability_pct: 1,
          completeness_pct: 1,
          total_verdicts: 1,
          passing_verdicts: 1,
          maintenance_verdicts: 0,
          gap_verdicts: 0,
          distinct_locations: 1,
          window: '24h',
          computed_at: '2026-07-21T00:00:00Z',
        },
      ],
    )

    expect(joined[0].intervalSeconds).toBeNull()
    expect(joined[0].name).toBe('Legacy Signal')
  })
})
