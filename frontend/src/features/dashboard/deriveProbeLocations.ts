import type { ObservationDTO } from '../../api/types'
import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'
import { locationLabel } from './locationLabel'

export interface ProbeLocationRow {
  location: string
  label: string
  /** The most recent observation's health at this location, mapped onto
   * the shell's health vocabulary ('up' for a passing check, 'down'
   * otherwise — `ObservationDTO.health` is the closed up/down/degraded
   * verdict, not the vendor component-status string). */
  health: HealthStatus
  latestLatencyMs: number | null
  /** Fraction of the FETCHED sample's observations at this location that
   * were "up" — a real, derived figure over the same window the history
   * call covers, not the full-window `/availability` computation (which is
   * per-signal, not per-location). */
  availabilityPct: number
  /** Count of non-"up" observations at this location, in the fetched sample. */
  errorCount: number
}

function toRowHealth(health: string): HealthStatus {
  return health === 'up' ? 'up' : health === 'down' ? 'down' : 'degraded'
}

/**
 * Groups a signal's history into one row per distinct real probe location
 * (STORY-122 AC3) — never a fabricated/geo-placed location. Each row's
 * health/latency come from that location's MOST RECENT observation (by
 * `observed_at`), not array order (history may interleave locations).
 */
export function deriveProbeLocations(observations: ObservationDTO[]): ProbeLocationRow[] {
  const byLocation = new Map<string, ObservationDTO[]>()

  for (const observation of observations) {
    const existing = byLocation.get(observation.location)
    if (existing) {
      existing.push(observation)
    } else {
      byLocation.set(observation.location, [observation])
    }
  }

  return [...byLocation.entries()].map(([location, locationObservations]) => {
    const mostRecent = locationObservations.reduce((latest, observation) =>
      new Date(observation.observed_at) > new Date(latest.observed_at) ? observation : latest,
    )
    const upCount = locationObservations.filter((observation) => observation.health === 'up').length

    return {
      location,
      label: locationLabel(location),
      health: toRowHealth(mostRecent.health),
      latestLatencyMs: mostRecent.latency_ms,
      availabilityPct: upCount / locationObservations.length,
      errorCount: locationObservations.length - upCount,
    }
  })
}
