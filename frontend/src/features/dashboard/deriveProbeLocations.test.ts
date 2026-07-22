import { describe, expect, it } from 'vitest'
import type { ObservationDTO } from '../../api/types'
import { deriveProbeLocations } from './deriveProbeLocations'

// Real-shaped sample (live-api-samples.md), most-recent first, 2 locations.
const OBSERVATIONS: ObservationDTO[] = [
  { signal_key: 'http-check', observed_at: '2026-07-21T07:58:41Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000060', latency_ms: 588, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:57:41Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: 951, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:56:41Z', health: 'down', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: null, response_status_code: null, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:54:41Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000060', latency_ms: 570, response_status_code: 200, check_type: 'http' },
]

describe('deriveProbeLocations', () => {
  it('groups observations into one row per distinct real location', () => {
    const rows = deriveProbeLocations(OBSERVATIONS)
    expect(rows).toHaveLength(2)
    expect(rows.map((row) => row.location).sort()).toEqual([
      'SYNTHETIC_LOCATION-0000000000000047',
      'SYNTHETIC_LOCATION-0000000000000060',
    ])
  })

  it("uses each location's MOST RECENT observation for health and latest latency", () => {
    const rows = deriveProbeLocations(OBSERVATIONS)
    const loc60 = rows.find((row) => row.location.endsWith('0060'))!
    expect(loc60.health).toBe('up')
    expect(loc60.latestLatencyMs).toBe(588)

    const loc47 = rows.find((row) => row.location.endsWith('0047'))!
    // Most recent for #0047 is the 07:57:41 "up" check, not the later
    // 07:56:41 "down" one it's chronologically after in this fixture — the
    // derivation must pick by observed_at, not array order.
    expect(loc47.health).toBe('up')
    expect(loc47.latestLatencyMs).toBe(951)
  })

  it('computes a per-location availability percentage from the fetched sample', () => {
    const rows = deriveProbeLocations(OBSERVATIONS)
    const loc47 = rows.find((row) => row.location.endsWith('0047'))!
    // 1 of 2 #0047 observations is "up".
    expect(loc47.availabilityPct).toBeCloseTo(0.5)
  })

  it('counts non-"up" observations as errors for a location', () => {
    const rows = deriveProbeLocations(OBSERVATIONS)
    const loc47 = rows.find((row) => row.location.endsWith('0047'))!
    expect(loc47.errorCount).toBe(1)

    const loc60 = rows.find((row) => row.location.endsWith('0060'))!
    expect(loc60.errorCount).toBe(0)
  })

  it('renders a friendly label alongside the raw location id', () => {
    const rows = deriveProbeLocations(OBSERVATIONS)
    const loc60 = rows.find((row) => row.location.endsWith('0060'))!
    expect(loc60.label).toBe('#0060')
  })

  it('returns an empty array for no observations rather than a crash', () => {
    expect(deriveProbeLocations([])).toEqual([])
  })
})
