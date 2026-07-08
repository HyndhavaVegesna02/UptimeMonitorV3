import { Fragment, useMemo, useState } from 'react'
import type { AvailabilityDTO } from '../api/types'
import type { UptimeSegment } from '../components'
import {
  EmptyState,
  ErrorState,
  Icon,
  LoadingState,
  Panel,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  UptimeBar,
} from '../components'
import { cx } from '../lib/cx'
import { availabilityBand, formatDownLabel, formatPct, isCompletenessLow } from '../features/availability/format'
import { useAvailability } from '../features/availability/useAvailability'
import type { WindowPreset } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
import './AvailabilityPage.css'

const WINDOW_PRESETS: Array<{ value: WindowPreset; label: string }> = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
]

/** The Availability cell (STORY-058 AC1): a big mono % (colored by
 * `availabilityBand`), a "down" sublabel derived from the real verdict
 * counts, and — for the headline/rollup row only — the real `UptimeBar`
 * sparkline (`showBar=false` for per-signal drill-down rows, matching the
 * Dashboard's own convention of a bar-less drill-down table). */
function AvailabilityCell({
  rollup,
  segments,
  label,
  showBar = true,
}: {
  rollup: AvailabilityDTO
  segments: UptimeSegment[]
  label: string
  showBar?: boolean
}) {
  const band = availabilityBand(rollup.availability_pct)

  return (
    <div className="availability-cell">
      <div className="availability-cell__headline">
        <span
          className={cx(
            'text-mono availability-cell__value',
            band && `availability-cell__value--${band}`,
          )}
        >
          {formatPct(rollup.availability_pct)}
        </span>
        <span className="availability-cell__down-label">{formatDownLabel(rollup)}</span>
      </div>
      {showBar && (
        <UptimeBar
          segments={segments}
          label={`${label} availability segments`}
          className="availability-cell__bar"
        />
      )}
    </div>
  )
}

/** The Data completeness cell (STORY-058 AC1): a big mono % (never
 * rescaled — `completeness_pct` is a 0-1 wire fraction, per `formatPct`), a
 * "missing data" chip when the REAL completeness is below the 98% threshold
 * (`isCompletenessLow`), and a split bar — the `--color-health-up`-colored
 * portion is real completeness width, the remainder a HATCHED
 * `--color-health-missing` fill (never a flat/misleading "full" bar). */
function CompletenessCell({ rollup }: { rollup: AvailabilityDTO }) {
  const pct = rollup.completeness_pct
  const low = isCompletenessLow(pct)
  const width = pct === null ? 0 : Math.max(0, Math.min(100, pct * 100))

  return (
    <div className="availability-cell">
      <div className="availability-cell__headline">
        <span
          className={cx(
            'text-mono availability-cell__value',
            low && 'availability-cell__value--low',
          )}
        >
          {formatPct(pct)}
        </span>
        {low && (
          <span className="availability-cell__missing-chip">
            <span className="availability-cell__missing-dot" aria-hidden="true" />
            missing data
          </span>
        )}
      </div>
      <div className="completeness-bar" aria-hidden="true">
        <span className="completeness-bar__fill" style={{ width: `${width}%` }} />
        <span className="completeness-bar__missing" />
      </div>
    </div>
  )
}

/**
 * The Availability tab (STORY-058 rebuild of STORY-015d): a two-column
 * grid — Availability (real `availability_pct` + down count + sparkline)
 * and Data completeness (real `completeness_pct` + hatched split bar) — per
 * component, with a legend and a 24h/7d/30d window toggle
 * (`features/availability/windowRange.ts`, kept API-stable — Check History
 * (STORY-060) also imports it). Fetches `GET /api/v1/topology` +
 * `GET /api/v1/availability/component/{id}` (+ `GET /api/v1/history` for
 * the sparkline, an enhancement) per component via `useAvailability` (AC1,
 * AC2). Per-signal drill-down preserved (AC2) — expand a component to see
 * each signal's own availability/completeness cells (bar-less, mirroring
 * the Dashboard's drill-down convention).
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
    <div className="availability-page">
      <div className="availability-page__header">
        <div>
          <h1 className="text-h1 availability-page__title">Availability</h1>
          <p className="text-caption availability-page__subtitle">
            Uptime vs. how much monitoring data we actually captured
          </p>
        </div>

        <div className="availability-page__controls">
          <div className="availability-page__legend">
            <span className="availability-page__legend-item">
              <span
                className="availability-page__legend-swatch availability-page__legend-swatch--down"
                aria-hidden="true"
              />
              Down / outage
            </span>
            <span className="availability-page__legend-item">
              <span
                className="availability-page__legend-swatch availability-page__legend-swatch--missing"
                aria-hidden="true"
              />
              Missing data
            </span>
          </div>

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
        </div>
      </div>

      {state.phase === 'loading' && <LoadingState label="Loading availability…" />}

      {state.phase === 'error' && (
        <ErrorState message="Could not load availability" onRetry={retry} />
      )}

      {state.phase === 'success' && state.data.topology.length === 0 && (
        <EmptyState message="No components configured" />
      )}

      {state.phase === 'success' && state.data.topology.length > 0 && (
        <Panel>
          <Table className="availability-table">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Component</TableHeaderCell>
                <TableHeaderCell>Availability</TableHeaderCell>
                <TableHeaderCell>Data completeness</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {state.data.topology.map((component) => {
                const availability = state.data.availabilityByComponent[component.id]
                const segments = state.data.segmentsByComponent[component.id] ?? []
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
                    <TableRow>
                      <TableCell>
                        {hasSignals ? (
                          <button
                            type="button"
                            className="availability-table__expand"
                            aria-expanded={expanded}
                            onClick={() => toggleExpanded(component.id)}
                          >
                            <Icon
                              name="chevron-right"
                              className={cx(
                                'availability-table__chevron',
                                expanded && 'availability-table__chevron--expanded',
                              )}
                            />
                            <span className="text-mono availability-table__name">
                              {component.name}
                            </span>
                          </button>
                        ) : (
                          <span className="text-mono availability-table__name availability-table__name--static">
                            {component.name}
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <AvailabilityCell
                          rollup={availability.rollup}
                          segments={segments}
                          label={component.name}
                        />
                      </TableCell>
                      <TableCell>
                        <CompletenessCell rollup={availability.rollup} />
                      </TableCell>
                    </TableRow>

                    {expanded &&
                      availability.signals.map((signal) => {
                        const signalName = signalNameByKey.get(signal.signal_key) ?? signal.signal_key
                        return (
                          <TableRow key={signal.signal_key} className="availability-table__child">
                            <TableCell>
                              <span className="availability-table__signal-name">
                                {signalName}
                              </span>{' '}
                              <span className="text-mono availability-table__signal-key">
                                {signal.signal_key}
                              </span>
                            </TableCell>
                            <TableCell>
                              <AvailabilityCell
                                rollup={signal}
                                segments={[]}
                                label={signalName}
                                showBar={false}
                              />
                            </TableCell>
                            <TableCell>
                              <CompletenessCell rollup={signal} />
                            </TableCell>
                          </TableRow>
                        )
                      })}
                  </Fragment>
                )
              })}
            </TableBody>
          </Table>
        </Panel>
      )}
    </div>
  )
}
