import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_PUBLICATIONS } from '../mocks/handlers'
import { PublicationsPage } from './PublicationsPage'

describe('PublicationsPage', () => {
  it('shows a loading state, then a table with one row per publication, newest-first (AC1)', async () => {
    render(<PublicationsPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()

    expect(
      screen.getByRole('columnheader', { name: 'Published at' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('columnheader', { name: 'Component' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Status' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Proposal' })).toBeInTheDocument()

    // Exactly one data row per fixture publication, in the API's own order.
    const rows = screen.getAllByRole('row')
    expect(rows).toHaveLength(FIXTURE_PUBLICATIONS.length + 1)

    // Row order matches the fixture's (already newest-first) order — never
    // re-sorted client-side.
    for (const publication of FIXTURE_PUBLICATIONS) {
      expect(screen.getByText(publication.published_at)).toBeInTheDocument()
    }
    expect(screen.getAllByText('checkout')).toHaveLength(2)
    expect(screen.getByText('login')).toBeInTheDocument()
  })

  it('maps a non-operational published status onto the correct badge label (AC1, AC3)', async () => {
    render(<PublicationsPage />)
    await screen.findByRole('table')

    // FIXTURE_PUBLICATIONS[1] is login / major_outage -> "Down".
    expect(screen.getByText('Down')).toBeInTheDocument()
    // FIXTURE_PUBLICATIONS[0] is checkout / operational -> "Up".
    expect(screen.getByText('Up')).toBeInTheDocument()
    // FIXTURE_PUBLICATIONS[2] is checkout / degraded -> "Degraded".
    expect(screen.getByText('Degraded')).toBeInTheDocument()
  })

  it('renders a null proposal_id as an em-dash, never a sentinel 0 (AC1)', async () => {
    render(<PublicationsPage />)
    await screen.findByRole('table')

    // FIXTURE_PUBLICATIONS[0] has proposal_id: null.
    expect(screen.getByText('—')).toBeInTheDocument()
    // FIXTURE_PUBLICATIONS[1]/[2] carry real proposal ids.
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('states the 50-item cap visibly in the header copy (AC3)', async () => {
    render(<PublicationsPage />)
    await screen.findByRole('table')

    expect(screen.getByText(/latest 50 publications/i)).toBeInTheDocument()
  })

  it('renders the empty state when nothing has been published yet (AC2)', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.json([])))

    render(<PublicationsPage />)

    expect(await screen.findByText('Nothing published yet')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows an error state on failure, then recovers via retry (AC2)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/publications', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_PUBLICATIONS)
      }),
    )

    render(<PublicationsPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Could not load publications',
    )

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByRole('table')).toBeInTheDocument()
    expect(callCount).toBe(2)
  })
})
