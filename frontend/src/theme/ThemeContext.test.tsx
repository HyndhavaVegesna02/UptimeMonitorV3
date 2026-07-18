import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ThemeProvider } from './ThemeContext'
import { THEME_STORAGE_KEY } from './resolveTheme'
import { useTheme } from './useTheme'

/**
 * STORY-103 reality-gate correction (2026-07-18): stored choice > dark,
 * PERIOD — `prefers-color-scheme` is never consulted, so these tests no
 * longer stub `matchMedia` at all (there is nothing left for it to
 * influence).
 */
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

  it('resolves to dark on first render when nothing is stored', () => {
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
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Toggle theme' }))

    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })

  it('a stored override wins over the dark default on mount', () => {
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
