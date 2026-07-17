import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { QUERY_MOBILE_DOWN, QUERY_TABLET_DOWN } from '../lib/breakpoints'
import { stubMatchMedia } from '../test/matchMedia'
import { SIDEBAR_STORAGE_KEY } from './sidebarState'
import { useResponsiveSidebar } from './useResponsiveSidebar'

function Harness() {
  const { isMobile, expanded, toggleExpanded, drawerOpen, openDrawer, closeDrawer } =
    useResponsiveSidebar()
  return (
    <div>
      <p>isMobile: {String(isMobile)}</p>
      <p>expanded: {String(expanded)}</p>
      <p>drawerOpen: {String(drawerOpen)}</p>
      <button onClick={toggleExpanded}>toggle expanded</button>
      <button onClick={openDrawer}>open drawer</button>
      <button onClick={closeDrawer}>close drawer</button>
    </div>
  )
}

describe('useResponsiveSidebar', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('defaults expanded (desktop, nothing persisted, no breakpoint active)', () => {
    stubMatchMedia({ [QUERY_TABLET_DOWN]: false, [QUERY_MOBILE_DOWN]: false })
    render(<Harness />)
    expect(screen.getByText('expanded: true')).toBeInTheDocument()
    expect(screen.getByText('isMobile: false')).toBeInTheDocument()
  })

  it('honors a persisted collapsed preference at desktop width', () => {
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, 'false')
    stubMatchMedia({ [QUERY_TABLET_DOWN]: false, [QUERY_MOBILE_DOWN]: false })
    render(<Harness />)
    expect(screen.getByText('expanded: false')).toBeInTheDocument()
  })

  it('forces collapsed (rail) at <=1024px regardless of the persisted expanded preference (AC3)', () => {
    stubMatchMedia({ [QUERY_TABLET_DOWN]: true, [QUERY_MOBILE_DOWN]: false })
    render(<Harness />)
    expect(screen.getByText('expanded: false')).toBeInTheDocument()
  })

  it('still lets the user expand while narrow, without persisting the override', async () => {
    const user = userEvent.setup()
    stubMatchMedia({ [QUERY_TABLET_DOWN]: true, [QUERY_MOBILE_DOWN]: false })
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'toggle expanded' }))

    expect(screen.getByText('expanded: true')).toBeInTheDocument()
    expect(window.localStorage.getItem(SIDEBAR_STORAGE_KEY)).toBeNull()
  })

  it('drops the narrow-mode override on re-widening, reverting to the persisted preference (AC3)', async () => {
    const user = userEvent.setup()
    const media = stubMatchMedia({ [QUERY_TABLET_DOWN]: true, [QUERY_MOBILE_DOWN]: false })
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'toggle expanded' }))
    expect(screen.getByText('expanded: true')).toBeInTheDocument()

    act(() => {
      media.setMatches(QUERY_TABLET_DOWN, false)
    })

    // Back above 1024px: the persisted (default expanded=true) preference
    // applies, not the temporary narrow-mode override.
    expect(screen.getByText('expanded: true')).toBeInTheDocument()
  })

  it('a manual toggle at desktop width DOES persist (unchanged pre-096 behavior)', async () => {
    const user = userEvent.setup()
    stubMatchMedia({ [QUERY_TABLET_DOWN]: false, [QUERY_MOBILE_DOWN]: false })
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'toggle expanded' }))

    expect(screen.getByText('expanded: false')).toBeInTheDocument()
    expect(window.localStorage.getItem(SIDEBAR_STORAGE_KEY)).toBe('false')
  })

  it('reports isMobile at <=768px and starts with the drawer closed', () => {
    stubMatchMedia({ [QUERY_TABLET_DOWN]: true, [QUERY_MOBILE_DOWN]: true })
    render(<Harness />)
    expect(screen.getByText('isMobile: true')).toBeInTheDocument()
    expect(screen.getByText('drawerOpen: false')).toBeInTheDocument()
  })

  it('opens and closes the drawer via openDrawer/closeDrawer', async () => {
    const user = userEvent.setup()
    stubMatchMedia({ [QUERY_TABLET_DOWN]: true, [QUERY_MOBILE_DOWN]: true })
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'open drawer' }))
    expect(screen.getByText('drawerOpen: true')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'close drawer' }))
    expect(screen.getByText('drawerOpen: false')).toBeInTheDocument()
  })

  it('closes an open drawer automatically when the viewport widens past the mobile breakpoint', async () => {
    const user = userEvent.setup()
    const media = stubMatchMedia({ [QUERY_TABLET_DOWN]: true, [QUERY_MOBILE_DOWN]: true })
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'open drawer' }))
    expect(screen.getByText('drawerOpen: true')).toBeInTheDocument()

    act(() => {
      media.setMatches(QUERY_MOBILE_DOWN, false)
    })

    expect(screen.getByText('drawerOpen: false')).toBeInTheDocument()
  })
})
