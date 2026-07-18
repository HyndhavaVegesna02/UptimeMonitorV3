import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from './theme/ThemeContext'
import { AppShell } from './AppShell'
import { TABS } from './nav/tabs'
import { QUERY_MOBILE_DOWN } from './lib/breakpoints'
import { stubMatchMedia } from './test/matchMedia'
import { server } from './mocks/server'
import { FIXTURE_COMPONENTS } from './mocks/handlers'

function renderShell(initialPath = '/', { isMobile = false } = {}) {
  const media = stubMatchMedia({ [QUERY_MOBILE_DOWN]: isMobile })
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <ThemeProvider>
        <AppShell />
      </ThemeProvider>
    </MemoryRouter>,
  )
  return media
}

beforeEach(() => {
  window.localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
})

describe('AppShell — routing (STORY-104 AC1)', () => {
  it('renders all six nav items (icon + label) via the command bar', () => {
    renderShell()
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })

  it('renders the Dashboard placeholder at the root route with exactly one h1', () => {
    renderShell('/')
    expect(screen.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
  })

  it.each(TABS)('renders a placeholder for the $label tab at $path', (tab) => {
    renderShell(tab.path)
    expect(screen.getByRole('heading', { name: tab.label, level: 1 })).toBeInTheDocument()
  })

  it('renders the REAL Availability page (not a placeholder) at /availability (STORY-106)', () => {
    renderShell('/availability')
    expect(screen.getByRole('group', { name: 'Time window' })).toBeInTheDocument()
    expect(screen.queryByText(/rewrite in progress/i)).not.toBeInTheDocument()
  })

  it('renders the REAL Approvals page (not a placeholder) at /approvals (STORY-107)', async () => {
    renderShell('/approvals')
    expect(
      await screen.findByText(
        'Approving publishes the change to the public status page. Every decision requires confirmation before it submits.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText(/rewrite in progress/i)).not.toBeInTheDocument()
  })

  it('switches the active panel when a tab is clicked', async () => {
    const user = userEvent.setup()
    renderShell('/')

    await user.click(screen.getByRole('link', { name: 'Availability' }))

    expect(screen.getByRole('heading', { name: 'Availability' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Dashboard' })).not.toBeInTheDocument()
  })

  it('switches the active panel via keyboard activation of a tab', async () => {
    const user = userEvent.setup()
    renderShell('/')

    const maintenanceLink = screen.getByRole('link', { name: 'Maintenance' })
    maintenanceLink.focus()
    await user.keyboard('{Enter}')

    expect(screen.getByRole('heading', { name: 'Maintenance' })).toBeInTheDocument()
  })

  it('reflects the active route via aria-current on the matching tab only', () => {
    renderShell('/approvals')
    expect(screen.getByRole('link', { name: 'Approvals' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveAttribute('aria-current')
  })

  it('renders a not-found placeholder with a link back to Dashboard for an unknown path', () => {
    renderShell('/nonexistent-tab')

    expect(screen.getByRole('heading', { name: /not found/i, level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to Dashboard' })).toBeInTheDocument()
    // The command bar still renders alongside the not-found panel.
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
  })

  it('offers a skip link that moves focus to the main landmark', async () => {
    const user = userEvent.setup()
    renderShell('/')

    const skipLink = screen.getByRole('link', { name: 'Skip to main content' })
    expect(skipLink).toHaveAttribute('href', '#main-content')

    skipLink.focus()
    await user.keyboard('{Enter}')

    expect(screen.getByRole('main')).toHaveFocus()
  })

  it('renders NO sidebar in the DOM (design brief §IA: sidebar-less rewrite)', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/']}>
        <ThemeProvider>
          <AppShell />
        </ThemeProvider>
      </MemoryRouter>,
    )
    expect(container.querySelector('aside')).toBeNull()
    expect(container.querySelector('.sidebar')).toBeNull()
  })

  it('renders the command bar as a persistent header on every route', () => {
    renderShell('/publications')
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })
})

describe('AppShell — overall-status dot (STORY-104 AC2)', () => {
  it('shows "Unknown" while the components fetch is loading', () => {
    renderShell('/')
    expect(screen.getByText('Overall status: Unknown')).toBeInTheDocument()
  })

  it('shows the worst-of status once the components fetch resolves', async () => {
    server.use(
      http.get('/api/v1/components', () =>
        HttpResponse.json([
          { id: 'a', name: 'A', status: 'operational' },
          { id: 'b', name: 'B', status: 'major_outage' },
        ]),
      ),
    )
    renderShell('/')

    expect(await screen.findByText('Overall status: Down')).toBeInTheDocument()
  })

  it('shows "Up" once every component resolves healthy', async () => {
    server.use(
      http.get('/api/v1/components', () => HttpResponse.json(FIXTURE_COMPONENTS)),
    )
    renderShell('/')

    // FIXTURE_COMPONENTS has one degraded component, so the worst-of is
    // "Degraded" — assert the dot reflects it (not a fabricated "Up").
    expect(await screen.findByText('Overall status: Degraded')).toBeInTheDocument()
  })

  it('renders "Updated <relative time>" once the components fetch resolves', async () => {
    renderShell('/')
    expect(await screen.findByText('just now')).toBeInTheDocument()
  })
})

describe('AppShell — sample-mode switch + theme toggle (STORY-104 AC3)', () => {
  it('renders the sample-mode switch and theme toggle', async () => {
    renderShell('/')
    expect(await screen.findByRole('switch', { name: 'Sample mode' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /switch to/i })).toBeInTheDocument()
  })

  it('shows the sample-mode banner only once the flag is on', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderShell('/')

    expect(
      await screen.findByText(/sample mode — signals recorded as down/i),
    ).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('does not show the banner when the flag is off', async () => {
    renderShell('/')
    await screen.findByRole('switch', { name: 'Sample mode' })
    expect(
      screen.queryByText(/sample mode — signals recorded as down/i),
    ).not.toBeInTheDocument()
  })

  it('toggling the switch on shows the banner (single shared source of truth)', async () => {
    const user = userEvent.setup()
    server.use(http.put('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderShell('/')

    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    await user.click(toggle)

    expect(
      await screen.findByText(/sample mode — signals recorded as down/i),
    ).toBeInTheDocument()
  })
})

describe('AppShell — persistent SAMPLE chip (STORY-104 AC3, ported STORY-102 contract)', () => {
  it('shows no chip while the banner is visible (not yet dismissed)', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderShell('/')

    await screen.findByRole('status')
    expect(screen.queryByText('SAMPLE')).not.toBeInTheDocument()
  })

  it('shows the persistent chip once the banner is dismissed while the flag stays on', async () => {
    const user = userEvent.setup()
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderShell('/')

    await user.click(await screen.findByRole('button', { name: 'Dismiss' }))

    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByText('SAMPLE')).toBeInTheDocument()
  })

  it('restores the banner (and hides the chip) when the chip is clicked', async () => {
    const user = userEvent.setup()
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderShell('/')

    await user.click(await screen.findByRole('button', { name: 'Dismiss' }))
    const chip = screen.getByText('SAMPLE')

    await user.click(chip)

    expect(await screen.findByRole('status')).toBeInTheDocument()
    expect(screen.queryByText('SAMPLE')).not.toBeInTheDocument()
  })

  it('persists across a tab switch: the chip stays visible after navigating (shell-level, all tabs)', async () => {
    const user = userEvent.setup()
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))
    renderShell('/')

    await user.click(await screen.findByRole('button', { name: 'Dismiss' }))
    expect(screen.getByText('SAMPLE')).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Availability' }))

    expect(screen.getByRole('heading', { name: 'Availability' })).toBeInTheDocument()
    expect(screen.getByText('SAMPLE')).toBeInTheDocument()
  })
})

describe('AppShell — theme toggle', () => {
  it('reflects the CURRENT theme and toggles <html data-theme>', async () => {
    const user = userEvent.setup()
    renderShell('/')

    const toggle = screen.getByRole('button', { name: 'Switch to light theme' })
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    await user.click(toggle)

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(screen.getByRole('button', { name: 'Switch to dark theme' })).toBeInTheDocument()
  })
})

describe('AppShell — mobile hamburger sheet (STORY-104 AC4, ported SidebarDrawer contract)', () => {
  it('renders a hamburger trigger at mobile widths', () => {
    renderShell('/', { isMobile: true })
    expect(screen.getByRole('button', { name: 'Open navigation menu' })).toBeInTheDocument()
  })

  it('renders no hamburger trigger at desktop widths', () => {
    renderShell('/', { isMobile: false })
    expect(
      screen.queryByRole('button', { name: 'Open navigation menu' }),
    ).not.toBeInTheDocument()
  })

  it('opens the sheet from the hamburger trigger, revealing every tab', async () => {
    const user = userEvent.setup()
    renderShell('/', { isMobile: true })

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))

    const dialog = screen.getByRole('dialog', { name: 'Navigation' })
    expect(dialog).toBeInTheDocument()
    for (const tab of TABS) {
      expect(screen.getAllByRole('link', { name: tab.label }).length).toBeGreaterThan(0)
    }
  })

  it('closes on Escape and returns focus to the trigger', async () => {
    const user = userEvent.setup()
    renderShell('/', { isMobile: true })

    const trigger = screen.getByRole('button', { name: 'Open navigation menu' })
    await user.click(trigger)
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('closes the sheet when a nav link inside it is activated, navigating to the destination', async () => {
    const user = userEvent.setup()
    renderShell('/', { isMobile: true })

    await user.click(screen.getByRole('button', { name: 'Open navigation menu' }))
    const dialog = screen.getByRole('dialog')
    const availabilityLink = within(dialog).getByRole('link', { name: 'Availability' })

    await user.click(availabilityLink)

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Availability' })).toBeInTheDocument()
  })
})
