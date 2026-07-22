import { ArrowLeft } from '@phosphor-icons/react'
import { useCallback, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getTopology } from '../../api/client'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { Icon } from '../../components/Icon/Icon'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { ComponentAvailabilityCard } from '../../features/availability/ComponentAvailabilityCard'
import { WindowToggle } from '../../features/availability/WindowToggle'
import type { WindowKey } from '../../features/availability/windowRange'
import { computeWindowRange } from '../../features/availability/windowRange'
import { useFetch } from '../../lib/useFetch'
import './ComponentAvailabilityPage.css'

/**
 * The component-scoped availability view (STORY-143 AC1) — the pinned
 * sidebar quick-link's real destination, in place of the generic list. A
 * fresh page composition (NOT a copy of `AvailabilityPage`): it fetches the
 * SAME `getTopology` list `AvailabilityPage` uses (so a component-not-found
 * check needs no second endpoint), finds the ONE component matching the
 * `:componentId` route param, and renders it through the exact same reused
 * `ComponentAvailabilityCard` — which itself independently fetches the real
 * `GET /availability/component/{id}` data (STORY-129). No `<h1>` here —
 * `ShellLayout`'s `Topbar` owns the page's one top-level heading, resolved to
 * this component's own name by `derivePageTitle` (STORY-143 AC1).
 */
export function ComponentAvailabilityPage() {
  const { componentId } = useParams<{ componentId: string }>()
  const [windowKey, setWindowKey] = useState<WindowKey>('24h')
  // Same stable-`now`-on-selection discipline as `AvailabilityPage` — `now`
  // only advances when the operator picks a NEW window, keeping `since`/
  // `until` referentially stable across unrelated re-renders.
  const [now, setNow] = useState(() => new Date())

  const { since, until } = useMemo(() => computeWindowRange(windowKey, now), [windowKey, now])

  const handleWindowChange = useCallback((next: WindowKey) => {
    setWindowKey(next)
    setNow(new Date())
  }, [])

  const topologyFetch = useFetch(getTopology)

  const component =
    topologyFetch.state.phase === 'success'
      ? topologyFetch.state.data.find((candidate) => candidate.id === componentId)
      : undefined

  return (
    <div className="component-availability-page">
      <div className="component-availability-page__toolbar">
        <Link to="/availability" className="component-availability-page__back">
          <Icon icon={ArrowLeft} aria-hidden size={14} />
          Back to Availability
        </Link>
        <WindowToggle value={windowKey} onChange={handleWindowChange} />
      </div>

      {topologyFetch.state.phase === 'loading' ? <LoadingState label="Loading component…" /> : null}
      {topologyFetch.state.phase === 'error' ? (
        <ErrorState message={topologyFetch.state.message} onRetry={topologyFetch.retry} />
      ) : null}
      {topologyFetch.state.phase === 'success' ? (
        component ? (
          <ComponentAvailabilityCard component={component} since={since} until={until} />
        ) : (
          <EmptyState
            message="Component not found"
            detail={`No component matches "${componentId}".`}
          />
        )
      ) : null}
    </div>
  )
}
