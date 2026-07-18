import { useMemo, useState } from 'react'
import { EmptyState, ErrorState, LoadingState, Tile } from '../components'
import { cx } from '../lib/cx'
import { useAvailability } from '../features/availability/useAvailability'
import type { WindowPreset } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
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
 * The Availability tab (STORY-106 rewrite of the STORY-058/015d
 * incarnation), Step 1: one h1, a subtitle, and the 24h/7d/30d window
 * switcher in the header (AC1), wired to the surviving
 * `features/availability/{windowRange,useAvailability}.ts` hooks verbatim
 * (design brief: "re-skin freely; keep the tested behavior"). Renders one
 * Tile per topology component (name only) — the availability/completeness
 * metrics and drill-down land in the following steps of this story.
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
          {state.data.topology.map((component) => (
            <Tile key={component.id} elevation="md" className="availability-tile">
              <span className="text-body-lg availability-tile__name">{component.name}</span>
            </Tile>
          ))}
        </div>
      )}
    </div>
  )
}
