import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { FIXTURE_COMPONENTS } from '../mocks/handlers/components'
import { FIXTURE_PROPOSALS } from '../mocks/handlers/approvals'
import { AppRoutes } from '../routes'
import { SIDEBAR_COLLAPSE_STORAGE_KEY } from './useSidebarCollapse'

/** Renders through the REAL routing table (`routes.tsx`), the same one
 * `App.tsx` uses in production, rather than mounting `ShellLayout` in
 * isolation — `ShellLayout` is a layout route (`<Outlet />`) and only
 * renders page content when composed into the real route tree. */
function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

describe('ShellLayout', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('redirects "/" to the Dashboard tab', async () => {
    renderAt('/')
    expect(
      await screen.findByRole('heading', { name: 'Dashboard', level: 1 }),
    ).toBeInTheDocument()
  })

  it('redirects an unknown path to the Dashboard tab', async () => {
    renderAt('/nope')
    expect(
      await screen.findByRole('heading', { name: 'Dashboard', level: 1 }),
    ).toBeInTheDocument()
  })

  it('routes the Availability tab to its page', async () => {
    renderAt('/availability')
    expect(
      await screen.findByRole('heading', { name: 'Availability', level: 1 }),
    ).toBeInTheDocument()
  })

  it('keeps /styleguide reachable through the same shell', async () => {
    renderAt('/styleguide')
    expect(
      await screen.findByRole('heading', { name: 'Design system', level: 1 }),
    ).toBeInTheDocument()
  })

  it("sources the Approvals sidebar badge from GET /api/v1/approvals's length", async () => {
    renderAt('/dashboard')
    const sidebarApprovals = await screen.findByRole('link', { name: /Approvals/ })
    await waitFor(() => expect(sidebarApprovals).toHaveTextContent(String(FIXTURE_PROPOSALS.length)))
  })

  it('derives the topbar overall status pill worst-of across GET /api/v1/components', async () => {
    renderAt('/dashboard')
    const topbar = screen.getByRole('banner')
    // FIXTURE_COMPONENTS includes an under_maintenance component and no
    // down/partial/degraded ones, so the worst-of is "maintenance".
    await waitFor(() => expect(within(topbar).getByText('Maintenance')).toBeInTheDocument())
  })

  it('renders the Pinned sidebar group from the same components fetch', async () => {
    renderAt('/dashboard')
    const pinned = await screen.findByRole('navigation', { name: 'Pinned' })
    expect(within(pinned).getByRole('link', { name: new RegExp(FIXTURE_COMPONENTS[0].name) })).toBeInTheDocument()
  })

  describe('last-updated indicator (quality review fix — captured at fetch success, not every render)', () => {
    afterEach(() => {
      vi.useRealTimers()
    })

    it('stays fixed at the fetch-completion time across an unrelated re-render, instead of reading "just now" forever', async () => {
      renderAt('/dashboard')

      // Real timers: let the initial GET /api/v1/components resolve.
      await screen.findByText('Updated just now')

      // Freeze/advance the clock 5 minutes forward for everything AFTER
      // this point — no fetch is in flight, so nothing needs a fake timer
      // to be manually advanced. `fireEvent` (not `userEvent`) is
      // synchronous and schedules no timers of its own, so it's safe to
      // use once fake timers are active.
      vi.useFakeTimers({ now: Date.now() + 5 * 60_000 })

      // An UNRELATED re-render (the desktop collapse toggle) must not reset
      // lastUpdated back to "now" a second time.
      const toggle = screen.getByRole('button', { name: /collapse sidebar/i })
      act(() => {
        fireEvent.click(toggle)
      })

      expect(screen.getByText('Updated 5m ago')).toBeInTheDocument()
    })
  })

  describe('desktop collapse toggle (AC5)', () => {
    it('toggles the sidebar collapsed state and persists it to localStorage', async () => {
      const user = userEvent.setup()
      renderAt('/dashboard')

      const toggle = await screen.findByRole('button', { name: /collapse sidebar/i })
      expect(toggle).toHaveAttribute('aria-expanded', 'true')

      await user.click(toggle)

      expect(await screen.findByRole('button', { name: /expand sidebar/i })).toHaveAttribute(
        'aria-expanded',
        'false',
      )
      expect(window.localStorage.getItem(SIDEBAR_COLLAPSE_STORAGE_KEY)).toBe('true')
    })

    it('restores a persisted collapsed=true choice with no flash of the expanded state', async () => {
      window.localStorage.setItem(SIDEBAR_COLLAPSE_STORAGE_KEY, 'true')
      renderAt('/dashboard')
      expect(await screen.findByRole('button', { name: /expand sidebar/i })).toHaveAttribute(
        'aria-expanded',
        'false',
      )
    })
  })

  describe('mobile sheet (AC6/AC8)', () => {
    function getMobileToggle(container: HTMLElement): HTMLButtonElement {
      const toggle = container.querySelector<HTMLButtonElement>('.shell-topbar__mobile-toggle')
      if (!toggle) throw new Error('mobile toggle not found')
      return toggle
    }

    it('opens the sheet from the topbar toggle and closes it on Escape, returning focus to the toggle', async () => {
      const user = userEvent.setup()
      const { container } = renderAt('/dashboard')
      const toggle = getMobileToggle(container)

      await user.click(toggle)
      expect(toggle).toHaveAttribute('aria-expanded', 'true')

      await user.keyboard('{Escape}')

      await waitFor(() => expect(toggle).toHaveAttribute('aria-expanded', 'false'))
      expect(toggle).toHaveFocus()
    })

    it('closes the sheet when the backdrop is clicked', async () => {
      const user = userEvent.setup()
      const { container } = renderAt('/dashboard')
      const toggle = getMobileToggle(container)

      await user.click(toggle)
      expect(toggle).toHaveAttribute('aria-expanded', 'true')

      const backdrop = container.querySelector<HTMLButtonElement>('.sidebar-backdrop')
      expect(backdrop).not.toBeNull()
      await user.click(backdrop!)

      await waitFor(() => expect(toggle).toHaveAttribute('aria-expanded', 'false'))
    })
  })
})
