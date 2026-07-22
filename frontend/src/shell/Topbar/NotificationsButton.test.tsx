import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { NotificationsButton } from './NotificationsButton'

function renderNotifications() {
  // A sibling button OUTSIDE the component, to exercise real
  // click-outside-to-close behavior against another focusable element.
  return render(
    <div>
      <button type="button">Elsewhere</button>
      <NotificationsButton />
    </div>,
  )
}

describe('NotificationsButton (STORY-141 AC1)', () => {
  it('renders a closed, accessibly-labelled trigger with aria-haspopup/aria-expanded wired', () => {
    renderNotifications()
    const trigger = screen.getByRole('button', { name: 'Notifications' })
    expect(trigger).toHaveAttribute('aria-haspopup')
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(trigger).toHaveAttribute('aria-controls')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('opens a panel with a "No notifications" empty state when the trigger is activated', async () => {
    const user = userEvent.setup()
    renderNotifications()
    const trigger = screen.getByRole('button', { name: 'Notifications' })

    await user.click(trigger)

    expect(trigger).toHaveAttribute('aria-expanded', 'true')
    const panel = screen.getByRole('dialog', { name: 'Notifications' })
    expect(panel).toBeInTheDocument()
    expect(panel).toHaveTextContent('No notifications')
    // aria-controls must actually resolve to the rendered panel.
    expect(panel).toHaveAttribute('id', trigger.getAttribute('aria-controls'))
  })

  it('moves focus into the panel on open', async () => {
    const user = userEvent.setup()
    renderNotifications()
    await user.click(screen.getByRole('button', { name: 'Notifications' }))

    const panel = screen.getByRole('dialog', { name: 'Notifications' })
    expect(panel).toHaveFocus()
  })

  it('closes on Escape and returns focus to the trigger', async () => {
    const user = userEvent.setup()
    renderNotifications()
    const trigger = screen.getByRole('button', { name: 'Notifications' })

    await user.click(trigger)
    expect(screen.getByRole('dialog', { name: 'Notifications' })).toBeInTheDocument()

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(trigger).toHaveFocus()
  })

  it('closes when clicking outside the panel', async () => {
    const user = userEvent.setup()
    renderNotifications()
    const trigger = screen.getByRole('button', { name: 'Notifications' })

    await user.click(trigger)
    expect(screen.getByRole('dialog', { name: 'Notifications' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Elsewhere' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
  })

  it('does not close when clicking inside the panel itself', async () => {
    const user = userEvent.setup()
    renderNotifications()
    await user.click(screen.getByRole('button', { name: 'Notifications' }))

    const panel = screen.getByRole('dialog', { name: 'Notifications' })
    await user.click(panel)

    expect(screen.getByRole('dialog', { name: 'Notifications' })).toBeInTheDocument()
  })

  it('toggles closed when the trigger is activated again while open', async () => {
    const user = userEvent.setup()
    renderNotifications()
    const trigger = screen.getByRole('button', { name: 'Notifications' })

    await user.click(trigger)
    expect(screen.getByRole('dialog', { name: 'Notifications' })).toBeInTheDocument()

    await user.click(trigger)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
  })
})
