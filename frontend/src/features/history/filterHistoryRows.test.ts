import { describe, expect, it } from 'vitest'
import type { HistoryRow } from './mergeHistoryRows'
import { deriveLocationOptions, filterHistoryRows, RESULT_FILTER_OPTIONS } from './filterHistoryRows'

const ROWS: HistoryRow[] = [
  {
    key: '1',
    signalKey: 'http-check',
    componentName: 'HTTP Check',
    observedAt: '2026-07-21T07:58:41.133000Z',
    checkType: 'http',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    health: 'up',
    latencyMs: 588,
    responseStatusCode: 200,
  },
  {
    key: '2',
    signalKey: 'ping-check',
    componentName: 'Ping Check',
    observedAt: '2026-07-21T07:57:41.000000Z',
    checkType: 'ping',
    location: 'SYNTHETIC_LOCATION-0000000000000047',
    health: 'down',
    latencyMs: null,
    responseStatusCode: null,
  },
  {
    key: '3',
    signalKey: 'db-check',
    componentName: 'Database Check',
    observedAt: '2026-07-21T07:56:41.000000Z',
    checkType: 'db',
    location: 'SYNTHETIC_LOCATION-0000000000000047',
    health: 'degraded',
    latencyMs: 900,
    responseStatusCode: 200,
  },
]

describe('RESULT_FILTER_OPTIONS', () => {
  it('offers the FIXED wire vocabulary All/Up/Degraded/Down, in that order — pinned, never derived from data', () => {
    expect(RESULT_FILTER_OPTIONS.map((option) => option.key)).toEqual(['all', 'up', 'degraded', 'down'])
    expect(RESULT_FILTER_OPTIONS.map((option) => option.label)).toEqual(['All', 'Up', 'Degraded', 'Down'])
  })
})

describe('deriveLocationOptions', () => {
  it('derives distinct locations from the loaded rows, sorted', () => {
    expect(deriveLocationOptions(ROWS)).toEqual([
      'SYNTHETIC_LOCATION-0000000000000047',
      'SYNTHETIC_LOCATION-0000000000000060',
    ])
  })

  it('returns an empty array for zero rows (no crash)', () => {
    expect(deriveLocationOptions([])).toEqual([])
  })
})

describe('filterHistoryRows', () => {
  it('returns every row when the filters are all defaults', () => {
    expect(filterHistoryRows(ROWS, { search: '', result: 'all', location: 'all' })).toHaveLength(3)
  })

  it('narrows by the Result filter using the fixed wire vocabulary', () => {
    const filtered = filterHistoryRows(ROWS, { search: '', result: 'down', location: 'all' })
    expect(filtered.map((row) => row.key)).toEqual(['2'])
  })

  it('narrows by the Location filter (exact match on the raw location value)', () => {
    const filtered = filterHistoryRows(ROWS, {
      search: '',
      result: 'all',
      location: 'SYNTHETIC_LOCATION-0000000000000047',
    })
    expect(filtered.map((row) => row.key).sort()).toEqual(['2', '3'])
  })

  it('matches the text search case-insensitively against component name, location, and signal_key', () => {
    expect(filterHistoryRows(ROWS, { search: 'ping', result: 'all', location: 'all' }).map((r) => r.key)).toEqual(['2'])
    expect(filterHistoryRows(ROWS, { search: '0060', result: 'all', location: 'all' }).map((r) => r.key)).toEqual(['1'])
    expect(filterHistoryRows(ROWS, { search: 'DATABASE', result: 'all', location: 'all' }).map((r) => r.key)).toEqual([
      '3',
    ])
  })

  it('combines all three filters (AND, not OR)', () => {
    const filtered = filterHistoryRows(ROWS, {
      search: 'check',
      result: 'degraded',
      location: 'SYNTHETIC_LOCATION-0000000000000047',
    })
    expect(filtered.map((row) => row.key)).toEqual(['3'])
  })

  it('returns an empty array when nothing matches (the filtered-empty case) rather than crashing', () => {
    expect(filterHistoryRows(ROWS, { search: 'nope-does-not-exist', result: 'all', location: 'all' })).toEqual([])
  })
})
