import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ThemeProvider } from './ThemeContext'
import { THEME_STORAGE_KEY } from './resolveTheme'
import { useTheme } from './useTheme'

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

function Probe() {
  const { theme, toggleTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <button onClick={toggleTheme}>Toggle theme</button>
    </div>
  )
}

describe('ThemeProvider / useTheme', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('resolves the system-default theme on first render', () => {
    mockMatchMedia(true)
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    )
    expect(screen.getByTestId('theme-value')).toHaveTextContent('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('toggles the theme and reflects it on <html data-theme>', async () => {
    const user = userEvent.setup()
    mockMatchMedia(true)
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Toggle theme' }))

    expect(screen.getByTestId('theme-value')).toHaveTextContent('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('persists a toggled override to localStorage', async () => {
    const user = userEvent.setup()
    mockMatchMedia(true)
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Toggle theme' }))

    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })

  it('a stored override wins over the system preference on mount', () => {
    mockMatchMedia(true)
    window.localStorage.setItem(THEME_STORAGE_KEY, 'light')

    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    )

    expect(screen.getByTestId('theme-value')).toHaveTextContent('light')
  })

  it('throws a clear error when useTheme is used outside the provider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<Probe />)).toThrow(
      'useTheme must be used within a ThemeProvider',
    )
    consoleError.mockRestore()
  })
})
