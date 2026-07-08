import { useCallback } from 'react'
import { getHistory } from '../../api/client'
import type { ObservationDTO, TopologySignalDTO } from '../../api/types'
import type { HealthStatus } from '../../components'
import type { AvailabilityRange } from '../availability/windowRange'
import { observationHealth } from '../history/observationHealth'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'

/** One drill-down row for the expanded component (STORY-057 AC2): the latest
 * observation of ONE signal at ONE location — location / label (signal name)
 * / status / latency / last-observed. Real observation fields only. */
export interface SignalRow {
  key: string
  signalKey: string
  /** The signal's display name (from topology) — the "label" column. */
  label: string
  /** Raw vendor location id, or `null` when the signal has no observations
   * in the window (rendered as an em-dash, never fabricated). */
  location: string | null
  status: HealthStatus
  /** Integer ms, or `null` for no measurement / no observation. */
  latencyMs: number | null
  /** ISO timestamp of the latest observation at this location, or `null`. */
  lastObserved: string | null
}

/**
 * Collapses each signal's raw observations into "latest per location" rows
 * (STORY-057 AC2). `getHistory` returns newest-first, so the FIRST
 * observation seen for a given location IS its most recent — we keep that and
 * drop older ones. A signal with NO observations in the window contributes a
 * single honest "missing data" row (null location/latency/last, `'missing'`
 * status) rather than being silently dropped or fabricating a fake reading.
 */
export function buildSignalRows(
  signals: TopologySignalDTO[],
  historyBySignal: Record<string, ObservationDTO[]>,
): SignalRow[] {
  const rows: SignalRow[] = []

  for (const signal of signals) {
    const observations = historyBySignal[signal.signal_key] ?? []
    const seenLocations = new Set<string>()

    for (const observation of observations) {
      if (seenLocations.has(observation.location)) {
        continue
      }
      seenLocations.add(observation.location)
      rows.push({
        key: `${signal.signal_key}::${observation.location}`,
        signalKey: signal.signal_key,
        label: signal.name,
        location: observation.location,
        status: observationHealth(observation.health),
        latencyMs: observation.latency_ms,
        lastObserved: observation.observed_at,
      })
    }

    if (seenLocations.size === 0) {
      rows.push({
        key: `${signal.signal_key}::no-data`,
        signalKey: signal.signal_key,
        label: signal.name,
        location: null,
        status: 'missing',
        latencyMs: null,
        lastObserved: null,
      })
    }
  }

  return rows
}

async function fetchComponentSignals(
  signals: TopologySignalDTO[],
  range: AvailabilityRange,
): Promise<SignalRow[]> {
  const histories = await Promise.all(
    signals.map((signal) =>
      getHistory({ signal_key: signal.signal_key, since: range.since, until: range.until }),
    ),
  )

  const historyBySignal: Record<string, ObservationDTO[]> = {}
  signals.forEach((signal, index) => {
    historyBySignal[signal.signal_key] = histories[index]
  })

  return buildSignalRows(signals, historyBySignal)
}

export type UseComponentSignalsResult = UseFetchResult<SignalRow[]>

/**
 * Read hook for one expanded component's signal drill-down (STORY-057 AC2).
 * Mounted lazily — only while a row is expanded — so a collapsed component
 * never fires its per-signal history requests. Built on the shared
 * `useFetch<T>` via the parameterized-fetch pattern (`useHistory.ts`): the
 * fetcher is `useCallback`-keyed on `[signals, range]`, so the caller MUST
 * pass a stable `signals` reference (the component's own `signals` array from
 * the memoized topology) and a memoized `range`. A drill-down fetch failure
 * surfaces INSIDE the expanded region only (its own error state) and never
 * touches the primary components table (AC2 graceful degradation).
 */
export function useComponentSignals(
  signals: TopologySignalDTO[],
  range: AvailabilityRange,
): UseComponentSignalsResult {
  const fetcher = useCallback(
    () => fetchComponentSignals(signals, range),
    [signals, range],
  )
  return useFetch(fetcher)
}
