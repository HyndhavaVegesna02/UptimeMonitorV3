import { useCallback, useEffect, useState } from 'react'
import { getComponents } from '../../api/client'
import { toHealthStatus } from '../../api/statusMapping'
import type { ComponentDTO } from '../../api/types'
import { EmptyState, ErrorState, LoadingState, StatusBadge } from '../../components'
import './ComponentsProbe.css'

type FetchState =
  | { phase: 'loading' }
  | { phase: 'error'; message: string }
  | { phase: 'success'; data: ComponentDTO[] }

/**
 * The AC3 proving example: `GET /api/v1/components` wired end to end with
 * loading, error, and retry states, using only the T3 primitives + T2
 * tokens. Lives inside the Dashboard placeholder (STORY-015a); the real
 * Dashboard tab content is STORY-015b.
 */
export function ComponentsProbe() {
  const [state, setState] = useState<FetchState>({ phase: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    getComponents()
      .then((data) => {
        if (!cancelled) {
          setState({ phase: 'success', data })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            phase: 'error',
            message: err instanceof Error ? err.message : 'Unknown error',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [attempt])

  const retry = useCallback(() => {
    // Reset to loading in the event handler, not synchronously inside the
    // effect body (react-hooks/set-state-in-effect) — this is what shows
    // the spinner again for the in-flight retry.
    setState({ phase: 'loading' })
    setAttempt((n) => n + 1)
  }, [])

  if (state.phase === 'loading') {
    return <LoadingState label="Loading components…" />
  }

  if (state.phase === 'error') {
    return <ErrorState message="Could not load components" onRetry={retry} />
  }

  if (state.data.length === 0) {
    return (
      <EmptyState
        message="No components yet"
        detail="Components appear here once seeded."
      />
    )
  }

  return (
    <ul className="components-probe__list">
      {state.data.map((component) => (
        <li key={component.id} className="components-probe__item">
          <span>{component.name}</span>
          <StatusBadge status={toHealthStatus(component.status)} />
        </li>
      ))}
    </ul>
  )
}
