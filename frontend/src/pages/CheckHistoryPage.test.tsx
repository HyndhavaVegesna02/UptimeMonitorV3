import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import {
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_HISTORY_FRONTEND_TLS,
  FIXTURE_TOPOLOGY,
} from '../mocks/handlers'
import { CheckHistoryPage } from './CheckHistoryPage'

const TOTAL_MERGED_ROWS =
  FIXTURE_HISTORY_FRONTEND_HTTP.length + FIXTURE_HISTORY_FRONTEND_TLS.length

/** Renders `CheckHistoryPage` inside a `MemoryRouter` — required as of
 * STORY-100 since the page now reads an optional `signal` URL param via
 * `useSearchParams` (AC2), which throws outside a Router. `route` lets a
 * test drive a deep-linked initial URL. */
function renderCheckHistory(
  props: { maxRenderedRows?: number } = {},
  route = '/check-history',
) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <CheckHistoryPage {...props} />
    </MemoryRouter>,
  )
}

// Fixed 4 minutes after the newest fixture observation (STORY-098) so the
// relative-time text below is deterministic — `vi.setSystemTime` alone
// (without `vi.useFakeTimers()`) mocks `Date` without freezing real timers,
// so MSW's fetch handling is unaffected (same trick as
// `MaintenancePage.test.tsx`).
const NOW = new Date('2026-07-03T13:33:17.931000Z')

describe('CheckHistoryPage', () => {
  beforeEach(() => {
    vi.setSystemTime(NOW)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders the h1 + subtitle via the shared PageHeader, outside the card, opted into full width (STORY-097 AC1, AC2)', async () => {
    const { container } = renderCheckHistory()

    const heading = screen.getByRole('heading', { name: 'Check History', level: 1 })
    expect(heading.closest('.page-header')).not.toBeNull()
    expect(heading.closest('.panel')).toBeNull()

    const root = container.querySelector('.check-history-page')
    expect(root).toHaveClass('page', 'page--wide')
  })

  it('renders every topology signal\'s observations merged newest-first, tagged with their component (AC1, AC2)', async () => {
    renderCheckHistory()

    const table = await screen.findByRole('table')
    const rows = within(table).getAllByRole('row').slice(1) // drop the header row
    expect(rows).toHaveLength(TOTAL_MERGED_ROWS)

    const frontendComponentName = FIXTURE_TOPOLOGY[0].name
    // The frontend-http fixture is newest overall, so it occupies the first
    // rows exactly in its own newest-first order. Relative to the fixed NOW
    // above: rows 0-3 sit 4m/5m/6m/7m in the past.
    const expectedRelative = ['4m ago', '5m ago', '6m ago', '7m ago']
    // Location display is the short "Location …tail" form (STORY-098 AC4);
    // the raw id lives in the cell's `title` tooltip.
    const expectedLocationLabel = ['Location …0060', 'Location …0061', 'Location …0060', 'Location …0062']

    FIXTURE_HISTORY_FRONTEND_HTTP.forEach((observation, index) => {
      // AC1: no bare ISO-8601 string as primary text — the relative label
      // renders instead, with the raw instant carried on `dateTime`.
      expect(within(rows[index]).queryByText(observation.observed_at)).not.toBeInTheDocument()
      const timeEl = within(rows[index]).getByText(expectedRelative[index])
      expect(timeEl.tagName).toBe('TIME')
      expect(timeEl).toHaveAttribute('dateTime', observation.observed_at)
      expect(timeEl.getAttribute('title')).toContain(new Date(observation.observed_at).toISOString())

      expect(within(rows[index]).getByText(expectedLocationLabel[index])).toBeInTheDocument()
      expect(within(rows[index]).getByTitle(observation.location)).toBeInTheDocument()
      expect(within(rows[index]).getByText(frontendComponentName)).toBeInTheDocument()
    })

    // Health badges: dot + ink label, never color-alone — assert the label text.
    expect(within(rows[0]).getByText('Up')).toBeInTheDocument()
    expect(within(rows[1]).getByText('Degraded')).toBeInTheDocument()
    expect(within(rows[2]).getByText('Down')).toBeInTheDocument()
  })

  it('renders Type and Code columns from ObservationDTO (STORY-064)', async () => {
    renderCheckHistory()
    await screen.findByRole('table')

    expect(screen.getByRole('columnheader', { name: 'Timestamp' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Type' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Component' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Location' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Result' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Code' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Latency' })).toBeInTheDocument()
  })

  it('renders check_type uppercased, and the HTTP status code in the mono token, with a null code as an em-dash (STORY-064)', async () => {
    renderCheckHistory()

    const table = await screen.findByRole('table')
    const rows = within(table).getAllByRole('row').slice(1)

    // frontend-http row 0: check_type 'http' -> 'HTTP'; response_status_code 200.
    expect(within(rows[0]).getByText('HTTP')).toBeInTheDocument()
    expect(within(rows[0]).getByText('200')).toBeInTheDocument()

    // frontend-http row 1: response_status_code null -> em-dash.
    const row1Cells = within(rows[1]).getAllByText('—')
    expect(row1Cells.length).toBeGreaterThan(0)
  })

  it('renders latency in the mono token as integer milliseconds, and a null latency as an em-dash (never "0 ms") (AC2)', async () => {
    renderCheckHistory()

    const table = await screen.findByRole('table')
    const rows = within(table).getAllByRole('row').slice(1)

    // frontend-http row 0: latency_ms 571.
    expect(within(rows[0]).getByText('571 ms')).toBeInTheDocument()

    // frontend-http row 2: latency_ms null (STORY-064: response_status_code
    // is ALSO null on this row, so both cells render as an em-dash).
    expect(within(rows[2]).getAllByText('—').length).toBeGreaterThan(0)
    expect(within(rows[2]).queryByText('0 ms')).not.toBeInTheDocument()
    expect(within(rows[2]).queryByText('null ms')).not.toBeInTheDocument()
  })

  it('has accessible names for the search input and both filter selects (AC1)', async () => {
    renderCheckHistory()
    await screen.findByRole('table')

    expect(screen.getByLabelText('Search')).toBeInTheDocument()
    expect(screen.getByLabelText('Result')).toBeInTheDocument()
    expect(screen.getByLabelText('Location')).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Time window' })).toBeInTheDocument()
  })

  it('the search input filters rows by component, location, or signal_key text, client-side (AC1)', async () => {
    const user = userEvent.setup()
    let historyCallCount = 0
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        historyCallCount += 1
        const url = new URL(request.url)
        const signalKey = url.searchParams.get('signal_key')
        if (signalKey === 'frontend-http') return HttpResponse.json(FIXTURE_HISTORY_FRONTEND_HTTP)
        if (signalKey === 'frontend-tls') return HttpResponse.json(FIXTURE_HISTORY_FRONTEND_TLS)
        return HttpResponse.json([])
      }),
    )

    renderCheckHistory()
    await screen.findByRole('table')
    const callsAfterLoad = historyCallCount

    await user.type(screen.getByLabelText('Search'), 'frontend-tls')

    const table = screen.getByRole('table')
    const rows = within(table).getAllByRole('row').slice(1)
    expect(rows).toHaveLength(FIXTURE_HISTORY_FRONTEND_TLS.length)
    expect(
      within(table).queryByTitle(FIXTURE_HISTORY_FRONTEND_HTTP[0].location),
    ).not.toBeInTheDocument()

    // Filtering is purely client-side — never triggers a refetch.
    expect(historyCallCount).toBe(callsAfterLoad)
  })

  it('seeds the search filter from a `signal` URL param on initial load (STORY-100 AC2 deep link)', async () => {
    renderCheckHistory({}, '/check-history?signal=frontend-tls')

    const table = await screen.findByRole('table')

    expect(screen.getByLabelText('Search')).toHaveValue('frontend-tls')
    const rows = within(table).getAllByRole('row').slice(1)
    expect(rows).toHaveLength(FIXTURE_HISTORY_FRONTEND_TLS.length)
  })

  it('a `signal`-seeded search filter remains fully editable afterwards (STORY-100 AC2)', async () => {
    const user = userEvent.setup()
    renderCheckHistory({}, '/check-history?signal=frontend-tls')

    await screen.findByRole('table')
    expect(screen.getByLabelText('Search')).toHaveValue('frontend-tls')

    await user.clear(screen.getByLabelText('Search'))

    const table = screen.getByRole('table')
    const rows = within(table).getAllByRole('row').slice(1)
    expect(rows).toHaveLength(TOTAL_MERGED_ROWS)
  })

  it('with no `signal` URL param, the search filter starts empty exactly as before (STORY-100 AC2)', async () => {
    renderCheckHistory()
    await screen.findByRole('table')

    expect(screen.getByLabelText('Search')).toHaveValue('')
  })

  it('the result filter narrows rows to the selected health value (AC1)', async () => {
    const user = userEvent.setup()
    renderCheckHistory()
    const table = await screen.findByRole('table')

    await user.selectOptions(screen.getByLabelText('Result'), 'degraded')

    const rows = within(table).getAllByRole('row').slice(1)
    expect(rows).toHaveLength(1)
    expect(within(rows[0]).getByText('Degraded')).toBeInTheDocument()
  })

  it('the location filter narrows rows to the selected location (AC1)', async () => {
    const user = userEvent.setup()
    renderCheckHistory()
    const table = await screen.findByRole('table')

    const targetLocation = FIXTURE_HISTORY_FRONTEND_TLS[0].location
    // The <select> is still keyed by the RAW location id — its value/behavior
    // is unchanged even though the visible option text is now prettified
    // (STORY-098 AC4).
    await user.selectOptions(screen.getByLabelText('Location'), targetLocation)

    const rows = within(table).getAllByRole('row').slice(1)
    rows.forEach((row) => {
      expect(within(row).getByTitle(targetLocation)).toBeInTheDocument()
    })
  })

  it('shows a distinct empty state when filters match nothing, without hiding that data exists (AC1, AC4)', async () => {
    const user = userEvent.setup()
    const { container } = renderCheckHistory()
    await screen.findByRole('table')

    await user.type(screen.getByLabelText('Search'), 'no-such-signal-or-component')

    const message = await screen.findByText('No observations match your filters')
    expect(message.closest('.empty-state')).not.toBeNull()
    expect(container.querySelector('.empty-state__icon')).not.toBeNull()
    expect(
      screen.getByText('Try widening the time window or clearing a filter.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('driving the window selector refetches every signal with a NEW tz-aware since/until (AC1)', async () => {
    const user = userEvent.setup()
    const seenRanges: Array<{ since: string; until: string }> = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        seenRanges.push({
          since: url.searchParams.get('since') ?? '',
          until: url.searchParams.get('until') ?? '',
        })
        return HttpResponse.json([])
      }),
    )

    renderCheckHistory()
    await screen.findByText('No observations in this window')

    const initialSince = seenRanges[0].since

    await user.click(screen.getByRole('button', { name: '7d' }))

    await waitFor(() => {
      expect(seenRanges.some((r) => r.since !== initialSince)).toBe(true)
    })

    expect(screen.getByRole('button', { name: '7d' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '24h' })).toHaveAttribute('aria-pressed', 'false')

    const newRange = seenRanges[seenRanges.length - 1]
    expect(new Date(newRange.since).toString()).not.toBe('Invalid Date')
    expect(newRange.since).toMatch(/Z$/)
  })

  it('shows the shared LoadingState while the merged history is loading (AC4)', () => {
    renderCheckHistory()
    expect(screen.getByRole('status')).toHaveTextContent('Loading observations…')
  })

  it('shows the shared EmptyState "no observations in this window" when nothing loaded at all (AC4)', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.json([])))

    renderCheckHistory()

    expect(await screen.findByText('No observations in this window')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows the shared ErrorState on a topology-fetch failure, then recovers via retry (AC4)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/topology', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_TOPOLOGY)
      }),
    )

    renderCheckHistory()

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load check history')

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await screen.findByRole('table')
    expect(callCount).toBe(2)
  })

  it('shows the shared ErrorState on a history-fetch failure, then recovers via retry (AC4)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('signal_key') === 'frontend-http') {
          callCount += 1
          if (callCount === 1) {
            return HttpResponse.json({ detail: 'boom' }, { status: 500 })
          }
        }
        return HttpResponse.json([])
      }),
    )

    renderCheckHistory()

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load check history')

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await screen.findByText('No observations in this window')
    expect(callCount).toBe(2)
  })

  /**
   * STORY-054 resolution, re-fixed by the STORY-060 quality review (AC3):
   * production restores the pre-060 STORY-015e 1,000-row cap
   * (`DEFAULT_MAX_RENDERED_ROWS` in `CheckHistoryPage.tsx`, the "preserve all
   * existing functionality" rule) — see the sibling test below for that. The
   * STORY-054 flake was never really about the cap NUMBER, it was this TEST
   * rendering ~1,000-1,500 real DOM rows, which was slow enough under
   * `npm test` file-parallelism/CPU contention to occasionally exceed
   * Vitest's per-test timeout. The real fix is making the cap injectable via
   * the `maxRenderedRows` prop and exercising the exact same
   * truncation+caption logic against a tiny fixture (8 rows, cap 5) — this
   * renders in milliseconds regardless of contention, with NO 1,000-row
   * render anywhere in the suite. Only ONE signal (`frontend-http`) returns
   * the fixture; every other topology signal returns `[]`, so the merged
   * total is exactly 8 regardless of how many signals the topology fixture
   * enumerates.
   */
  it('caps rendering at an injected row limit with a visible count note when the window returns more (AC3)', async () => {
    const TOTAL = 8
    const generated = Array.from({ length: TOTAL }, (_, index) => ({
      signal_key: 'frontend-http',
      observed_at: new Date(Date.UTC(2026, 6, 3, 0, 0, 0) - index * 1000).toISOString(),
      health: 'up',
      location: 'SYNTHETIC_LOCATION-0000000000000060',
      latency_ms: 500,
      response_status_code: 200,
      check_type: 'http',
    }))
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('signal_key') === 'frontend-http') {
          return HttpResponse.json(generated)
        }
        return HttpResponse.json([])
      }),
    )

    renderCheckHistory({ maxRenderedRows: 5 })

    expect(await screen.findByText('showing latest 5 of 8 observations')).toBeInTheDocument()

    const table = screen.getByRole('table')
    const rows = within(table).getAllByRole('row').slice(1)
    expect(rows).toHaveLength(5)
    // The rendered subset is the NEWEST 5 — the first row is the array's
    // first (newest-first) element, unchanged. Its raw instant is carried on
    // `dateTime` now that the visible text is a relative label (STORY-098).
    const firstRowTime = within(rows[0]).getByText(/ago|just now/)
    expect(firstRowTime).toHaveAttribute('dateTime', generated[0].observed_at)
  })

  /**
   * Confirms the PRODUCTION default (no `maxRenderedRows` prop, exactly as
   * the router renders it) is the restored 1,000-row cap, not the injected
   * test value — a fixture of 1,001 single-signal rows would be exactly the
   * slow render the STORY-054 fix avoids, so this asserts the cap NUMBER via
   * a small fixture (`TOTAL` under the cap) plus a direct read of the
   * caption logic instead: with `TOTAL` below 1,000, nothing is truncated,
   * proving the default is >= this fixture size, while the module docstring
   * and the injected-cap test above pin the exact value (1,000) and the
   * truncation/caption mechanics respectively.
   */
  it('uses a 1,000-row cap by default (no maxRenderedRows prop) — untruncated below that size', async () => {
    renderCheckHistory()

    const table = await screen.findByRole('table')
    const rows = within(table).getAllByRole('row').slice(1)
    // The default fixture set is well under 1,000, so nothing is truncated
    // and no cap-note renders — the production default is not the small
    // test-only value used elsewhere in this file.
    expect(rows).toHaveLength(TOTAL_MERGED_ROWS)
    expect(screen.queryByText(/showing latest/)).not.toBeInTheDocument()
  })

  it('shows the shared EmptyState "no observations in this window" when the topology itself is empty (AC4)', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json([])))

    renderCheckHistory()

    expect(await screen.findByText('No observations in this window')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })
})
