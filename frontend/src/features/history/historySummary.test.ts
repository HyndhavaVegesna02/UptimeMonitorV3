import { describe, expect, it } from 'vitest'
import type { HistoryRow } from './mergeObservations'
import { DEFAULT_HISTORY_FILTERS } from './filterHistory'
import { buildHistorySummary, countDownRows, describeActiveFilters } from './historySummary'

function makeRow(overrides: Partial<HistoryRow> = {}): HistoryRow {
  return {
    signal_key: 'frontend-http',
    observed_at: '2026-07-03T13:29:17.931000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: 571,
    response_status_code: 200,
    check_type: 'http',
    componentName: 'Sock Shop — frontend',
    ...overrides,
  }
}

describe('countDownRows', () => {
  it('returns 0 for an empty input — the explicit empty-input case, never a leaked stdlib error', () => {
    expect(countDownRows([])).toBe(0)
  })

  it('counts only the down rows, ignoring up/degraded', () => {
    const rows = [
      makeRow({ health: 'up' }),
      makeRow({ health: 'down' }),
      makeRow({ health: 'degraded' }),
      makeRow({ health: 'down' }),
    ]
    expect(countDownRows(rows)).toBe(2)
  })
})

describe('describeActiveFilters', () => {
  it('returns an empty list when every filter is at its default (no active-filter echo)', () => {
    expect(describeActiveFilters(DEFAULT_HISTORY_FILTERS)).toEqual([])
  })

  it('describes an active free-text search', () => {
    expect(describeActiveFilters({ ...DEFAULT_HISTORY_FILTERS, query: 'frontend-http' })).toEqual([
      'search "frontend-http"',
    ])
  })

  it('describes an active result filter', () => {
    expect(describeActiveFilters({ ...DEFAULT_HISTORY_FILTERS, result: 'down' })).toEqual([
      'result: down',
    ])
  })

  it('describes an active location filter using the short display label, not the raw id', () => {
    const described = describeActiveFilters({
      ...DEFAULT_HISTORY_FILTERS,
      location: 'SYNTHETIC_LOCATION-0000000000000060',
    })
    expect(described).toEqual(['location: Location …0060'])
  })

  it('describes every active filter together, in query/result/location order', () => {
    const described = describeActiveFilters({
      query: 'checkout',
      result: 'down',
      location: 'SYNTHETIC_LOCATION-0000000000000060',
    })
    expect(described).toEqual([
      'search "checkout"',
      'result: down',
      'location: Location …0060',
    ])
  })

  it('trims a whitespace-only query to "no active search" rather than an empty-quoted echo', () => {
    expect(describeActiveFilters({ ...DEFAULT_HISTORY_FILTERS, query: '   ' })).toEqual([])
  })
})

describe('buildHistorySummary', () => {
  it('renders the explicit zero-row case ("0 checks · 0 down"), never a leaked stdlib message', () => {
    expect(buildHistorySummary([], DEFAULT_HISTORY_FILTERS)).toBe('0 checks · 0 down')
  })

  it('pluralizes a single row correctly', () => {
    const rows = [makeRow({ health: 'up' })]
    expect(buildHistorySummary(rows, DEFAULT_HISTORY_FILTERS)).toBe('1 check · 0 down')
  })

  it('counts checks and down rows accurately with no active filters', () => {
    const rows = [makeRow({ health: 'up' }), makeRow({ health: 'down' }), makeRow({ health: 'down' })]
    expect(buildHistorySummary(rows, DEFAULT_HISTORY_FILTERS)).toBe('3 checks · 2 down')
  })

  it('appends the active-filter echo when a filter is applied', () => {
    const rows = [makeRow({ health: 'down' })]
    expect(buildHistorySummary(rows, { ...DEFAULT_HISTORY_FILTERS, result: 'down' })).toBe(
      '1 check · 1 down — filtered by result: down',
    )
  })
})
