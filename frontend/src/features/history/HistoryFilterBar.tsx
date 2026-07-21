import { useId } from 'react'
import { MagnifyingGlass } from '@phosphor-icons/react'
import { Icon } from '../../components/Icon/Icon'
import { locationLabel } from '../dashboard/locationLabel'
import { RESULT_FILTER_OPTIONS } from './filterHistoryRows'
import type { ResultFilterKey } from './filterHistoryRows'
import './HistoryFilterBar.css'

export interface HistoryFilterBarProps {
  search: string
  onSearchChange: (value: string) => void
  result: ResultFilterKey
  onResultChange: (value: ResultFilterKey) => void
  location: string
  onLocationChange: (value: string) => void
  /** Derived from the currently-loaded rows (STORY-130 AC2) — unlike
   * `RESULT_FILTER_OPTIONS`, which is a fixed vocabulary. */
  locationOptions: string[]
}

/**
 * The History page's client-side filter toolbar (STORY-130 AC2) — a text
 * search plus two `<select>`s, every control with a visible `<label>` (web-
 * interface-guidelines: every form field needs an associated label, not
 * just a placeholder). The window toggle lives in the page itself (it is
 * the one control that refetches, a materially different concern from
 * these three purely client-side filters).
 */
export function HistoryFilterBar({
  search,
  onSearchChange,
  result,
  onResultChange,
  location,
  onLocationChange,
  locationOptions,
}: HistoryFilterBarProps) {
  const searchId = useId()
  const resultId = useId()
  const locationId = useId()

  return (
    <div className="history-filter-bar">
      <div className="history-filter-bar__field history-filter-bar__field--search">
        <label htmlFor={searchId}>Search</label>
        <div className="history-filter-bar__search-input">
          <Icon icon={MagnifyingGlass} aria-hidden size={14} />
          <input
            id={searchId}
            type="text"
            placeholder="Component, location, or signal…"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
          />
        </div>
      </div>

      <div className="history-filter-bar__field">
        <label htmlFor={resultId}>Result</label>
        <select
          id={resultId}
          value={result}
          onChange={(event) => onResultChange(event.target.value as ResultFilterKey)}
        >
          {RESULT_FILTER_OPTIONS.map((option) => (
            <option key={option.key} value={option.key}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="history-filter-bar__field">
        <label htmlFor={locationId}>Location</label>
        <select id={locationId} value={location} onChange={(event) => onLocationChange(event.target.value)}>
          <option value="all">All locations</option>
          {locationOptions.map((option) => (
            <option key={option} value={option}>
              {locationLabel(option)}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
