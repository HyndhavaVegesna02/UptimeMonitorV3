import { useCallback } from 'react'
import { Check, Warning } from '@phosphor-icons/react'
import { getComponents, getPublications } from '../../api/client'
import { toHealthStatus } from '../../api/statusMapping'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { Icon } from '../../components/Icon/Icon'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { useFetch } from '../../lib/useFetch'

export function PublicationsView() {
  const fetcher = useCallback(async () => {
    const [publications, components] = await Promise.all([
      getPublications(),
      getComponents(),
    ])
    const compMap = new Map(components.map((c) => [c.id, c.name]))
    return { publications, compMap }
  }, [])

  const { state, retry } = useFetch(fetcher)

  const loading = state.phase === 'loading'
  const error = state.phase === 'error' ? state : null
  const publications = state.phase === 'success' ? state.data.publications : undefined
  const compMap = state.phase === 'success' ? state.data.compMap : undefined

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      <p
        style={{
          fontSize: 'var(--font-sm)',
          color: 'var(--color-text-secondary)',
          margin: 0,
        }}
      >
        Timeline of status publication attempts to external Statuspage targets.
      </p>

      {loading && <LoadingState label="Loading publication history…" />}

      {error && (
        <ErrorState
          message={error.message ?? 'Failed to load publication history'}
          onRetry={retry}
        />
      )}

      {!loading && !error && publications && publications.length === 0 && (
        <EmptyState message="No publish attempts recorded yet." />
      )}

      {!loading && !error && publications && publications.length > 0 && (
        <Panel title="Showing recent publish attempts (capped at 50)">
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
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Published At</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Component</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Target Status</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Outcome</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Proposal</th>
                  <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Author</th>
                </tr>
              </thead>
              <tbody>
                {publications.map((pub) => {
                  const compName = compMap?.get(pub.component_id) ?? pub.component_id
                  const isSuccess = pub.outcome === 'succeeded'

                  return (
                    <tr key={pub.id} style={{ borderBottom: '1px solid var(--color-bg-subtle)' }}>
                      <td
                        style={{
                          padding: 'var(--space-xs) var(--space-sm)',
                          fontFamily: 'var(--font-mono)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {new Date(pub.published_at).toLocaleString()}
                      </td>
                      <td style={{ padding: 'var(--space-xs) var(--space-sm)' }}>
                        <div>
                          <strong>{compName}</strong>
                        </div>
                        <div
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: 'var(--font-xs)',
                            color: 'var(--color-text-secondary)',
                          }}
                        >
                          {pub.component_id}
                        </div>
                      </td>
                      <td style={{ padding: 'var(--space-xs) var(--space-sm)' }}>
                        <StatusBadge status={toHealthStatus(pub.status)} />
                      </td>
                      <td style={{ padding: 'var(--space-xs) var(--space-sm)' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '2px 8px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: 'var(--font-xs)',
                            fontWeight: 'var(--font-weight-medium)',
                            backgroundColor: isSuccess
                              ? 'var(--color-health-up-bg)'
                              : 'var(--color-health-down-bg)',
                            color: isSuccess
                              ? 'var(--color-health-up-text)'
                              : 'var(--color-health-down-text)',
                          }}
                        >
                          <Icon icon={isSuccess ? Check : Warning} aria-hidden />
                          <span>{isSuccess ? 'Succeeded' : 'Failed'}</span>
                        </span>
                      </td>
                      <td
                        style={{
                          padding: 'var(--space-xs) var(--space-sm)',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {pub.proposal_id !== null ? `#${pub.proposal_id}` : '—'}
                      </td>
                      <td
                        style={{
                          padding: 'var(--space-xs) var(--space-sm)',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {pub.author ?? '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  )
}
