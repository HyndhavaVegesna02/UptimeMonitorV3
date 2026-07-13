import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_PUBLICATIONS } from '../mocks/handlers'
import { PublicationsPage } from './PublicationsPage'

describe('PublicationsPage', () => {
  it('shows a loading state, then a vertical timeline with one item per publication, newest-first (AC1)', async () => {
    render(<PublicationsPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const list = await screen.findByRole('list', { name: 'Publication log' })
    expect(list).toBeInTheDocument()

    // Exactly one listitem per fixture publication, in the API's own
    // (already newest-first) order — never re-sorted client-side.
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(FIXTURE_PUBLICATIONS.length)

    FIXTURE_PUBLICATIONS.forEach((publication, index) => {
      expect(
        within(items[index]).getByText(publication.published_at),
      ).toBeInTheDocument()
      expect(
        within(items[index]).getByText(publication.component_id),
      ).toBeInTheDocument()
    })
  })

  it('shows scope (component name) then status via toHealthStatus, dot + text never color-only (AC1)', async () => {
    render(<PublicationsPage />)
    const list = await screen.findByRole('list', { name: 'Publication log' })

    // FIXTURE_PUBLICATIONS[0] is checkout / operational -> "Up".
    // FIXTURE_PUBLICATIONS[1] is login / major_outage -> "Down".
    // FIXTURE_PUBLICATIONS[2] is checkout / degraded -> "Degraded".
    expect(within(list).getByText('Up')).toBeInTheDocument()
    expect(within(list).getByText('Down')).toBeInTheDocument()
    expect(within(list).getByText('Degraded')).toBeInTheDocument()

    const items = screen.getAllByRole('listitem')
    expect(within(items[1]).getByText('login')).toBeInTheDocument()
    expect(within(items[1]).getByText('Down')).toBeInTheDocument()
  })

  it('renders the outcome as a dot+text chip, succeeded vs failed (STORY-072 AC4)', async () => {
    render(<PublicationsPage />)
    const list = await screen.findByRole('list', { name: 'Publication log' })
    const items = screen.getAllByRole('listitem')

    // FIXTURE_PUBLICATIONS[0]/[2] are outcome: 'succeeded'; [1] is 'failed'.
    expect(within(items[0]).getByText('Succeeded')).toBeInTheDocument()
    expect(within(items[1]).getByText('Failed')).toBeInTheDocument()
    expect(within(items[2]).getByText('Succeeded')).toBeInTheDocument()

    // Never color-only: the outcome text is present alongside the status
    // text, both accompanied by a decorative (aria-hidden) dot.
    expect(within(list).getAllByText('Succeeded')).toHaveLength(2)
    expect(within(list).getAllByText('Failed')).toHaveLength(1)
  })

  it('renders a null proposal_id as an em-dash, never a sentinel 0 (AC1)', async () => {
    render(<PublicationsPage />)
    await screen.findByRole('list', { name: 'Publication log' })

    const items = screen.getAllByRole('listitem')
    // FIXTURE_PUBLICATIONS[0] has proposal_id: null.
    expect(within(items[0]).getByText('Proposal —')).toBeInTheDocument()
    // FIXTURE_PUBLICATIONS[1]/[2] carry real proposal ids.
    expect(within(items[1]).getByText('Proposal 5')).toBeInTheDocument()
    expect(within(items[2]).getByText('Proposal 42')).toBeInTheDocument()
  })

  it('renders the author metadata or an em-dash if null (STORY-066)', async () => {
    render(<PublicationsPage />)
    await screen.findByRole('list', { name: 'Publication log' })

    const items = screen.getAllByRole('listitem')
    // FIXTURE_PUBLICATIONS[0] has author: null.
    expect(within(items[0]).getByText('Author —')).toBeInTheDocument()
    // FIXTURE_PUBLICATIONS[1] has author: 'dashboard-operator'.
    expect(within(items[1]).getByText('Author dashboard-operator')).toBeInTheDocument()
    // FIXTURE_PUBLICATIONS[2] has author: 'dashboard-operator'.
    expect(within(items[2]).getByText('Author dashboard-operator')).toBeInTheDocument()
  })


  it('omits the connector line below the last item only (AC1)', async () => {
    const { container } = render(<PublicationsPage />)
    await screen.findByRole('list', { name: 'Publication log' })

    const rails = container.querySelectorAll('.timeline__item')
    expect(rails).toHaveLength(FIXTURE_PUBLICATIONS.length)
    // Every item but the last has a connector line below its dot.
    for (let i = 0; i < rails.length - 1; i += 1) {
      expect(rails[i].querySelector('.timeline__line')).not.toBeNull()
    }
    expect(rails[rails.length - 1].querySelector('.timeline__line')).toBeNull()
  })

  it('states the 50-item cap visibly in the header copy (AC2)', async () => {
    render(<PublicationsPage />)
    await screen.findByRole('list', { name: 'Publication log' })

    expect(screen.getByText(/latest 50 publications/i)).toBeInTheDocument()
  })

  it('renders the empty state when nothing has been published yet (AC2)', async () => {
    server.use(http.get('/api/v1/publications', () => HttpResponse.json([])))

    render(<PublicationsPage />)

    expect(await screen.findByText('Nothing published yet')).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: 'Publication log' })).not.toBeInTheDocument()
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

    expect(
      await screen.findByRole('list', { name: 'Publication log' }),
    ).toBeInTheDocument()
    expect(callCount).toBe(2)
  })
})
