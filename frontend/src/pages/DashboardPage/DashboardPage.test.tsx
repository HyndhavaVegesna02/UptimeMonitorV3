import { render, screen, within } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { ComponentDTO } from '../../api/types'
import { server } from '../../mocks/server'
import { AppRoutes } from '../../routes'
import { DashboardPage } from './DashboardPage'

/** The real captured single-component sample (live-api-samples.md) — the
 * shared default `componentsHandlers`/`approvalsHandlers` fixtures serve a
 * 4-component sockshop shape for the SHELL's own tests (STORY-121); the
 * Dashboard's own tests override with the REAL "http-check" shape so the
 * signal_key derivation (component id == signal_key) actually lines up
 * with the real `history`/`availability` fixtures. */
const REAL_COMPONENTS: ComponentDTO[] = [{ id: 'http-check', name: 'HTTP Check', status: 'operational' }]

/** Also pins `approvals` to the real captured `[]` sample — the shared
 * default `approvalsHandlers` fixture (1 open proposal) is STORY-121's own,
 * used by the shell's tests; the Dashboard's cross-checks are against the
 * live-api-samples.md capture, which has zero open approvals. */
function useRealComponents() {
  server.use(
    http.get('/api/v1/components', () => HttpResponse.json(REAL_COMPONENTS)),
    http.get('/api/v1/approvals', () => HttpResponse.json([])),
  )
}

function renderDashboard() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <DashboardPage />
    </MemoryRouter>,
  )
}

describe('DashboardPage', () => {
  it('renders the KPI row derived from the real availability/history/components/approvals fixtures', async () => {
    useRealComponents()
    renderDashboard()

    // availability_pct 1.0 -> "100.00"
    expect(await screen.findByText('Overall availability · 24h')).toBeInTheDocument()
    expect(await screen.findByText('100.00')).toBeInTheDocument()

    // avg latency across the 8 real observations rounds to 569ms.
    expect(await screen.findByText('569')).toBeInTheDocument()

    // 1 real component, operational -> 1/1 healthy.
    expect(screen.getByText('Components healthy')).toBeInTheDocument()
    expect(screen.getByText('/ 1')).toBeInTheDocument()

    // No open approvals in the real sample.
    expect(screen.getByText('Pending approvals')).toBeInTheDocument()
    const pendingLink = screen.getByRole('link', { name: /Pending approvals/ })
    expect(within(pendingLink).getByText(/^0$/)).toBeInTheDocument()
    expect(pendingLink).not.toHaveClass('summary-card--attention')
  })

  it('renders the response-time chart with the real spike (951ms at …0047)', async () => {
    useRealComponents()
    renderDashboard()

    const chart = await screen.findByRole('img', { name: /Response time over the last 24 hours/ })
    expect(chart.getAttribute('aria-label')).toContain('569')
    expect(chart.getAttribute('aria-label')).toContain('951')
  })

  it('renders the 2 real probe locations with a working segmented control', async () => {
    useRealComponents()
    renderDashboard()

    const group = await screen.findByRole('group', { name: 'Metric' })
    const panel = group.closest('.panel')!
    expect(within(panel as HTMLElement).getByText(/…0047/)).toBeInTheDocument()
    expect(within(panel as HTMLElement).getByText(/…0060/)).toBeInTheDocument()
  })

  it('renders a tidy empty state for maintenance (the real sample is [])', async () => {
    useRealComponents()
    renderDashboard()

    expect(await screen.findByText(/No maintenance scheduled/)).toBeInTheDocument()
  })

  it('renders the recent-checks feed and components roster from the real data', async () => {
    useRealComponents()
    renderDashboard()

    expect(await screen.findAllByText('HTTP Check')).not.toHaveLength(0)
    expect(screen.getByText('Recent checks')).toBeInTheDocument()
    expect(screen.getByText('Components')).toBeInTheDocument()
  })

  it('shows a loading state before the fetches settle', () => {
    useRealComponents()
    renderDashboard()
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0)
  })

  it('shows an error state with a retry action when a fetch fails, never fabricating KPI numbers', async () => {
    server.use(http.get('/api/v1/components', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    renderDashboard()

    expect((await screen.findAllByRole('alert')).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: 'Retry' }).length).toBeGreaterThan(0)
    expect(screen.queryByText('Overall availability · 24h')).toBeNull()
  })

  it('has exactly one <h1> on the full routed page (the shell topbar owns it, not this page)', async () => {
    useRealComponents()
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AppRoutes />
      </MemoryRouter>,
    )

    expect(await screen.findAllByRole('heading', { level: 1 })).toHaveLength(1)
  })
})
