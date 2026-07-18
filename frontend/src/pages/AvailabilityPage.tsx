import { useMemo, useState } from 'react'
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
import { EmptyState, ErrorState, LoadingState, Tile, UptimeBar } from '../components'
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
}

/**
 * The Availability metric (STORY-106 AC2): a large `--fs-stat` JetBrains
 * Mono percentage (colored by `availabilityBand` — a reinforcing cue only,
 * the number itself is the accessible text), a "down" sublabel derived from
 * the REAL verdict counts, and the windowed `UptimeBar` sparkline.
 */
function AvailabilityMetric({ rollup, segments, label }: AvailabilityMetricProps) {
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
      <UptimeBar
        segments={segments}
        label={`${label} availability segments`}
        className="availability-metric__bar"
      />
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

/**
 * The Availability tab (STORY-106 rewrite of the STORY-058/015d
 * incarnation), Step 2: per-component Availability + Data completeness
 * metrics (AC2) and the down/missing legend, on top of Step 1's header +
 * window switcher. Rewires the surviving
 * `features/availability/{windowRange,useAvailability,format,segments}.ts`
 * hooks verbatim (design brief: "re-skin freely; keep the tested
 * behavior") rather than re-deriving the fetch/merge logic. Signal-level
 * drill-down lands in the next step of this story.
 */
export function AvailabilityPage() {
  const [preset, setPreset] = useState<WindowPreset>('24h')
  // Memoized per preset (not per render) so `useAvailability`'s fetcher
  // keeps a STABLE identity while the selection is unchanged, and only
  // gets a new one — triggering a refetch — when the preset changes.
  const range = useMemo(() => windowToRange(preset), [preset])
  const { state, retry } = useAvailability(range)

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
            const band = availabilityBand(availability.rollup.availability_pct)

            return (
              <Tile
                key={component.id}
                elevation="md"
                accent={band ?? undefined}
                className="availability-tile"
              >
                <span className="text-body-lg availability-tile__name">{component.name}</span>
                <div className="availability-tile__metrics">
                  <AvailabilityMetric
                    rollup={availability.rollup}
                    segments={segments}
                    label={component.name}
                  />
                  <CompletenessMetric completenessPct={availability.rollup.completeness_pct} />
                </div>
              </Tile>
            )
          })}
        </div>
      )}
    </div>
  )
}
