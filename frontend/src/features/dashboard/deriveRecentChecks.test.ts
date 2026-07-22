import { describe, expect, it } from 'vitest'
import type { ComponentDTO } from '../../api/types'
import type { SignalsMap } from './types'
import { deriveRecentChecks } from './deriveRecentChecks'

const COMPONENTS: ComponentDTO[] = [{ id: 'http-check', name: 'HTTP Check', status: 'operational' }]

const NOW = new Date('2026-07-21T08:00:00Z')

const SIGNALS: SignalsMap = {
  'http-check': {
    availability: {
      availability_pct: 1,
      completeness_pct: 0.5,
      total_verdicts: 2,
      passing_verdicts: 2,
      maintenance_verdicts: 0,
      gap_verdicts: 0,
      distinct_locations: 2,
      window: '24h',
      computed_at: '2026-07-21T08:00:00Z',
    },
    history: [
      {
        signal_key: 'http-check',
        observed_at: '2026-07-21T07:59:32Z',
        health: 'up',
        location: 'SYNTHETIC_LOCATION-0000000000000047',
        latency_ms: 294,
        response_status_code: 200,
        check_type: 'http',
      },
      {
        signal_key: 'http-check',
        observed_at: '2026-07-21T07:58:00Z',
        health: 'down',
        location: 'SYNTHETIC_LOCATION-0000000000000060',
        latency_ms: null,
        response_status_code: 500,
        check_type: 'http',
      },
    ],
  },
}

describe('deriveRecentChecks', () => {
  it("maps each observation to its owning component's name (via signal_key === component id)", () => {
    const rows = deriveRecentChecks(COMPONENTS, SIGNALS, NOW, 10)
    expect(rows.every((row) => row.componentName === 'HTTP Check')).toBe(true)
  })

  it('sorts rows most-recent first across all signals', () => {
    const rows = deriveRecentChecks(COMPONENTS, SIGNALS, NOW, 10)
    expect(rows[0].latencyMs).toBe(294)
    expect(rows[1].health).toBe('down')
  })

  it('renders a friendly location label and relative time', () => {
    const rows = deriveRecentChecks(COMPONENTS, SIGNALS, NOW, 10)
    expect(rows[0].locationLabel).toBe('#0047')
    expect(rows[0].relativeTime).toBe('28s ago')
  })

  it('caps the result at the given limit', () => {
    const rows = deriveRecentChecks(COMPONENTS, SIGNALS, NOW, 1)
    expect(rows).toHaveLength(1)
  })

  it('returns an empty array when there is no history yet', () => {
    expect(deriveRecentChecks(COMPONENTS, { 'http-check': { ...SIGNALS['http-check'], history: [] } }, NOW, 10)).toEqual(
      [],
    )
  })

  it('falls back to the signal_key itself when no component matches (defensive, never crashes)', () => {
    const rows = deriveRecentChecks([], SIGNALS, NOW, 10)
    expect(rows[0].componentName).toBe('http-check')
  })

  it('assigns a UNIQUE key even when two observations share an identical (signal_key, observed_at, location) triple — the same live collision class STORY-130 fixed on History (reality gate 2026-07-22)', () => {
    const duplicateTriple = SIGNALS['http-check'].history[0]
    const signalsWithDuplicate: SignalsMap = {
      'http-check': {
        ...SIGNALS['http-check'],
        history: [duplicateTriple, { ...duplicateTriple }],
      },
    }

    const rows = deriveRecentChecks(COMPONENTS, signalsWithDuplicate, NOW, 10)

    expect(rows).toHaveLength(2)
    expect(rows[0].key).not.toBe(rows[1].key)
    // Every other field is still carried through untouched.
    expect(rows[0]).toMatchObject({ latencyMs: duplicateTriple.latency_ms, health: 'up' })
    expect(rows[1]).toMatchObject({ latencyMs: duplicateTriple.latency_ms, health: 'up' })
  })

  it('keys are unique across the whole sorted+capped list, not derived from wire fields', () => {
    const rows = deriveRecentChecks(COMPONENTS, SIGNALS, NOW, 10)
    const keys = rows.map((row) => row.key)
    expect(new Set(keys).size).toBe(keys.length)
  })
})
