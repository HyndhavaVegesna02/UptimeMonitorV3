/**
 * Theme resolution (STORY-015a AC5). Pure, dependency-free functions so they
 * can run both in the pre-paint inline script in index.html (duplicated
 * there deliberately — see that file's comment) and inside React via
 * ThemeContext, with a single shared storage key and precedence rule:
 * a persisted override always wins over the OS `prefers-color-scheme`.
 */

export const THEME_STORAGE_KEY = 'uptime-monitor-theme'

export type Theme = 'dark' | 'light'

function isTheme(value: string | null): value is Theme {
  return value === 'dark' || value === 'light'
}

/** The OS/browser color-scheme preference, defaulting to dark when unknown. */
export function getSystemTheme(): Theme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light'
}

/** The persisted override, or null if none is stored (or it is corrupt). */
export function getStoredTheme(): Theme | null {
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY)
  return isTheme(stored) ? stored : null
}

/** Persist an explicit user override. */
export function persistTheme(theme: Theme): void {
  window.localStorage.setItem(THEME_STORAGE_KEY, theme)
}

/** Stored override > system preference. This is the single source of truth
 * for "what theme should apply right now" — both the pre-paint script and
 * ThemeProvider's initial state must agree with it to avoid a flash. */
export function resolveInitialTheme(): Theme {
  return getStoredTheme() ?? getSystemTheme()
}
