import type { SignalAvailabilityDTO, TopologySignalDTO } from '../../api/types'

/**
 * A `SignalAvailabilityDTO` joined with its topology-sourced display name +
 * interval (STORY-129 AC2) — the availability endpoint's per-signal
 * children carry only `signal_key`; the name/interval come from
 * `GET /api/v1/topology`.
 */
export interface JoinedSignalAvailability extends SignalAvailabilityDTO {
  name: string
  /** From `TopologySignalDTO.interval_seconds` - `int | null` (nullable for
   * signals predating the interval backfill, plan §Availability edge
   * behavior (b)); also `null` if no topology signal matched at all. */
  intervalSeconds: number | null
}

/**
 * Joins each availability-endpoint signal child onto its topology signal by
 * `signal_key` (STORY-129 AC2). A signal with no topology match (should not
 * happen in practice, but never crash on it) falls back to its own
 * `signal_key` as the display name and a `null` interval, rather than
 * throwing or fabricating a name.
 */
export function joinSignalAvailability(
  topologySignals: TopologySignalDTO[],
  availabilitySignals: SignalAvailabilityDTO[],
): JoinedSignalAvailability[] {
  const bySignalKey = new Map(topologySignals.map((signal) => [signal.signal_key, signal]))

  return availabilitySignals.map((signal) => {
    const topologySignal = bySignalKey.get(signal.signal_key)
    return {
      ...signal,
      name: topologySignal?.name ?? signal.signal_key,
      intervalSeconds: topologySignal?.interval_seconds ?? null,
    }
  })
}
