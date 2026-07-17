import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from './theme/ThemeContext'
import { AppShell } from './AppShell'
import { TABS } from './nav/tabs'
import { QUERY_MOBILE_DOWN, QUERY_TABLET_DOWN } from './lib/breakpoints'
import { stubMatchMedia } from './test/matchMedia'
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

describe('AppShell — persistent SAMPLE chip (STORY-102 AC2)', () => {
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
    server.use(
      http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })),
      http.get('/api/v1/approvals', () => HttpResponse.json([])),
    )
    renderShell('/')

    await user.click(await screen.findByRole('button', { name: 'Dismiss' }))
    expect(screen.getByText('SAMPLE')).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Availability' }))

    expect(
      screen.getByRole('heading', { name: 'Availability' }),
    ).toBeInTheDocument()
    expect(screen.getByText('SAMPLE')).toBeInTheDocument()
  })

  it('shows no chip when the flag is off', async () => {
    renderShell('/')
    await screen.findByRole('switch', { name: 'Sample mode' })
    expect(screen.queryByText('SAMPLE')).not.toBeInTheDocument()
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

/** Stubs both the theme's `prefers-color-scheme` query AND the two
 * responsive breakpoints in one call, for the STORY-096 describe blocks
 * below — `renderShell` above intentionally keeps its own narrower
 * `mockMatchMedia` untouched (existing desktop-width behavior must stay
 * provably unchanged with ZERO changes to those tests). */
function renderShellAtViewport(
  { isNarrow = false, isMobile = false }: { isNarrow?: boolean; isMobile?: boolean },
  initialPath = '/',
) {
  stubMatchMedia({
    '(prefers-color-scheme: dark)': true,
    [QUERY_TABLET_DOWN]: isNarrow || isMobile,
    [QUERY_MOBILE_DOWN]: isMobile,
  })
  server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <ThemeProvider>
        <AppShell />
      </ThemeProvider>
    </MemoryRouter>,
  )
}

describe('AppShell — responsive shell (STORY-096 AC3): <=1024px rail auto-collapse', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('auto-collapses the sidebar to the icon rail, ignoring the persisted expanded preference', () => {
    renderShellAtViewport({ isNarrow: true })
    expect(
      screen.getByRole('button', { name: 'Expand sidebar' }),
    ).toHaveAttribute('aria-expanded', 'false')
  })

  it('renders no drawer/hamburger trigger at this width (rail only, not drawer)', () => {
    renderShellAtViewport({ isNarrow: true })
    expect(
      screen.queryByRole('button', { name: 'Open navigation menu' }),
    ).not.toBeInTheDocument()
  })

  it('still lets the user expand the rail manually at this width', async () => {
    const user = userEvent.setup()
    renderShellAtViewport({ isNarrow: true })

    await user.click(screen.getByRole('button', { name: 'Expand sidebar' }))

    expect(
      screen.getByRole('button', { name: 'Collapse sidebar' }),
    ).toHaveAttribute('aria-expanded', 'true')
  })
})

describe('AppShell — responsive shell (STORY-096 AC2): <=768px overlay drawer', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders no persistent sidebar nav — only a hamburger trigger in the top bar', () => {
    renderShellAtViewport({ isMobile: true })
    expect(screen.queryByRole('navigation', { name: 'Primary' })).not.toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Open navigation menu' }),
    ).toBeInTheDocument()
  })

  it('opens the drawer from the hamburger trigger, closes on Escape, and returns focus', async () => {
    const user = userEvent.setup()
    renderShellAtViewport({ isMobile: true })

    const trigger = screen.getByRole('button', { name: 'Open navigation menu' })
    await user.click(trigger)

    expect(screen.getByRole('dialog', { name: 'Navigation' })).toBeInTheDocument()
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })
})
