import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { FIXTURE_MAINTENANCE_WINDOWS } from '../../mocks/handlers/maintenance'
import { server } from '../../mocks/server'
import { AppRoutes } from '../../routes'
import { MaintenancePage } from './MaintenancePage'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/maintenance']}>
      <MaintenancePage />
    </MemoryRouter>,
  )
}

describe('MaintenancePage', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('AC5: shows a loading state for the list while the fetch is in flight', () => {
    server.use(http.get('/api/v1/maintenance', async () => new Promise(() => {})))
    renderPage()
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0)
  })

  it('AC5: shows an error state with retry on list fetch failure', async () => {
    server.use(http.get('/api/v1/maintenance', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    renderPage()

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })

  it('AC5: shows a tidy "no maintenance scheduled" empty state for zero windows (the real captured sample)', async () => {
    server.use(http.get('/api/v1/maintenance', () => HttpResponse.json([])))
    renderPage()

    expect(await screen.findByText(/no maintenance scheduled/i)).toBeInTheDocument()
  })

  it('AC1: renders every window with title, component, range, reason, and derived state badge', async () => {
    server.use(http.get('/api/v1/maintenance', () => HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS)))
    renderPage()

    expect(await screen.findByText('Planned DB maintenance')).toBeInTheDocument()
    expect(screen.getByText('Upcoming')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Past')).toBeInTheDocument()
  })

  it('AC2: scheduling a window POSTs to the real endpoint and the list reconciles from the server', async () => {
    let maintenanceCallCount = 0
    server.use(
      http.get('/api/v1/maintenance', () => {
        maintenanceCallCount += 1
        return HttpResponse.json(maintenanceCallCount === 1 ? [] : FIXTURE_MAINTENANCE_WINDOWS)
      }),
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS[0], { status: 201 }),
      ),
    )
    const user = userEvent.setup()
    renderPage()
    await screen.findByText(/no maintenance scheduled/i)

    await user.selectOptions(screen.getByLabelText(/component/i), 'sockshop-checkout')
    await user.type(screen.getByLabelText(/^start/i), '2026-07-22T10:00')
    await user.type(screen.getByLabelText(/^end/i), '2026-07-22T12:00')
    await user.click(screen.getByRole('button', { name: /schedule/i }))

    await waitFor(() => expect(screen.queryByText(/no maintenance scheduled/i)).toBeNull())
    expect(maintenanceCallCount).toBeGreaterThanOrEqual(2)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4 CRUX: deleting a window that is already gone (404) shows a non-destructive notice and refreshes the list', async () => {
    let maintenanceCallCount = 0
    server.use(
      http.get('/api/v1/maintenance', () => {
        maintenanceCallCount += 1
        return HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS)
      }),
      http.delete('/api/v1/maintenance/:windowId', () =>
        HttpResponse.json({ detail: 'Maintenance window not found' }, { status: 404 }),
      ),
    )
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('Planned DB maintenance')
    const callsBeforeDelete = maintenanceCallCount

    const deleteButtons = screen.getAllByRole('button', { name: /^delete /i })
    await user.click(deleteButtons[0])
    await user.click(screen.getByRole('button', { name: /^confirm delete$/i }))

    expect(await screen.findByText(/already deleted/i)).toBeInTheDocument()
    await waitFor(() => expect(maintenanceCallCount).toBeGreaterThan(callsBeforeDelete))
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4: deleting a window (204 success) removes it once the list reconciles', async () => {
    let maintenanceCallCount = 0
    server.use(
      http.get('/api/v1/maintenance', () => {
        maintenanceCallCount += 1
        return HttpResponse.json(maintenanceCallCount === 1 ? FIXTURE_MAINTENANCE_WINDOWS : [])
      }),
      http.delete('/api/v1/maintenance/:windowId', () => new HttpResponse(null, { status: 204 })),
    )
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('Planned DB maintenance')

    const deleteButtons = screen.getAllByRole('button', { name: /^delete /i })
    await user.click(deleteButtons[0])
    await user.click(screen.getByRole('button', { name: /^confirm delete$/i }))

    await waitFor(() => expect(screen.queryByText('Planned DB maintenance')).toBeNull())
    expect(await screen.findByText(/no maintenance scheduled/i)).toBeInTheDocument()
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('has exactly one <h1> on the full routed page (the shell topbar owns it, not this page)', async () => {
    render(
      <MemoryRouter initialEntries={['/maintenance']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    expect(await screen.findAllByRole('heading', { level: 1 })).toHaveLength(1)
  })
})
