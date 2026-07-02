import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '../theme/ThemeContext'
import { Nav } from './Nav'
import { TABS } from './tabs'

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

function renderNav(initialPath = '/') {
  mockMatchMedia(true)
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <ThemeProvider>
        <Nav />
      </ThemeProvider>
    </MemoryRouter>,
  )
}

describe('Nav', () => {
  it('renders the app title', () => {
    renderNav()
    expect(screen.getByText('Uptime Monitor')).toBeInTheDocument()
  })

  it('renders all six tabs', () => {
    renderNav()
    for (const tab of TABS) {
      expect(screen.getByRole('link', { name: tab.label })).toBeInTheDocument()
    }
  })

  it('marks the tab matching the current route as active (aria-current)', () => {
    renderNav('/availability')
    expect(screen.getByRole('link', { name: 'Availability' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveAttribute(
      'aria-current',
    )
  })

  it('renders a theme toggle control', () => {
    renderNav()
    expect(
      screen.getByRole('button', { name: /toggle theme|switch to/i }),
    ).toBeInTheDocument()
  })
})
