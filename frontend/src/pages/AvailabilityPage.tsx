import { useMemo, useState } from 'react'
import type { ComponentTopologyDTO } from '../api/types'
import type { DownCounts } from '../features/availability/format'
import {
  availabilityBand,
  formatDownLabel,
  formatPct,
  isCompletenessLow,
} from '../features/availability/format'
import { useAvailability } from '../features/availability/useAvailability'
import type { WindowPreset } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
import type { UptimeSegment } from '../components'
import { EmptyState, ErrorState, Icon, LoadingState, Tile, UptimeBar } from '../components'
import { cx } from '../lib/cx'
import './AvailabilityPage.css'

const WINDOW_PRESETS: Array<{ value: WindowPreset; label: string }> = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
]

interface WindowSwitcherProps {
  value: WindowPreset
  onChange: (preset: WindowPreset) => void
}

/**
 * The 24h/7d/30d window switcher (STORY-106 AC1, design brief §IA — "in the
 * page header"): a `role="group"` button set, the active window carrying
 * `aria-pressed="true"` (never color alone — the active class also bumps
 * font-weight/background), each button >=44px (`--target-min`) and natively
 * keyboard-operable (a real `<button>`, not a styled `div`).
 */
function WindowSwitcher({ value, onChange }: WindowSwitcherProps) {
  return (
    <div className="availability-page__window" role="group" aria-label="Time window">
      {WINDOW_PRESETS.map((preset) => (
        <button
          key={preset.value}
          type="button"
          className={cx(
            'availability-page__window-button',
            value === preset.value && 'availability-page__window-button--active',
          )}
          aria-pressed={value === preset.value}
          onClick={() => onChange(preset.value)}
        >
          {preset.label}
        </button>
      ))}
    </div>
  )
}

/**
 * The legend explaining the two non-nominal sparkline/value cues (STORY-106
 * AC2): a solid swatch for "down" and a HATCHED swatch (mirrors
 * `UptimeBar`'s own missing-segment gradient) for "missing data" — pattern
 * plus text, never color alone.
 */
function AvailabilityLegend() {
  return (
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
  )
}

interface AvailabilityMetricProps {
  rollup: DownCounts
  segments: UptimeSegment[]
  label: string
  /** `false` for a per-signal drill-down row — there is no dedicated
   * per-signal history fetch (STORY-106 AC3, mirrors the pre-rewrite
   * Availability's bar-less drill-down convention), so a signal row shows
   * only its own real %/down-count, never a fabricated bar. */
  showBar?: boolean
}

/**
 * The Availability metric (STORY-106 AC2): a large `--fs-stat` JetBrains
 * Mono percentage (colored by `availabilityBand` — a reinforcing cue only,
 * the number itself is the accessible text), a "down" sublabel derived from
 * the REAL verdict counts, and — for a rollup row — the windowed `UptimeBar`
 * sparkline.
 */
function AvailabilityMetric({ rollup, segments, label, showBar = true }: AvailabilityMetricProps) {
  const band = availabilityBand(rollup.availability_pct)

  return (
    <div className="availability-metric">
      <span className="text-label availability-metric__label">Availability</span>
      <div className="availability-metric__headline">
        <span
          className={cx(
            'text-mono availability-metric__value',
            band && `availability-metric__value--${band}`,
          )}
        >
          {formatPct(rollup.availability_pct)}
        </span>
        <span className="text-caption availability-metric__down">{formatDownLabel(rollup)}</span>
      </div>
      {showBar && (
        <UptimeBar
          segments={segments}
          label={`${label} availability segments`}
          className="availability-metric__bar"
        />
      )}
    </div>
  )
}

interface CompletenessMetricProps {
  completenessPct: number | null
}

/**
 * The Data completeness metric (STORY-106 AC2) — the unambiguous
 * "N% of expected checks received" phrasing carried from the accepted
 * redesign work (journal #9: an adjacent "missing data" chip made a
 * RECEIVED share read like a missing one). A `null` completeness (no data
 * at all) omits the sub-label — there is no "received share" to state.
 */
function CompletenessMetric({ completenessPct }: CompletenessMetricProps) {
  const low = isCompletenessLow(completenessPct)

  return (
    <div className="availability-metric">
      <span className="text-label availability-metric__label">Data completeness</span>
      <p className="availability-metric__headline">
        <span
          className={cx(
            'text-mono availability-metric__value',
            low && 'availability-metric__value--low',
          )}
        >
          {formatPct(completenessPct)}
        </span>
        {completenessPct !== null && (
          <span className="text-caption availability-metric__completeness-sub">
            of expected checks received
          </span>
        )}
      </p>
    </div>
  )
}

interface ComponentTileProps {
  component: ComponentTopologyDTO
  rollup: DownCounts & { completeness_pct: number | null }
  segments: UptimeSegment[]
  signals: Array<DownCounts & { completeness_pct: number | null; signal_key: string }>
  expanded: boolean
  onToggleExpand: () => void
}

/**
 * One per-component Availability tile (STORY-106 AC2/AC3): name, the
 * Availability + Data completeness metrics on the rollup, and — for a
 * component with mapped signals — an `aria-expanded` drill-down toggle
 * revealing each signal's own metrics (bar-less, per
 * `AvailabilityMetric`'s `showBar={false}`). A zero-signal component
 * renders a plain, non-interactive name (no broken expand affordance).
 */
function ComponentTile({
  component,
  rollup,
  segments,
  signals,
  expanded,
  onToggleExpand,
}: ComponentTileProps) {
  const band = availabilityBand(rollup.availability_pct)
  const hasSignals = component.signals.length > 0
  const signalNameByKey = new Map(
    component.signals.map((signal) => [signal.signal_key, signal.name]),
  )

  return (
    <Tile elevation="md" accent={band ?? undefined} className="availability-tile">
      {hasSignals ? (
        <button
          type="button"
          className="availability-tile__expand"
          aria-expanded={expanded}
          aria-controls={`availability-signals-${component.id}`}
          onClick={onToggleExpand}
        >
          <Icon
            name="chevron-right"
            className={cx(
              'availability-tile__chevron',
              expanded && 'availability-tile__chevron--expanded',
            )}
          />
          <span className="text-body-lg availability-tile__name">{component.name}</span>
        </button>
      ) : (
        <span className="text-body-lg availability-tile__name availability-tile__name--static">
          {component.name}
        </span>
      )}

      <div className="availability-tile__metrics">
        <AvailabilityMetric rollup={rollup} segments={segments} label={component.name} />
        <CompletenessMetric completenessPct={rollup.completeness_pct} />
      </div>

      {hasSignals && expanded && (
        <ul id={`availability-signals-${component.id}`} className="availability-tile__signals">
          {signals.map((signal) => {
            const signalName = signalNameByKey.get(signal.signal_key) ?? signal.signal_key
            return (
              <li key={signal.signal_key} className="availability-tile__signal">
                <div className="availability-tile__signal-header">
                  <span className="text-body availability-tile__signal-name">{signalName}</span>
                  <span className="text-caption text-mono availability-tile__signal-key">
                    {signal.signal_key}
                  </span>
                </div>
                <div className="availability-tile__metrics availability-tile__metrics--signal">
                  <AvailabilityMetric
                    rollup={signal}
                    segments={[]}
                    label={signalName}
                    showBar={false}
                  />
                  <CompletenessMetric completenessPct={signal.completeness_pct} />
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </Tile>
  )
}

/**
 * The Availability tab (STORY-106 rewrite of the STORY-058/015d
 * incarnation): one h1, a subtitle, a 24h/7d/30d window switcher in the
 * header (AC1), a legend explaining down vs missing (AC2), and one Tile per
 * monitored component — availability % + windowed bar + data completeness,
 * expandable to per-signal drill-down rows (AC3). Rewires the surviving
 * `features/availability/{windowRange,useAvailability,format,segments}.ts`
 * hooks verbatim (design brief: "re-skin freely; keep the tested
 * behavior") rather than re-deriving the fetch/merge logic.
 */
export function AvailabilityPage() {
  const [preset, setPreset] = useState<WindowPreset>('24h')
  // Memoized per preset (not per render) so `useAvailability`'s fetcher
  // keeps a STABLE identity while the selection is unchanged, and only
  // gets a new one — triggering a refetch — when the preset changes.
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
        <div className="availability-page__heading">
          <h1 className="text-h1 availability-page__title">Availability</h1>
          <p className="text-caption availability-page__subtitle">
            Uptime vs. how much monitoring data we actually captured
          </p>
        </div>
        <WindowSwitcher value={preset} onChange={setPreset} />
      </div>

      <AvailabilityLegend />

      {state.phase === 'loading' && (
        <Tile elevation="md">
          <LoadingState label="Loading availability…" />
        </Tile>
      )}

      {state.phase === 'error' && (
        <Tile elevation="md">
          <ErrorState message="Could not load availability" onRetry={retry} />
        </Tile>
      )}

      {state.phase === 'success' && state.data.topology.length === 0 && (
        <Tile elevation="md">
          <EmptyState message="No components configured" />
        </Tile>
      )}

      {state.phase === 'success' && state.data.topology.length > 0 && (
        <div className="availability-grid">
          {state.data.topology.map((component) => {
            const availability = state.data.availabilityByComponent[component.id]
            const segments = state.data.segmentsByComponent[component.id] ?? []

            return (
              <ComponentTile
                key={component.id}
                component={component}
                rollup={availability.rollup}
                segments={segments}
                signals={availability.signals}
                expanded={expandedIds.has(component.id)}
                onToggleExpand={() => toggleExpanded(component.id)}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
