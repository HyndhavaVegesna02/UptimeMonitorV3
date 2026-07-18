import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import {
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_HISTORY_FRONTEND_TLS,
  FIXTURE_TOPOLOGY,
} from '../mocks/handlers'
import CHECK_HISTORY_CSS from './CheckHistoryPage.css?raw'
import { CheckHistoryPage } from './CheckHistoryPage'

function renderPage(initialPath = '/check-history') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <CheckHistoryPage />
    </MemoryRouter>,
  )
}

describe('CheckHistoryPage — layout (STORY-108 AC1)', () => {
  it('renders exactly one h1 titled Check History', async () => {
    renderPage()
    await screen.findByRole('table')
    expect(screen.getByRole('heading', { name: 'Check History', level: 1 })).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
  })

  it('renders the search input, result select, location select, and window switcher', async () => {
    renderPage()
    await screen.findByRole('table')

    expect(screen.getByRole('searchbox', { name: 'Search' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Result' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Location' })).toBeInTheDocument()
    const group = screen.getByRole('group', { name: 'Time window' })
    expect(within(group).getByRole('button', { name: '24h' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('populates the location select from the currently loaded rows, using the short label', async () => {
    renderPage()
    await screen.findByRole('table')

    const select = screen.getByRole('combobox', { name: 'Location' })
    // FIXTURE_HISTORY_FRONTEND_HTTP has 3 distinct locations + FRONTEND_TLS's 1.
    expect(within(select).getAllByText(/^Location …/).length).toBeGreaterThan(0)
    expect(within(select).getByText('All locations')).toBeInTheDocument()
  })
})

describe('CheckHistoryPage — ?signal= URL seed (STORY-108 AC1, STORY-107 deep link)', () => {
  it('seeds the search box from ?signal= on first render', async () => {
    renderPage('/check-history?signal=frontend-tls')
    await screen.findByRole('table')

    expect(screen.getByRole('searchbox', { name: 'Search' })).toHaveValue('frontend-tls')
    // Narrowed to only the frontend-tls rows.
    expect(screen.getAllByRole('row')).toHaveLength(FIXTURE_HISTORY_FRONTEND_TLS.length + 1)
  })

  it('is editable after the seed — typing over it is never re-synced back to the URL value', async () => {
    const user = userEvent.setup()
    renderPage('/check-history?signal=frontend-tls')
    await screen.findByRole('table')

    const search = screen.getByRole('searchbox', { name: 'Search' })
    await user.clear(search)
    await user.type(search, 'catalogue')

    expect(search).toHaveValue('catalogue')
  })

  it('renders every row unfiltered when no ?signal= param is present', async () => {
    renderPage('/check-history')
    await screen.findByRole('table')

    expect(screen.getByRole('searchbox', { name: 'Search' })).toHaveValue('')
    expect(screen.getAllByRole('row')).toHaveLength(
      FIXTURE_HISTORY_FRONTEND_HTTP.length + FIXTURE_HISTORY_FRONTEND_TLS.length + 1,
    )
  })
})

describe('CheckHistoryPage — filtering (STORY-108 AC1)', () => {
  it('narrows rows via the free-text search box', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('table')

    await user.type(screen.getByRole('searchbox', { name: 'Search' }), 'frontend-tls')

    expect(screen.getAllByRole('row')).toHaveLength(FIXTURE_HISTORY_FRONTEND_TLS.length + 1)
  })

  it('narrows rows via the result select', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('table')

    await user.selectOptions(screen.getByRole('combobox', { name: 'Result' }), 'degraded')

    const rows = screen.getAllByRole('row').slice(1)
    expect(rows).toHaveLength(1)
    expect(within(rows[0]).getByText('Degraded')).toBeInTheDocument()
  })

  it('narrows rows via the location select', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('table')

    const select = screen.getByRole('combobox', { name: 'Location' })
    await user.selectOptions(select, FIXTURE_HISTORY_FRONTEND_HTTP[0].location)

    const rows = screen.getAllByRole('row').slice(1)
    rows.forEach((row) => {
      expect(within(row).getByTitle(FIXTURE_HISTORY_FRONTEND_HTTP[0].location)).toBeInTheDocument()
    })
  })

  it('refetches with the new window when the preset changes', async () => {
    const user = userEvent.setup()
    const seenRanges: string[] = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        seenRanges.push(url.searchParams.get('since') ?? '')
        return HttpResponse.json([])
      }),
      http.get('/api/v1/topology', () => HttpResponse.json(FIXTURE_TOPOLOGY)),
    )
    renderPage()
    await screen.findByText('No observations in this window')
    const firstCount = seenRanges.length

    await user.click(screen.getByRole('button', { name: '7d' }))

    await waitFor(() => expect(seenRanges.length).toBeGreaterThan(firstCount))
  })
})

describe('CheckHistoryPage — dense table anatomy (STORY-108 AC2)', () => {
  it('renders the column headers, with no separate redundant Type column', async () => {
    renderPage()
    await screen.findByRole('table')

    expect(
      screen.getByRole('columnheader', { name: 'Timestamp' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Component' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Location' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Result' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Code' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Latency' })).toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: 'Type' })).not.toBeInTheDocument()
  })

  it('renders the signal/check type as secondary text under the component name, not a separate column', async () => {
    renderPage()
    await screen.findByRole('table')

    const rows = screen.getAllByRole('row').slice(1)
    const firstRow = rows[0]
    expect(within(firstRow).getByText(FIXTURE_TOPOLOGY[0].name)).toBeInTheDocument()
    expect(within(firstRow).getByText('HTTP')).toBeInTheDocument()
  })

  it('renders the timestamp as RelativeTime — a <time> element, never a raw ISO string as visible text', async () => {
    renderPage()
    await screen.findByRole('table')

    const rows = screen.getAllByRole('row').slice(1)
    const timeEl = rows[0].querySelector('time') as HTMLElement
    expect(timeEl).toBeInTheDocument()
    expect(timeEl).toHaveAttribute('dateTime', FIXTURE_HISTORY_FRONTEND_HTTP[0].observed_at)
    expect(screen.queryByText(FIXTURE_HISTORY_FRONTEND_HTTP[0].observed_at)).not.toBeInTheDocument()
  })

  it('renders the location as a short label with the raw vendor id as a tooltip, never the raw id as visible text', async () => {
    renderPage()
    await screen.findByRole('table')

    const rows = screen.getAllByRole('row').slice(1)
    const cell = within(rows[0]).getByTitle(FIXTURE_HISTORY_FRONTEND_HTTP[0].location)
    expect(cell).toHaveTextContent(/^Location …/)
    expect(screen.queryByText(FIXTURE_HISTORY_FRONTEND_HTTP[0].location)).not.toBeInTheDocument()
  })

  it('renders the Result column as a StatusBadge, never color-only', async () => {
    renderPage()
    await screen.findByRole('table')

    const rows = screen.getAllByRole('row').slice(1)
    expect(within(rows[0]).getByText('Up')).toBeInTheDocument()
  })

  it('renders the Code column, an em-dash for a missing response_status_code', async () => {
    renderPage()
    await screen.findByRole('table')

    const rows = screen.getAllByRole('row').slice(1)
    expect(within(rows[0]).getByText('200')).toBeInTheDocument()
    // Row index 2 (down, latency null, response_status_code null) — both
    // the Code and Latency cells render an em-dash.
    expect(within(rows[2]).getAllByText('—')).toHaveLength(2)
  })

  it('tints the Latency column via the named threshold tokens, an em-dash for a null reading', async () => {
    renderPage()
    await screen.findByRole('table')

    const rows = screen.getAllByRole('row').slice(1)
    // FIXTURE_HISTORY_FRONTEND_HTTP[0]: latency_ms 571 -> warn band.
    expect(screen.getByText('571 ms')).toHaveClass('check-history-page__latency--warn')
    // FIXTURE_HISTORY_FRONTEND_HTTP[1]: latency_ms 2140 -> high band.
    expect(screen.getByText('2140 ms')).toHaveClass('check-history-page__latency--high')
    // FIXTURE_HISTORY_FRONTEND_HTTP[2]: latency_ms null -> em-dash, no tint class.
    const nullLatencyRow = rows[2]
    const nullLatencyCell = within(nullLatencyRow).getAllByText('—')[1]
    expect(nullLatencyCell.className).not.toMatch(/check-history-page__latency--/)
  })

  it('sticky-heads the table within its OWN scroll container (never the page)', () => {
    expect(CHECK_HISTORY_CSS).toMatch(/\.check-history-page__table-wrapper\s*\{[^}]*overflow:\s*auto/)
    expect(CHECK_HISTORY_CSS).toMatch(
      /\.check-history-page__table-wrapper \.table__header-cell\s*\{[^}]*position:\s*sticky/,
    )
  })
})

describe('CheckHistoryPage — results summary line (STORY-108 AC2)', () => {
  it('renders "N checks · M down" in an aria-live=polite region', async () => {
    renderPage()
    await screen.findByRole('table')

    const total = FIXTURE_HISTORY_FRONTEND_HTTP.length + FIXTURE_HISTORY_FRONTEND_TLS.length
    const downCount = FIXTURE_HISTORY_FRONTEND_HTTP.filter((row) => row.health === 'down').length
    const summary = screen.getByText(`${total} checks · ${downCount} down`)
    expect(summary).toHaveAttribute('aria-live', 'polite')
  })

  it('echoes the active filter in the summary line', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('table')

    await user.selectOptions(screen.getByRole('combobox', { name: 'Result' }), 'down')

    expect(screen.getByText(/1 check · 1 down — filtered by result: down/)).toBeInTheDocument()
  })
})

describe('CheckHistoryPage — empty states (STORY-108 AC3)', () => {
  it('renders the designed unfiltered-window-empty state when the window genuinely has no data', async () => {
    server.use(
      http.get('/api/v1/history', () => HttpResponse.json([])),
      http.get('/api/v1/topology', () => HttpResponse.json(FIXTURE_TOPOLOGY)),
    )
    renderPage()

    expect(await screen.findByText('No observations in this window')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('renders the designed filtered-to-zero empty state (distinct copy + recovery detail)', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByRole('table')

    await user.type(screen.getByRole('searchbox', { name: 'Search' }), 'no-such-signal-anywhere')

    expect(await screen.findByText('No observations match your filters')).toBeInTheDocument()
    expect(
      screen.getByText('Try widening the time window or clearing a filter.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows a loading state, then an error state with retry on a fetch failure', async () => {
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
    renderPage()

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load check history')

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await screen.findByRole('table')
    expect(callCount).toBe(2)
  })
})
