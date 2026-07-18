import { useRef, useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { NavSheet } from './NavSheet'

/** Mirrors how `AppShell` will drive this: a real hamburger trigger button
 * whose ref is handed to the sheet for the "focus returns to the trigger
 * on close" requirement (STORY-104 AC4, ported `SidebarDrawer` contract),
 * and open/close wired to real state (not mocked) so Escape/scrim-click
 * round-trip through a genuine re-render. */
function Harness() {
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)

  return (
    <MemoryRouter>
      <button ref={triggerRef} onClick={() => setOpen(true)}>
        Open navigation menu
      </button>
      <NavSheet open={open} onClose={() => setOpen(false)} triggerRef={triggerRef} />
    </MemoryRouter>
  )
}

describe('NavSheet (STORY-104 AC4, ported SidebarDrawer focus contract)', () => {
  it('renders nothing (no dialog) while closed', () => {
    render(<Harness />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders as a labeled dialog with the tab nav once opened', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))

    const dialog = screen.getByRole('dialog', { name: 'Navigation' })
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
  })

  it('moves focus into the sheet on open', async () => {
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

    const scrim = container.querySelector('.nav-sheet__scrim')
    expect(scrim).not.toBeNull()
    await user.click(scrim as Element)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('closes when the sheet header close button is clicked', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))
    await user.click(screen.getByRole('button', { name: 'Close navigation' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('wraps Tab focus at the end of the sheet back to the first focusable element', async () => {
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

  it('closes the sheet when a nav link is activated (destination page must not stay covered), returning focus to the trigger', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    const trigger = screen.getByRole('button', { name: 'Open navigation menu' })
    await user.click(trigger)
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Availability' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })
})
