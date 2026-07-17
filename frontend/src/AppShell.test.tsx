import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AppShell } from './AppShell'
import { TABS } from './nav/tabs'
import { ThemeProvider } from './theme/ThemeContext'

function mockMatchMedia(preference: 'dark' | 'light' | 'no-preference') {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches:
        (query === '(prefers-color-scheme: dark)' && preference === 'dark') ||
        (query === '(prefers-color-scheme: light)' && preference === 'light'),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

function renderShell(initialPath = '/') {
  mockMatchMedia('dark')
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <ThemeProvider>
        <AppShell />
      </ThemeProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  window.localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('AppShell — minimal rewrite-in-progress placeholder shell (STORY-103 AC5)', () => {
  it('renders the brand in the top bar', () => {
    renderShell()
    expect(screen.getByText('Uptime Monitor')).toBeInTheDocument()
  })

  it('renders the Dashboard placeholder at the root route with exactly one h1', () => {
    renderShell('/')
    expect(
      screen.getByRole('heading', { name: 'Dashboard', level: 1 }),
    ).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getByText(/rewrite in progress/i)).toBeInTheDocument()
  })

  it.each(TABS)('renders a placeholder for the $label tab at $path', (tab) => {
    renderShell(tab.path)
    expect(
      screen.getByRole('heading', { name: tab.label, level: 1 }),
    ).toBeInTheDocument()
  })

  it('renders a not-found placeholder with a link back to Dashboard for an unknown path', () => {
    renderShell('/nonexistent-tab')

    expect(
      screen.getByRole('heading', { name: /not found/i, level: 1 }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Back to Dashboard' }),
    ).toBeInTheDocument()
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

  it('renders a theme toggle reflecting the CURRENT theme, and toggles <html data-theme>', async () => {
    const user = userEvent.setup()
    renderShell('/')

    const toggle = screen.getByRole('button', { name: 'Switch to light theme' })
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    await user.click(toggle)

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(
      screen.getByRole('button', { name: 'Switch to dark theme' }),
    ).toBeInTheDocument()
  })
})
