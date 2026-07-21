import { WINDOW_OPTIONS } from './windowRange'
import type { WindowKey } from './windowRange'
import './WindowToggle.css'

export interface WindowToggleProps {
  value: WindowKey
  onChange: (windowKey: WindowKey) => void
}

/**
 * The 24h/7d/30d window segmented control (STORY-129 AC3) - same
 * `role="group"` + `aria-pressed` segmented-control shape as the Dashboard's
 * `ProbeLocationsPanel` metric switcher, native `<button>`s so keyboard
 * operability (Enter/Space) is free. Selecting a window is a genuinely new
 * fetch, never a data-refresh flicker - no motion here beyond the `:active`
 * press feedback (emil-design-eng: no motion on data refresh).
 */
export function WindowToggle({ value, onChange }: WindowToggleProps) {
  return (
    <div className="window-toggle" role="group" aria-label="Window">
      {WINDOW_OPTIONS.map((option) => (
        <button
          key={option.key}
          type="button"
          aria-pressed={value === option.key}
          onClick={() => onChange(option.key)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
