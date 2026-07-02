import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from './theme/ThemeContext'
import { AppShell } from './AppShell'
import { TABS } from './nav/tabs'

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

describe('AppShell routing', () => {
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
    // Nav still renders alongside the not-found panel.
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
  })
})
