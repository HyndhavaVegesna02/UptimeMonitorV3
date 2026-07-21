import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http, delay } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { ComponentTopologyDTO, ObservationDTO } from '../../api/types'
import { FIXTURE_HISTORY } from '../../mocks/handlers/history'
import { server } from '../../mocks/server'
import { AppRoutes } from '../../routes'
import { HistoryPage } from './HistoryPage'

/** A second synthetic signal (STORY-130 AC1 multi-signal-merge), same
 * shape/scale as the real captured `http-check` sample — reused location
 * ids, plausible latencies, `check_type: 'ping'` — just a distinct
 * signal_key/timestamps so the global re-sort is provable end to end. */
const PING_CHECK_HISTORY: ObservationDTO[] = [
  {
    signal_key: 'ping-check',
    observed_at: '2026-07-21T07:57:41.000000Z',
    health: 'down',
    location: 'SYNTHETIC_LOCATION-0000000000000047',
    latency_ms: null,
    response_status_code: null,
    check_type: 'ping',
  },
  {
    signal_key: 'ping-check',
    observed_at: '2026-07-21T07:53:00.000000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: 12,
    response_status_code: 200,
    check_type: 'ping',
  },
]

const TWO_SIGNAL_TOPOLOGY: ComponentTopologyDTO[] = [
  {
    id: 'http-check',
    name: 'HTTP Check',
    signals: [{ signal_key: 'http-check', name: 'HTTP Check', interval_seconds: 120, component_id: 'http-check' }],
  },
  {
    id: 'ping-check',
    name: 'Ping Check',
    signals: [{ signal_key: 'ping-check', name: 'Ping Check', interval_seconds: 60, component_id: 'ping-check' }],
  },
]

function useTwoSignals() {
  server.use(
    http.get('/api/v1/topology', () => HttpResponse.json(TWO_SIGNAL_TOPOLOGY)),
    http.get('/api/v1/history', ({ request }) => {
      const signalKey = new URL(request.url).searchParams.get('signal_key') ?? ''
      if (signalKey === 'ping-check') {
        return HttpResponse.json(PING_CHECK_HISTORY)
      }
      return HttpResponse.json(FIXTURE_HISTORY[signalKey] ?? [])
    }),
  )
}

function renderPage(props: Partial<Parameters<typeof HistoryPage>[0]> = {}) {
  return render(
    <MemoryRouter initialEntries={['/history']}>
      <HistoryPage {...props} />
    </MemoryRouter>,
  )
}

describe('HistoryPage', () => {
  it('paints the toolbar (window toggle) immediately, before topology/history resolve', () => {
    server.use(http.get('/api/v1/topology', async () => { await delay(50); return HttpResponse.json([]) }))
    renderPage()
    expect(screen.getByRole('group', { name: 'Window' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '24h' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('AC1: merges every signal into one grid, re-sorted globally by observed_at desc (not concatenated)', async () => {
    useTwoSignals()
    renderPage()

    const table = await screen.findByRole('table')
    const rows = within(table).getAllByRole('row').slice(1) // drop header
    // http-check (real captured sample): 07:58:41.133, 07:57:41.375, 07:56:41.164 x2, …
    // ping-check (synthetic): 07:57:41.000, 07:53:00.000.
    // Correct global order interleaves the two signals — ping's 07:57:41
    // slots between http's 07:57:41.375 and 07:56:41.164, proving this is
    // a real re-sort, not a per-signal concatenation.
    expect(within(rows[0]).getByText('Jul 21, 07:58:41')).toBeInTheDocument()
    expect(within(rows[0]).getByText('HTTP Check')).toBeInTheDocument()
    expect(within(rows[1]).getByText('Jul 21, 07:57:41')).toBeInTheDocument()
    expect(within(rows[1]).getByText('HTTP Check')).toBeInTheDocument()
    expect(within(rows[2]).getByText('Jul 21, 07:57:41')).toBeInTheDocument()
    expect(within(rows[2]).getByText('Ping Check')).toBeInTheDocument()
    expect(within(rows[3]).getByText('HTTP Check')).toBeInTheDocument()
  })

  it('AC2: the text search narrows the grid client-side (no extra network calls)', async () => {
    useTwoSignals()
    const user = userEvent.setup()
    renderPage()

    await screen.findByRole('table')
    await user.type(screen.getByRole('textbox', { name: /search/i }), 'ping')

    const table = screen.getByRole('table')
    const rows = within(table).getAllByRole('row').slice(1)
    expect(rows).toHaveLength(2)
    expect(rows.every((row) => within(row).getByText('Ping Check'))).toBeTruthy()
  })

  it('AC2: the Result filter narrows to the fixed wire vocabulary', async () => {
    useTwoSignals()
    const user = userEvent.setup()
    renderPage()

    await screen.findByRole('table')
    await user.selectOptions(screen.getByRole('combobox', { name: /result/i }), 'down')

    const rows = within(screen.getByRole('table')).getAllByRole('row').slice(1)
    expect(rows).toHaveLength(1)
    expect(within(rows[0]).getByText('Down')).toBeInTheDocument()
  })

  it('AC2: the Location filter (derived from loaded rows) narrows the grid', async () => {
    useTwoSignals()
    const user = userEvent.setup()
    renderPage()

    await screen.findByRole('table')
    await user.selectOptions(screen.getByRole('combobox', { name: /location/i }), 'SYNTHETIC_LOCATION-0000000000000060')

    const rows = within(screen.getByRole('table')).getAllByRole('row').slice(1)
    expect(rows.length).toBeGreaterThan(0)
    expect(rows.every((row) => within(row).getByText('…0060'))).toBeTruthy()
  })

  it('AC2: the window toggle recomputes since/until as tz-aware UTC ISO and refetches', async () => {
    useTwoSignals()
    const seenUrls: string[] = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        seenUrls.push(request.url)
        return HttpResponse.json(FIXTURE_HISTORY['http-check'])
      }),
    )
    const user = userEvent.setup()
    renderPage()

    await screen.findByRole('table')
    const initialCount = seenUrls.length
    expect(initialCount).toBeGreaterThan(0)

    await user.click(screen.getByRole('button', { name: '7d' }))
    await screen.findByRole('table')

    expect(seenUrls.length).toBeGreaterThan(initialCount)
    const lastUrl = new URL(seenUrls[seenUrls.length - 1])
    const since = lastUrl.searchParams.get('since')!
    const until = lastUrl.searchParams.get('until')!
    expect(since.endsWith('Z')).toBe(true)
    expect(until.endsWith('Z')).toBe(true)
    expect(new Date(until).getTime() - new Date(since).getTime()).toBe(7 * 24 * 60 * 60 * 1000)
  })

  it('AC3: renders the dense grid with the real captured http-check values', async () => {
    renderPage()
    const table = await screen.findByRole('table')
    expect(within(table).getAllByText('…0060').length).toBeGreaterThan(0)
    expect(within(table).getByText('588')).toBeInTheDocument()
    expect(within(table).getAllByText('200').length).toBeGreaterThan(0)
  })

  it('AC4: caps rendered rows and shows a "showing latest N of M" caption when truncated (cap injectable)', async () => {
    renderPage({ renderCap: 3 })
    await screen.findByRole('table')

    const rows = within(screen.getByRole('table')).getAllByRole('row').slice(1)
    expect(rows).toHaveLength(3)
    expect(screen.getByText(/showing latest 3 of 8/i)).toBeInTheDocument()
  })

  it('does not show the truncation caption when nothing was truncated', async () => {
    renderPage({ renderCap: 1000 })
    await screen.findByRole('table')
    expect(screen.queryByText(/showing latest/i)).toBeNull()
  })

  it('AC5: shows a loading state while topology is in flight', () => {
    server.use(http.get('/api/v1/topology', async () => { await delay(50); return HttpResponse.json([]) }))
    renderPage()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('AC5: shows an error state with retry on a topology failure, never crashing the frame', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    renderPage()

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Window' })).toBeInTheDocument()
  })

  it('AC5: shows the window-empty state ("no observations in this window") for a zero-observation window', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.json([])))
    renderPage()

    expect(await screen.findByText('No observations in this window')).toBeInTheDocument()
  })

  it('AC5: shows a DISTINCT filtered-empty state ("no observations match your filters") when filters narrow to zero', async () => {
    const user = userEvent.setup()
    renderPage()

    await screen.findByRole('table')
    await user.type(screen.getByRole('textbox', { name: /search/i }), 'no-such-thing-xyz')

    expect(await screen.findByText('No observations match your filters')).toBeInTheDocument()
    expect(screen.queryByText('No observations in this window')).toBeNull()
  })

  it('has exactly one <h1> on the full routed page (the shell topbar owns it, not this page)', async () => {
    render(
      <MemoryRouter initialEntries={['/history']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    expect(await screen.findAllByRole('heading', { level: 1 })).toHaveLength(1)
  })
})
