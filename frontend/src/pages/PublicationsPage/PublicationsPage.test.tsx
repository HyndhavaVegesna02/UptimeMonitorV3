import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { FIXTURE_PUBLICATIONS_TIMELINE } from '../../mocks/handlers/publications'
import { server } from '../../mocks/server'
import { AppRoutes } from '../../routes'
import { PublicationsPage } from './PublicationsPage'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/publications']}>
      <PublicationsPage />
    </MemoryRouter>,
  )
}

describe('PublicationsPage', () => {
  it('AC3: shows a loading state while the fetch is in flight', () => {
    server.use(http.get('/api/v1/publications', async () => new Promise(() => {})))
    renderPage()
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0)
  })

  it('AC3: shows an error state with retry on fetch failure', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    renderPage()

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('AC3: shows "nothing published yet" for the real empty list', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.json([])))
    renderPage()

    expect(await screen.findByText(/nothing published yet/i)).toBeInTheDocument()
  })

  it('AC1: renders the populated timeline from the fixture shape', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.json(FIXTURE_PUBLICATIONS_TIMELINE)))
    renderPage()

    expect(await screen.findByText('Succeeded')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getAllByText('http-check').length).toBeGreaterThan(0)
  })

  it('AC1: notes the ~50 cap in the UI', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.json([])))
    renderPage()

    await screen.findByText(/nothing published yet/i)
    expect(screen.getByText(/50/)).toBeInTheDocument()
  })

  it('has exactly one <h1> on the full routed page (the shell topbar owns it, not this page)', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.json([])))
    render(
      <MemoryRouter initialEntries={['/publications']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    expect(await screen.findAllByRole('heading', { level: 1 })).toHaveLength(1)
  })
})
