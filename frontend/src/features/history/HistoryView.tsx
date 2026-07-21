import { useState, useMemo, useCallback } from 'react'
import { getHistory, getTopology } from '../../api/client'
import type { ObservationDTO } from '../../api/types'
import { Button } from '../../components/Button/Button'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'
import { useFetch } from '../../lib/useFetch'

type WindowChoice = '24h' | '7d' | '30d'

interface JoinedObservation extends ObservationDTO {
  componentName: string
}

function mapObservationHealth(health: string): HealthStatus {
  switch (health.toLowerCase()) {
    case 'up':
      return 'up'
    case 'degraded':
      return 'degraded'
    case 'down':
      return 'down'
    default:
      return 'unknown'
  }
}

interface HistoryViewProps {
  maxRenderCap?: number
}

export function HistoryView({ maxRenderCap = 1000 }: HistoryViewProps) {
  const [windowChoice, setWindowChoice] = useState<WindowChoice>('24h')
  const [searchTerm, setSearchTerm] = useState('')
  const [resultFilter, setResultFilter] = useState<string>('all')
  const [locationFilter, setLocationFilter] = useState<string>('all')

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

  const fetcher = useCallback(async (): Promise<JoinedObservation[]> => {
    const topology = await getTopology()
    const componentMap = new Map<string, string>()
    const signalKeys: string[] = []

    for (const comp of topology) {
      for (const sig of comp.signals) {
        componentMap.set(sig.signal_key, comp.name)
        if (!signalKeys.includes(sig.signal_key)) {
          signalKeys.push(sig.signal_key)
        }
      }
    }

    const historyPromises = signalKeys.map((signalKey) =>
      getHistory({ signalKey, since, until }),
    )

    const results = await Promise.all(historyPromises)
    const combined: JoinedObservation[] = []

    for (const obsArray of results) {
      for (const obs of obsArray) {
        combined.push({
          ...obs,
          componentName: componentMap.get(obs.signal_key) ?? obs.signal_key,
        })
      }
    }

    // Global sort by observed_at desc
    combined.sort(
      (a, b) => new Date(b.observed_at).getTime() - new Date(a.observed_at).getTime(),
    )

    return combined
  }, [since, until])

  const { state, retry } = useFetch(fetcher)

  const loading = state.phase === 'loading'
  const error = state.phase === 'error' ? state : null
  const observations = state.phase === 'success' ? state.data : undefined

  const availableLocations = useMemo(() => {
    if (!observations) return []
    const set = new Set<string>()
    for (const obs of observations) {
      if (obs.location) set.add(obs.location)
    }
    return Array.from(set).sort()
  }, [observations])

  const filteredObservations = useMemo(() => {
    if (!observations) return []
    return observations.filter((obs) => {
      if (
        resultFilter !== 'all' &&
        obs.health.toLowerCase() !== resultFilter.toLowerCase()
      ) {
        return false
      }
      if (locationFilter !== 'all' && obs.location !== locationFilter) {
        return false
      }
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase()
        const matchComp = obs.componentName.toLowerCase().includes(term)
        const matchSig = obs.signal_key.toLowerCase().includes(term)
        const matchLoc = obs.location.toLowerCase().includes(term)
        if (!matchComp && !matchSig && !matchLoc) {
          return false
        }
      }
      return true
    })
  }, [observations, resultFilter, locationFilter, searchTerm])

  const displayedObservations = useMemo(() => {
    return filteredObservations.slice(0, maxRenderCap)
  }, [filteredObservations, maxRenderCap])

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
          Synthetic monitor observations across all components and locations.
        </p>

        <div
          role="group"
          aria-label="History time window"
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

      <Panel>
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 'var(--space-md)',
            alignItems: 'center',
          }}
        >
          <div style={{ flex: '1 1 200px' }}>
            <label
              htmlFor="history-search"
              style={{
                display: 'block',
                fontSize: 'var(--font-xs)',
                color: 'var(--color-text-secondary)',
                marginBottom: '4px',
              }}
            >
              Search
            </label>
            <input
              id="history-search"
              type="text"
              placeholder="Search component, signal, location…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: 'var(--space-xs) var(--space-sm)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-sm)',
              }}
            />
          </div>

          <div style={{ flex: '0 0 140px' }}>
            <label
              htmlFor="history-result-filter"
              style={{
                display: 'block',
                fontSize: 'var(--font-xs)',
                color: 'var(--color-text-secondary)',
                marginBottom: '4px',
              }}
            >
              Result
            </label>
            <select
              id="history-result-filter"
              value={resultFilter}
              onChange={(e) => setResultFilter(e.target.value)}
              style={{
                width: '100%',
                padding: 'var(--space-xs) var(--space-sm)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-sm)',
              }}
            >
              <option value="all">All Results</option>
              <option value="up">Up</option>
              <option value="degraded">Degraded</option>
              <option value="down">Down</option>
            </select>
          </div>

          <div style={{ flex: '0 0 180px' }}>
            <label
              htmlFor="history-location-filter"
              style={{
                display: 'block',
                fontSize: 'var(--font-xs)',
                color: 'var(--color-text-secondary)',
                marginBottom: '4px',
              }}
            >
              Location
            </label>
            <select
              id="history-location-filter"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              style={{
                width: '100%',
                padding: 'var(--space-xs) var(--space-sm)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-sm)',
              }}
            >
              <option value="all">All Locations</option>
              {availableLocations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Panel>

      {loading && <LoadingState label="Loading check history…" />}

      {error && (
        <ErrorState
          message={error.message ?? 'Failed to load check history'}
          onRetry={retry}
        />
      )}

      {!loading && !error && observations && observations.length === 0 && (
        <EmptyState message="No check observations found in this time window." />
      )}

      {!loading &&
        !error &&
        observations &&
        observations.length > 0 &&
        filteredObservations.length === 0 && (
          <EmptyState message="No check observations match the active search and filters." />
        )}

      {!loading && !error && displayedObservations.length > 0 && (
        <Panel
          title={`Showing latest ${displayedObservations.length} of ${filteredObservations.length} checks`}
        >
          <div style={{ overflowX: 'auto', width: '100%' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: 'var(--font-sm)',
                textAlign: 'left',
              }}
            >
              <thead>
                <tr
                  style={{
                    borderBottom: '1px solid var(--color-border)',
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Observed At</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Type</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Component / Signal</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Location</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Result</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Code</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Latency</th>
                </tr>
              </thead>
              <tbody>
                {displayedObservations.map((obs, idx) => (
                  <tr
                    key={`${obs.signal_key}-${obs.observed_at}-${idx}`}
                    style={{ borderBottom: '1px solid var(--color-bg-subtle)' }}
                  >
                    <td
                      style={{
                        padding: 'var(--space-xs) var(--space-sm)',
                        fontFamily: 'var(--font-mono)',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {new Date(obs.observed_at).toLocaleString()}
                    </td>
                    <td
                      style={{
                        padding: 'var(--space-xs) var(--space-sm)',
                        textTransform: 'uppercase',
                        fontSize: 'var(--font-xs)',
                        fontWeight: 'var(--font-weight-medium)',
                      }}
                    >
                      {obs.check_type}
                    </td>
                    <td style={{ padding: 'var(--space-xs) var(--space-sm)' }}>
                      <div>
                        <strong>{obs.componentName}</strong>
                      </div>
                      <div
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 'var(--font-xs)',
                          color: 'var(--color-text-secondary)',
                        }}
                      >
                        {obs.signal_key}
                      </div>
                    </td>
                    <td
                      style={{
                        padding: 'var(--space-xs) var(--space-sm)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: 'var(--font-xs)',
                      }}
                    >
                      {obs.location}
                    </td>
                    <td style={{ padding: 'var(--space-xs) var(--space-sm)' }}>
                      <StatusBadge status={mapObservationHealth(obs.health)} />
                    </td>
                    <td
                      style={{
                        padding: 'var(--space-xs) var(--space-sm)',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {obs.response_status_code !== null &&
                      obs.response_status_code !== undefined
                        ? obs.response_status_code
                        : '—'}
                    </td>
                    <td
                      style={{
                        padding: 'var(--space-xs) var(--space-sm)',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {obs.latency_ms !== null && obs.latency_ms !== undefined
                        ? `${obs.latency_ms} ms`
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  )
}
