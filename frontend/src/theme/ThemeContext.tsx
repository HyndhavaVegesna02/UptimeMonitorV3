import { useEffect, useState, type ReactNode } from 'react'
import { persistTheme, resolveInitialTheme, type Theme } from './resolveTheme'
import { ThemeContext } from './theme-context'

/**
 * Owns the resolved theme for the whole app (STORY-015a AC5). Initial state
 * mirrors index.html's pre-paint inline script (stored choice > dark,
 * PERIOD — the OS `prefers-color-scheme` is never consulted, corrected at
 * the STORY-103 reality gate) so there is no flash: the <html data-theme>
 * attribute the script already set on load is simply confirmed, never
 * changed, on the first render.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => resolveInitialTheme())

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme((current) => {
      const next: Theme = current === 'dark' ? 'light' : 'dark'
      persistTheme(next)
      return next
    })
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
