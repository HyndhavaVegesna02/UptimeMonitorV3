import { useState, useMemo } from 'react'
import { getTopology } from '../../api/client'
import { Button } from '../../components/Button/Button'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { useFetch } from '../../lib/useFetch'
import { ComponentAvailabilityCard } from './ComponentAvailabilityCard'

type WindowChoice = '24h' | '7d' | '30d'

export function AvailabilityView() {
  const [windowChoice, setWindowChoice] = useState<WindowChoice>('24h')

  const { state, retry } = useFetch(getTopology)

  const { since, until } = useMemo(() => {
    const now = new Date()
    const untilStr = now.toISOString()
    let hours = 24
    if (windowChoice === '7d') hours = 7 * 24
    if (windowChoice === '30d') hours = 30 * 24
    const sinceDate = new Date(now.getTime() - hours * 60 * 60 * 1000)
    return {
      since: sinceDate.toISOString(),
      until: untilStr,
    }
  }, [windowChoice])

  const loading = state.phase === 'loading'
  const error = state.phase === 'error' ? state : null
  const topology = state.phase === 'success' ? state.data : undefined

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-md)',
        }}
      >
        <p
          style={{
            fontSize: 'var(--font-sm)',
            color: 'var(--color-text-secondary)',
            margin: 0,
          }}
        >
          Multi-grain availability and verdict counts per component and monitor signal.
        </p>

        <div
          role="group"
          aria-label="Availability time window"
          style={{ display: 'flex', gap: 'var(--space-xs)' }}
        >
          {(['24h', '7d', '30d'] as const).map((win) => (
            <Button
              key={win}
              variant={windowChoice === win ? 'primary' : 'ghost'}
              onClick={() => setWindowChoice(win)}
            >
              {win.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      {loading && <LoadingState label="Loading component topology…" />}

      {error && (
        <ErrorState
          message={error.message ?? 'Failed to load topology'}
          onRetry={retry}
        />
      )}

      {!loading && !error && topology && topology.length === 0 && (
        <EmptyState message="No components found in system topology." />
      )}

      {!loading && !error && topology && topology.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {topology.map((comp) => (
            <ComponentAvailabilityCard
              key={comp.id}
              component={comp}
              since={since}
              until={until}
            />
          ))}
        </div>
      )}
    </div>
  )
}
