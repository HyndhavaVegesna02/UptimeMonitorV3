import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { server } from '../mocks/server'
import { Sidebar } from './Sidebar'
import { TABS } from './tabs'

function renderSidebar(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Sidebar />
    </MemoryRouter>,
  )
}

describe('Sidebar', () => {
  it('renders all six tabs as routed links', () => {
    renderSidebar()
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })

  it('marks the tab matching the current route as active (aria-current)', () => {
    renderSidebar('/availability')
    expect(screen.getByRole('link', { name: 'Availability' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveAttribute(
      'aria-current',
    )
  })

  it('exposes a "Primary" nav landmark (deliberately not a tablist)', () => {
    renderSidebar()
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
  })

  it('renders the app title and a collapse toggle expanded by default', () => {
    renderSidebar()
    expect(screen.getByText('Uptime Monitor')).toBeInTheDocument()
    const toggle = screen.getByRole('button', { name: 'Collapse sidebar' })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
  })

  it('collapses to icons-only on toggle, hiding labels and flipping aria state', async () => {
    const user = userEvent.setup()
    renderSidebar()

    const toggle = screen.getByRole('button', { name: 'Collapse sidebar' })
    await user.click(toggle)

    const expandToggle = screen.getByRole('button', { name: 'Expand sidebar' })
    expect(expandToggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('Uptime Monitor')).not.toBeInTheDocument()
    // Links keep an accessible name even with the visible label hidden.
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })

  it('expands again on a second toggle click', async () => {
    const user = userEvent.setup()
    renderSidebar()

    await user.click(screen.getByRole('button', { name: 'Collapse sidebar' }))
    await user.click(screen.getByRole('button', { name: 'Expand sidebar' }))

    expect(screen.getByRole('button', { name: 'Collapse sidebar' })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
    expect(screen.getByText('Uptime Monitor')).toBeInTheDocument()
  })

  it('shows a live pending-count badge (number) on the Approvals link', async () => {
    renderSidebar()
    const approvalsLink = await screen.findByRole('link', { name: /Approvals/ })
    expect(await screen.findByText('2')).toBeInTheDocument()
    expect(approvalsLink).toBeInTheDocument()
  })

  it('shows a dot (not a number) badge when collapsed', async () => {
    const user = userEvent.setup()
    renderSidebar()

    await screen.findByText('2') // wait for the count to load while expanded
    await user.click(screen.getByRole('button', { name: 'Collapse sidebar' }))

    expect(screen.queryByText('2')).not.toBeInTheDocument()
    expect(document.querySelector('.sidebar__badge-dot')).toBeInTheDocument()
  })

  it('shows no badge when there are no open proposals', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))
    renderSidebar()

    await screen.findByRole('link', { name: 'Approvals' })
    expect(document.querySelector('.sidebar__badge-count')).not.toBeInTheDocument()
    expect(document.querySelector('.sidebar__badge-dot')).not.toBeInTheDocument()
  })

  it('degrades gracefully with no badge when the approvals fetch fails', async () => {
    server.use(
      http.get('/api/v1/approvals', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )
    renderSidebar()

    await screen.findByRole('link', { name: 'Approvals' })
    expect(document.querySelector('.sidebar__badge-count')).not.toBeInTheDocument()
    expect(document.querySelector('.sidebar__badge-dot')).not.toBeInTheDocument()
  })
})
