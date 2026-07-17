import { useRef, useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { SidebarDrawer } from './SidebarDrawer'

/** Mirrors how `AppShell` will drive this: a real hamburger trigger button
 * whose ref is handed to the drawer for the "focus returns to the trigger
 * on close" requirement (STORY-096 AC2), and open/close wired to real
 * state (not mocked) so Escape/scrim-click round-trip through a genuine
 * re-render. */
function Harness({ pendingApprovals }: { pendingApprovals?: number } = {}) {
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)

  return (
    <MemoryRouter>
      <button ref={triggerRef} onClick={() => setOpen(true)}>
        Open navigation menu
      </button>
      <SidebarDrawer
        open={open}
        onClose={() => setOpen(false)}
        triggerRef={triggerRef}
        pendingApprovals={pendingApprovals}
      />
    </MemoryRouter>
  )
}

describe('SidebarDrawer', () => {
  it('renders nothing (no dialog) while closed', () => {
    render(<Harness />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders as a labeled dialog with the sidebar nav once opened', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))

    const dialog = screen.getByRole('dialog', { name: 'Navigation' })
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
  })

  it('moves focus into the drawer on open', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))

    expect(screen.getByRole('button', { name: 'Close navigation' })).toHaveFocus()
  })

  it('closes on Escape and returns focus to the trigger', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    const trigger = screen.getByRole('button', { name: 'Open navigation menu' })
    await user.click(trigger)
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('closes on a scrim click and returns focus to the trigger', async () => {
    const user = userEvent.setup()
    const { container } = render(<Harness />)

    const trigger = screen.getByRole('button', { name: 'Open navigation menu' })
    await user.click(trigger)

    const scrim = container.querySelector('.sidebar-drawer__scrim')
    expect(scrim).not.toBeNull()
    await user.click(scrim as Element)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('closes when the sidebar header ("Close navigation") is clicked', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))
    await user.click(screen.getByRole('button', { name: 'Close navigation' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('passes the pending-approvals count through to the sidebar badge', async () => {
    const user = userEvent.setup()
    render(<Harness pendingApprovals={2} />)

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))

    expect(screen.getByRole('link', { name: 'Approvals, 2 pending' })).toBeInTheDocument()
  })

  it('wraps Tab focus at the end of the drawer back to the first focusable element', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))
    const closeButton = screen.getByRole('button', { name: 'Close navigation' })
    const publicationsLink = screen.getByRole('link', { name: 'Publications' })

    publicationsLink.focus()
    await user.tab()

    expect(closeButton).toHaveFocus()
  })

  it('wraps shift+Tab focus at the first focusable element back to the last one', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))
    const closeButton = screen.getByRole('button', { name: 'Close navigation' })
    const publicationsLink = screen.getByRole('link', { name: 'Publications' })

    closeButton.focus()
    await user.tab({ shift: true })

    expect(publicationsLink).toHaveFocus()
  })

  it('closes the drawer when a nav link is activated (destination page must not stay covered), returning focus to the trigger', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    const trigger = screen.getByRole('button', { name: 'Open navigation menu' })
    await user.click(trigger)
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Availability' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('does not error when there is no pending-approvals count yet', async () => {
    const user = userEvent.setup()
    render(<Harness pendingApprovals={undefined} />)
    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))
    expect(screen.getByRole('link', { name: 'Approvals' })).toBeInTheDocument()
  })
})
