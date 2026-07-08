import type { ObservationDTO } from '../../api/types'
import type { SignalOption } from './signals'

/** An `ObservationDTO` enriched with the name of the component its signal
 * belongs to (STORY-060 AC2) — `ObservationDTO` itself only carries
 * `signal_key`, but the dense grid's "Component" column needs a human name,
 * so this is resolved once at merge time via the topology's `SignalOption`
 * list rather than re-derived per render. */
export interface HistoryRow extends ObservationDTO {
  componentName: string
}

/**
 * Merges the PER-SIGNAL `getHistory` results (STORY-060 AC1, AC2) into one
 * flat, newest-first list spanning every signal in the topology — the Check
 * History tab shows the whole system's ledger, not one signal at a time
 * (the pre-STORY-060 shape). `observationsBySignal` is keyed by
 * `signal_key`; a signal absent from the map (e.g. a component with no
 * fixtured history yet) contributes zero rows rather than throwing.
 *
 * Each signal's own observations already arrive newest-first from the API
 * (the `getHistory` contract), but interleaving MULTIPLE signals means the
 * merged list must be re-sorted by `observed_at` descending to stay
 * newest-first overall.
 */
export function mergeObservations(
  signals: SignalOption[],
  observationsBySignal: Record<string, ObservationDTO[]>,
): HistoryRow[] {
  const rows: HistoryRow[] = signals.flatMap((signal) => {
    const observations = observationsBySignal[signal.signal_key] ?? []
    return observations.map((observation) => ({
      ...observation,
      componentName: signal.componentName,
    }))
  })

  return rows.sort((a, b) => (a.observed_at < b.observed_at ? 1 : a.observed_at > b.observed_at ? -1 : 0))
}
