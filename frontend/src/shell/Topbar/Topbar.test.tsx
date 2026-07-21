import { createRef } from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { Topbar } from './Topbar'

function renderTopbar(overrides: Partial<React.ComponentProps<typeof Topbar>> = {}) {
  return render(
    <MemoryRouter>
      <Topbar
        title="Dashboard"
        overallStatus="up"
        lastUpdated={new Date('2026-07-21T12:00:00Z')}
        now={new Date('2026-07-21T12:00:00Z')}
        mobileNavOpen={false}
        mobileNavId="shell-sidebar-nav"
        onOpenMobileNav={vi.fn()}
        mobileToggleRef={createRef<HTMLButtonElement>()}
        {...overrides}
      />
    </MemoryRouter>,
  )
}

describe('Topbar', () => {
  it('renders the page title as the single top-level heading', () => {
    renderTopbar()
    expect(screen.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeInTheDocument()
  })

  it('renders the worst-of overall status as a dot+icon+text pill, never colour alone', () => {
    renderTopbar({ overallStatus: 'down' })
    expect(screen.getByText('Down')).toBeInTheDocument()
  })

  it('renders a last-updated indicator', () => {
    renderTopbar({
      lastUpdated: new Date('2026-07-21T11:55:00Z'),
      now: new Date('2026-07-21T12:00:00Z'),
    })
    expect(screen.getByText('Updated 5m ago')).toBeInTheDocument()
  })

  it('has an accessibly-labelled notifications button', () => {
    renderTopbar()
    expect(screen.getByRole('button', { name: 'Notifications' })).toBeInTheDocument()
  })

  it('has a "+ Maintenance" affordance linking to the Maintenance tab', () => {
    renderTopbar()
    expect(screen.getByRole('link', { name: /Maintenance/ })).toHaveAttribute(
      'href',
      '/maintenance',
    )
  })

  describe('mobile nav toggle (AC6)', () => {
    // The toggle is only visually shown at the mobile breakpoint
    // (Topbar.css) — jsdom's default viewport is desktop-sized, so it's
    // legitimately CSS-hidden here (as it would be on a real desktop), and
    // dom-accessibility-api returns "" for a hidden element's accessible
    // name even with `{ hidden: true }`. Select by its class instead of
    // role+name to exercise the real attributes regardless of viewport.
    function getMobileToggle(container: HTMLElement): HTMLButtonElement {
      const toggle = container.querySelector<HTMLButtonElement>('.shell-topbar__mobile-toggle')
      if (!toggle) {
        throw new Error('mobile nav toggle button not found')
      }
      return toggle
    }

    it('has an aria-label, reflects the open state via aria-expanded, and points aria-controls at the sheet', () => {
      const { container } = renderTopbar({
        mobileNavOpen: true,
        mobileNavId: 'shell-sidebar-nav',
      })
      const toggle = getMobileToggle(container)
      expect(toggle).toHaveAttribute('aria-label', 'Navigation menu')
      expect(toggle).toHaveAttribute('aria-expanded', 'true')
      expect(toggle).toHaveAttribute('aria-controls', 'shell-sidebar-nav')
    })

    it('reflects aria-expanded="false" when the sheet is closed', () => {
      const { container } = renderTopbar({ mobileNavOpen: false })
      expect(getMobileToggle(container)).toHaveAttribute('aria-expanded', 'false')
    })

    it('calls onOpenMobileNav when activated', () => {
      const onOpenMobileNav = vi.fn()
      const { container } = renderTopbar({ onOpenMobileNav })
      getMobileToggle(container).click()
      expect(onOpenMobileNav).toHaveBeenCalledTimes(1)
    })
  })
})
