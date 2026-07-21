import { useCallback, useMemo, useState } from 'react'
import { getTopology } from '../../api/client'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { ComponentAvailabilityCard } from '../../features/availability/ComponentAvailabilityCard'
import { WindowToggle } from '../../features/availability/WindowToggle'
import type { WindowKey } from '../../features/availability/windowRange'
import { computeWindowRange } from '../../features/availability/windowRange'
import { useFetch } from '../../lib/useFetch'
import './AvailabilityPage.css'

/**
 * The Availability page (STORY-129) - component-rollup availability plus
 * per-signal drill-down, over a selectable 24h/7d/30d window (AC1/AC2/AC3).
 * The page FRAME (description + window toggle) paints immediately from a
 * single `getTopology` fetch; each component's own availability is then
 * fetched INDEPENDENTLY by its own `ComponentAvailabilityCard` instance -
 * never one blocking `Promise.all` gated behind the slowest region (AC5,
 * the STORY-122 first-paint lesson: the `/availability` computation is slow
 * against local DynamoDB). No `<h1>` here - `ShellLayout`'s `Topbar` already
 * owns the page's one top-level heading; each component card is its own
 * level-two heading via `Panel`.
 */
export function AvailabilityPage() {
  const [windowKey, setWindowKey] = useState<WindowKey>('24h')
  // `now` only advances when the operator picks a NEW window (never a fresh
  // `new Date()` read on every render) - this, plus deriving `since`/`until`
  // with `useMemo`, keeps them referentially stable across unrelated
  // re-renders, which each `ComponentAvailabilityCard`'s `useFetch` needs
  // (a `useEffect` dependency that changed every render would refetch every
  // render - checklist: stable fetcher references).
  const [now, setNow] = useState(() => new Date())

  const { since, until } = useMemo(() => computeWindowRange(windowKey, now), [windowKey, now])

  const handleWindowChange = useCallback((next: WindowKey) => {
    setWindowKey(next)
    setNow(new Date())
  }, [])

  const topologyFetch = useFetch(getTopology)

  return (
    <div className="availability-page">
      <div className="availability-page__toolbar">
        <p className="availability-page__description">
          Availability and data completeness per component, with a per-signal drill-down.
        </p>
        <WindowToggle value={windowKey} onChange={handleWindowChange} />
      </div>

      {topologyFetch.state.phase === 'loading' ? <LoadingState label="Loading components…" /> : null}
      {topologyFetch.state.phase === 'error' ? (
        <ErrorState message={topologyFetch.state.message} onRetry={topologyFetch.retry} />
      ) : null}
      {topologyFetch.state.phase === 'success' ? (
        topologyFetch.state.data.length === 0 ? (
          <EmptyState message="No components" detail="Nothing to monitor yet." />
        ) : (
          <div className="availability-page__list">
            {topologyFetch.state.data.map((component) => (
              <ComponentAvailabilityCard key={component.id} component={component} since={since} until={until} />
            ))}
          </div>
        )
      ) : null}
    </div>
  )
}
