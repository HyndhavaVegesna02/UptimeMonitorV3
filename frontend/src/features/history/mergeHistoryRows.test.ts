import { describe, expect, it } from 'vitest'
import type { ComponentTopologyDTO, ObservationDTO } from '../../api/types'
import { FIXTURE_HISTORY } from '../../mocks/handlers/history'
import { mergeHistoryRows } from './mergeHistoryRows'

/**
 * A second synthetic signal (STORY-130 multi-signal-merge test) — same
 * shape/scale as the real captured `http-check` sample (same
 * `SYNTHETIC_LOCATION-…` ids, `check_type: 'http'`, a plausible latency),
 * just a distinct `signal_key`/timestamps so the interleave is provable.
 */
const PING_CHECK_HISTORY: ObservationDTO[] = [
  {
    signal_key: 'ping-check',
    observed_at: '2026-07-21T07:57:41.000000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000047',
    latency_ms: 42,
    response_status_code: 200,
    check_type: 'ping',
  },
  {
    signal_key: 'ping-check',
    observed_at: '2026-07-21T07:55:41.000000Z',
    health: 'down',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: null,
    response_status_code: null,
    check_type: 'ping',
  },
]

const TOPOLOGY: ComponentTopologyDTO[] = [
  {
    id: 'http-check',
    name: 'HTTP Check',
    signals: [{ signal_key: 'http-check', name: 'HTTP Check', interval_seconds: 120, component_id: 'http-check' }],
  },
  {
    id: 'ping-check',
    name: 'Ping Check',
    signals: [{ signal_key: 'ping-check', name: 'Ping Check', interval_seconds: 60, component_id: 'ping-check' }],
  },
]

describe('mergeHistoryRows', () => {
  it('merges every signal into ONE list and re-sorts globally by observed_at desc (interleaved, not concatenated)', () => {
    // http-check (real captured sample) is newest-first on its own:
    // 07:58:41 then 07:56:41. ping-check is newest-first on its own:
    // 07:57:41 then 07:55:41. Concatenating them naively would read
    // [07:58:41, 07:56:41, 07:57:41, 07:55:41] — NOT globally sorted. The
    // correct global order interleaves the two signals.
    const rows = mergeHistoryRows(TOPOLOGY, {
      'http-check': [FIXTURE_HISTORY['http-check'][0], FIXTURE_HISTORY['http-check'][2]],
      'ping-check': PING_CHECK_HISTORY,
    })

    expect(rows.map((row) => row.observedAt)).toEqual([
      '2026-07-21T07:58:41.133000Z', // http-check
      '2026-07-21T07:57:41.000000Z', // ping-check
      '2026-07-21T07:56:41.164000Z', // http-check
      '2026-07-21T07:55:41.000000Z', // ping-check
    ])
  })

  it("joins each row's component display name from the topology, by signal_key", () => {
    const rows = mergeHistoryRows(TOPOLOGY, { 'ping-check': PING_CHECK_HISTORY })
    expect(rows.every((row) => row.componentName === 'Ping Check')).toBe(true)
  })

  it('falls back to the raw signal_key when no topology component matches (defensive, never crashes)', () => {
    const rows = mergeHistoryRows([], { 'orphan-signal': [PING_CHECK_HISTORY[0]] })
    expect(rows[0].componentName).toBe('orphan-signal')
  })

  it('carries the raw wire health/latency/status-code/check_type/location through untouched', () => {
    const rows = mergeHistoryRows(TOPOLOGY, { 'ping-check': [PING_CHECK_HISTORY[1]] })
    expect(rows[0]).toMatchObject({
      health: 'down',
      latencyMs: null,
      responseStatusCode: null,
      checkType: 'ping',
      location: 'SYNTHETIC_LOCATION-0000000000000060',
      signalKey: 'ping-check',
    })
  })

  it('returns an empty array for an empty observations map (a real empty-input behavior, not a crash)', () => {
    expect(mergeHistoryRows(TOPOLOGY, {})).toEqual([])
  })
})
