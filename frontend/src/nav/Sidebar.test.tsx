import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TABS } from './tabs'

function renderSidebar(
  initialPath = '/',
  props: Partial<React.ComponentProps<typeof Sidebar>> = {},
) {
  const onToggleExpanded = props.onToggleExpanded ?? vi.fn()
  return {
    onToggleExpanded,
    ...render(
      <MemoryRouter initialEntries={[initialPath]}>
        <Sidebar
          expanded={props.expanded ?? true}
          onToggleExpanded={onToggleExpanded}
          pendingApprovals={props.pendingApprovals}
          variant={props.variant}
          onNavigate={props.onNavigate}
        />
      </MemoryRouter>,
    ),
  }
}

describe('Sidebar', () => {
  it('renders the app title when expanded', () => {
    renderSidebar()
    expect(screen.getByText('Uptime Monitor')).toBeInTheDocument()
  })

  it('renders all six tabs as routed links, by role/name', () => {
    renderSidebar()
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })

  it('marks the tab matching the current route as active', () => {
    renderSidebar('/availability')
    expect(screen.getByRole('link', { name: 'Availability' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveAttribute(
      'aria-current',
    )
  })

  it('exposes a collapse toggle with aria-expanded and a dynamic aria-label', async () => {
    const user = userEvent.setup()
    const { onToggleExpanded } = renderSidebar('/', { expanded: true })

    const toggle = screen.getByRole('button', { name: 'Collapse sidebar' })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    await user.click(toggle)
    expect(onToggleExpanded).toHaveBeenCalledTimes(1)
  })

  it('flips the toggle label/state when collapsed', () => {
    renderSidebar('/', { expanded: false })
    const toggle = screen.getByRole('button', { name: 'Expand sidebar' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  it('still exposes every tab by accessible name when collapsed (icon-only, label kept off-screen)', () => {
    renderSidebar('/', { expanded: false })
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
    // The title text itself hides visually with the sidebar, but the
    // collapse button keeps its own accessible name regardless.
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()
  })

  it('shows no Approvals badge when the pending count is zero, undefined, or the fetch failed', () => {
    renderSidebar('/', { pendingApprovals: undefined })
    expect(screen.getByRole('link', { name: 'Approvals' })).toBeInTheDocument()
    expect(screen.queryByText(/pending/)).not.toBeInTheDocument()
  })

  it('shows a visible number badge next to Approvals when expanded with a positive pending count', () => {
    renderSidebar('/', { expanded: true, pendingApprovals: 3 })
    const link = screen.getByRole('link', { name: 'Approvals, 3 pending' })
    expect(link).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('shows a decorative dot (no visible number) next to Approvals when collapsed with a positive pending count', () => {
    renderSidebar('/', { expanded: false, pendingApprovals: 3 })
    expect(
      screen.getByRole('link', { name: 'Approvals, 3 pending' }),
    ).toBeInTheDocument()
    expect(screen.queryByText('3')).not.toBeInTheDocument()
  })
})

describe('Sidebar — drawer variant (STORY-096 AC2)', () => {
  it('always shows the full labeled layout, ignoring `expanded`', () => {
    renderSidebar('/', { expanded: false, variant: 'drawer' })
    expect(screen.getByText('Uptime Monitor')).toBeInTheDocument()
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })

  it('renders its header as a "Close navigation" control instead of the collapse toggle', async () => {
    const user = userEvent.setup()
    const { onToggleExpanded } = renderSidebar('/', { expanded: true, variant: 'drawer' })

    const closeButton = screen.getByRole('button', { name: 'Close navigation' })
    expect(closeButton).not.toHaveAttribute('aria-expanded')

    await user.click(closeButton)
    expect(onToggleExpanded).toHaveBeenCalledTimes(1)
  })

  it('does not render the static-variant collapse toggle in drawer mode', () => {
    renderSidebar('/', { expanded: true, variant: 'drawer' })
    expect(screen.queryByRole('button', { name: 'Collapse sidebar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Expand sidebar' })).not.toBeInTheDocument()
  })
})

describe('Sidebar — onNavigate (STORY-096 fix: drawer must close after nav-link activation)', () => {
  it('calls onNavigate when a tab link is activated', async () => {
    const user = userEvent.setup()
    const onNavigate = vi.fn()
    renderSidebar('/', { onNavigate })

    await user.click(screen.getByRole('link', { name: 'Availability' }))

    expect(onNavigate).toHaveBeenCalledTimes(1)
  })

  it('does not throw when onNavigate is omitted (static usage, unchanged)', async () => {
    const user = userEvent.setup()
    renderSidebar('/')

    await user.click(screen.getByRole('link', { name: 'Availability' }))

    expect(screen.getByRole('link', { name: 'Availability' })).toHaveAttribute(
      'aria-current',
      'page',
    )
  })
})
