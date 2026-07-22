import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { ComponentAvailabilityPage } from './ComponentAvailabilityPage'

function renderPage(componentId: string) {
  return render(
    <MemoryRouter initialEntries={[`/availability/${componentId}`]}>
      <Routes>
        <Route path="/availability/:componentId" element={<ComponentAvailabilityPage />} />
        <Route path="/availability" element={<div>Generic availability list</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ComponentAvailabilityPage', () => {
  it('paints the page frame (back link + window toggle) immediately, before topology resolves', () => {
    renderPage('http-check')

    expect(screen.getByRole('link', { name: /Back to Availability/ })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Window' })).toBeInTheDocument()
  })

  it('renders the real captured http-check component rollup once topology + availability resolve (AC1)', async () => {
    renderPage('http-check')

    expect(await screen.findByRole('heading', { name: 'HTTP Check', level: 2 })).toBeInTheDocument()
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })

  it('shows a loading state while topology is in flight (AC3)', () => {
    renderPage('http-check')

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows an error state with retry when the topology fetch fails, never crashing the frame (AC3)', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    renderPage('http-check')

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    // The frame keeps rendering regardless of the topology-region error.
    expect(screen.getByRole('link', { name: /Back to Availability/ })).toBeInTheDocument()
  })

  it('shows a clean not-found treatment for an unknown component id, never a crash or infinite spinner (AC3)', async () => {
    renderPage('does-not-exist')

    expect(await screen.findByText('Component not found')).toBeInTheDocument()
    expect(screen.queryByRole('status')).toBeNull()
    expect(screen.queryByRole('table')).toBeNull()
  })

  it('supports back-navigation to the generic Availability list (AC4)', async () => {
    const user = userEvent.setup()
    renderPage('http-check')

    await user.click(screen.getByRole('link', { name: /Back to Availability/ }))

    expect(await screen.findByText('Generic availability list')).toBeInTheDocument()
  })
})
