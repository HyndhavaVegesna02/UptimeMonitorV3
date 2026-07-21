import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http, delay } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { ComponentTopologyDTO } from '../../api/types'
import { FIXTURE_COMPONENT_AVAILABILITY } from '../../mocks/handlers/availability'
import { server } from '../../mocks/server'
import { AppRoutes } from '../../routes'
import { AvailabilityPage } from './AvailabilityPage'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/availability']}>
      <AvailabilityPage />
    </MemoryRouter>,
  )
}

describe('AvailabilityPage', () => {
  it('paints the page frame (description + window toggle) immediately, before topology resolves', () => {
    renderPage()

    expect(screen.getByRole('group', { name: 'Window' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '24h' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('renders the real captured http-check component rollup once topology + availability resolve', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { name: 'HTTP Check', level: 2 })).toBeInTheDocument()
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })

  it('renders a tidy empty state for zero components, no crash', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json([])))
    renderPage()

    expect(await screen.findByText('No components')).toBeInTheDocument()
  })

  it('shows a region error with retry when the topology fetch fails, never crashing the frame', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    renderPage()

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    // The frame keeps rendering regardless of the topology-region error.
    expect(screen.getByRole('group', { name: 'Window' })).toBeInTheDocument()
  })

  it('AC5: fetches each component independently - a fast region is not gated behind a slow one', async () => {
    const FAST = 'http-check'
    const SLOW = 'slow-check'
    const topology: ComponentTopologyDTO[] = [
      { id: FAST, name: 'Fast Component', signals: [] },
      { id: SLOW, name: 'Slow Component', signals: [] },
    ]
    server.use(
      http.get('/api/v1/topology', () => HttpResponse.json(topology)),
      http.get('/api/v1/availability/component/:componentId', async ({ params }) => {
        if (params.componentId === SLOW) {
          // A real, but SLOW, component - simulates the serialized local
          // DynamoDB availability computation (plan §Availability). This
          // must never block the fast component's own independent fetch.
          await delay(200)
        }
        return HttpResponse.json({
          ...FIXTURE_COMPONENT_AVAILABILITY['http-check'],
          component_id: String(params.componentId),
        })
      }),
    )

    renderPage()

    // The fast component's table renders well before the slow one settles.
    const fastHeading = await screen.findByRole('heading', { name: 'Fast Component', level: 2 })
    const fastPanel = fastHeading.closest('.panel') as HTMLElement
    expect(await within(fastPanel).findByRole('table')).toBeInTheDocument()

    const slowHeading = screen.getByRole('heading', { name: 'Slow Component', level: 2 })
    const slowPanel = slowHeading.closest('.panel') as HTMLElement
    // The slow region is STILL loading at this point - proves the two
    // fetches are independent, not bundled behind one blocking Promise.all.
    expect(within(slowPanel).getByRole('status')).toBeInTheDocument()
    expect(within(slowPanel).queryByRole('table')).toBeNull()

    expect(await within(slowPanel).findByRole('table')).toBeInTheDocument()
  })

  it('recomputes since/until as tz-aware UTC ISO (trailing Z) and refetches on window change', async () => {
    const seenRequests: string[] = []
    server.use(
      http.get('/api/v1/availability/component/:componentId', ({ request }) => {
        seenRequests.push(request.url)
        return HttpResponse.json(FIXTURE_COMPONENT_AVAILABILITY['http-check'])
      }),
    )
    const user = userEvent.setup()
    renderPage()

    await screen.findByRole('table')
    const initialCount = seenRequests.length
    expect(initialCount).toBeGreaterThan(0)

    await user.click(screen.getByRole('button', { name: '7d' }))

    await screen.findByRole('table')
    expect(seenRequests.length).toBeGreaterThan(initialCount)

    const lastUrl = new URL(seenRequests[seenRequests.length - 1])
    const since = lastUrl.searchParams.get('since')!
    const until = lastUrl.searchParams.get('until')!
    expect(since.endsWith('Z')).toBe(true)
    expect(until.endsWith('Z')).toBe(true)
    const deltaMs = new Date(until).getTime() - new Date(since).getTime()
    expect(deltaMs).toBe(7 * 24 * 60 * 60 * 1000)
  })

  it('has exactly one <h1> on the full routed page (the shell topbar owns it, not this page)', async () => {
    render(
      <MemoryRouter initialEntries={['/availability']}>
        <AppRoutes />
      </MemoryRouter>,
    )

    expect(await screen.findAllByRole('heading', { level: 1 })).toHaveLength(1)
  })
})
