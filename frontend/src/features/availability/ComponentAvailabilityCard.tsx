import { useState, useCallback } from 'react'
import { CaretDown, CaretUp } from '@phosphor-icons/react'
import { getComponentAvailability } from '../../api/client'
import type { ComponentTopologyDTO } from '../../api/types'
import { Button } from '../../components/Button/Button'
import { ErrorState } from '../../components/ErrorState/ErrorState'
import { Icon } from '../../components/Icon/Icon'
import { LoadingState } from '../../components/LoadingState/LoadingState'
import { Panel } from '../../components/Panel/Panel'
import { useFetch } from '../../lib/useFetch'

interface ComponentAvailabilityCardProps {
  component: ComponentTopologyDTO
  since?: string
  until?: string
}

export function ComponentAvailabilityCard({
  component,
  since,
  until,
}: ComponentAvailabilityCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const fetcher = useCallback(
    () => getComponentAvailability(component.id, { since, until }),
    [component.id, since, until],
  )

  const { state, retry } = useFetch(fetcher)

  if (state.phase === 'loading') {
    return (
      <Panel title={component.name}>
        <LoadingState label={`Calculating availability for ${component.name}…`} />
      </Panel>
    )
  }

  if (state.phase === 'error') {
    return (
      <Panel title={component.name}>
        <ErrorState message={state.message} onRetry={retry} />
      </Panel>
    )
  }

  const data = state.data
  const rollup = data.rollup
  const signals = data.signals ?? []

  const availPctText =
    rollup.availability_pct !== null && rollup.availability_pct !== undefined
      ? `${(rollup.availability_pct * 100).toFixed(1)}%`
      : 'No data'

  const compPctText =
    rollup.completeness_pct !== null && rollup.completeness_pct !== undefined
      ? `${(rollup.completeness_pct * 100).toFixed(1)}%`
      : 'No data'

  const isLowCompleteness =
    rollup.completeness_pct !== null &&
    rollup.completeness_pct !== undefined &&
    rollup.completeness_pct < 0.9

  const downVerdicts = Math.max(
    0,
    rollup.total_verdicts - rollup.passing_verdicts - rollup.maintenance_verdicts,
  )

  const signalMap = new Map(component.signals.map((s) => [s.signal_key, s]))

  return (
    <Panel title={component.name}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--font-xs)',
              color: 'var(--color-text-secondary)',
              backgroundColor: 'var(--color-bg-subtle)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            ID: {component.id}
          </span>
          {signals.length > 0 && (
            <Button
              variant="ghost"
              onClick={() => setIsExpanded((prev) => !prev)}
              aria-expanded={isExpanded}
            >
              <Icon icon={isExpanded ? CaretUp : CaretDown} aria-hidden />
              <span>{isExpanded ? 'Hide Signals' : `Signals (${signals.length})`}</span>
            </Button>
          )}
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: 'var(--space-sm)',
            backgroundColor: 'var(--color-bg-subtle)',
            padding: 'var(--space-md)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <div>
            <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Availability
            </div>
            <div
              style={{
                fontSize: 'var(--font-xl)',
                fontWeight: 'var(--font-weight-semibold)',
                fontFamily: 'var(--font-mono)',
                color:
                  rollup.availability_pct !== null && rollup.availability_pct >= 0.999
                    ? 'var(--color-health-up-text)'
                    : rollup.availability_pct !== null && rollup.availability_pct >= 0.95
                      ? 'var(--color-health-degraded-text)'
                      : 'var(--color-text-primary)',
              }}
            >
              {availPctText}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Completeness
            </div>
            <div
              style={{
                fontSize: 'var(--font-xl)',
                fontWeight: 'var(--font-weight-semibold)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {compPctText}
            </div>
            {isLowCompleteness && (
              <span
                style={{
                  fontSize: 'var(--font-xs)',
                  color: 'var(--color-health-degraded-text)',
                  backgroundColor: 'var(--color-health-degraded-bg)',
                  padding: '1px 6px',
                  borderRadius: 'var(--radius-sm)',
                  display: 'inline-block',
                  marginTop: '2px',
                }}
              >
                Low completeness
              </span>
            )}
          </div>

          <div>
            <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Passing / Total
            </div>
            <div
              style={{
                fontSize: 'var(--font-md)',
                fontFamily: 'var(--font-mono)',
                marginTop: '4px',
              }}
            >
              <strong style={{ color: 'var(--color-health-up-text)' }}>
                {rollup.passing_verdicts}
              </strong>{' '}
              / {rollup.total_verdicts}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Down / Maintenance
            </div>
            <div
              style={{
                fontSize: 'var(--font-md)',
                fontFamily: 'var(--font-mono)',
                marginTop: '4px',
              }}
            >
              <span
                style={{
                  color: downVerdicts > 0 ? 'var(--color-health-down-text)' : 'inherit',
                }}
              >
                {downVerdicts}
              </span>{' '}
              /{' '}
              <span style={{ color: 'var(--color-health-maintenance-text)' }}>
                {rollup.maintenance_verdicts}
              </span>
            </div>
          </div>

          <div>
            <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Gap Verdicts
            </div>
            <div
              style={{
                fontSize: 'var(--font-md)',
                fontFamily: 'var(--font-mono)',
                marginTop: '4px',
              }}
            >
              {rollup.gap_verdicts}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-text-secondary)' }}>
              Locations
            </div>
            <div
              style={{
                fontSize: 'var(--font-md)',
                fontFamily: 'var(--font-mono)',
                marginTop: '4px',
              }}
            >
              {rollup.distinct_locations} location
              {rollup.distinct_locations === 1 ? '' : 's'}
            </div>
          </div>
        </div>

        {isExpanded && signals.length > 0 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-xs)',
              borderTop: '1px solid var(--color-border)',
              paddingTop: 'var(--space-sm)',
            }}
          >
            <div style={{ fontSize: 'var(--font-sm)', fontWeight: 'var(--font-weight-medium)' }}>
              Signal Breakdown
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: 'var(--font-sm)',
                }}
              >
                <thead>
                  <tr
                    style={{
                      borderBottom: '1px solid var(--color-border)',
                      textAlign: 'left',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Signal</th>
                    <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Interval</th>
                    <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Availability</th>
                    <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Completeness</th>
                    <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Passing</th>
                    <th style={{ padding: 'var(--space-xs) var(--space-sm)' }}>Locations</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((sig) => {
                    const meta = signalMap.get(sig.signal_key)
                    const sigAvailText =
                      sig.availability_pct !== null && sig.availability_pct !== undefined
                        ? `${(sig.availability_pct * 100).toFixed(1)}%`
                        : 'No data'
                    const sigCompText =
                      sig.completeness_pct !== null && sig.completeness_pct !== undefined
                        ? `${(sig.completeness_pct * 100).toFixed(1)}%`
                        : 'No data'
                    const intervalText =
                      meta?.interval_seconds !== null && meta?.interval_seconds !== undefined
                        ? `${meta.interval_seconds}s`
                        : '—'

                    return (
                      <tr
                        key={sig.signal_key}
                        style={{ borderBottom: '1px solid var(--color-bg-subtle)' }}
                      >
                        <td style={{ padding: 'var(--space-xs) var(--space-sm)' }}>
                          <div>
                            <strong>{meta?.name ?? sig.signal_key}</strong>
                          </div>
                          <div
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: 'var(--font-xs)',
                              color: 'var(--color-text-secondary)',
                            }}
                          >
                            {sig.signal_key}
                          </div>
                        </td>
                        <td
                          style={{
                            padding: 'var(--space-xs) var(--space-sm)',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {intervalText}
                        </td>
                        <td
                          style={{
                            padding: 'var(--space-xs) var(--space-sm)',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {sigAvailText}
                        </td>
                        <td
                          style={{
                            padding: 'var(--space-xs) var(--space-sm)',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {sigCompText}
                        </td>
                        <td
                          style={{
                            padding: 'var(--space-xs) var(--space-sm)',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {sig.passing_verdicts} / {sig.total_verdicts}
                        </td>
                        <td
                          style={{
                            padding: 'var(--space-xs) var(--space-sm)',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {sig.distinct_locations}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Panel>
  )
}
