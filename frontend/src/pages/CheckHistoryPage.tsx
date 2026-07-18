import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  RelativeTime,
  StatusBadge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../components'
import { cx } from '../lib/cx'
import { formatLocationLabel } from '../lib/formatLocation'
import type { AvailabilityRange, WindowPreset } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
import {
  ALL_LOCATIONS,
  ALL_RESULTS,
  filterHistoryRows,
  initialHistoryFilters,
  uniqueLocations,
} from '../features/history/filterHistory'
import type { HistoryFilters } from '../features/history/filterHistory'
import { buildHistorySummary } from '../features/history/historySummary'
import { latencyTone } from '../features/history/latencyTone'
import { observationHealth } from '../features/history/observationHealth'
import { useAllHistory } from '../features/history/useAllHistory'
import './CheckHistoryPage.css'

const WINDOW_PRESETS: Array<{ value: WindowPreset; label: string }> = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
]

/** The result-filter `<select>` options (STORY-108 AC1) — the fixed
 * `ObservationDTO.health` wire vocabulary, not derived from loaded data, so
 * the option is present and usable even before a matching row has loaded. */
const RESULT_OPTIONS: Array<{ value: string; label: string }> = [
  { value: ALL_RESULTS, label: 'All results' },
  { value: 'up', label: 'Up' },
  { value: 'degraded', label: 'Degraded' },
  { value: 'down', label: 'Down' },
]

/** `latency_ms` renders as integer milliseconds; `null` (no measurement)
 * renders as an em-dash — never `0 ms` (page-local copy, matching the
 * existing per-page file-scope-isolation convention — see
 * `DashboardPage.tsx::formatLatency`). */
function formatLatency(latencyMs: number | null): string {
  return latencyMs === null ? '—' : `${latencyMs} ms`
}

/** `response_status_code` renders as its raw integer; `null` (missing/
 * unparsable at the source, or a pre-migration row) renders as an em-dash —
 * the same convention as `formatLatency`. */
function formatResponseStatusCode(code: number | null): string {
  return code === null ? '—' : `${code}`
}

interface WindowSwitcherProps {
  value: WindowPreset
  onChange: (preset: WindowPreset) => void
}

/** The 24h/7d/30d window switcher (mirrors `AvailabilityPage`'s own —
 * duplicated per this codebase's page-local convention rather than
 * extracted into a shared primitive, since each page independently owns its
 * markup/class names). */
function WindowSwitcher({ value, onChange }: WindowSwitcherProps) {
  return (
    <div className="check-history-page__window" role="group" aria-label="Time window">
      {WINDOW_PRESETS.map((preset) => (
        <button
          key={preset.value}
          type="button"
          className={cx(
            'check-history-page__window-button',
            value === preset.value && 'check-history-page__window-button--active',
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
 * The Check History tab (STORY-108, rewriting STORY-060/015e): a dense,
 * system-wide, chronological observation ledger on the Mission Teal tokens.
 * Rewires `useAllHistory` (AC1 — merges every topology signal's
 * `GET /api/v1/history` for the selected 24h/7d/30d window into one
 * newest-first list) verbatim, and the surviving `filterHistory.ts`
 * client-side toolbar helpers (search/result/location — none of the three
 * trigger a refetch, only the window toggle does).
 *
 * The free-text search box is seeded from `?signal=` (STORY-107's "View
 * checks" deep link) via a LAZY `useState` initializer — read exactly ONCE
 * on mount, never re-synced if the URL changes later, so an operator
 * editing the box afterward is never silently overwritten.
 */
export function CheckHistoryPage() {
  const [searchParams] = useSearchParams()
  const [filters, setFilters] = useState<HistoryFilters>(() => initialHistoryFilters(searchParams))
  const [preset, setPreset] = useState<WindowPreset>('24h')
  // Memoized per preset (not per render) so `useAllHistory`'s fetcher keeps
  // a STABLE identity while the window selection is unchanged (the same
  // discipline `AvailabilityPage`/`DashboardPage` use).
  const range: AvailabilityRange = useMemo(() => windowToRange(preset), [preset])
  const { state, retry } = useAllHistory(range)

  const rows = useMemo(() => (state.phase === 'success' ? state.data : []), [state])
  const locationOptions = useMemo(() => uniqueLocations(rows), [rows])
  const filtered = useMemo(() => filterHistoryRows(rows, filters), [rows, filters])
  const summary = useMemo(() => buildHistorySummary(filtered, filters), [filtered, filters])

  return (
    <div className="check-history-page">
      <div className="check-history-page__header">
        <h1 className="text-h1 check-history-page__title">Check History</h1>
        <p className="text-caption check-history-page__subtitle">
          A chronological ledger of every monitored signal&rsquo;s observations across the
          selected time window.
        </p>
      </div>

      <div className="check-history-page__toolbar">
        <div className="check-history-page__field">
          <label className="check-history-page__label" htmlFor="check-history-search">
            Search
          </label>
          <input
            id="check-history-search"
            type="search"
            className="check-history-page__search-input"
            placeholder="Search component, location, or signal…"
            value={filters.query}
            onChange={(event) =>
              setFilters((previous) => ({ ...previous, query: event.target.value }))
            }
          />
        </div>

        <div className="check-history-page__field">
          <label className="check-history-page__label" htmlFor="check-history-result">
            Result
          </label>
          <select
            id="check-history-result"
            className="check-history-page__select"
            value={filters.result}
            onChange={(event) =>
              setFilters((previous) => ({ ...previous, result: event.target.value }))
            }
          >
            {RESULT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="check-history-page__field">
          <label className="check-history-page__label" htmlFor="check-history-location">
            Location
          </label>
          <select
            id="check-history-location"
            className="check-history-page__select"
            value={filters.location}
            onChange={(event) =>
              setFilters((previous) => ({ ...previous, location: event.target.value }))
            }
          >
            <option value={ALL_LOCATIONS}>All locations</option>
            {locationOptions.map((location) => (
              <option key={location} value={location}>
                {formatLocationLabel(location)}
              </option>
            ))}
          </select>
        </div>

        <WindowSwitcher value={preset} onChange={setPreset} />
      </div>

      {state.phase === 'success' && (
        <p className="text-caption check-history-page__summary" aria-live="polite">
          {summary}
        </p>
      )}

      {state.phase === 'loading' && <LoadingState label="Loading observations…" />}

      {state.phase === 'error' && (
        <ErrorState message="Could not load check history" onRetry={retry} />
      )}

      {state.phase === 'success' && rows.length === 0 && (
        <EmptyState
          message="No observations in this window"
          detail="Try a wider time window — no signal reported a check in this range."
        />
      )}

      {state.phase === 'success' && rows.length > 0 && filtered.length === 0 && (
        <EmptyState
          message="No observations match your filters"
          detail="Try widening the time window or clearing a filter."
        />
      )}

      {state.phase === 'success' && filtered.length > 0 && (
        <div className="check-history-page__table-wrapper">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Timestamp</TableHeaderCell>
                <TableHeaderCell>Component</TableHeaderCell>
                <TableHeaderCell>Location</TableHeaderCell>
                <TableHeaderCell>Result</TableHeaderCell>
                <TableHeaderCell>Code</TableHeaderCell>
                <TableHeaderCell>Latency</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.map((row, index) => {
                const tone = latencyTone(row.latency_ms)
                return (
                  <TableRow key={`${row.signal_key}-${row.location}-${row.observed_at}-${index}`}>
                    <TableCell className="text-mono">
                      <RelativeTime iso={row.observed_at} />
                    </TableCell>
                    <TableCell>
                      <div className="check-history-page__component">
                        <span className="text-body check-history-page__component-name">
                          {row.componentName}
                        </span>
                        <span className="text-caption text-mono check-history-page__component-type">
                          {row.check_type.toUpperCase()}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-mono" title={row.location}>
                      {formatLocationLabel(row.location)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={observationHealth(row.health)} />
                    </TableCell>
                    <TableCell className="text-mono">
                      {formatResponseStatusCode(row.response_status_code)}
                    </TableCell>
                    <TableCell
                      className={cx(
                        'text-mono',
                        tone && `check-history-page__latency--${tone}`,
                      )}
                    >
                      {formatLatency(row.latency_ms)}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
