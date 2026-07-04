import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import {
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_HISTORY_FRONTEND_TLS,
  FIXTURE_TOPOLOGY,
} from '../mocks/handlers'
import { CheckHistoryPage } from './CheckHistoryPage'

describe('CheckHistoryPage', () => {
  it('defaults to the first enumerated signal and renders its observations newest-first with mapped badges (AC1, AC3)', async () => {
    render(<CheckHistoryPage />)

    const table = await screen.findByRole('table')
    const rows = within(table).getAllByRole('row').slice(1) // drop the header row
    expect(rows).toHaveLength(FIXTURE_HISTORY_FRONTEND_HTTP.length)

    const select = screen.getByLabelText('Signal') as HTMLSelectElement
    expect(select.value).toBe('frontend-http')

    // Order preserved exactly as returned — never re-sorted.
    rows.forEach((row, index) => {
      const observation = FIXTURE_HISTORY_FRONTEND_HTTP[index]
      expect(within(row).getByText(observation.observed_at)).toBeInTheDocument()
      expect(within(row).getByText(observation.location)).toBeInTheDocument()
    })

    // Health badges: dot + ink label, never color-alone — assert the label text.
    expect(within(rows[0]).getByText('Up')).toBeInTheDocument()
    expect(within(rows[1]).getByText('Degraded')).toBeInTheDocument()
    expect(within(rows[2]).getByText('Down')).toBeInTheDocument()
  })

  it('renders latency in the mono token as integer milliseconds, and a null latency as an em-dash (never "0 ms") (AC3)', async () => {
    render(<CheckHistoryPage />)

    const table = await screen.findByRole('table')
    const rows = within(table).getAllByRole('row').slice(1)

    // First fixture row: latency_ms 571.
    expect(within(rows[0]).getByText('571 ms')).toBeInTheDocument()

    // Third fixture row: latency_ms null.
    expect(within(rows[2]).getByText('—')).toBeInTheDocument()
    expect(within(rows[2]).queryByText('0 ms')).not.toBeInTheDocument()
    expect(within(rows[2]).queryByText('null ms')).not.toBeInTheDocument()
  })

  it('lists every enumerated signal in the selector, labeled with its owning component', async () => {
    render(<CheckHistoryPage />)
    await screen.findByRole('table')

    const select = screen.getByLabelText('Signal') as HTMLSelectElement
    const optionLabels = Array.from(select.options).map((option) => option.textContent)

    const multiSignal = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-frontend')!
    for (const signal of multiSignal.signals) {
      expect(optionLabels).toContain(`${multiSignal.name} — ${signal.name}`)
    }
  })

  it('switching the signal selector loads and renders the newly-selected signal\'s observations (AC1, AC2)', async () => {
    const user = userEvent.setup()
    render(<CheckHistoryPage />)
    await screen.findByRole('table')

    const select = screen.getByLabelText('Signal')
    await user.selectOptions(select, 'frontend-tls')

    await waitFor(async () => {
      const table = screen.getByRole('table')
      const rows = within(table).getAllByRole('row').slice(1)
      expect(rows).toHaveLength(FIXTURE_HISTORY_FRONTEND_TLS.length)
    })

    const table = screen.getByRole('table')
    expect(
      within(table).getByText(FIXTURE_HISTORY_FRONTEND_TLS[0].observed_at),
    ).toBeInTheDocument()
    expect(
      within(table).queryByText(FIXTURE_HISTORY_FRONTEND_HTTP[0].observed_at),
    ).not.toBeInTheDocument()
  })

  it('driving the window selector refetches with a NEW tz-aware since/until (AC2)', async () => {
    const user = userEvent.setup()
    const seenRanges: Array<{ since: string; until: string }> = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        seenRanges.push({
          since: url.searchParams.get('since') ?? '',
          until: url.searchParams.get('until') ?? '',
        })
        return HttpResponse.json(FIXTURE_HISTORY_FRONTEND_HTTP)
      }),
    )

    render(<CheckHistoryPage />)
    await screen.findByRole('table')

    expect(seenRanges).toHaveLength(1)
    const initialRange = seenRanges[0]

    await user.click(screen.getByRole('button', { name: '7d' }))

    await waitFor(() => {
      expect(seenRanges.length).toBeGreaterThan(1)
    })

    expect(screen.getByRole('button', { name: '7d' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '24h' })).toHaveAttribute('aria-pressed', 'false')

    const newRange = seenRanges[seenRanges.length - 1]
    expect(newRange.since).not.toBe(initialRange.since)
    expect(new Date(newRange.since).toString()).not.toBe('Invalid Date')
    expect(newRange.since).toMatch(/Z$/)
  })
})
