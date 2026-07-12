import { describe, expect, it } from 'vitest'
import type { ObservationDTO } from '../../api/types'
import { mergeObservations } from './mergeObservations'
import type { SignalOption } from './signals'

function makeSignal(overrides: Partial<SignalOption> = {}): SignalOption {
  return {
    signal_key: 'frontend-http',
    name: 'Frontend HTTP check',
    interval_seconds: 60,
    component_id: 'sockshop-frontend',
    componentName: 'Sock Shop — frontend',
    ...overrides,
  }
}

function makeObservation(overrides: Partial<ObservationDTO> = {}): ObservationDTO {
  return {
    signal_key: 'frontend-http',
    observed_at: '2026-07-03T13:29:17.931000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: 571,
    response_status_code: 200,
    check_type: 'http',
    ...overrides,
  }
}

describe('mergeObservations', () => {
  it('tags each observation with the component name of the signal it belongs to', () => {
    const signals = [makeSignal()]
    const rows = mergeObservations(signals, {
      'frontend-http': [makeObservation()],
    })

    expect(rows).toHaveLength(1)
    expect(rows[0].componentName).toBe('Sock Shop — frontend')
    expect(rows[0].signal_key).toBe('frontend-http')
  })

  it('interleaves multiple signals and re-sorts the merged list newest-first', () => {
    const signals = [
      makeSignal({ signal_key: 'frontend-http', componentName: 'Sock Shop — frontend' }),
      makeSignal({ signal_key: 'catalogue-http', componentName: 'Sock Shop — catalogue' }),
    ]
    const rows = mergeObservations(signals, {
      'frontend-http': [
        makeObservation({ observed_at: '2026-07-03T13:00:00.000000Z' }),
        makeObservation({ observed_at: '2026-07-03T12:00:00.000000Z' }),
      ],
      'catalogue-http': [
        makeObservation({
          signal_key: 'catalogue-http',
          observed_at: '2026-07-03T13:30:00.000000Z',
        }),
      ],
    })

    expect(rows.map((row) => row.observed_at)).toEqual([
      '2026-07-03T13:30:00.000000Z',
      '2026-07-03T13:00:00.000000Z',
      '2026-07-03T12:00:00.000000Z',
    ])
  })

  it('contributes zero rows for a signal absent from the observations map (never throws)', () => {
    const signals = [makeSignal({ signal_key: 'nodata-http', componentName: 'Sock Shop — nodata' })]
    const rows = mergeObservations(signals, {})

    expect(rows).toEqual([])
  })

  it('returns an empty list when there are no signals at all', () => {
    expect(mergeObservations([], {})).toEqual([])
  })
})
