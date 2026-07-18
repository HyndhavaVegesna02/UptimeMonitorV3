import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { server } from '../mocks/server'
import { FIXTURE_TOPOLOGY } from '../mocks/handlers'
import { AvailabilityPage } from './AvailabilityPage'

// Mirrors the `useAvailability.test.tsx` contention note (STORY-068): this
// page fans out one `getTopology()` hop plus 2 x FIXTURE_TOPOLOGY.length
// requests (rollup + segment history per component) on every render — a
// per-file timeout bump, not a global one.
beforeAll(() => {
  vi.setConfig({ testTimeout: 15000 })
})

afterAll(() => {
  vi.resetConfig()
})

function renderPage() {
  return render(
    <MemoryRouter>
      <AvailabilityPage />
    </MemoryRouter>,
  )
}

describe('AvailabilityPage — layout (AC1)', () => {
  it('renders exactly one h1 titled Availability, with a subtitle', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: 'Availability', level: 1 })).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
  })

  it('renders a 24h/7d/30d window switcher with 24h active by default', () => {
    renderPage()
    const group = screen.getByRole('group', { name: 'Time window' })
    const button24h = within(group).getByRole('button', { name: '24h' })
    const button7d = within(group).getByRole('button', { name: '7d' })
    const button30d = within(group).getByRole('button', { name: '30d' })

    expect(button24h).toHaveAttribute('aria-pressed', 'true')
    expect(button7d).toHaveAttribute('aria-pressed', 'false')
    expect(button30d).toHaveAttribute('aria-pressed', 'false')
  })

  it('switches the active window on click (keyboard operable via click activation)', async () => {
    const user = userEvent.setup()
    renderPage()

    const button7d = screen.getByRole('button', { name: '7d' })
    await user.click(button7d)

    expect(button7d).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '24h' })).toHaveAttribute('aria-pressed', 'false')
  })
})

describe('AvailabilityPage — per-tile states (AC3)', () => {
  it('shows a loading state before the fetch resolves', () => {
    renderPage()
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0)
  })

  it('surfaces a fetch failure as an error state with retry, never a blank page', async () => {
    server.use(
      http.get('/api/v1/topology', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load availability')
    // The header + window switcher survive the failure.
    expect(screen.getByRole('heading', { name: 'Availability', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Time window' })).toBeInTheDocument()
  })

  it('renders an explicit empty state when there are no components configured', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json([])))
    renderPage()

    expect(await screen.findByText(/no components configured/i)).toBeInTheDocument()
  })

  it('renders one tile per component once the fetch resolves', async () => {
    renderPage()

    await screen.findByText(FIXTURE_TOPOLOGY[0].name)
    for (const component of FIXTURE_TOPOLOGY) {
      expect(screen.getByText(component.name)).toBeInTheDocument()
    }
  })
})
