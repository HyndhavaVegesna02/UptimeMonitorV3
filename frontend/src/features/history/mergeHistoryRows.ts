import type { ComponentTopologyDTO, ObservationDTO } from '../../api/types'

/** One merged, display-ready observation row (STORY-130 AC1). Raw wire
 * fields are carried through untouched (health/latency/status-code mapping
 * and "—" null rendering happen at the presentation layer, not here). */
export interface HistoryRow {
  key: string
  signalKey: string
  componentName: string
  observedAt: string
  checkType: string
  location: string
  health: string
  latencyMs: number | null
  responseStatusCode: number | null
}

/**
 * Merges every signal's per-signal observation list into ONE list and
 * re-sorts it globally by `observed_at` descending (STORY-130 AC1). Each
 * signal's own list is already newest-first, but the INTERLEAVING across
 * signals is not — a global re-sort is required, not a plain concatenation
 * (proven by `mergeHistoryRows.test.ts`'s interleave assertion). Each row's
 * component display name is joined from the topology by `signal_key`; an
 * unmatched signal_key falls back to the raw key itself rather than
 * crashing or fabricating a name (same defensive convention as
 * `dashboard/deriveRecentChecks.ts`).
 */
export function mergeHistoryRows(
  topology: ComponentTopologyDTO[],
  observationsBySignal: Record<string, ObservationDTO[]>,
): HistoryRow[] {
  const componentNameBySignalKey = new Map<string, string>()
  for (const component of topology) {
    for (const signal of component.signals) {
      componentNameBySignalKey.set(signal.signal_key, component.name)
    }
  }

  const rows = Object.entries(observationsBySignal).flatMap(([signalKey, observations]) =>
    observations.map((observation) => ({
      key: `${signalKey}-${observation.observed_at}-${observation.location}`,
      signalKey,
      componentName: componentNameBySignalKey.get(signalKey) ?? signalKey,
      observedAt: observation.observed_at,
      checkType: observation.check_type,
      location: observation.location,
      health: observation.health,
      latencyMs: observation.latency_ms,
      responseStatusCode: observation.response_status_code,
    })),
  )

  return rows.sort((a, b) => new Date(b.observedAt).getTime() - new Date(a.observedAt).getTime())
}
