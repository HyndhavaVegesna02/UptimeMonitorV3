import { useCallback, useDeferredValue, useMemo, useState } from 'react'
import { getTopology } from '../../api/client'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { WindowToggle } from '../../features/availability/WindowToggle'
import type { WindowKey } from '../../features/availability/windowRange'
import { computeWindowRange } from '../../features/availability/windowRange'
import { DEFAULT_RENDER_CAP, capRows } from '../../features/history/capRows'
import type { HistoryFilters, ResultFilterKey } from '../../features/history/filterHistoryRows'
import { deriveLocationOptions, filterHistoryRows } from '../../features/history/filterHistoryRows'
import { HistoryFilterBar } from '../../features/history/HistoryFilterBar'
import { HistoryGrid } from '../../features/history/HistoryGrid'
import { mergeHistoryRows } from '../../features/history/mergeHistoryRows'
import { useHistoryData } from '../../features/history/useHistoryData'
import { combineFetchPhase, firstErrorMessage } from '../../lib/combineFetchStates'
import { useFetch } from '../../lib/useFetch'
import './HistoryPage.css'

export interface HistoryPageProps {
  /** Injectable for tests (STORY-130 AC4) — defaults to
   * `DEFAULT_RENDER_CAP` (1000) in production. */
  renderCap?: number
}

/**
 * The Check History page (STORY-130) — every signal's raw observations,
 * merged into one globally-sorted grid over a selectable 24h/7d/30d window,
 * with a client-side filter toolbar (search/Result/Location). Fresh design
 * (not the old tab layout, per PO directive), reusing the Availability
 * page's `WindowToggle`/`computeWindowRange` rather than duplicating window
 * math. No `<h1>` here — `ShellLayout`'s `Topbar` already owns the page's
 * one top-level heading.
 */
export function HistoryPage({ renderCap = DEFAULT_RENDER_CAP }: HistoryPageProps) {
  const [windowKey, setWindowKey] = useState<WindowKey>('24h')
  // Same discipline as `AvailabilityPage`: `now` only advances on a genuine
  // window change, never a fresh `new Date()` read every render — keeps
  // `since`/`until` referentially stable (via `useMemo`) so `useHistoryData`'s
  // effect dependency doesn't refetch on unrelated re-renders.
  const [now, setNow] = useState(() => new Date())
  const { since, until } = useMemo(() => computeWindowRange(windowKey, now), [windowKey, now])

  const handleWindowChange = useCallback((next: WindowKey) => {
    setWindowKey(next)
    setNow(new Date())
  }, [])

  const topologyFetch = useFetch(getTopology)
  const historyState = useHistoryData(topologyFetch.state, since, until)

  const [search, setSearch] = useState('')
  // Filtering the (bounded) merged row list is cheap, but `useDeferredValue`
  // keeps rapid keystrokes from ever competing with paint (ui-ux-pro-max:
  // debounce/defer search-filter inputs) without needing a debounce timer.
  const deferredSearch = useDeferredValue(search)
  const [result, setResult] = useState<ResultFilterKey>('all')
  const [location, setLocation] = useState('all')

  const phase = combineFetchPhase([topologyFetch.state, historyState])
  const errorMessage = firstErrorMessage([topologyFetch.state, historyState])
  const retry = () => topologyFetch.retry()

  // Not memoized (same reasoning as `DashboardPage`'s `combinedHistory`):
  // `topologyFetch.state`/`historyState` aren't referentially stable across
  // the loading phase anyway (a fresh `[]`/`{}` literal below each render
  // until they succeed), so a `useMemo` here would never actually hit.
  // Merging/filtering/capping a render-cap-bounded row list is cheap.
  const topology = topologyFetch.state.phase === 'success' ? topologyFetch.state.data : []
  const observationsBySignal = historyState.phase === 'success' ? historyState.data : {}

  const mergedRows = mergeHistoryRows(topology, observationsBySignal)
  const locationOptions = deriveLocationOptions(mergedRows)

  const filters: HistoryFilters = { search: deferredSearch, result, location }
  const filteredRows = filterHistoryRows(mergedRows, filters)
  const { rows: cappedRows, total, truncated } = capRows(filteredRows, renderCap)

  return (
    <div className="history-page">
      <div className="history-page__toolbar">
        <p className="history-page__description">
          Every raw synthetic-check observation across all signals, most-recent first.
        </p>
        <WindowToggle value={windowKey} onChange={handleWindowChange} />
      </div>

      <Panel title="Observations" className="history-page__panel">
        <HistoryFilterBar
          search={search}
          onSearchChange={setSearch}
          result={result}
          onResultChange={setResult}
          location={location}
          onLocationChange={setLocation}
          locationOptions={locationOptions}
        />

        {phase === 'loading' ? <LoadingState label="Loading observations…" /> : null}
        {phase === 'error' ? <ErrorState message={errorMessage} onRetry={retry} /> : null}
        {phase === 'success' ? (
          mergedRows.length === 0 ? (
            <EmptyState
              message="No observations in this window"
              detail="Widen the window or check back once checks have run."
            />
          ) : filteredRows.length === 0 ? (
            <EmptyState
              message="No observations match your filters"
              detail="Try a broader search, or clear the Result/Location filters."
            />
          ) : (
            <>
              <HistoryGrid rows={cappedRows} />
              {truncated ? (
                <p className="history-page__caption">
                  Showing latest {cappedRows.length} of {total}
                </p>
              ) : null}
            </>
          )
        ) : null}
      </Panel>
    </div>
  )
}
