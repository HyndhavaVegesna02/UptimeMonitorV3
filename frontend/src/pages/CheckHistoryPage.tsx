import { useMemo, useState } from 'react'
import { EmptyState, ErrorState, LoadingState, Panel, StatusBadge } from '../components'
import { cx } from '../lib/cx'
import { observationHealth } from '../features/history/observationHealth'
import { flattenSignals } from '../features/history/signals'
import { useHistory } from '../features/history/useHistory'
import { useSignalOptions } from '../features/history/useSignalOptions'
import type { AvailabilityRange, WindowPreset } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
import './CheckHistoryPage.css'

const WINDOW_PRESETS: Array<{ value: WindowPreset; label: string }> = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
]

/** The most rows the tab will ever RENDER (STORY-015e AC4) — the `/history`
 * endpoint has no pagination, so a wide window can return many thousands of
 * rows; this is a client-side render cap, not a request limit. */
const MAX_RENDERED_ROWS = 1000

/** `latency_ms` renders as integer milliseconds; `null` (no measurement)
 * renders as an em-dash — NEVER `0 ms`, which would misreport "no reading"
 * as "instant" (STORY-015e AC3). */
function formatLatency(latencyMs: number | null): string {
  return latencyMs === null ? '—' : `${latencyMs} ms`
}

/**
 * The observation table for the currently-selected signal+window (STORY-015e
 * AC1, AC3, AC4) — mounted only once a signal is selected, so it owns its
 * own `useHistory` fetch and states independent of the outer signal
 * enumeration above it.
 */
function ObservationTable({
  signalKey,
  range,
}: {
  signalKey: string
  range: AvailabilityRange
}) {
  const { state, retry } = useHistory({ signalKey, range })

  if (state.phase === 'loading') {
    return <LoadingState label="Loading observations…" />
  }

  if (state.phase === 'error') {
    return <ErrorState message="Could not load check history" onRetry={retry} />
  }

  const observations = state.data

  if (observations.length === 0) {
    return <EmptyState message="No observations in this window" />
  }

  // The API's own newest-first order IS the contract — never re-sorted here.
  const rendered = observations.slice(0, MAX_RENDERED_ROWS)
  const truncated = observations.length > MAX_RENDERED_ROWS

  return (
    <>
      {truncated ? (
        <p className="check-history-page__cap-note text-caption">
          showing latest {MAX_RENDERED_ROWS.toLocaleString()} of{' '}
          {observations.length.toLocaleString()} observations
        </p>
      ) : null}
      <table className="check-history-table">
        <thead>
          <tr>
            <th scope="col">Observed at</th>
            <th scope="col">Status</th>
            <th scope="col">Latency</th>
            <th scope="col">Location</th>
          </tr>
        </thead>
        <tbody>
          {rendered.map((observation, index) => (
            <tr key={`${observation.observed_at}-${index}`}>
              <td>
                <span className="text-mono">{observation.observed_at}</span>
              </td>
              <td>
                <StatusBadge status={observationHealth(observation.health)} />
              </td>
              <td>
                <span className="text-mono">{formatLatency(observation.latency_ms)}</span>
              </td>
              <td>
                <span className="text-mono">{observation.location}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

/**
 * The Check History tab (STORY-015e): a dense, chronological, per-signal
 * observation ledger — the ingest ledger view (dossier §17). Enumerates
 * signals via the EXISTING `GET /api/v1/topology` (STORY-044/015d,
 * `useSignalOptions` + `flattenSignals`, reused rather than re-added) to
 * populate a signal selector, defaulting to the first signal; a 24h/7d/30d
 * window selector mirrors the Availability tab's (`windowToRange` reused,
 * not duplicated — the parallel-shape agreement). Both selections feed
 * `useHistory` (AC1, AC2), which fetches `GET /api/v1/history` newest-first
 * for exactly that signal+window.
 *
 * `selectedSignalKey` starts `null` and the EFFECTIVE selection is computed
 * on every render as `selectedSignalKey ?? signals[0]?.signal_key` (never
 * synced into state via an effect) — the same pattern the STORY-049
 * sample-mode toggle uses to avoid a one-frame flash of a wrong default the
 * instant the topology fetch resolves (`docs/scrum/wiki/frontend-zone.md`).
 */
export function CheckHistoryPage() {
  const { state: signalState, retry: retrySignals } = useSignalOptions()
  const [preset, setPreset] = useState<WindowPreset>('24h')
  // Memoized per preset (not per render) so `useHistory`'s fetcher keeps a
  // STABLE identity while the window selection is unchanged (015d pattern).
  const range = useMemo(() => windowToRange(preset), [preset])
  const [selectedSignalKey, setSelectedSignalKey] = useState<string | null>(null)

  const signals = signalState.phase === 'success' ? flattenSignals(signalState.data) : []
  const effectiveSignalKey = selectedSignalKey ?? signals[0]?.signal_key ?? null

  return (
    <Panel title="Check History" headingLevel="h1">
      {signalState.phase === 'loading' && <LoadingState label="Loading signals…" />}

      {signalState.phase === 'error' && (
        <ErrorState message="Could not load signals" onRetry={retrySignals} />
      )}

      {signalState.phase === 'success' && signals.length === 0 && (
        <EmptyState message="No signals configured" />
      )}

      {signalState.phase === 'success' && signals.length > 0 && effectiveSignalKey ? (
        <>
          <div className="check-history-page__controls">
            <div className="check-history-page__signal">
              <label className="check-history-page__signal-label" htmlFor="check-history-signal">
                Signal
              </label>
              <select
                id="check-history-signal"
                className="check-history-page__signal-select"
                value={effectiveSignalKey}
                onChange={(event) => setSelectedSignalKey(event.target.value)}
              >
                {signals.map((signal) => (
                  <option key={signal.signal_key} value={signal.signal_key}>
                    {signal.componentName} — {signal.name}
                  </option>
                ))}
              </select>
            </div>

            <div
              className="check-history-page__window"
              role="group"
              aria-label="Time window"
            >
              {WINDOW_PRESETS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={cx(
                    'check-history-page__window-button',
                    preset === option.value && 'check-history-page__window-button--active',
                  )}
                  aria-pressed={preset === option.value}
                  onClick={() => setPreset(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <ObservationTable signalKey={effectiveSignalKey} range={range} />
        </>
      ) : null}
    </Panel>
  )
}
