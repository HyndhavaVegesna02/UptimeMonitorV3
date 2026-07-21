import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { FIXTURE_COMPONENTS } from '../../mocks/handlers/components'
import { Sidebar } from './Sidebar'

function renderSidebar(overrides: Partial<React.ComponentProps<typeof Sidebar>> = {}) {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Sidebar
        collapsed={false}
        onToggleCollapsed={vi.fn()}
        activePath="/dashboard"
        approvalsCount={0}
        components={[]}
        mobileOpen={false}
        onCloseMobile={vi.fn()}
        {...overrides}
      />
    </MemoryRouter>,
  )
}

describe('Sidebar', () => {
  it('renders the Monitoring group with its three tabs', () => {
    renderSidebar()
    const group = screen.getByRole('navigation', { name: 'Monitoring' })
    expect(within(group).getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
    expect(within(group).getByRole('link', { name: 'Availability' })).toBeInTheDocument()
    expect(within(group).getByRole('link', { name: 'History' })).toBeInTheDocument()
  })

  it('renders the Operations group with its three tabs', () => {
    renderSidebar()
    const group = screen.getByRole('navigation', { name: 'Operations' })
    expect(within(group).getByRole('link', { name: /Approvals/ })).toBeInTheDocument()
    expect(within(group).getByRole('link', { name: 'Maintenance' })).toBeInTheDocument()
    expect(within(group).getByRole('link', { name: 'Publications' })).toBeInTheDocument()
  })

  it('marks the active route aria-current="page" and leaves the rest unmarked', () => {
    renderSidebar({ activePath: '/availability' })
    expect(screen.getByRole('link', { name: 'Availability' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveAttribute('aria-current')
  })

  describe('Approvals pending-count badge (AC2)', () => {
    it('shows the count when there are pending approvals', () => {
      renderSidebar({ approvalsCount: 3 })
      expect(screen.getByRole('link', { name: /Approvals/ })).toHaveTextContent('3')
    })

    it('shows no badge when there are zero pending approvals', () => {
      renderSidebar({ approvalsCount: 0 })
      const link = screen.getByRole('link', { name: 'Approvals' })
      expect(link).not.toHaveTextContent(/\d/)
    })
  })

  describe('Pinned group (component quick-links)', () => {
    it('renders one pinned link per component, each with its name', () => {
      renderSidebar({ components: FIXTURE_COMPONENTS })
      const group = screen.getByRole('navigation', { name: 'Pinned' })
      for (const component of FIXTURE_COMPONENTS) {
        expect(within(group).getByRole('link', { name: new RegExp(component.name) })).toBeInTheDocument()
      }
    })

    it('renders no Pinned group heading/nav at all when there are no components', () => {
      renderSidebar({ components: [] })
      expect(screen.queryByRole('navigation', { name: 'Pinned' })).toBeNull()
    })
  })

  describe('collapse toggle (AC5)', () => {
    it('exposes an aria-expanded toggle reflecting the expanded state', () => {
      renderSidebar({ collapsed: false })
      const toggle = screen.getByRole('button', { name: /collapse sidebar/i })
      expect(toggle).toHaveAttribute('aria-expanded', 'true')
    })

    it('reflects the collapsed state and relabels the toggle', () => {
      renderSidebar({ collapsed: true })
      const toggle = screen.getByRole('button', { name: /expand sidebar/i })
      expect(toggle).toHaveAttribute('aria-expanded', 'false')
    })

    it('calls onToggleCollapsed when the toggle is activated', async () => {
      const onToggleCollapsed = vi.fn()
      renderSidebar({ onToggleCollapsed })
      const toggle = screen.getByRole('button', { name: /collapse sidebar/i })
      toggle.click()
      expect(onToggleCollapsed).toHaveBeenCalledTimes(1)
    })

    it('has aria-controls pointing at the sidebar nav landmark', () => {
      renderSidebar()
      const toggle = screen.getByRole('button', { name: /collapse sidebar/i })
      const controlsId = toggle.getAttribute('aria-controls')
      expect(controlsId).toBeTruthy()
      expect(document.getElementById(controlsId!)).not.toBeNull()
    })
  })
})
