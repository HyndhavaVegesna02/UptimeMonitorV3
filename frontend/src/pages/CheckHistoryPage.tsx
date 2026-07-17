import { useMemo, useState } from 'react'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Panel,
  StatusBadge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '../components'
import { cx } from '../lib/cx'
import { observationHealth } from '../features/history/observationHealth'
import { useAllHistory } from '../features/history/useAllHistory'
import {
  ALL_LOCATIONS,
  ALL_RESULTS,
  DEFAULT_HISTORY_FILTERS,
  filterHistoryRows,
  uniqueLocations,
} from '../features/history/filterHistory'
import type { HistoryFilters } from '../features/history/filterHistory'
import type { AvailabilityRange, WindowPreset } from '../features/availability/windowRange'
import { windowToRange } from '../features/availability/windowRange'
import './CheckHistoryPage.css'

const WINDOW_PRESETS: Array<{ value: WindowPreset; label: string }> = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
]

/** The result-filter `<select>` options (STORY-060 AC1) — a fixed list
 * matching the `ObservationDTO.health` wire vocabulary pinned at planning
 * (`"up" | "down" | "degraded"`, sprint-38 plan §"Verified API contracts"),
 * not derived from the loaded data — so the option is present and usable
 * even before/while a matching observation has loaded. */
const RESULT_OPTIONS: Array<{ value: string; label: string }> = [
  { value: ALL_RESULTS, label: 'All results' },
  { value: 'up', label: 'Up' },
  { value: 'degraded', label: 'Degraded' },
  { value: 'down', label: 'Down' },
]

/** The default (production) value for the most rows the tab will ever
 * RENDER (STORY-060 AC3, restoring the pre-060 STORY-015e cap of 1,000 per
 * the "preserve all existing functionality" rule) — the `/history` endpoint
 * has no client-driven pagination (the server does accept an optional
 * `limit` query param as of STORY-094, but `client.ts::getHistory`
 * deliberately never sends it), so a wide window can return many thousands
 * of rows across every signal; this is a client-side render cap, not a
 * request limit. It is passed as the `maxRenderedRows` prop's default rather than
 * hard-coded so tests can inject a small cap (STORY-054's flake was the cap
 * TEST rendering ~1,000-1,500 rows, slow enough under `npm test`
 * file-parallelism/CPU contention to occasionally exceed Vitest's 5s
 * per-test timeout) — production always renders via the default, unchanged
 * from pre-060 behavior. */
const DEFAULT_MAX_RENDERED_ROWS = 1000

/** `latency_ms` renders as integer milliseconds; `null` (no measurement)
 * renders as an em-dash — NEVER `0 ms`, which would misreport "no reading"
 * as "instant" (kept as this page's own copy per the sprint-38 Wave-2
 * file-scope isolation rule — see `DashboardPage.tsx::formatLatency`). */
function formatLatency(latencyMs: number | null): string {
  return latencyMs === null ? '—' : `${latencyMs} ms`
}

/** `response_status_code` (STORY-064) renders as its raw integer; `null`
 * (missing/unparsable at the source, or a pre-migration row) renders as an
 * em-dash — the same convention as `formatLatency` above. */
function formatResponseStatusCode(code: number | null): string {
  return code === null ? '—' : `${code}`
}

/**
 * The Check History tab (STORY-060, rebuilding STORY-015e): a dense,
 * system-wide, chronological observation ledger — the ingest ledger view
 * (dossier §17). `useAllHistory` (AC1, AC2) merges EVERY topology signal's
 * `GET /api/v1/history` for the selected 24h/7d/30d window
 * (`windowToRange`, reused from Availability — the parallel-shape
 * agreement) into one newest-first list; the search input plus the result
 * and location `<select>`s (AC1) then narrow that already-loaded list
 * client-side — none of the three filters trigger a refetch, only the
 * window toggle does. The h1 + subtitle render via the shared `PageHeader`
 * (STORY-097 AC1), outside the `Panel` card, in the shared full-width
 * `page--wide` container (a dense table page, per AC2).
 */
export function CheckHistoryPage({
  maxRenderedRows = DEFAULT_MAX_RENDERED_ROWS,
}: { maxRenderedRows?: number } = {}) {
  const [preset, setPreset] = useState<WindowPreset>('24h')
  // Memoized per preset (not per render) so `useAllHistory`'s fetcher keeps
  // a STABLE identity while the window selection is unchanged (015d
  // pattern).
  const range: AvailabilityRange = useMemo(() => windowToRange(preset), [preset])
  const { state, retry } = useAllHistory(range)

  const [filters, setFilters] = useState<HistoryFilters>(DEFAULT_HISTORY_FILTERS)

  const rows = useMemo(() => (state.phase === 'success' ? state.data : []), [state])
  const locationOptions = useMemo(() => uniqueLocations(rows), [rows])
  const filtered = useMemo(() => filterHistoryRows(rows, filters), [rows, filters])

  const rendered = filtered.slice(0, maxRenderedRows)
  const truncated = filtered.length > maxRenderedRows

  return (
    <div className="check-history-page page page--wide">
      <PageHeader
        title="Check History"
        subtitle="A chronological ledger of every monitored signal's observations across the selected time window."
      />

      <Panel>
        <div className="check-history-page__toolbar">
          <div className="check-history-page__search">
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

          <div className="check-history-page__filter">
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

          <div className="check-history-page__filter">
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
                  {location}
                </option>
              ))}
            </select>
          </div>

          <div className="check-history-page__window" role="group" aria-label="Time window">
            {WINDOW_PRESETS.map((option) => (
              <button
                key={option.value}
                type="button"
                className={cx(
                  'check-history-page__window-button',
                  preset === option.value && 'check-history-page__window-button--active',
                )}
                aria-pressed={preset === option.value}
                onClick={() => setPreset(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {state.phase === 'loading' && <LoadingState label="Loading observations…" />}

        {state.phase === 'error' && (
          <ErrorState message="Could not load check history" onRetry={retry} />
        )}

        {state.phase === 'success' && rows.length === 0 && (
          <EmptyState message="No observations in this window" />
        )}

        {state.phase === 'success' && rows.length > 0 && filtered.length === 0 && (
          <EmptyState
            icon="search"
            message="No observations match your filters"
            detail="Try widening the time window or clearing a filter."
          />
        )}

        {state.phase === 'success' && filtered.length > 0 && (
          <>
            {truncated ? (
              <p className="check-history-page__cap-note text-caption">
                showing latest {maxRenderedRows.toLocaleString()} of{' '}
                {filtered.length.toLocaleString()} observations
              </p>
            ) : null}
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Timestamp</TableHeaderCell>
                  <TableHeaderCell>Type</TableHeaderCell>
                  <TableHeaderCell>Component</TableHeaderCell>
                  <TableHeaderCell>Location</TableHeaderCell>
                  <TableHeaderCell>Result</TableHeaderCell>
                  <TableHeaderCell>Code</TableHeaderCell>
                  <TableHeaderCell>Latency</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rendered.map((row, index) => (
                  <TableRow key={`${row.signal_key}-${row.observed_at}-${index}`}>
                    <TableCell className="text-mono">{row.observed_at}</TableCell>
                    <TableCell className="text-mono">{row.check_type.toUpperCase()}</TableCell>
                    <TableCell>{row.componentName}</TableCell>
                    <TableCell className="text-mono">{row.location}</TableCell>
                    <TableCell>
                      <StatusBadge status={observationHealth(row.health)} />
                    </TableCell>
                    <TableCell className="text-mono">
                      {formatResponseStatusCode(row.response_status_code)}
                    </TableCell>
                    <TableCell className="text-mono">{formatLatency(row.latency_ms)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
      </Panel>
    </div>
  )
}
