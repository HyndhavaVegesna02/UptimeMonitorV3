import { describe, expect, it } from 'vitest'
import type { HistoryRow } from './mergeObservations'
import { DEFAULT_HISTORY_FILTERS, filterHistoryRows, uniqueLocations } from './filterHistory'

function makeRow(overrides: Partial<HistoryRow> = {}): HistoryRow {
  return {
    signal_key: 'frontend-http',
    observed_at: '2026-07-03T13:29:17.931000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: 571,
    componentName: 'Sock Shop — frontend',
    ...overrides,
  }
}

describe('filterHistoryRows', () => {
  it('returns every row unchanged when all filters are at their default (AC1)', () => {
    const rows = [makeRow(), makeRow({ signal_key: 'frontend-tls' })]
    expect(filterHistoryRows(rows, DEFAULT_HISTORY_FILTERS)).toEqual(rows)
  })

  it('filters by exact result (health) match', () => {
    const rows = [makeRow({ health: 'up' }), makeRow({ health: 'degraded' }), makeRow({ health: 'down' })]
    const filtered = filterHistoryRows(rows, { ...DEFAULT_HISTORY_FILTERS, result: 'degraded' })
    expect(filtered).toHaveLength(1)
    expect(filtered[0].health).toBe('degraded')
  })

  it('filters by exact location match', () => {
    const rows = [
      makeRow({ location: 'SYNTHETIC_LOCATION-A' }),
      makeRow({ location: 'SYNTHETIC_LOCATION-B' }),
    ]
    const filtered = filterHistoryRows(rows, {
      ...DEFAULT_HISTORY_FILTERS,
      location: 'SYNTHETIC_LOCATION-B',
    })
    expect(filtered).toHaveLength(1)
    expect(filtered[0].location).toBe('SYNTHETIC_LOCATION-B')
  })

  it('matches the free-text query case-insensitively against component name, location, or signal_key', () => {
    const rows = [
      makeRow({ componentName: 'Sock Shop — frontend', location: 'LOC-A', signal_key: 'frontend-http' }),
      makeRow({ componentName: 'Sock Shop — catalogue', location: 'LOC-B', signal_key: 'catalogue-http' }),
    ]

    expect(filterHistoryRows(rows, { ...DEFAULT_HISTORY_FILTERS, query: 'CATALOGUE' })).toHaveLength(1)
    expect(filterHistoryRows(rows, { ...DEFAULT_HISTORY_FILTERS, query: 'loc-a' })).toHaveLength(1)
    expect(
      filterHistoryRows(rows, { ...DEFAULT_HISTORY_FILTERS, query: 'frontend-http' }),
    ).toHaveLength(1)
    expect(filterHistoryRows(rows, { ...DEFAULT_HISTORY_FILTERS, query: 'nonexistent' })).toHaveLength(0)
  })

  it('ANDs all three filters together', () => {
    const rows = [
      makeRow({ health: 'up', location: 'LOC-A', componentName: 'Frontend' }),
      makeRow({ health: 'up', location: 'LOC-B', componentName: 'Frontend' }),
      makeRow({ health: 'down', location: 'LOC-A', componentName: 'Frontend' }),
    ]
    const filtered = filterHistoryRows(rows, { query: 'frontend', result: 'up', location: 'LOC-A' })
    expect(filtered).toHaveLength(1)
    expect(filtered[0]).toEqual(rows[0])
  })
})

describe('uniqueLocations', () => {
  it('returns the distinct locations present, sorted alphabetically', () => {
    const rows = [
      makeRow({ location: 'SYNTHETIC_LOCATION-B' }),
      makeRow({ location: 'SYNTHETIC_LOCATION-A' }),
      makeRow({ location: 'SYNTHETIC_LOCATION-B' }),
    ]
    expect(uniqueLocations(rows)).toEqual(['SYNTHETIC_LOCATION-A', 'SYNTHETIC_LOCATION-B'])
  })

  it('returns an empty list for an empty input', () => {
    expect(uniqueLocations([])).toEqual([])
  })
})
