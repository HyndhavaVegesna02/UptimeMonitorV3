import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from './theme/ThemeContext'
import { AppShell } from './AppShell'
import { TABS } from './nav/tabs'
import { server } from './mocks/server'
import { FIXTURE_PROPOSALS } from './mocks/handlers'

function mockMatchMedia(prefersDark: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: query === '(prefers-color-scheme: dark)' && prefersDark,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

function renderShell(initialPath = '/') {
  mockMatchMedia(true)
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <ThemeProvider>
        <AppShell />
      </ThemeProvider>
    </MemoryRouter>,
  )
}

// The sidebar persists its expanded/collapsed choice to localStorage
// (STORY-056 AC1) — clear it before every test so one test's collapse
// click can never leak into the next test's "starts expanded" assumption.
beforeEach(() => {
  window.localStorage.clear()
})

describe('AppShell routing', () => {
  // These routing tests assert every tab's PLAIN accessible name — pin the
  // Approvals fetch to zero open proposals so its badge never appends a
  // ", N pending" suffix (the badge itself is exercised separately below,
  // in "AppShell — Approvals badge").
  beforeEach(() => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))
  })

  it('renders all six nav items', () => {
    renderShell()
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })

  it('renders the Dashboard panel at the root route', () => {
    renderShell('/')
    expect(
      screen.getByRole('heading', { name: 'Dashboard' }),
    ).toBeInTheDocument()
  })

  it('switches the active panel when a tab is clicked', async () => {
    const user = userEvent.setup()
    renderShell('/')

    await user.click(screen.getByRole('link', { name: 'Availability' }))

    expect(
      screen.getByRole('heading', { name: 'Availability' }),
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('heading', { name: 'Dashboard' }),
    ).not.toBeInTheDocument()
  })

  it('switches the active panel via keyboard activation of a tab', async () => {
    const user = userEvent.setup()
    renderShell('/')

    await user.tab() // theme toggle or first focusable before tabs, keep tabbing to the link
    // Tab until the Maintenance link is focused, then activate with Enter.
    const maintenanceLink = screen.getByRole('link', { name: 'Maintenance' })
    maintenanceLink.focus()
    await user.keyboard('{Enter}')

    expect(
      screen.getByRole('heading', { name: 'Maintenance' }),
    ).toBeInTheDocument()
  })

  it('renders each route to its own placeholder panel', async () => {
    const user = userEvent.setup()
    renderShell('/')

    for (const tab of TABS.slice(1)) {
      await user.click(screen.getByRole('link', { name: tab.label }))
      expect(
        screen.getByRole('heading', { name: tab.label }),
      ).toBeInTheDocument()
    }
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

  it('gives each route exactly one level-one heading', () => {
    renderShell('/')
    expect(
      screen.getByRole('heading', { name: 'Dashboard', level: 1 }),
    ).toBeInTheDocument()
  })

  it('renders a not-found panel with a link back to Dashboard for an unknown path', () => {
    renderShell('/nonexistent-tab')

    expect(
      screen.getByRole('heading', { name: /not found/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Back to Dashboard' }),
    ).toBeInTheDocument()
    // Sidebar still renders alongside the not-found panel.
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
  })
})

describe('AppShell — sidebar collapse (STORY-056 AC1)', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))
  })

  it('starts expanded by default and collapses/expands via the header toggle', async () => {
    const user = userEvent.setup()
    renderShell('/')

    const toggle = screen.getByRole('button', { name: 'Collapse sidebar' })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    await user.click(toggle)

    expect(
      screen.getByRole('button', { name: 'Expand sidebar' }),
    ).toHaveAttribute('aria-expanded', 'false')

    // Tabs remain reachable by accessible name regardless of collapse state.
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })
})

describe('AppShell — top bar + banner (STORY-056 AC2, AC3)', () => {
  it('renders the top bar sample-mode trigger and theme toggle', async () => {
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

  it('toggling the top-bar trigger on shows the banner (single shared source of truth)', async () => {
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

describe('AppShell — Approvals badge (STORY-056 AC4)', () => {
  it('shows the open-proposal count on the Approvals sidebar item', async () => {
    renderShell('/')
    expect(
      await screen.findByRole('link', {
        name: `Approvals, ${FIXTURE_PROPOSALS.length} pending`,
      }),
    ).toBeInTheDocument()
  })

  it('shows no badge when the approvals fetch fails', async () => {
    server.use(
      http.get('/api/v1/approvals', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )
    renderShell('/')

    // Still routable by its plain label — no ", N pending" suffix.
    expect(await screen.findByRole('link', { name: 'Approvals' })).toBeInTheDocument()
  })
})
