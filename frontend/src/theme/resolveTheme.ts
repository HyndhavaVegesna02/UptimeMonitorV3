/**
 * Theme resolution (STORY-015a AC5; precedence corrected at the STORY-103
 * reality gate, 2026-07-18). Pure, dependency-free functions so they can
 * run both in the pre-paint inline script in index.html (duplicated there
 * deliberately — see that file's comment) and inside React via
 * ThemeContext, with a single shared storage key and precedence rule:
 * a persisted override always wins; otherwise the app is DARK,
 * unconditionally — the OS `prefers-color-scheme` is NEVER consulted.
 * Mission Teal is a dark-first mission-control identity, and most
 * headless/desktop OSes report `prefers-color-scheme: light` by default,
 * so honoring it would make the common first impression light and defeat
 * that identity; the user's own explicit toggle (persisted) is the only
 * thing that can ever move the app to light.
 */

export const THEME_STORAGE_KEY = 'uptime-monitor-theme'

export type Theme = 'dark' | 'light'

function isTheme(value: string | null): value is Theme {
  return value === 'dark' || value === 'light'
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

/** Stored override > dark, period. This is the single source of truth for
 * "what theme should apply right now" — both the pre-paint script and
 * ThemeProvider's initial state must agree with it to avoid a flash. The
 * OS/browser `prefers-color-scheme` is deliberately NEVER read here (see
 * the module docstring). */
export function resolveInitialTheme(): Theme {
  return getStoredTheme() ?? 'dark'
}
