import { Fragment, useMemo, useState } from 'react'
import type { AvailabilityDTO } from '../api/types'
import { EmptyState, ErrorState, LoadingState, Panel } from '../components'
import { cx } from '../lib/cx'
import { formatPct } from '../features/availability/format'
import { useAvailability } from '../features/availability/useAvailability'
import type { WindowPreset } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
import './AvailabilityPage.css'

const WINDOW_PRESETS: Array<{ value: WindowPreset; label: string }> = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
]

/** One value+bar cell (STORY-015d AC1, AC4): the numeric value is ALWAYS
 * rendered as text — the bar is never the sole carrier. A null pct (a
 * degenerate/no-data window) renders "no data" and an empty bar, never
 * `0%`/`NaN%`. */
function AvailabilityStat({ pct }: { pct: number | null }) {
  const hasData = pct !== null
  const width = hasData ? Math.max(0, Math.min(100, pct)) : 0

  return (
    <span className="availability-stat">
      <span className="text-mono availability-stat__value">{formatPct(pct)}</span>
      <span className="availability-stat__track" aria-hidden="true">
        <span
          className={cx(
            'availability-stat__fill',
            !hasData && 'availability-stat__fill--empty',
          )}
          style={{ width: `${width}%` }}
        />
      </span>
    </span>
  )
}

/** The three shared cells (availability / completeness / verdict counts)
 * every row — rollup or per-signal child — renders the same way. */
function AvailabilityCells({ availability }: { availability: AvailabilityDTO }) {
  return (
    <>
      <td>
        <AvailabilityStat pct={availability.availability_pct} />
      </td>
      <td>
        <span className="text-mono">{formatPct(availability.completeness_pct)}</span>
      </td>
      <td>
        <span className="availability-table__counts text-mono">
          {availability.passing_verdicts}/{availability.total_verdicts} passing ·{' '}
          {availability.maintenance_verdicts} maint · {availability.gap_verdicts} gap
        </span>
      </td>
    </>
  )
}

/**
 * The Availability tab (STORY-015d): two-grain availability over a
 * selectable window — the component-grain rollup as the headline row
 * (`rollup_group` — "a group is only as available as its worst signal"),
 * expandable to each per-signal child, each computed with its own
 * configured interval (STORY-044). Fetches `GET /api/v1/topology` +
 * `GET /api/v1/availability/component/{id}` per component via
 * `useAvailability` (AC1, AC2).
 */
export function AvailabilityPage() {
  const [preset, setPreset] = useState<WindowPreset>('24h')
  // Memoized per preset (not per render) so `useAvailability`'s fetcher
  // keeps a STABLE identity while the window selection is unchanged, and
  // only gets a new one — triggering a refetch — when the preset changes.
  const range = useMemo(() => windowToRange(preset), [preset])
  const { state, retry } = useAvailability(range)
  const [expandedIds, setExpandedIds] = useState<ReadonlySet<string>>(new Set())

  function toggleExpanded(componentId: string) {
    setExpandedIds((current) => {
      const next = new Set(current)
      if (next.has(componentId)) {
        next.delete(componentId)
      } else {
        next.add(componentId)
      }
      return next
    })
  }

  return (
    <Panel title="Availability" headingLevel="h1">
      <div
        className="availability-page__window"
        role="group"
        aria-label="Time window"
      >
        {WINDOW_PRESETS.map((option) => (
          <button
            key={option.value}
            type="button"
            className={cx(
              'availability-page__window-button',
              preset === option.value && 'availability-page__window-button--active',
            )}
            aria-pressed={preset === option.value}
            onClick={() => setPreset(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {state.phase === 'loading' && <LoadingState label="Loading availability…" />}

      {state.phase === 'error' && (
        <ErrorState message="Could not load availability" onRetry={retry} />
      )}

      {state.phase === 'success' && state.data.topology.length === 0 && (
        <EmptyState message="No components configured" />
      )}

      {state.phase === 'success' && state.data.topology.length > 0 && (
        <table className="availability-table">
          <thead>
            <tr>
              <th scope="col">Component</th>
              <th scope="col">Availability</th>
              <th scope="col">Completeness</th>
              <th scope="col">Verdicts</th>
            </tr>
          </thead>
          <tbody>
            {state.data.topology.map((component) => {
              const availability = state.data.availabilityByComponent[component.id]
              const expanded = expandedIds.has(component.id)
              const hasSignals = component.signals.length > 0
              // The availability response's per-signal children carry only
              // `signal_key` (no `name`) — the topology response is the
              // source of the display name (STORY-015d AC1).
              const signalNameByKey = new Map(
                component.signals.map((signal) => [signal.signal_key, signal.name]),
              )

              return (
                <Fragment key={component.id}>
                  <tr>
                    <td>
                      {hasSignals ? (
                        <button
                          type="button"
                          className="availability-table__expand"
                          aria-expanded={expanded}
                          onClick={() => toggleExpanded(component.id)}
                        >
                          <span className="availability-table__caret" aria-hidden="true">
                            {expanded ? '▾' : '▸'}
                          </span>
                          {component.name}
                        </button>
                      ) : (
                        <span className="availability-table__name">{component.name}</span>
                      )}
                    </td>
                    <AvailabilityCells availability={availability.rollup} />
                  </tr>

                  {expanded &&
                    availability.signals.map((signal) => (
                      <tr key={signal.signal_key} className="availability-table__child">
                        <td>
                          <span className="availability-table__signal-name">
                            {signalNameByKey.get(signal.signal_key) ?? signal.signal_key}
                          </span>{' '}
                          <span className="text-mono availability-table__signal-key">
                            {signal.signal_key}
                          </span>
                        </td>
                        <AvailabilityCells availability={signal} />
                      </tr>
                    ))}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
